"""Services __init__ — re-export services for convenience."""

from app.services.redis_service import (
    cache_get, cache_set, cache_delete, cache_delete_pattern,
    check_rate_limit, check_idempotency, store_idempotency,
    acquire_streak_lock, get_flashcard_daily_count,
    increment_flashcard_daily_count,
    enqueue_recitation_job, publish_recitation_result,
    init_redis, close_redis, get_redis,
)
from app.services.srs_service import calculate_sm2, SM2Result
from app.services.streak_service import update_streak
from app.services.flashcard_service import (
    get_due_flashcards, count_due_flashcards,
    auto_create_flashcard, auto_create_from_quiz_miss,
    auto_create_from_recitation_miss,
)
from app.services.badge_service import evaluate_badges
from app.services.content_bundle_service import generate_bundle_manifest
