"""Add device_tokens table for push notifications

Revision ID: add_device_tokens_table
Revises: add_appstore_subscription_fields
Create Date: 2026-02-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_device_tokens_table'
down_revision = 'add_appstore_subscription_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # device_tokensテーブルを作成
    op.create_table(
        'device_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False, comment='ユーザーID'),
        sa.Column('device_token', sa.String(length=512), nullable=False, comment='デバイストークン'),
        sa.Column('platform', sa.String(length=20), nullable=False, server_default='ios', comment='プラットフォーム（ios/android）'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='作成日時'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新日時'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # インデックス作成
    op.create_index('ix_device_tokens_user_id', 'device_tokens', ['user_id'], unique=False)
    op.create_index('ix_device_tokens_device_token', 'device_tokens', ['device_token'], unique=True)


def downgrade() -> None:
    # インデックス削除
    op.drop_index('ix_device_tokens_device_token', table_name='device_tokens')
    op.drop_index('ix_device_tokens_user_id', table_name='device_tokens')
    
    # テーブル削除
    op.drop_table('device_tokens')
