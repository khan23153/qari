"""Tests for SM-2 spaced repetition algorithm."""
import pytest
from datetime import datetime, timedelta, timezone

from app.services.srs_service import sm2_update, GRADE_MAP


class TestSM2:
    def test_first_correct_grade_5(self):
        ef, interval, reps, due = sm2_update(2.5, 0, 0, 5)
        assert reps == 1
        assert interval == 1  # first repetition = 1 day
        assert ef > 2.5  # ease factor increases on perfect grade
        assert due > datetime.now(timezone.utc)

    def test_second_correct_grade_5(self):
        ef, interval, reps, due = sm2_update(2.6, 1, 1, 5)
        assert reps == 2
        assert interval == 6  # second repetition = 6 days

    def test_failed_resets(self):
        ef, interval, reps, due = sm2_update(2.5, 6, 3, 1)
        assert reps == 0
        assert interval == 0

    def test_ease_factor_minimum(self):
        ef, _, _, _ = sm2_update(1.3, 1, 1, 0)
        assert ef >= 1.3

    def test_grade_map(self):
        assert GRADE_MAP["bhool_gaya"] == 1
        assert GRADE_MAP["mushkil"] == 3
        assert GRADE_MAP["aasaan"] == 5
