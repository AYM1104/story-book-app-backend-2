from fastapi import APIRouter, Depends, HTTPException, status
import json
from sqlalchemy.orm import Session
from app.database.supabase_session import get_supabase_db
from app.models.story.story_plot import StoryPlot
from app.models.story.story_book import StoryBook
from app.models.child.child import Child
from app.schemas.story.story_book import (
    ThemeConfirmationRequest,
    ThemeConfirmationResponse,
    StoryBookCreate,
    StoryBookResponse,
    StorybookImageUrlUpdateRequest,
    StorybookImageUrlUpdateResponse,
    ImageGenerationStatus
)
from app.service.credits import PricingService, CreditsService
from app.models.credits.subscription import PlanType
from app.core.dependencies.plan_validator import validate_story_plan
from datetime import datetime, date, timedelta
from sqlalchemy import and_, func
from typing import Dict, List, Optional

router = APIRouter(prefix="/storybook", tags=["generated-storybook"])

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
        
        # 2. 物語本文が生成されているかチェック（page_1が空でないことを確認）
        if not story_plot.page_1 or story_plot.page_1.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="物語本文が生成されていません。先に /story/select_theme で物語を生成してください。"
            )
        
        # 3. 選択されたテーマのストーリー内容を取得
        # 新しい実装では generated_stories は空なので、ページ内容を結合してストーリー内容を作成
        selected_story_content_dict = {}
        if story_plot.generated_stories and request.selected_theme in story_plot.generated_stories:
            selected_story_content_dict = story_plot.generated_stories[request.selected_theme]
        else:
            # generated_storiesが空の場合は、ページ内容を結合してストーリー内容を作成（最大10ページまで）
            pages_content = []
            for i in range(1, 11):
                page_key = f"page_{i}"
                page_content = getattr(story_plot, page_key, None)
                if page_content and page_content.strip():
                    pages_content.append(f"{i}ページ目: {page_content}")
            
            selected_story_content_dict = {
                "title": story_plot.title or "無題のえほん",
                "content": "\n\n".join(pages_content),
                "selected_theme": request.selected_theme
            }
        
        # Textカラムに保存可能なようJSON文字列化
        selected_story_content = json.dumps(selected_story_content_dict, ensure_ascii=False)
        
        # 3.5. child_idの検証（child_idが指定されている場合のみ）
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
        
        # 3.6. story_pagesの検証とプランチェック
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
        
        # 4. StoryBookレコードを作成（最大10ページまで対応）
        storybook_data = {
            "story_plot_id": story_plot.id,
            "user_id": story_plot.user_id,
            "child_id": request.child_id,
            "title": story_plot.title or "無題のえほん",
            "description": story_plot.description,
            "keywords": story_plot.keywords,
            "content": selected_story_content_dict.get("content", ""),
            "story_content": selected_story_content,
            "image_generation_status": ImageGenerationStatus.PENDING,
            # 画像生成開始前に進捗取得APIが呼ばれても正しい値を返せるよう、total_pagesを初期設定
            "generation_progress": {
                "total_pages": 1 + request.story_pages  # 表紙 + リクエストページ数
            }
        }
        
        # ページ内容を動的に設定（最大10ページまで）
        for i in range(1, 11):
            page_key = f"page_{i}"
            page_content = getattr(story_plot, page_key, None)
            if page_content:
                storybook_data[page_key] = page_content
            elif i <= 5:  # page_1からpage_5は必須（nullable=False）
                storybook_data[page_key] = ""
        
        new_storybook = StoryBook(**storybook_data)
        
        db.add(new_storybook)
        db.flush()  # IDを取得するためにflush
        
        # 5. トランザクションをコミット
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
        # クレジット関連のValueError（残高不足など）
        db.rollback()
        # 既に402エラーとして処理済みの場合はそのままraise
        # その他のValueErrorの場合は500エラーとして処理
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
    
    storybook = db.query(StoryBook).filter(
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
    
    # GCSの画像URLをプロキシURLに変換（Cloud Run環境対応）
    from app.service.gcs_storage_service import gcs_storage_service
    gcs_service = gcs_storage_service  # グローバルインスタンスを使用
    
    # 表紙画像URLをプロキシURLに変換
    if storybook.cover_image_url:
        storybook.cover_image_url = gcs_service.get_proxy_url(storybook.cover_image_url)
    
    # ページ画像URLを動的に変換（最大10ページまで）
    for i in range(1, 11):
        page_image_url_attr = f"page_{i}_image_url"
        image_url = getattr(storybook, page_image_url_attr, None)
        if image_url:
            setattr(storybook, page_image_url_attr, gcs_service.get_proxy_url(image_url))

    
    # アップロード画像の情報をレスポンスに追加（最大10ページまで対応）
    response_data = {
        "id": storybook.id,
        "story_plot_id": storybook.story_plot_id,
        "user_id": storybook.user_id,
        "child_id": storybook.child_id,
        "title": storybook.title,
        "description": storybook.description,
        "keywords": storybook.keywords,
        "story_content": storybook.story_content,
        "cover_image_url": storybook.cover_image_url,
        "image_generation_status": storybook.image_generation_status,
        "created_at": storybook.created_at,
        "updated_at": storybook.updated_at
    }
    
    # ページ内容と画像URLを動的に追加（最大10ページまで）
    for i in range(1, 11):
        page_content_attr = f"page_{i}"
        page_image_url_attr = f"page_{i}_image_url"
        response_data[page_content_attr] = getattr(storybook, page_content_attr, "")
        response_data[page_image_url_attr] = getattr(storybook, page_image_url_attr, None)
    
    if uploaded_image_info:
        response_data['uploaded_image'] = uploaded_image_info
    
    return response_data

@router.get("/user/{user_id}")
async def get_supabase_user_storybooks(
    user_id: str,
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用のユーザーのストーリーブック一覧を取得するエンドポイント（月別・日別フィルタリング対応）
    
    レスポンス形式:
    - dayが指定されている場合: {"books": [...], "folder_count": int} (folder_countはDBから取得したカウント)
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
                # 特定の日をフィルタリング
                try:
                    target_date = datetime(year, month, day)
                    next_date = target_date + timedelta(days=1)
                    date_filtered_query = query.filter(
                        StoryBook.created_at >= target_date,
                        StoryBook.created_at < next_date
                    )
                    # DBからカウントを取得（GCSより高速）
                    folder_count = date_filtered_query.count()
                    # データ取得用のクエリも同じフィルタを適用
                    query = date_filtered_query
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"無効な日付です: {year}-{month}-{day}"
                    )
            else:
                # 特定の月をフィルタリング
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
            # 特定の年をフィルタリング
            start_date = datetime(year, 1, 1)
            end_date = datetime(year + 1, 1, 1)
            query = query.filter(
                StoryBook.created_at >= start_date,
                StoryBook.created_at < end_date
            )
    
    storybooks = query.order_by(StoryBook.created_at.desc()).all()
    
    # GCSの画像URLをプロキシURLに変換（Cloud Run環境対応）
    from app.service.gcs_storage_service import gcs_storage_service
    gcs_service = gcs_storage_service  # グローバルインスタンスを使用
    
    books = []
    for storybook in storybooks:
        # 表紙画像URLをプロキシURLに変換
        cover_url = storybook.cover_image_url
        if cover_url:
            cover_url = gcs_service.get_proxy_url(cover_url)
        
        # ページ画像URLもプロキシURLに変換
        page_image_urls = {}
        for i in range(1, 11):
            page_image_url = getattr(storybook, f"page_{i}_image_url", None)
            if page_image_url:
                page_image_urls[f"page_{i}_image_url"] = gcs_service.get_proxy_url(page_image_url)
            else:
                page_image_urls[f"page_{i}_image_url"] = None
        
        books.append({
            "id": storybook.id,
            "story_plot_id": storybook.story_plot_id,
            "user_id": storybook.user_id,
            "child_id": storybook.child_id,
            "title": storybook.title,
            "description": storybook.description,
            "keywords": storybook.keywords,
            "story_content": storybook.story_content,
            "cover_image_url": cover_url,
            "image_generation_status": storybook.image_generation_status,
            "is_favorite": storybook.is_favorite,
            "created_at": storybook.created_at,
            "updated_at": storybook.updated_at,
            **{f"page_{i}": getattr(storybook, f"page_{i}", "") for i in range(1, 11)},
            **page_image_urls
        })

    
    # 日別フィルタリングの場合はフォルダ数も返す
    if folder_count is not None:
        return {
            "books": books,
            "folder_count": folder_count
        }
    
    # それ以外の場合は従来通りリストを返す（後方互換性のため）
    return books

# ユーザーの特定年月に作成した日の一覧（Supabase用）
@router.get("/user/{user_id}/created-days")
async def get_supabase_user_created_days(
    user_id: str,
    year: int,
    month: int,
    db: Session = Depends(get_supabase_db)
):
    """指定ユーザーが指定の年月に作成したえほんの日付一覧を返す。
    返却形式: { "year": 2025, "month": 10, "days": [1,5,12] }
    """
    try:
        # 月初と翌月初を計算（created_atはSupabaseBaseで自動管理）
        start_dt = date(year, month, 1)
        if month == 12:
            end_dt = date(year + 1, 1, 1)
        else:
            end_dt = date(year, month + 1, 1)

        # 指定範囲のストーリーブック取得
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

        # 日付の重複を排除して昇順で返す
        days_set = set()
        for sb in storybooks:
            created = sb.created_at
            # created_at が datetime の想定。date へ丸める
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
        
        # 更新されたページを記録
        updated_pages = []
        page_image_url_map = {
            'cover': 'cover_image_url',
            'page_1': 'page_1_image_url',
            'page_2': 'page_2_image_url',
            'page_3': 'page_3_image_url',
            'page_4': 'page_4_image_url',
            'page_5': 'page_5_image_url',
            'page_6': 'page_6_image_url',
            'page_7': 'page_7_image_url',
            'page_8': 'page_8_image_url',
            'page_9': 'page_9_image_url',
            'page_10': 'page_10_image_url',
        }
        
        # 各ページの画像URLを更新（最大10ページまで対応）
        if request.cover_image_url:
            storybook.cover_image_url = request.cover_image_url
            updated_pages.append("cover")
        
        for i in range(1, 11):
            page_key = f"page_{i}"
            page_image_url_attr = f"page_{i}_image_url"
            image_url = getattr(request, page_image_url_attr, None)
            if image_url:
                setattr(storybook, page_image_url_attr, image_url)
                updated_pages.append(page_key)
        
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
    
    storybook = db.query(StoryBook).filter(
        StoryBook.id == storybook_id
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
@router.get("/", response_model=list[StoryBookResponse])
def get_supabase_storybooks(db: Session = Depends(get_supabase_db)):
    """Supabase用のストーリーブック一覧取得エンドポイント"""
    
    storybooks = db.query(StoryBook).order_by(
        StoryBook.created_at.desc()
    ).all()
    
    # GCSの画像URLを署名付きURLに変換
    from app.service.gcs_storage_service import gcs_storage_service
    gcs_service = gcs_storage_service  # グローバルインスタンスを使用
    
    books = []
    for storybook in storybooks:
        # 表紙画像URLをプロキシURLに変換
        cover_url = storybook.cover_image_url
        if cover_url:
            cover_url = gcs_service.get_proxy_url(cover_url)
        
        # ページ画像URLもプロキシURLに変換
        page_image_urls = {}
        for i in range(1, 11):
            page_image_url = getattr(storybook, f"page_{i}_image_url", None)
            if page_image_url:
                page_image_urls[f"page_{i}_image_url"] = gcs_service.get_proxy_url(page_image_url)
            else:
                page_image_urls[f"page_{i}_image_url"] = None
        
        books.append({
            "id": storybook.id,
            "story_plot_id": storybook.story_plot_id,
            "user_id": storybook.user_id,
            "child_id": storybook.child_id,
            "title": storybook.title,
            "description": storybook.description,
            "keywords": storybook.keywords,
            "story_content": storybook.story_content,
            "cover_image_url": cover_url,
            "image_generation_status": storybook.image_generation_status,
            "created_at": storybook.created_at,
            "updated_at": storybook.updated_at,
            **{f"page_{i}": getattr(storybook, f"page_{i}", "") for i in range(1, 11)},
            **page_image_urls
        })
    
    return books

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
        
        # 生成済みページ数をカウント（表紙 + 最大10ページまで）
        generated_pages = sum([
            1 if storybook.cover_image_url else 0,
            *[1 if getattr(storybook, f"page_{i}_image_url", None) else 0 for i in range(1, 11)]
        ])
        
        # 実際のページ数を動的に計算（内容があるページをカウント、空文字列は除外）
        actual_pages = sum([
            1 if getattr(storybook, f"page_{i}", None) and getattr(storybook, f"page_{i}", "").strip() else 0 for i in range(1, 11)
        ])
        total_pages = 1 + actual_pages  # 表紙 + 実際のページ数（最大11ページ: 表紙+10ページ）
        
        # 詳細進捗情報を取得
        generation_progress = storybook.generation_progress or {}
        current_page = generation_progress.get("current_page", 0)
        current_step = generation_progress.get("current_step", "")
        completed_pages = generation_progress.get("completed_pages", generated_pages)
        # generation_progressが total_pages を持っていればそちらを優先（表紙 + リクエストページ数）
        progress_total_pages = generation_progress.get("total_pages")
        calc_total_pages = progress_total_pages or total_pages
        
        # 各ステップの進捗率（1ページあたり）
        step_progress_map = {
            "prompt": 10,      # 0-20%の中間
            "api_call": 40,    # 20-60%の中間
            "saving": 75,      # 60-90%の中間
            "completed": 95    # 90-100%の中間
        }
        
        # 進捗計算用にステータスを解釈（pendingでも生成途中の値があれば計算する）
        status_for_calc = str(storybook.image_generation_status)

        # 画像生成が開始されていない場合
        if status_for_calc == "pending" and not generation_progress and generated_pages == 0:
            progress_percent = 0
            current_page = 0
        elif storybook.image_generation_status == "completed":
            progress_percent = 100
            current_page = calc_total_pages
        elif current_step and current_page > 0:
            # 詳細進捗情報がある場合、各ステップの進捗を考慮
            current_step_progress = step_progress_map.get(current_step, 0)
            # 完了ページの進捗 + 現在ページのステップ進捗
            progress_percent = int((completed_pages / calc_total_pages) * 100 + (current_step_progress / calc_total_pages)) if calc_total_pages > 0 else 0
            progress_percent = min(100, max(0, progress_percent))  # 0-100%の範囲に制限
        elif generated_pages == 0:
            progress_percent = 0
            current_page = 0
        else:
            # 詳細進捗情報がない場合は従来の計算方法
            progress_percent = int((generated_pages / calc_total_pages) * 100) if calc_total_pages > 0 else 0
            current_page = generated_pages
        
        # 完了ステータスでは必ず100%に揃える（API値が95%程度で止まることを防ぐ）
        if str(storybook.image_generation_status) == "completed":
            progress_percent = 100
            current_page = calc_total_pages

        return {
            "storybook_id": storybook_id,
            "current_page": current_page,
            "total_pages": calc_total_pages,
            "progress_percent": progress_percent,
            "status": str(storybook.image_generation_status),
            "current_step": current_step  # 現在のステップを追加
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"進捗情報の取得に失敗しました: {str(e)}"
        )
