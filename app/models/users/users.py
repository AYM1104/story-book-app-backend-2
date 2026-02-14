"""
ユーザーモデル定義モジュール

このモジュールは、アプリケーションの中心となる「ユーザー」テーブルの
SQLAlchemy ORM モデルを定義しています。
ユーザーの基本情報（名前・メール等）やクレジット残高、サブスクリプション情報を保持し、
子ども・絵本・課金履歴など、他のテーブルとのリレーションシップを管理します。
"""

from sqlalchemy import Column, Integer, String, Enum
from app.models.credits.subscription import PlanType  # サブスクリプションプラン種別（FREE / BASIC / PREMIUM 等）
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase    # Supabase 向け共通ベースクラス（テーブル共通設定を含む）


class Users(SupabaseBase):
    """
    ユーザーモデル

    アプリを利用するユーザー1人分のレコードを表します。
    認証は Auth0 で行い、このテーブルではパスワードを保持しません。

    主な責務:
      - ユーザーの基本プロフィール情報を保持
      - クレジット残高（絵本生成などに使うポイント）を管理
      - 現在のサブスクリプションプランを保持
      - 関連テーブル（子ども、絵本、課金履歴 等）への参照を提供
    """

    # データベース上のテーブル名
    __tablename__ = "users"

    # =====================================================================
    # カラム定義
    # =====================================================================

    # Auth0から発行されるユーザーID。主キーとして使用。
    id = Column(String(255), primary_key=True, index=True, comment="Auth0のユーザーID")

    # ユーザーの表示名。アプリ内で表示される名前。
    user_name = Column(String(255), nullable=False, comment="ユーザー名")

    # メールアドレス。Apple Sign In など、メールが取得できないケースがあるため nullable。
    # ユニーク制約があるため、同一メールでの重複登録は不可。
    email = Column(String(255), nullable=True, unique=True, comment="メールアドレス（オプショナル）")

    # クレジット残高。絵本を生成するたびに消費されるポイント。
    # 新規登録時にデフォルトで 0 が設定される（別途初回ボーナスとして300クレジットを付与）。
    balance = Column(Integer, nullable=False, default=0, comment="クレジット残高")

    # 現在のサブスクリプションプラン（FREE / BASIC / PREMIUM など）。
    # PlanType enum で定義された値のみが格納される。デフォルトは FREE。
    subscription_plan = Column(
        Enum(PlanType), nullable=False, default=PlanType.FREE,
        comment="現在のサブスクリプションプラン"
    )

    # パスワードは Auth0 側で管理するため、このテーブルでは保持しない。
    # password = Column(String(255), nullable=False, comment="パスワード")

    # =====================================================================
    # リレーションシップ定義
    #
    # ・back_populates: 相手側モデルからこのユーザーを逆参照するための属性名
    # ・cascade="all, delete-orphan": ユーザー削除時に関連レコードも一括削除
    # =====================================================================

    # このユーザーに紐づくお子さま一覧
    children = relationship("Child", back_populates="user", cascade="all, delete-orphan")

    # このユーザーが生成した絵本の一覧
    storybooks = relationship("StoryBook", back_populates="user", cascade="all, delete-orphan")

    # クレジットの増減履歴（購入・消費・ボーナス付与などの出入り記録）
    credit_ledger = relationship("CreditLedger", back_populates="user", cascade="all, delete-orphan")

    # サブスクリプション情報（1ユーザーにつき1件のため uselist=False で単一オブジェクト）
    subscription = relationship("Subscription", back_populates="user", cascade="all, delete-orphan", uselist=False)

    # App Store での取引（購入・更新・キャンセル等）履歴
    app_store_transactions = relationship("AppStoreTransaction", back_populates="user", cascade="all, delete-orphan")

    # ユーザーがアップロードした画像（子どもの顔写真など、絵本生成の素材に使用）
    upload_images = relationship("UploadImages", back_populates="user", cascade="all, delete-orphan")

    # プッシュ通知用のデバイストークン一覧（複数デバイスに対応）
    device_tokens = relationship("DeviceToken", back_populates="user", cascade="all, delete-orphan")
    

