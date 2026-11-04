import base64, os, sys, types
os.environ["HF_TOKEN"] = "<HF_TOKEN>"
CUT_B64 = "<written by sample_qmb.py>"
os.makedirs("/kaggle/working/pkg/ml/alignment", exist_ok=True); os.makedirs("/kaggle/working/pkg/ml/assets", exist_ok=True)
for p in ("ml", "ml/alignment"): open(f"/kaggle/working/pkg/{p}/__init__.py", "w").close()
open("/kaggle/working/pkg/ml/alignment/quran_g2p.py", "w").write('"""Diacritised Arabic -> IqraEval phonemes, for the v3 pronunciation verifier.\n\nThe verifier (``ml/inference/pronunciation_verifier.py``) is told which\nphonemes the reciter SHOULD say, in the exact symbol set and conventions of the\nIqraEval data it was trained on. This module writes those phonemes from the\nfully vowelled text. It is our own rule set (the phonetiser IqraEval used is\nlicensed non-commercial), checked against IqraEval\'s own reference phonemes\nby ``ml/evaluation/check_quran_g2p.py``.\n\nConventions (read off IqraEval\'s ``phoneme_ref``):\n  * one symbol per consonant, doubled for shadda: ``b`` / ``bb``; every hamza is ``<``;\n  * short vowels ``a i u``, long ``aa ii uu``; a vowel next to an emphatic\n    consonant is written upper case (``A I U``, ``AA II UU``);\n  * tanween is not pronounced (fathatan + alif reads ``aa``); a word is read\n    in connection with the next one, and the last word of the utterance is\n    read in pause (its final short vowel drops);\n  * hamzat al-wasl and the lam of a sun letter are silent; at the very start\n    of an utterance hamzat al-wasl is ``<`` plus its vowel.\n\n``phonemize(text)`` gives one flat list; ``phonemize_words(words)`` gives one\nlist per word (for folding verifier scores back onto words).\n"""\nfrom __future__ import annotations\n\nimport re\nimport unicodedata\n\nFATHA, DAMMA, KASRA, SUKUN, SHADDA = "َ", "ُ", "ِ", "ْ", "ّ"\nFATHATAN, DAMMATAN, KASRATAN = "ً", "ٌ", "ٍ"\nDAGGER_ALIF = "ٰ"\nVOWEL_MARK = {FATHA: "a", DAMMA: "u", KASRA: "i"}\nTANWEEN = {FATHATAN: "a", DAMMATAN: "u", KASRATAN: "i"}\n\nCONSONANT = {\n    "ب": "b", "ت": "t", "ث": "^", "ج": "j", "ح": "H", "خ": "x", "د": "d", "ذ": "*",\n    "ر": "r", "ز": "z", "س": "s", "ش": "$", "ص": "S", "ض": "D", "ط": "T", "ظ": "Z",\n    "ع": "E", "غ": "g", "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",\n    "ه": "h", "و": "w", "ي": "y", "ى": "y",\n    "ء": "<", "أ": "<", "إ": "<", "ؤ": "<", "ئ": "<",\n}\nSUN = set("تثدذرزسشصضطظلن")\n# A vowel right after these is "heavy" (upper case) ...\nEMPHATIC_AFTER = {"S", "D", "T", "Z", "q", "x", "g"}\n# ... and right before these.\nEMPHATIC_BEFORE = {"S", "D", "T", "Z", "q"}\n\n# Uthmani (Mushaf) spelling -> the plain vowelled spelling the rules expect.\n_UTHMANI = [\n    ("ٱ", "ا"),          # hamzat al-wasl\n    ("ۡ", SUKUN),   # small high dotless head of khah = sukun\n    ("ـ", ""),           # tatweel\n]\n_DROP = re.compile("[ؐ-ؚۖ-ۜ۟-۪ۨ-ۭٕٓٔ]")\n\n\n# Words whose long aa is not written in plain spelling.\n_HIDDEN_ALIF = {\n    "هَذَا": "هَاذَا", "هَذِهِ": "هَاذِهِ", "هَذَانِ": "هَاذَانِ", "هَؤُلَاءِ": "هَاؤُلَاءِ",\n    "ذَلِكَ": "ذَالِكَ", "ذَلِكُمْ": "ذَالِكُمْ", "لَكِنْ": "لَاكِنْ", "لَكِنَّ": "لَاكِنَّ",\n    "لَكِنَّهُ": "لَاكِنَّهُ", "أُولَئِكَ": "أُولَائِكَ", "كَذَلِكَ": "كَذَالِكَ",\n}\n\n\ndef normalize(text: str) -> str:\n    text = unicodedata.normalize("NFC", text)\n    for a, b in _UTHMANI:\n        text = text.replace(a, b)\n    # آ after a vowelled letter is a long aa (Uthmani madd: مَآءً); at a word\n    # start or after sukun it is hamza + aa (آمَنُوا، الْآخِرَة).\n    text = re.sub("([\\u0621-\\u064a][\\u0651]?[\\u064e\\u064b][\\u0651]?)آ", "\\\\1ا", text)\n    text = text.replace("آ", "ء" + FATHA + "ا")\n    text = text.replace(DAGGER_ALIF, "")  # IqraEval reads the dagger alif short (lexicon below has the exceptions)\n    for word, fixed in _HIDDEN_ALIF.items():\n        text = re.sub(rf"(?<![\\u0621-\\u064a]){word}", fixed, text)\n    text = _DROP.sub("", text)\n    text = re.sub(r"[^ء-يً-ْٰ\\s]", "", text)\n    return re.sub(r"\\s+", " ", text).strip()\n\n\ndef _letters(word: str) -> list[tuple[str, set]]:\n    """[(base letter, {marks})] for one word."""\n    out: list[tuple[str, set]] = []\n    for ch in word:\n        if "ً" <= ch <= "ْ" or ch == DAGGER_ALIF:\n            if out:\n                out[-1][1].add(ch)\n        else:\n            out.append((ch, set()))\n    return out\n\n\ndef _word_units(word: str, *, utterance_start: bool, quran: bool = True) -> list[str]:\n    """Phonemes of one word, before cross-word effects (pause, emphasis)."""\n    tail: list[str] = []\n    if word.endswith("َوْا"):\n        word, tail = word[:-3], ["uu"]  # -aw + silent alif (waw al-jama\'a): IqraEval writes a uu\n    L = _letters(word)\n    ph: list[str] = []\n    i = 0\n    while i < len(L):\n        ch, marks = L[i]\n        nxt = L[i + 1] if i + 1 < len(L) else None\n        prev_vowel = ph[-1] if ph and ph[-1] in ("a", "i", "u") else None\n\n        if ch == "ا":\n            if i == 0:  # hamzat al-wasl\n                v = marks & set(VOWEL_MARK)\n                if v:\n                    ph += ["<", VOWEL_MARK[next(iter(v))]]\n                elif utterance_start and nxt and nxt[0] == "ل":\n                    ph += ["<", "a"]  # the article opening an utterance is voiced\n                i += 1\n                continue\n            v = marks & set(VOWEL_MARK)\n            if v:  # a vowelled alif inside a word is read as a hamza\n                ph += ["<", VOWEL_MARK[next(iter(v))]]\n                i += 1\n                continue\n            if (not marks and nxt and nxt[0] == "ل" and i + 2 < len(L) and L[i - 1][0] in "وفبكل"\n                    and (not nxt[1] & set(VOWEL_MARK) or SHADDA in nxt[1])):\n                i += 1  # al- after a prefix (wa-, fa-, bi-, ka-): wasl alif, silent\n                continue\n            if prev_vowel == "a" or FATHATAN in (L[i - 1][1] if i else set()):\n                ph[-1:] = ["aa"] if prev_vowel == "a" else ph[-1:]\n                if prev_vowel != "a":\n                    ph.append("aa")\n            # waw al-jama\'a alif and other silent alifs: nothing\n            i += 1\n            continue\n\n        if ch == "ة":\n            if marks & set(VOWEL_MARK):\n                ph.append("t")\n                ph.append(VOWEL_MARK[next(iter(marks & set(VOWEL_MARK)))])\n            elif marks & set(TANWEEN):\n                if quran:\n                    ph += ["t", TANWEEN[next(iter(marks & set(TANWEEN)))], "n"]\n            else:\n                ph.append("t")\n            i += 1\n            continue\n\n        if ch == "ل" and not (marks & (set(VOWEL_MARK) | {SHADDA})) and nxt and nxt[0] in SUN and SHADDA in nxt[1]:\n            i += 1  # lam of al- before a sun letter: silent (the sun letter is doubled)\n            continue\n\n        if ch in ("و", "ي") and marks == {SUKUN} and prev_vowel == ("u" if ch == "و" else "i"):\n            ph[-1] = prev_vowel * 2; i += 1; continue  # long vowel written with an explicit sukun\n        if ch in ("و", "ي", "ى") and not marks & (set(VOWEL_MARK) | {SHADDA, SUKUN} | set(TANWEEN)):\n            if ch in ("ى",) and prev_vowel == "a":\n                ph[-1] = "aa"; i += 1; continue\n            if ch == "و" and prev_vowel == "u":\n                ph[-1] = "uu"; i += 1; continue\n            if ch in ("ي", "ى") and prev_vowel == "i":\n                ph[-1] = "ii"; i += 1; continue\n            if ch == "ى":\n                ph[-1:] = ph[-1:]  # alif maqsura after a consonant: rare; treat as aa\n                ph.append("aa"); i += 1; continue\n\n        if ch in CONSONANT:\n            c = CONSONANT[ch]\n            if SHADDA in marks:\n                # kasra + shadda-ya / damma + shadda-waw: the long vowel then the glide\n                if c == "y" and prev_vowel == "i":\n                    ph[-1] = "ii"; ph.append("y")\n                elif c == "w" and prev_vowel == "u":\n                    ph[-1] = "uu"; ph.append("w")\n                else:\n                    ph.append(c + c)\n            else:\n                ph.append(c)\n            v = marks & set(VOWEL_MARK)\n            if v:\n                ph.append(VOWEL_MARK[next(iter(v))])\n            elif ch == "إ" and not marks & ({SUKUN} | set(TANWEEN)):\n                ph.append("i")  # hamza under alif always carries kasra\n            elif marks & set(TANWEEN):\n                t = next(iter(marks & set(TANWEEN)))\n                if quran:  # Mushaf style (IqraEval QuranMB / IS26): tanween is a vowel + n\n                    ph += [TANWEEN[t], "n"]\n                    if t == FATHATAN and nxt and nxt[0] in ("ا", "ى"):\n                        ph.append("aa"); i += 1  # IqraEval also voices the alif after fathatan\n                elif t == FATHATAN and nxt and nxt[0] in ("ا", "ى"):\n                    ph.append("aa"); i += 1  # consume the alif\n                elif t == FATHATAN:\n                    ph.append("aa")\n            if DAGGER_ALIF in marks:  # dagger alif: a long aa (IqraEval keeps al-rahman short)\n                if ph and ph[-1] == "a":\n                    ph[-1] = "aa"\n                else:\n                    ph.append("aa")\n            i += 1\n            continue\n        i += 1\n    return ph + tail\n\n\ndef _pause(ph: list[str], word: str = "") -> list[str]:\n    """Last word of the utterance: its final short vowel is not pronounced."""\n    if len(ph) >= 3 and ph[-3:] in (["i", "y", "a"], ["u", "w", "a"]):\n        return ph[:-3] + [ph[-3] * 2]  # -iya / -uwa in pause: a long vowel\n    if re.sub("[\\u064b-\\u0652]", "", word).endswith("ة"):\n        # ta marbuta in pause: the \'a\' before it stays, the ta (and its vowel) go\n        while ph and ph[-1] in ("t", "a", "i", "u") and not (ph[-1] == "a" and (len(ph) < 2 or ph[-2] != "t")):\n            if ph[-1] == "t":\n                ph = ph[:-1]\n                break\n            ph = ph[:-1]\n        return ph\n    if ph and ph[-1] in ("a", "i", "u"):\n        return ph[:-1]\n    return ph\n\n\ndef _emphasis(ph: list[str], word_end: set[int]) -> list[str]:\n    """``word_end``: indices that are the last phoneme of a word."""\n    out = list(ph)\n    base = lambda s: s[0] if s else s\n    for k, p in enumerate(out):\n        if p in ("a", "i", "u", "aa", "ii", "uu"):\n            before = out[k - 1] if k else ""\n            after = out[k + 1] if k + 1 < len(out) and k not in word_end else ""\n            if base(before) in EMPHATIC_AFTER or (p in ("a", "i", "u", "aa") and base(after) in EMPHATIC_BEFORE):\n                out[k] = p.upper()\n    return out\n\n\ndef phonemize_words(words: list[str], *, style: str = "quran") -> list[list[str]]:\n    """One phoneme list per word, the words read as one connected utterance.\n\n    ``style="quran"`` (default) follows IqraEval\'s Quran sets (QuranMB, IS26):\n    every vowel and tanween pronounced, no pause form. ``style="sentence"``\n    follows Iqra_train\'s sentences: tanween dropped, last word in pause.\n    """\n    quran = style == "quran"\n    norm = [normalize(w) for w in words]\n    per = [_word_units(w, utterance_start=(k == 0), quran=quran) for k, w in enumerate(norm)]\n    if per and not quran:\n        per[-1] = _pause(per[-1], norm[-1])\n    # emphasis looks across word boundaries\n    flat = [p for w in per for p in w]\n    ends, k = set(), 0\n    for w in per:\n        k += len(w)\n        if w:\n            ends.add(k - 1)\n    flat = _emphasis(flat, ends)\n    out, k = [], 0\n    for w in per:\n        out.append(flat[k:k + len(w)])\n        k += len(w)\n    return out\n\n\ndef phonemize(text: str, *, style: str = "quran") -> list[str]:\n    return [p for w in phonemize_words(normalize(text).split(), style=style) for p in w]\n\n\n# ---------------------------------------------------------------------------\n# Precomputed Quran lexicon (built by scripts/build_quran_phonemes.py from the\n# plain vowelled text, which matches IqraEval\'s references best).\n_LEXICON: dict | None = None\n\n\ndef ayah_word_phonemes(surah: int, ayah: int) -> list[list[str]] | None:\n    """Phonemes for each word of an ayah (Mushaf word order), or None if unknown."""\n    global _LEXICON\n    if _LEXICON is None:\n        import gzip\n        import json\n        from pathlib import Path\n        path = Path(__file__).resolve().parents[1] / "assets" / "quran_phonemes.json.gz"\n        try:\n            with gzip.open(path, "rt", encoding="utf-8") as f:\n                raw = json.load(f)\n            _LEXICON = {k: [w.split() for w in v] for k, v in raw["ayahs"].items()}\n        except OSError:\n            _LEXICON = {}\n    return _LEXICON.get(f"{surah}:{ayah}")\n')
open("/kaggle/working/pkg/ml/assets/quran_phonemes.json.gz", "wb").write(base64.b64decode("<ml/assets/quran_phonemes.json.gz, base64>"))
mod = types.ModuleType("pv"); sys.modules["pv"] = mod
exec(compile('"""Reference-aware pronunciation verifier (Safha MDD v3).\n\nGiven audio and the phonemes the reciter SHOULD say, the v3 model returns, for\neach expected phoneme, the probability that it was mispronounced. The live\nsession already knows the expected text (the user picks the surah), so this is\na second, independent opinion on words the ASR heard as "correct".\n\nModel files (from the safha-latest bundle, ``models/safha-mdd-v3``):\n  config.json, model.safetensors, preprocessor_config.json  (w2v-BERT 2.0 encoder + CTC head)\n  verifier.pt                                                 (small transformer over expected phonemes)\n  vocab.json                                                  (IqraEval phoneme set; index 0 = CTC blank)\n  decision.json                                               ({"threshold": 0.35, "verifier": {...}})\n\nQuranMB.v2 test (1,642 human-annotated recordings), end to end with the\nphonemes from ``ml/alignment/quran_g2p.py``:\n\n    threshold 0.35: precision 0.79, recall 0.45, false alarms 0.78% per phoneme\n    threshold 0.50: precision 0.82, recall 0.44, false alarms 0.65%  (app default)\n    (IqraEval\'s own phonemes at 0.35: precision 0.84, recall 0.48, 0.63%)\n\nIt is meant to ADD red marks only when confident, never to clear an ASR verdict.\nThese numbers do NOT meet Safha\'s release gate (``ml/evaluation/pronunciation.py``:\nprecision >= 0.98, recall >= 0.90 per kind, held-out speakers and surahs), so the\nlive session runs it in shadow mode unless a passing report for ``fingerprint()``\nis configured.\n\nHeavy imports (torch, transformers) happen in ``load``; importing this module\nis cheap and safe in tests.\n"""\nfrom __future__ import annotations\n\nimport json\nimport math\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom typing import Callable, Optional, Sequence\n\n# Training clipped utterances at 15 s; longer windows are scored in pieces.\nMAX_WINDOW_S = 15.0\n\n\n@dataclass(frozen=True)\nclass VerifierResult:\n    """Per expected phoneme: probability it was said wrong."""\n    probabilities: list[float]\n    threshold: float\n\n    def flags(self) -> list[bool]:\n        return [p >= self.threshold for p in self.probabilities]\n\n\ndef word_verdicts(word_phonemes: Sequence[Sequence[str]], result: VerifierResult) -> list[Optional[float]]:\n    """Fold phoneme probabilities back onto words: a word\'s score is its worst phoneme.\n\n    ``None`` for a word with no phonemes (nothing to judge).\n    """\n    out: list[Optional[float]] = []\n    k = 0\n    for phonemes in word_phonemes:\n        n = len(phonemes)\n        chunk = result.probabilities[k:k + n]\n        out.append(max(chunk) if chunk else None)\n        k += n\n    if k != len(result.probabilities):\n        raise ValueError(f"{k} phonemes in words but {len(result.probabilities)} probabilities")\n    return out\n\n\nclass PronunciationVerifier:\n    """Loads the v3 model once; ``score`` is thread-safe for inference (no grad, eval mode)."""\n\n    def __init__(self, model_dir: str | Path, *, device: str = "cpu", threshold: Optional[float] = None):\n        self.model_dir = Path(model_dir)\n        self.device = device\n        decision = json.loads((self.model_dir / "decision.json").read_text())\n        # decision.json holds the threshold picked with IqraEval\'s own phonemes (0.35).\n        # With our phonemizer, 0.5 gives the same precision on QuranMB.v2 (0.82, false alarms 0.65%).\n        self.threshold = float(threshold if threshold is not None else decision.get("threshold", 0.35))\n        self._arch = decision.get("verifier", {})\n        self.vocab: list[str] = json.loads((self.model_dir / "vocab.json").read_text())\n        self.phoneme_id = {p: i for i, p in enumerate(self.vocab)}\n        self._encoder = self._fe = self._verifier = self._torch = None\n\n    # ------------------------------------------------------------------\n    def load(self) -> "PronunciationVerifier":\n        import torch\n        import torch.nn as nn\n        from transformers import AutoFeatureExtractor, Wav2Vec2BertForCTC\n\n        self._torch = torch\n        self._fe = AutoFeatureExtractor.from_pretrained(self.model_dir)\n        enc = Wav2Vec2BertForCTC.from_pretrained(self.model_dir, torch_dtype=torch.float32)\n        enc.float().eval().to(self.device)\n        self._encoder = enc\n        hid, v = int(self._arch.get("hidden", 1024)), int(self._arch.get("vocab", len(self.vocab)))\n        d, layers, heads = int(self._arch.get("d", 256)), int(self._arch.get("layers", 3)), int(self._arch.get("heads", 4))\n\n        class Verifier(nn.Module):  # must match train_mdd_v3.py exactly\n            def __init__(self):\n                super().__init__()\n                self.mem = nn.Sequential(nn.Linear(hid, d), nn.LayerNorm(d))\n                self.post = nn.Linear(v, d)\n                self.emb = nn.Embedding(v + 1, d, padding_idx=v)\n                layer = nn.TransformerDecoderLayer(d, heads, 4 * d, dropout=0.1, batch_first=True, norm_first=True)\n                self.dec = nn.TransformerDecoder(layer, layers)\n                self.head = nn.Sequential(nn.LayerNorm(d), nn.Linear(d, 1))\n                self.d = d\n\n            def forward(self, hidden, logp, frame_pad, ref, ref_pad):\n                m = self.mem(hidden) + self.post(logp.exp()) + _sinusoid(torch, hidden.shape[1], self.d, hidden.device)\n                q = self.emb(ref) + _sinusoid(torch, ref.shape[1], self.d, ref.device)\n                h = self.dec(q, m, tgt_key_padding_mask=ref_pad, memory_key_padding_mask=frame_pad)\n                return self.head(h).squeeze(-1)\n\n        ver = Verifier()\n        state = torch.load(self.model_dir / "verifier.pt", map_location="cpu")\n        ver.load_state_dict({k: t.float() for k, t in state.items()})\n        self._verifier = ver.eval().to(self.device)\n        return self\n\n    BUNDLE_FILES = ("config.json", "preprocessor_config.json", "vocab.json", "decision.json",\n                    "model.safetensors", "verifier.pt")\n\n    def fingerprint(self, extra: Sequence[str] = ()) -> str:\n        """SHA-256 of everything that decides a verdict, so a qualification\n        report (``ml.evaluation.pronunciation.qualified_for_model``) covers the\n        whole pipeline, not just the weights:\n\n        - every model file and the decision threshold;\n        - the phoneme lexicon and the source of the phonemizer that writes\n          references (``ml/alignment/quran_g2p.py``);\n        - the source of this module (feature extraction, scoring);\n        - torch / transformers / numpy versions;\n        - ``extra``: source text of caller-side logic, e.g. how the live\n          session cuts windows and folds phonemes onto words.\n        """\n        cache = getattr(self, "_fingerprints", None)\n        if cache is None:\n            cache = self._fingerprints = {}\n        key = tuple(extra)\n        if key in cache:\n            return cache[key]\n        import hashlib\n        import importlib.metadata as md\n\n        def file_digest(path: Path) -> str:\n            digest = hashlib.sha256()\n            with open(path, "rb") as f:\n                for chunk in iter(lambda: f.read(1 << 20), b""):\n                    digest.update(chunk)\n            return digest.hexdigest()\n\n        ml_root = Path(__file__).resolve().parents[1]\n        parts = [f"model/{n}:{file_digest(self.model_dir / n)}" for n in self.BUNDLE_FILES]\n        parts += [\n            f"lexicon:{file_digest(ml_root / \'assets\' / \'quran_phonemes.json.gz\')}",\n            f"g2p:{file_digest(ml_root / \'alignment\' / \'quran_g2p.py\')}",\n            f"scorer:{file_digest(Path(__file__).resolve())}",\n            f"threshold:{self.threshold:.4f}",\n        ]\n        for pkg in ("torch", "transformers", "numpy"):\n            try:\n                parts.append(f"{pkg}:{md.version(pkg)}")\n            except md.PackageNotFoundError:\n                parts.append(f"{pkg}:missing")\n        parts += [f"extra:{hashlib.sha256(src.encode()).hexdigest()}" for src in extra]\n        cache[key] = hashlib.sha256("\\n".join(parts).encode()).hexdigest()\n        return cache[key]\n\n    @property\n    def loaded(self) -> bool:\n        return self._verifier is not None\n\n    # ------------------------------------------------------------------\n    def score(self, audio_16k: Sequence[float], phonemes: Sequence[str]) -> VerifierResult:\n        """Probabilities per expected phoneme for one window of audio (16 kHz mono floats).\n\n        Phonemes outside the model\'s vocabulary get probability 0.0 (no evidence\n        either way) rather than an automatic red mark.\n        """\n        if not self.loaded:\n            self.load()\n        torch = self._torch\n        known = [i for i, p in enumerate(phonemes) if p in self.phoneme_id]\n        probs = [0.0] * len(phonemes)\n        if not known or len(audio_16k) < 1600:\n            return VerifierResult(probs, self.threshold)\n        import numpy as np\n        feats = self._fe(np.asarray(audio_16k, dtype=np.float32), sampling_rate=16000, return_tensors="pt")\n        x, m = feats["input_features"].to(self.device), feats["attention_mask"].to(self.device)\n        ref = torch.tensor([[self.phoneme_id[phonemes[i]] for i in known]], device=self.device)\n        pad = len(self.vocab)\n        with torch.no_grad():\n            out = self._encoder.wav2vec2_bert(input_features=x, attention_mask=m)\n            hidden = out.last_hidden_state.float()\n            logp = self._encoder.lm_head(hidden).float().log_softmax(-1)\n            n = hidden.shape[1]\n            length = max(1, min(n, math.ceil(float(m.sum()) * n / m.shape[1])))\n            frame_pad = torch.arange(n, device=self.device)[None] >= length\n            logit = self._verifier(hidden, logp, frame_pad, ref, ref == pad)\n        p = torch.sigmoid(logit[0]).cpu().tolist()\n        for k, i in enumerate(known):\n            probs[i] = float(p[k])\n        return VerifierResult(probs, self.threshold)\n\n\ndef _sinusoid(torch, n, d, device):\n    pos = torch.arange(n, device=device).float()[:, None]\n    i = torch.arange(0, d, 2, device=device).float()[None]\n    ang = pos / torch.pow(10000.0, i / d)\n    pe = torch.zeros(n, d, device=device)\n    pe[:, 0::2] = torch.sin(ang)\n    pe[:, 1::2] = torch.cos(ang)\n    return pe\n\n\nScoreFn = Callable[[Sequence[float], Sequence[str]], VerifierResult]\n', "pv", "exec"), mod.__dict__)
import base64, csv, gzip, io, json, math, os, random, sys, time
import numpy as np, soundfile as sf, torch, pyarrow.parquet as pq
import torch.nn.functional as F
from huggingface_hub import hf_hub_download, list_repo_files
from datasets import load_dataset, Audio
sys.path.insert(0, "/kaggle/working/pkg")
from ml.alignment.quran_g2p import ayah_word_phonemes, phonemize
import pv
random.seed(1)
d = next(r for r, _, f in os.walk("/kaggle/input") if r.rstrip("/").endswith("safha-mdd-v3") and "verifier.pt" in f)
v = pv.PronunciationVerifier(d, device="cuda", threshold=0.5).load()
pid = v.phoneme_id; PAD = len(v.vocab)
SHORT = {"a": "iu", "i": "au", "u": "ai", "A": "IU", "I": "AU", "U": "AI"}
LONG = {"a": "aa", "i": "ii", "u": "uu", "A": "AA", "I": "II", "U": "UU"}
LONG.update({b: a for a, b in list(LONG.items())})
VOW = set(SHORT) | {x for x in LONG if len(x) == 2}
CONS = [("S", "s"), ("D", "d"), ("T", "t"), ("Z", "*"), ("H", "h"), ("E", "<"), ("q", "k"), ("x", "H"),
        ("g", "x"), ("^", "s"), ("*", "z"), ("$", "s")]
CMAP = {}
for a, b in CONS:
    CMAP.setdefault(a, []).append(b); CMAP.setdefault(b, []).append(a)
def gem(p): return len(p) == 2 and p[0] == p[1] and p not in VOW
def kind(p): return "vowel" if p in VOW else "gemination" if gem(p) else "consonant"
def alts(p):
    """Competing realisations; None = phoneme dropped."""
    if p in SHORT: return [c for c in SHORT[p]] + [LONG[p], None]
    if p in VOW:  # long
        s = LONG[p]; return [s] + [x * 2 for x in SHORT[s]]
    if gem(p): return [p[0]] + [c * 2 for c in CMAP.get(p[0], []) if c * 2 in pid]
    out = [c for c in CMAP.get(p, [])]
    if p * 2 in pid: out.append(p * 2)
    return out
def variants(ref):
    out, n = [], len(ref)
    idx = list(range(n)); random.shuffle(idx)
    first = lambda cond: next((i for i in idx if cond(i)), None)
    i = first(lambda i: ref[i] in SHORT)
    if i is not None: out.append(("vowel_swap", ref[:i] + [random.choice(SHORT[ref[i]])] + ref[i + 1:], i))
    i = first(lambda i: ref[i] in LONG)
    if i is not None: out.append(("vowel_length", ref[:i] + [LONG[ref[i]]] + ref[i + 1:], i))
    i = first(lambda i: i + 1 < n and ref[i] not in VOW and ref[i + 1] not in VOW and ref[i] in pid)
    if i is not None: out.append(("sukun_to_vowel", ref[:i + 1] + [random.choice("aiu")] + ref[i + 1:], i + 1))
    i = first(lambda i: gem(ref[i]) and ref[i][0] in pid)
    if i is not None: out.append(("shadda_dropped", ref[:i] + [ref[i][0]] + ref[i + 1:], i))
    i = first(lambda i: ref[i] not in VOW and not gem(ref[i]) and ref[i] * 2 in pid)
    if i is not None: out.append(("shadda_added", ref[:i] + [ref[i] * 2] + ref[i + 1:], i))
    i = first(lambda i: ref[i] in CMAP)
    if i is not None: out.append(("consonant_swap", ref[:i] + [random.choice(CMAP[ref[i]])] + ref[i + 1:], i))
    return out
def load(b):
    x, sr = sf.read(io.BytesIO(b), dtype="float32", always_2d=False)
    if x.ndim > 1: x = x.mean(1)
    if sr != 16000:
        import torchaudio.functional as Fa; x = Fa.resample(torch.from_numpy(x), sr, 16000).numpy()
    return x
@torch.no_grad()
def encode(audio):
    fe = v._fe(np.asarray(audio, dtype=np.float32), sampling_rate=16000, return_tensors="pt")
    x, m = fe["input_features"].cuda(), fe["attention_mask"].cuda()
    hidden = v._encoder.wav2vec2_bert(input_features=x, attention_mask=m).last_hidden_state.float()
    logp = v._encoder.lm_head(hidden).float().log_softmax(-1)
    n = hidden.shape[1]
    length = max(1, min(n, math.ceil(float(m.sum()) * n / m.shape[1])))
    return hidden, logp, length
@torch.no_grad()
def verifier(hidden, logp, length, refs):
    frame_pad = torch.arange(hidden.shape[1], device="cuda")[None] >= length
    out = []
    for ref in refs:
        ids = torch.tensor([[pid.get(p, PAD) for p in ref]], device="cuda")
        out.append(torch.sigmoid(v._verifier(hidden, logp, frame_pad, ids, ids == PAD)[0]).cpu().tolist())
    return out
@torch.no_grad()
def seq_ll(logp, length, seqs, chunk=256):
    """log P(audio | seq) under the CTC head for each phoneme sequence."""
    lp = logp[0, :length]
    res = []
    for s0 in range(0, len(seqs), chunk):
        part = seqs[s0:s0 + chunk]
        tg = [torch.tensor([pid[p] for p in s if p in pid], dtype=torch.long) for s in part]
        tl = torch.tensor([len(t) for t in tg]); targets = torch.cat(tg).cuda()
        il = torch.full((len(part),), length, dtype=torch.long)
        loss = F.ctc_loss(lp[:, None, :].expand(-1, len(part), -1), targets, il, tl, blank=0,
                          reduction="none", zero_infinity=False)
        res += (-loss).cpu().tolist()
    return res
def gop(logp, length, ref, slots):
    """Score per slot (higher = audio fits an alternative better than the expected phoneme)."""
    seqs, owner = [list(ref)], [None]
    for s in slots:
        for a in alts(ref[s]):
            seqs.append(ref[:s] + ([a] if a else []) + ref[s + 1:]); owner.append(s)
    ll = seq_ll(logp, length, seqs)
    best = {s: -1e9 for s in slots}
    for o, x in zip(owner[1:], ll[1:]):
        if not math.isinf(x): best[o] = max(best[o], x)
    return {s: (best[s] - ll[0]) if not math.isinf(ll[0]) and best[s] > -1e9 else None for s in slots}

import hashlib, subprocess, secrets
OUTD = "/kaggle/working/clips"; os.makedirs(OUTD, exist_ok=True)
CUT = json.loads(gzip.decompress(base64.b64decode(CUT_B64)))
def sha(b): return hashlib.sha256(b).hexdigest()
@torch.no_grad()
def word_spans(logp, length, words, n_samples):
    """CTC forced alignment of the expected phonemes -> (start_s, end_s) per word."""
    import torchaudio.functional as TAF
    flat = [pid[p] for w in words for p in w]
    em = logp[:, :length].float().cpu()
    ali, _ = TAF.forced_align(em, torch.tensor([flat], dtype=torch.int32), blank=0)
    ali = ali[0].tolist()
    sec_per_frame = n_samples / 16000 / length
    # frames -> token index: each new non-blank run advances the token pointer
    tok_frames = [[] for _ in flat]; k = -1; prev = 0
    for t, a in enumerate(ali):
        if a != 0 and (a != prev or k < 0): k += 1
        if a != 0 and 0 <= k < len(flat): tok_frames[k].append(t)
        prev = a
    spans, j = [], 0
    for w in words:
        fr = [f for x in tok_frames[j:j + len(w)] for f in x]; j += len(w)
        spans.append((min(fr) * sec_per_frame, (max(fr) + 1) * sec_per_frame) if fr else None)
    return spans
def write_mp3(audio, name):
    wav = f"/tmp/{name}.wav"; sf.write(wav, audio, 16000)
    mp3 = f"{OUTD}/{name}.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-b:a", "48k", mp3], check=True)
    return mp3, sha(open(mp3, "rb").read())
manifest = []
def emit(clip_id, source, source_id, audio_bytes, audio, words, wi, extra):
    hidden, logp, length = encode(audio)
    spans = word_spans(logp, length, words, len(audio))
    sp = spans[wi]
    if sp is None: print("no span", clip_id); return
    a = max(0, int((sp[0] - 0.15) * 16000)); b = min(len(audio), int((sp[1] + 0.15) * 16000))
    w_mp3, w_sha = write_mp3(audio[a:b], clip_id + "_w")
    c_mp3, c_sha = write_mp3(audio, clip_id + "_c")
    manifest.append({"clip_id": clip_id, "source": source, "source_id": source_id, "source_audio_sha256": sha(audio_bytes),
                     "word_index": wi, "word_span_s": [round(sp[0], 3), round(sp[1], 3)],
                     "word_clip": os.path.basename(w_mp3), "word_clip_sha256": w_sha,
                     "context_clip": os.path.basename(c_mp3), "context_clip_sha256": c_sha, **extra})
want = {c["id"]: c for c in CUT}
test = load_dataset("IqraEval/QuranMB.v2", split="test").cast_column("audio", Audio(decode=False))
for row in test:
    c = want.get(row["ID"])
    if not c: continue
    b = row["audio"]["bytes"]
    emit(c["clip_id"], "QuranMB.v2", row["ID"], b, load(b), c["ours_words"], c["word"], {})
print("qmb clips", len(manifest), flush=True)
# ---- TLOG: real app recordings, no labels. 10 random words + 10 words flagged by v3 or GOP ----
tok = os.environ.get("HF_TOKEN")
files = sorted(f for f in list_repo_files("tarteel-ai/tlog", repo_type="dataset", token=tok) if f.startswith("data/clean-"))
rnd, flg, scores = [], [], []
for f in random.sample(files, 4):
    t = pq.read_table(hf_hub_download("tarteel-ai/tlog", f, repo_type="dataset", token=tok))
    for k in random.sample(range(t.num_rows), min(60, t.num_rows)):
        if len(rnd) >= 10 and len(flg) >= 10: break
        r = t.slice(k, 1).to_pylist()[0]
        try:
            name = os.path.basename(r["audio"]["path"]); s, a = name.split("_")[:2]
            words = ayah_word_phonemes(int(s), int(a))
            if not words or any(p not in pid for w in words for p in w): continue
            b = r["audio"]["bytes"]; audio = load(b)
            if not 1.5 <= len(audio) / 16000 <= 15: continue
            hidden, logp, length = encode(audio)
            ours = [p for w in words for p in w]
            probs = verifier(hidden, logp, length, [ours])[0]
            g = gop(logp, length, ours, [i for i, p in enumerate(ours) if alts(p)])
            wv, k2 = [], 0
            for wi, w in enumerate(words):
                pp = probs[k2:k2 + len(w)]; gg = [g.get(i) for i in range(k2, k2 + len(w)) if g.get(i) is not None]; k2 += len(w)
                wv.append((wi, max(pp), max(gg) if gg else None))
            cand = [x for x in wv if len(words[x[0]]) >= 2 and x[2] is not None]
            flagged = [x for x in cand if x[1] >= .5 or x[2] > 0]
            if flagged and len(flg) < 10:
                x = random.choice(flagged); flg.append(1); stratum = "tlog_flagged"
            elif len(rnd) < 10 and cand:
                x = random.choice(cand); rnd.append(1); stratum = "tlog_random"
            else:
                continue
            cid = secrets.token_hex(5)
            emit(cid, "tarteel-ai/tlog", name, b, audio, words, x[0], {"surah": int(s), "ayah": int(a)})
            scores.append({"clip_id": cid, "stratum": stratum, "v3_max": round(x[1], 4), "gop_max": round(x[2], 3)})
        except Exception as e:
            print("skip", e)
json.dump(manifest, open("/kaggle/working/manifest.json", "w"), ensure_ascii=False, indent=0)
json.dump(scores, open("/kaggle/working/tlog_scores_PRIVATE.json", "w"), indent=0)
print("DONE", len(manifest), flush=True)
