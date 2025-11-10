"""
画像リサイズサービスのテスト
"""
import pytest
import io
from PIL import Image
from app.service.upload_image._99_image_resize_service import ImageResizeService


class TestImageResizeService:
    """ImageResizeServiceのテストクラス"""
    
    def setup_method(self):
        """テストのセットアップ"""
        self.service = ImageResizeService()
    
    def create_test_image(self, width: int = 100, height: int = 100) -> bytes:
        """テスト用の画像を作成"""
        image = Image.new('RGB', (width, height), color='red')
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()
    
    @pytest.mark.asyncio
    async def test_resize_image_success(self):
        """正常なリサイズ処理のテスト"""
        # テスト用画像を作成
        original_image = self.create_test_image(200, 150)
        
        # リサイズ実行
        result = await self.service.resize_image(original_image, 1920, 1080)
        
        # 結果の検証
        assert result["success"] is True
        assert "resized_data" in result
        assert "original_info" in result
        assert "resized_info" in result
        assert result["file_extension"] == "png"
        
        # リサイズ後のデータが元のデータと異なることを確認
        assert result["resized_data"] != original_image
        
        # リサイズ後の画像情報を確認
        resized_info = result["resized_info"]
        assert resized_info["width"] == 1920
        assert resized_info["height"] == 1080
    
    @pytest.mark.asyncio
    async def test_resize_image_with_default_size(self):
        """デフォルトサイズでのリサイズテスト"""
        original_image = self.create_test_image(100, 100)
        
        # デフォルトサイズでリサイズ
        result = await self.service.resize_image(original_image)
        
        assert result["success"] is True
        resized_info = result["resized_info"]
        assert resized_info["width"] == 1920
        assert resized_info["height"] == 1080
    
    @pytest.mark.asyncio
    async def test_resize_image_custom_size(self):
        """カスタムサイズでのリサイズテスト"""
        original_image = self.create_test_image(300, 200)
        
        # カスタムサイズでリサイズ
        result = await self.service.resize_image(original_image, 800, 600)
        
        assert result["success"] is True
        resized_info = result["resized_info"]
        assert resized_info["width"] == 800
        assert resized_info["height"] == 600
    
    @pytest.mark.asyncio
    async def test_resize_image_invalid_data(self):
        """無効な画像データでのテスト"""
        invalid_data = b"invalid image data"
        
        result = await self.service.resize_image(invalid_data)
        
        # エラーが発生することを期待
        assert result["success"] is False
        assert "error" in result
        assert result["resized_data"] == invalid_data  # 元のデータが返される
        assert result["file_extension"] is None
    
    @pytest.mark.asyncio
    async def test_resize_image_empty_data(self):
        """空のデータでのテスト"""
        empty_data = b""
        
        result = await self.service.resize_image(empty_data)
        
        assert result["success"] is False
        assert "error" in result
        assert result["resized_data"] == empty_data
