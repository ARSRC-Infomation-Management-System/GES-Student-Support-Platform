"""Add production tracking fields.

Revision ID: b7b2d8e1f4a3
Revises: 6ac4afbc63ea
Create Date: 2026-07-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7b2d8e1f4a3"
down_revision: Union[str, None] = "6ac4afbc63ea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep historic "investigating" records compatible with the new status vocabulary.
    op.execute("UPDATE complaints SET status = 'under_review' WHERE status = 'investigating'")
    op.add_column(
        "complaints",
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"),
    )
    with op.batch_alter_table("complaints") as batch_op:
        batch_op.create_check_constraint(
            "complaint_status",
            "status IN ('pending', 'under_review', 'escalated', 'resolved', 'closed', 'rejected')",
        )
        batch_op.create_check_constraint(
            "complaint_priority",
            "priority IN ('low', 'medium', 'high', 'urgent')",
        )
    op.add_column(
        "notifications",
        sa.Column("notification_type", sa.String(length=50), nullable=False, server_default="general"),
    )
    op.add_column("notifications", sa.Column("reference_id", sa.Integer(), nullable=True))
    op.add_column("notifications", sa.Column("link", sa.String(length=255), nullable=True))
    op.add_column("notifications", sa.Column("read_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "audit_logs",
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column("audit_logs", sa.Column("user_agent", sa.String(length=512), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("complaints") as batch_op:
        batch_op.drop_constraint("complaint_priority", type_="check")
        batch_op.drop_constraint("complaint_status", type_="check")
    op.drop_column("audit_logs", "user_agent")
    op.drop_column("audit_logs", "success")
    op.drop_column("notifications", "read_at")
    op.drop_column("notifications", "link")
    op.drop_column("notifications", "reference_id")
    op.drop_column("notifications", "notification_type")
    op.drop_column("complaints", "priority")
