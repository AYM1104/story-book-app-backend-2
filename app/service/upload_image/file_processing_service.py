"""
ファイル処理サービス
"""
import time
from typing import Dict, Any, Optional
from fastapi import UploadFile, HTTPException, status
from app.core.config import MAX_UPLOAD_SIZE, ALLOWED_MIME


class FileProcessingService:
    """ファイル処理を担当するサービス"""
    
    async def validate_and_read_file(
        self, 
        file: UploadFile
    ) -> Dict[str, Any]:
        """
        ファイルの検証と読み込みを行う
        
        Args:
            file: アップロードされたファイル
        
        Returns:
            ファイル処理結果の辞書
        """
        start_time = time.time()
                
        try:
            # ファイル形式の検証
            if not file.content_type or file.content_type not in ALLOWED_MIME:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"サポートされていないファイル形式です。許可されている形式: {', '.join(ALLOWED_MIME)}",
                )
            
            # ファイル読み込み
            read_start_time = time.time()
            content = await file.read()
            read_time = time.time() - read_start_time
            
            print(f"　⭐️ ファイル読み込み時間: {read_time:.3f}秒")
            print(f"　⭐️ 読み込んだファイルサイズ: {len(content)} bytes")
            
            # ファイルサイズの検証
            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"ファイルサイズが大きすぎます。最大{MAX_UPLOAD_SIZE // (1024 * 1024)}MBまでです。",
                )
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "content": content,
                "content_type": file.content_type,
                "filename": file.filename,
                "size_bytes": len(content),
                "processing_time": processing_time,
                "read_time": read_time
            }
            
        except HTTPException:
            raise
        except Exception as error:
            processing_time = time.time() - start_time
            print(f"⏱️ ファイル処理時間（エラー）: {processing_time:.3f}秒")
            print(f"ファイル処理エラー: {error}")
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ファイルの処理に失敗しました: {error}",
            )


# サービスインスタンス
file_processing_service = FileProcessingService()
