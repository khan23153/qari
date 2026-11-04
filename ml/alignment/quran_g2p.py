"""Diacritised Arabic -> IqraEval phonemes, for the v3 pronunciation verifier.

The verifier (``ml/inference/pronunciation_verifier.py``) is told which
phonemes the reciter SHOULD say, in the exact symbol set and conventions of the
IqraEval data it was trained on. This module writes those phonemes from the
fully vowelled text. It is our own rule set (the phonetiser IqraEval used is
licensed non-commercial), checked against IqraEval's own reference phonemes
by ``ml/evaluation/check_quran_g2p.py``.

Conventions (read off IqraEval's ``phoneme_ref``):
  * one symbol per consonant, doubled for shadda: ``b`` / ``bb``; every hamza is ``<``;
  * short vowels ``a i u``, long ``aa ii uu``; a vowel next to an emphatic
    consonant is written upper case (``A I U``, ``AA II UU``);
  * tanween is not pronounced (fathatan + alif reads ``aa``); a word is read
    in connection with the next one, and the last word of the utterance is
    read in pause (its final short vowel drops);
  * hamzat al-wasl and the lam of a sun letter are silent; at the very start
    of an utterance hamzat al-wasl is ``<`` plus its vowel.

``phonemize(text)`` gives one flat list; ``phonemize_words(words)`` gives one
list per word (for folding verifier scores back onto words).
"""
from __future__ import annotations

import re
import unicodedata

FATHA, DAMMA, KASRA, SUKUN, SHADDA = "َ", "ُ", "ِ", "ْ", "ّ"
FATHATAN, DAMMATAN, KASRATAN = "ً", "ٌ", "ٍ"
DAGGER_ALIF = "ٰ"
VOWEL_MARK = {FATHA: "a", DAMMA: "u", KASRA: "i"}
TANWEEN = {FATHATAN: "a", DAMMATAN: "u", KASRATAN: "i"}

CONSONANT = {
    "ب": "b", "ت": "t", "ث": "^", "ج": "j", "ح": "H", "خ": "x", "د": "d", "ذ": "*",
    "ر": "r", "ز": "z", "س": "s", "ش": "$", "ص": "S", "ض": "D", "ط": "T", "ظ": "Z",
    "ع": "E", "غ": "g", "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",
    "ه": "h", "و": "w", "ي": "y", "ى": "y",
    "ء": "<", "أ": "<", "إ": "<", "ؤ": "<", "ئ": "<",
}
SUN = set("تثدذرزسشصضطظلن")
# A vowel right after these is "heavy" (upper case) ...
EMPHATIC_AFTER = {"S", "D", "T", "Z", "q", "x", "g"}
# ... and right before these.
EMPHATIC_BEFORE = {"S", "D", "T", "Z", "q"}

# Uthmani (Mushaf) spelling -> the plain vowelled spelling the rules expect.
_UTHMANI = [
    ("ٱ", "ا"),          # hamzat al-wasl
    ("ۡ", SUKUN),   # small high dotless head of khah = sukun
    ("ـ", ""),           # tatweel
]
_DROP = re.compile("[ؐ-ؚۖ-ۜ۟-۪ۨ-ۭٕٓٔ]")


# Words whose long aa is not written in plain spelling.
_HIDDEN_ALIF = {
    "هَذَا": "هَاذَا", "هَذِهِ": "هَاذِهِ", "هَذَانِ": "هَاذَانِ", "هَؤُلَاءِ": "هَاؤُلَاءِ",
    "ذَلِكَ": "ذَالِكَ", "ذَلِكُمْ": "ذَالِكُمْ", "لَكِنْ": "لَاكِنْ", "لَكِنَّ": "لَاكِنَّ",
    "لَكِنَّهُ": "لَاكِنَّهُ", "أُولَئِكَ": "أُولَائِكَ", "كَذَلِكَ": "كَذَالِكَ",
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    for a, b in _UTHMANI:
        text = text.replace(a, b)
    # آ after a vowelled letter is a long aa (Uthmani madd: مَآءً); at a word
    # start or after sukun it is hamza + aa (آمَنُوا، الْآخِرَة).
    text = re.sub("([\u0621-\u064a][\u0651]?[\u064e\u064b][\u0651]?)آ", "\\1ا", text)
    text = text.replace("آ", "ء" + FATHA + "ا")
    text = text.replace(DAGGER_ALIF, "")  # IqraEval reads the dagger alif short (lexicon below has the exceptions)
    for word, fixed in _HIDDEN_ALIF.items():
        text = re.sub(rf"(?<![\u0621-\u064a]){word}", fixed, text)
    text = _DROP.sub("", text)
    text = re.sub(r"[^ء-يً-ْٰ\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _letters(word: str) -> list[tuple[str, set]]:
    """[(base letter, {marks})] for one word."""
    out: list[tuple[str, set]] = []
    for ch in word:
        if "ً" <= ch <= "ْ" or ch == DAGGER_ALIF:
            if out:
                out[-1][1].add(ch)
        else:
            out.append((ch, set()))
    return out


def _word_units(word: str, *, utterance_start: bool, quran: bool = True) -> list[str]:
    """Phonemes of one word, before cross-word effects (pause, emphasis)."""
    tail: list[str] = []
    if word.endswith("َوْا"):
        word, tail = word[:-3], ["uu"]  # -aw + silent alif (waw al-jama'a): IqraEval writes a uu
    L = _letters(word)
    ph: list[str] = []
    i = 0
    while i < len(L):
        ch, marks = L[i]
        nxt = L[i + 1] if i + 1 < len(L) else None
        prev_vowel = ph[-1] if ph and ph[-1] in ("a", "i", "u") else None

        if ch == "ا":
            if i == 0:  # hamzat al-wasl
                v = marks & set(VOWEL_MARK)
                if v:
                    ph += ["<", VOWEL_MARK[next(iter(v))]]
                elif utterance_start and nxt and nxt[0] == "ل":
                    ph += ["<", "a"]  # the article opening an utterance is voiced
                i += 1
                continue
            v = marks & set(VOWEL_MARK)
            if v:  # a vowelled alif inside a word is read as a hamza
                ph += ["<", VOWEL_MARK[next(iter(v))]]
                i += 1
                continue
            if (not marks and nxt and nxt[0] == "ل" and i + 2 < len(L) and L[i - 1][0] in "وفبكل"
                    and (not nxt[1] & set(VOWEL_MARK) or SHADDA in nxt[1])):
                i += 1  # al- after a prefix (wa-, fa-, bi-, ka-): wasl alif, silent
                continue
            if prev_vowel == "a" or FATHATAN in (L[i - 1][1] if i else set()):
                ph[-1:] = ["aa"] if prev_vowel == "a" else ph[-1:]
                if prev_vowel != "a":
                    ph.append("aa")
            # waw al-jama'a alif and other silent alifs: nothing
            i += 1
            continue

        if ch == "ة":
            if marks & set(VOWEL_MARK):
                ph.append("t")
                ph.append(VOWEL_MARK[next(iter(marks & set(VOWEL_MARK)))])
            elif marks & set(TANWEEN):
                if quran:
                    ph += ["t", TANWEEN[next(iter(marks & set(TANWEEN)))], "n"]
            else:
                ph.append("t")
            i += 1
            continue

        if ch == "ل" and not (marks & (set(VOWEL_MARK) | {SHADDA})) and nxt and nxt[0] in SUN and SHADDA in nxt[1]:
            i += 1  # lam of al- before a sun letter: silent (the sun letter is doubled)
            continue

        if ch in ("و", "ي") and marks == {SUKUN} and prev_vowel == ("u" if ch == "و" else "i"):
            ph[-1] = prev_vowel * 2; i += 1; continue  # long vowel written with an explicit sukun
        if ch in ("و", "ي", "ى") and not marks & (set(VOWEL_MARK) | {SHADDA, SUKUN} | set(TANWEEN)):
            if ch in ("ى",) and prev_vowel == "a":
                ph[-1] = "aa"; i += 1; continue
            if ch == "و" and prev_vowel == "u":
                ph[-1] = "uu"; i += 1; continue
            if ch in ("ي", "ى") and prev_vowel == "i":
                ph[-1] = "ii"; i += 1; continue
            if ch == "ى":
                ph[-1:] = ph[-1:]  # alif maqsura after a consonant: rare; treat as aa
                ph.append("aa"); i += 1; continue

        if ch in CONSONANT:
            c = CONSONANT[ch]
            if SHADDA in marks:
                # kasra + shadda-ya / damma + shadda-waw: the long vowel then the glide
                if c == "y" and prev_vowel == "i":
                    ph[-1] = "ii"; ph.append("y")
                elif c == "w" and prev_vowel == "u":
                    ph[-1] = "uu"; ph.append("w")
                else:
                    ph.append(c + c)
            else:
                ph.append(c)
            v = marks & set(VOWEL_MARK)
            if v:
                ph.append(VOWEL_MARK[next(iter(v))])
            elif ch == "إ" and not marks & ({SUKUN} | set(TANWEEN)):
                ph.append("i")  # hamza under alif always carries kasra
            elif marks & set(TANWEEN):
                t = next(iter(marks & set(TANWEEN)))
                if quran:  # Mushaf style (IqraEval QuranMB / IS26): tanween is a vowel + n
                    ph += [TANWEEN[t], "n"]
                    if t == FATHATAN and nxt and nxt[0] in ("ا", "ى"):
                        ph.append("aa"); i += 1  # IqraEval also voices the alif after fathatan
                elif t == FATHATAN and nxt and nxt[0] in ("ا", "ى"):
                    ph.append("aa"); i += 1  # consume the alif
                elif t == FATHATAN:
                    ph.append("aa")
            if DAGGER_ALIF in marks:  # dagger alif: a long aa (IqraEval keeps al-rahman short)
                if ph and ph[-1] == "a":
                    ph[-1] = "aa"
                else:
                    ph.append("aa")
            i += 1
            continue
        i += 1
    return ph + tail


def _pause(ph: list[str], word: str = "") -> list[str]:
    """Last word of the utterance: its final short vowel is not pronounced."""
    if len(ph) >= 3 and ph[-3:] in (["i", "y", "a"], ["u", "w", "a"]):
        return ph[:-3] + [ph[-3] * 2]  # -iya / -uwa in pause: a long vowel
    if re.sub("[\u064b-\u0652]", "", word).endswith("ة"):
        # ta marbuta in pause: the 'a' before it stays, the ta (and its vowel) go
        while ph and ph[-1] in ("t", "a", "i", "u") and not (ph[-1] == "a" and (len(ph) < 2 or ph[-2] != "t")):
            if ph[-1] == "t":
                ph = ph[:-1]
                break
            ph = ph[:-1]
        return ph
    if ph and ph[-1] in ("a", "i", "u"):
        return ph[:-1]
    return ph


def _emphasis(ph: list[str], word_end: set[int]) -> list[str]:
    """``word_end``: indices that are the last phoneme of a word."""
    out = list(ph)
    base = lambda s: s[0] if s else s
    for k, p in enumerate(out):
        if p in ("a", "i", "u", "aa", "ii", "uu"):
            before = out[k - 1] if k else ""
            after = out[k + 1] if k + 1 < len(out) and k not in word_end else ""
            if base(before) in EMPHATIC_AFTER or (p in ("a", "i", "u", "aa") and base(after) in EMPHATIC_BEFORE):
                out[k] = p.upper()
    return out


def phonemize_words(words: list[str], *, style: str = "quran") -> list[list[str]]:
    """One phoneme list per word, the words read as one connected utterance.

    ``style="quran"`` (default) follows IqraEval's Quran sets (QuranMB, IS26):
    every vowel and tanween pronounced, no pause form. ``style="sentence"``
    follows Iqra_train's sentences: tanween dropped, last word in pause.
    """
    quran = style == "quran"
    norm = [normalize(w) for w in words]
    per = [_word_units(w, utterance_start=(k == 0), quran=quran) for k, w in enumerate(norm)]
    if per and not quran:
        per[-1] = _pause(per[-1], norm[-1])
    # emphasis looks across word boundaries
    flat = [p for w in per for p in w]
    ends, k = set(), 0
    for w in per:
        k += len(w)
        if w:
            ends.add(k - 1)
    flat = _emphasis(flat, ends)
    out, k = [], 0
    for w in per:
        out.append(flat[k:k + len(w)])
        k += len(w)
    return out


def phonemize(text: str, *, style: str = "quran") -> list[str]:
    return [p for w in phonemize_words(normalize(text).split(), style=style) for p in w]


# ---------------------------------------------------------------------------
# Precomputed Quran lexicon (built by scripts/build_quran_phonemes.py from the
# plain vowelled text, which matches IqraEval's references best).
_LEXICON: dict | None = None


def ayah_word_phonemes(surah: int, ayah: int) -> list[list[str]] | None:
    """Phonemes for each word of an ayah (Mushaf word order), or None if unknown."""
    global _LEXICON
    if _LEXICON is None:
        import gzip
        import json
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / "assets" / "quran_phonemes.json.gz"
        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                raw = json.load(f)
            _LEXICON = {k: [w.split() for w in v] for k, v in raw["ayahs"].items()}
        except OSError:
            _LEXICON = {}
    return _LEXICON.get(f"{surah}:{ayah}")
