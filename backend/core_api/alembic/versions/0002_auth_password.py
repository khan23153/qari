"""Add email/password auth support to the users table.

Revision ID: 0002
Revises: 0001
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Password hash column
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(255), nullable=True),
    )

    # firebase_uid is now optional (email/password accounts have none)
    op.alter_column(
        "users",
        "firebase_uid",
        existing_type=sa.String(128),
        nullable=True,
    )

    # Email must be unique for auth
    op.drop_index("ix_users_email", table_name="users")
    op.create_index("uq_users_email", "users", ["email"], unique=True)

    # Allow 'ar' as an app language
    op.drop_constraint("ck_users_app_language", "users", type_="check")
    op.create_check_constraint(
        "ck_users_app_language",
        "users",
        "app_language IN ('en','ur','hi_latn','ar')",
    )

    # Allow the new mobile starting paths
    op.drop_constraint("ck_users_starting_path", "users", type_="check")
    op.create_check_constraint(
        "ck_users_starting_path",
        "users",
        "starting_path IS NULL OR starting_path IN "
        "('beginner','intermediate','advanced','tajweed_focus','memorization',"
        "'foundation','quran_direct')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_starting_path", "users", type_="check")
    op.create_check_constraint(
        "ck_users_starting_path",
        "users",
        "starting_path IS NULL OR starting_path IN "
        "('beginner','intermediate','advanced','tajweed_focus','memorization')",
    )

    op.drop_constraint("ck_users_app_language", "users", type_="check")
    op.create_check_constraint(
        "ck_users_app_language",
        "users",
        "app_language IN ('en','ur','hi_latn')",
    )

    op.drop_index("uq_users_email", table_name="users")
    op.create_index("ix_users_email", "users", ["email"])

    op.alter_column(
        "users",
        "firebase_uid",
        existing_type=sa.String(128),
        nullable=False,
    )

    op.drop_column("users", "password_hash")
