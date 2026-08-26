""" add_order_batch_allocations

Revision ID: 9d0422eb7b85
Revises: 8c0311daF6a4
Create Date: 2026-08-26 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '9d0422eb7b85'
down_revision: Union[str, None] = '8c0311daF6a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'order_batch_allocations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inventory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('allocated_quantity', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['order_item_id'], ['order_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['inventory_id'], ['inventory.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_batch_allocations_order_item_id'), 'order_batch_allocations', ['order_item_id'], unique=False)
    op.create_index(op.f('ix_order_batch_allocations_order_id'), 'order_batch_allocations', ['order_id'], unique=False)
    op.create_index(op.f('ix_order_batch_allocations_product_id'), 'order_batch_allocations', ['product_id'], unique=False)
    op.create_index(op.f('ix_order_batch_allocations_batch_id'), 'order_batch_allocations', ['batch_id'], unique=False)
    op.create_index(op.f('ix_order_batch_allocations_inventory_id'), 'order_batch_allocations', ['inventory_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_order_batch_allocations_inventory_id'), table_name='order_batch_allocations')
    op.drop_index(op.f('ix_order_batch_allocations_batch_id'), table_name='order_batch_allocations')
    op.drop_index(op.f('ix_order_batch_allocations_product_id'), table_name='order_batch_allocations')
    op.drop_index(op.f('ix_order_batch_allocations_order_id'), table_name='order_batch_allocations')
    op.drop_index(op.f('ix_order_batch_allocations_order_item_id'), table_name='order_batch_allocations')
    op.drop_table('order_batch_allocations')
