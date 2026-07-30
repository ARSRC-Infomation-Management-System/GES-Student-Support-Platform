"""add student_id and must_change_password to users

Revision ID: d2e3f4a5b6c7
Revises: c1f2e3d4e5f6
Create Date: 2026-07-30
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, None] = "c1f2e3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("student_id", sa.String(length=50), nullable=True))
    op.create_index(op.f("ix_users_student_id"), "users", ["student_id"], unique=True)
    op.add_column("users", sa.Column("must_change_password", sa.Boolean(), server_default="true", nullable=False))


def downgrade() -> None:
    op.drop_column("users", "must_change_password")
    op.drop_index(op.f("ix_users_student_id"), table_name="users")
    op.drop_column("users", "student_id")
