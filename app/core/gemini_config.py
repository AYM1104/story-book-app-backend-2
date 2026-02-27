"""Gemini API設定とユーティリティ関数"""
import os
import traceback
import google.generativeai as genai
from typing import Tuple, Optional


def get_and_validate_api_key() -> Tuple[str, str]:
    """
    Gemini APIキーを取得し、検証する
    
    Returns:
        Tuple[str, str]: (api_key, api_key_type) のタプル
        
    Raises:
        ValueError: APIキーが設定されていない、または無効な場合
    """
    # APIキーの取得（Free APIキーを優先、なければPaid APIキーを使用）
    api_key = os.getenv("GOOGLE_API_KEY_Free") or os.getenv("GOOGLE_API_KEY_Paid")
    if not api_key:
        error_msg = "GOOGLE_API_KEY_FreeまたはGOOGLE_API_KEY_Paidが設定されていません。"
        print(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    # 使用しているAPIキーの種類を判定
    api_key_type = "GOOGLE_API_KEY_Free" if os.getenv("GOOGLE_API_KEY_Free") else "GOOGLE_API_KEY_Paid"
    print(f"🔑 Gemini APIキー確認: {api_key_type} を使用")
    
    # APIキーのクリーンアップ（改行、スペース、引用符を削除）
    api_key = api_key.strip().strip('"').strip("'")
    
    # APIキーの形式検証
    if not api_key.startswith("AIza"):
        print(f"⚠️ 警告: APIキーの形式が正しくない可能性があります（AIzaで始まる必要があります）")
    
    # APIキーが空でないことを再確認
    if not api_key or len(api_key) < 20:
        error_msg = f"APIキーが無効です（長さ: {len(api_key)}文字）。APIキーは通常39文字以上です。"
        print(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    return api_key, api_key_type


# def configure_gemini_model(api_key: str, model_name: str = 'gemini-2.5-flash') -> genai.GenerativeModel:
def configure_gemini_model(api_key: str, model_name: str = 'gemini-3-flash-preview') -> genai.GenerativeModel:
    """
    Gemini APIを設定し、モデルインスタンスを返す
    
    Args:
        api_key: 検証済みのAPIキー
        model_name: 使用するモデル名（デフォルト: 'gemini-2.5-flash'）
        
    Returns:
        genai.GenerativeModel: 設定済みのGenerativeModelインスタンス
        
    Raises:
        ValueError: APIの初期化に失敗した場合
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        return model
    except Exception as e:
        error_msg = f"Gemini APIの初期化に失敗しました: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"エラーの詳細: {traceback.format_exc()}")
        raise ValueError(error_msg) from e


# def initialize_gemini_model_2_5_flash(model_name: str = 'gemini-2.5-flash') -> genai.GenerativeModel:
def initialize_gemini_model_2_5_flash(model_name: str = 'gemini-3-flash-preview') -> genai.GenerativeModel:
    """
    Gemini APIキーを取得・検証し、モデルを初期化する（一括処理）
    
    Args:
        model_name: 使用するモデル名（デフォルト: 'gemini-2.5-flash'）
        
    Returns:
        genai.GenerativeModel: 設定済みのGenerativeModelインスタンス
        
    Raises:
        ValueError: APIキーが設定されていない、無効、または初期化に失敗した場合
    """
    api_key, api_key_type = get_and_validate_api_key()
    return configure_gemini_model(api_key, model_name)

