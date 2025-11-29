# テーマ生成用のプロンプトテンプレート

from app.core.prompt.constants import (
    TONE_DESCRIPTIONS,
    AGE_DESCRIPTIONS,
    READING_LEVEL_DESCRIPTIONS
)


def create_theme_options_prompt(
    protagonist_name: str,
    protagonist_type: str,
    setting_place: str,
    tone: str,
    target_age: str,
    reading_level: str
) -> str:
    """テーマ案生成用のプロンプトを作成
    
    Args:
        protagonist_name: 主人公の名前
        protagonist_type: キャラクターの特徴（外見・種族）
        setting_place: 舞台
        tone: 雰囲気の種類
        target_age: 対象年齢
        reading_level: 読みやすさレベル
        
    Returns:
        プロンプト文字列
    """
    reading_level_desc = READING_LEVEL_DESCRIPTIONS.get(reading_level, reading_level)
    
    prompt = f"""
あなたは、子供の想像力をかき立てるプロの絵本作家です。
ユーザーが選んだ「{TONE_DESCRIPTIONS.get(tone)}」という雰囲気に合わせて、
子供がワクワクする3種類の物語テーマを提案してください。

【基本設定】
- 主人公: {protagonist_name}
- キャラクターの特徴（外見・種族）: {protagonist_type}
  ※この特徴は物語の展開や解決の鍵として必ず活用すること
- 舞台: {setting_place}
- 雰囲気: {TONE_DESCRIPTIONS.get(tone)}
- 対象年齢: {AGE_DESCRIPTIONS.get(target_age, '3-6歳の未就学児向け')}
- 読みやすさ: {reading_level_desc}

【作成する3つのテーマ】
1. variation_type: "classic" / theme_id: "adventure"
   - 雰囲気を王道に味わえる直球展開
2. variation_type: "character_driven" / theme_id: "friendship"
   - "{protagonist_type}" でないと成立しない個性的な展開
3. variation_type: "unique_twist" / theme_id: "discovery"
   - ちょっと不思議で意外性のある展開

【制約事項】
- わかりやすい起承転結を意識し、難しい言い回しを避ける
- 教育的な学びをひとつ含めつつ、エンタメ性を最優先
- 選択した雰囲気から逸脱しない
- タイトルとキャッチコピーはひらがな中心、15文字以内

【出力形式】
以下のJSON形式で出力してください：
{{
  "theme_options": {{
    "theme1": {{
      "theme_id": "adventure",
      "title": "タイトル",
      "description": "物語の概要（2-3文）",
      "keywords": ["キーワード1", "キーワード2", "キーワード3"]
    }},
    "theme2": {{
      "theme_id": "friendship",
      "title": "タイトル",
      "description": "物語の概要（2-3文）",
      "keywords": ["キーワード1", "キーワード2", "キーワード3"]
    }},
    "theme3": {{
      "theme_id": "discovery",
      "title": "タイトル",
      "description": "物語の概要（2-3文）",
      "keywords": ["キーワード1", "キーワード2", "キーワード3"]
    }}
  }}
}}

必ずJSON形式で出力し、他の説明文は含めないでください。
"""
    
    return prompt

