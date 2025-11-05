from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from fastapi import UploadFile

class ImageGenerationRequest(BaseModel):
    """単一画像生成リクエスト"""
    prompt: str
    prefix: Optional[str] = "storybook_image"

class MultipleImageGenerationRequest(BaseModel):
    """複数画像生成リクエスト"""
    prompts: List[str]
    prefix: Optional[str] = "storybook_page"

class StorybookImageGenerationRequest(BaseModel):
    """絵本画像生成リクエスト"""
    story_pages: List[str]
    storybook_id: str

class ImageInfo(BaseModel):
    """画像情報"""
    filename: str
    filepath: str
    size_bytes: int
    image_size: tuple
    format: str
    timestamp: str
    prompt: Optional[str] = None
    page_number: Optional[int] = None
    storybook_id: Optional[str] = None
    page_content: Optional[str] = None

class ImageGenerationResponse(BaseModel):
    """画像生成レスポンス"""
    success: bool
    message: str
    images: List[ImageInfo]
    total_generated: int

class SingleImageGenerationResponse(BaseModel):
    """単一画像生成レスポンス"""
    success: bool
    message: str
    image: ImageInfo

class StoryPlotImageGenerationRequest(BaseModel):
    """StoryPlot画像生成リクエスト"""
    story_plot_id: int
    page_number: int

class StoryPlotAllPagesGenerationRequest(BaseModel):
    """StoryPlot全ページ画像生成リクエスト"""
    story_plot_id: int

class StoryPlotImageInfo(BaseModel):
    """StoryPlot画像情報"""
    story_plot_id: int
    page_number: int
    filename: str
    filepath: str
    size_bytes: int
    image_size: tuple
    format: str
    timestamp: str
    page_content: str
    title: Optional[str] = None
    protagonist_name: Optional[str] = None
    setting_place: Optional[str] = None

class StoryPlotImageGenerationResponse(BaseModel):
    """StoryPlot画像生成レスポンス"""
    success: bool
    message: str
    image: StoryPlotImageInfo

class StoryPlotAllPagesGenerationResponse(BaseModel):
    """StoryPlot全ページ画像生成レスポンス"""
    success: bool
    message: str
    images: List[StoryPlotImageInfo]
    total_generated: int

class ImageToImageRequest(BaseModel):
    """Image-to-Image生成リクエスト"""
    prompt: str
    reference_image_path: str  # 参考画像のパス
    strength: Optional[float] = 1.0  # 参考画像の影響度 (0.0-1.0)
    prefix: Optional[str] = "i2i_image"

class ImageToImageResponse(BaseModel):
    """Image-to-Image生成レスポンス"""
    success: bool
    message: str
    image: ImageInfo
    reference_image_path: str
    strength: float

class StoryPlotImageToImageRequest(BaseModel):
    """StoryPlot用Image-to-Image生成リクエスト"""
    story_plot_id: int
    page_number: int
    reference_image_path: str
    strength: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="強度は0.0-1.0の範囲で指定してください")
    prefix: Optional[str] = "storyplot_i2i"

class StoryPlotAllPagesImageToImageRequest(BaseModel):
    """StoryPlot全ページImage-to-Image生成リクエスト"""
    # story_plot_idまたはstorybook_idのどちらか一方を指定
    story_plot_id: Optional[int] = None
    storybook_id: Optional[int] = None
    # 省略可。未指定の場合は story_plot_id → story_setting → upload_image.file_path を自動解決
    reference_image_path: Optional[str] = None
    strength: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="強度は0.0-1.0の範囲で指定してください")
    story_pages: Optional[int] = Field(default=5, ge=3, le=10, description="物語ページ数（3, 5, 7, 10のいずれか、デフォルトは5）")
    prefix: Optional[str] = "storyplot_i2i_all"

class StorybookAllPagesImageToImageRequest(BaseModel):
    """ストーリーブック全ページImage-to-Image生成リクエスト"""
    storybook_id: int
    # 省略可。未指定の場合は storybook_id → story_plot_id → story_setting → upload_image.file_path を自動解決
    reference_image_path: Optional[str] = None
    strength: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="強度は0.0-1.0の範囲で指定してください")
    prefix: Optional[str] = "storybook_i2i_all"

class StorybookAllPagesGenerationResponse(BaseModel):
    """ストーリーブック全ページ画像生成レスポンス"""
    success: bool
    message: str
    images: List[StoryPlotImageInfo]
    total_generated: int

class ImageUploadResponse(BaseModel):
    """画像アップロードレスポンス"""
    success: bool
    message: str
    filename: str
    filepath: str
    size_bytes: int
    image_size: tuple
    format: str
    timestamp: str
