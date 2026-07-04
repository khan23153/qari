"""SM-2 spaced repetition algorithm tests."""

from datetime import datetime, timedelta, timezone

import pytest

from app.services.srs_service import calculate_sm2, SM2Result


class TestSM2Algorithm:
    """Test the SM-2 implementation against known scenarios."""

    def test_perfect_grade_first_review(self):
        """First review with grade 5: repetitions=1, interval=1."""
        result = calculate_sm2(
            grade=5,
            easiness=2.5,
            repetitions=0,
            interval=1,
        )
        assert result.new_repetitions == 1
        assert result.new_interval == 1
        assert result.new_easiness == 2.5  # EF stays at max for grade 5
        assert not result.is_suspended

    def test_good_grade_second_review(self):
        """Second review with grade 4: repetitions=2, interval=6."""
        result = calculate_sm2(
            grade=4,
            easiness=2.5,
            repetitions=1,
            interval=1,
        )
        assert result.new_repetitions == 2
        assert result.new_interval == 6  # SM-2 fixed second interval
        assert result.new_easiness == 2.5

    def test_third_review_uses_easiness(self):
        """Third review: interval = round(prev_interval * easiness)."""
        result = calculate_sm2(
            grade=4,
            easiness=2.36,
            repetitions=2,
            interval=6,
        )
        assert result.new_repetitions == 3
        assert result.new_interval == round(6 * 2.36)  # ~14
        assert result.new_easiness == 2.36

    def test_grade_below_3_resets(self):
        """Grade < 3 resets repetitions to 0 and interval to 1."""
        result = calculate_sm2(
            grade=2,
            easiness=2.5,
            repetitions=5,
            interval=30,
        )
        assert result.new_repetitions == 0
        assert result.new_interval == 1

    def test_grade_zero_blackout(self):
        """Grade 0 (complete blackout) resets and decreases easiness."""
        result = calculate_sm2(
            grade=0,
            easiness=2.5,
            repetitions=3,
            interval=15,
        )
        assert result.new_repetitions == 0
        assert result.new_interval == 1
        # EF' = 2.5 + (0.1 - 5*(0.08 + 5*0.02)) = 2.5 + (0.1 - 5*0.18) = 2.5 - 0.8 = 1.7
        assert result.new_easiness == 1.7

    def test_easiness_clamped_to_min(self):
        """Easiness should not go below 1.3."""
        # Repeated grade 0 will drive EF down
        result = calculate_sm2(
            grade=0,
            easiness=1.3,
            repetitions=0,
            interval=1,
        )
        assert result.new_easiness == 1.3  # clamped

    def test_easiness_clamped_to_max(self):
        """Easiness should not exceed 2.5."""
        result = calculate_sm2(
            grade=5,
            easiness=2.5,
            repetitions=0,
            interval=1,
        )
        assert result.new_easiness == 2.5

    def test_next_due_at_calculation(self):
        """Next due date should be now + interval days."""
        now = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = calculate_sm2(
            grade=5,
            easiness=2.5,
            repetitions=2,
            interval=6,
            last_reviewed_at=now,
        )
        expected_due = now + timedelta(days=round(6 * 2.5))  # 15 days
        assert result.next_due_at == expected_due

    def test_invalid_grade_raises(self):
        """Grade outside 0-5 should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sm2(grade=6, easiness=2.5, repetitions=0, interval=1)
        with pytest.raises(ValueError):
            calculate_sm2(grade=-1, easiness=2.5, repetitions=0, interval=1)

    def test_grade_3_hard_passing(self):
        """Grade 3 is the minimum passing grade (repetitions increment)."""
        result = calculate_sm2(
            grade=3,
            easiness=2.5,
            repetitions=0,
            interval=1,
        )
        assert result.new_repetitions == 1
        assert result.new_interval == 1
        # EF' = 2.5 + (0.1 - 2*(0.08 + 2*0.02)) = 2.5 + (0.1 - 2*0.12) = 2.5 - 0.14 = 2.36
        assert result.new_easiness == 2.36

    def test_suspension_on_chronic_failure(self):
        """Grade 0 with 0 repetitions and min easiness → suspended."""
        result = calculate_sm2(
            grade=0,
            easiness=1.3,
            repetitions=0,
            interval=1,
        )
        assert result.is_suspended

    def test_no_suspension_on_normal_failure(self):
        """Grade 2 should not suspend even if repetitions reset."""
        result = calculate_sm2(
            grade=2,
            easiness=2.0,
            repetitions=3,
            interval=10,
        )
        assert not result.is_suspended

    def test_easiness_decreases_on_low_grade(self):
        """Grade 1 should decrease easiness."""
        result = calculate_sm2(
            grade=1,
            easiness=2.5,
            repetitions=2,
            interval=6,
        )
        # EF' = 2.5 + (0.1 - 4*(0.08 + 4*0.02)) = 2.5 + (0.1 - 4*0.16) = 2.5 - 0.54 = 1.96
        assert result.new_easiness < 2.5
        assert result.new_easiness == 1.96
