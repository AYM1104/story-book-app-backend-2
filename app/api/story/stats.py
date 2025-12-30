from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import Dict, Any

from app.database.supabase_session import get_supabase_db
from app.models.story.story_book import StoryBook

router = APIRouter(prefix="/storybook", tags=["storybook-statistics"])


@router.get("/stats/{user_id}")
async def get_storybook_stats(
    user_id: str,
    db: Session = Depends(get_supabase_db)
):
    """ユーザーのストーリーブック統計を取得するエンドポイント
    
    Returns:
        - total: すべてのストーリーブック作成数
        - this_month: 今月のストーリーブック作成数
        - this_week: 今週のストーリーブック作成数
    """
    try:
        # 現在の日時を取得
        now = datetime.now()
        today = now.date()
        
        # すべてのストーリーブック作成数を取得
        total_count = db.query(func.count(StoryBook.id)).filter(
            StoryBook.user_id == user_id
        ).scalar() or 0
        
        # 今月の開始日を計算
        month_start = datetime(now.year, now.month, 1)
        month_end = month_start + timedelta(days=32)
        month_end = datetime(month_end.year, month_end.month, 1)
        
        # 今月のストーリーブック作成数を取得
        this_month_count = db.query(func.count(StoryBook.id)).filter(
            and_(
                StoryBook.user_id == user_id,
                StoryBook.created_at >= month_start,
                StoryBook.created_at < month_end
            )
        ).scalar() or 0
        
        # 今週の開始日を計算（日曜日を週の始まりとする）
        # weekday(): 月曜日=0, 日曜日=6
        days_since_sunday = (today.weekday() + 1) % 7
        week_start_date = today - timedelta(days=days_since_sunday)
        week_start = datetime.combine(week_start_date, datetime.min.time())
        week_end = week_start + timedelta(days=7)
        
        # 今週のストーリーブック作成数を取得
        this_week_count = db.query(func.count(StoryBook.id)).filter(
            and_(
                StoryBook.user_id == user_id,
                StoryBook.created_at >= week_start,
                StoryBook.created_at < week_end
            )
        ).scalar() or 0
        
        return {
            "user_id": user_id,
            "total": total_count,
            "this_month": this_month_count,
            "this_week": this_week_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"統計データの取得に失敗しました: {str(e)}"
        )
