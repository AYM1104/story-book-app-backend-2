"""
画像解析サービス（Vision API）
"""
import os
import json
import tempfile
import time
from typing import Dict, Any, Optional
from app.service.vision_api_service import vision_service


class ImageAnalysisService:
    """画像解析処理を担当するサービス"""
    
    async def analyze_image(
        self, 
        image_data: bytes, 
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        画像をVision APIで解析する
        
        Args:
            image_data: 画像のバイトデータ
            filename: ファイル名（拡張子取得用）
        
        Returns:
            解析結果の辞書
        """
        start_time = time.time()
        temp_file_path = None
        
        print("=== Vision API解析処理開始 ===")
        
        try:
            # ファイル拡張子を取得
            file_extension = (
                filename.split(".")[-1].lower()
                if filename and "." in filename
                else "jpg"
            )
            
            # 一時ファイルを作成
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
                temp_file.write(image_data)
                temp_file_path = temp_file.name
            
            print(f"一時ファイル作成: {temp_file_path}")
            
            # Vision APIで解析
            analysis_result = await vision_service.analyze_image(temp_file_path)
            
            processing_time = time.time() - start_time
            print(f"　⭐️ Vision API解析時間: {processing_time:.3f}秒")
            print(f"　⭐️ Vision API解析結果: {analysis_result}")
            # print("=== Vision API解析処理完了 ===")
            
            return {
                "success": True,
                "analysis_result": analysis_result,
                "processing_time": processing_time,
                "meta_data_json": json.dumps(analysis_result, ensure_ascii=False)
            }
            
        except Exception as error:
            processing_time = time.time() - start_time
            print(f"⏱️ Vision API解析時間（エラー）: {processing_time:.3f}秒")
            print(f"Vision API解析エラー: {error}")
            
            # エラー時のデフォルト結果
            error_result = {
                "error": f"Vision API解析に失敗しました: {str(error)}",
                "labels": [],
                "text": [],
                "objects": [],
                "faces": [],
                "safe_search": {},
                "colors": [],
                "analysis_timestamp": None,
            }
            
            return {
                "success": False,
                "analysis_result": error_result,
                "processing_time": processing_time,
                "error": str(error),
                "meta_data_json": json.dumps(error_result, ensure_ascii=False)
            }
            
        finally:
            # 一時ファイルのクリーンアップ
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    print(f"🙆‍♀️ 一時ファイルを削除しました: {temp_file_path}")
                except Exception as cleanup_error:
                    print(f"一時ファイル削除エラー: {cleanup_error}")


# サービスインスタンス
image_analysis_service = ImageAnalysisService()
