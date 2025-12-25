"""
画像リサイズサービス
"""
import time
from typing import Dict, Any, Optional
from app.utils.image_utils import resize_image_to_fixed_size, get_image_info


class ImageResizeService:
    """画像リサイズ処理を担当するサービス"""
    
    def __init__(self):
        # 縦長（2:3）に変更
        self.default_width = 1280
        self.default_height = 1920
    
    async def resize_image(
        self, 
        image_data: bytes, 
        target_width: Optional[int] = None, 
        target_height: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        画像をリサイズする
        
        Args:
            image_data: 元画像のバイトデータ
            target_width: 目標幅（デフォルト: 1280）
            target_height: 目標高さ（デフォルト: 1920）
        
        Returns:
            リサイズ結果の辞書
        """
        start_time = time.time()
        
        # デフォルト値を設定
        width = target_width or self.default_width
        height = target_height or self.default_height
        
        print("=== 画像リサイズ処理開始 ===")
        
        try:
            # 元画像の情報を取得
            original_info = get_image_info(image_data)
            print(f"元画像情報: {original_info}")
            
            # 画像をリサイズ
            resized_data = resize_image_to_fixed_size(image_data, width, height)
            
            # リサイズ後の情報を取得
            resized_info = get_image_info(resized_data)
            print(f"リサイズ後情報: {resized_info}")
            
            processing_time = time.time() - start_time
            print(f"⏱️ 画像リサイズ時間: {processing_time:.3f}秒")
            print("=== 画像リサイズ処理完了 ===")
            
            return {
                "success": True,
                "resized_data": resized_data,
                "original_info": original_info,
                "resized_info": resized_info,
                "processing_time": processing_time,
                "file_extension": "png"
            }
            
        except Exception as error:
            processing_time = time.time() - start_time
            print(f"⏱️ 画像リサイズ時間（エラー）: {processing_time:.3f}秒")
            print(f"画像リサイズ処理エラー: {error}")
            print("リサイズ処理をスキップして元の画像を使用します")
            
            return {
                "success": False,
                "resized_data": image_data,
                "original_info": get_image_info(image_data),
                "resized_info": None,
                "processing_time": processing_time,
                "error": str(error),
                "file_extension": None  # 元のファイル拡張子を使用する必要がある
            }


# サービスインスタンス
image_resize_service = ImageResizeService()
