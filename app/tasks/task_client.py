"""
Cloud Tasksクライアント

Cloud Tasksを使用してバックグラウンドジョブを作成・管理するクライアント。
"""

import os
import json
from typing import Optional, Dict, Any
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
import datetime


class TaskClient:
    """Cloud Tasksクライアントのラッパークラス"""
    
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("CLOUD_TASKS_LOCATION", "us-west1")  # Cloud Runと同じリージョン
        self.queue_name = os.getenv("CLOUD_TASKS_QUEUE", "image-generation-queue")
        
        if not self.project_id:
            raise ValueError("環境変数 GOOGLE_CLOUD_PROJECT が設定されていません")
        
        self.client = tasks_v2.CloudTasksClient()
        self.queue_path = self.client.queue_path(
            self.project_id,
            self.location,
            self.queue_name
        )
    
    def create_image_generation_task(
        self,
        storybook_id: int,
        story_plot_id: int,
        reference_image_path: str,
        strength: float,
        prefix: str,
        user_id: str,
        story_pages: int,
        webhook_url: str,
        schedule_delay_seconds: int = 0
    ) -> str:
        """
        画像生成タスクをCloud Tasksに作成
        
        Args:
            storybook_id: ストーリーブックID
            story_plot_id: ストーリープロットID
            reference_image_path: 参照画像のパス
            strength: 画像生成の強度
            prefix: プレフィックス
            user_id: ユーザーID
            story_pages: ページ数
            webhook_url: Webhookエンドポイントの完全URL
            schedule_delay_seconds: タスク実行までの遅延（秒）
        
        Returns:
            作成されたタスクの名前
        """
        
        # タスクのペイロード
        payload = {
            "storybook_id": storybook_id,
            "story_plot_id": story_plot_id,
            "reference_image_path": reference_image_path,
            "strength": strength,
            "prefix": prefix,
            "user_id": user_id,
            "story_pages": story_pages
        }
        
        # HTTPリクエストタスクを作成
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": webhook_url,
                "headers": {
                    "Content-Type": "application/json",
                },
                "body": json.dumps(payload).encode(),
            }
        }
        
        # 遅延実行の設定
        if schedule_delay_seconds > 0:
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(
                datetime.datetime.utcnow() + datetime.timedelta(seconds=schedule_delay_seconds)
            )
            task["schedule_time"] = timestamp
        
        # OIDC認証トークンの設定（Cloud Run間の認証）
        service_account_email = os.getenv("CLOUD_TASKS_SERVICE_ACCOUNT")
        if service_account_email:
            task["http_request"]["oidc_token"] = {
                "service_account_email": service_account_email
            }
        
        # タスクを作成
        try:
            response = self.client.create_task(
                request={
                    "parent": self.queue_path,
                    "task": task
                }
            )
            print(f"✅ Cloud Taskを作成しました: {response.name}")
            return response.name
        except Exception as e:
            print(f"❌ Cloud Task作成エラー: {e}")
            raise
    
    def get_task(self, task_name: str) -> Optional[tasks_v2.Task]:
        """
        タスクの情報を取得
        
        Args:
            task_name: タスクの名前
        
        Returns:
            タスク情報、または存在しない場合はNone
        """
        try:
            task = self.client.get_task(name=task_name)
            return task
        except Exception as e:
            print(f"⚠️ タスク取得エラー: {e}")
            return None
    
    def delete_task(self, task_name: str) -> bool:
        """
        タスクを削除（キャンセル）
        
        Args:
            task_name: タスクの名前
        
        Returns:
            削除に成功した場合True
        """
        try:
            self.client.delete_task(name=task_name)
            print(f"✅ Cloud Taskを削除しました: {task_name}")
            return True
        except Exception as e:
            print(f"⚠️ タスク削除エラー: {e}")
            return False


# グローバルインスタンス（シングルトン）
_task_client: Optional[TaskClient] = None


def get_task_client() -> TaskClient:
    """TaskClientのシングルトンインスタンスを取得"""
    global _task_client
    if _task_client is None:
        _task_client = TaskClient()
    return _task_client
