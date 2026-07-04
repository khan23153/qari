"""SM-2 spaced repetition algorithm implementation.

Reference: https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-obtained-in-working-with-the-supermemo-method

The SM-2 algorithm adjusts the easiness factor (EF), repetition count,
and inter-repetition interval based on the quality of the response (0-5).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from shared import SM2_INITIAL_EASINESS, SM2_MAX_EASINESS, SM2_MIN_EASINESS, SM2_REPETITION_INTERVAL


@dataclass
class SM2Result:
    """Result of an SM-2 update."""
    new_easiness: float
    new_interval: int          # days
    new_repetitions: int
    next_due_at: datetime
    is_suspended: bool


def calculate_sm2(
    *,
    grade: int,
    easiness: float,
    repetitions: int,
    interval: int,
    last_reviewed_at: Optional[datetime] = None,
) -> SM2Result:
    """Run one iteration of the SM-2 algorithm.

    Parameters
    ----------
    grade : int
        Quality of response, 0-5 (0=complete blackout, 5=perfect).
    easiness : float
        Current easiness factor (EF), typically 1.3–2.5.
    repetitions : int
        Number of consecutive correct repetitions.
    interval : int
        Current interval in days.
    last_reviewed_at : datetime, optional
        When the card was last reviewed. Defaults to now.

    Returns
    -------
    SM2Result
        Updated easiness, interval, repetitions, next due datetime, and
        suspension flag.
    """
    if not 0 <= grade <= 5:
        raise ValueError(f"grade must be 0-5, got {grade}")

    now = last_reviewed_at or datetime.now(timezone.utc)

    # --- Grade < 3: reset repetitions, interval = 1 ---
    if grade < 3:
        new_repetitions = 0
        new_interval = 1
    else:
        new_repetitions = repetitions + 1
        if new_repetitions == 1:
            new_interval = 1
        elif new_repetitions == 2:
            new_interval = SM2_REPETITION_INTERVAL  # 6 days
        else:
            new_interval = max(1, round(interval * easiness))

    # --- Update easiness factor ---
    # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_easiness = easiness + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))

    # Clamp to [1.3, 2.5]
    new_easiness = max(SM2_MIN_EASINESS, min(SM2_MAX_EASINESS, round(new_easiness, 2)))

    # --- Suspension: grade 0 repeatedly could warrant suspension ---
    # We suspend only if grade is 0 AND repetitions were already 0 (chronic failure)
    is_suspended = (grade == 0 and repetitions == 0 and new_easiness <= SM2_MIN_EASINESS)

    next_due = now + timedelta(days=new_interval)

    return SM2Result(
        new_easiness=new_easiness,
        new_interval=new_interval,
        new_repetitions=new_repetitions,
        next_due_at=next_due,
        is_suspended=is_suspended,
    )
