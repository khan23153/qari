"""
Qari ML Recitation Engine
=========================

AI-powered recitation feedback engine for the Qari Quran Learning App.

Modules
-------
inference   : ASR (Whisper-Quran) and VAD
alignment   : Word-level Levenshtein alignment and Wav2Vec2 forced alignment
tajweed     : Tajweed rule checks and reference store
evaluation  : Scoring and precision evaluation framework
training    : Fine-tuning scripts for Whisper and tajweed classifiers
tests       : Unit tests for alignment, scoring, normalization, tajweed
"""

__version__ = "1.0.0"
__all__ = [
    "pipeline",
    "inference",
    "alignment",
    "tajweed",
    "evaluation",
    "training",
]
