"""
テーマ生成のみをテストするスクリプト
APIサーバーを起動しなくても実行可能

使用方法:
1. 環境変数を設定（.envファイルまたは環境変数）:
   - GEMINI_API_KEY: Gemini APIキー
   - その他の必要な環境変数

2. このスクリプトを実行:
   python test_theme_generation.py
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 環境変数を読み込む
load_dotenv()

from app.features._02_generate_theme.services.theme_generator import ThemeGenerator


def print_section(title: str):
    """セクションタイトルの表示"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_success(message: str):
    """成功メッセージの表示"""
    print(f"✅ {message}")


def print_error(message: str):
    """エラーメッセージの表示"""
    print(f"❌ {message}")


def test_theme_generation():
    """テーマ生成をテスト"""
    
    print_section("テーマ生成テスト")
    
    # テスト用のストーリー設定
    story_setting = {
        "protagonist_name": "たろう",
        "protagonist_type": "うさぎ",
        "setting_place": "森",
        "tone": "gentle",
        "target_age": "preschool",
        "reading_level": "hiragana_only"
    }
    
    print("\n【テスト設定】")
    for key, value in story_setting.items():
        print(f"  {key}: {value}")
    
    try:
        # ThemeGeneratorのインスタンスを作成
        print_section("ThemeGeneratorを初期化")
        generator = ThemeGenerator()
        print_success("ThemeGeneratorの初期化に成功しました")
        
        # テーマ生成を実行
        print_section("テーマ生成を実行")
        print("Gemini APIを呼び出しています...")
        
        theme_data = generator.generate_theme_options_only(story_setting)
        
        print_success("テーマ生成に成功しました！")
        
        # 結果を表示
        print_section("生成されたテーマ")
        
        if "theme_options" in theme_data:
            theme_options = theme_data["theme_options"]
            print(f"\n生成されたテーマ数: {len(theme_options)}")
            
            for theme_key, theme in theme_options.items():
                print(f"\n【{theme_key}】")
                print(f"  theme_id: {theme.get('theme_id', 'N/A')}")
                print(f"  タイトル: {theme.get('title', 'N/A')}")
                print(f"  説明: {theme.get('description', 'N/A')}")
                print(f"  キーワード: {', '.join(theme.get('keywords', []))}")
        else:
            print_error("theme_optionsが見つかりません")
            print(f"レスポンスデータ: {json.dumps(theme_data, ensure_ascii=False, indent=2)}")
        
        # JSON形式で結果を表示
        print_section("JSON形式の結果")
        print(json.dumps(theme_data, ensure_ascii=False, indent=2))
        
        print_section("テスト完了")
        print_success("テーマ生成のテストが正常に完了しました！")
        
        return True
        
    except Exception as e:
        print_error(f"テーマ生成中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = test_theme_generation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ テストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

