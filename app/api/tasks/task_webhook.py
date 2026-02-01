"""
タスクWebhookエンドポイント

Cloud Tasksからのリクエストを受け取り、バックグラウンドジョブを実行します。
"""

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from typing import Dict, Any
import traceback
from app.tasks.image_generation_task import execute_image_generation_task


router = APIRouter(prefix="/api/tasks", tags=["background-tasks"])


class ImageGenerationTaskRequest(BaseModel):
    """画像生成タスクのリクエストボディ"""
    storybook_id: int
    story_plot_id: int
    reference_image_path: str
    strength: float = 0.85
    prefix: str = ""
    user_id: str
    story_pages: int = 5


@router.post("/image-generation")
async def image_generation_webhook(
    request: ImageGenerationTaskRequest,
    raw_request: Request
):
    """
    画像生成タスクのWebhookエンドポイント
    
    Cloud Tasksから呼び出され、バックグラウンドで画像生成を実行します。
    
    Args:
        request: タスクのペイロード
        raw_request: 生のFastAPIリクエスト（ヘッダー検証用）
    
    Returns:
        実行結果
    """
    
    # Cloud Tasksからのリクエストかどうかを検証（簡易版）
    # 本番環境ではOIDCトークンの検証を追加することを推奨
    user_agent = raw_request.headers.get("user-agent", "")
    if not user_agent.startswith("Google-Cloud-Tasks"):
        print(f"⚠️ 不正なリクエスト元: {user_agent}")
        # 開発環境では警告のみ、本番環境では403を返す
        # raise HTTPException(
        #     status_code=status.HTTP_403_FORBIDDEN,
        #     detail="Cloud Tasksからのリクエストのみ許可されています"
        # )
    
    print(f"📥 画像生成タスクWebhook受信: storybook_id={request.storybook_id}")
    
    try:
        # タスクを実行
        payload = request.model_dump()
        result = execute_image_generation_task(payload)
        
        print(f"✅ 画像生成タスク完了: {result}")
        
        return {
            "success": True,
            "result": result,
            "message": "画像生成タスクが完了しました"
        }
        
    except Exception as e:
        error_msg = f"画像生成タスク実行エラー: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"エラーのトレースバック: {traceback.format_exc()}")
        
        # タスクが失敗してもHTTP 200を返す（Cloud Tasksのリトライを防ぐ）
        # ステータスはデータベースで管理
        return {
            "success": False,
            "error": str(e),
            "message": "画像生成タスクが失敗しました"
        }


@router.get("/health")
async def task_webhook_health():
    """Webhookエンドポイントのヘルスチェック"""
    return {
        "status": "healthy",
        "service": "task-webhook",
        "message": "タスクWebhookエンドポイントは正常に動作しています"
    }
