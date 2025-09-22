import os, uuid, json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.images.images import UploadImages
from app.schemas.images.images import UploadImageResponse
from app.core.config import UPLOAD_DIR, MAX_UPLOAD_SIZE, ALLOWED_MIME, VISION_API_ENABLED
from app.service.vision_api_service import vision_service

router = APIRouter(prefix="/images", tags=["images"])

# 画像アップロードをするエンドポイント
@router.post("/upload", response_model=UploadImageResponse)
async def upload_image(
    file: UploadFile = File(...), 
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """画像ファイルをアップロードしてVision APIで解析するエンドポイント"""
    
    # ファイルのバリデーションチェック
    if not file.content_type or file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"サポートされていないファイル形式です。許可されている形式: {', '.join(ALLOWED_MIME)}"
        )
    
    # ファイルサイズのチェック
    if file.size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"ファイルサイズが大きすぎます。最大{MAX_UPLOAD_SIZE // (1024*1024)}MBまでです。"
        )
    
    try:
        # ファイルの保存先ディレクトリを作成
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # ファイル名を生成
        file_extension = file.filename.split(".")[-1].lower()
        file_name = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        # ファイルを保存
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # デバッグ情報
        print(f"VISION_API_ENABLED: {VISION_API_ENABLED}")
        print(f"ファイルパス: {file_path}")
        
        # Vision API解析
        analysis_result = None
        if VISION_API_ENABLED:
            try:
                print("Vision API解析を開始...")
                analysis_result = await vision_service.analyze_image(file_path)
                print(f"Vision API解析結果: {analysis_result}")
            except Exception as e:
                print(f"Vision API解析エラー: {str(e)}")
                # Vision API解析に失敗してもアップロードは続行
                analysis_result = {
                    "error": f"Vision API解析に失敗しました: {str(e)}",
                    "labels": [],
                    "text": [],
                    "objects": [],
                    "faces": [],
                    "safe_search": {},
                    "colors": [],
                    "analysis_timestamp": None
                }
        else:
            print("Vision API解析は無効化されています")
        
        # meta_dataの準備
        meta_data_json = None
        if analysis_result:
            meta_data_json = json.dumps(analysis_result, ensure_ascii=False)
            print(f"meta_data JSON: {meta_data_json}")
        else:
            print("analysis_resultがNoneです")
        
        # データベースに保存
        new_image = UploadImages(
            file_name=file.filename,
            file_path=str(file_path),
            content_type=file.content_type,
            size_bytes=len(content),
            user_id=user_id,
            meta_data=meta_data_json
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)

        print(f"保存された画像のmeta_data: {new_image.meta_data}")
        return new_image

    # エラーが発生した場合は保存したファイルを削除
    except Exception as e:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.unlink(file_path)
        
        print(f"エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ファイルのアップロードに失敗しました: {str(e)}"
        )

