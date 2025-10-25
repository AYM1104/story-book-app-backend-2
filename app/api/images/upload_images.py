import time
import traceback
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.images.images import UploadImageResponse
from app.service.upload_image.file_processing_service import file_processing_service
from app.service.upload_image.image_analysis_service import image_analysis_service
from app.service.upload_image.image_database_service import image_database_service
from app.service.upload_image.image_upload_gcs_service import image_upload_gcs_service

router = APIRouter(prefix="/api/images", tags=["images"])


# 画像アップロードをするエンドポイント
@router.post("/upload", response_model=UploadImageResponse)
async def upload_gcs_image(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    db: Session = Depends(get_db),
):
    """GCSへ画像をアップロードするエンドポイント"""

    try:
        total_start_time = time.time()
        print("=== GCSアップロード処理開始 ===")

        # 1. アップロードされたファイルを検証
        file_validation_start_time = time.time()
        print("=== ファイル検証開始 ===")
        file_result = await file_processing_service.validate_and_read_file(file)    # file_processing_service.pyを呼び出す
        content = file_result["content"]
        content_type = file_result["content_type"]
        filename = file_result["filename"]
        print(f"=== ファイル検証完了: {time.time() - file_validation_start_time:.3f}秒 ===")

        # 2. GCSへアップロード
        upload_start_time = time.time()
        print("=== 画像をGCSにアップロード開始 ===")
        try:
            upload_result = await image_upload_gcs_service.upload_image(    # image_upload_gcs_service.pyを呼び出す
                file_content=content,
                filename=filename or "uploaded_image",
                user_id=user_id,
                content_type=content_type,
            )

            # アップロードに失敗した場合はエラーを返す
            if not upload_result.get("success"):
                print(f"GCSアップロード失敗: {upload_result.get('error')}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="画像のアップロードに失敗しました",
                )

            # アップロードに成功した場合はファイルパスと公開URLを取得
            file_path = upload_result["gcs_path"]
            public_url = upload_result["public_url"]
            print(f"=== 画像をGCSにアップロード完了: {time.time() - upload_start_time:.3f}秒 ===")
        
        # エラーが発生した場合はエラーを返す
        except HTTPException:
            raise

        # エラーが発生した場合はエラーを返す
        except Exception as gcs_error:
            upload_time = time.time() - upload_start_time
            print(f"⏱️ GCSアップロード時間（エラー）: {upload_time:.3f}秒")
            print(f"GCSエラー: {gcs_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"画像のアップロードに失敗しました: {gcs_error}",
            )

        print(f"ファイルパス: {file_path}")
        print(f"GCS public_url: {public_url}")

        # 3. Vision API 解析
        analysis_start_time = time.time()
        print("=== Vision API解析開始 ===")
        analysis_result = await image_analysis_service.analyze_image(content, filename)
        meta_data_json = analysis_result["meta_data_json"]
        print(f"=== Vision API解析完了: {time.time() - analysis_start_time:.3f}秒 ===")

        # 4. データベースへ保存
        db_result = await image_database_service.save_image_to_database(
            db=db,
            file_name=filename,
            file_path=file_path,
            content_type=content_type,
            size_bytes=len(content),
            user_id=user_id,
            meta_data_json=meta_data_json,
            public_url=public_url
        )

        if not db_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"画像情報の保存に失敗しました: {db_result['error']}",
            )

        response_data = db_result["response_data"]

        total_time = time.time() - total_start_time
        print(f"=== GCSアップロード処理完了: {total_time:.3f}秒 ===")
        print(f"Response public_url: {response_data['public_url']}")
        print(f"Response file_path: {response_data['file_path']}")

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"アップロード処理中にエラーが発生しました: {e}")
        print(f"エラーの詳細: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"画像のアップロードに失敗しました: {e}",
        )

