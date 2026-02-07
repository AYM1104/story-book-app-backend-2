from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database.supabase_session import get_supabase_db
from app.models.story.story_setting import StorySetting
from app.models.story.story_plot import StoryPlot
from app.features._02_generate_theme.services.theme_generator import theme_generator
from pydantic import BaseModel
from typing import Dict, Any
import traceback
import time

router = APIRouter(prefix="/api/story", tags=["theme-generation"])

# スキーマ定義
class StoryGenerationRequest(BaseModel):
    story_setting_id: int
    language: str = "ja"  # デフォルトは日本語

# テーマ案を生成して保存するエンドポイント
@router.post("/story_generator", response_model=Dict[str, Any])
async def supabase_story_generator(
    request: StoryGenerationRequest,
    db: Session = Depends(get_supabase_db)
):
    """3つのテーマ案をAIで生成して保存するエンドポイント"""
    
    # 処理時間計測開始
    start_time = time.time()

    # デバックログを出力
    print("================================================")
    print("テーマ生成処理開始")
    print("================================================")
    print()  # 改行を追加
    
    try:
        # DB取得時間を計測
        db_start = time.time()
        
        # DBからストーリー設定を取得（upload_imageとuserの情報も一緒に取得）
        print(f"DBからストーリー設定を取得開始: StorySetting.id = {request.story_setting_id}")
        story_setting = db.query(StorySetting).options(
            joinedload(StorySetting.upload_image)
        ).filter(
            StorySetting.id == request.story_setting_id
        ).first()
        
        db_fetch_time = time.time() - db_start
        print(f"  - ⏱️ ストーリー設定取得時間: {db_fetch_time:.3f}秒")
        print()  # 改行を追加
        
        if not story_setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ストーリー設定ID {request.story_setting_id} が見つかりません"
            )
        
        # user_idを自動取得
        user_id = story_setting.upload_image.user_id
        
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
        
        # データ変換時間を計算
        convert_time = time.time() - convert_start
        
        # Gemini 2.5 Flashで3つのテーマ案を生成
        print(f"3つのテーマ案を生成開始（Gemini） 言語: {request.language}")
        gemini_start = time.time()
        
        # theme_generatorで3つのテーマ案を生成
        theme_data = theme_generator.generate_theme_options_only(story_setting_dict, request.language)
        
        gemini_time = time.time() - gemini_start
        print(f"⏱️ Gemini API処理時間（テーマ生成のみ）: {gemini_time:.3f}秒")
        print()  # 改行を追加
        
        # データベースに保存（テーマ情報のみ、物語本文は空）
        print("💾 データベース保存処理開始（テーマ生成のみ）")
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
        print(f"✅ 3つのテーマをDBへ保存完了 story_plot_ids = {[sp.id for sp in story_plots]}")
        print()  # 改行を追加
        
        # 全体の処理時間
        total_time = time.time() - start_time
        processing_time_ms = total_time * 1000
        print(f"⏱️ テーマ生成処理の合計時間: {total_time:.3f}秒 ({processing_time_ms:.0f}ms)")
        print(f"  - DB取得: {db_fetch_time:.3f}秒")
        print(f"  - データ変換: {convert_time:.3f}秒")
        print(f"  - Gemini API: {gemini_time:.3f}秒")
        print(f"  - DB保存: {db_save_time:.3f}秒")
        print(f"=== テーマ生成処理完了 ===")
        print()  # 改行を追加
        
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

