# テーマ生成用のプロンプトテンプレート

from app.core.prompt.constants import (
    TONE_DESCRIPTIONS,
    AGE_DESCRIPTIONS,
    READING_LEVEL_DESCRIPTIONS
)

# 英語版の定数マッピング
TONE_DESCRIPTIONS_EN = {
    "gentle": "gentle and warm",
    "heartwarming": "heartwarming",
    "adventure": "adventurous",
    "brave": "brave and courageous",
    "mystery": "mysterious and exciting",
    "fun": "fun and playful",
    "dreamy": "dreamy and magical",
    "magical": "magical and fantastical"
}

AGE_DESCRIPTIONS_EN = {
    "infant": "for infants (0-2 years)",
    "toddler": "for toddlers (2-3 years)",
    "preschool": "for preschoolers (3-6 years)",
    "early_elementary": "for early elementary (6-8 years)"
}


def generate_theme_prompt(
    protagonist_name: str,
    protagonist_type: str,
    setting_place: str,
    tone: str,
    target_age: str,
    reading_level: str,
    language: str = "ja"
) -> str:
    """テーマ案生成用のプロンプトを作成
    
    Args:
        protagonist_name: 主人公の名前
        protagonist_type: キャラクターの特徴（外見・種族）
        setting_place: 舞台
        tone: 雰囲気の種類
        target_age: 対象年齢
        reading_level: 読みやすさレベル
        language: 出力言語 ("ja" または "en")
        
    Returns:
        プロンプト文字列
    """
    reading_level_desc = READING_LEVEL_DESCRIPTIONS.get(reading_level, reading_level)
    
    # tone（雰囲気）に応じた theme_id の候補を定義
    theme_ids = {"theme1": "adventure", "theme2": "friendship", "theme3": "discovery"}
    
    if tone in ["adventure", "brave"]:
        theme_ids = {
            "theme1": "adventure",
            "theme2": "challenge",
            "theme3": "journey"
        }
    elif tone in ["gentle", "heartwarming"]:
        theme_ids = {
            "theme1": "daily_life",
            "theme2": "kindness",
            "theme3": "friendship"
        }
    elif tone == "mystery":
        theme_ids = {
            "theme1": "mystery",
            "theme2": "detective",
            "theme3": "discovery"
        }
    elif tone == "fun":
        theme_ids = {
            "theme1": "play",
            "theme2": "friendship",
            "theme3": "fun_adventure"
        }
    elif tone in ["dreamy", "magical"]:
        theme_ids = {
            "theme1": "magical",
            "theme2": "fantasy",
            "theme3": "dreamy_journey"
        }
    else:
        # デフォルト（未定義のtone用）
        theme_ids = {
            "theme1": "adventure",
            "theme2": "friendship",
            "theme3": "discovery"
        }
    
    # 言語に応じたプロンプトを生成
    if language == "en":
        prompt = _generate_theme_prompt_en(
            protagonist_name, protagonist_type, setting_place,
            tone, target_age, reading_level_desc, theme_ids
        )
    else:
        prompt = _generate_theme_prompt_ja(
            protagonist_name, protagonist_type, setting_place,
            tone, target_age, reading_level_desc, theme_ids
        )
    
    return prompt


def _generate_theme_prompt_ja(
    protagonist_name: str,
    protagonist_type: str,
    setting_place: str,
    tone: str,
    target_age: str,
    reading_level_desc: str,
    theme_ids: dict
) -> str:
    """日本語版テーマ生成プロンプト"""
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
以下の theme_id を使用して、それぞれ異なるバリエーションのテーマを作成してください：

1. variation_type: "classic" / theme_id: "{theme_ids['theme1']}"
   - 雰囲気を王道に味わえる直球展開
2. variation_type: "character_driven" / theme_id: "{theme_ids['theme2']}"
   - "{protagonist_type}" でないと成立しない個性的な展開
3. variation_type: "unique_twist" / theme_id: "{theme_ids['theme3']}"
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
      "theme_id": "{theme_ids['theme1']}",
      "title": "タイトル",
      "description": "物語の概要（2-3文）",
      "keywords": ["キーワード1", "キーワード2", "キーワード3"]
    }},
    "theme2": {{
      "theme_id": "{theme_ids['theme2']}",
      "title": "タイトル",
      "description": "物語の概要（2-3文）",
      "keywords": ["キーワード1", "キーワード2", "キーワード3"]
    }},
    "theme3": {{
      "theme_id": "{theme_ids['theme3']}",
      "title": "タイトル",
      "description": "物語の概要（2-3文）",
      "keywords": ["キーワード1", "キーワード2", "キーワード3"]
    }}
  }}
}}

必ずJSON形式で出力し、他の説明文は含めないでください。
"""
    return prompt


def _generate_theme_prompt_en(
    protagonist_name: str,
    protagonist_type: str,
    setting_place: str,
    tone: str,
    target_age: str,
    reading_level_desc: str,
    theme_ids: dict
) -> str:
    """英語版テーマ生成プロンプト"""
    tone_en = TONE_DESCRIPTIONS_EN.get(tone, "gentle and warm")
    age_en = AGE_DESCRIPTIONS_EN.get(target_age, "for preschoolers (3-6 years)")
    
    prompt = f"""
You are a professional picture book author who sparks children's imagination.
Based on the "{tone_en}" mood the user selected, 
please suggest 3 exciting story themes for children.

【Basic Settings】
- Protagonist: {protagonist_name}
- Character traits: {protagonist_type}
  ※This trait must be used as a key element in the story development
- Setting: {setting_place}
- Mood: {tone_en}
- Target age: {age_en}

【3 Themes to Create】
Create three different theme variations using the following theme_ids:

1. variation_type: "classic" / theme_id: "{theme_ids['theme1']}"
   - A straightforward story that captures the mood perfectly
2. variation_type: "character_driven" / theme_id: "{theme_ids['theme2']}"
   - A unique story that only works because of "{protagonist_type}"
3. variation_type: "unique_twist" / theme_id: "{theme_ids['theme3']}"
   - A story with an unexpected or whimsical twist

【Requirements】
- Use simple, clear language appropriate for young children
- Include one educational element while prioritizing fun
- Stay true to the selected mood
- Keep titles short (under 6 words) and easy to understand
- Write all story content in English

【Output Format】
Output in the following JSON format:
{{
  "theme_options": {{
    "theme1": {{
      "theme_id": "{theme_ids['theme1']}",
      "title": "Title",
      "description": "Story summary (2-3 sentences)",
      "keywords": ["keyword1", "keyword2", "keyword3"]
    }},
    "theme2": {{
      "theme_id": "{theme_ids['theme2']}",
      "title": "Title",
      "description": "Story summary (2-3 sentences)",  
      "keywords": ["keyword1", "keyword2", "keyword3"]
    }},
    "theme3": {{
      "theme_id": "{theme_ids['theme3']}",
      "title": "Title",
      "description": "Story summary (2-3 sentences)",
      "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
  }}
}}

Output only valid JSON, no additional text.
"""
    return prompt
