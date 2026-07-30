"""add_image_url_and_public_id_to_events

Revision ID: a7d72cfc412e
Revises: d2e3f4a5b6c7
Create Date: 2026-07-30 22:52:56.814118

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a7d72cfc412e'
down_revision: Union[str, None] = 'd2e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('events', sa.Column('image_url', sa.String(length=500), nullable=True))
    op.add_column('events', sa.Column('image_public_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('events', 'image_public_id')
    op.drop_column('events', 'image_url')
