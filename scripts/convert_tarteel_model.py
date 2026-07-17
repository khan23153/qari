#!/usr/bin/env python3
"""Convert tarteel-ai/whisper-base-ar-quran to CTranslate2 (INT8) for CPU.

The live recitation engine uses ``faster-whisper`` (CTranslate2 runtime) instead
of the heavy PyTorch Whisper, so it can run with low latency on a CPU-only VPS.
CTranslate2 cannot read a standard HuggingFace model directly — it must be
converted first. This script wraps the official ``ct2-transformers-converter``
CLI (provided by the ``ctranslate2`` package) and writes the optimized model to
``backend/recitation_api/models/tarteel-ct2-base`` (which the container mounts
at ``/app/models/tarteel-ct2-base``).

Requirements (only needed at conversion time, not at inference):
    pip install "transformers==4.39.3" torch ctranslate2

Usage:
    python scripts/convert_tarteel_model.py
    python scripts/convert_tarteel_model.py --model tarteel-ai/whisper-base-ar-quran \
        --output backend/recitation_api/models/tarteel-ct2-base --quantization int8

The container reads the output location from QARI_FASTERWHISPER_MODEL_DIR
(default /app/models/tarteel-ct2-base).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

# Resolve repo root (this file lives in <repo>/scripts).
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUTPUT = os.path.join(
    REPO_ROOT, "backend", "recitation_api", "models", "tarteel-ct2-base"
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--model",
        default="tarteel-ai/whisper-base-ar-quran",
        help="Source HuggingFace Whisper model to convert.",
    )
    p.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Output directory for the CTranslate2 model.",
    )
    p.add_argument(
        "--quantization",
        default="int8",
        choices=["int8", "int8_float16", "float16", "float32"],
        help="CTranslate2 quantization (int8 = smallest + fastest on CPU).",
    )
    p.add_argument(
        "--compute-type",
        default=None,
        help="Override the CTranslate2 compute_type used at inference "
        "(defaults to match --quantization).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    # The converter ships as the `ct2-transformers-converter` console script
    # (part of the `ctranslate2` package). Prefer it; fall back to invoking the
    # module path if the script isn't on PATH.
    cmd = [
        "ct2-transformers-converter",
        "--model",
        args.model,
        "--output_dir",
        args.output,
        "--quantization",
        args.quantization,
        "--copy_files",
        "preprocessor_config.json",
    ]
    print("Running:", " ".join(cmd), flush=True)
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("Falling back to `python -m ctranslate2.converters` ...", flush=True)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "ctranslate2.converters",
                "--model",
                args.model,
                "--output_dir",
                args.output,
                "--quantization",
                args.quantization,
                "--copy_files",
                "preprocessor_config.json",
            ],
            check=True,
        )

    # The source Whisper model ships the classic GPT2-style tokenizer
    # (vocab.json + merges.txt), not a fast `tokenizer.json`. faster-whisper
    # requires `tokenizer.json` next to the CT2 weights, so generate it from
    # the source tokenizer (this also embeds the Arabic normalizer).
    print("Generating tokenizer.json for faster-whisper ...", flush=True)
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(args.model)
    tok.save_pretrained(args.output, legacy_format=False)

    print(
        "\nDone. Model written to:\n ",
        args.output,
        "\nMount this into the recitation-api container at /app/models "
        "(or set QARI_FASTERWHISPER_MODEL_DIR).",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
