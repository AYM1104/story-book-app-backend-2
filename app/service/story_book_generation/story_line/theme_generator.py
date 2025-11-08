# story_book_generation/story_line/theme_generator.py
# 絵本のテーマ案を生成するサービス

import json
import google.generativeai as genai
from typing import Dict, Any
import os
import time
from dotenv import load_dotenv
from google.api_core import exceptions as google_exceptions

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
        
        # APIキーの確認（最初の8文字のみ表示）
        api_key_preview = api_key[:8] + "..." if len(api_key) > 8 else api_key
        print(f"🔑 Gemini APIキー確認: {api_key_preview} (長さ: {len(api_key)})")
        
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

        # プロンプト全文をターミナルに表示
        print("=" * 80)
        print("【Gemini API プロンプト全文 - テーマ案生成】")
        print("=" * 80)
        print(prompt)
        print("=" * 80)
        
        # Gemini 2.5 Flashでテーマ案のみを生成（リトライロジック付き）
        max_retries = 3
        retry_delay = 2.0  # 秒
        timeout_seconds = 180.0  # 3分（180秒）
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Gemini API呼び出し試行 {attempt + 1}/{max_retries}（タイムアウト: {timeout_seconds}秒）")
                response = self.model.generate_content(
                    prompt,
                    request_options={"timeout": timeout_seconds}
                )
                print(f"✅ Gemini API レスポンス受信成功")
                print(f"レスポンステキスト（最初の500文字）: {response.text[:500]}")
                
                theme_data = self._parse_theme_options_response(response.text)
                print(f"✅ JSON解析成功")
                return theme_data
                
            except google_exceptions.ServiceUnavailable as e:
                # 503エラーの場合
                error_str = str(e)
                print(f"❌ Gemini API呼び出しエラー（503 Service Unavailable）（試行 {attempt + 1}/{max_retries}）: {error_str}")
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)  # 指数バックオフ
                    print(f"⏳ {wait_time}秒待機してリトライします...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ 最大リトライ回数に達しました")
                    raise Exception(f"Gemini API呼び出しが{max_retries}回失敗しました（503エラー）。最後のエラー: {error_str}")
                    
            except google_exceptions.DeadlineExceeded as e:
                # タイムアウトエラーの場合
                error_str = str(e)
                print(f"❌ Gemini API呼び出しエラー（タイムアウト）（試行 {attempt + 1}/{max_retries}）: {error_str}")
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    print(f"⏳ {wait_time}秒待機してリトライします...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ 最大リトライ回数に達しました")
                    raise Exception(f"Gemini API呼び出しが{max_retries}回失敗しました（タイムアウト）。最後のエラー: {error_str}")
                    
            except Exception as e:
                error_str = str(e)
                print(f"❌ Gemini API呼び出しエラー（試行 {attempt + 1}/{max_retries}）: {error_str}")
                
                # "503"や"Illegal metadata"を含むエラーの場合はリトライ
                if "503" in error_str or "Illegal metadata" in error_str or "timeout" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)  # 指数バックオフ
                        print(f"⏳ {wait_time}秒待機してリトライします...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ 最大リトライ回数に達しました")
                        raise Exception(f"Gemini API呼び出しが{max_retries}回失敗しました。最後のエラー: {error_str}")
                else:
                    # その他のエラーは即座に再スロー
                    raise

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
                print(f"📝 JSONコードブロックを検出（```json形式）")
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.rfind("```")
                json_text = response_text[json_start:json_end].strip()
                print(f"📝 コードブロックを検出（```形式）")
            else:
                json_text = response_text.strip()
                print(f"📝 プレーンテキストとして処理")

            print(f"抽出されたJSONテキスト（最初の500文字）: {json_text[:500]}")
            theme_data = json.loads(json_text)
            print(f"✅ JSON解析成功: theme_optionsのキー = {list(theme_data.get('theme_options', {}).keys())}")
            return theme_data

        except json.JSONDecodeError as e:
            print(f"❌ JSON解析エラー: {e}")
            print(f"エラー位置: 行 {e.lineno if hasattr(e, 'lineno') else '不明'}, 列 {e.colno if hasattr(e, 'colno') else '不明'}")
            print(f"レスポンステキスト（全文）: {response_text}")
            print(f"抽出されたJSONテキスト（全文）: {json_text if 'json_text' in locals() else '抽出失敗'}")
            raise ValueError("Geminiからのレスポンスが正しいJSON形式ではありません")


# シングルトンインスタンス
theme_generator = ThemeGenerator()

