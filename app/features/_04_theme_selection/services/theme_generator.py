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
from app.core.gemini_config import initialize_gemini_model_2_5_flash
from app.features._02_generate_theme.prompt.generate_theme_prompt import generate_theme_prompt
from app.core.prompt.constants import (
    TONE_DESCRIPTIONS,
    AGE_DESCRIPTIONS,
    READING_LEVEL_DESCRIPTIONS
)

# ローカル環境では.envファイルを読み込む（Cloud Runでは環境変数が直接設定されるため不要）
load_dotenv()

class ThemeGenerator:
    """Gemini 2.5 Flashを使用してテーマ案を生成するサービス"""

    def __init__(self):
        # Gemini APIの設定（共通のユーティリティ関数を使用）
        self.model = initialize_gemini_model_2_5_flash('gemini-2.5-flash')

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
        # print("================================================")
        # print("【Gemini API プロンプト全文 - テーマ案生成】")
        # print("================================================")
        # print(prompt)
        
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
                print()  # 改行を追加

                response_text = response.text
                print(f"レスポンステキスト（全文）:")
                print(response_text)
                print()  # 改行を追加

                theme_data = self._parse_theme_options_response(response_text)
                print(f"✅ JSON解析成功")
                print()  # 改行を追加
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
        """テーマ案生成用のプロンプトを作成（プロンプトファイルから読み込み）"""
        return generate_theme_prompt(
            protagonist_name, protagonist_type, setting_place, tone, target_age, reading_level
        )

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
                # print(f"📝 JSONコードブロックを検出（```json形式）")
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.rfind("```")
                if json_end == -1 or json_end <= json_start:
                    json_end = len(response_text)
                json_text = response_text[json_start:json_end].strip()
                # print(f"📝 コードブロックを検出（```形式）")
            else:
                json_text = response_text.strip()
                # print(f"📝 プレーンテキストとして処理")

            if not json_text:
                raise ValueError("JSONテキストが抽出できませんでした")

            # print(f"抽出されたJSONテキスト（全文）:")
            # print(json_text)
            theme_data = json.loads(json_text)
            
            # データ構造の検証
            if not isinstance(theme_data, dict):
                raise ValueError(f"JSONのルートが辞書型ではありません: {type(theme_data)}")
            if "theme_options" not in theme_data:
                raise ValueError("JSONに'theme_options'キーがありません")
            
            print(f"✅ JSON解析完了: theme_optionsのキー = {list(theme_data.get('theme_options', {}).keys())}")
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

