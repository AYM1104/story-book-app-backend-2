# story_book_generation/story_line/theme_generator.py
# 絵本のテーマ案を生成するサービス

import json
import google.generativeai as genai
from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# 共通の定数定義（story_line_generator.pyでも使用）
TONE_DESCRIPTIONS = {
    "gentle": "優しく温かい雰囲気",
    "fun": "楽しく明るい雰囲気",
    "adventure": "冒険的でワクワクする雰囲気",
    "mystery": "謎解きでドキドキする雰囲気",
    "heartwarming": "感動的で心が温まる雰囲気",
    "dreamy": "幻想的で夢のような雰囲気",
    "magical": "魔法のように不思議な雰囲気",
    "brave": "勇気をもって挑戦する雰囲気"
}

AGE_DESCRIPTIONS = {
    "preschool": "3-6歳の未就学児向け",
    "elementary_low": "7-9歳の小学生低学年向け"
}

READING_LEVEL_DESCRIPTIONS = {
    "hiragana_only": "ひらがなのみを使用",
    "hiragana_katakana": "ひらがなとカタカナを使用",
    "basic_kanji": "基本的な漢字も含む",
    "normal": "普通のレベル"
}

class ThemeGenerator:
    """Gemini 2.5 Flashを使用してテーマ案を生成するサービス"""

    def __init__(self):
        # Gemini APIの設定（物語生成用のFree APIキーを使用）
        api_key = os.getenv("GOOGLE_API_KEY_Free") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY_Free、GEMINI_API_KEYまたはGOOGLE_API_KEYが設定されていません")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def generate_theme_options_only(self, story_setting: Dict[str, Any]) -> Dict[str, Any]:
        """3つのテーマ案のみを生成する関数"""
        
        protagonist_name = story_setting.get("protagonist_name", "主人公")
        protagonist_type = story_setting.get("protagonist_type", "子供")
        setting_place = story_setting.get("setting_place", "公園")
        tone = story_setting.get("tone", "gentle")
        target_age = story_setting.get("target_age", "preschool")
        reading_level = story_setting.get("reading_level", "hiragana_only")

        # プロンプトを作成
        prompt = self._create_theme_options_prompt(
            protagonist_name, protagonist_type, setting_place, 
            tone, target_age, reading_level
        )

        try:
            # プロンプト全文をターミナルに表示
            print("=" * 80)
            print("【Gemini API プロンプト全文 - テーマ案生成】")
            print("=" * 80)
            print(prompt)
            print("=" * 80)
            
            # Gemini 2.5 Flashでテーマ案のみを生成
            response = self.model.generate_content(prompt)
            theme_data = self._parse_theme_options_response(response.text)
            return theme_data

        except Exception as e:
            print(f"Gemini API エラー: {e}")
            # エラー時はフォールバック
            return self._generate_fallback_theme_options(protagonist_name, protagonist_type, setting_place, tone)

    def _create_theme_options_prompt(self, protagonist_name: str, protagonist_type: str, 
                                    setting_place: str, tone: str, target_age: str, reading_level: str) -> str:
        """テーマ案のみ生成用のプロンプトを作成（物語本文は生成しない）"""
        
        # 共通定数を使用
        reading_level_desc = READING_LEVEL_DESCRIPTIONS.get(reading_level, reading_level)

        prompt = f"""
あなたは子供向けの絵本のストーリー企画者です。
以下の設定を元に、3つの異なるテーマの物語案を提案してください。

【基本設定】
- 主人公: {protagonist_name}（{protagonist_type}）
- 舞台: {setting_place}
- 雰囲気: {TONE_DESCRIPTIONS.get(tone, '優しく温かい雰囲気')}
- 対象年齢: {AGE_DESCRIPTIONS.get(target_age, '3-6歳の未就学児向け')}
- 読みやすさ: {reading_level_desc}

【要求事項】
1. 3つの異なるテーマ（冒険、友情、発見など）
2. 各テーマのタイトル、概要説明、キーワード
3. 子供が楽しめる内容
4. 教育的な要素を含む

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

    def _parse_theme_options_response(self, response_text: str) -> Dict[str, Any]:
        """テーマ案のみのレスポンスをパース"""
        try:
            # JSON部分を抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.rfind("```")
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()

            theme_data = json.loads(json_text)
            return theme_data

        except json.JSONDecodeError as e:
            print(f"JSON解析エラー: {e}")
            print(f"レスポンステキスト: {response_text}")
            raise ValueError("Geminiからのレスポンスが正しいJSON形式ではありません")

    def _generate_fallback_theme_options(self, protagonist_name: str, protagonist_type: str, setting_place: str, tone: str) -> Dict[str, Any]:
        """エラー時のフォールバック用テーマ案のみ"""
        return {
            "theme_options": {
                "theme1": {
                    "theme_id": "adventure",
                    "title": f"{protagonist_name}の冒険",
                    "description": f"{protagonist_name}が{setting_place}で冒険に出かける物語。勇気を出して新しいことに挑戦します。",
                    "keywords": ["冒険", "勇気", "挑戦"]
                },
                "theme2": {
                    "theme_id": "friendship",
                    "title": f"{protagonist_name}の新しい友達",
                    "description": f"{protagonist_name}が{setting_place}で新しい友達と出会う物語。友情の大切さを学びます。",
                    "keywords": ["友情", "優しさ", "協力"]
                },
                "theme3": {
                    "theme_id": "discovery",
                    "title": f"{protagonist_name}の不思議な発見",
                    "description": f"{protagonist_name}が{setting_place}で不思議なものを見つける物語。好奇心を持って探求します。",
                    "keywords": ["発見", "探求", "好奇心"]
                }
            }
        }

# シングルトンインスタンス
theme_generator = ThemeGenerator()

