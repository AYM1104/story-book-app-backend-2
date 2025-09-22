from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.story.story_setting import StorySetting
from app.service.question_generator_service import question_generator_service
from app.schemas.story.question import QuestionResponse, AnswerRequest, AnswerResponse

router = APIRouter(prefix="/story", tags=["story-questions"])

@router.get("/story_settings/{story_setting_id}/questions", response_model=QuestionResponse)
async def get_questions_for_story_setting(
    story_setting_id: int,
    db: Session = Depends(get_db)
):
    """物語設定の不足情報に対して質問を生成するエンドポイント"""
    
    # 物語設定を取得
    story_setting = db.query(StorySetting).filter(
        StorySetting.id == story_setting_id
    ).first()
    
    if not story_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"物語設定ID {story_setting_id} が見つかりません"
        )
    
    # 物語設定を辞書形式に変換
    story_setting_dict = {
        "id": story_setting.id,
        "upload_image_id": story_setting.upload_image_id,
        "title_suggestion": story_setting.title_suggestion,
        "protagonist_name": story_setting.protagonist_name,
        "protagonist_type": story_setting.protagonist_type,
        "setting_place": story_setting.setting_place,
        "tone": story_setting.tone,
        "target_age": story_setting.target_age,
        "language": story_setting.language,
        "reading_level": story_setting.reading_level,
        "style_guideline": story_setting.style_guideline
    }
    
    # 質問を生成
    questions = question_generator_service.generate_questions_for_missing_info(story_setting_dict)
    
    return QuestionResponse(
        questions=questions,
        story_setting_id=story_setting_id,
        message=f"物語設定を完成させるために{len(questions)}つの質問があります"
    )

@router.post("/story_settings/{story_setting_id}/answers", response_model=AnswerResponse)
async def submit_answer(
    story_setting_id: int,
    answer_request: AnswerRequest,
    db: Session = Depends(get_db)
):
    """ユーザーの回答を受け取って物語設定を更新するエンドポイント"""
    
    # 物語設定を取得
    story_setting = db.query(StorySetting).filter(
        StorySetting.id == story_setting_id
    ).first()
    
    if not story_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"物語設定ID {story_setting_id} が見つかりません"
        )
    
    try:
        # 回答に応じて物語設定を更新
        field = answer_request.field
        answer = answer_request.answer
        
        if field == "protagonist_name":
            story_setting.protagonist_name = answer
        elif field == "setting_place":
            story_setting.setting_place = answer
        elif field == "tone":
            story_setting.tone = answer
        elif field == "target_age":
            story_setting.target_age = answer
        elif field == "reading_level":
            story_setting.reading_level = answer
        
        db.commit()
        db.refresh(story_setting)
        
        return AnswerResponse(
            story_setting_id=story_setting_id,
            field=field,
            answer=answer,
            message=f"{field}が正常に更新されました"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"回答の保存に失敗しました: {str(e)}"
        )

@router.get("/story_settings/{story_setting_id}/status", response_model=dict)
async def get_story_setting_completion_status(
    story_setting_id: int,
    db: Session = Depends(get_db)
):
    """物語設定の完成度を確認するエンドポイント"""
    
    # 物語設定を取得
    story_setting = db.query(StorySetting).filter(
        StorySetting.id == story_setting_id
    ).first()
    
    if not story_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"物語設定ID {story_setting_id} が見つかりません"
        )
    
    # 完成度を計算
    required_fields = [
        "protagonist_name",
        "setting_place", 
        "tone",
        "target_age"
    ]
    
    completed_fields = []
    missing_fields = []
    
    for field in required_fields:
        value = getattr(story_setting, field)
        if value:
            completed_fields.append(field)
        else:
            missing_fields.append(field)
    
    completion_percentage = (len(completed_fields) / len(required_fields)) * 100
    
    return {
        "story_setting_id": story_setting_id,
        "completion_percentage": completion_percentage,
        "completed_fields": completed_fields,
        "missing_fields": missing_fields,
        "is_complete": len(missing_fields) == 0,
        "message": f"物語設定は{completion_percentage:.0f}%完成しています"
    }
