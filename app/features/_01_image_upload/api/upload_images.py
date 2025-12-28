import os
import time
import traceback
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.features._01_image_upload.schemas.images import UploadImageResponse
from app.features._01_image_upload.services._00_file_processing_service import file_processing_service
from app.service.gcs_storage_service import gcs_storage_service
from app.features._01_image_upload.services._02_image_analysis_service import image_analysis_service
from app.features._01_image_upload.services._03_image_database_service import image_database_service
from app.features._01_image_upload.services._99_image_resize_service import image_resize_service

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
        print("================================================================================")
        print("【 GCSアップロード処理開始 】")
        print("================================================================================")

        # 1. アップロードされたファイルを検証
        file_validation_start_time = time.time()
        print("1. アップロードされたファイルを検証 -------------------")
        file_result = await file_processing_service.validate_and_read_file(file)    # _00_file_processing_service.pyを呼び出す
        content = file_result["content"]
        content_type = file_result["content_type"]
        filename = file_result["filename"]
        print(f"✅ ファイル検証完了: {time.time() - file_validation_start_time:.3f}秒 ===")

        # 1.5. 画像をリサイズ（縦長 1280×1920）
        resize_start_time = time.time()
        print("1.5. 画像をリサイズ（縦長 1280×1920） -------------------")
        resize_result = await image_resize_service.resize_image(
            image_data=content,
            target_width=1280,
            target_height=1920
        )
        
        if resize_result["success"]:
            # リサイズ後の画像を使用
            content = resize_result["resized_data"]
            # リサイズ後はPNG形式になるため、content_typeを更新
            content_type = "image/png"
            print(f"✅ 画像リサイズ完了: {time.time() - resize_start_time:.3f}秒 ===")
        else:
            # リサイズに失敗した場合は元の画像を使用
            print(f"⚠️ 画像リサイズ失敗、元の画像を使用します: {resize_result.get('error')}")
            print(f"⏱️ リサイズ処理時間（スキップ）: {time.time() - resize_start_time:.3f}秒 ===")

        # 2. GCSへアップロード
        upload_start_time = time.time()
        print("2. GCSへ画像をアップロード -------------------")
        try:
            upload_result = gcs_storage_service.upload_image(
                file_content=content,
                filename=filename or "uploaded_image",
                user_id=user_id,
                content_type=content_type,
            )

            # アップロードに失敗した場合はエラーを返す
            if not upload_result.get("success"):
                error_msg = upload_result.get('error', '不明なエラー')
                print(f"GCSアップロード失敗: {error_msg}")
                # テストモード時は詳細なエラーメッセージを返す
                is_test_mode = os.getenv("ENABLE_TEST_MODE", "false").lower() == "true"
                detail_msg = f"GCSアップロードに失敗しました: {error_msg}" if is_test_mode else "画像のアップロードに失敗しました"
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=detail_msg,
                )

            # アップロードに成功した場合はファイルパスと公開URLを取得
            file_path = upload_result["gcs_path"]
            public_url = upload_result["public_url"]
            print(f"✅ GCSに画像アップロード完了: {time.time() - upload_start_time:.3f}秒 ===")
        
        # エラーが発生した場合はエラーを返す
        except HTTPException:
            raise

        # エラーが発生した場合はエラーを返す
        except HTTPException:
            raise
        except Exception as gcs_error:
            upload_time = time.time() - upload_start_time
            print(f"⏱️ GCSアップロード時間（エラー）: {upload_time:.3f}秒")
            print(f"GCSエラー: {gcs_error}")
            print(f"エラーの詳細: {traceback.format_exc()}")
            # テストモード時は詳細なエラーメッセージを返す
            is_test_mode = os.getenv("ENABLE_TEST_MODE", "false").lower() == "true"
            detail_msg = f"GCSアップロードエラー: {str(gcs_error)}" if is_test_mode else "画像のアップロードに失敗しました"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=detail_msg,
            )

        # print(f"ファイルパス: {file_path}")
        # print(f"GCS public_url: {public_url}")

        # 3. Vision API 解析
        analysis_start_time = time.time()
        print("3. Vision API解析 -------------------")
        analysis_result = await image_analysis_service.analyze_image(content, filename)    # _02_image_analysis_service.pyを呼び出す
        meta_data_json = analysis_result["meta_data_json"]
        print(f"✅ Vision API解析完了: {time.time() - analysis_start_time:.3f}秒 ===")

        # 4. データベースへ保存
        db_result = await image_database_service.save_image_to_database(    # _03_image_database_service.pyを呼び出す
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
        error_traceback = traceback.format_exc()
        print(f"アップロード処理中にエラーが発生しました: {e}")
        print(f"エラーの詳細: {error_traceback}")
        # テストモード時は詳細なエラーメッセージを返す
        is_test_mode = os.getenv("ENABLE_TEST_MODE", "false").lower() == "true"
        if is_test_mode:
            detail_msg = f"画像のアップロードに失敗しました: {str(e)}"
        else:
            detail_msg = "画像のアップロードに失敗しました"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail_msg,
        )

