from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

# 物語の設定作成時のリクエストスキーマ
class StorySettingCreate(BaseModel):
    upload_image_id: int
    title_suggestion: Optional[str] = None
    protagonist_name: Optional[str] = None
    protagonist_type: Optional[str] = None
    setting_place: Optional[str] = None
    tone: Optional[str] = None
    target_age: Optional[str] = None
    language: Optional[str] = None
    reading_level: Optional[str] = None
    style_guideline: Optional[Dict[str, Any]] = None

