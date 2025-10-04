from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.supabase_session import get_supabase_db
from app.models.story.supabase_story_setting import SupabaseStorySetting
from app.models.images.supabase_images import SupabaseUploadImages
from app.service.story_generator_service import story_generator_service
import json

router = APIRouter(prefix="/story", tags=["story"])

@router.post("/story_settings/{upload_image_id}", response_model=dict)
async def create_supabase_story_setting_from_image(
    upload_image_id: int,
    db: Session = Depends(get_supabase_db)
):
    """Supabase用の画像IDを指定して、meta_dataの解析結果から物語設定を作成または更新するエンドポイント"""

    # 画像レコードを取得
    upload_image = db.query(SupabaseUploadImages).filter(
        SupabaseUploadImages.id == upload_image_id
    ).first()
    
    # 画像レコードが存在しない場合はエラー
    if not upload_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"画像ID {upload_image_id} が見つかりません"
        )

    # meta_dataが存在しない場合はエラー
    if not upload_image.meta_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"画像ID {upload_image_id} のmeta_dataが見つかりません"
        )
    
    try:
        action = "作成"  # デフォルト値（例外時のスコープエラー回避）
        # meta_dataをパース
        meta_data_json = json.loads(upload_image.meta_data)

        # エラーがある場合はスキップ
        if meta_data_json.get("error"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"画像解析にエラーがあります: {meta_data_json.get('error')}"
            )
        
        # 物語設定を自動生成（app/service/story_generator_service.py）
        story_setting_data = story_generator_service.generate_story_setting_from_analysis(
            meta_data_json, 
            upload_image_id
        )
        
        # 既存の物語設定をチェック
        existing_story_setting = db.query(SupabaseStorySetting).filter(
            SupabaseStorySetting.upload_image_id == upload_image_id
        ).first()
        
        if existing_story_setting:
            # 既存のレコードを更新
            existing_story_setting.title_suggestion = story_setting_data.get("title_suggestion")
            existing_story_setting.protagonist_type = story_setting_data.get("protagonist_type")
            existing_story_setting.setting_place = story_setting_data.get("setting_place")
            existing_story_setting.tone = story_setting_data.get("tone")
            existing_story_setting.target_age = story_setting_data.get("target_age")
            existing_story_setting.language = story_setting_data.get("language")
            existing_story_setting.reading_level = story_setting_data.get("reading_level")
            existing_story_setting.style_guideline = story_setting_data.get("style_guideline")
            
            # protagonist_nameは既に設定されている場合は保持
            if not existing_story_setting.protagonist_name:
                existing_story_setting.protagonist_name = story_setting_data.get("protagonist_name")
            
            db.commit()
            db.refresh(existing_story_setting)
            
            action = "更新"
            story_setting_id = existing_story_setting.id
            
        else:
            # 新しいレコードを作成
            new_story_setting = SupabaseStorySetting(
                upload_image_id=upload_image_id,
                title_suggestion=story_setting_data.get("title_suggestion"),
                protagonist_name=story_setting_data.get("protagonist_name"),
                protagonist_type=story_setting_data.get("protagonist_type"),
                setting_place=story_setting_data.get("setting_place"),
                tone=story_setting_data.get("tone"),
                target_age=story_setting_data.get("target_age"),
                language=story_setting_data.get("language"),
                reading_level=story_setting_data.get("reading_level"),
                style_guideline=story_setting_data.get("style_guideline")
            )
            
            db.add(new_story_setting)
            db.commit()
            db.refresh(new_story_setting)
            
            action = "作成"
            story_setting_id = new_story_setting.id

        return {
            "message": f"物語設定が{action}されました",
            "action": action,
            "story_setting_id": story_setting_id,
            "upload_image_id": upload_image_id,
            "generated_data": story_setting_data
        }

    # JSONデコードエラーが発生した場合はエラーを返す
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="meta_dataの解析に失敗しました"
        )
    
    # エラーが発生した場合はエラーを返す
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"物語設定の{action}に失敗しました: {str(e)}"
        )

# 物語設定一覧取得エンドポイント（Supabase用）
@router.get("/story_settings", response_model=list[dict])
def get_supabase_story_settings(db: Session = Depends(get_supabase_db)):
    """Supabase用の物語設定一覧取得エンドポイント"""
    
    story_settings = db.query(SupabaseStorySetting).all()
    return [
        {
            "id": setting.id,
            "upload_image_id": setting.upload_image_id,
            "title_suggestion": setting.title_suggestion,
            "protagonist_name": setting.protagonist_name,
            "protagonist_type": setting.protagonist_type,
            "setting_place": setting.setting_place,
            "tone": setting.tone,
            "target_age": setting.target_age,
            "language": setting.language,
            "reading_level": setting.reading_level,
            "style_guideline": setting.style_guideline,
            "created_at": setting.created_at.isoformat(),
            "updated_at": setting.updated_at.isoformat()
        }
        for setting in story_settings
    ]

# 物語設定詳細取得エンドポイント（Supabase用）
@router.get("/story_settings/{story_setting_id}", response_model=dict)
def get_supabase_story_setting(story_setting_id: int, db: Session = Depends(get_supabase_db)):
    """Supabase用の物語設定詳細取得エンドポイント"""
    
    story_setting = db.query(SupabaseStorySetting).filter(
        SupabaseStorySetting.id == story_setting_id
    ).first()
    
    if not story_setting:
        raise HTTPException(status_code=404, detail="物語設定が見つかりません")
    
    return {
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
        "style_guideline": story_setting.style_guideline,
        "created_at": story_setting.created_at.isoformat(),
        "updated_at": story_setting.updated_at.isoformat()
    }

# 物語設定削除エンドポイント（Supabase用）
@router.delete("/story_settings/{story_setting_id}")
def delete_supabase_story_setting(story_setting_id: int, db: Session = Depends(get_supabase_db)):
    """Supabase用の物語設定削除エンドポイント"""
    
    story_setting = db.query(SupabaseStorySetting).filter(
        SupabaseStorySetting.id == story_setting_id
    ).first()
    
    if not story_setting:
        raise HTTPException(status_code=404, detail="物語設定が見つかりません")
    
    db.delete(story_setting)
    db.commit()
    
    return {"message": "物語設定が削除されました"}
