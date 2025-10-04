"""
画像処理に関するユーティリティ関数
"""
import io
from PIL import Image, ImageOps


def resize_image_to_fixed_size(image_data: bytes, target_width: int = 1920, target_height: int = 1080) -> bytes:
    """
    画像を指定された固定サイズにリサイズする（縦横比保持、透明背景）
    
    Args:
        image_data: 元画像のバイトデータ
        target_width: 目標幅
        target_height: 目標高さ
    
    Returns:
        リサイズされた画像のバイトデータ
    """
    try:
        print(f"画像リサイズ開始: 目標サイズ {target_width} x {target_height}")
        print(f"入力データサイズ: {len(image_data)} bytes")
        
        # 画像を開く
        image = Image.open(io.BytesIO(image_data))
        print(f"元画像サイズ: {image.width} x {image.height}")
        print(f"元画像形式: {image.format}, モード: {image.mode}")
        
        # RGBAモードに変換（透明背景のため）
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # 元画像の縦横比を計算
        original_ratio = image.width / image.height
        target_ratio = target_width / target_height
        
        # 縦横比を保持してリサイズするサイズを計算
        if original_ratio > target_ratio:
            # 元画像が横長の場合、幅を基準にリサイズ
            new_width = target_width
            new_height = int(target_width / original_ratio)
        else:
            # 元画像が縦長の場合、高さを基準にリサイズ
            new_height = target_height
            new_width = int(target_height * original_ratio)
        
        # 画像をリサイズ（高品質なリサンプリングを使用）
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 透明背景の新しいキャンバスを作成
        canvas = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))
        
        # リサイズした画像を中央に配置
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        canvas.paste(resized_image, (x_offset, y_offset), resized_image)
        
        # バイトデータに変換（PNG形式で透明背景を保持）
        output_buffer = io.BytesIO()
        canvas.save(output_buffer, format='PNG', optimize=True)
        
        result_data = output_buffer.getvalue()
        print(f"リサイズ完了: 出力サイズ {len(result_data)} bytes")
        print(f"最終画像サイズ: {canvas.width} x {canvas.height}")
        print(f"配置位置: x={x_offset}, y={y_offset}")
        
        return result_data
        
    except Exception as e:
        print(f"画像リサイズエラー: {str(e)}")
        # エラーの場合は元の画像データをそのまま返す
        return image_data


def get_image_info(image_data: bytes) -> dict:
    """
    画像の情報を取得する
    
    Args:
        image_data: 画像のバイトデータ
    
    Returns:
        画像情報の辞書
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        return {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
            "aspect_ratio": round(image.width / image.height, 2)
        }
    except Exception as e:
        print(f"画像情報取得エラー: {str(e)}")
        return {
            "width": 0,
            "height": 0,
            "format": "unknown",
            "mode": "unknown",
            "aspect_ratio": 0
        }
