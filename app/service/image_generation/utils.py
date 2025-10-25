import os
from typing import Dict, Any, List
from datetime import datetime
from PIL import Image
from io import BytesIO
from .base_image_generator import BaseImageGenerator

class ImageUtils(BaseImageGenerator):
    """画像関連のユーティリティ機能を提供するクラス"""
    
    def upload_reference_image(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """参考画像をアップロード"""
        try:
            # 画像情報を取得
            image = Image.open(BytesIO(file_content))
            image_size = image.size
            image_format = image.format.lower() if image.format else "unknown"
            
            # ファイル名を生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = os.urandom(4).hex()
            filename = f"reference_{timestamp}_{unique_id}.{image_format}"
            
            # GCSにアップロード
            save_result = self.save_image_to_storage(
                image_data=file_content,
                filename=filename,
                user_id="2",  # 参考画像はデフォルトユーザーIDを使用
                content_type=f"image/{image_format}"
            )
            
            if save_result["success"]:
                return {
                    "filename": filename,
                    "filepath": save_result.get("filepath", save_result.get("gcs_path")),
                    "public_url": save_result.get("public_url"),
                    "size_bytes": len(file_content),
                    "image_size": image_size,
                    "format": image_format,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "error": f"画像アップロードに失敗しました: {save_result.get('error')}",
                    "filename": None
                }
                
        except Exception as e:
            print(f"❌ 参考画像アップロードエラー: {e}")
            return {
                "error": f"画像アップロードに失敗しました: {str(e)}",
                "filename": None
            }

    def get_uploaded_images_list(self) -> List[Dict[str, Any]]:
        """アップロードされた画像のリストを取得"""
        try:
            # GCSから画像リストを取得
            # 実際の実装では、GCSのバケットから画像ファイルを一覧取得する必要があります
            # ここでは簡易的な実装として空のリストを返します
            
            uploaded_images = []
            
            print(f"📁 アップロード画像一覧: {len(uploaded_images)}枚")
            return uploaded_images
            
        except Exception as e:
            print(f"❌ アップロード画像一覧取得エラー: {e}")
            return []

    def get_generation_history(self, story_plot_id: int) -> List[dict]:
        """画像生成履歴を取得"""
        try:
            # 実際の実装では、データベースから生成履歴を取得する必要があります
            # ここでは簡易的な実装として空のリストを返します
            
            history = []
            print(f"📋 画像生成履歴取得: StoryPlot ID {story_plot_id}")
            return history
            
        except Exception as e:
            print(f"❌ 画像生成履歴取得エラー: {e}")
            return []

    def get_generation_status(self, story_plot_id: int) -> dict:
        """画像生成状態を確認"""
        try:
            # 実際の実装では、データベースから生成状態を確認する必要があります
            # ここでは簡易的な実装としてデフォルト状態を返します
            
            status_info = {
                "story_plot_id": story_plot_id,
                "status": "unknown",
                "generated_pages": [],
                "total_pages": 5,
                "last_updated": datetime.now().isoformat()
            }
            
            print(f"📊 画像生成状態確認: StoryPlot ID {story_plot_id}")
            return status_info
            
        except Exception as e:
            print(f"❌ 画像生成状態確認エラー: {e}")
            return {
                "story_plot_id": story_plot_id,
                "status": "error",
                "error": str(e)
            }
