#!/usr/bin/env python3
"""
参照画像に基づいて新しいイラストを生成するテストスクリプト

使い方:
    python test_image_generation.py <参照画像のパス> [プロンプト]

例:
    python test_image_generation.py /path/to/reference.jpg "これがついたりしてる"
    python test_image_generation.py https://storage.googleapis.com/.../image.jpg "これがついたりしてる"
"""

import sys
import os
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.service.image_generator_service import image_generator_service


def main():
    """メイン処理"""
    # 引数のチェック
    if len(sys.argv) < 2:
        print("❌ エラー: 参照画像のパスを指定してください")
        print("\n使い方:")
        print(f"  python {sys.argv[0]} <参照画像のパス> [プロンプト]")
        print("\n例:")
        print(f'  python {sys.argv[0]} /path/to/reference.jpg "これがついたりしてる"')
        sys.exit(1)
    
    # 参照画像のパス
    reference_image_path = sys.argv[1]
    
    # プロンプト（指定がない場合はデフォルト値を使用）
    if len(sys.argv) >= 3:
        prompt = sys.argv[2]
    else:
        prompt = "これがついたりしてる"
    
    # 参照画像の存在確認（ローカルファイルの場合のみ）
    if not (reference_image_path.startswith("http://") or reference_image_path.startswith("https://")):
        if not os.path.exists(reference_image_path):
            print(f"❌ エラー: 参照画像が見つかりません: {reference_image_path}")
            sys.exit(1)
    
    print(f"🖼️  参照画像: {reference_image_path}")
    print(f"📝 プロンプト: {prompt}")
    print("\n🎨 画像生成を開始します...\n")
    
    try:
        # Image-to-Image生成を実行
        result = image_generator_service.generate_image_to_image(
            prompt=prompt,
            reference_image_path=reference_image_path,
            strength=1.0,  # 参照画像の影響度（0.0-1.0）
            prefix="test_i2i",
            user_id=None
        )
        
        # 結果を表示
        if "error" in result:
            print(f"❌ エラー: {result['error']}")
            sys.exit(1)
        
        print("\n✅ 画像生成成功!")
        print(f"📁 ファイル名: {result.get('filename', 'N/A')}")
        print(f"📂 ファイルパス: {result.get('filepath', result.get('gcs_path', 'N/A'))}")
        if result.get('public_url'):
            print(f"🔗 公開URL: {result.get('public_url')}")
        print(f"📊 サイズ: {result.get('size_bytes', 0)} bytes")
        if result.get('image_size'):
            print(f"🖼️  画像サイズ: {result.get('image_size')[0]}x{result.get('image_size')[1]} px")
        if result.get('processing_times'):
            times = result['processing_times']
            if times.get('api_duration'):
                print(f"⏱️  API処理時間: {times['api_duration']:.2f}秒")
            if times.get('save_duration'):
                print(f"💾 保存処理時間: {times['save_duration']:.2f}秒")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

