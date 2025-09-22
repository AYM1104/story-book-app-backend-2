from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database.session import get_db
from app.models.story.story_setting import StorySetting
from app.models.story.stroy_plot import StoryPlot
from app.service.story_generator_service import StoryGeneratorService
from pydantic import BaseModel
from typing import Dict, Any
import traceback

router = APIRouter(prefix="/story", tags=["story-generation"])

# スキーマ定義
class StoryGenerationRequest(BaseModel):
    story_setting_id: int

class ThemeSelectionRequest(BaseModel):
    story_setting_id: int
    selected_theme: str

# ストーリー生成サービス
story_generator_service = StoryGeneratorService()

# 1. テーマ案と物語本文を生成して保存
@router.post("/story_generator", response_model=Dict[str, Any])
async def story_generator(
    request: StoryGenerationRequest,
    db: Session = Depends(get_db)
):
    """ストーリー設定を元に3つのテーマ案と物語本文をAIで生成して保存するエンドポイント"""
    
    try:
        print(f"デバッグ: story_setting_id = {request.story_setting_id}")
        
        # ストーリー設定を取得（upload_imageとuserの情報も一緒に取得）
        story_setting = db.query(StorySetting).options(
            joinedload(StorySetting.upload_image)
        ).filter(
            StorySetting.id == request.story_setting_id
        ).first()
        
        print(f"デバッグ: story_setting = {story_setting}")
        
        if not story_setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ストーリー設定ID {request.story_setting_id} が見つかりません"
            )
        
        print(f"デバッグ: upload_image = {story_setting.upload_image}")
        
        # user_idを自動取得
        user_id = story_setting.upload_image.user_id
        print(f"デバッグ: user_id = {user_id}")
        
        # ストーリー設定を辞書形式に変換
        story_setting_dict = {
            "protagonist_name": story_setting.protagonist_name,
            "protagonist_type": story_setting.protagonist_type,
            "setting_place": story_setting.setting_place,
            "tone": story_setting.tone,
            "target_age": story_setting.target_age,
            "reading_level": story_setting.reading_level
        }
        
        print(f"デバッグ: story_setting_dict = {story_setting_dict}")
        
        # Gemini 2.5 Flashでテーマ案と物語本文を生成
        print("デバッグ: Gemini API呼び出し開始")
        story_data = story_generator_service.generate_complete_story(story_setting_dict)
        print(f"デバッグ: story_data = {story_data}")
        
        # データベースに保存
        # 3つのレコードを作成してそれぞれに異なるテーマを保存
        generated_stories = story_data.get("generated_stories", {})
        theme_options = story_data.get("theme_options", {})

        story_plots = []

        # theme1のレコードを作成
        theme1_story = generated_stories.get("theme1", {})
        theme1_pages = theme1_story.get("story_pages", [])
        theme1_info = theme_options.get("theme1", {})

        story_plot1 = StoryPlot(
            story_setting_id=request.story_setting_id,
            user_id=user_id,
            title=theme1_story.get("title", ""),
            description=theme1_info.get("description", ""),  # descriptionを追加
            theme_options=theme_options,  # 全テーマの情報
            selected_theme="theme1",
            keywords=theme1_info.get("keywords", []),
            generated_stories=generated_stories,  # 全テーマの物語
            page_1=theme1_pages[0].get("page_1", "") if len(theme1_pages) > 0 else "",
            page_2=theme1_pages[1].get("page_2", "") if len(theme1_pages) > 1 else "",
            page_3=theme1_pages[2].get("page_3", "") if len(theme1_pages) > 2 else "",
            page_4=theme1_pages[3].get("page_4", "") if len(theme1_pages) > 3 else "",
            page_5=theme1_pages[4].get("page_5", "") if len(theme1_pages) > 4 else "",
            current_page=1,
            conversation_context={}
        )
        story_plots.append(story_plot1)

        # theme2のレコードを作成
        theme2_story = generated_stories.get("theme2", {})
        theme2_pages = theme2_story.get("story_pages", [])
        theme2_info = theme_options.get("theme2", {})

        story_plot2 = StoryPlot(
            story_setting_id=request.story_setting_id,
            user_id=user_id,
            title=theme2_story.get("title", ""),
            description=theme2_info.get("description", ""),  # 追加
            theme_options=theme_options,
            selected_theme="theme2",
            keywords=theme2_info.get("keywords", []),
            generated_stories=generated_stories,
            page_1=theme2_pages[0].get("page_1", "") if len(theme2_pages) > 0 else "",
            page_2=theme2_pages[1].get("page_2", "") if len(theme2_pages) > 1 else "",
            page_3=theme2_pages[2].get("page_3", "") if len(theme2_pages) > 2 else "",
            page_4=theme2_pages[3].get("page_4", "") if len(theme2_pages) > 3 else "",
            page_5=theme2_pages[4].get("page_5", "") if len(theme2_pages) > 4 else "",
            current_page=1,
            conversation_context={}
        )
        story_plots.append(story_plot2)

        # theme3のレコードを作成
        theme3_story = generated_stories.get("theme3", {})
        theme3_pages = theme3_story.get("story_pages", [])
        theme3_info = theme_options.get("theme3", {})

        story_plot3 = StoryPlot(
            story_setting_id=request.story_setting_id,
            user_id=user_id,
            title=theme3_story.get("title", ""),
            description=theme3_info.get("description", ""),  # 追加
            theme_options=theme_options,
            selected_theme="theme3",
            keywords=theme3_info.get("keywords", []),
            generated_stories=generated_stories,
            page_1=theme3_pages[0].get("page_1", "") if len(theme3_pages) > 0 else "",
            page_2=theme3_pages[1].get("page_2", "") if len(theme3_pages) > 1 else "",
            page_3=theme3_pages[2].get("page_3", "") if len(theme3_pages) > 2 else "",
            page_4=theme3_pages[3].get("page_4", "") if len(theme3_pages) > 3 else "",
            page_5=theme3_pages[4].get("page_5", "") if len(theme3_pages) > 4 else "",
            current_page=1,
            conversation_context={}
        )
        story_plots.append(story_plot3)

        # データベースに保存
        for story_plot in story_plots:
            db.add(story_plot)

        db.commit()
        for story_plot in story_plots:
            db.refresh(story_plot)

        print(f"デバッグ: 3つのレコード保存完了 story_plot_ids = {[sp.id for sp in story_plots]}")
        
        return {
            "story_plot_id": story_plot.id,
            "story_setting_id": request.story_setting_id,
            "user_id": user_id,  # 自動取得したuser_idを返す
            "message": "3つのテーマ案と物語本文を生成して保存しました。お好きなテーマを選択してください。",
            "theme_options": story_data.get("theme_options", {}),
            "generated_stories": story_data.get("generated_stories", {}),
            "next_step": "theme_selection"
        }
        
    except Exception as e:
        db.rollback()
        print(f"エラーの詳細: {str(e)}")
        print(f"エラーのトレースバック: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ストーリーの生成に失敗しました: {str(e)}"
        )

# 2. 選択されたテーマの物語を保存（修正）
@router.post("/select_theme", response_model=Dict[str, Any])
async def select_theme(
    request: ThemeSelectionRequest,
    db: Session = Depends(get_db)
):
    """選択されたテーマの物語を保存するエンドポイント"""
    
    # ストーリー設定からuser_idを取得
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
    
    # ストーリープロットを取得
    story_plot = db.query(StoryPlot).filter(
        StoryPlot.story_setting_id == request.story_setting_id,
        StoryPlot.user_id == user_id
    ).first()
    
    if not story_plot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ストーリープロットが見つかりません"
        )
    
    try:
        # 選択されたテーマの情報を取得
        selected_story = story_plot.generated_stories.get(request.selected_theme, {})
        
        # keywordsはtheme_optionsから取得
        selected_theme_info = story_plot.theme_options.get(request.selected_theme, {})
        keywords = selected_theme_info.get("keywords", [])
        
        # データベースを更新
        story_plot.selected_theme = request.selected_theme
        story_plot.title = selected_story.get("title", "")
        story_plot.keywords = keywords  # theme_optionsから取得したkeywords
        
        # 各ページの内容を保存
        story_pages = selected_story.get("story_pages", [])
        print(f"デバッグ: selected_story = {selected_story}")
        print(f"デバッグ: story_pages = {story_pages}")
        print(f"デバッグ: story_pagesの長さ = {len(story_pages)}")

        if len(story_pages) >= 5:
            print(f"デバッグ: page_1の内容 = {story_pages[0]}")
            story_plot.page_1 = story_pages[0].get("page_1", "")
            story_plot.page_2 = story_pages[1].get("page_2", "")
            story_plot.page_3 = story_pages[2].get("page_3", "")
            story_plot.page_4 = story_pages[3].get("page_4", "")
            story_plot.page_5 = story_pages[4].get("page_5", "")
            print(f"デバッグ: ページ保存完了")
        else:
            print(f"デバッグ: エラー - ページ数が不足 (必要な数: 5, 実際の数: {len(story_pages)})")
        
        db.commit()
        db.refresh(story_plot)
        
        return {
            "story_plot_id": story_plot.id,
            "story_setting_id": request.story_setting_id,
            "user_id": user_id,
            "selected_theme": story_plot.selected_theme,
            "title": story_plot.title,
            "keywords": story_plot.keywords,  # keywordsも返す
            "message": f"テーマ「{story_plot.title}」が選択され、物語が保存されました。",
            "story_pages": story_pages,
            "next_step": "story_completed"
        }
        
    except Exception as e:
        db.rollback()
        print(f"エラーの詳細: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"テーマ選択の保存に失敗しました: {str(e)}"
        )

# 3. 保存されたストーリーを取得
@router.get("/story_plots/{story_plot_id}", response_model=Dict[str, Any])
async def get_story_plot(
    story_plot_id: int,
    db: Session = Depends(get_db)
):
    """保存されたストーリーを取得するエンドポイント"""
    
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
        "keywords": story_plot.keywords,  # keywordsも返す
        "theme_options": story_plot.theme_options,
        "story_pages": [
            {"page_1": story_plot.page_1},
            {"page_2": story_plot.page_2},
            {"page_3": story_plot.page_3},
            {"page_4": story_plot.page_4},
            {"page_5": story_plot.page_5}
        ],
        "created_at": story_plot.created_at,
        "updated_at": story_plot.updated_at
    }

# 4. ユーザーのストーリー一覧を取得
@router.get("/users/{user_id}/stories", response_model=Dict[str, Any])
async def get_user_stories(
    user_id: int,
    db: Session = Depends(get_db)
):
    """ユーザーのストーリー一覧を取得するエンドポイント"""
    
    story_plots = db.query(StoryPlot).filter(
        StoryPlot.user_id == user_id
    ).order_by(StoryPlot.created_at.desc()).all()
    
    stories = []
    for plot in story_plots:
        stories.append({
            "story_plot_id": plot.id,
            "title": plot.title,
            "selected_theme": plot.selected_theme,
            "created_at": plot.created_at,
            "updated_at": plot.updated_at
        })
    
    return {
        "user_id": user_id,
        "total_count": len(stories),
        "stories": stories
    }

# 5. 後方互換性のためのエンドポイント
@router.post("/get_selected_story", response_model=Dict[str, Any])
async def get_selected_story_legacy(
    request: ThemeSelectionRequest,
    db: Session = Depends(get_db)
):
    """後方互換性のためのエンドポイント"""
    return await select_theme(request, db)