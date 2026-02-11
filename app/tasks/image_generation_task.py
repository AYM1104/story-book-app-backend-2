"""
画像生成タスク

Cloud Tasksから呼び出される画像生成処理のロジック。
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.database.supabase_session import get_supabase_db_sync
from app.service.image_generator_service import image_generator_service
from app.models.story.story_book import StoryBook


def execute_image_generation_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    画像生成タスクを実行
    
    Args:
        payload: タスクのペイロード
            - storybook_id: ストーリーブックID
            - story_plot_id: ストーリープロットID
            - reference_image_path: 参照画像のパス
            - strength: 画像生成の強度
            - prefix: プレフィックス
            - user_id: ユーザーID
            - story_pages: ページ数
    
    Returns:
        実行結果
    """
    storybook_id = payload.get("storybook_id")
    story_plot_id = payload.get("story_plot_id")
    reference_image_path = payload.get("reference_image_path")
    strength = payload.get("strength", 0.85)
    prefix = payload.get("prefix", "")
    user_id = payload.get("user_id")
    story_pages = payload.get("story_pages", 5)
    
    print(f"🎨 画像生成タスク開始: storybook_id={storybook_id}, story_plot_id={story_plot_id}")
    
    # データベースセッションを取得
    db = get_supabase_db_sync()
    
    try:
        # ストーリーブックの存在確認とステータス更新
        storybook = db.query(StoryBook).filter(StoryBook.id == storybook_id).first()
        if not storybook:
            raise ValueError(f"StoryBook ID {storybook_id} が見つかりません")
        
        # ステータスを「生成中」に更新
        storybook.image_generation_status = "generating"
        storybook.generation_progress = {
            "current_page": 0,
            "current_step": "prompt",
            "completed_pages": 0,
            "total_pages": 1 + story_pages  # 表紙 + ページ数
        }
        db.commit()
        
        print(f"✅ ステータスを'generating'に更新しました")
        
        # 画像生成サービスを呼び出し
        images_info = image_generator_service.generate_storyplot_all_pages_i2i(
            db=db,
            story_plot_id=story_plot_id,
            reference_image_path=reference_image_path,
            strength=strength,
            prefix=prefix,
            user_id=user_id,
            story_pages=story_pages
        )
        
        print(f"✅ 画像生成完了: {len(images_info)}枚")
        
        # ストーリーブックのステータスを「完了」に更新
        storybook = db.query(StoryBook).filter(StoryBook.id == storybook_id).first()
        if storybook:
            storybook.image_generation_status = "completed"
            storybook.generation_progress = {
                "current_page": 1 + story_pages,
                "current_step": "completed",
                "completed_pages": 1 + story_pages,
                "total_pages": 1 + story_pages
            }
            db.commit()
        
        print(f"✅ 画像生成タスク完了: storybook_id={storybook_id}")
        
        # プッシュ通知を送信
        try:
            from app.service.push_notification_service import push_notification_service
            
            # ストーリーブックのタイトルを取得
            storybook_title = storybook.title if hasattr(storybook, 'title') and storybook.title else None
            
            push_notification_service.send_storybook_complete_notification(
                db=db,
                user_id=user_id,
                storybook_id=storybook_id,
                storybook_title=storybook_title
            )
            print(f"📬 プッシュ通知を送信しました")
        except Exception as push_error:
            # プッシュ通知の失敗は画像生成の成功に影響しない
            print(f"⚠️ プッシュ通知送信エラー: {push_error}")
        
        return {
            "success": True,
            "storybook_id": storybook_id,
            "generated_images": len(images_info),
            "message": "画像生成が完了しました"
        }
        
    except Exception as e:
        print(f"❌ 画像生成タスクエラー: {e}")
        
        # エラー時はステータスを「失敗」に更新
        try:
            storybook = db.query(StoryBook).filter(StoryBook.id == storybook_id).first()
            if storybook:
                storybook.image_generation_status = "failed"
                db.commit()
                print(f"⚠️ ステータスを'failed'に更新しました")
        except Exception as status_error:
            print(f"⚠️ ステータス更新エラー: {status_error}")
        
        raise
    
    finally:
        db.close()
