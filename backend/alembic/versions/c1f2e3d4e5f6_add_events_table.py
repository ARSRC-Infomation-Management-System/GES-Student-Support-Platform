"""add events table

Revision ID: c1f2e3d4e5f6
Revises: b7b2d8e1f4a3
Create Date: 2026-07-27
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c1f2e3d4e5f6"
down_revision: Union[str, None] = "763c26d1dc12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("target_region_id", sa.Integer(), sa.ForeignKey("regions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("events") as batch_op:
        batch_op.create_index("idx_events_school", ["target_school_id", "start_time"])
        batch_op.create_index("idx_events_region", ["target_region_id", "start_time"])
        batch_op.create_index("idx_events_status_end", ["status", "end_time"])
        batch_op.create_check_constraint(
            "event_status",
            "status IN ('draft', 'published', 'cancelled', 'completed')",
        )


def downgrade() -> None:
    with op.batch_alter_table("events") as batch_op:
        batch_op.drop_constraint("event_status", type_="check")
        batch_op.drop_index("idx_events_status_end")
        batch_op.drop_index("idx_events_region")
        batch_op.drop_index("idx_events_school")
    op.drop_table("events")
