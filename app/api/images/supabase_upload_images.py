import os, uuid, json, tempfile
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.database.supabase_session import get_supabase_db
from app.models.images.supabase_images import SupabaseUploadImages
from app.schemas.images.images import UploadImageResponse
from app.core.supabase_config import MAX_UPLOAD_SIZE, ALLOWED_MIME, SUPABASE_STORAGE_BUCKET
from app.service.vision_api_service import vision_service
from app.service.gcs_storage_service import GCSStorageService
from app.utils.image_utils import resize_image_to_fixed_size, get_image_info

router = APIRouter(prefix="/images", tags=["images"])

# GCSサービスのインスタンス化
gcs_storage_service = GCSStorageService()

# 既存の画像用の認証済みURLを生成するエンドポイント（Supabase用）
@router.get("/signed-url/{image_id}")
async def get_supabase_signed_url(image_id: int, db: Session = Depends(get_supabase_db)):
    """Supabase用の既存画像認証済みURL生成エンドポイント"""
    try:
        # 画像情報を取得
        image = db.query(SupabaseUploadImages).filter(SupabaseUploadImages.id == image_id).first()
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

# 画像アップロードをするエンドポイント（Supabase用）
@router.post("/upload", response_model=UploadImageResponse)
async def upload_supabase_image(
    file: UploadFile = File(...), 
    user_id: int = Form(...),
    db: Session = Depends(get_supabase_db)
):
    """Supabase用の画像ファイルアップロードエンドポイント"""
    
    # ファイルのバリデーションチェック
    if not file.content_type or file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"サポートされていないファイル形式です。許可されている形式: {', '.join(ALLOWED_MIME)}"
        )
    
    try:
        print("🔥🔥🔥 SUPABASE UPLOAD - 新しいコードが実行されています！ 🔥🔥🔥")
        print("=== Supabaseアップロード処理開始 ===")
        
        # ファイル内容を読み込み（サイズ検証を保存前に実施）
        content = await file.read()
        print(f"読み込んだファイルサイズ: {len(content)} bytes")
        
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"ファイルサイズが大きすぎます。最大{MAX_UPLOAD_SIZE // (1024*1024)}MBまでです。"
            )

        print("=== 画像リサイズ処理開始 ===")
        # 画像を1920x1080の固定サイズにリサイズ（縦横比保持、透明背景）
        try:
            # インポート確認
            from app.utils.image_utils import resize_image_to_fixed_size, get_image_info
            print("画像ユーティリティのインポート成功")
            
            original_info = get_image_info(content)
            print(f"元画像情報: {original_info}")
            
            resized_content = resize_image_to_fixed_size(content, 1920, 1080)
            resized_info = get_image_info(resized_content)
            print(f"リサイズ後情報: {resized_info}")
            
            # リサイズ後のコンテンツを使用
            content = resized_content
            print("=== 画像リサイズ処理完了 ===")
        except ImportError as e:
            print(f"画像ユーティリティのインポートエラー: {e}")
            print("リサイズ処理をスキップして元の画像を使用します")
        except Exception as e:
            print(f"画像リサイズ処理エラー: {e}")
            print("リサイズ処理をスキップして元の画像を使用します")

        # ファイル拡張子を決定（リサイズ成功時はPNG、失敗時は元の拡張子）
        try:
            # リサイズ処理が成功した場合はPNG
            file_extension = "png"
            print("ファイル拡張子をPNGに設定")
        except:
            # リサイズ処理が失敗した場合は元の拡張子
            file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
            print(f"ファイル拡張子を元のまま設定: {file_extension}")
        
        # ストレージタイプに応じて保存先を決定
        # 現在はGCSを使用（将来的にSupabaseストレージに移行可能）
        try:
            # GCSサービスを使用（user_idが必要）
            content_type = "image/png" if file_extension == "png" else file.content_type
            upload_result = gcs_storage_service.upload_image(
                file_content=content,
                filename=file.filename or "uploaded_image",
                user_id=user_id,
                content_type=content_type
            )
            
            if not upload_result["success"]:
                print(f"GCSアップロード失敗: {upload_result['error']}")
                raise HTTPException(status_code=500, detail="画像のアップロードに失敗しました")
            
            file_path = upload_result["gcs_path"]
            public_url = upload_result["public_url"]
                
        except Exception as gcs_error:
            print(f"GCSエラー: {str(gcs_error)}")
            raise HTTPException(status_code=500, detail=f"画像のアップロードに失敗しました: {str(gcs_error)}")
        
        # デバッグ情報
        print(f"ファイルパス: {file_path}")
        print(f"GCS public_url: {public_url}")
        
        # Vision API解析
        analysis_result = None
        temp_file_path = None
        try:
            print("Vision API解析を開始...")
            # 一時ファイルを作成（クロスプラットフォーム対応）
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            analysis_result = await vision_service.analyze_image(temp_file_path)
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
        
        # meta_dataの準備
        meta_data_json = None
        if analysis_result:
            meta_data_json = json.dumps(analysis_result, ensure_ascii=False)
            print(f"meta_data JSON: {meta_data_json}")
        
        # データベースに保存
        new_image = SupabaseUploadImages(
            file_name=file.filename,
            file_path=file_path,
            content_type=file.content_type,
            size_bytes=len(content),
            user_id=user_id,
            meta_data=meta_data_json,
            public_url=public_url
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
            "uploaded_at": new_image.created_at.isoformat(),  # SupabaseBaseのcreated_atを使用
            "meta_data": new_image.meta_data,
            "public_url": new_image.public_url
        }
        
        # デバッグ用ログ
        print(f"Database public_url: {new_image.public_url}")
        print(f"Response public_url: {response_data['public_url']}")
        print(f"Response file_path: {response_data['file_path']}")
        
        return response_data

    # エラーが発生した場合は保存したファイルを削除
    except HTTPException:
        raise
    except Exception as e:
        print(f"アップロード処理中にエラーが発生しました: {str(e)}")
        import traceback
        print(f"エラーの詳細: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"画像のアップロードに失敗しました: {str(e)}"
        )

# 画像一覧取得エンドポイント（Supabase用）
@router.get("/", response_model=list[UploadImageResponse])
def get_supabase_images(db: Session = Depends(get_supabase_db)):
    """Supabase用の画像一覧取得エンドポイント"""
    
    images = db.query(SupabaseUploadImages).all()
    return [
        {
            "id": img.id,
            "file_name": img.file_name,
            "file_path": img.file_path,
            "content_type": img.content_type,
            "size_bytes": img.size_bytes,
            "uploaded_at": img.created_at.isoformat(),
            "meta_data": img.meta_data,
            "public_url": img.public_url
        }
        for img in images
    ]

# 画像詳細取得エンドポイント（Supabase用）
@router.get("/{image_id}", response_model=UploadImageResponse)
def get_supabase_image(image_id: int, db: Session = Depends(get_supabase_db)):
    """Supabase用の画像詳細取得エンドポイント"""
    
    image = db.query(SupabaseUploadImages).filter(SupabaseUploadImages.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="画像が見つかりません")
    
    return {
        "id": image.id,
        "file_name": image.file_name,
        "file_path": image.file_path,
        "content_type": image.content_type,
        "size_bytes": image.size_bytes,
        "uploaded_at": image.created_at.isoformat(),
        "meta_data": image.meta_data,
        "public_url": image.public_url
    }
