"""Initial schema – all 16 tables for Qari Quran Learning App.

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00

Tables (16):
  Corpus Mirror (read-only, written by ETL): surahs, ayahs, words, roots,
    tajweed_annotations, qaris
  Learning Content: lessons, quiz_questions, badges
  User Data: users, user_lesson_progress, user_ayah_progress, flashcards,
    flashcard_reviews, user_stats, user_badges, recitation_sessions,
    recitation_word_results, scholar_questions
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # (A) CORPUS MIRROR — read-only, populated exclusively by the ETL pipeline
    # =========================================================================

    # --- qaris ----------------------------------------------------------------
    op.create_table(
        "qaris",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("arabic_name", sa.String(200), nullable=True),
        sa.Column("style", sa.String(50), nullable=True),
        sa.Column("audio_base_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("name", name="uq_qaris_name"),
    )

    # --- surahs ---------------------------------------------------------------
    op.create_table(
        "surahs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("surah_number", sa.SmallInteger, nullable=False),
        sa.Column("name_arabic", sa.String(100), nullable=False),
        sa.Column("name_transliteration", sa.String(200), nullable=False),
        sa.Column("name_translation_en", sa.String(200), nullable=True),
        sa.Column("name_translation_ur", sa.String(200), nullable=True),
        sa.Column("name_translation_hi_latn", sa.String(200), nullable=True),
        sa.Column("revelation_place", sa.String(20), nullable=False),
        sa.Column("revelation_order", sa.SmallInteger, nullable=False),
        sa.Column("ayah_count", sa.SmallInteger, nullable=False),
        sa.Column("page_start", sa.SmallInteger, nullable=True),
        sa.Column("juz_list", sa.JSON, nullable=True),
        sa.Column("context_story_en", sa.Text, nullable=True),
        sa.Column("context_story_ur", sa.Text, nullable=True),
        sa.Column("context_story_hi_latn", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "surah_number BETWEEN 1 AND 114",
            name="ck_surahs_surah_number_range",
        ),
        sa.CheckConstraint(
            "revelation_place IN ('meccan','medinan')",
            name="ck_surahs_revelation_place",
        ),
        sa.CheckConstraint("ayah_count > 0", name="ck_surahs_ayah_count_positive"),
        sa.UniqueConstraint("surah_number", name="uq_surahs_surah_number"),
    )
    op.create_index("ix_surahs_surah_number", "surahs", ["surah_number"], unique=True)

    # --- roots ----------------------------------------------------------------
    op.create_table(
        "roots",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("root_arabic", sa.String(50), nullable=False),
        sa.Column("root_transliteration", sa.String(100), nullable=False),
        sa.Column("meaning_en", sa.Text, nullable=True),
        sa.Column("meaning_ur", sa.Text, nullable=True),
        sa.Column("meaning_hi_latn", sa.Text, nullable=True),
        sa.Column("occurrence_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("root_arabic", name="uq_roots_root_arabic"),
    )
    op.create_index("ix_roots_root_transliteration", "roots", ["root_transliteration"])

    # --- ayahs ----------------------------------------------------------------
    op.create_table(
        "ayahs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("surah_id", sa.Integer, sa.ForeignKey("surahs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("surah_number", sa.SmallInteger, nullable=False),
        sa.Column("ayah_number", sa.SmallInteger, nullable=False),
        sa.Column("text_arabic", sa.Text, nullable=False),
        sa.Column("text_translation_en", sa.Text, nullable=True),
        sa.Column("text_translation_ur", sa.Text, nullable=True),
        sa.Column("text_translation_hi_latn", sa.Text, nullable=True),
        sa.Column("text_transliteration", sa.Text, nullable=True),
        sa.Column("juz", sa.SmallInteger, nullable=True),
        sa.Column("page", sa.SmallInteger, nullable=True),
        sa.Column("ruku", sa.SmallInteger, nullable=True),
        sa.Column("hizb_quarter", sa.SmallInteger, nullable=True),
        sa.Column("sajda", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("audio_url", sa.String(500), nullable=True),
        sa.Column("qari_id", sa.Integer, sa.ForeignKey("qaris.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("surah_number BETWEEN 1 AND 114", name="ck_ayahs_surah_number_range"),
        sa.CheckConstraint("ayah_number >= 1", name="ck_ayahs_ayah_number_positive"),
        sa.CheckConstraint("juz IS NULL OR (juz BETWEEN 1 AND 30)", name="ck_ayahs_juz_range"),
        sa.CheckConstraint("page IS NULL OR (page BETWEEN 1 AND 604)", name="ck_ayahs_page_range"),
        sa.UniqueConstraint("surah_number", "ayah_number", name="uq_ayahs_surah_ayah"),
    )
    op.create_index("ix_ayahs_surah_ayah", "ayahs", ["surah_number", "ayah_number"], unique=True)
    op.create_index("ix_ayahs_surah_id", "ayahs", ["surah_id"])
    op.create_index("ix_ayahs_juz", "ayahs", ["juz"])
    op.create_index("ix_ayahs_page", "ayahs", ["page"])

    # --- words ----------------------------------------------------------------
    op.create_table(
        "words",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ayah_id", sa.Integer, sa.ForeignKey("ayahs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("surah_number", sa.SmallInteger, nullable=False),
        sa.Column("ayah_number", sa.SmallInteger, nullable=False),
        sa.Column("word_position", sa.SmallInteger, nullable=False),
        sa.Column("text_arabic", sa.String(200), nullable=False),
        sa.Column("text_transliteration", sa.String(200), nullable=True),
        sa.Column("translation_en", sa.String(500), nullable=True),
        sa.Column("translation_ur", sa.String(500), nullable=True),
        sa.Column("translation_hi_latn", sa.String(500), nullable=True),
        sa.Column("root_id", sa.Integer, sa.ForeignKey("roots.id", ondelete="SET NULL"), nullable=True),
        sa.Column("pos_group", sa.String(30), nullable=True),
        sa.Column("pos_detail", sa.String(100), nullable=True),
        sa.Column("morphology_features", sa.JSON, nullable=True),
        sa.Column("audio_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("word_position >= 1", name="ck_words_word_position_positive"),
        sa.CheckConstraint(
            "pos_group IS NULL OR pos_group IN ('noun','verb','particle','pronoun',"
            "'adjective','adverb','conjunction','preposition','interjection',"
            "'proper_noun','number')",
            name="ck_words_pos_group",
        ),
        sa.UniqueConstraint("surah_number", "ayah_number", "word_position", name="uq_words_surah_ayah_pos"),
    )
    op.create_index("ix_words_ayah_id", "words", ["ayah_id"])
    op.create_index("ix_words_surah_ayah_pos", "words", ["surah_number", "ayah_number", "word_position"], unique=True)
    op.create_index("ix_words_root_id", "words", ["root_id"])

    # --- tajweed_annotations --------------------------------------------------
    op.create_table(
        "tajweed_annotations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("word_id", sa.Integer, sa.ForeignKey("words.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ayah_id", sa.Integer, sa.ForeignKey("ayahs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_category", sa.String(50), nullable=False),
        sa.Column("rule_name", sa.String(100), nullable=False),
        sa.Column("rule_name_arabic", sa.String(100), nullable=True),
        sa.Column("description_en", sa.Text, nullable=True),
        sa.Column("description_ur", sa.Text, nullable=True),
        sa.Column("description_hi_latn", sa.Text, nullable=True),
        sa.Column("char_start", sa.SmallInteger, nullable=True),
        sa.Column("char_end", sa.SmallInteger, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "char_start IS NULL OR char_start >= 0",
            name="ck_tajweed_char_start_nonneg",
        ),
        sa.CheckConstraint(
            "char_end IS NULL OR char_end >= 0",
            name="ck_tajweed_char_end_nonneg",
        ),
    )
    op.create_index("ix_tajweed_word_id", "tajweed_annotations", ["word_id"])
    op.create_index("ix_tajweed_ayah_id", "tajweed_annotations", ["ayah_id"])
    op.create_index("ix_tajweed_rule_category", "tajweed_annotations", ["rule_category"])

    # =========================================================================
    # (B) LEARNING CONTENT
    # =========================================================================

    # --- badges ---------------------------------------------------------------
    op.create_table(
        "badges",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=False),
        sa.Column("name_ur", sa.String(200), nullable=True),
        sa.Column("name_hi_latn", sa.String(200), nullable=True),
        sa.Column("description_en", sa.Text, nullable=True),
        sa.Column("description_ur", sa.Text, nullable=True),
        sa.Column("description_hi_latn", sa.Text, nullable=True),
        sa.Column("icon_url", sa.String(500), nullable=True),
        sa.Column("tier", sa.String(20), nullable=False, server_default="bronze"),
        sa.Column("xp_reward", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("criteria_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "tier IN ('bronze','silver','gold','platinum')",
            name="ck_badges_tier",
        ),
        sa.CheckConstraint("xp_reward >= 0", name="ck_badges_xp_reward_nonneg"),
        sa.UniqueConstraint("slug", name="uq_badges_slug"),
    )

    # --- lessons --------------------------------------------------------------
    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("module", sa.String(100), nullable=False),
        sa.Column("title_en", sa.String(300), nullable=False),
        sa.Column("title_ur", sa.String(300), nullable=True),
        sa.Column("title_hi_latn", sa.String(300), nullable=True),
        sa.Column("summary_en", sa.Text, nullable=True),
        sa.Column("summary_ur", sa.Text, nullable=True),
        sa.Column("summary_hi_latn", sa.Text, nullable=True),
        sa.Column("content_en", sa.JSON, nullable=True),
        sa.Column("content_ur", sa.JSON, nullable=True),
        sa.Column("content_hi_latn", sa.JSON, nullable=True),
        sa.Column("lesson_order", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("estimated_minutes", sa.SmallInteger, nullable=True),
        sa.Column("xp_reward", sa.Integer, nullable=False, server_default=sa.text("10")),
        sa.Column("surah_ref", sa.String(50), nullable=True),
        sa.Column("ayah_range", sa.String(50), nullable=True),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("review_status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "review_status IN ('draft','in_review','published','archived')",
            name="ck_lessons_review_status",
        ),
        sa.CheckConstraint("estimated_minutes IS NULL OR estimated_minutes > 0", name="ck_lessons_estimated_minutes_positive"),
        sa.CheckConstraint("xp_reward >= 0", name="ck_lessons_xp_reward_nonneg"),
        sa.UniqueConstraint("slug", name="uq_lessons_slug"),
    )
    op.create_index("ix_lessons_module", "lessons", ["module"])
    op.create_index("ix_lessons_review_status", "lessons", ["review_status"])
    op.create_index("ix_lessons_module_order", "lessons", ["module", "lesson_order"])

    # --- quiz_questions -------------------------------------------------------
    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("lesson_id", sa.Integer, sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_en", sa.Text, nullable=False),
        sa.Column("question_ur", sa.Text, nullable=True),
        sa.Column("question_hi_latn", sa.Text, nullable=True),
        sa.Column("question_type", sa.String(30), nullable=False, server_default="multiple_choice"),
        sa.Column("options_en", sa.JSON, nullable=True),
        sa.Column("options_ur", sa.JSON, nullable=True),
        sa.Column("options_hi_latn", sa.JSON, nullable=True),
        sa.Column("correct_answer", sa.String(500), nullable=False),
        sa.Column("explanation_en", sa.Text, nullable=True),
        sa.Column("explanation_ur", sa.Text, nullable=True),
        sa.Column("explanation_hi_latn", sa.Text, nullable=True),
        sa.Column("points", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("order_index", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "question_type IN ('multiple_choice','true_false','fill_blank','match')",
            name="ck_quiz_questions_question_type",
        ),
        sa.CheckConstraint("points > 0", name="ck_quiz_questions_points_positive"),
    )
    op.create_index("ix_quiz_questions_lesson_id", "quiz_questions", ["lesson_id"])
    op.create_index("ix_quiz_questions_lesson_order", "quiz_questions", ["lesson_id", "order_index"])

    # =========================================================================
    # (C) USER DATA
    # =========================================================================

    # --- users ----------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("firebase_uid", sa.String(128), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("display_name", sa.String(200), nullable=True),
        sa.Column("app_language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("starting_path", sa.String(30), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("total_xp", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("current_streak", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("longest_streak", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("freeze_credits", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("last_streak_date", sa.Date, nullable=True),
        sa.Column("last_freeze_grant_date", sa.Date, nullable=True),
        sa.Column("is_onboarded", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "app_language IN ('en','ur','hi_latn')",
            name="ck_users_app_language",
        ),
        sa.CheckConstraint(
            "starting_path IS NULL OR starting_path IN ('beginner','intermediate','advanced','tajweed_focus','memorization')",
            name="ck_users_starting_path",
        ),
        sa.CheckConstraint("total_xp >= 0", name="ck_users_total_xp_nonneg"),
        sa.CheckConstraint("current_streak >= 0", name="ck_users_current_streak_nonneg"),
        sa.CheckConstraint("longest_streak >= 0", name="ck_users_longest_streak_nonneg"),
        sa.CheckConstraint("freeze_credits >= 0", name="ck_users_freeze_credits_nonneg"),
        sa.UniqueConstraint("firebase_uid", name="uq_users_firebase_uid"),
    )
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"], unique=True)
    op.create_index("ix_users_email", "users", ["email"])

    # --- user_lesson_progress -------------------------------------------------
    op.create_table(
        "user_lesson_progress",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.Integer, sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="not_started"),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("xp_earned", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_accessed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.String(100), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('not_started','in_progress','completed')",
            name="ck_user_lesson_progress_status",
        ),
        sa.CheckConstraint("score IS NULL OR (score >= 0 AND score <= 100)", name="ck_user_lesson_progress_score_range"),
        sa.CheckConstraint("xp_earned >= 0", name="ck_user_lesson_progress_xp_nonneg"),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress_user_lesson"),
    )
    op.create_index("ix_user_lesson_progress_user_id", "user_lesson_progress", ["user_id"])
    op.create_index("ix_user_lesson_progress_lesson_id", "user_lesson_progress", ["lesson_id"])
    op.create_index("ix_ulp_user_status", "user_lesson_progress", ["user_id", "status"])

    # --- user_ayah_progress ---------------------------------------------------
    op.create_table(
        "user_ayah_progress",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("surah_number", sa.SmallInteger, nullable=False),
        sa.Column("ayah_number", sa.SmallInteger, nullable=False),
        sa.Column("times_studied", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("last_studied_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("surah_number BETWEEN 1 AND 114", name="ck_user_ayah_progress_surah_range"),
        sa.CheckConstraint("ayah_number >= 1", name="ck_user_ayah_progress_ayah_positive"),
        sa.CheckConstraint("times_studied >= 0", name="ck_user_ayah_progress_times_studied_nonneg"),
        sa.UniqueConstraint("user_id", "surah_number", "ayah_number", name="uq_uap_user_surah_ayah"),
    )
    op.create_index("ix_user_ayah_progress_user_id", "user_ayah_progress", ["user_id"])
    op.create_index("ix_uap_user_surah_ayah", "user_ayah_progress", ["user_id", "surah_number", "ayah_number"], unique=True)

    # --- flashcards -----------------------------------------------------------
    op.create_table(
        "flashcards",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("word_id", sa.Integer, sa.ForeignKey("words.id", ondelete="CASCADE"), nullable=False),
        sa.Column("surah_number", sa.SmallInteger, nullable=False),
        sa.Column("ayah_number", sa.SmallInteger, nullable=False),
        sa.Column("word_position", sa.SmallInteger, nullable=False),
        sa.Column("source", sa.String(30), nullable=False, server_default="manual"),
        sa.Column("sm2_easiness", sa.Numeric(3, 2), nullable=False, server_default=sa.text("2.50")),
        sa.Column("sm2_interval", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("sm2_repetitions", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("due_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_reviewed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("is_suspended", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "source IN ('manual','quiz_miss','recitation_miss')",
            name="ck_flashcards_source",
        ),
        sa.CheckConstraint("sm2_easiness >= 1.30 AND sm2_easiness <= 2.50", name="ck_flashcards_sm2_easiness_range"),
        sa.CheckConstraint("sm2_interval >= 0", name="ck_flashcards_sm2_interval_nonneg"),
        sa.CheckConstraint("sm2_repetitions >= 0", name="ck_flashcards_sm2_repetitions_nonneg"),
        sa.UniqueConstraint("user_id", "word_id", name="uq_flashcards_user_word"),
    )
    op.create_index("ix_flashcards_user_id", "flashcards", ["user_id"])
    op.create_index("ix_flashcards_user_due", "flashcards", ["user_id", "due_at"])
    op.create_index("ix_flashcards_user_suspended_due", "flashcards", ["user_id", "is_suspended", "due_at"])

    # --- flashcard_reviews ----------------------------------------------------
    op.create_table(
        "flashcard_reviews",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("flashcard_id", sa.Integer, sa.ForeignKey("flashcards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("grade", sa.SmallInteger, nullable=False),
        sa.Column("prev_easiness", sa.Numeric(3, 2), nullable=True),
        sa.Column("new_easiness", sa.Numeric(3, 2), nullable=True),
        sa.Column("prev_interval", sa.Integer, nullable=True),
        sa.Column("new_interval", sa.Integer, nullable=True),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("grade BETWEEN 0 AND 5", name="ck_flashcard_reviews_grade_range"),
    )
    op.create_index("ix_flashcard_reviews_flashcard_id", "flashcard_reviews", ["flashcard_id"])
    op.create_index("ix_flashcard_reviews_user_id", "flashcard_reviews", ["user_id"])
    op.create_index("ix_flashcard_reviews_user_reviewed", "flashcard_reviews", ["user_id", "reviewed_at"])

    # --- user_stats -----------------------------------------------------------
    op.create_table(
        "user_stats",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("lessons_completed", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("ayahs_studied", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("flashcards_reviewed", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("recitation_sessions", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("total_recitation_duration_sec", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("avg_recitation_accuracy", sa.Numeric(5, 2), nullable=True),
        sa.Column("questions_asked", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("lessons_completed >= 0", name="ck_user_stats_lessons_completed_nonneg"),
        sa.CheckConstraint("ayahs_studied >= 0", name="ck_user_stats_ayahs_studied_nonneg"),
        sa.CheckConstraint("flashcards_reviewed >= 0", name="ck_user_stats_flashcards_reviewed_nonneg"),
        sa.CheckConstraint("recitation_sessions >= 0", name="ck_user_stats_recitation_sessions_nonneg"),
        sa.CheckConstraint("total_recitation_duration_sec >= 0", name="ck_user_stats_recitation_duration_nonneg"),
        sa.CheckConstraint(
            "avg_recitation_accuracy IS NULL OR (avg_recitation_accuracy >= 0 AND avg_recitation_accuracy <= 100)",
            name="ck_user_stats_avg_accuracy_range",
        ),
    )
    op.create_index("ix_user_stats_user_id", "user_stats", ["user_id"], unique=True)

    # --- user_badges ----------------------------------------------------------
    op.create_table(
        "user_badges",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("badge_id", sa.Integer, sa.ForeignKey("badges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("awarded_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "badge_id", name="uq_user_badges_user_badge"),
    )
    op.create_index("ix_user_badges_user_id", "user_badges", ["user_id"])
    op.create_index("ix_user_badges_badge_id", "user_badges", ["badge_id"])

    # --- recitation_sessions --------------------------------------------------
    op.create_table(
        "recitation_sessions",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("surah_number", sa.SmallInteger, nullable=False),
        sa.Column("ayah_from", sa.SmallInteger, nullable=False),
        sa.Column("ayah_to", sa.SmallInteger, nullable=False),
        sa.Column("qari_id", sa.Integer, sa.ForeignKey("qaris.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("audio_url", sa.String(500), nullable=True),
        sa.Column("audio_duration_sec", sa.Numeric(8, 2), nullable=True),
        sa.Column("total_words", sa.Integer, nullable=True),
        sa.Column("correct_words", sa.Integer, nullable=True),
        sa.Column("accuracy_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("queued_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processing_started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("surah_number BETWEEN 1 AND 114", name="ck_recitation_sessions_surah_range"),
        sa.CheckConstraint("ayah_from >= 1", name="ck_recitation_sessions_ayah_from_positive"),
        sa.CheckConstraint("ayah_to >= ayah_from", name="ck_recitation_sessions_ayah_to_gte_from"),
        sa.CheckConstraint(
            "status IN ('queued','processing','completed','failed')",
            name="ck_recitation_sessions_status",
        ),
        sa.CheckConstraint(
            "accuracy_pct IS NULL OR (accuracy_pct >= 0 AND accuracy_pct <= 100)",
            name="ck_recitation_sessions_accuracy_range",
        ),
    )
    op.create_index("ix_recitation_sessions_user_id", "recitation_sessions", ["user_id"])
    op.create_index("ix_recitation_sessions_status", "recitation_sessions", ["status"])
    op.create_index("ix_recitation_sessions_user_created", "recitation_sessions", ["user_id", "created_at"])

    # --- recitation_word_results ----------------------------------------------
    op.create_table(
        "recitation_word_results",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.UUID, sa.ForeignKey("recitation_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("surah_number", sa.SmallInteger, nullable=False),
        sa.Column("ayah_number", sa.SmallInteger, nullable=False),
        sa.Column("word_position", sa.SmallInteger, nullable=False),
        sa.Column("expected_text", sa.String(200), nullable=False),
        sa.Column("detected_text", sa.String(200), nullable=True),
        sa.Column("verdict", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("error_detail_en", sa.Text, nullable=True),
        sa.Column("error_detail_ur", sa.Text, nullable=True),
        sa.Column("error_detail_hi_latn", sa.Text, nullable=True),
        sa.Column("audio_start_sec", sa.Numeric(10, 3), nullable=True),
        sa.Column("audio_end_sec", sa.Numeric(10, 3), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("surah_number BETWEEN 1 AND 114", name="ck_recitation_word_results_surah_range"),
        sa.CheckConstraint("ayah_number >= 1", name="ck_recitation_word_results_ayah_positive"),
        sa.CheckConstraint("word_position >= 1", name="ck_recitation_word_results_word_position_positive"),
        sa.CheckConstraint(
            "verdict IN ('correct','mispronounced','skipped','extra','unclear')",
            name="ck_recitation_word_results_verdict",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_recitation_word_results_confidence_range",
        ),
    )
    op.create_index("ix_recitation_word_results_session_id", "recitation_word_results", ["session_id"])
    op.create_index("ix_rwr_session_ayah_pos", "recitation_word_results", ["session_id", "surah_number", "ayah_number", "word_position"])

    # --- scholar_questions ----------------------------------------------------
    op.create_table(
        "scholar_questions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_text", sa.Text, nullable=True),
        sa.Column("audio_url", sa.String(500), nullable=True),
        sa.Column("audio_duration_sec", sa.Numeric(8, 2), nullable=True),
        sa.Column("surah_ref", sa.String(50), nullable=True),
        sa.Column("ayah_ref", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("answer_text", sa.Text, nullable=True),
        sa.Column("answer_audio_url", sa.String(500), nullable=True),
        sa.Column("scholar_name", sa.String(200), nullable=True),
        sa.Column("answered_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('pending','answered','rejected')",
            name="ck_scholar_questions_status",
        ),
        sa.CheckConstraint(
            "question_text IS NOT NULL OR audio_url IS NOT NULL",
            name="ck_scholar_questions_has_content",
        ),
    )
    op.create_index("ix_scholar_questions_user_id", "scholar_questions", ["user_id"])
    op.create_index("ix_scholar_questions_status", "scholar_questions", ["status"])
    op.create_index("ix_scholar_questions_user_created", "scholar_questions", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("scholar_questions")
    op.drop_table("recitation_word_results")
    op.drop_table("recitation_sessions")
    op.drop_table("user_badges")
    op.drop_table("user_stats")
    op.drop_table("flashcard_reviews")
    op.drop_table("flashcards")
    op.drop_table("user_ayah_progress")
    op.drop_table("user_lesson_progress")
    op.drop_table("users")
    op.drop_table("quiz_questions")
    op.drop_table("lessons")
    op.drop_table("badges")
    op.drop_table("tajweed_annotations")
    op.drop_table("words")
    op.drop_table("ayahs")
    op.drop_table("roots")
    op.drop_table("surahs")
    op.drop_table("qaris")
