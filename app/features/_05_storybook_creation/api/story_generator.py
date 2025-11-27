from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database.supabase_session import get_supabase_db
from app.models.story.story_setting import StorySetting
from app.models.story.story_plot import StoryPlot
from app.models.story.story_book import StoryBook
from app.features._02_generation_plan.services.story_line.story_line_generator import StoryGeneratorService
from app.service.credits import CreditsService, PricingService
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import traceback
import time

router = APIRouter(prefix="/api/story", tags=["story-generation"])

# スキーマ定義
class StoryGenerationRequest(BaseModel):
    story_setting_id: int

class ThemeSelectionRequest(BaseModel):
    story_setting_id: int
    selected_theme: str
    story_pages: int = 5  # 物語ページ数（3, 5, 7, 10のいずれか、デフォルトは5）

# ストーリー生成サービス
story_generator_service = StoryGeneratorService()

# クエリ用スキーマ
class StoryPlotQueryParams(BaseModel):
    user_id: str
    story_setting_id: int
    limit: int = 3

# 1. テーマ案と物語本文を生成して保存（Supabase用）
@router.post("/story_generator", response_model=Dict[str, Any])
async def supabase_story_generator(
    request: StoryGenerationRequest,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用のストーリー設定を元に3つのテーマ案と物語本文をAIで生成して保存するエンドポイント"""
    
    # 処理時間計測開始
    start_time = time.time()
    print(f"=== テーマ生成処理開始 (Supabase) ===")
    print(f"Story Setting ID: {request.story_setting_id}")
    
    try:
        # DB取得時間を計測
        db_start = time.time()
        
        # ストーリー設定を取得（upload_imageとuserの情報も一緒に取得）
        story_setting = db.query(StorySetting).options(
            joinedload(StorySetting.upload_image)
        ).filter(
            StorySetting.id == request.story_setting_id
        ).first()
        
        db_fetch_time = time.time() - db_start
        print(f"⏱️ DB取得時間: {db_fetch_time:.3f}秒")
        
        if not story_setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ストーリー設定ID {request.story_setting_id} が見つかりません"
            )
        
        # user_idを自動取得
        user_id = story_setting.upload_image.user_id
        print(f"User ID: {user_id}")
        
        # データ変換時間を計測
        convert_start = time.time()
        
        # ストーリー設定を辞書形式に変換
        story_setting_dict = {
            "protagonist_name": story_setting.protagonist_name,
            "protagonist_type": story_setting.protagonist_type,
            "setting_place": story_setting.setting_place,
            "tone": story_setting.tone,
            "target_age": story_setting.target_age,
            "reading_level": story_setting.reading_level
        }
        
        convert_time = time.time() - convert_start
        print(f"⏱️ データ変換時間: {convert_time:.3f}秒")
        
        # Gemini 2.5 Flashで3つのテーマ案のみを生成（高速化版）
        print("🤖 Gemini API呼び出し開始（3つのテーマのみ生成）")
        gemini_start = time.time()
        
        theme_data = story_generator_service.generate_theme_options_only(story_setting_dict)
        
        gemini_time = time.time() - gemini_start
        print(f"⏱️ Gemini API処理時間（テーマのみ）: {gemini_time:.3f}秒")
        
        # データベースに保存（テーマ情報のみ、物語本文は空）
        print("💾 データベース保存処理開始（テーマのみ）")
        db_save_start = time.time()
        
        # 3つのレコードを作成してそれぞれに異なるテーマを保存
        theme_options = theme_data.get("theme_options", {})

        story_plots = []

        # 3つのテーマをループで処理
        for theme_key in ["theme1", "theme2", "theme3"]:
            theme_info = theme_options.get(theme_key, {})

            story_plot = StoryPlot(
                story_setting_id=request.story_setting_id,
                user_id=user_id,
                title=theme_info.get("title", ""),
                description=theme_info.get("description", ""),
                theme_options=theme_options,
                selected_theme=theme_key,
                keywords=theme_info.get("keywords", []),
                generated_stories={},  # 空のまま（テーマ選択後に生成）
                page_1="",  # 空のまま（テーマ選択後に生成）
                page_2="",
                page_3="",
                page_4="",
                page_5="",
                current_page=1,
                conversation_context={}
            )
            story_plots.append(story_plot)

        # データベースに保存
        for story_plot in story_plots:
            db.add(story_plot)

        db.commit()
        for story_plot in story_plots:
            db.refresh(story_plot)

        db_save_time = time.time() - db_save_start
        print(f"⏱️ DB保存時間: {db_save_time:.3f}秒")
        print(f"✅ 3つのテーマレコード保存完了 story_plot_ids = {[sp.id for sp in story_plots]}")
        
        # 全体の処理時間
        total_time = time.time() - start_time
        processing_time_ms = total_time * 1000
        print(f"⏱️ テーマ生成処理の合計時間: {total_time:.3f}秒 ({processing_time_ms:.0f}ms)")
        print(f"  - DB取得: {db_fetch_time:.3f}秒")
        print(f"  - データ変換: {convert_time:.3f}秒")
        print(f"  - Gemini API: {gemini_time:.3f}秒")
        print(f"  - DB保存: {db_save_time:.3f}秒")
        print(f"=== テーマ生成処理完了 ===")
        
        return {
            "story_plot_ids": [sp.id for sp in story_plots],
            "story_setting_id": request.story_setting_id,
            "user_id": user_id,
            "message": "3つのテーマ案を生成しました。お好きなテーマを選択してください。",
            "theme_options": theme_data.get("theme_options", {}),
            "next_step": "theme_selection",
            "processing_time_ms": processing_time_ms,
            "timing_details": {
                "db_fetch": round(db_fetch_time * 1000, 0),
                "data_conversion": round(convert_time * 1000, 0),
                "gemini_api": round(gemini_time * 1000, 0),
                "db_save": round(db_save_time * 1000, 0),
                "total": round(total_time * 1000, 0)
            }
        }
        
    except Exception as e:
        db.rollback()
        error_time = time.time() - start_time
        print(f"❌ テーマ生成処理エラー（処理時間: {error_time:.3f}秒）: {str(e)}")
        print(f"エラーのトレースバック: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ストーリーの生成に失敗しました: {str(e)}"
        )

# 2. 選択されたテーマの物語を生成して保存（Supabase用）
@router.post("/select_theme", response_model=Dict[str, Any])
async def supabase_select_theme(
    request: ThemeSelectionRequest,
    db: Session = Depends(get_supabase_db)
):
    """選択されたテーマの物語を生成して保存するエンドポイント"""
    
    # 処理時間計測開始
    start_time = time.time()
    print(f"=== テーマ選択＆物語生成処理開始 (Supabase) ===")
    print(f"Story Setting ID: {request.story_setting_id}")
    print(f"Selected Theme: {request.selected_theme}")
    print(f"Request Story Pages: {request.story_pages}")  # デバッグ: リクエストのページ数を確認
    
    try:
        # ストーリー設定からuser_idを取得
        db_start = time.time()
        
        story_setting = db.query(StorySetting).options(
            joinedload(StorySetting.upload_image)
        ).filter(
            StorySetting.id == request.story_setting_id
        ).first()
        
        if not story_setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ストーリー設定ID {request.story_setting_id} が見つかりません"
            )
        
        user_id = story_setting.upload_image.user_id
        
        db_fetch_time = time.time() - db_start
        print(f"⏱️ DB取得時間: {db_fetch_time:.3f}秒")
        
        # ---------------------------------------------------------
        # 1. プランの事前チェック
        # ---------------------------------------------------------
        
        # ユーザーのプランを取得し、ページ数制限のみ確認
        user_plan = CreditsService.get_plan(db, user_id)
        
        if not PricingService.is_allowed_for_plan(request.story_pages, user_plan):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PLAN_LIMIT",
                    "message": "現在のプランでは選択されたページ数の絵本を作成できません",
                    "plan": user_plan.value,
                    "requested_pages": request.story_pages,
                    "allowed_pages": PricingService.ALLOWED_PAGES.get(user_plan, [])
                }
            )

        # 選択されたテーマのストーリープロットを取得
        story_plot = db.query(StoryPlot).filter(
            StoryPlot.story_setting_id == request.story_setting_id,
            StoryPlot.user_id == user_id,
            StoryPlot.selected_theme == request.selected_theme
        ).first()
        
        if not story_plot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"選択されたテーマ {request.selected_theme} のストーリープロットが見つかりません"
            )
        
        # ---------------------------------------------------------
        # 2. クレジット消費
        # ---------------------------------------------------------
        
        # 必要クレジット数を計算
        required_credits = PricingService.get_required_credits(request.story_pages)
        
        print(f"💰 クレジット消費処理開始２: pages={request.story_pages}, plot_id={story_plot.id}")
        print(f"DEBUG: spend_credits parameters - user_id={user_id}, amount={required_credits}, work_id={story_plot.id}")
        
        # クレジットを消費（この時点でDBに反映されるが、トランザクション内なのでロールバック可能）
        # auto_commit=Falseにして、後のcommitで一括コミットする
        CreditsService.spend_credits(
            db=db,
            user_id=user_id,
            amount=required_credits,
            reason=f"story_generation_theme_{request.selected_theme}",
            work_id=None,  # StoryBook未作成のため紐づけは後続フローで実施
            auto_commit=False
        )
        
        print(f"💸 クレジット消費完了: {required_credits}クレジット")

        # 選択されたテーマの情報を取得
        selected_theme_info = story_plot.theme_options.get(request.selected_theme, {})
        theme_title = selected_theme_info.get("title", "物語")
        keywords = selected_theme_info.get("keywords", [])
        
        # ストーリー設定を辞書形式に変換
        convert_start = time.time()
        story_setting_dict = {
            "protagonist_name": story_setting.protagonist_name,
            "protagonist_type": story_setting.protagonist_type,
            "setting_place": story_setting.setting_place,
            "tone": story_setting.tone,
            "target_age": story_setting.target_age,
            "reading_level": story_setting.reading_level
        }
        convert_time = time.time() - convert_start
        print(f"⏱️ データ変換時間: {convert_time:.3f}秒")
        
        # ページ数の検証（PricingServiceでもチェック済みだが念のため）
        if request.story_pages not in [3, 5, 7, 10]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"無効なページ数です。3, 5, 7, 10のいずれかを指定してください。指定値: {request.story_pages}"
            )
        
        # Gemini APIで選択されたテーマの物語本文を生成（動的ページ数）
        print(f"🤖 Gemini API呼び出し開始（テーマ「{theme_title}」の物語生成、{request.story_pages}ページ）")
        gemini_start = time.time()
        
        story_data = story_generator_service.generate_single_story(
            story_setting_dict, 
            theme_title,
            story_pages=request.story_pages
        )
        
        gemini_time = time.time() - gemini_start
        print(f"⏱️ Gemini API処理時間（物語生成）: {gemini_time:.3f}秒")
        
        # 各ページの内容を保存（動的ページ数に対応）
        story_pages = story_data.get("story_pages", [])
        print(f"デバッグ: story_pages = {story_pages}")
        print(f"デバッグ: story_pagesの長さ = {len(story_pages)}")
        print(f"デバッグ: リクエストされたページ数 = {request.story_pages}")

        # ページ数をリセット（空文字で初期化、最大10ページまで）
        for i in range(1, 11):
            page_key = f"page_{i}"
            if hasattr(story_plot, page_key):
                setattr(story_plot, page_key, "")
        
        # 生成されたページ数に応じて保存（最大10ページまで）
        max_save_pages = min(len(story_pages), 10)
        for i, page_data in enumerate(story_pages[:max_save_pages], 1):
            page_key = f"page_{i}"
            if hasattr(story_plot, page_key):
                # 新しい形式（page_no, story_text, background_prompt）に対応
                if isinstance(page_data, dict):
                    if "story_text" in page_data:
                        # 新しい形式: {"page_no": 1, "story_text": "...", "background_prompt": "..."}
                        setattr(story_plot, page_key, page_data["story_text"])
                    elif page_key in page_data:
                        # 旧形式との互換性: {"page_1": "..."}
                        setattr(story_plot, page_key, page_data[page_key])
                    elif f"page_{page_data.get('page_no', i)}" == page_key:
                        # page_noを使用した新しい形式
                        setattr(story_plot, page_key, page_data.get("story_text", ""))
        
        print(f"✅ ページ保存完了（{max_save_pages}ページ保存）")
        
        # データベース保存
        db_save_start = time.time()
        story_plot.title = story_data.get("title", theme_title)
        story_plot.keywords = keywords
        
        db.commit()
        db.refresh(story_plot)
        
        db_save_time = time.time() - db_save_start
        print(f"⏱️ DB保存時間: {db_save_time:.3f}秒")
        
        # 全体の処理時間
        total_time = time.time() - start_time
        processing_time_ms = total_time * 1000
        print(f"⏱️ 物語生成処理の合計時間: {total_time:.3f}秒 ({processing_time_ms:.0f}ms)")
        print(f"  - DB取得: {db_fetch_time:.3f}秒")
        print(f"  - データ変換: {convert_time:.3f}秒")
        print(f"  - Gemini API: {gemini_time:.3f}秒")
        print(f"  - DB保存: {db_save_time:.3f}秒")
        print(f"=== 物語生成処理完了 ===")
        
        return {
            "story_plot_id": story_plot.id,
            "story_setting_id": request.story_setting_id,
            "user_id": user_id,
            "selected_theme": story_plot.selected_theme,
            "title": story_plot.title,
            "keywords": story_plot.keywords,
            "message": f"テーマ「{story_plot.title}」の物語を生成して保存しました。",
            "story_pages": request.story_pages,
            "pages": [
                {f"page_{i}": getattr(story_plot, f"page_{i}", None) or ""}
                for i in range(1, 11)
                if getattr(story_plot, f"page_{i}", None)
            ],
            "next_step": "story_completed",
            "processing_time_ms": processing_time_ms,
            "credits_spent": required_credits,  # 消費クレジット数を返す
            "timing_details": {
                "db_fetch": round(db_fetch_time * 1000, 0),
                "data_conversion": round(convert_time * 1000, 0),
                "gemini_api": round(gemini_time * 1000, 0),
                "db_save": round(db_save_time * 1000, 0),
                "total": round(total_time * 1000, 0)
            }
        }
        
    except HTTPException as he:
        # HTTP例外はそのまま再送出
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        error_time = time.time() - start_time
        print(f"❌ 物語生成処理エラー（処理時間: {error_time:.3f}秒）: {str(e)}")
        print(f"エラーのトレースバック: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"物語の生成に失敗しました: {str(e)}"
        )

# 3. 保存されたストーリーを取得（Supabase用）
@router.get("/story_plots/{story_plot_id}", response_model=Dict[str, Any])
async def get_supabase_story_plot(
    story_plot_id: int,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用の保存されたストーリーを取得するエンドポイント"""
    
    story_plot = db.query(StoryPlot).filter(
        StoryPlot.id == story_plot_id
    ).first()
    
    if not story_plot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ストーリープロットID {story_plot_id} が見つかりません"
        )
    
    return {
        "story_plot_id": story_plot.id,
        "story_setting_id": story_plot.story_setting_id,
        "user_id": story_plot.user_id,
        "title": story_plot.title,
        "selected_theme": story_plot.selected_theme,
        "keywords": story_plot.keywords,
        "theme_options": story_plot.theme_options,
        "story_pages": [
            {f"page_{i}": getattr(story_plot, f"page_{i}", None) or ""}
            for i in range(1, 11)
            if getattr(story_plot, f"page_{i}", None)
        ],
        "created_at": story_plot.created_at.isoformat(),
        "updated_at": story_plot.updated_at.isoformat()
    }

# 4. ユーザーのストーリー一覧を取得（Supabase用）
@router.get("/users/{user_id}/stories", response_model=Dict[str, Any])
async def get_supabase_user_stories(
    user_id: str,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用のユーザーのストーリー一覧を取得するエンドポイント"""
    
    story_plots = db.query(StoryPlot).filter(
        StoryPlot.user_id == user_id
    ).order_by(StoryPlot.created_at.desc()).all()
    
    stories = []
    for plot in story_plots:
        stories.append({
            "story_plot_id": plot.id,
            "title": plot.title,
            "selected_theme": plot.selected_theme,
            "created_at": plot.created_at.isoformat(),
            "updated_at": plot.updated_at.isoformat()
        })
    
    return {
        "user_id": user_id,
        "total_count": len(stories),
        "stories": stories
    }

# 5. ユーザーIDと設定IDで最新のタイトルを取得（Supabase用）
@router.get("/story_plots", response_model=Dict[str, Any])
async def list_supabase_story_plots(
    user_id: str,
    story_setting_id: int,
    limit: int = 3,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用のユーザーIDと設定IDで `story_plots` の最新タイトルを最大 `limit` 件返す"""

    if limit <= 0:
        limit = 1
    if limit > 50:
        limit = 50

    plots = (
        db.query(StoryPlot)
        .filter(
            StoryPlot.user_id == user_id,
            StoryPlot.story_setting_id == story_setting_id,
            StoryPlot.title.isnot(None)
        )
        .order_by(StoryPlot.created_at.desc())
        .limit(limit)
        .all()
    )

    items = [
        {
            "story_plot_id": p.id,
            "title": p.title,
            "description": p.description,
            "selected_theme": p.selected_theme,
            "created_at": p.created_at.isoformat(),
        }
        for p in plots
    ]

    return {
        "user_id": user_id,
        "story_setting_id": story_setting_id,
        "count": len(items),
        "items": items,
    }

# 6. 週間統計を取得（Supabase用）
@router.get("/users/{user_id}/weekly_stats", response_model=Dict[str, Any])
async def get_supabase_weekly_stats(
    user_id: str,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用の週間統計を取得するエンドポイント（日曜日始まり）
    
    現在の週（日曜日から土曜日）の日別絵本作成数を返す
    """
    try:
        # 現在の日時を取得
        now = datetime.now()
        
        # 日曜日を週の始まりとして計算
        # weekday(): 月曜日=0, 日曜日=6
        days_since_sunday = (now.weekday() + 1) % 7  # 日曜日からの日数を計算
        week_start = now - timedelta(days=days_since_sunday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 週の終わり（次の日曜日の0時）
        week_end = week_start + timedelta(days=7)
        
        # 週間の絵本作成数を日別で取得
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
        
        # 日別のカウントを辞書に変換
        daily_counts_dict = {str(row.date): row.count for row in daily_counts_query}
        
        # 週の各日（日曜日から土曜日）のカウントを取得
        daily_counts = []
        week_total = 0
        
        for i in range(7):
            current_date = week_start + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            count = daily_counts_dict.get(date_str, 0)
            
            # 曜日の略称を取得（日=0, 月=1, ..., 土=6）
            day_names = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
            day_name = day_names[i]
            
            daily_counts.append({
                "day": day_name,
                "date": date_str,
                "count": count
            })
            week_total += count
        
        return {
            "week_total": week_total,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "daily_counts": daily_counts
        }
        
    except Exception as e:
        print(f"❌ 週間統計取得エラー: {str(e)}")
        print(f"エラーのトレースバック: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"週間統計の取得に失敗しました: {str(e)}"
        )
