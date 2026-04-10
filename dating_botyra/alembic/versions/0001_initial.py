"""initial

Revision ID: 0001
Revises:
Create Date: 2026-04-08

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sub_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(16), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("photos_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"], unique=True)

    op.create_table(
        "photos",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_id", UUID(as_uuid=True), nullable=False),
        sa.Column("s3_key", sa.String(512), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_photos_profile_id", "photos", ["profile_id"])

    op.create_table(
        "ratings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("primary_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("behavioral_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("combined_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ratings_user_id", "ratings", ["user_id"], unique=True)
    op.create_index("ix_ratings_combined_score", "ratings", ["combined_score"])

    op.create_table(
        "likes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("from_user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("to_user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(8), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["from_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("from_user_id", "to_user_id", name="uq_likes_from_to"),
    )
    op.create_index("ix_likes_from_to", "likes", ["from_user_id", "to_user_id"])

    op.create_table(
        "matches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user1_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user2_id", UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user1_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user2_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_matches_user1_id", "matches", ["user1_id"])
    op.create_index("ix_matches_user2_id", "matches", ["user2_id"])

    op.create_table(
        "messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("match_id", UUID(as_uuid=True), nullable=False),
        sa.Column("sender_id", UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_messages_match_id", "messages", ["match_id"])

    op.create_table(
        "subscriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("plan", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])

    op.create_table(
        "payments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("subscription_id", UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_id", sa.String(256), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"], ["subscriptions.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("ix_payments_subscription_id", "payments", ["subscription_id"])


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("subscriptions")
    op.drop_table("messages")
    op.drop_table("matches")
    op.drop_table("likes")
    op.drop_table("ratings")
    op.drop_table("photos")
    op.drop_table("profiles")
    op.drop_table("users")
