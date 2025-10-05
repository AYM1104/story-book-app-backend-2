from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from sqlalchemy.orm import Session
import os
from app.database.session import get_db
from app.schemas.images.image_generation import (
    StoryPlotImageToImageRequest,
    StoryPlotAllPagesImageToImageRequest,
    StoryPlotImageGenerationResponse,
    StoryPlotAllPagesGenerationResponse,
    StoryPlotImageInfo,
    ImageUploadResponse
)
from typing import List

router = APIRouter(prefix="/images/generation", tags=["image-generation"])

@router.post("/generate-storyplot-image-to-image", response_model=StoryPlotImageGenerationResponse)
async def generate_storyplot_image_to_image(
    request: StoryPlotImageToImageRequest,
    db: Session = Depends(get_db)
):
    """StoryPlot用Image-to-Image生成エンドポイント（メイン機能）"""
    try:
        # 遅延インポート
        from app.service.image_generator_service import image_generator_service
        
        # バリデーション
        if not (1 <= request.page_number <= 5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ページ番号は1-5の範囲で指定してください"
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
            prefix=request.prefix
        )
        
        return StoryPlotImageGenerationResponse(
            success=True,
            message=f"StoryPlot Image-to-Image生成が成功しました: {image_info['filename']}",
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
            detail=f"StoryPlot Image-to-Image生成に失敗しました: {str(e)}"
        )

@router.post("/generate-storyplot-all-pages-image-to-image", response_model=StoryPlotAllPagesGenerationResponse)
async def generate_storyplot_all_pages_image_to_image(
    request: StoryPlotAllPagesImageToImageRequest,
    db: Session = Depends(get_db)
):
    """StoryPlot全ページImage-to-Image生成エンドポイント"""
    try:
        # 遅延インポート
        from app.service.image_generator_service import image_generator_service
        
        if not (0.0 <= request.strength <= 1.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="強度は0.0-1.0の範囲で指定してください"
            )
        
        # 参考画像の自動解決
        image_path = request.reference_image_path
        if not image_path:
            # request.reference_image_path が未指定の場合、story_plot_id から解決
            from app.models.story.stroy_plot import StoryPlot
            from app.models.story.story_setting import StorySetting
            from app.models.images.images import UploadImages

            story_plot = db.query(StoryPlot).filter(StoryPlot.id == request.story_plot_id).first()
            if not story_plot:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"StoryPlot ID {request.story_plot_id} が見つかりません")

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
            story_plot_id=request.story_plot_id,
            reference_image_path=request.reference_image_path,
            strength=request.strength,
            prefix=request.prefix
        )
        
        return StoryPlotAllPagesGenerationResponse(
            success=True,
            message=f"StoryPlot ID {request.story_plot_id} の全ページImage-to-Image生成が完了しました",
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
            detail=f"StoryPlot全ページImage-to-Image生成に失敗しました: {str(e)}"
        )

@router.post("/upload-reference-image", response_model=ImageUploadResponse)
async def upload_reference_image(file: UploadFile = File(...)):
    """参考画像をアップロードするエンドポイント"""
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
            message=f"参考画像のアップロードが成功しました: {image_info['filename']}",
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
            detail=f"参考画像のアップロードに失敗しました: {str(e)}"
        )

@router.get("/uploaded-images", response_model=List[ImageUploadResponse])
async def get_uploaded_images():
    """アップロードされた画像のリストを取得するエンドポイント"""
    try:
        images_info = image_generator_service.get_uploaded_images_list()
        
        return [
            ImageUploadResponse(
                success=True,
                message="アップロード済み画像",
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
            detail=f"アップロード画像一覧の取得に失敗しました: {str(e)}"
        )
