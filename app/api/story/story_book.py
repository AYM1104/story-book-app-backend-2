from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import Response
import json
from sqlalchemy.orm import Session, joinedload
from app.database.supabase_session import get_supabase_db
from app.models.story.story_plot import StoryPlot
from app.models.story.story_setting import StorySetting
from app.models.story.story_book import StoryBook
from app.models.story.story_page import StoryPage
from app.models.child.child import Child
from app.schemas.story.story_book import (
    ThemeConfirmationRequest,
    ThemeConfirmationResponse,
    StoryBookCreate,
    StoryBookResponse,
    StorybookImageUrlUpdateRequest,
    StorybookImageUrlUpdateResponse,
    ImageGenerationStatus,
    PageResponse
)
from app.service.credits import PricingService, CreditsService
from app.models.credits.subscription import PlanType
from app.core.dependencies.plan_validator import validate_story_plan
from datetime import datetime, date, timedelta
from sqlalchemy import and_, func
from typing import Dict, List, Optional

router = APIRouter(prefix="/storybook", tags=["generated-storybook"])


def _build_pages_response(storybook: StoryBook, gcs_service=None, base_url: str = None) -> List[dict]:
    """StoryBook の pages リレーションからページレスポンスを構築するヘルパー"""
    pages = []
    for page in storybook.pages:
        image_url = page.image_url
        if image_url and gcs_service and base_url:
            image_url = gcs_service.get_proxy_url(image_url, base_url=base_url)
        pages.append({
            "page_number": page.page_number,
            "content": page.content or "",
            "image_url": image_url
        })
    return pages


def _build_storybook_dict(storybook: StoryBook, gcs_service=None, base_url: str = None) -> dict:
    """StoryBook をレスポンス用辞書に変換するヘルパー"""
    cover_url = storybook.cover_image_url
    if cover_url and gcs_service and base_url:
        cover_url = gcs_service.get_proxy_url(cover_url, base_url=base_url)
    
    return {
        "id": storybook.id,
        "story_plot_id": storybook.story_plot_id,
        "user_id": storybook.user_id,
        "child_id": storybook.child_id,
        "title": storybook.title,
        "description": storybook.description,
        "keywords": storybook.keywords,
        "cover_image_url": cover_url,
        "pages": _build_pages_response(storybook, gcs_service, base_url),
        "image_generation_status": storybook.image_generation_status,
        "is_favorite": storybook.is_favorite,
        "created_at": storybook.created_at,
        "updated_at": storybook.updated_at,
    }


@router.post("/confirm-theme-and-create", response_model=ThemeConfirmationResponse)
async def supabase_confirm_theme_and_create_storybook(
    request: ThemeConfirmationRequest,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用のテーマ選択後にストーリーブックを作成するエンドポイント"""
    
    try:
        # 1. StoryPlotから選択されたテーマの情報を取得
        story_plot = db.query(StoryPlot).filter(StoryPlot.id == request.story_plot_id).first()
        if not story_plot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"StoryPlot ID {request.story_plot_id} が見つかりません"
            )
        
        # 2. 物語本文が生成されているかチェック（pagesリレーションにデータがあること）
        if not story_plot.pages or len(story_plot.pages) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="物語本文が生成されていません。先に /story/select_theme で物語を生成してください。"
            )
        
        # 3. child_idの検証（child_idが指定されている場合のみ）
        if request.child_id is not None:
            child = db.query(Child).filter(
                Child.id == request.child_id,
                Child.user_id == story_plot.user_id
            ).first()
            if not child:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Child ID {request.child_id} が見つかりません、またはこのユーザーに属していません"
                )
        
        # 3.5. story_pagesの検証とプランチェック
        if request.story_pages not in [3, 5, 7, 10]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"無効なページ数です。3, 5, 7, 10のいずれかを指定してください。指定値: {request.story_pages}"
            )
        
        # プランで許可されているページ数か確認
        plan = CreditsService.get_plan(db, story_plot.user_id)
        if not PricingService.is_allowed_for_plan(request.story_pages, plan):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PLAN_LIMIT",
                    "message": "現在のプランでは選択されたページ数の絵本を作成できません",
                    "plan": plan.value,
                    "requested_pages": request.story_pages,
                    "allowed_pages": PricingService.ALLOWED_PAGES.get(plan, [])
                }
            )
        
        # 4. StoryBookレコードを作成
        new_storybook = StoryBook(
            story_plot_id=story_plot.id,
            user_id=story_plot.user_id,
            child_id=request.child_id,
            title=story_plot.title or "無題のえほん",
            description=story_plot.description,
            keywords=story_plot.keywords,
            image_generation_status=ImageGenerationStatus.PENDING,
            generation_progress={
                "total_pages": 1 + request.story_pages  # 表紙 + リクエストページ数
            }
        )
        
        db.add(new_storybook)
        db.flush()  # IDを取得するためにflush
        
        # 5. PlotPage → StoryPage へのページデータコピー
        for plot_page in story_plot.pages:
            if plot_page.page_number <= request.story_pages:
                story_page = StoryPage(
                    story_book_id=new_storybook.id,
                    page_number=plot_page.page_number,
                    content=plot_page.content or ""
                )
                db.add(story_page)
        
        # 6. トランザクションをコミット
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
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ストーリーブック作成に失敗しました: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ストーリーブック作成に失敗しました: {str(e)}"
        )


@router.get("/{storybook_id}", response_model=StoryBookResponse)
async def get_supabase_storybook(
    storybook_id: int,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用のストーリーブック詳細を取得するエンドポイント"""
    
    try:
        storybook = db.query(StoryBook).options(
            joinedload(StoryBook.pages),
            joinedload(StoryBook.story_plot).joinedload(StoryPlot.story_setting).joinedload(StorySetting.upload_image)
        ).filter(
            StoryBook.id == storybook_id
        ).first()
        
        if not storybook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"StoryBook ID {storybook_id} が見つかりません"
            )
        
        # アップロード画像の情報を取得
        uploaded_image_info = None
        if storybook.story_plot and storybook.story_plot.story_setting:
            story_setting = storybook.story_plot.story_setting
            if story_setting.upload_image:
                uploaded_image = story_setting.upload_image
                uploaded_image_info = {
                    "id": uploaded_image.id,
                    "filename": uploaded_image.file_name,
                    "file_path": uploaded_image.file_path,
                    "public_url": uploaded_image.public_url,
                    "uploaded_at": uploaded_image.created_at
                }
        
        # ページ情報を正規化形式で構築
        pages = _build_pages_response(storybook)
        
        response_data = {
            "id": storybook.id,
            "story_plot_id": storybook.story_plot_id,
            "user_id": storybook.user_id,
            "child_id": storybook.child_id,
            "title": storybook.title,
            "description": storybook.description,
            "keywords": storybook.keywords,
            "cover_image_url": storybook.cover_image_url,
            "pages": pages,
            "image_generation_status": storybook.image_generation_status,
            "created_at": storybook.created_at,
            "updated_at": storybook.updated_at
        }
        
        if uploaded_image_info:
            response_data['uploaded_image'] = uploaded_image_info
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ストーリーブック取得エラー (ID: {storybook_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ストーリーブックの取得に失敗しました: {str(e)}"
        )



@router.get("/user/{user_id}")
async def get_supabase_user_storybooks(
    request: Request,
    response: Response,
    user_id: str,
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用のユーザーのストーリーブック一覧を取得するエンドポイント（月別・日別フィルタリング対応）
    
    レスポンス形式:
    - dayが指定されている場合: {"books": [...], "folder_count": int}
    - それ以外: [...]
    """
    
    query = db.query(StoryBook).filter(
        StoryBook.user_id == user_id
    )
    
    # 日付フィルタリング
    folder_count = None
    if year is not None:
        if month is not None:
            if day is not None:
                try:
                    target_date = datetime(year, month, day)
                    next_date = target_date + timedelta(days=1)
                    date_filtered_query = query.filter(
                        StoryBook.created_at >= target_date,
                        StoryBook.created_at < next_date
                    )
                    folder_count = date_filtered_query.count()
                    query = date_filtered_query
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"無効な日付です: {year}-{month}-{day}"
                    )
            else:
                try:
                    start_date = datetime(year, month, 1)
                    if month == 12:
                        end_date = datetime(year + 1, 1, 1)
                    else:
                        end_date = datetime(year, month + 1, 1)
                    query = query.filter(
                        StoryBook.created_at >= start_date,
                        StoryBook.created_at < end_date
                    )
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"無効な月です: {year}-{month}"
                    )
        else:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year + 1, 1, 1)
            query = query.filter(
                StoryBook.created_at >= start_date,
                StoryBook.created_at < end_date
            )
    
    storybooks = query.order_by(StoryBook.created_at.desc()).all()
    
    # HTTPキャッシュヘッダーを設定（60秒キャッシュ）
    response.headers["Cache-Control"] = "private, max-age=60"
    
    # GCSの画像URLをプロキシURLに変換
    from app.service.gcs_storage_service import gcs_storage_service
    gcs_service = gcs_storage_service
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    books = [_build_storybook_dict(sb, gcs_service, base_url) for sb in storybooks]
    
    if folder_count is not None:
        return {
            "books": books,
            "folder_count": folder_count
        }
    
    return books


# ユーザーの特定年月に作成した日の一覧（Supabase用）
@router.get("/user/{user_id}/created-days")
async def get_supabase_user_created_days(
    response: Response,
    user_id: str,
    year: int,
    month: int,
    db: Session = Depends(get_supabase_db)
):
    """指定ユーザーが指定の年月に作成したえほんの日付一覧を返す。
    返却形式: { "year": 2025, "month": 10, "days": [1,5,12] }
    """
    response.headers["Cache-Control"] = "private, max-age=300"
    
    try:
        start_dt = date(year, month, 1)
        if month == 12:
            end_dt = date(year + 1, 1, 1)
        else:
            end_dt = date(year, month + 1, 1)

        storybooks = (
            db.query(StoryBook)
            .filter(
                and_(
                    StoryBook.user_id == user_id,
                    StoryBook.created_at >= start_dt,
                    StoryBook.created_at < end_dt,
                )
            )
            .all()
        )

        days_set = set()
        for sb in storybooks:
            created = sb.created_at
            d = created.date() if hasattr(created, "date") else created
            if d is not None and d.month == month and d.year == year:
                days_set.add(d.day)

        return {
            "year": year,
            "month": month,
            "days": sorted(list(days_set))
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"作成日一覧の取得に失敗しました: {str(e)}"
        )


@router.post("/update-image-urls", response_model=StorybookImageUrlUpdateResponse)
async def update_supabase_storybook_image_urls(
    request: StorybookImageUrlUpdateRequest,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用の生成された画像のURLをストーリーブックに紐づけるエンドポイント"""
    
    try:
        storybook = db.query(StoryBook).filter(
            StoryBook.id == request.storybook_id
        ).first()
        
        if not storybook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"StoryBook ID {request.storybook_id} が見つかりません"
            )
        
        updated_pages = []
        
        # 表紙画像URLを更新
        if request.cover_image_url:
            storybook.cover_image_url = request.cover_image_url
            updated_pages.append("cover")
        
        # 各ページの画像URLを更新（正規化形式）
        for page_update in request.page_images:
            story_page = db.query(StoryPage).filter(
                StoryPage.story_book_id == storybook.id,
                StoryPage.page_number == page_update.page_number
            ).first()
            
            if story_page:
                story_page.image_url = page_update.image_url
                updated_pages.append(f"page_{page_update.page_number}")
        
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
    new_status: ImageGenerationStatus,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用の画像生成状態を更新するエンドポイント"""
    
    storybook = db.query(StoryBook).filter(
        StoryBook.id == storybook_id
    ).first()
    
    if not storybook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"StoryBook ID {storybook_id} が見つかりません"
        )
    
    storybook.image_generation_status = new_status
    db.commit()
    return {"message": "画像生成状態が更新されました"}


# ストーリーブック一覧取得エンドポイント（Supabase用）
@router.get("/", response_model=list[StoryBookResponse])
def get_supabase_storybooks(request: Request, db: Session = Depends(get_supabase_db)):
    """Supabase用のストーリーブック一覧取得エンドポイント"""
    
    storybooks = db.query(StoryBook).order_by(
        StoryBook.created_at.desc()
    ).all()
    
    from app.service.gcs_storage_service import gcs_storage_service
    gcs_service = gcs_storage_service
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    return [_build_storybook_dict(sb, gcs_service, base_url) for sb in storybooks]


# ストーリーブック削除エンドポイント（Supabase用）
@router.delete("/{storybook_id}")
def delete_supabase_storybook(storybook_id: int, db: Session = Depends(get_supabase_db)):
    """Supabase用のストーリーブック削除エンドポイント"""
    
    storybook = db.query(StoryBook).filter(
        StoryBook.id == storybook_id
    ).first()
    
    if not storybook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"StoryBook ID {storybook_id} が見つかりません"
        )
    
    db.delete(storybook)
    db.commit()
    
    return {"message": "ストーリーブックが削除されました"}

# お気に入り状態更新エンドポイント（Supabase用）
@router.patch("/{storybook_id}/favorite")
async def update_favorite_status(
    storybook_id: int,
    is_favorite: bool,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用のお気に入り状態更新エンドポイント"""
    try:
        storybook = db.query(StoryBook).filter(
            StoryBook.id == storybook_id
        ).first()
        
        if not storybook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"StoryBook ID {storybook_id} が見つかりません"
            )
        
        storybook.is_favorite = is_favorite
        db.commit()
        
        return {
            "success": True,
            "storybook_id": storybook_id,
            "is_favorite": is_favorite
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"お気に入り状態の更新に失敗しました: {str(e)}"
        )


@router.get("/{storybook_id}/generation-progress")
async def get_generation_progress(
    storybook_id: int,
    db: Session = Depends(get_supabase_db)
):
    """画像生成の進捗情報を取得"""
    try:
        storybook = db.query(StoryBook).filter(
            StoryBook.id == storybook_id
        ).first()
        
        if not storybook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"StoryBook ID {storybook_id} が見つかりません"
            )
        
        # 生成済みページ数をカウント（表紙 + StoryPage の image_url が設定済みのもの）
        generated_pages = (1 if storybook.cover_image_url else 0) + sum(
            1 for page in storybook.pages if page.image_url
        )
        
        # 実際のページ数（StoryPage のうちcontentが空でないもの）
        actual_pages = sum(
            1 for page in storybook.pages if page.content and page.content.strip()
        )
        total_pages = 1 + actual_pages  # 表紙 + 実際のページ数
        
        # 詳細進捗情報を取得
        generation_progress = storybook.generation_progress or {}
        current_page = generation_progress.get("current_page", 0)
        current_step = generation_progress.get("current_step", "")
        completed_pages = generation_progress.get("completed_pages", generated_pages)
        progress_total_pages = generation_progress.get("total_pages")
        calc_total_pages = progress_total_pages or total_pages
        
        # 各ステップの進捗率
        step_progress_map = {
            "prompt": 10,
            "api_call": 40,
            "saving": 75,
            "completed": 95
        }
        
        status_for_calc = str(storybook.image_generation_status)

        if status_for_calc == "pending" and not generation_progress and generated_pages == 0:
            progress_percent = 0
            current_page = 0
        elif storybook.image_generation_status == "completed":
            progress_percent = 100
            current_page = calc_total_pages
        elif current_step and current_page > 0:
            current_step_progress = step_progress_map.get(current_step, 0)
            progress_percent = int((completed_pages / calc_total_pages) * 100 + (current_step_progress / calc_total_pages)) if calc_total_pages > 0 else 0
            progress_percent = min(100, max(0, progress_percent))
        elif generated_pages == 0:
            progress_percent = 0
            current_page = 0
        else:
            progress_percent = int((generated_pages / calc_total_pages) * 100) if calc_total_pages > 0 else 0
            current_page = generated_pages
        
        if str(storybook.image_generation_status) == "completed":
            progress_percent = 100
            current_page = calc_total_pages

        return {
            "storybook_id": storybook_id,
            "current_page": current_page,
            "total_pages": calc_total_pages,
            "progress_percent": progress_percent,
            "status": str(storybook.image_generation_status),
            "current_step": current_step
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"進捗情報の取得に失敗しました: {str(e)}"
        )
