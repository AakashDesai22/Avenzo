""" add_notification_tables

Revision ID: 6a0199b8d4e2
Revises: 5f0189a7c3e1
Create Date: 2026-08-19 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '6a0199b8d4e2'
down_revision: Union[str, None] = '5f0189a7c3e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Notification Preferences
    op.create_table(
        'notification_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expiry_alerts', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('critical_expiry_alerts', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('pantry_updates', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('recommendation_alerts', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('quiet_hours_start', sa.String(length=10), nullable=True, server_default='22:00'),
        sa.Column('quiet_hours_end', sa.String(length=10), nullable=True, server_default='07:00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_notification_preferences')
    )
    op.create_index(op.f('ix_notification_preferences_user_id'), 'notification_preferences', ['user_id'], unique=False)

    # 2. Consumer Devices
    op.create_table(
        'consumer_devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', sa.String(length=100), nullable=False),
        sa.Column('platform', sa.String(length=30), nullable=False, server_default='android'),
        sa.Column('fcm_token', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'device_id', name='uq_user_device')
    )
    op.create_index(op.f('ix_consumer_devices_user_id'), 'consumer_devices', ['user_id'], unique=False)
    op.create_index(op.f('ix_consumer_devices_device_id'), 'consumer_devices', ['device_id'], unique=False)
    op.create_index(op.f('ix_consumer_devices_fcm_token'), 'consumer_devices', ['fcm_token'], unique=False)
    op.create_index(op.f('ix_consumer_devices_is_active'), 'consumer_devices', ['is_active'], unique=False)

    # 3. Notification Records
    op.create_table(
        'notification_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='CREATED'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_records_user_id'), 'notification_records', ['user_id'], unique=False)
    op.create_index(op.f('ix_notification_records_notification_type'), 'notification_records', ['notification_type'], unique=False)
    op.create_index(op.f('ix_notification_records_status'), 'notification_records', ['status'], unique=False)
    op.create_index(op.f('ix_notification_records_is_read'), 'notification_records', ['is_read'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_notification_records_is_read'), table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_status'), table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_notification_type'), table_name='notification_records')
    op.drop_index(op.f('ix_notification_records_user_id'), table_name='notification_records')
    op.drop_table('notification_records')

    op.drop_index(op.f('ix_consumer_devices_is_active'), table_name='consumer_devices')
    op.drop_index(op.f('ix_consumer_devices_fcm_token'), table_name='consumer_devices')
    op.drop_index(op.f('ix_consumer_devices_device_id'), table_name='consumer_devices')
    op.drop_index(op.f('ix_consumer_devices_user_id'), table_name='consumer_devices')
    op.drop_table('consumer_devices')

    op.drop_index(op.f('ix_notification_preferences_user_id'), table_name='notification_preferences')
    op.drop_table('notification_preferences')
