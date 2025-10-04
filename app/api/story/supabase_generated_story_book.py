from fastapi import APIRouter, Depends, HTTPException, status
import json
from sqlalchemy.orm import Session
from app.database.supabase_session import get_supabase_db
from app.models.story.supabase_story_plot import SupabaseStoryPlot
from app.models.story.supabase_generated_story_book import SupabaseGeneratedStoryBook
from app.schemas.story.generated_story_book import (
    ThemeConfirmationRequest,
    ThemeConfirmationResponse,
    GeneratedStoryBookCreate,
    GeneratedStoryBookResponse,
    StorybookImageUrlUpdateRequest,
    StorybookImageUrlUpdateResponse,
    ImageGenerationStatus
)

router = APIRouter(prefix="/storybook", tags=["generated-storybook"])

@router.post("/confirm-theme-and-create", response_model=ThemeConfirmationResponse)
async def supabase_confirm_theme_and_create_storybook(
    request: ThemeConfirmationRequest,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用のテーマ選択後にストーリーブックを作成するエンドポイント"""
    
    try:
        # 1. StoryPlotから選択されたテーマの情報を取得
        story_plot = db.query(SupabaseStoryPlot).filter(SupabaseStoryPlot.id == request.story_plot_id).first()
        if not story_plot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"StoryPlot ID {request.story_plot_id} が見つかりません"
            )
        
        # 2. 選択されたテーマが存在するかチェック
        if not story_plot.generated_stories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="生成されたストーリーが見つかりません"
            )
        
        if request.selected_theme not in story_plot.generated_stories:
            available_themes = list(story_plot.generated_stories.keys())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"選択されたテーマ '{request.selected_theme}' が見つかりません。利用可能なテーマ: {available_themes}"
            )
        
        # 3. 選択されたテーマのストーリー内容を取得（辞書 → JSON文字列に変換）
        selected_story_content_dict = story_plot.generated_stories[request.selected_theme]
        # Textカラムに保存可能なようJSON文字列化
        selected_story_content = json.dumps(selected_story_content_dict, ensure_ascii=False)
        
        # 4. GeneratedStoryBookレコードを作成
        new_storybook = SupabaseGeneratedStoryBook(
            story_plot_id=story_plot.id,
            user_id=story_plot.user_id,
            title=story_plot.title or "無題のえほん",
            description=story_plot.description,
            keywords=story_plot.keywords,
            story_content=selected_story_content,
            page_1=story_plot.page_1 or "",
            page_2=story_plot.page_2 or "",
            page_3=story_plot.page_3 or "",
            page_4=story_plot.page_4 or "",
            page_5=story_plot.page_5 or "",
            image_generation_status=ImageGenerationStatus.PENDING
        )
        
        db.add(new_storybook)
        db.commit()
        db.refresh(new_storybook)
        
        return ThemeConfirmationResponse(
            success=True,
            message="ストーリーブックが作成されました。画像生成を開始できます。",
            storybook_id=new_storybook.id,
            selected_theme=request.selected_theme
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ストーリーブック作成に失敗しました: {str(e)}"
        )

@router.get("/{storybook_id}", response_model=GeneratedStoryBookResponse)
async def get_supabase_storybook(
    storybook_id: int,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用のストーリーブック詳細を取得するエンドポイント"""
    
    storybook = db.query(SupabaseGeneratedStoryBook).filter(
        SupabaseGeneratedStoryBook.id == storybook_id
    ).first()
    
    if not storybook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"StoryBook ID {storybook_id} が見つかりません"
        )
    
    # GCSの画像URLを公開URLに変換
    from app.service.gcs_storage_service import GCSStorageService
    gcs_service = GCSStorageService()
    
    # 各ページの画像URLをGCSの公開URLに変換
    if storybook.page_1_image_url and not storybook.page_1_image_url.startswith('http'):
        storybook.page_1_image_url = gcs_service.get_public_url(storybook.page_1_image_url)
    
    if storybook.page_2_image_url and not storybook.page_2_image_url.startswith('http'):
        storybook.page_2_image_url = gcs_service.get_public_url(storybook.page_2_image_url)
    
    if storybook.page_3_image_url and not storybook.page_3_image_url.startswith('http'):
        storybook.page_3_image_url = gcs_service.get_public_url(storybook.page_3_image_url)
    
    if storybook.page_4_image_url and not storybook.page_4_image_url.startswith('http'):
        storybook.page_4_image_url = gcs_service.get_public_url(storybook.page_4_image_url)
    
    if storybook.page_5_image_url and not storybook.page_5_image_url.startswith('http'):
        storybook.page_5_image_url = gcs_service.get_public_url(storybook.page_5_image_url)
    
    return {
        "id": storybook.id,
        "story_plot_id": storybook.story_plot_id,
        "user_id": storybook.user_id,
        "title": storybook.title,
        "description": storybook.description,
        "keywords": storybook.keywords,
        "story_content": storybook.story_content,
        "page_1": storybook.page_1,
        "page_2": storybook.page_2,
        "page_3": storybook.page_3,
        "page_4": storybook.page_4,
        "page_5": storybook.page_5,
        "page_1_image_url": storybook.page_1_image_url,
        "page_2_image_url": storybook.page_2_image_url,
        "page_3_image_url": storybook.page_3_image_url,
        "page_4_image_url": storybook.page_4_image_url,
        "page_5_image_url": storybook.page_5_image_url,
        "image_generation_status": storybook.image_generation_status,
        "created_at": storybook.created_at,
        "updated_at": storybook.updated_at
    }

@router.get("/user/{user_id}", response_model=list[GeneratedStoryBookResponse])
async def get_supabase_user_storybooks(
    user_id: int,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用のユーザーのストーリーブック一覧を取得するエンドポイント"""
    
    storybooks = db.query(SupabaseGeneratedStoryBook).filter(
        SupabaseGeneratedStoryBook.user_id == user_id
    ).order_by(SupabaseGeneratedStoryBook.created_at.desc()).all()
    
    return [
        {
            "id": storybook.id,
            "story_plot_id": storybook.story_plot_id,
            "user_id": storybook.user_id,
            "title": storybook.title,
            "description": storybook.description,
            "keywords": storybook.keywords,
            "story_content": storybook.story_content,
            "page_1": storybook.page_1,
            "page_2": storybook.page_2,
            "page_3": storybook.page_3,
            "page_4": storybook.page_4,
            "page_5": storybook.page_5,
            "page_1_image_url": storybook.page_1_image_url,
            "page_2_image_url": storybook.page_2_image_url,
            "page_3_image_url": storybook.page_3_image_url,
            "page_4_image_url": storybook.page_4_image_url,
            "page_5_image_url": storybook.page_5_image_url,
            "image_generation_status": storybook.image_generation_status,
            "created_at": storybook.created_at,
            "updated_at": storybook.updated_at
        }
        for storybook in storybooks
    ]

@router.post("/update-image-urls", response_model=StorybookImageUrlUpdateResponse)
async def update_supabase_storybook_image_urls(
    request: StorybookImageUrlUpdateRequest,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用の生成された画像のURLをストーリーブックに紐づけるエンドポイント"""
    
    try:
        storybook = db.query(SupabaseGeneratedStoryBook).filter(
            SupabaseGeneratedStoryBook.id == request.storybook_id
        ).first()
        
        if not storybook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"StoryBook ID {request.storybook_id} が見つかりません"
            )
        
        # 更新されたページを記録
        updated_pages = []
        
        # 各ページの画像URLを更新
        if request.page_1_image_url:
            storybook.page_1_image_url = request.page_1_image_url
            updated_pages.append("page_1")
        
        if request.page_2_image_url:
            storybook.page_2_image_url = request.page_2_image_url
            updated_pages.append("page_2")
        
        if request.page_3_image_url:
            storybook.page_3_image_url = request.page_3_image_url
            updated_pages.append("page_3")
        
        if request.page_4_image_url:
            storybook.page_4_image_url = request.page_4_image_url
            updated_pages.append("page_4")
        
        if request.page_5_image_url:
            storybook.page_5_image_url = request.page_5_image_url
            updated_pages.append("page_5")
        
        # 画像生成状態を更新
        if updated_pages:
            storybook.image_generation_status = ImageGenerationStatus.COMPLETED
        
        db.commit()
        
        return StorybookImageUrlUpdateResponse(
            success=True,
            message=f"画像URLが正常に更新されました（{len(updated_pages)}ページ）",
            storybook_id=storybook.id,
            updated_pages=updated_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"画像URL更新に失敗しました: {str(e)}"
        )

@router.put("/{storybook_id}/image-generation-status")
async def update_supabase_image_generation_status(
    storybook_id: int,
    status: ImageGenerationStatus,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用の画像生成状態を更新するエンドポイント"""
    
    storybook = db.query(SupabaseGeneratedStoryBook).filter(
        SupabaseGeneratedStoryBook.id == storybook_id
    ).first()
    
    if not storybook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"StoryBook ID {storybook_id} が見つかりません"
        )
    
    storybook.image_generation_status = status
    db.commit()
    
    return {"message": f"画像生成状態が '{status}' に更新されました"}

# ストーリーブック一覧取得エンドポイント（Supabase用）
@router.get("/", response_model=list[GeneratedStoryBookResponse])
def get_supabase_storybooks(db: Session = Depends(get_supabase_db)):
    """Supabase用のストーリーブック一覧取得エンドポイント"""
    
    storybooks = db.query(SupabaseGeneratedStoryBook).order_by(
        SupabaseGeneratedStoryBook.created_at.desc()
    ).all()
    
    return [
        {
            "id": storybook.id,
            "story_plot_id": storybook.story_plot_id,
            "user_id": storybook.user_id,
            "title": storybook.title,
            "description": storybook.description,
            "keywords": storybook.keywords,
            "story_content": storybook.story_content,
            "page_1": storybook.page_1,
            "page_2": storybook.page_2,
            "page_3": storybook.page_3,
            "page_4": storybook.page_4,
            "page_5": storybook.page_5,
            "page_1_image_url": storybook.page_1_image_url,
            "page_2_image_url": storybook.page_2_image_url,
            "page_3_image_url": storybook.page_3_image_url,
            "page_4_image_url": storybook.page_4_image_url,
            "page_5_image_url": storybook.page_5_image_url,
            "image_generation_status": storybook.image_generation_status,
            "created_at": storybook.created_at,
            "updated_at": storybook.updated_at
        }
        for storybook in storybooks
    ]

# ストーリーブック削除エンドポイント（Supabase用）
@router.delete("/{storybook_id}")
def delete_supabase_storybook(storybook_id: int, db: Session = Depends(get_supabase_db)):
    """Supabase用のストーリーブック削除エンドポイント"""
    
    storybook = db.query(SupabaseGeneratedStoryBook).filter(
        SupabaseGeneratedStoryBook.id == storybook_id
    ).first()
    
    if not storybook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"StoryBook ID {storybook_id} が見つかりません"
        )
    
    db.delete(storybook)
    db.commit()
    
    return {"message": "ストーリーブックが削除されました"}
