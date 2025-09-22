from pydantic import BaseModel
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
    strength: Optional[float] = 0.8  # 参考画像の影響度 (0.0-1.0)
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
    strength: Optional[float] = 0.8
    prefix: Optional[str] = "storyplot_i2i"

class StoryPlotAllPagesImageToImageRequest(BaseModel):
    """StoryPlot全ページImage-to-Image生成リクエスト"""
    story_plot_id: int
    reference_image_path: str
    strength: Optional[float] = 0.8
    prefix: Optional[str] = "storyplot_i2i_all"

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
