"""add_resource_file_columns

Revision ID: d39c84df8afc
Revises: a7d72cfc412e
Create Date: 2026-07-31 09:01:22.588681

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd39c84df8afc'
down_revision: Union[str, None] = 'a7d72cfc412e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('resources', sa.Column('file_url', sa.String(length=500), nullable=True))
    op.add_column('resources', sa.Column('file_public_id', sa.String(length=255), nullable=True))
    op.add_column('resources', sa.Column('file_type', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('resources', 'file_type')
    op.drop_column('resources', 'file_public_id')
    op.drop_column('resources', 'file_url')
