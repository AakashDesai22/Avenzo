""" add_is_published_to_products

Revision ID: b1c2d3e4f5a6
Revises: a12b34c56d7e
Create Date: 2026-10-20 17:00:00.000000

Adds an `is_published` boolean flag to the products table to support a
draft/publish workflow. Draft products (is_published=False) are hidden from
the consumer marketplace. Published products (is_published=True) are visible
to consumers through /api/v1/marketplace/products.

Existing products default to is_published=False (unpublished) so that admins
must explicitly publish each product. This is intentionally conservative -
no data is lost or promoted silently.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a12b34c56d7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'products',
        sa.Column(
            'is_published',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
    )
    op.create_index(
        op.f('ix_products_is_published'),
        'products',
        ['is_published'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_products_is_published'), table_name='products')
    op.drop_column('products', 'is_published')
