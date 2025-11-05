from .image_generation.basic_generator import BasicImageGenerator
from .image_generation.image_to_image_generator import ImageToImageGenerator
from .image_generation.storyplot_generator import StoryPlotGenerator
from .image_generation.storybook_generator import StoryBookGenerator
from .image_generation.utils import ImageUtils

class ImageGeneratorService:
    """画像生成サービスのメインクラス（デリゲーションパターン）"""
    
    def __init__(self):
        """各機能別ジェネレーターを初期化"""
        self.basic = BasicImageGenerator()
        self.i2i = ImageToImageGenerator()
        self.storyplot = StoryPlotGenerator()
        self.storybook = StoryBookGenerator()
        self.utils = ImageUtils()
    
    # === 基本画像生成メソッド ===
    def generate_single_image(self, prompt: str, prefix: str = "storybook_image", user_id: str = None) -> dict:
        """単一の画像を生成"""
        return self.basic.generate_single_image(prompt, prefix, user_id)
    
    def generate_multiple_images(self, prompts: list, prefix: str = "storybook_page", user_id: str = None) -> list:
        """複数の画像を一括生成"""
        return self.basic.generate_multiple_images(prompts, prefix, user_id)
    
    # === Image-to-Image生成メソッド ===
    def generate_image_to_image(
        self, 
        prompt: str, 
        reference_image_path: str, 
        strength: float = 1.0,
        prefix: str = "i2i_image",
        user_id: str = None
    ) -> dict:
        """Image-to-Image生成"""
        return self.i2i.generate_image_to_image(prompt, reference_image_path, strength, prefix, user_id)
    
    # === StoryPlot関連メソッド ===
    def generate_storyplot_image_to_image(
        self, 
        db, 
        story_plot_id: int, 
        page_number: int, 
        reference_image_path: str,
        strength: float = 1.0,  # 参考画像の影響度
        prefix: str = "storyplot_i2i",
        user_id: str = None
    ) -> dict:
        """StoryPlot用Image-to-Image生成（1ページずつ）"""
        return self.storyplot.generate_storyplot_image_to_image(
            db, story_plot_id, page_number, reference_image_path, strength, prefix, user_id
        )
    
    def generate_storyplot_all_pages_i2i(
        self, 
        db, 
        story_plot_id: int, 
        reference_image_path: str,
        strength: float = 1.0,
        prefix: str = "storyplot_i2i_all",
        user_id: str = None,
        story_pages: int = 5
    ) -> list:
        """StoryPlotの全ページをi2iで一括生成"""
        return self.storyplot.generate_storyplot_all_pages_i2i(
            db, story_plot_id, reference_image_path, strength, prefix, user_id, story_pages
        )
    
    # === StoryBook関連メソッド ===
    def generate_storybook_images(self, story_pages: list, storybook_id: str, user_id: str = None) -> list:
        """絵本用の画像を生成（ストーリーページごと）"""
        return self.storybook.generate_storybook_images(story_pages, storybook_id, user_id)
    
    def generate_image_for_story_plot_page(self, db, story_plot_id: int, page_number: int, user_id: str = None) -> dict:
        """StoryPlotの指定ページの画像を生成"""
        return self.storybook.generate_image_for_story_plot_page(db, story_plot_id, page_number, user_id)
    
    def generate_all_pages_for_story_plot(self, db, story_plot_id: int, user_id: str = None, story_pages: int = 5) -> list:
        """StoryPlotの全ページの画像を一括生成"""
        return self.storybook.generate_all_pages_for_story_plot(db, story_plot_id, user_id, story_pages)
    
    # === ユーティリティメソッド ===
    def upload_reference_image(self, file_content: bytes, filename: str) -> dict:
        """参考画像をアップロード"""
        return self.utils.upload_reference_image(file_content, filename)
    
    def get_uploaded_images_list(self) -> list:
        """アップロードされた画像のリストを取得"""
        return self.utils.get_uploaded_images_list()
    
    def get_generation_history(self, story_plot_id: int) -> list:
        """画像生成履歴を取得"""
        return self.utils.get_generation_history(story_plot_id)
    
    def get_generation_status(self, story_plot_id: int, db=None) -> dict:
        """画像生成状態を確認"""
        return self.utils.get_generation_status(story_plot_id, db=db)
    
    # === 後方互換性のためのメソッド ===
    def create_save_directory(self, subdir: str = None):
        """画像保存用ディレクトリを作成（GCS使用のため不要）"""
        return None
    
    def generate_unique_filename(self, prefix: str = "generated_image", extension: str = "png"):
        """ユニークなファイル名を生成"""
        return self.basic.generate_unique_filename(prefix, extension)
    
    def save_image_to_storage(self, image_data: bytes, filename: str, user_id: str, story_id: int = None, content_type: str = "image/png") -> dict:
        """画像をGoogle Cloud Storageに保存"""
        return self.basic.save_image_to_storage(image_data, filename, user_id, story_id, content_type)
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """画像ファイルをBase64エンコード"""
        return self.basic.encode_image_to_base64(image_path)

# シングルトンインスタンス
image_generator_service = ImageGeneratorService()
