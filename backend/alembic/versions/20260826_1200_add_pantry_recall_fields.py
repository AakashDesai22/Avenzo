""" add_pantry_recall_fields

Revision ID: a12b34c56d7e
Revises: 9d0422eb7b85
Create Date: 2026-08-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a12b34c56d7e'
down_revision: Union[str, None] = '9d0422eb7b85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. PantryItem additions
    op.add_column('pantry_items', sa.Column('order_item_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('pantry_items', sa.Column('is_recalled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('pantry_items', sa.Column('recalled_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('pantry_items', sa.Column('recall_reason', sa.Text(), nullable=True))
    op.create_foreign_key('fk_pantry_items_order_item_id', 'pantry_items', 'order_items', ['order_item_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_pantry_items_order_item_id'), 'pantry_items', ['order_item_id'], unique=False)
    op.create_index(op.f('ix_pantry_items_is_recalled'), 'pantry_items', ['is_recalled'], unique=False)

    # 2. Batch additions
    op.add_column('batches', sa.Column('recalled_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('batches', sa.Column('recall_reason', sa.Text(), nullable=True))
    op.add_column('batches', sa.Column('recalled_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_batches_recalled_by', 'batches', 'users', ['recalled_by'], ['id'], ondelete='SET NULL')

    # 3. NotificationRecord additions
    op.add_column('notification_records', sa.Column('reference_type', sa.String(length=50), nullable=True))
    op.add_column('notification_records', sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_notification_records_reference_type'), 'notification_records', ['reference_type'], unique=False)
    op.create_index(op.f('ix_notification_records_reference_id'), 'notification_records', ['reference_id'], unique=False)
    op.create_index('ix_notification_user_type_ref', 'notification_records', ['user_id', 'notification_type', 'reference_type', 'reference_id'], unique=False)


def downgrade() -> None:
    # 3. NotificationRecord revert
    op.drop_index('ix_notification_user_type_ref', table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_reference_id'), table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_reference_type'), table_name='notification_records')
    op.drop_column('notification_records', 'reference_id')
    op.drop_column('notification_records', 'reference_type')

    # 2. Batch revert
    op.drop_constraint('fk_batches_recalled_by', 'batches', type_='foreignkey')
    op.drop_column('batches', 'recalled_by')
    op.drop_column('batches', 'recall_reason')
    op.drop_column('batches', 'recalled_at')

    # 1. PantryItem revert
    op.drop_index(op.f('ix_pantry_items_is_recalled'), table_name='pantry_items')
    op.drop_index(op.f('ix_pantry_items_order_item_id'), table_name='pantry_items')
    op.drop_constraint('fk_pantry_items_order_item_id', 'pantry_items', type_='foreignkey')
    op.drop_column('pantry_items', 'recall_reason')
    op.drop_column('pantry_items', 'recalled_at')
    op.drop_column('pantry_items', 'is_recalled')
    op.drop_column('pantry_items', 'order_item_id')
