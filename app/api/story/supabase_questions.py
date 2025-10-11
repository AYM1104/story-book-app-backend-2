from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.supabase_session import get_supabase_db
from app.models.story.supabase_story_setting import SupabaseStorySetting
from app.service.question_generator_service import question_generator_service
from app.schemas.story.question import QuestionResponse, AnswerRequest, AnswerResponse
import time

router = APIRouter(prefix="/story", tags=["story-questions"])

@router.get("/story_settings/{story_setting_id}/questions", response_model=QuestionResponse)
async def get_supabase_questions_for_story_setting(
    story_setting_id: int,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用の物語設定の不足情報に対して質問を生成するエンドポイント"""
    
    # 処理時間計測開始
    start_time = time.time()
    print(f"=== 質問取得処理開始 (Supabase) ===")
    print(f"Story Setting ID: {story_setting_id}")
    
    # 物語設定を取得
    db_start = time.time()
    story_setting = db.query(SupabaseStorySetting).filter(
        SupabaseStorySetting.id == story_setting_id
    ).first()
    db_fetch_time = time.time() - db_start
    print(f"⏱️ DB取得時間: {db_fetch_time:.3f}秒")
    
    if not story_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"物語設定ID {story_setting_id} が見つかりません"
        )
    
    # 物語設定を辞書形式に変換
    convert_start = time.time()
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
    convert_time = time.time() - convert_start
    print(f"⏱️ データ変換時間: {convert_time:.3f}秒")
    
    # 質問を生成
    question_start = time.time()
    questions = question_generator_service.generate_questions_for_missing_info(story_setting_dict)
    question_time = time.time() - question_start
    print(f"⏱️ 質問生成時間: {question_time:.3f}秒")
    
    # 全体の処理時間
    total_time = time.time() - start_time
    print(f"⏱️ 質問取得処理の合計時間: {total_time:.3f}秒")
    print(f"=== 質問取得処理完了 ===")
    
    return QuestionResponse(
        questions=questions,
        story_setting_id=story_setting_id,
        message=f"物語設定を完成させるために{len(questions)}つの質問があります"
    )

@router.post("/story_settings/{story_setting_id}/answers", response_model=AnswerResponse)
async def submit_supabase_answer(
    story_setting_id: int,
    answer_request: AnswerRequest,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用のユーザーの回答を受け取って物語設定を更新するエンドポイント"""
    
    # 処理時間計測開始
    start_time = time.time()
    print(f"=== 質問回答処理開始 (Supabase) ===")
    print(f"Story Setting ID: {story_setting_id}")
    print(f"Field: {answer_request.field}, Answer: {answer_request.answer}")
    
    # 物語設定を取得
    db_start = time.time()
    story_setting = db.query(SupabaseStorySetting).filter(
        SupabaseStorySetting.id == story_setting_id
    ).first()
    db_fetch_time = time.time() - db_start
    print(f"⏱️ DB取得時間: {db_fetch_time:.3f}秒")
    
    if not story_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"物語設定ID {story_setting_id} が見つかりません"
        )
    
    try:
        # 回答に応じて物語設定を更新
        update_start = time.time()
        field = answer_request.field
        answer = answer_request.answer
        
        if field == "protagonist_name":
            story_setting.protagonist_name = answer
        elif field == "protagonist_type":
            story_setting.protagonist_type = answer
        elif field == "setting_place":
            story_setting.setting_place = answer
        elif field == "tone":
            story_setting.tone = answer
        elif field == "target_age":
            story_setting.target_age = answer
        elif field == "reading_level":
            story_setting.reading_level = answer
        
        update_time = time.time() - update_start
        print(f"⏱️ データ更新時間: {update_time:.3f}秒")
        
        # データベースに保存
        commit_start = time.time()
        db.commit()
        db.refresh(story_setting)
        commit_time = time.time() - commit_start
        print(f"⏱️ DB保存時間: {commit_time:.3f}秒")
        
        # 全体の処理時間
        total_time = time.time() - start_time
        print(f"⏱️ 質問回答処理の合計時間: {total_time:.3f}秒")
        print(f"=== 質問回答処理完了 ===")
        
        return AnswerResponse(
            story_setting_id=story_setting_id,
            field=field,
            answer=answer,
            message=f"{field}が正常に更新されました"
        )
        
    except Exception as e:
        db.rollback()
        error_time = time.time() - start_time
        print(f"❌ 質問回答処理エラー（処理時間: {error_time:.3f}秒）: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"回答の保存に失敗しました: {str(e)}"
        )

@router.get("/story_settings/{story_setting_id}/status", response_model=dict)
async def get_supabase_story_setting_completion_status(
    story_setting_id: int,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用の物語設定の完成度を確認するエンドポイント"""
    
    # 物語設定を取得
    story_setting = db.query(SupabaseStorySetting).filter(
        SupabaseStorySetting.id == story_setting_id
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

# 質問履歴一覧取得エンドポイント（Supabase用）
@router.get("/story_settings/{story_setting_id}/question-history", response_model=list[dict])
def get_supabase_question_history(
    story_setting_id: int,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用の質問履歴一覧取得エンドポイント"""
    
    # 物語設定を取得
    story_setting = db.query(SupabaseStorySetting).filter(
        SupabaseStorySetting.id == story_setting_id
    ).first()
    
    if not story_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"物語設定ID {story_setting_id} が見つかりません"
        )
    
    # 現在の設定から回答済みフィールドを抽出
    answered_fields = []
    required_fields = ["protagonist_name", "setting_place", "tone", "target_age", "reading_level"]
    
    for field in required_fields:
        value = getattr(story_setting, field)
        if value:
            answered_fields.append({
                "field": field,
                "answer": value,
                "answered_at": story_setting.updated_at.isoformat()
            })
    
    return answered_fields
