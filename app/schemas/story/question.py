from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class QuestionOption(BaseModel):
    value: str
    label: str

class Question(BaseModel):
    field: str
    question: str
    type: str  # "text_input", "select"
    placeholder: Optional[str] = None
    options: Optional[List[QuestionOption]] = None
    required: bool = True

class QuestionResponse(BaseModel):
    questions: List[Question]
    story_setting_id: int
    message: str
    processing_time_ms: Optional[float] = None  # 処理時間（ミリ秒）

class AnswerRequest(BaseModel):
    field: str
    answer: str

class AnswerResponse(BaseModel):
    story_setting_id: int
    field: str
    answer: str
    message: str
    processing_time_ms: Optional[float] = None  # 処理時間（ミリ秒）
