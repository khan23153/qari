"""Offline ("shadow") pronunciation scoring on an isolated worker.

The live server never loads an unqualified pronunciation model. With
``QARI_PRON_SHADOW_EXPORT=1`` it only writes ``pron_inputs.json`` (word windows
and expected phonemes, no model) next to each session's ``audio.wav``. Copy
those session folders to a separate machine (or a Kaggle job) and run:

    python scripts/pron_shadow_worker.py /path/to/sessions /path/to/safha-mdd-v3

Each scored session gets ``pron_shadow.json`` with per-word and per-phoneme
scores, the model fingerprint and threshold. Nothing here is shown to users;
it is raw material for human review and evaluation.
"""
from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def read_wav(path: Path):
    import numpy as np
    with wave.open(str(path), "rb") as wf:
        if wf.getsampwidth() != 2 or wf.getnchannels() != 1:
            raise ValueError("expected 16-bit mono")
        rate = wf.getframerate()
        pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype="<i2").astype("float32") / 32768.0
    return pcm, rate


def score_session(folder: Path, verifier, fingerprint: str) -> dict | None:
    from ml.inference.pronunciation_verifier import word_verdicts
    inputs = json.loads((folder / "pron_inputs.json").read_text())
    audio, rate = read_wav(folder / inputs.get("audio", "audio.wav"))
    if rate != 16000:
        return None
    words = []
    for run in inputs["runs"]:
        start, end = run["window"]
        window = audio[int(start * rate):int(end * rate)]
        flat = [p for w in run["phonemes"] for p in w]
        result = verifier.score(window, flat)
        scores = word_verdicts(run["phonemes"], result)
        k = 0
        for index, word, phonemes, span, score in zip(run["word_indices"], run["words"], run["phonemes"],
                                                      run["spans"], scores):
            probs = result.probabilities[k:k + len(phonemes)]
            k += len(phonemes)
            words.append({"word_index": index, "word": word, "surah": run.get("surah"), "ayah": run.get("ayah"),
                          "phonemes": phonemes, "phoneme_scores": [round(p, 4) for p in probs],
                          "score": None if score is None else round(score, 4),
                          "flagged": score is not None and score >= result.threshold,
                          "audio_span_ms": [int(span[0] * 1000), int(span[1] * 1000)]})
    return {"schema": 1, "session_id": inputs.get("session_id"), "model_sha256": fingerprint,
            "threshold": verifier.threshold, "words": words}


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2:
        print(__doc__)
        return 2
    sessions, model_dir = Path(argv[0]), Path(argv[1])
    from ml.inference.pronunciation_verifier import PronunciationVerifier
    verifier = PronunciationVerifier(model_dir, threshold=0.5).load()
    fingerprint = verifier.fingerprint(extra=("pron_shadow_worker",))
    done = 0
    for inputs in sorted(sessions.glob("*/pron_inputs.json")):
        folder = inputs.parent
        if (folder / "pron_shadow.json").exists():
            continue
        try:
            out = score_session(folder, verifier, fingerprint)
        except Exception as exc:  # keep going; one bad recording must not stop the batch
            print(f"skip {folder.name}: {exc}", file=sys.stderr)
            continue
        if out is not None:
            (folder / "pron_shadow.json").write_text(json.dumps(out, ensure_ascii=False))
            done += 1
    print(f"scored {done} sessions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
