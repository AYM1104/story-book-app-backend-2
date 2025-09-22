from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from sqlalchemy.orm import Session
import os
from app.database.session import get_db
from app.service.image_generator_service import image_generator_service
from app.schemas.images.image_generation import (
    ImageGenerationRequest,
    MultipleImageGenerationRequest,
    StorybookImageGenerationRequest,
    ImageGenerationResponse,
    SingleImageGenerationResponse,
    ImageInfo,
    StoryPlotImageGenerationRequest,
    StoryPlotAllPagesGenerationRequest,
    StoryPlotImageGenerationResponse,
    StoryPlotAllPagesGenerationResponse,
    StoryPlotImageInfo,
    ImageToImageRequest,
    ImageToImageResponse,
    StoryPlotImageToImageRequest,
    StoryPlotAllPagesImageToImageRequest,
    ImageUploadResponse
)
from typing import List

router = APIRouter(prefix="/images/generation", tags=["image-generation"])

@router.post("/generate", response_model=SingleImageGenerationResponse)
async def generate_single_image(request: ImageGenerationRequest):
    """単一の画像を生成するエンドポイント"""
    try:
        image_info = image_generator_service.generate_single_image(
            prompt=request.prompt,
            prefix=request.prefix
        )
        
        return SingleImageGenerationResponse(
            success=True,
            message=f"画像生成が成功しました: {image_info['filename']}",
            image=ImageInfo(**image_info)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"画像生成に失敗しました: {str(e)}"
        )

@router.post("/generate-multiple", response_model=ImageGenerationResponse)
async def generate_multiple_images(request: MultipleImageGenerationRequest):
    """複数の画像を一括生成するエンドポイント"""
    try:
        if len(request.prompts) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="一度に生成できる画像は最大10枚までです"
            )
        
        images_info = image_generator_service.generate_multiple_images(
            prompts=request.prompts,
            prefix=request.prefix
        )
        
        return ImageGenerationResponse(
            success=True,
            message=f"{len(images_info)}枚の画像生成が完了しました",
            images=[ImageInfo(**img) for img in images_info],
            total_generated=len(images_info)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"複数画像生成に失敗しました: {str(e)}"
        )

@router.post("/generate-storybook", response_model=ImageGenerationResponse)
async def generate_storybook_images(request: StorybookImageGenerationRequest):
    """絵本用の画像を生成するエンドポイント"""
    try:
        if len(request.story_pages) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="一度に生成できる絵本ページは最大10ページまでです"
            )
        
        images_info = image_generator_service.generate_storybook_images(
            story_pages=request.story_pages,
            storybook_id=request.storybook_id
        )
        
        return ImageGenerationResponse(
            success=True,
            message=f"絵本 '{request.storybook_id}' の{len(images_info)}ページの画像生成が完了しました",
            images=[ImageInfo(**img) for img in images_info],
            total_generated=len(images_info)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"絵本画像生成に失敗しました: {str(e)}"
        )

@router.get("/test", response_model=dict)
async def test_image_generation():
    """画像生成機能のテストエンドポイント"""
    try:
        test_prompt = (
            "A cute cat playing with a ball, children's book illustration style, "
            "warm and friendly, bright colors. "
            "IMPORTANT: No text, no letters, no words, no writing, no captions, no speech bubbles, "
            "no signs, no labels - pure illustration only"
        )
        image_info = image_generator_service.generate_single_image(
            prompt=test_prompt,
            prefix="test_image"
        )
        
        return {
            "success": True,
            "message": "画像生成テストが成功しました",
            "test_image": image_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"画像生成テストに失敗しました: {str(e)}"
        )

@router.post("/generate-storyplot-page", response_model=StoryPlotImageGenerationResponse)
async def generate_storyplot_page_image(
    request: StoryPlotImageGenerationRequest,
    db: Session = Depends(get_db)
):
    """StoryPlotの指定ページの画像を生成するエンドポイント"""
    try:
        if not (1 <= request.page_number <= 5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ページ番号は1-5の範囲で指定してください"
            )
        
        image_info = image_generator_service.generate_image_for_story_plot_page(
            db=db,
            story_plot_id=request.story_plot_id,
            page_number=request.page_number
        )
        
        return StoryPlotImageGenerationResponse(
            success=True,
            message=f"StoryPlot ID {request.story_plot_id} のページ {request.page_number} の画像生成が成功しました",
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
            detail=f"StoryPlot画像生成に失敗しました: {str(e)}"
        )

@router.post("/generate-storyplot-all-pages", response_model=StoryPlotAllPagesGenerationResponse)
async def generate_storyplot_all_pages_images(
    request: StoryPlotAllPagesGenerationRequest,
    db: Session = Depends(get_db)
):
    """StoryPlotの全ページの画像を一括生成するエンドポイント"""
    try:
        images_info = image_generator_service.generate_all_pages_for_story_plot(
            db=db,
            story_plot_id=request.story_plot_id
        )
        
        return StoryPlotAllPagesGenerationResponse(
            success=True,
            message=f"StoryPlot ID {request.story_plot_id} の全ページ画像生成が完了しました",
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
            detail=f"StoryPlot全ページ画像生成に失敗しました: {str(e)}"
        )

@router.post("/generate-image-to-image", response_model=ImageToImageResponse)
async def generate_image_to_image(request: ImageToImageRequest):
    """Image-to-Image生成エンドポイント"""
    try:
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
        
        image_info = image_generator_service.generate_image_to_image(
            prompt=request.prompt,
            reference_image_path=request.reference_image_path,
            strength=request.strength,
            prefix=request.prefix
        )
        
        return ImageToImageResponse(
            success=True,
            message=f"Image-to-Image生成が成功しました: {image_info['filename']}",
            image=ImageInfo(**image_info),
            reference_image_path=request.reference_image_path,
            strength=request.strength
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image-to-Image生成に失敗しました: {str(e)}"
        )

@router.post("/generate-storyplot-image-to-image", response_model=StoryPlotImageGenerationResponse)
async def generate_storyplot_image_to_image(
    request: StoryPlotImageToImageRequest,
    db: Session = Depends(get_db)
):
    """StoryPlot用Image-to-Image生成エンドポイント"""
    try:
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
