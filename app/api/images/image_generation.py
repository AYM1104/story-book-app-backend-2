from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
import os
import threading
from typing import List, Optional

from app.database.supabase_session import get_supabase_db, get_supabase_db_sync
from app.service.image_generator_service import image_generator_service
from app.core.security.auth0_jwt import get_auth0_sub_from_token
from app.schemas.images.image_generation import (
    StoryPlotImageToImageRequest,
    StoryPlotAllPagesImageToImageRequest,
    StoryPlotImageGenerationResponse,
    StoryPlotAllPagesGenerationResponse,
    StoryPlotImageInfo,
    ImageUploadResponse,
    StorybookAllPagesImageToImageRequest,
    StorybookAllPagesGenerationResponse
)
from typing import List

router = APIRouter(prefix="/api/images/generation", tags=["image-generation"])

@router.post("/generate-storyplot-image-to-image", response_model=StoryPlotImageGenerationResponse)
async def generate_supabase_storyplot_image_to_image(
    request: StoryPlotImageToImageRequest,
    db: Session = Depends(get_supabase_db),
    user_id: str = Depends(get_auth0_sub_from_token)  # Auth0のsubクレーム
):
    """Supabase用のStoryPlot Image-to-Image生成エンドポイント（メイン機能）"""
    try:
        # story_plotを取得してページ数を確認
        from app.models.story.story_plot import StoryPlot
        
        story_plot = db.query(StoryPlot).filter(StoryPlot.id == request.story_plot_id).first()
        if not story_plot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"StoryPlot ID {request.story_plot_id} が見つかりません"
            )
        
        # 実際に存在するページ数を計算（最大10ページまで）
        def get_page_count(plot):
            for i in range(10, 0, -1):
                page_content = getattr(plot, f'page_{i}', None)
                if page_content and page_content.strip():
                    return i
            return 5  # デフォルトは5ページ
        
        max_pages = get_page_count(story_plot)
        
        # バリデーション（動的なページ数に対応）
        if not (1 <= request.page_number <= max_pages):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ページ番号は1-{max_pages}の範囲で指定してください"
            )
        
        if not (0.0 <= request.strength <= 1.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="強度は0.0-1.0の範囲で指定してください"
            )
        
        # 参考画像の存在確認（絶対パスと相対パスの両方に対応）
        image_path = request.reference_image_path
        if not os.path.isabs(image_path):
            # 相対パスの場合は、プロジェクトルートからの相対パスとして扱う
            image_path = os.path.join(os.getcwd(), image_path)
        
        if not os.path.exists(image_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"参考画像が見つかりません: {request.reference_image_path}"
            )
        
        # 絶対パスに変換
        request.reference_image_path = os.path.abspath(image_path)
        
        image_info = image_generator_service.generate_storyplot_image_to_image(
            db=db,
            story_plot_id=request.story_plot_id,
            page_number=request.page_number,
            reference_image_path=request.reference_image_path,
            strength=request.strength,
            prefix=request.prefix,
            user_id=user_id
        )
        
        return StoryPlotImageGenerationResponse(
            success=True,
            message=f"Supabase StoryPlot Image-to-Image生成が成功しました: {image_info['filename']}",
            image=StoryPlotImageInfo(**image_info)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase StoryPlot Image-to-Image生成に失敗しました: {str(e)}"
        )

@router.post("/generate-storyplot-all-pages-image-to-image", response_model=StoryPlotAllPagesGenerationResponse)
async def generate_supabase_storyplot_all_pages_image_to_image(
    request: StoryPlotAllPagesImageToImageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_supabase_db),
    user_id: str = Depends(get_auth0_sub_from_token)  # Auth0のsubクレーム
):
    """Supabase用のStoryPlot全ページImage-to-Image生成エンドポイント"""
    try:
        print(f"DEBUG: request.story_plot_id={request.story_plot_id}, request.storybook_id={request.storybook_id}")
        
        if not (0.0 <= request.strength <= 1.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="強度は0.0-1.0の範囲で指定してください"
            )
        
        # story_pagesのバリデーション（3, 5, 7, 10のいずれかのみ許可）
        if request.story_pages not in [3, 5, 7, 10]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"無効なページ数です。3, 5, 7, 10のいずれかを指定してください。指定値: {request.story_pages}"
            )
        
        # story_plot_idまたはstorybook_idのどちらか一方を指定する必要がある
        if not request.story_plot_id and not request.storybook_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="story_plot_idまたはstorybook_idのどちらか一方を指定してください"
            )
        
        if request.story_plot_id and request.storybook_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="story_plot_idとstorybook_idの両方を指定することはできません"
            )
        
        # story_plot_idを決定
        story_plot_id = request.story_plot_id
        print(f"DEBUG: Initial story_plot_id={story_plot_id}")
        if request.storybook_id:
            # storybook_idからstory_plot_idを取得
            from app.models.story.story_book import StoryBook
            
            storybook = db.query(StoryBook).filter(
                StoryBook.id == request.storybook_id
            ).first()
            
            if not storybook:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"StoryBook ID {request.storybook_id} が見つかりません"
                )
            
            story_plot_id = storybook.story_plot_id
            print(f"DEBUG: After storybook lookup, story_plot_id={story_plot_id}")
        
        # クレジットチェックはフロントエンド側でページ数選択時に実施されるため、
        # 画像生成APIではチェックしない（画像生成自体は追加コストがかからない）
        
        # 参考画像の自動解決
        image_path = request.reference_image_path
        if not image_path:
            # request.reference_image_path が未指定の場合、story_plot_id から解決
            from app.models.story.story_plot import StoryPlot
            from app.models.story.story_setting import StorySetting
            from app.features._01_image_upload.models.images import UploadImages

            story_plot = db.query(StoryPlot).filter(StoryPlot.id == story_plot_id).first()
            if not story_plot:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"StoryPlot ID {story_plot_id} が見つかりません")

            story_setting = db.query(StorySetting).filter(StorySetting.id == story_plot.story_setting_id).first()
            if not story_setting:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"StorySetting ID {story_plot.story_setting_id} が見つかりません")

            upload_image = story_setting.upload_image
            if not upload_image:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="参照画像（upload_image）が見つかりません")

            # GCSのpublic_urlを優先的に使用
            if upload_image.public_url:
                image_path = upload_image.public_url
            elif upload_image.file_path:
                image_path = upload_image.file_path
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="参照画像のパスが見つかりません")

        # GCSのURLかローカルパスかを判定
        if image_path.startswith("https://") or image_path.startswith("http://"):
            # GCSのURLの場合はそのまま使用
            request.reference_image_path = image_path
        else:
            # ローカルパスの場合のみ絶対パス・存在確認
            if not os.path.isabs(image_path):
                image_path = os.path.join(os.getcwd(), image_path)
            if not os.path.exists(image_path):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"参考画像が見つかりません: {image_path}")
            request.reference_image_path = os.path.abspath(image_path)

        # 先にステータスを「生成中」に更新（storybookが存在する場合）
        try:
            from app.models.story.story_book import StoryBook

            target_storybook = None
            if request.storybook_id:
                target_storybook = db.query(StoryBook).filter(StoryBook.id == request.storybook_id).first()
            if not target_storybook:
                target_storybook = db.query(StoryBook).filter(StoryBook.story_plot_id == story_plot_id).first()

            if target_storybook:
                target_storybook.image_generation_status = "generating"
                target_storybook.generation_progress = {
                    "current_page": 0,
                    "current_step": "prompt",
                    "completed_pages": 0,
                    "total_pages": 1 + min(request.story_pages or 0, 10)
                }
                db.commit()
        except Exception as status_init_error:
            print(f"⚠️ Failed to initialize generation status: {status_init_error}")

        # 重い生成処理はレスポンスとは切り離してバックグラウンドで実行
        request_payload = request.model_dump()
        background_tasks.add_task(
            _kickoff_storyplot_all_pages_generation,
            request_payload,
            user_id,
            story_plot_id,
            request.storybook_id
        )

        return StoryPlotAllPagesGenerationResponse(
            success=True,
            message=f"Supabase StoryPlot ID {story_plot_id} の全ページImage-to-Image生成を開始しました",
            images=[],
            total_generated=0
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase StoryPlot全ページImage-to-Image生成に失敗しました: {str(e)}"
        )


def _kickoff_storyplot_all_pages_generation(
    request_payload: dict,
    user_id: str,
    story_plot_id: int,
    storybook_id: Optional[int]
) -> None:
    """重い生成処理を別スレッドで実行し、レスポンスをブロックしない。"""
    thread = threading.Thread(
        target=_run_storyplot_all_pages_generation,
        args=(request_payload, user_id, story_plot_id, storybook_id),
        daemon=True
    )
    thread.start()


def _run_storyplot_all_pages_generation(
    request_payload: dict,
    user_id: str,
    story_plot_id: int,
    storybook_id: Optional[int]
) -> None:
    """実際の画像生成を実行し、失敗時はステータスをfailedに更新する。"""
    db = get_supabase_db_sync()
    try:
        request_obj = StoryPlotAllPagesImageToImageRequest(**request_payload)

        image_generator_service.generate_storyplot_all_pages_i2i(
            db=db,
            story_plot_id=story_plot_id,
            reference_image_path=request_obj.reference_image_path,
            strength=request_obj.strength,
            prefix=request_obj.prefix,
            user_id=user_id,
            story_pages=request_obj.story_pages
        )
    except Exception as e:
        print(f"❌ Background storyplot all pages generation failed: {e}")
        try:
            from app.models.story.story_book import StoryBook

            target_storybook = None
            if storybook_id:
                target_storybook = db.query(StoryBook).filter(StoryBook.id == storybook_id).first()
            if not target_storybook:
                target_storybook = db.query(StoryBook).filter(StoryBook.story_plot_id == story_plot_id).first()

            if target_storybook:
                target_storybook.image_generation_status = "failed"
                db.commit()
        except Exception as inner:
            print(f"⚠️ Failed to update storybook status after generation error: {inner}")
    finally:
        db.close()

@router.post("/upload-reference-image", response_model=ImageUploadResponse)
async def upload_supabase_reference_image(file: UploadFile = File(...)):
    """Supabase用の参考画像をアップロードするエンドポイント"""
    try:
        # ファイル形式のチェック
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="画像ファイルのみアップロード可能です"
            )
        
        # ファイルサイズのチェック（10MB制限）
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="ファイルサイズは10MB以下にしてください"
            )
        
        # ファイル内容を読み込み
        file_content = await file.read()
        
        # 画像をアップロード
        image_info = image_generator_service.upload_reference_image(
            file_content=file_content,
            filename=file.filename or "uploaded_image"
        )
        
        return ImageUploadResponse(
            success=True,
            message=f"Supabase参考画像のアップロードが成功しました: {image_info['filename']}",
            filename=image_info['filename'],
            filepath=image_info['filepath'],
            size_bytes=image_info['size_bytes'],
            image_size=image_info['image_size'],
            format=image_info['format'],
            timestamp=image_info['timestamp']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase参考画像のアップロードに失敗しました: {str(e)}"
        )

@router.get("/uploaded-images", response_model=List[ImageUploadResponse])
async def get_supabase_uploaded_images():
    """Supabase用のアップロードされた画像のリストを取得するエンドポイント"""
    try:
        images_info = image_generator_service.get_uploaded_images_list()
        
        return [
            ImageUploadResponse(
                success=True,
                message="Supabaseアップロード済み画像",
                filename=img['filename'],
                filepath=img['filepath'],
                size_bytes=img['size_bytes'],
                image_size=img['image_size'],
                format=img['format'],
                timestamp=img['timestamp']
            )
            for img in images_info
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabaseアップロード画像一覧の取得に失敗しました: {str(e)}"
        )

# 画像生成履歴取得エンドポイント（Supabase用）
@router.get("/generation-history/{story_plot_id}", response_model=List[dict])
async def get_supabase_generation_history(
    story_plot_id: int,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用の画像生成履歴を取得するエンドポイント"""
    try:
        # 生成された画像の履歴を取得（実装はサービス層で行う）
        history = image_generator_service.get_generation_history(story_plot_id)
        
        return history
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase画像生成履歴の取得に失敗しました: {str(e)}"
        )

# 画像生成状態確認エンドポイント（Supabase用）
@router.get("/generation-status/{story_plot_id}", response_model=dict)
async def get_supabase_generation_status(
    story_plot_id: int,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用の画像生成状態を確認するエンドポイント"""
    try:
        # 画像生成の状態を確認（データベースセッションを渡して動的にページ数を取得）
        status_info = image_generator_service.get_generation_status(story_plot_id, db=db)
        
        return status_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase画像生成状態の確認に失敗しました: {str(e)}"
        )
        
@router.post("/generate-storybook-all-pages-image-to-image", response_model=StorybookAllPagesGenerationResponse)
async def generate_storybook_all_pages_image_to_image(
    request: StorybookAllPagesImageToImageRequest,
    db: Session = Depends(get_supabase_db),
    user_id: str = Depends(get_auth0_sub_from_token)  # Auth0のsubクレーム
):
    """ストーリーブック全ページImage-to-Image生成エンドポイント"""
    try:
        if not (0.0 <= request.strength <= 1.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="強度は0.0-1.0の範囲で指定してください"
            )
        
        # ストーリーブックからstory_plot_idを取得
        from app.models.story.story_book import StoryBook
        
        storybook = db.query(StoryBook).filter(
            StoryBook.id == request.storybook_id
        ).first()
        
        if not storybook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"StoryBook ID {request.storybook_id} が見つかりません"
            )
        
        story_plot_id = storybook.story_plot_id
        
        # クレジットチェックはフロントエンド側でページ数選択時に実施されるため、
        # 画像生成APIではチェックしない（画像生成自体は追加コストがかからない）
        
        # 参考画像の自動解決
        image_path = request.reference_image_path
        if not image_path:
            # request.reference_image_path が未指定の場合、story_plot_id から解決
            from app.models.story.story_plot import StoryPlot
            from app.models.story.story_setting import StorySetting
            from app.features._01_image_upload.models.images import UploadImages

            story_plot = db.query(StoryPlot).filter(StoryPlot.id == story_plot_id).first()
            if not story_plot:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"StoryPlot ID {story_plot_id} が見つかりません")

            story_setting = db.query(StorySetting).filter(StorySetting.id == story_plot.story_setting_id).first()
            if not story_setting:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"StorySetting ID {story_plot.story_setting_id} が見つかりません")

            upload_image = story_setting.upload_image
            if not upload_image:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="参照画像（upload_image）が見つかりません")

            # GCSのpublic_urlを優先的に使用
            if upload_image.public_url:
                image_path = upload_image.public_url
            elif upload_image.file_path:
                image_path = upload_image.file_path
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="参照画像のパスが見つかりません")

        # GCSのURLかローカルパスかを判定
        if image_path.startswith("https://") or image_path.startswith("http://"):
            # GCSのURLの場合はそのまま使用
            request.reference_image_path = image_path
        else:
            # ローカルパスの場合のみ絶対パス・存在確認
            if not os.path.isabs(image_path):
                image_path = os.path.join(os.getcwd(), image_path)
            if not os.path.exists(image_path):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"参考画像が見つかりません: {image_path}")
            request.reference_image_path = os.path.abspath(image_path)
        
        images_info = image_generator_service.generate_storyplot_all_pages_i2i(
            db=db,
            story_plot_id=story_plot_id,
            reference_image_path=request.reference_image_path,
            strength=request.strength,
            prefix=request.prefix,
            user_id=user_id,
            story_pages=request.story_pages
        )
        
        return StorybookAllPagesGenerationResponse(
            success=True,
            message=f"StoryBook ID {request.storybook_id} の全ページImage-to-Image生成が完了しました",
            images=[StoryPlotImageInfo(**img) for img in images_info],
            total_generated=len(images_info)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ストーリーブック全ページImage-to-Image生成に失敗しました: {str(e)}"
        )
