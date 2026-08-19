""" add_consumer_recommendations_table

Revision ID: 5f0189a7c3e1
Revises: 5a0179f8b4d2
Create Date: 2026-08-19 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '5f0189a7c3e1'
down_revision: Union[str, None] = '5a0179f8b4d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'consumer_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pantry_item_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recommendation_type', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=30), nullable=False, server_default='MEDIUM'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('suggested_action', sa.String(length=255), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('is_dismissed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pantry_item_id'], ['pantry_items.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consumer_recommendations_user_id'), 'consumer_recommendations', ['user_id'], unique=False)
    op.create_index(op.f('ix_consumer_recommendations_pantry_item_id'), 'consumer_recommendations', ['pantry_item_id'], unique=False)
    op.create_index(op.f('ix_consumer_recommendations_recommendation_type'), 'consumer_recommendations', ['recommendation_type'], unique=False)
    op.create_index(op.f('ix_consumer_recommendations_priority'), 'consumer_recommendations', ['priority'], unique=False)
    op.create_index(op.f('ix_consumer_recommendations_is_dismissed'), 'consumer_recommendations', ['is_dismissed'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_consumer_recommendations_is_dismissed'), table_name='consumer_recommendations')
    op.drop_index(op.f('ix_consumer_recommendations_priority'), table_name='consumer_recommendations')
    op.drop_index(op.f('ix_consumer_recommendations_recommendation_type'), table_name='consumer_recommendations')
    op.drop_index(op.f('ix_consumer_recommendations_pantry_item_id'), table_name='consumer_recommendations')
    op.drop_index(op.f('ix_consumer_recommendations_user_id'), table_name='consumer_recommendations')
    op.drop_table('consumer_recommendations')
