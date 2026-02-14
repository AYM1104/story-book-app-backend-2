"""
ユーザー関連の Pydantic スキーマ定義モジュール

このモジュールは、API のリクエスト / レスポンスで使用する
ユーザー関連のデータバリデーション用スキーマを定義しています。

スキーマ一覧:
  - UserCreate : ユーザー新規登録リクエスト用
  - UserUpdate : ユーザー情報更新リクエスト用
  - UserRead   : ユーザー情報取得レスポンス用

※ ORM モデル（SQLAlchemy）は models/users/users.py に定義されています。
  このファイルはあくまで「API 層でのデータ検証・シリアライズ」を担当します。
"""

from pydantic import BaseModel, EmailStr  # BaseModel: バリデーション基底クラス / EmailStr: メール形式を自動検証する型
from datetime import datetime
from typing import Optional
from app.models.credits.subscription import PlanType  # サブスクリプションプラン種別（FREE / BASIC / PREMIUM 等）


# =========================================================================
# ユーザー新規登録スキーマ
# =========================================================================
class UserCreate(BaseModel):
    """
    ユーザー新規登録時にクライアントから送られるリクエストボディのスキーマ。

    Auth0 での認証完了後、フロントエンドがこのスキーマに従って
    ユーザー情報をバックエンドに送信し、DB にレコードを作成します。
    """

    # Auth0 から発行されるユーザーID（例: "auth0|abc123"）
    id: str

    # アプリ内で表示されるユーザー名
    user_name: str

    # メールアドレス（オプショナル）。
    # Apple Sign In や LINE ログインなど、一部の OAuth プロバイダーでは
    # メールアドレスが取得できないケースがあるため Optional にしている。
    email: Optional[EmailStr] = None

    # パスワードは Auth0 側で管理するため、このスキーマでは受け取らない。
    # password: str


# =========================================================================
# ユーザー情報更新スキーマ
# =========================================================================
class UserUpdate(BaseModel):
    """
    ユーザー情報の部分更新（PATCH）リクエスト用スキーマ。

    変更したいフィールドだけを送信すれば OK。
    送信されなかった（None の）フィールドは更新対象外として扱われます。
    """

    # 新しいユーザー名（変更する場合のみ送信）
    user_name: Optional[str] = None

    # 新しいメールアドレス（変更する場合のみ送信）
    email: Optional[EmailStr] = None


# =========================================================================
# ユーザー情報取得スキーマ
# =========================================================================
class UserRead(BaseModel):
    """
    ユーザー情報取得時の API レスポンス用スキーマ。

    ORM のユーザーモデルから自動的に値をマッピングし、
    クライアントに返却するフィールドを定義しています。
    """

    # Auth0 のユーザーID
    id: str

    # ユーザー名
    user_name: str

    # メールアドレス（未登録の場合は null）
    email: Optional[EmailStr] = None

    # クレジット残高（絵本生成などで消費されるポイント）
    balance: int

    # 現在のサブスクリプションプラン（FREE / BASIC / PREMIUM など）
    subscription_plan: PlanType

    # レコード作成日時
    created_at: datetime

    # レコード最終更新日時
    updated_at: datetime

    class Config:
        # True にすると、ORM モデル（SQLAlchemy）のインスタンスから
        # 直接属性を読み取ってスキーマに変換できるようになる。
        # 例: UserRead.from_orm(user_orm_instance) → UserRead オブジェクト
        from_attributes = True