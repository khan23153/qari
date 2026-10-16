"""Release checks using real PCM and the production live-recitation session."""

import argparse
import asyncio
import json
import os
import sys
import wave
from pathlib import Path


def release_checks(results: dict) -> dict:
    return {
        "phone_recall": results["phone_fatihah"]["matched"] >= 27,
        "reference_fatihah_recall": results["reference_fatihah"]["matched"] >= 27,
        "reference_ikhlas_recall": results["reference_ikhlas"]["matched"] >= 14,
        "no_false_confirmed_mistakes": all(
            results[name]["confirmed_errors"] == 0
            for name in ("phone_fatihah", "reference_fatihah", "reference_ikhlas")
        ),
        "silence_no_reveal": results["silence"]["events"] == 0,
        "wrong_surah_no_completion": results["wrong_surah"]["max_cursor"] < 29
            and results["wrong_surah"]["matched"] <= 7,
    }


async def evaluate(model: Path, fixture_root: Path, source_root: Path) -> dict:
    os.environ.update({
        "QARI_JWT_SECRET_KEY": "isolated-model-evaluation-key-no-production-access",
        "QARI_ENVIRONMENT": "test", "QARI_ML_USE_STUB": "false",
        "QARI_EVIDENCE_POLICY": "tier2", "QARI_FASTERWHISPER_THREADS": "2",
        "QARI_FASTERWHISPER_MODEL_DIR": str(model),
        "QARI_FASTERWHISPER_VERIFY_MODEL_DIR": str(model),
        "QARI_REFERENCE_DATA_DIR": str(source_root / "backend/recitation_api/reference_data"),
        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
    })
    sys.path.insert(0, str(source_root / "backend/recitation_api"))
    from app.services.streaming_session import StreamingRecitationSession

    def pcm(name):
        with wave.open(str(fixture_root / name), "rb") as f:
            if (f.getframerate(), f.getnchannels(), f.getsampwidth()) != (16000, 1, 2):
                raise ValueError("Release fixtures must be mono PCM16 at 16 kHz")
            return f.readframes(f.getnframes())

    phone = pcm("phone_fatihah.wav")
    ikhlas = pcm("ikhlas.wav")
    cases = [
        ("phone_fatihah", 1, 7, phone),
        ("reference_fatihah", 1, 7, pcm("fatihah.wav")),
        ("silence", 1, 7, bytes(len(phone))),
        ("wrong_surah", 1, 7, ikhlas),
        ("reference_ikhlas", 112, 4, ikhlas),
    ]
    results = {}
    for name, surah, ayah_to, data in cases:
        session = StreamingRecitationSession(surah=surah, ayah_to=ayah_to)
        session.load_reference()
        events = []
        max_cursor = 0
        for start in range(0, len(data), 9600):
            session.add_audio(data[start:start + 9600])
            events.extend(await session.maybe_transcribe())
            max_cursor = max(max_cursor, session._matcher._cursor)
        events.extend(await session.maybe_transcribe(force=True))
        matches = {e["word_index"] for e in events if e["status"] == "match"}
        confirmed_errors = {e["word_index"] for e in events
                            if e["status"] == "error_skipped" and e.get("evidence_confirmed") is True}
        results[name] = {
            "matched": len(matches), "word_count": len(session.reference_words),
            "cursor": session._matcher._cursor, "events": len(events),
            "max_cursor": max(max_cursor, session._matcher._cursor),
            "confirmed_errors": len(confirmed_errors),
        }
        print(json.dumps({"case": name, **results[name]}), flush=True)
    checks = release_checks(results)
    return {"pass": all(checks.values()), "checks": checks, "cases": results,
            "vps_latency_verified": False}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--fixtures", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    report = asyncio.run(evaluate(args.model, args.fixtures, args.source))
    args.output.write_text(json.dumps(report, indent=2) + "\n")
