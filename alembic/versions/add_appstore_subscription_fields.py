"""Add App Store subscription fields

Revision ID: add_appstore_subscription_fields
Revises: 
Create Date: 2026-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_appstore_subscription_fields'
down_revision = None  # TODO: 最新のrevisionに置き換えてください
branch_labels = None
depends_on = None


def upgrade() -> None:
    # subscriptionsテーブルにApp Store関連カラムを追加
    op.add_column('subscriptions', sa.Column('original_transaction_id', sa.String(length=255), nullable=True, comment='App StoreのオリジナルトランザクションID（一意）'))
    op.add_column('subscriptions', sa.Column('latest_transaction_id', sa.String(length=255), nullable=True, comment='最新のトランザクションID'))
    op.add_column('subscriptions', sa.Column('product_id', sa.String(length=255), nullable=True, comment='App StoreのプロダクトID'))
    op.add_column('subscriptions', sa.Column('auto_renew_status', sa.Boolean(), nullable=True, server_default='true', comment='自動更新ステータス'))
    op.add_column('subscriptions', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='サブスクリプション有効期限（日本時間）'))
    op.add_column('subscriptions', sa.Column('grace_period_expires_at', sa.DateTime(timezone=True), nullable=True, comment='グレースピリオド終了日時'))
    op.add_column('subscriptions', sa.Column('is_in_billing_retry', sa.Boolean(), nullable=True, server_default='false', comment='請求リトライ中'))
    op.add_column('subscriptions', sa.Column('cancellation_date', sa.DateTime(timezone=True), nullable=True, comment='キャンセル日時'))
    op.add_column('subscriptions', sa.Column('last_credit_grant_date', sa.DateTime(timezone=True), nullable=True, comment='最後にクレジット付与した日時'))
    
    # インデックス作成
    op.create_index('ix_subscriptions_original_transaction_id', 'subscriptions', ['original_transaction_id'], unique=True)
    op.create_index('ix_subscriptions_latest_transaction_id', 'subscriptions', ['latest_transaction_id'], unique=False)
    op.create_index('ix_subscriptions_product_id', 'subscriptions', ['product_id'], unique=False)
    
    # credit_ledgerテーブルにtransaction_idカラムを追加
    op.add_column('credit_ledger', sa.Column('transaction_id', sa.String(length=255), nullable=True, comment='App StoreトランザクションID（サブスクリプション関連の場合）'))
    op.create_index('ix_credit_ledger_transaction_id', 'credit_ledger', ['transaction_id'], unique=False)
    
    # app_store_transactionsテーブルを作成
    op.create_table(
        'app_store_transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False, comment='ユーザーID'),
        sa.Column('transaction_id', sa.String(length=255), nullable=False, comment='トランザクションID'),
        sa.Column('original_transaction_id', sa.String(length=255), nullable=False, comment='オリジナルトランザクションID'),
        sa.Column('product_id', sa.String(length=255), nullable=False, comment='プロダクトID'),
        sa.Column('purchase_date', sa.DateTime(timezone=True), nullable=False, comment='購入日時'),
        sa.Column('expires_date', sa.DateTime(timezone=True), nullable=True, comment='有効期限'),
        sa.Column('is_upgraded', sa.Boolean(), nullable=True, server_default='false', comment='アップグレードフラグ'),
        sa.Column('cancellation_date', sa.DateTime(timezone=True), nullable=True, comment='キャンセル日時'),
        sa.Column('jws_representation', sa.Text(), nullable=True, comment='JWS（検証用）'),
        sa.Column('notification_type', sa.String(length=100), nullable=True, comment='Server Notificationタイプ'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='作成日時'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False, comment='更新日時'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # インデックス作成
    op.create_index('ix_app_store_transactions_user_id', 'app_store_transactions', ['user_id'], unique=False)
    op.create_index('ix_app_store_transactions_transaction_id', 'app_store_transactions', ['transaction_id'], unique=True)
    op.create_index('ix_app_store_transactions_original_transaction_id', 'app_store_transactions', ['original_transaction_id'], unique=False)


def downgrade() -> None:
    # app_store_transactionsテーブルを削除
    op.drop_index('ix_app_store_transactions_original_transaction_id', table_name='app_store_transactions')
    op.drop_index('ix_app_store_transactions_transaction_id', table_name='app_store_transactions')
    op.drop_index('ix_app_store_transactions_user_id', table_name='app_store_transactions')
    op.drop_table('app_store_transactions')
    
    # credit_ledgerのカラムを削除
    op.drop_index('ix_credit_ledger_transaction_id', table_name='credit_ledger')
    op.drop_column('credit_ledger', 'transaction_id')
    
    # subscriptionsのカラムを削除
    op.drop_index('ix_subscriptions_product_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_latest_transaction_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_original_transaction_id', table_name='subscriptions')
    op.drop_column('subscriptions', 'last_credit_grant_date')
    op.drop_column('subscriptions', 'cancellation_date')
    op.drop_column('subscriptions', 'is_in_billing_retry')
    op.drop_column('subscriptions', 'grace_period_expires_at')
    op.drop_column('subscriptions', 'expires_at')
    op.drop_column('subscriptions', 'auto_renew_status')
    op.drop_column('subscriptions', 'product_id')
    op.drop_column('subscriptions', 'latest_transaction_id')
    op.drop_column('subscriptions', 'original_transaction_id')
