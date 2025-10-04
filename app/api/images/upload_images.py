import os, uuid, json, tempfile
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.images.images import UploadImages
from app.schemas.images.images import UploadImageResponse
from app.core.config import UPLOAD_DIR, MAX_UPLOAD_SIZE, ALLOWED_MIME, VISION_API_ENABLED, STORAGE_TYPE
from app.service.vision_api_service import vision_service
from app.service.gcs_storage_service import GCSStorageService
from app.utils.image_utils import resize_image_to_aspect_ratio, get_image_info

# ファイル読み込み確認用のテスト出力
print("=" * 100)
print("📁 UPLOAD_IMAGES.PY FILE LOADED - NEW VERSION")
print("=" * 100)

router = APIRouter(prefix="/images", tags=["images"])

# GCSサービスのインスタンス化
gcs_storage_service = GCSStorageService()

# 既存の画像用の認証済みURLを生成するエンドポイント
@router.get("/signed-url/{image_id}")
async def get_signed_url(image_id: int, db: Session = Depends(get_db)):
    """既存の画像用に認証済みURLを生成"""
    try:
        # 画像情報を取得
        image = db.query(UploadImages).filter(UploadImages.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="画像が見つかりません")
        
        # ローカルストレージの場合は既存のパスをそのまま返る
        if not image.file_path.startswith("users/"):
            filename = urlparse(image.file_path).path.split("/")[-1]
            return {"signed_url": f"http://localhost:8000/uploads/{filename}"}
        
        # GCSの場合、認証済みURLを生成
        try:
            blob = gcs_storage_service.bucket.blob(image.file_path)
            from datetime import timedelta
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=1),
                method="GET"
            )
            return {"signed_url": signed_url}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"認証済みURLの生成に失敗しました: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"エラーが発生しました: {str(e)}")

# 画像アップロードをするエンドポイント
@router.post("/upload", response_model=UploadImageResponse)
async def upload_image(
    file: UploadFile = File(...), 
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """画像ファイルをアップロードしてVision APIで解析するエンドポイント"""
    
    # サーバー再起動確認用のテスト出力
    print("🔥🔥🔥 サーバーが更新されたコードを使用しています！ 🔥🔥🔥")
    print("🚀🚀🚀 このメッセージが見えていれば、新しいコードが実行されています！ 🚀🚀🚀")
    print("=" * 80)
    print("UPLOAD FUNCTION CALLED - NEW CODE IS RUNNING")
    print("=" * 80)
    
    # ファイルのバリデーションチェック
    if not file.content_type or file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"サポートされていないファイル形式です。許可されている形式: {', '.join(ALLOWED_MIME)}"
        )
    
    try:
        print("=== アップロード処理開始 ===")
        print(f"ファイル名: {file.filename}")
        print(f"コンテンツタイプ: {file.content_type}")
        print(f"ユーザーID: {user_id}")
        
        # ファイル内容を読み込み（サイズ検証を保存前に実施）
        content = await file.read()
        print(f"読み込んだファイルサイズ: {len(content)} bytes")
        
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"ファイルサイズが大きすぎます。最大{MAX_UPLOAD_SIZE // (1024*1024)}MBまでです。"
            )

        print("=== 画像リサイズ処理開始 ===")
        # 画像を16:9のアスペクト比にリサイズ
        print("=" * 50)
        print("画像リサイズ処理開始")
        print("=" * 50)
        
        # インポート確認
        try:
            from app.utils.image_utils import get_image_info, resize_image_to_aspect_ratio
            print("画像ユーティリティのインポート成功")
        except ImportError as e:
            print(f"画像ユーティリティのインポートエラー: {e}")
            raise
        
        original_info = get_image_info(content)
        print(f"元画像情報: {original_info}")
        print(f"元画像サイズ: {len(content)} bytes")
        
        resized_content = resize_image_to_aspect_ratio(content, "16:9")
        resized_info = get_image_info(resized_content)
        print(f"リサイズ後情報: {resized_info}")
        print(f"リサイズ後サイズ: {len(resized_content)} bytes")
        
        # リサイズ前後のサイズを比較
        size_change = len(resized_content) - len(content)
        print(f"サイズ変化: {size_change} bytes ({'増加' if size_change > 0 else '減少' if size_change < 0 else '変化なし'})")
        
        # リサイズ後のコンテンツを使用
        content = resized_content
        
        print("=" * 50)
        print("画像リサイズ処理完了")
        print("=" * 50)

        # ファイル拡張子を最初に決定（共通で使用）
        file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
        
        # ストレージタイプに応じて保存先を決定
        if STORAGE_TYPE == "gcs":

            try:
                print("GCSアップロード開始")
                print(f"アップロードするコンテンツサイズ: {len(content)} bytes")
                print(f"ファイル名: {file.filename}")
                print(f"ユーザーID: {user_id}")
                print(f"コンテンツタイプ: {file.content_type}")
                
                # GCSサービスを使用（user_idが必要）
                upload_result = gcs_storage_service.upload_image(
                    file_content=content,
                    filename=file.filename or "uploaded_image",
                    user_id=user_id,  # これが重要！
                    content_type=file.content_type
                )
                
                print(f"GCSアップロード結果: {upload_result}")
                
                if not upload_result["success"]:
                    print(f"GCSアップロード失敗: {upload_result['error']}")
                    print("ローカルストレージにフォールバック...")
                    # ローカルストレージにフォールバック
                    os.makedirs(UPLOAD_DIR, exist_ok=True)
                    
                    # ファイル名を生成
                    file_name = f"{uuid.uuid4()}.{file_extension}"
                    file_path = os.path.join(UPLOAD_DIR, file_name)
                    
                    # ファイルを保存
                    with open(file_path, "wb") as buffer:
                        buffer.write(content)
                    
                    public_url = None
                else:
                    file_path = upload_result["gcs_path"]
                    public_url = upload_result["public_url"]
                    
            except Exception as gcs_error:
                print(f"GCSエラーでローカルストレージにフォールバック: {str(gcs_error)}")
                # ローカルストレージにフォールバック
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                
                # ファイル名を生成
                file_name = f"{uuid.uuid4()}.{file_extension}"
                file_path = os.path.join(UPLOAD_DIR, file_name)
                
                # ファイルを保存
                with open(file_path, "wb") as buffer:
                    buffer.write(content)
                
                public_url = None
            
        else:
            # ローカルストレージに保存（従来の方法）
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            
            # ファイル名を生成
            file_name = f"{uuid.uuid4()}.{file_extension}"
            file_path = os.path.join(UPLOAD_DIR, file_name)
            
            # ファイルを保存
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            public_url = None
        
        # デバッグ情報
        print(f"STORAGE_TYPE: {STORAGE_TYPE}")
        print(f"VISION_API_ENABLED: {VISION_API_ENABLED}")
        print(f"ファイルパス: {file_path}")
        
        # GCS使用時の詳細情報を出力
        if STORAGE_TYPE == "gcs":
            print(f"GCS upload success: {upload_result['success']}")
            print(f"GCS public_url: {upload_result.get('public_url')}")
        else:
            print("ローカルストレージを使用中")
        
        # Vision API解析
        analysis_result = None
        temp_file_path = None
        if VISION_API_ENABLED:
            try:
                print("Vision API解析を開始...")
                # GCSの場合は一時的にローカルに保存してから解析
                if STORAGE_TYPE == "gcs":
                    # 一時ファイルを作成（クロスプラットフォーム対応）
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
                        temp_file.write(content)
                        temp_file_path = temp_file.name
                    
                    analysis_result = await vision_service.analyze_image(temp_file_path)
                else:
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
            finally:
                # 一時ファイルを削除
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                        print(f"一時ファイルを削除しました: {temp_file_path}")
                    except Exception as e:
                        print(f"一時ファイル削除エラー: {str(e)}")
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
            file_path=file_path,  # GCSの場合はgcs_path、ローカルの場合はローカルパス
            content_type=file.content_type,
            size_bytes=len(content),
            user_id=user_id,
            meta_data=meta_data_json,
            public_url=public_url if STORAGE_TYPE == "gcs" else None  # GCSの場合のみ保存
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)

        print(f"保存された画像のmeta_data: {new_image.meta_data}")
        
        # レスポンスに公開URLを含める
        response_data = {
            "id": new_image.id,
            "file_name": new_image.file_name,
            "file_path": new_image.file_path,
            "content_type": new_image.content_type,
            "size_bytes": new_image.size_bytes,
            "user_id": new_image.user_id,
            "uploaded_at": new_image.uploaded_at.isoformat(),
            "meta_data": new_image.meta_data,
            "public_url": new_image.public_url  # データベースから取得
        }
        
        # デバッグ用ログ
        print(f"Stored image - STORAGE_TYPE: {STORAGE_TYPE}")
        print(f"Database public_url: {new_image.public_url}")
        print(f"Response public_url: {response_data['public_url']}")
        print(f"Response file_path: {response_data['file_path']}")
        
        return response_data

    # エラーが発生した場合は保存したファイルを削除
    except HTTPException:
        raise
    except Exception as e:
        print(f"エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"画像のアップロードに失敗しました: {str(e)}"
        )

