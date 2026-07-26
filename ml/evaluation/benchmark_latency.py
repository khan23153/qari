"""
Live-inference latency benchmark for the streaming recitation engine.

The live tracker re-transcribes a ~6 s sliding audio window every ~1.2 s of
new audio (backend/recitation_api/app/services/streaming_session.py). For
tracking to feel real-time, ONE window transcription must finish comfortably
inside that 1.2 s budget on the deployment machine — otherwise windows queue
up and the word reveal lags behind the reciter.

Run this ON THE VPS (or wherever the recitation-api container runs) before
switching to a new live model:

    python -m ml.evaluation.benchmark_latency \\
        --model_dir backend/recitation_api/models/tarteel-ct2-tiny \\
        --wav /path/to/some_recitation_16k.wav

Without --wav it benchmarks on synthetic speech-shaped noise, which is a
fair *upper-bound* smoke test (real speech decodes a similar token count).

Interpretation:
    p95 <= 0.8 s  → comfortable, ship it
    p95 <= 1.2 s  → works, no headroom (watch concurrent sessions)
    p95  > 1.2 s  → the tracker WILL lag — use a smaller model / more
                    cpu_threads / smaller window
"""

from __future__ import annotations

import argparse
import statistics
import time

import numpy as np

WINDOW_S = 6.0
BUDGET_S = 1.2
SAMPLE_RATE = 16000


def make_test_signal(seconds: float, seed: int = 7) -> np.ndarray:
    """Speech-shaped noise: band-limited, amplitude-modulated at syllable
    rate (~4 Hz) so the decoder does real work instead of instant-silence."""
    rng = np.random.default_rng(seed)
    n = int(seconds * SAMPLE_RATE)
    noise = rng.standard_normal(n).astype(np.float32)
    # crude 100–3000 Hz band-pass via FFT mask
    spec = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(n, 1 / SAMPLE_RATE)
    spec[(freqs < 100) | (freqs > 3000)] = 0
    shaped = np.fft.irfft(spec, n).astype(np.float32)
    t = np.arange(n) / SAMPLE_RATE
    envelope = (0.55 + 0.45 * np.sin(2 * np.pi * 4.0 * t)).astype(np.float32)
    sig = shaped * envelope
    return (0.1 * sig / (np.abs(sig).max() + 1e-9)).astype(np.float32)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model_dir", default=None,
                    help="CT2 model dir (default: QARI_FASTERWHISPER_MODEL_DIR)")
    ap.add_argument("--wav", default=None, help="Real 16k mono WAV to slice")
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--window_s", type=float, default=WINDOW_S)
    args = ap.parse_args()

    from ml.inference.faster_whisper_transcriber import FasterWhisperTranscriber

    if args.wav:
        import soundfile as sf

        audio, sr = sf.read(args.wav, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        assert sr == SAMPLE_RATE, f"need 16k WAV, got {sr}"
    else:
        audio = make_test_signal(args.window_s * 2)
        print("(no --wav given: using synthetic speech-shaped noise)")

    win = int(args.window_s * SAMPLE_RATE)
    t = FasterWhisperTranscriber(model_dir=args.model_dir)
    t.load()

    # Warm-up (first decode pays one-off allocation costs).
    t.transcribe(audio[:win])

    times: list[float] = []
    for i in range(args.rounds):
        start = (i * win // 2) % max(1, len(audio) - win)
        chunk = audio[start : start + win]
        t0 = time.perf_counter()
        words, _ = t.transcribe(chunk)
        dt = time.perf_counter() - t0
        times.append(dt)
        print(f"  round {i + 1:2d}: {dt:.3f}s  ({len(words)} words)")

    times.sort()
    p50 = statistics.median(times)
    p95 = times[max(0, int(len(times) * 0.95) - 1)]
    rtf = p50 / args.window_s
    print(f"\nwindow={args.window_s:.1f}s  rounds={args.rounds}")
    print(f"p50={p50:.3f}s  p95={p95:.3f}s  RTF={rtf:.2f}  budget={BUDGET_S}s")
    if p95 <= 0.8:
        print("VERDICT: comfortable — ship it.")
    elif p95 <= BUDGET_S:
        print("VERDICT: OK, but no headroom — watch concurrent sessions.")
    else:
        print("VERDICT: TOO SLOW — live tracking will lag. Use a smaller "
              "model, more cpu_threads, or a shorter window.")


if __name__ == "__main__":
    main()
