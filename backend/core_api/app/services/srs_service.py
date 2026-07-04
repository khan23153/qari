"""Spaced Repetition System (SRS) — SM-2 algorithm implementation.

Grades 0-5:
  0-2: incorrect, reset repetitions
  3:   correct but difficult
  4:   correct with effort
  5:   perfect
"""
from datetime import datetime, timedelta, timezone


def sm2_update(
    ease_factor: float,
    interval_days: float,
    repetitions: int,
    grade: int,
) -> tuple[float, float, int, datetime]:
    """Run one SM-2 step.

    Returns (new_ease_factor, new_interval_days, new_repetitions, next_due_at).
    """
    if grade < 3:
        # Failed — reset
        repetitions = 0
        interval_days = 0
    else:
        repetitions += 1
        if repetitions == 1:
            interval_days = 1
        elif repetitions == 2:
            interval_days = 6
        else:
            interval_days = interval_days * ease_factor

    # Update ease factor (clamped to 1.3)
    ease_factor = max(
        1.3,
        ease_factor + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02)),
    )

    next_due = datetime.now(timezone.utc) + timedelta(days=interval_days)
    return ease_factor, interval_days, repetitions, next_due


# Grade mapping from UI labels (Hinglish)
GRADE_MAP = {
    "bhool_gaya": 1,   # "I forgot"
    "mushkil": 3,       # "Difficult"
    "aasaan": 5,        # "Easy"
}
