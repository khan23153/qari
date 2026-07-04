"""
Reference Store — stores expected phonemes, reference alignments, and
tajweed annotation positions per ayah (Quran verse).

This module provides an in-memory and file-backed store that maps
(surah, ayah) → reference data including:
  - Expected word sequence (normalized Arabic)
  - Expected phoneme sequences per word
  - Reference qari alignment (professional reciter timestamps)
  - Tajweed annotation positions (which letters have which rules)

The store can be populated from JSON files or programmatically.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class TajweedAnnotation:
    """A single tajweed rule annotation at a specific position in a word."""
    rule: str           # "ghunnah", "qalqalah", "madd", "ikhfa", "idgham"
    letter: str         # The Arabic letter
    position: int       # Character position within the word (0-indexed)
    context: str = ""   # Additional context (e.g., "shadda", "sakin")
    expected_duration_ms: int = 0  # Expected duration for duration-based rules


@dataclass
class WordReference:
    """Reference data for a single word in an ayah."""
    word: str                           # Normalized Arabic word
    phonemes: list[str] = field(default_factory=list)  # Expected phoneme sequence
    tajweed_checks: list[TajweedAnnotation] = field(default_factory=list)
    ref_start_ms: int = 0              # Reference qari start time
    ref_end_ms: int = 0                # Reference qari end time


@dataclass
class AyahReference:
    """Complete reference data for a single ayah (verse)."""
    surah: int
    ayah: int
    text: str                           # Full ayah text (with diacritics)
    normalized_text: str                # Normalized text (no diacritics)
    words: list[WordReference] = field(default_factory=list)
    reference_audio_url: str = ""       # URL to reference qari audio
    reference_qari: str = ""            # Name of reference reciter

    @property
    def word_count(self) -> int:
        return len(self.words)

    @property
    def expected_words(self) -> list[str]:
        """List of normalized expected words."""
        return [w.word for w in self.words]

    @property
    def tajweed_positions(self) -> list[dict]:
        """
        Per-word tajweed annotations in the format expected by TajweedChecker.

        Returns a list (one per word) of dicts with a "checks" key containing
        a list of {rule, letter, position} dicts.
        """
        result: list[dict] = []
        for word_ref in self.words:
            checks = [
                {
                    "rule": ann.rule,
                    "letter": ann.letter,
                    "position": ann.position,
                    "expected_duration_ms": ann.expected_duration_ms,
                }
                for ann in word_ref.tajweed_checks
            ]
            result.append({"checks": checks})
        return result


# ── Reference Store ──────────────────────────────────────────────────────────

class ReferenceStore:
    """
    Store for Quran reference data: expected text, phonemes, alignments,
    and tajweed positions per ayah.

    Data is keyed by (surah, ayah) and can be loaded from JSON files
    or added programmatically.

    Parameters
    ----------
    data_dir : str or Path, optional
        Directory containing JSON reference files. Files should be named
        ``{surah}_{ayah}.json`` and contain the serialized AyahReference.
    """

    def __init__(self, data_dir: Optional[str | Path] = None) -> None:
        self._store: dict[tuple[int, int], AyahReference] = {}
        self._data_dir = Path(data_dir) if data_dir else None

        if self._data_dir and self._data_dir.exists():
            self._load_from_dir(self._data_dir)

    def _load_from_dir(self, directory: Path) -> None:
        """Load all JSON reference files from a directory."""
        for json_file in directory.glob("*.json"):
            try:
                surah, ayah = json_file.stem.split("_")
                self.load_from_file(json_file, int(surah), int(ayah))
            except (ValueError, json.JSONDecodeError) as e:
                logger.warning("Could not load reference file %s: %s", json_file, e)

    def load_from_file(self, filepath: str | Path, surah: int, ayah: int) -> None:
        """Load a single ayah reference from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        ref = self._deserialize_ayah(data, surah, ayah)
        self._store[(surah, ayah)] = ref

    def _deserialize_ayah(self, data: dict, surah: int, ayah: int) -> AyahReference:
        """Deserialize a JSON dict into an AyahReference."""
        words: list[WordReference] = []
        for w_data in data.get("words", []):
            tajweed_checks = [
                TajweedAnnotation(
                    rule=tj["rule"],
                    letter=tj["letter"],
                    position=tj["position"],
                    context=tj.get("context", ""),
                    expected_duration_ms=tj.get("expected_duration_ms", 0),
                )
                for tj in w_data.get("tajweed_checks", [])
            ]
            words.append(WordReference(
                word=w_data["word"],
                phonemes=w_data.get("phonemes", []),
                tajweed_checks=tajweed_checks,
                ref_start_ms=w_data.get("ref_start_ms", 0),
                ref_end_ms=w_data.get("ref_end_ms", 0),
            ))

        return AyahReference(
            surah=surah,
            ayah=ayah,
            text=data.get("text", ""),
            normalized_text=data.get("normalized_text", ""),
            words=words,
            reference_audio_url=data.get("reference_audio_url", ""),
            reference_qari=data.get("reference_qari", ""),
        )

    def add(self, reference: AyahReference) -> None:
        """Add or replace a reference for an ayah."""
        self._store[(reference.surah, reference.ayah)] = reference

    def get(self, surah: int, ayah: int) -> Optional[AyahReference]:
        """Get the reference for a specific ayah. Returns None if not found."""
        return self._store.get((surah, ayah))

    def has(self, surah: int, ayah: int) -> bool:
        """Check if a reference exists for the given ayah."""
        return (surah, ayah) in self._store

    def get_expected_words(self, surah: int, ayah: int) -> list[str]:
        """Get the expected word sequence for an ayah."""
        ref = self.get(surah, ayah)
        if ref is None:
            return []
        return ref.expected_words

    def get_tajweed_positions(self, surah: int, ayah: int) -> list[dict]:
        """Get tajweed annotation positions for an ayah."""
        ref = self.get(surah, ayah)
        if ref is None:
            return []
        return ref.tajweed_positions

    def get_reference_phonemes(self, surah: int, ayah: int) -> list[list[str]]:
        """Get expected phoneme sequences per word for an ayah."""
        ref = self.get(surah, ayah)
        if ref is None:
            return []
        return [w.phonemes for w in ref.words]

    def get_reference_audio_url(self, surah: int, ayah: int) -> str:
        """Get the reference qari audio URL for an ayah."""
        ref = self.get(surah, ayah)
        if ref is None:
            return ""
        return ref.reference_audio_url

    def list_ayahs(self) -> list[tuple[int, int]]:
        """List all (surah, ayah) pairs in the store."""
        return sorted(self._store.keys())

    def save_to_file(self, surah: int, ayah: int, filepath: str | Path) -> None:
        """Save a single ayah reference to a JSON file."""
        ref = self.get(surah, ayah)
        if ref is None:
            raise KeyError(f"No reference for ({surah}, {ayah})")

        data = self._serialize_ayah(ref)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _serialize_ayah(self, ref: AyahReference) -> dict:
        """Serialize an AyahReference to a JSON-compatible dict."""
        return {
            "surah": ref.surah,
            "ayah": ref.ayah,
            "text": ref.text,
            "normalized_text": ref.normalized_text,
            "reference_audio_url": ref.reference_audio_url,
            "reference_qari": ref.reference_qari,
            "words": [
                {
                    "word": w.word,
                    "phonemes": w.phonemes,
                    "tajweed_checks": [
                        {
                            "rule": tj.rule,
                            "letter": tj.letter,
                            "position": tj.position,
                            "context": tj.context,
                            "expected_duration_ms": tj.expected_duration_ms,
                        }
                        for tj in w.tajweed_checks
                    ],
                    "ref_start_ms": w.ref_start_ms,
                    "ref_end_ms": w.ref_end_ms,
                }
                for w in ref.words
            ],
        }

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: tuple[int, int]) -> bool:
        return key in self._store
