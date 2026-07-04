"""
ETL validators: row counts, checksums, and diff against previous loads.

The validators enforce the **mirror strategy**: the Quranic text in our
database must be byte-for-byte identical to the canonical source.  Any
diff in Quranic text (Uthmani or Imlaei) causes the pipeline to **FAIL
loudly** — no silent updates, no partial loads.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Result of a validation check."""

    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge two results (both must pass for the merged result to pass)."""
        return ValidationResult(
            passed=self.passed and other.passed,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            metadata={**self.metadata, **other.metadata},
        )

    def __bool__(self) -> bool:
        return self.passed


@dataclass
class DiffResult:
    """Result of diffing against a previous load."""

    identical: bool
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[Tuple[str, str, str]] = field(default_factory=list)  # (verse_key, old, new)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class ETLValidator:
    """Validate ETL outputs: row counts, checksums, and text diffs.

    Parameters
    ----------
    expected_surahs:
        Expected number of surahs (default 114).
    expected_ayahs:
        Expected number of ayahs (default 6,236).
    expected_words:
        Expected number of words (default 77,430).
    """

    def __init__(
        self,
        expected_surahs: int = 114,
        expected_ayahs: int = 6_236,
        expected_words: int = 77_430,
    ) -> None:
        self.expected_surahs = expected_surahs
        self.expected_ayahs = expected_ayahs
        self.expected_words = expected_words

    # ------------------------------------------------------------------
    # Row count validation
    # ------------------------------------------------------------------

    def validate_row_counts(
        self,
        surahs: int,
        ayahs: int,
        words: int,
    ) -> ValidationResult:
        """Validate that row counts match expected canonical counts.

        Parameters
        ----------
        surahs:
            Number of surahs loaded.
        ayahs:
            Number of ayahs loaded.
        words:
            Number of words loaded.

        Returns
        -------
        ``ValidationResult`` with ``passed=True`` if all counts match.
        Any mismatch is an error (not a warning).
        """
        errors: List[str] = []
        metadata: Dict[str, Any] = {
            "surahs": {"expected": self.expected_surahs, "actual": surahs},
            "ayahs": {"expected": self.expected_ayahs, "actual": ayahs},
            "words": {"expected": self.expected_words, "actual": words},
        }

        if surahs != self.expected_surahs:
            errors.append(
                f"Surah count mismatch: expected {self.expected_surahs}, got {surahs}"
            )

        if ayahs != self.expected_ayahs:
            errors.append(
                f"Ayah count mismatch: expected {self.expected_ayahs}, got {ayahs}"
            )

        if words != self.expected_words:
            errors.append(
                f"Word count mismatch: expected {self.expected_words}, got {words}"
            )

        passed = len(errors) == 0
        result = ValidationResult(passed=passed, errors=errors, metadata=metadata)

        if passed:
            logger.info("row_counts_validated", status="PASS", **metadata)
        else:
            logger.error("row_counts_validated", status="FAIL", errors=errors, **metadata)

        return result

    # ------------------------------------------------------------------
    # Checksum computation
    # ------------------------------------------------------------------

    @staticmethod
    def compute_checksum(text: str) -> str:
        """Compute SHA-256 checksum of a text block."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def validate_checksums(
        self,
        text_blocks: Dict[str, str],
    ) -> Dict[str, str]:
        """Compute and validate SHA-256 checksums of Quranic text blocks.

        Parameters
        ----------
        text_blocks:
            Dict mapping verse_key → Quranic text (Uthmani or Imlaei).

        Returns
        -------
        Dict mapping verse_key → SHA-256 hex digest.

        Raises
        ------
        ValueError
            If any text block is empty or None.
        """
        checksums: Dict[str, str] = {}

        for verse_key, text in text_blocks.items():
            if not text:
                raise ValueError(f"Empty text for verse {verse_key}")
            checksums[verse_key] = self.compute_checksum(text)

        logger.info("checksums_computed", count=len(checksums))
        return checksums

    # ------------------------------------------------------------------
    # Diff against previous load
    # ------------------------------------------------------------------

    def diff_against_previous(
        self,
        new_checksums: Dict[str, str],
        previous_checksums: Dict[str, str],
    ) -> DiffResult:
        """Diff new checksums against the previous load.

        **Any change in Quranic text checksum is a hard failure.**  The
        pipeline must not proceed if any verse's checksum differs from the
        previous load.  New verses (added) and removed verses are reported
        as warnings but do not cause a failure by themselves (they may
        indicate a first load or a schema change).

        Parameters
        ----------
        new_checksums:
            Dict mapping verse_key → checksum for the current load.
        previous_checksums:
            Dict mapping verse_key → checksum for the previous load.

        Returns
        -------
        ``DiffResult`` with ``identical=True`` if no Quranic text changed.
        """
        new_keys = set(new_checksums.keys())
        old_keys = set(previous_checksums.keys())

        added = sorted(new_keys - old_keys)
        removed = sorted(old_keys - new_keys)
        changed: List[Tuple[str, str, str]] = []

        for key in sorted(new_keys & old_keys):
            new_sum = new_checksums[key]
            old_sum = previous_checksums[key]
            if new_sum != old_sum:
                changed.append((key, old_sum, new_sum))

        identical = len(changed) == 0

        result = DiffResult(
            identical=identical,
            added=added,
            removed=removed,
            changed=changed,
            metadata={
                "new_count": len(new_keys),
                "old_count": len(old_keys),
                "added_count": len(added),
                "removed_count": len(removed),
                "changed_count": len(changed),
            },
        )

        if identical:
            logger.info(
                "diff_passed",
                added=len(added),
                removed=len(removed),
                changed=0,
            )
        else:
            logger.error(
                "diff_failed",
                changed_count=len(changed),
                sample_changes=changed[:5],
                added=len(added),
                removed=len(removed),
            )

        return result

    # ------------------------------------------------------------------
    # Full validation (convenience)
    # ------------------------------------------------------------------

    def validate_all(
        self,
        surah_count: int,
        ayah_count: int,
        word_count: int,
        uthmani_texts: Dict[str, str],
        imlaei_texts: Dict[str, str],
        previous_uthmani: Optional[Dict[str, str]] = None,
        previous_imlaei: Optional[Dict[str, str]] = None,
    ) -> Tuple[ValidationResult, Dict[str, str], Dict[str, str]]:
        """Run all validations in sequence.

        Returns
        -------
        Tuple of (combined ValidationResult, uthmani_checksums, imlaei_checksums).
        """
        # 1. Row counts
        count_result = self.validate_row_counts(surah_count, ayah_count, word_count)

        # 2. Checksums
        uthmani_checksums = self.validate_checksums(uthmani_texts)
        imlaei_checksums = self.validate_checksums(imlaei_texts)

        # 3. Diff (only if previous data exists)
        diff_result = ValidationResult(passed=True, metadata={})
        if previous_uthmani:
            d = self.diff_against_previous(uthmani_checksums, previous_uthmani)
            if not d.identical:
                diff_result = ValidationResult(
                    passed=False,
                    errors=[
                        f"Uthmani text changed for {len(d.changed)} verses: "
                        f"{[c[0] for c in d.changed[:5]]}..."
                    ],
                    metadata={"uthmani_diff": d.metadata},
                )
        if previous_imlaei:
            d = self.diff_against_previous(imlaei_checksums, previous_imlaei)
            if not d.identical:
                diff_result = diff_result.merge(ValidationResult(
                    passed=False,
                    errors=[
                        f"Imlaei text changed for {len(d.changed)} verses: "
                        f"{[c[0] for c in d.changed[:5]]}..."
                    ],
                    metadata={"imlaei_diff": d.metadata},
                ))

        combined = count_result.merge(diff_result)
        return combined, uthmani_checksums, imlaei_checksums
