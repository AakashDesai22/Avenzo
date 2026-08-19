""" add_consumer_pantry_tables

Revision ID: 5a0179f8b4d2
Revises: 3ac1dfeaac26
Create Date: 2026-08-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5a0179f8b4d2'
down_revision: Union[str, None] = '3ac1dfeaac26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create consumer_pantries table
    op.create_table(
        'consumer_pantries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, server_default='My Home Pantry'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_pantry_name')
    )
    op.create_index('ix_consumer_pantries_user_id', 'consumer_pantries', ['user_id'], unique=False)

    # 2. Create pantry_items table
    op.create_table(
        'pantry_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('pantry_id', sa.UUID(), nullable=False),
        sa.Column('product_id', sa.UUID(), nullable=True),
        sa.Column('batch_id', sa.UUID(), nullable=True),
        sa.Column('custom_name', sa.String(length=255), nullable=True),
        sa.Column('barcode', sa.String(length=100), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), nullable=False, server_default='1.0'),
        sa.Column('unit', sa.String(length=50), nullable=False, server_default='units'),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('storage_location', sa.String(length=50), nullable=False, server_default='pantry'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['pantry_id'], ['consumer_pantries.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pantry_items_pantry_id', 'pantry_items', ['pantry_id'], unique=False)
    op.create_index('ix_pantry_items_product_id', 'pantry_items', ['product_id'], unique=False)
    op.create_index('ix_pantry_items_batch_id', 'pantry_items', ['batch_id'], unique=False)
    op.create_index('ix_pantry_items_barcode', 'pantry_items', ['barcode'], unique=False)
    op.create_index('ix_pantry_items_expiry_date', 'pantry_items', ['expiry_date'], unique=False)
    op.create_index('ix_pantry_items_status', 'pantry_items', ['status'], unique=False)

    # 3. Create pantry_item_logs table
    op.create_table(
        'pantry_item_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('pantry_item_id', sa.UUID(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('quantity_change', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('logged_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['pantry_item_id'], ['pantry_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pantry_item_logs_pantry_item_id', 'pantry_item_logs', ['pantry_item_id'], unique=False)
    op.create_index('ix_pantry_item_logs_action', 'pantry_item_logs', ['action'], unique=False)
    op.create_index('ix_pantry_item_logs_logged_at', 'pantry_item_logs', ['logged_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_pantry_item_logs_logged_at', table_name='pantry_item_logs')
    op.drop_index('ix_pantry_item_logs_action', table_name='pantry_item_logs')
    op.drop_index('ix_pantry_item_logs_pantry_item_id', table_name='pantry_item_logs')
    op.drop_table('pantry_item_logs')

    op.drop_index('ix_pantry_items_status', table_name='pantry_items')
    op.drop_index('ix_pantry_items_expiry_date', table_name='pantry_items')
    op.drop_index('ix_pantry_items_barcode', table_name='pantry_items')
    op.drop_index('ix_pantry_items_batch_id', table_name='pantry_items')
    op.drop_index('ix_pantry_items_product_id', table_name='pantry_items')
    op.drop_index('ix_pantry_items_pantry_id', table_name='pantry_items')
    op.drop_table('pantry_items')

    op.drop_index('ix_consumer_pantries_user_id', table_name='consumer_pantries')
    op.drop_table('consumer_pantries')
