"""ユーザーアカウント削除時の関連データ/ストレージ整理サービス"""
from __future__ import annotations

from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from app.models.users.users import Users
from app.models.child.child import Child
from app.features._01_image_upload.models.images import UploadImages
from app.models.story.story_setting import StorySetting
from app.models.story.story_plot import StoryPlot
from app.models.story.story_book import StoryBook
from app.service.gcs_storage_service import gcs_storage_service
from app.features._00_auth.services.auth0_management_service import Auth0ManagementService


class UserAccountCleanupService:
    """Supabase上のユーザー関連データとGCSファイルを整理するサービス"""

    def __init__(self) -> None:
        self._gcs_service = gcs_storage_service  # グローバルインスタンスを使用
        self._auth0_service: Optional[Auth0ManagementService] = None

    def _get_gcs_service(self):
        """GCSサービスを取得（グローバルインスタンス）"""
        return self._gcs_service

    def _get_auth0_service(self) -> Optional[Auth0ManagementService]:
        """Auth0管理サービスを遅延初期化"""
        if self._auth0_service is None:
            try:
                self._auth0_service = Auth0ManagementService()
            except Exception as exc:  # noqa: BLE001
                print(f"⚠️ Auth0ManagementService初期化エラー: {exc}")
                self._auth0_service = None
        return self._auth0_service

    def delete_user_account(self, user_id: str, db: Session) -> Dict[str, Any]:
        """ユーザー本体と紐づく全データを削除"""

        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # 事前に関連IDを収集
        story_plots = (
            db.query(StoryPlot.id, StoryPlot.story_setting_id)
            .filter(StoryPlot.user_id == user_id)
            .all()
        )
        story_plot_ids = [plot.id for plot in story_plots]
        story_setting_ids_from_plots = {plot.story_setting_id for plot in story_plots}

        upload_image_ids = [
            row[0]
            for row in db.query(UploadImages.id)
            .filter(UploadImages.user_id == user_id)
            .all()
        ]

        story_setting_ids_from_images = set()
        if upload_image_ids:
            story_setting_ids_from_images = {
                row[0]
                for row in db.query(StorySetting.id)
                .filter(StorySetting.upload_image_id.in_(upload_image_ids))
                .all()
            }

        story_setting_ids = story_setting_ids_from_plots.union(story_setting_ids_from_images)

        # 子テーブルから順に削除
        deleted_storybooks = (
            db.query(StoryBook)
            .filter(StoryBook.user_id == user_id)
            .delete(synchronize_session=False)
        )

        deleted_story_plots = (
            db.query(StoryPlot)
            .filter(StoryPlot.user_id == user_id)
            .delete(synchronize_session=False)
        )

        deleted_story_settings = 0
        if story_setting_ids:
            deleted_story_settings = (
                db.query(StorySetting)
                .filter(StorySetting.id.in_(story_setting_ids))
                .delete(synchronize_session=False)
            )

        deleted_upload_images = (
            db.query(UploadImages)
            .filter(UploadImages.user_id == user_id)
            .delete(synchronize_session=False)
        )

        # 子供レコードを削除（ユーザー削除前に削除する必要がある）
        deleted_children = (
            db.query(Child)
            .filter(Child.user_id == user_id)
            .delete(synchronize_session=False)
        )

        # ユーザー本体を削除
        db.delete(user)
        db.commit()

        storage_cleanup = {
            "enabled": False,
            "uploads_removed": None,
            "generated_removed": None,
            "error": None,
        }

        gcs_service = self._get_gcs_service()
        if gcs_service:
            storage_cleanup["enabled"] = True
            try:
                storage_cleanup["uploads_removed"] = gcs_service.delete_user_images(user_id, "uploads")
                storage_cleanup["generated_removed"] = gcs_service.delete_user_images(user_id, "generated")
            except Exception as exc:  # noqa: BLE001 - 失敗してもアカウント削除自体は成功とする
                storage_cleanup["error"] = str(exc)
        else:
            storage_cleanup["error"] = "GCS storage service is not configured"

        auth0_cleanup = {
            "enabled": False,
            "account_removed": None,
            "error": None,
        }

        auth0_service = self._get_auth0_service()
        if auth0_service:
            auth0_cleanup["enabled"] = True
            try:
                auth0_cleanup["account_removed"] = auth0_service.delete_user(user_id)
            except Exception as exc:  # noqa: BLE001
                auth0_cleanup["error"] = str(exc)
        else:
            auth0_cleanup["error"] = "Auth0 management service is not configured"

        return {
            "user_id": user_id,
            "deleted_storybooks": deleted_storybooks,
            "deleted_story_plots": deleted_story_plots,
            "deleted_story_settings": deleted_story_settings,
            "deleted_upload_images": deleted_upload_images,
            "deleted_children": deleted_children,
            "storage_cleanup": storage_cleanup,
            "auth0_cleanup": auth0_cleanup,
        }


user_account_cleanup_service = UserAccountCleanupService()
