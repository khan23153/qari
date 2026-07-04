"""Initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2026-07-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Corpus Mirror (1A) ──
    op.create_table(
        "surahs",
        sa.Column("surah_number", sa.SmallInteger, primary_key=True),
        sa.Column("name_arabic", sa.Text, nullable=False),
        sa.Column("name_translit", sa.Text, nullable=False),
        sa.Column("name_translated", postgresql.JSONB, nullable=False),
        sa.Column("revelation_place", sa.Text, nullable=False),
        sa.Column("ayah_count", sa.SmallInteger, nullable=False),
        sa.Column("context_story", postgresql.JSONB),
        sa.CheckConstraint("surah_number BETWEEN 1 AND 114", "ck_surahs_number"),
        sa.CheckConstraint("revelation_place IN ('makkah','madinah')", "ck_surahs_revelation"),
    )

    op.create_table(
        "roots",
        sa.Column("root_id", sa.Integer, primary_key=True),
        sa.Column("root_arabic", sa.Text, nullable=False, unique=True),
        sa.Column("root_translit", sa.Text, nullable=False),
        sa.Column("core_meaning", postgresql.JSONB, nullable=False),
        sa.Column("occurrence_count", sa.Integer, nullable=False),
    )

    op.create_table(
        "ayahs",
        sa.Column("surah_number", sa.SmallInteger,
                  sa.ForeignKey("surahs.surah_number"), primary_key=True),
        sa.Column("ayah_number", sa.SmallInteger, primary_key=True),
        sa.Column("text_uthmani", sa.Text, nullable=False),
        sa.Column("text_imlaei", sa.Text, nullable=False),
        sa.Column("page_number", sa.SmallInteger),
        sa.Column("juz_number", sa.SmallInteger),
        sa.Column("audio_segments", postgresql.JSONB),
    )

    op.create_table(
        "words",
        sa.Column("surah_number", sa.SmallInteger, primary_key=True),
        sa.Column("ayah_number", sa.SmallInteger, primary_key=True),
        sa.Column("word_position", sa.SmallInteger, primary_key=True),
        sa.Column("text_uthmani", sa.Text, nullable=False),
        sa.Column("transliteration", sa.Text, nullable=False),
        sa.Column("translation", postgresql.JSONB, nullable=False),
        sa.Column("root_id", sa.Integer, sa.ForeignKey("roots.root_id")),
        sa.Column("lemma", sa.Text),
        sa.Column("pos_tag", sa.Text, nullable=False),
        sa.Column("pos_group", sa.Text, nullable=False),
        sa.Column("morphology", postgresql.JSONB, nullable=False),
        sa.Column("audio_url", sa.Text),
        sa.ForeignKeyConstraint(
            ["surah_number", "ayah_number"],
            ["ayahs.surah_number", "ayahs.ayah_number"],
        ),
        sa.CheckConstraint("pos_group IN ('ism','fil','harf')", "ck_words_pos_group"),
    )
    op.create_index("idx_words_root", "words", ["root_id"])
    op.create_index("idx_words_pos", "words", ["pos_group"])

    op.create_table(
        "tajweed_annotations",
        sa.Column("surah_number", sa.SmallInteger, primary_key=True),
        sa.Column("ayah_number", sa.SmallInteger, primary_key=True),
        sa.Column("word_position", sa.SmallInteger, primary_key=True),
        sa.Column("char_start", sa.SmallInteger, primary_key=True),
        sa.Column("rule", sa.Text, primary_key=True),
        sa.Column("char_end", sa.SmallInteger, nullable=False),
        sa.ForeignKeyConstraint(
            ["surah_number", "ayah_number", "word_position"],
            ["words.surah_number", "words.ayah_number", "words.word_position"],
        ),
    )

    op.create_table(
        "qaris",
        sa.Column("qari_id", sa.SmallInteger, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("style", sa.Text),
        sa.Column("base_audio_url", sa.Text, nullable=False),
        sa.Column("is_default", sa.Boolean, default=False),
    )

    # ── Learning Content (1B) ──
    op.create_table(
        "lessons",
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("module", sa.SmallInteger, nullable=False),
        sa.Column("unit_number", sa.SmallInteger, nullable=False),
        sa.Column("sequence", sa.SmallInteger, nullable=False),
        sa.Column("lesson_type", sa.Text, nullable=False),
        sa.Column("title", postgresql.JSONB, nullable=False),
        sa.Column("content", postgresql.JSONB, nullable=False),
        sa.Column("xp_reward", sa.SmallInteger, nullable=False, server_default="10"),
        sa.Column("min_pass_pct", sa.SmallInteger, server_default="70"),
        sa.Column("review_status", sa.Text, nullable=False, server_default="draft"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.CheckConstraint("module IN (1,2,3)", "ck_lessons_module"),
        sa.CheckConstraint(
            "lesson_type IN ('alphabet','makhraj','grammar_card','sentence_builder',"
            "'quiz','reader_assignment','tajweed_theory','recitation_practice')",
            "ck_lessons_type",
        ),
        sa.CheckConstraint(
            "review_status IN ('draft','in_review','scholar_approved','published')",
            "ck_lessons_review",
        ),
        sa.UniqueConstraint("module", "unit_number", "sequence", "uq_lessons_seq"),
    )

    op.create_table(
        "quiz_questions",
        sa.Column("question_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("lessons.lesson_id")),
        sa.Column("q_type", sa.Text, nullable=False),
        sa.Column("prompt", postgresql.JSONB, nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("difficulty", sa.SmallInteger, server_default="1"),
        sa.CheckConstraint(
            "q_type IN ('mcq','drag_match','fill_blank','audio_pick','word_order')",
            "ck_quiz_type",
        ),
    )

    op.create_table(
        "badges",
        sa.Column("badge_id", sa.Text, primary_key=True),
        sa.Column("title", postgresql.JSONB, nullable=False),
        sa.Column("description", postgresql.JSONB, nullable=False),
        sa.Column("icon_url", sa.Text, nullable=False),
        sa.Column("criteria", postgresql.JSONB, nullable=False),
    )

    # ── User Data (1C) ──
    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("auth_provider_id", sa.Text, unique=True, nullable=False),
        sa.Column("display_name", sa.Text),
        sa.Column("app_language", sa.Text, nullable=False, server_default="hi_latn"),
        sa.Column("starting_path", sa.Text),
        sa.Column("font_scale", sa.Float, server_default="1.0"),
        sa.Column("theme", sa.Text, server_default="system"),
        sa.Column("preferred_qari", sa.SmallInteger, sa.ForeignKey("qaris.qari_id")),
        sa.Column("audio_training_consent", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("app_language IN ('en','ur','hi_latn')", "ck_users_lang"),
        sa.CheckConstraint("starting_path IN ('foundation','quran_direct')", "ck_users_path"),
        sa.CheckConstraint("theme IN ('light','dark','system','high_contrast')", "ck_users_theme"),
    )

    op.create_table(
        "user_lesson_progress",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.user_id"), primary_key=True),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("lessons.lesson_id"), primary_key=True),
        sa.Column("status", sa.Text, nullable=False, server_default="not_started"),
        sa.Column("best_score", sa.SmallInteger),
        sa.Column("attempts", sa.SmallInteger, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('not_started','in_progress','completed')", "ck_ulp_status"),
    )

    op.create_table(
        "user_ayah_progress",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.user_id"), primary_key=True),
        sa.Column("surah_number", sa.SmallInteger, primary_key=True),
        sa.Column("ayah_number", sa.SmallInteger, primary_key=True),
        sa.Column("studied_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "flashcards",
        sa.Column("card_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id")),
        sa.Column("surah_number", sa.SmallInteger),
        sa.Column("ayah_number", sa.SmallInteger),
        sa.Column("word_position", sa.SmallInteger),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("ease_factor", sa.Float, nullable=False, server_default="2.5"),
        sa.Column("interval_days", sa.Float, nullable=False, server_default="0"),
        sa.Column("repetitions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("suspended", sa.Boolean, server_default="false"),
        sa.CheckConstraint("source IN ('quiz_miss','recitation_miss','manual_save','auto_frequency')", "ck_fc_source"),
        sa.UniqueConstraint("user_id", "surah_number", "ayah_number", "word_position", "uq_fc_word"),
        sa.ForeignKeyConstraint(
            ["surah_number", "ayah_number", "word_position"],
            ["words.surah_number", "words.ayah_number", "words.word_position"],
        ),
    )
    op.create_index("idx_flashcards_due", "flashcards", ["user_id", "due_at"])

    op.create_table(
        "flashcard_reviews",
        sa.Column("review_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("flashcards.card_id")),
        sa.Column("grade", sa.SmallInteger, nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("grade BETWEEN 0 AND 5", "ck_fr_grade"),
    )

    op.create_table(
        "user_stats",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.user_id"), primary_key=True),
        sa.Column("xp_total", sa.Integer, server_default="0"),
        sa.Column("current_streak", sa.Integer, server_default="0"),
        sa.Column("longest_streak", sa.Integer, server_default="0"),
        sa.Column("last_active_date", sa.Date),
        sa.Column("timezone", sa.Text, server_default="Asia/Kolkata"),
    )

    op.create_table(
        "user_badges",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.user_id"), primary_key=True),
        sa.Column("badge_id", sa.Text, sa.ForeignKey("badges.badge_id"), primary_key=True),
        sa.Column("earned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "recitation_sessions",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id")),
        sa.Column("surah_number", sa.SmallInteger),
        sa.Column("ayah_start", sa.SmallInteger),
        sa.Column("ayah_end", sa.SmallInteger),
        sa.Column("audio_url", sa.Text),
        sa.Column("overall_score", sa.SmallInteger),
        sa.Column("fluency_score", sa.SmallInteger),
        sa.Column("tajweed_score", sa.SmallInteger),
        sa.Column("model_version", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "recitation_word_results",
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("recitation_sessions.session_id"), primary_key=True),
        sa.Column("surah_number", sa.SmallInteger, primary_key=True),
        sa.Column("ayah_number", sa.SmallInteger, primary_key=True),
        sa.Column("word_position", sa.SmallInteger, primary_key=True),
        sa.Column("verdict", sa.Text, nullable=False),
        sa.Column("error_detail", postgresql.JSONB),
        sa.Column("start_ms", sa.Integer),
        sa.Column("end_ms", sa.Integer),
        sa.CheckConstraint(
            "verdict IN ('correct','mispronounced','omitted','inserted_extra','low_confidence')",
            "ck_rwr_verdict",
        ),
    )

    op.create_table(
        "scholar_questions",
        sa.Column("question_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id")),
        sa.Column("audio_url", sa.Text),
        sa.Column("text_body", sa.Text),
        sa.Column("status", sa.Text, nullable=False, server_default="queued"),
        sa.Column("scholar_id", postgresql.UUID(as_uuid=True)),
        sa.Column("answer_audio_url", sa.Text),
        sa.Column("answer_text", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("answered_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('queued','assigned','answered','rejected')", "ck_sq_status"),
    )


def downgrade() -> None:
    op.drop_table("scholar_questions")
    op.drop_table("recitation_word_results")
    op.drop_table("recitation_sessions")
    op.drop_table("user_badges")
    op.drop_table("user_stats")
    op.drop_table("flashcard_reviews")
    op.drop_index("idx_flashcards_due", table_name="flashcards")
    op.drop_table("flashcards")
    op.drop_table("user_ayah_progress")
    op.drop_table("user_lesson_progress")
    op.drop_table("users")
    op.drop_table("badges")
    op.drop_table("quiz_questions")
    op.drop_table("lessons")
    op.drop_table("qaris")
    op.drop_table("tajweed_annotations")
    op.drop_index("idx_words_pos", table_name="words")
    op.drop_index("idx_words_root", table_name="words")
    op.drop_table("words")
    op.drop_table("ayahs")
    op.drop_table("roots")
    op.drop_table("surahs")
