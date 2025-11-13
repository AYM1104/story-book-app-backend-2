from pydantic import BaseModel


class UserInfoResponse(BaseModel):
    """ユーザー情報レスポンス"""

    user_id: str
    user_name: str  # データベースから取得したユーザー名
    email: str | None = None
    name: str | None = None  # Auth0から取得した名前（後方互換性のため残す）
    picture: str | None = None


class StorageCleanupResponse(BaseModel):
    """ストレージ削除結果レスポンス"""

    enabled: bool
    uploads_removed: bool | None = None
    generated_removed: bool | None = None
    error: str | None = None


class Auth0CleanupResponse(BaseModel):
    """Auth0アカウント削除結果レスポンス"""

    enabled: bool
    account_removed: bool | None = None
    error: str | None = None


class AccountDeletionResponse(BaseModel):
    """アカウント削除結果レスポンス"""

    message: str
    user_id: str
    deleted_storybooks: int
    deleted_story_plots: int
    deleted_story_settings: int
    deleted_upload_images: int
    storage_cleanup: StorageCleanupResponse
    auth0_cleanup: Auth0CleanupResponse

