"""Does our Whisper model hear a wrong zabar/zer/pesh? Run on the server.

Decodes a recording with the independent, UNPROMPTED Whisper model (the live
vowel witness: no target text, condition_on_previous_text=False), prints its
raw diacritized output, and, given the expected text, the harakat verdict for
every expected word (letters aligned first, then vowels compared).

Inside the recitation container (ml/ is mounted at /app/ml):

    docker compose exec recitation-api python /app/ml/evaluation/probe_whisper_vowels.py \\
        --wav /tmp/qari_audio/anamtu.wav \\
        --expected "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ"

Record the ayah once correctly and once with a deliberate vowel mistake
(e.g. أَنْعَمْتُ). The witness is only useful if the mistake shows up in the
raw output: Whisper may "correct" vowels from what it learned.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import wave
from difflib import SequenceMatcher

from ml.alignment.harakat import compare_harakat
from ml.alignment.vowel_witness import has_short_vowel

_MARKS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭ]")


def _normalizer():
    try:
        from app.services.streaming_session import _normalize
        return _normalize
    except Exception:  # outside the API container
        return lambda t: _MARKS.sub("", t).translate(str.maketrans("أإآٱ", "اااا"))


def _load_wav(path: str):
    import numpy as np
    with wave.open(path, "rb") as wf:
        channels, width, rate = wf.getnchannels(), wf.getsampwidth(), wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    if width != 2:
        raise SystemExit("Expected 16-bit PCM WAV")
    audio = np.frombuffer(frames, dtype=np.int16).astype("float32") / 32768.0
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    return audio, rate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wav", required=True)
    parser.add_argument("--expected", default="", help="Expected ayah text with tashkeel")
    args = parser.parse_args()

    from ml.inference.faster_whisper_transcriber import get_transcriber

    audio, rate = _load_wav(args.wav)
    transcriber = get_transcriber()
    began = time.perf_counter()
    tokens, confidences = transcriber.transcribe_independent(audio, rate)
    seconds = time.perf_counter() - began
    marks = sum(1 for t in tokens for ch in t if "ً" <= ch <= "ْ")

    print(f"model: {transcriber.verify_model_dir}")
    print(f"audio: {len(audio) / rate:.2f}s  decode: {seconds:.2f}s")
    print("raw:", " ".join(tokens))
    print(f"tokens: {len(tokens)}  vowel marks: {marks}")

    report = {"raw": tokens, "confidences": confidences, "decode_seconds": round(seconds, 3)}
    if args.expected:
        normalize = _normalizer()
        expected = args.expected.split()
        exp_norm = [normalize(w) for w in expected]
        heard_norm = [normalize(t) for t in tokens]
        pairs = {}
        for block in SequenceMatcher(None, exp_norm, heard_norm, autojunk=False).get_matching_blocks():
            for k in range(block.size):
                pairs[block.a + k] = block.b + k
        verdicts = []
        for i, word in enumerate(expected):
            j = pairs.get(i)
            if j is None:
                verdict, heard = "not heard (letters differ or missing)", None
            else:
                heard = tokens[j]
                if not has_short_vowel(heard):
                    verdict = "heard, no vowel marks (cannot judge)"
                else:
                    result = compare_harakat(
                        word, heard,
                        is_ayah_end=i == len(expected) - 1,
                        next_word_spoken=(i + 1) in pairs,
                    )
                    verdict = ("RED: harakat differ" if result.mismatch
                               else "inconclusive" if result.inconclusive else "ok")
            verdicts.append({"expected": word, "heard": heard, "verdict": verdict})
            print(f"  {word:>16}  <-  {heard or '-':<16}  {verdict}")
        report["verdicts"] = verdicts
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
