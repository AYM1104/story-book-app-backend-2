from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database.supabase_session import get_supabase_db
from app.models.story.supabase_story_setting import SupabaseStorySetting
from app.models.story.supabase_story_plot import SupabaseStoryPlot
from app.service.story_generator_service import StoryGeneratorService
from pydantic import BaseModel
from typing import Dict, Any
import traceback
import time

router = APIRouter(prefix="/story", tags=["story-generation"])

# スキーマ定義
class StoryGenerationRequest(BaseModel):
    story_setting_id: int

class ThemeSelectionRequest(BaseModel):
    story_setting_id: int
    selected_theme: str

# ストーリー生成サービス
story_generator_service = StoryGeneratorService()

# クエリ用スキーマ
class StoryPlotQueryParams(BaseModel):
    user_id: int
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
        story_setting = db.query(SupabaseStorySetting).options(
            joinedload(SupabaseStorySetting.upload_image)
        ).filter(
            SupabaseStorySetting.id == request.story_setting_id
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

            story_plot = SupabaseStoryPlot(
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
    """Supabase用の選択されたテーマの物語を生成して保存するエンドポイント"""
    
    # 処理時間計測開始
    start_time = time.time()
    print(f"=== テーマ選択＆物語生成処理開始 (Supabase) ===")
    print(f"Story Setting ID: {request.story_setting_id}")
    print(f"Selected Theme: {request.selected_theme}")
    
    try:
        # ストーリー設定からuser_idを取得
        db_start = time.time()
        
        story_setting = db.query(SupabaseStorySetting).options(
            joinedload(SupabaseStorySetting.upload_image)
        ).filter(
            SupabaseStorySetting.id == request.story_setting_id
        ).first()
        
        if not story_setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ストーリー設定ID {request.story_setting_id} が見つかりません"
            )
        
        user_id = story_setting.upload_image.user_id
        
        # 選択されたテーマのストーリープロットを取得
        story_plot = db.query(SupabaseStoryPlot).filter(
            SupabaseStoryPlot.story_setting_id == request.story_setting_id,
            SupabaseStoryPlot.user_id == user_id,
            SupabaseStoryPlot.selected_theme == request.selected_theme
        ).first()
        
        if not story_plot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"選択されたテーマ {request.selected_theme} のストーリープロットが見つかりません"
            )
        
        db_fetch_time = time.time() - db_start
        print(f"⏱️ DB取得時間: {db_fetch_time:.3f}秒")
        
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
        
        # Gemini APIで選択されたテーマの物語本文（5ページ）を生成
        print(f"🤖 Gemini API呼び出し開始（テーマ「{theme_title}」の物語生成）")
        gemini_start = time.time()
        
        story_data = story_generator_service.generate_single_story(
            story_setting_dict, 
            theme_title
        )
        
        gemini_time = time.time() - gemini_start
        print(f"⏱️ Gemini API処理時間（物語生成）: {gemini_time:.3f}秒")
        
        # 各ページの内容を保存
        story_pages = story_data.get("story_pages", [])
        print(f"デバッグ: story_pages = {story_pages}")
        print(f"デバッグ: story_pagesの長さ = {len(story_pages)}")

        if len(story_pages) >= 5:
            story_plot.page_1 = story_pages[0].get("page_1", "")
            story_plot.page_2 = story_pages[1].get("page_2", "")
            story_plot.page_3 = story_pages[2].get("page_3", "")
            story_plot.page_4 = story_pages[3].get("page_4", "")
            story_plot.page_5 = story_pages[4].get("page_5", "")
            print(f"✅ ページ保存完了")
        else:
            print(f"⚠️ エラー - ページ数が不足 (必要な数: 5, 実際の数: {len(story_pages)})")
        
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
            "story_pages": [
                {"page_1": story_plot.page_1},
                {"page_2": story_plot.page_2},
                {"page_3": story_plot.page_3},
                {"page_4": story_plot.page_4},
                {"page_5": story_plot.page_5}
            ],
            "next_step": "story_completed",
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
    
    story_plot = db.query(SupabaseStoryPlot).filter(
        SupabaseStoryPlot.id == story_plot_id
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
            {"page_1": story_plot.page_1},
            {"page_2": story_plot.page_2},
            {"page_3": story_plot.page_3},
            {"page_4": story_plot.page_4},
            {"page_5": story_plot.page_5}
        ],
        "created_at": story_plot.created_at.isoformat(),
        "updated_at": story_plot.updated_at.isoformat()
    }

# 4. ユーザーのストーリー一覧を取得（Supabase用）
@router.get("/users/{user_id}/stories", response_model=Dict[str, Any])
async def get_supabase_user_stories(
    user_id: int,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用のユーザーのストーリー一覧を取得するエンドポイント"""
    
    story_plots = db.query(SupabaseStoryPlot).filter(
        SupabaseStoryPlot.user_id == user_id
    ).order_by(SupabaseStoryPlot.created_at.desc()).all()
    
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
    user_id: int,
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
        db.query(SupabaseStoryPlot)
        .filter(
            SupabaseStoryPlot.user_id == user_id,
            SupabaseStoryPlot.story_setting_id == story_setting_id,
            SupabaseStoryPlot.title.isnot(None)
        )
        .order_by(SupabaseStoryPlot.created_at.desc())
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
