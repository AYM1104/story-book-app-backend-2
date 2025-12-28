"""
絵本生成の一連の流れをテストするスクリプト
アプリを起動しなくても実行可能

使用方法:
1. 環境変数を設定:
   export ENABLE_TEST_MODE=true
   export TEST_USER_ID=test|123456789
   export BACKEND_URL=http://localhost:8000

2. バックエンドサーバーを起動:
   cd backend && uvicorn app.main:app --reload

3. このスクリプトを実行:
   python test_storybook_generation.py
"""
import os
import sys
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# バックエンドのURL（環境変数から取得、デフォルトはローカル）
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# テスト用のユーザーID
TEST_USER_ID = os.getenv("TEST_USER_ID", "test|123456789")


def print_step(step_num: int, message: str):
    """ステップの表示"""
    print(f"\n{'='*60}")
    print(f"ステップ {step_num}: {message}")
    print(f"{'='*60}")


def print_success(message: str, data: Optional[Dict[str, Any]] = None):
    """成功メッセージの表示"""
    print(f"✅ {message}")
    if data:
        for key, value in data.items():
            print(f"   {key}: {value}")


def print_error(message: str, response: Optional[requests.Response] = None):
    """エラーメッセージの表示"""
    print(f"❌ {message}")
    if response:
        try:
            print(f"\n   ステータスコード: {response.status_code}")
            print(f"   レスポンス本文:")
            print(f"   {response.text}")
            
            # JSONレスポンスの場合は整形して表示
            try:
                error_json = response.json()
                if isinstance(error_json, dict):
                    print(f"\n   エラー詳細:")
                    for key, value in error_json.items():
                        if isinstance(value, str) and len(value) > 100:
                            print(f"     {key}: {value[:100]}...")
                        else:
                            print(f"     {key}: {value}")
            except Exception:
                pass
            
            # レスポンスヘッダーも表示（デバッグ用）
            if response.status_code >= 500:
                print(f"\n   ⚠️ サーバーエラーが発生しました")
                print(f"   バックエンドサーバーのログを確認してください")
        except Exception as e:
            print(f"   エラー情報の取得に失敗しました: {e}")


def test_storybook_generation_flow(image_path: Optional[str] = None):
    """絵本生成の一連の流れをテスト"""
    
    print("\n" + "="*60)
    print("絵本生成フローのテストを開始します")
    print("="*60)
    print(f"バックエンドURL: {BASE_URL}")
    print(f"テストユーザーID: {TEST_USER_ID}")
    
    # ヘルスチェック
    print_step(0, "ヘルスチェック")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("バックエンドサーバーに接続できました")
        else:
            print_error(f"バックエンドサーバーの応答が異常です: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"バックエンドサーバーに接続できません: {e}")
        print(f"   バックエンドサーバーが起動しているか確認してください: {BASE_URL}")
        return False
    
    # 1. 画像アップロード
    print_step(1, "画像をアップロード")
    
    if not image_path:
        image_path = input("画像ファイルのパスを入力してください（Enterでスキップ）: ").strip()
        if not image_path:
            print("⚠️ 画像アップロードをスキップします")
            print("   既存のupload_image_idを使用する場合は、手動で設定してください")
            upload_image_id = input("upload_image_idを入力してください（Enterで終了）: ").strip()
            if not upload_image_id:
                print("❌ テストを終了します")
                return False
            try:
                upload_image_id = int(upload_image_id)
            except ValueError:
                print_error("無効なupload_image_idです")
                return False
        else:
            if not Path(image_path).exists():
                print_error(f"画像ファイルが見つかりません: {image_path}")
                return False
            
            try:
                # ファイル名を取得
                filename = Path(image_path).name
                # ファイル拡張子からContent-Typeを推測
                ext = Path(image_path).suffix.lower()
                content_type_map = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.webp': 'image/webp'
                }
                content_type = content_type_map.get(ext, 'image/png')
                
                with open(image_path, "rb") as f:
                    files = {"file": (filename, f, content_type)}
                    data = {"user_id": TEST_USER_ID}
                    response = requests.post(
                        f"{BASE_URL}/api/images/upload",
                        files=files,
                        data=data,
                        timeout=60
                    )
                
                if response.status_code != 200:
                    print_error("画像アップロード失敗", response)
                    print("\n💡 トラブルシューティング:")
                    print("   - バックエンドサーバーのログを確認してください")
                    print("   - 環境変数 SUPABASE_DB_URL が設定されているか確認してください")
                    print("   - 環境変数 GCS_BUCKET_NAME が設定されているか確認してください")
                    print("   - 環境変数 GOOGLE_APPLICATION_CREDENTIALS が設定されているか確認してください")
                    return False
                
                upload_result = response.json()
                upload_image_id = upload_result["id"]
                print_success("画像アップロード成功", {"upload_image_id": upload_image_id})
            except Exception as e:
                print_error(f"画像アップロード中にエラーが発生しました: {e}")
                return False
    else:
        if not Path(image_path).exists():
            print_error(f"画像ファイルが見つかりません: {image_path}")
            return False
        
        try:
            # ファイル名を取得
            filename = Path(image_path).name
            # ファイル拡張子からContent-Typeを推測
            ext = Path(image_path).suffix.lower()
            content_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.webp': 'image/webp'
            }
            content_type = content_type_map.get(ext, 'image/png')
            
            with open(image_path, "rb") as f:
                files = {"file": (filename, f, content_type)}
                data = {"user_id": TEST_USER_ID}
                response = requests.post(
                    f"{BASE_URL}/api/images/upload",
                    files=files,
                    data=data,
                    timeout=60
                )
            
                if response.status_code != 200:
                    print_error("画像アップロード失敗", response)
                    print("\n💡 トラブルシューティング:")
                    print("   - バックエンドサーバーのログを確認してください")
                    print("   - 環境変数 SUPABASE_DB_URL が設定されているか確認してください")
                    print("   - 環境変数 GCS_BUCKET_NAME が設定されているか確認してください")
                    print("   - 環境変数 GOOGLE_APPLICATION_CREDENTIALS が設定されているか確認してください")
                    return False
            
            upload_result = response.json()
            upload_image_id = upload_result["id"]
            print_success("画像アップロード成功", {"upload_image_id": upload_image_id})
        except Exception as e:
            print_error(f"画像アップロード中にエラーが発生しました: {e}")
            return False
    
    # 2. ストーリー設定を作成
    print_step(2, "ストーリー設定を作成")
    try:
        response = requests.post(
            f"{BASE_URL}/api/story/story_settings/{upload_image_id}",
            timeout=30
        )
        
        if response.status_code != 200:
            print_error("ストーリー設定作成失敗", response)
            return False
        
        story_setting_result = response.json()
        story_setting_id = story_setting_result["story_setting_id"]
        print_success("ストーリー設定作成成功", {"story_setting_id": story_setting_id})
    except Exception as e:
        print_error(f"ストーリー設定作成中にエラーが発生しました: {e}")
        return False
    
    # 3. テーマ生成
    print_step(3, "テーマを生成")
    try:
        response = requests.post(
            f"{BASE_URL}/api/story/story_generator",
            json={"story_setting_id": story_setting_id},
            timeout=120
        )
        
        if response.status_code != 200:
            print_error("テーマ生成失敗", response)
            return False
        
        theme_result = response.json()
        story_plot_ids = theme_result["story_plot_ids"]
        theme_options = theme_result.get("theme_options", {})
        print_success("テーマ生成成功", {
            "story_plot_ids": story_plot_ids,
            "テーマ数": len(theme_options)
        })
        
        # テーマの一覧を表示
        for key, theme in theme_options.items():
            print(f"   - {key}: {theme.get('title', 'N/A')}")
    except Exception as e:
        print_error(f"テーマ生成中にエラーが発生しました: {e}")
        return False
    
    # 4. テーマ選択と物語生成
    print_step(4, "テーマを選択して物語を生成")
    
    # テーマを選択（デフォルトはtheme1）
    selected_theme = input("選択するテーマを入力してください (theme1/theme2/theme3、Enterでtheme1): ").strip() or "theme1"
    story_pages_input = input("ページ数を入力してください (3/5/7/10、Enterで5): ").strip() or "5"
    
    try:
        story_pages = int(story_pages_input)
        if story_pages not in [3, 5, 7, 10]:
            print_error(f"無効なページ数です: {story_pages} (3, 5, 7, 10のいずれかを指定してください)")
            return False
    except ValueError:
        print_error(f"無効なページ数です: {story_pages_input}")
        return False
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/story/select_theme",
            json={
                "story_setting_id": story_setting_id,
                "selected_theme": selected_theme,
                "story_pages": story_pages
            },
            timeout=120
        )
        
        if response.status_code != 200:
            print_error("物語生成失敗", response)
            return False
        
        story_result = response.json()
        story_plot_id = story_result["story_plot_id"]
        print_success("物語生成成功", {
            "story_plot_id": story_plot_id,
            "タイトル": story_result.get("title", "N/A"),
            "消費クレジット": story_result.get("credits_spent", "N/A"),
            "ページ数": story_pages
        })
    except Exception as e:
        print_error(f"物語生成中にエラーが発生しました: {e}")
        return False
    
    # 5. ストーリーブック作成
    print_step(5, "ストーリーブックを作成")
    try:
        response = requests.post(
            f"{BASE_URL}/api/storybook/confirm-theme-and-create",
            json={
                "story_plot_id": story_plot_id,
                "selected_theme": selected_theme,
                "story_pages": story_pages
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print_error("ストーリーブック作成失敗", response)
            return False
        
        storybook_result = response.json()
        storybook_id = storybook_result["storybook_id"]
        print_success("ストーリーブック作成成功", {
            "storybook_id": storybook_id,
            "タイトル": storybook_result.get("title", "N/A")
        })
    except Exception as e:
        print_error(f"ストーリーブック作成中にエラーが発生しました: {e}")
        return False
    
    # 完了メッセージ
    print("\n" + "="*60)
    print("🎉 絵本生成のテストが完了しました！")
    print("="*60)
    print(f"Storybook ID: {storybook_id}")
    print(f"次のステップ: 画像生成APIを呼び出して画像を生成してください")
    print(f"   エンドポイント: POST {BASE_URL}/api/images/generate-storybook-all-pages-image-to-image")
    print(f"   パラメータ: storybook_id={storybook_id}")
    
    return True


if __name__ == "__main__":
    # コマンドライン引数から画像パスを取得
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        success = test_storybook_generation_flow(image_path)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ テストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

