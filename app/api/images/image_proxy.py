from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import Response
from app.service.gcs_storage_service import gcs_storage_service
from typing import Optional

router = APIRouter(prefix="/api/images", tags=["images"])


@router.get("/signed-url")
async def get_signed_url(
    url: str = Query(..., description="GCS画像URL（storage.googleapis.com形式）"),
    expiration_hours: int = Query(1, description="URLの有効期限（時間単位）")
):
    """GCS画像の署名付きURLを生成するエンドポイント
    
    Args:
        url: GCS画像URL（例: https://storage.googleapis.com/bucket-name/path/to/image.png）
        expiration_hours: URLの有効期限（デフォルト1時間）
        
    Returns:
        JSON: 署名付きURLを含むレスポンス
    """
    try:
        signed_url = gcs_storage_service.generate_signed_url(
            file_path_or_url=url,
            expiration_hours=expiration_hours
        )
        
        return {
            "success": True,
            "signed_url": signed_url,
            "original_url": url,
            "expiration_hours": expiration_hours
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"署名付きURLの生成に失敗しました: {str(e)}"
        )


@router.get("/proxy")
async def proxy_image(
    url: str = Query(..., description="GCS画像URL（storage.googleapis.com形式）")
):
    """GCS画像をプロキシするエンドポイント（認証不要で画像を取得）
    
    Args:
        url: GCS画像URL（例: https://storage.googleapis.com/bucket-name/path/to/image.png）
        
    Returns:
        Response: 画像データ
    """
    try:
        # GCSから画像をダウンロード
        image_data = gcs_storage_service.download_file(url)
        
        # Content-Typeを推測（URLの拡張子から）
        content_type = "image/png"  # デフォルト
        if url.lower().endswith('.jpg') or url.lower().endswith('.jpeg'):
            content_type = "image/jpeg"
        elif url.lower().endswith('.png'):
            content_type = "image/png"
        elif url.lower().endswith('.webp'):
            content_type = "image/webp"
        elif url.lower().endswith('.gif'):
            content_type = "image/gif"
        
        return Response(
            content=image_data,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600"  # 1時間キャッシュ
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"画像の取得に失敗しました: {str(e)}"
        )

