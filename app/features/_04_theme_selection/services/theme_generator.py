# story_book_generation/story_line/theme_generator.py
# 絵本のテーマ案を生成するサービス

import json
import google.generativeai as genai
from typing import Dict, Any
import os
import time
import traceback
from dotenv import load_dotenv
from google.api_core import exceptions as google_exceptions

# ローカル環境では.envファイルを読み込む（Cloud Runでは環境変数が直接設定されるため不要）
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
        # Gemini APIの設定（物語生成用のFree APIキーを使用、なければPaid APIキーを使用）
        # Cloud Run環境では環境変数が直接設定されているため、os.getenv()で取得可能
        api_key = os.getenv("GOOGLE_API_KEY_Free") or os.getenv("GOOGLE_API_KEY_Paid")
        if not api_key:
            error_msg = "GOOGLE_API_KEY_FreeまたはGOOGLE_API_KEY_Paidが設定されていません。"
            print(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # 使用しているAPIキーの種類を判定
        api_key_type = "GOOGLE_API_KEY_Free" if os.getenv("GOOGLE_API_KEY_Free") else "GOOGLE_API_KEY_Paid"
        
        # APIキーのクリーンアップ（改行、スペース、引用符を削除）
        api_key = api_key.strip().strip('"').strip("'")
        
        # APIキーの形式検証
        if not api_key.startswith("AIza"):
            print(f"⚠️ 警告: APIキーの形式が正しくない可能性があります（AIzaで始まる必要があります）")
        
        # APIキーの確認（最初の8文字のみ表示）
        api_key_preview = api_key[:8] + "..." if len(api_key) > 8 else api_key
        print(f"🔑 Gemini APIキー確認: {api_key_type} を使用 - {api_key_preview} (長さ: {len(api_key)})")
        
        # APIキーが空でないことを再確認
        if not api_key or len(api_key) < 20:
            error_msg = f"APIキーが無効です（長さ: {len(api_key)}文字）。APIキーは通常39文字以上です。"
            print(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except Exception as e:
            error_msg = f"Gemini APIの初期化に失敗しました: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"エラーの詳細: {traceback.format_exc()}")
            raise ValueError(error_msg) from e

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
                # Cloud Run環境でもタイムアウトを設定
                # google.generativeaiのgenerate_contentはtimeoutパラメータを直接サポートしていないため、
                # リトライロジックでタイムアウトを処理
                response = self.model.generate_content(prompt)
                
                # レスポンスの検証
                if response is None:
                    raise ValueError("Gemini APIからのレスポンスがNoneです")
                
                # response.textがNoneの場合の処理
                if not hasattr(response, 'text') or response.text is None:
                    # エラーメッセージを確認
                    error_msg = "レスポンステキストが取得できませんでした"
                    if hasattr(response, 'prompt_feedback'):
                        error_msg += f" (prompt_feedback: {response.prompt_feedback})"
                    if hasattr(response, 'candidates') and response.candidates:
                        if hasattr(response.candidates[0], 'finish_reason'):
                            error_msg += f" (finish_reason: {response.candidates[0].finish_reason})"
                    print(f"❌ {error_msg}")
                    raise ValueError(error_msg)
                
                print(f"✅ Gemini API レスポンス受信成功")
                response_text = response.text
                print(f"レスポンステキスト（最初の500文字）: {response_text[:500] if len(response_text) > 500 else response_text}")
                
                theme_data = self._parse_theme_options_response(response_text)
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
                    
            except ValueError as e:
                # レスポンス検証エラーの場合
                error_str = str(e)
                print(f"❌ レスポンス検証エラー（試行 {attempt + 1}/{max_retries}）: {error_str}")
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    print(f"⏳ {wait_time}秒待機してリトライします...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ 最大リトライ回数に達しました")
                    raise Exception(f"Gemini API呼び出しが{max_retries}回失敗しました（レスポンス検証エラー）。最後のエラー: {error_str}")
                    
            except Exception as e:
                error_str = str(e)
                error_type = type(e).__name__
                print(f"❌ Gemini API呼び出しエラー（試行 {attempt + 1}/{max_retries}）: [{error_type}] {error_str}")
                
                # 詳細なエラー情報を出力（Cloud Runでのデバッグ用）
                print(f"エラーのトレースバック: {traceback.format_exc()}")
                
                # "503"や"Illegal metadata"を含むエラーの場合はリトライ
                retryable_errors = [
                    "503", "Illegal metadata", "timeout", "deadline", 
                    "service unavailable", "internal error", "unavailable"
                ]
                should_retry = any(keyword in error_str.lower() for keyword in retryable_errors)
                
                if should_retry:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)  # 指数バックオフ
                        print(f"⏳ {wait_time}秒待機してリトライします...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ 最大リトライ回数に達しました")
                        raise Exception(f"Gemini API呼び出しが{max_retries}回失敗しました。最後のエラー: [{error_type}] {error_str}")
                else:
                    # その他のエラーは即座に再スロー
                    raise

    def _create_theme_options_prompt(self, protagonist_name: str, protagonist_type: str, 
                                    setting_place: str, tone: str, target_age: str, reading_level: str) -> str:
        """テーマ案のみ生成用のプロンプトを作成（物語本文は生成しない）"""
        
        # 共通定数を使用
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

    def _parse_theme_options_response(self, response_text: str) -> Dict[str, Any]:
        """テーマ案のみのレスポンスをパース"""
        if not response_text or not response_text.strip():
            raise ValueError("レスポンステキストが空です")
        
        try:
            # JSON部分を抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end == -1:
                    json_end = len(response_text)
                json_text = response_text[json_start:json_end].strip()
                print(f"📝 JSONコードブロックを検出（```json形式）")
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.rfind("```")
                if json_end == -1 or json_end <= json_start:
                    json_end = len(response_text)
                json_text = response_text[json_start:json_end].strip()
                print(f"📝 コードブロックを検出（```形式）")
            else:
                json_text = response_text.strip()
                print(f"📝 プレーンテキストとして処理")

            if not json_text:
                raise ValueError("JSONテキストが抽出できませんでした")

            print(f"抽出されたJSONテキスト（最初の500文字）: {json_text[:500] if len(json_text) > 500 else json_text}")
            theme_data = json.loads(json_text)
            
            # データ構造の検証
            if not isinstance(theme_data, dict):
                raise ValueError(f"JSONのルートが辞書型ではありません: {type(theme_data)}")
            if "theme_options" not in theme_data:
                raise ValueError("JSONに'theme_options'キーがありません")
            
            print(f"✅ JSON解析成功: theme_optionsのキー = {list(theme_data.get('theme_options', {}).keys())}")
            return theme_data

        except json.JSONDecodeError as e:
            print(f"❌ JSON解析エラー: {e}")
            print(f"エラー位置: 行 {e.lineno if hasattr(e, 'lineno') else '不明'}, 列 {e.colno if hasattr(e, 'colno') else '不明'}")
            print(f"レスポンステキスト（全文）: {response_text}")
            print(f"抽出されたJSONテキスト（全文）: {json_text if 'json_text' in locals() else '抽出失敗'}")
            raise ValueError(f"Geminiからのレスポンスが正しいJSON形式ではありません: {str(e)}")
        except Exception as e:
            print(f"❌ 予期しないエラー: {type(e).__name__}: {str(e)}")
            print(f"レスポンステキスト（全文）: {response_text}")
            raise


# シングルトンインスタンス（遅延初期化）
_theme_generator_instance = None

def get_theme_generator() -> ThemeGenerator:
    """ThemeGeneratorのシングルトンインスタンスを取得（遅延初期化）"""
    global _theme_generator_instance
    if _theme_generator_instance is None:
        _theme_generator_instance = ThemeGenerator()
    return _theme_generator_instance

class ThemeGeneratorProxy:
    """ThemeGeneratorのプロキシクラス（遅延初期化用）"""
    def __getattr__(self, name):
        return getattr(get_theme_generator(), name)

# 後方互換性のため、theme_generatorとしてプロキシオブジェクトを提供
theme_generator = ThemeGeneratorProxy()

