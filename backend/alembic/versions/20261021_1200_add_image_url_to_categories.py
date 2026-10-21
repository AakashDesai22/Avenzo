""" add_image_url_to_categories

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-10-21 12:00:00.000000

Adds an optional `image_url` string column to the `categories` table to support
custom category icons and images in the business web portal and Flutter consumer app.
Existing categories retain `image_url = NULL` and gracefully fall back to curated icons.

Backward Compatibility:
Fully backward-compatible; nullable=True with no default value required.
Existing category queries and relations operate identically.

Rollback Strategy:
Downgrade safely drops the `image_url` column from `categories`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'categories',
        sa.Column(
            'image_url',
            sa.String(length=500),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column('categories', 'image_url')
