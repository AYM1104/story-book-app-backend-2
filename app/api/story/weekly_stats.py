from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import Dict, Any

from app.database.supabase_session import get_supabase_db
from app.models.story.story_book import StoryBook

router = APIRouter(prefix="/storybook", tags=["storybook-statistics"])


@router.get("/weekly-stats/{user_id}")
async def get_weekly_storybook_stats(
    user_id: str,
    db: Session = Depends(get_supabase_db)
):
    """週間（日曜日から土曜日）の日別絵本作成数を取得するエンドポイント"""
    try:
        # 現在の日時を取得
        now = datetime.now()
        today = now.date()
        
        # 日曜日を週の始まりとして計算
        # weekday(): 月曜日=0, 日曜日=6
        days_since_sunday = (today.weekday() + 1) % 7
        week_start_date = today - timedelta(days=days_since_sunday)
        week_start = datetime.combine(week_start_date, datetime.min.time())
        week_end = week_start + timedelta(days=7)
        
        # 週間の絵本作成数を日別で取得（1回のクエリで全データを取得）
        daily_counts_query = (
            db.query(
                func.date(StoryBook.created_at).label('date'),
                func.count(StoryBook.id).label('count')
            )
            .filter(
                and_(
                    StoryBook.user_id == user_id,
                    StoryBook.created_at >= week_start,
                    StoryBook.created_at < week_end
                )
            )
            .group_by(func.date(StoryBook.created_at))
            .all()
        )
        
        # 日別のカウントを辞書に変換（キーは日付文字列）
        daily_counts_dict = {str(row.date): row.count for row in daily_counts_query}
        
        # 週の各日（日曜日から土曜日）のカウントを配列形式で生成
        weekday_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        daily_counts_array = []
        total_count = 0
        
        for i in range(7):
            current_date = week_start_date + timedelta(days=i)
            date_str = current_date.isoformat()
            count = daily_counts_dict.get(date_str, 0)
            
            daily_counts_array.append({
                "day": weekday_names[i],
                "count": count
            })
            total_count += count
        
        # 辞書形式も生成（後方互換性のため）
        daily_counts = {weekday_names[i]: daily_counts_array[i]["count"] for i in range(7)}
        
        return {
            "user_id": user_id,
            "week_start": week_start_date.isoformat(),
            "week_end": (week_start_date + timedelta(days=6)).isoformat(),
            "daily_counts": daily_counts,
            "total_count": total_count,
            "daily_counts_array": daily_counts_array
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"週間統計の取得に失敗しました: {str(e)}"
        )

