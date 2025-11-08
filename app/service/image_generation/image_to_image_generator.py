import os
import time
from typing import Dict, Any, Optional
from PIL import Image
from io import BytesIO
from datetime import datetime
from .base_image_generator import BaseImageGenerator

class ImageToImageGenerator(BaseImageGenerator):
    """Image-to-Image生成機能を提供するクラス"""
    
    def generate_image_to_image(
        self, 
        prompt: str, 
        reference_image_path: str, 
        strength: float = 1.0,
        prefix: str = "i2i_image",
        user_id: str = None,
        story_id: Optional[int] = None,
        page_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """Image-to-Image生成"""
        try:
            # API処理時間計測開始
            api_start_time = time.time()
            
            # プロンプトに文字なしの指示とアスペクト比を追加（強化版）
            enhanced_prompt = (
                f"{prompt}. "
                f"Image format: 3:4 aspect ratio. "
                f"MANDATORY: The image must be exactly 3:4 ratio, wide and landscape, NOT portrait or square. "
                f"The composition should be horizontal with elements spread across the width. "
                f"CRITICAL REQUIREMENTS: Absolutely NO text, NO letters, NO words, NO writing, NO captions, "
                f"NO speech bubbles, NO signs, NO labels, NO symbols, NO numbers, NO typography, "
                f"NO written language of any kind. This must be a pure visual illustration only. "
                f"The image should be completely text-free and contain only visual elements, characters, "
                f"objects, and scenes without any written content whatsoever."
            )
            
            print(f"🎨 Image-to-Image生成開始")
            print(f"🖼️ 参考画像: {reference_image_path}")
            print(f"💪 強度: {strength} (型: {type(strength).__name__}, 値: {strength})")
            
            # 参考画像のURLを確認
            print(f"🔗 使用する画像URL: {reference_image_path}")
            
            # 参考画像をBase64エンコード
            reference_image_base64 = self.encode_image_to_base64(reference_image_path)
            
            # 画像のMIMEタイプを自動検出
            if reference_image_path.startswith("https://") or reference_image_path.startswith("http://"):
                # GCSのURLの場合は拡張子から判定
                file_extension = os.path.splitext(reference_image_path.split('?')[0])[1].lower()
            else:
                # ローカルファイルの場合
                file_extension = os.path.splitext(reference_image_path)[1].lower()
            
            mime_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.webp': 'image/webp'
            }
            mime_type = mime_type_map.get(file_extension, 'image/jpeg')
            
            # Gemini APIでImage-to-Image生成
            # 参考画像をBase64エンコードしてAPIに送信
            # Image-to-Image生成のためのプロンプトを作成
            strength_percentage = strength * 100
            print(f"🔍 [DEBUG] プロンプトに含まれる強度: {strength_percentage}% (strength={strength})")
            i2i_prompt = f"Based on this reference image, create a new illustration with the following description: {enhanced_prompt}. " \
                        f"Maintain the style and composition similar to the reference image with {strength_percentage}% similarity. " \
                        f"Reference image characteristics should be preserved while adapting to the new scene."
            
            # プロンプト全文をターミナルに表示
            print("=" * 80)
            print("【Gemini API プロンプト全文 - Image-to-Image生成】")
            print("=" * 80)
            print(i2i_prompt)
            print("=" * 80)
            
            response = self.model.generate_content([
                i2i_prompt,
                {
                    "mime_type": mime_type,
                    "data": reference_image_base64
                }
            ])
            
            # API処理時間計算
            api_end_time = time.time()
            api_duration = api_end_time - api_start_time
            print(f"⏱️ API処理時間: {api_duration:.2f}秒")
            
            # 簡潔なレスポンスログ（バイナリデータは出力しない）
            print(f"🔍 Gemini API レスポンス受信")
            if hasattr(response, 'candidates') and response.candidates:
                print(f"📋 candidates 数: {len(response.candidates)}")
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    if hasattr(content, 'parts') and content.parts:
                        print(f"📋 content.parts 数: {len(content.parts)}")
                        for j, part in enumerate(content.parts):
                            if hasattr(part, 'inline_data') and part.inline_data:
                                data_size = len(part.inline_data.data) if hasattr(part.inline_data, 'data') else 0
                                print(f"📋 part[{j}] 画像データサイズ: {data_size} bytes")
                            if hasattr(part, 'text') and part.text:
                                print(f"📋 part[{j}] テキスト: {part.text[:50]}...")
            else:
                print(f"📋 レスポンスに有効なデータがありません")
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    if hasattr(content, 'parts') and content.parts:
                        for idx, part in enumerate(content.parts):
                            if not hasattr(part, 'inline_data') or part.inline_data is None:
                                continue
                            mime = getattr(part.inline_data, 'mime_type', None)
                            if mime and not str(mime).startswith('image/'):
                                print(f"⚠️ part[{idx}] は画像ではないためスキップ (mime={mime})")
                                continue
                            # 画像バイトを取得
                            image_data = part.inline_data.data
                            # バイト検証（壊れたデータを除外）
                            try:
                                with Image.open(BytesIO(image_data)) as _img_verify:
                                    _img_verify.verify()
                                with Image.open(BytesIO(image_data)) as _img:
                                    image_size = _img.size
                            except Exception as e:
                                print(f"⚠️ part[{idx}] 画像バイトが不正のためスキップ: {e}")
                                continue

                            # page_indexが指定されている場合はpage_XX.png形式のファイル名を使用
                            if page_index is not None:
                                # page_indexに基づいたファイル名を生成（page_00.png, page_01.png, ...）
                                filename = f"page_{page_index:02d}.png"
                            else:
                                filename = self.generate_unique_filename(prefix, "png")
                            
                            # 保存処理時間計測
                            save_start_time = time.time()
                            save_result = self.save_image_to_storage(
                                image_data=image_data,
                                filename=filename,
                                user_id=user_id,
                                story_id=story_id,
                                content_type="image/png",
                                page_index=page_index
                            )
                            save_end_time = time.time()
                            save_duration = save_end_time - save_start_time
                            print(f"💾 保存処理時間: {save_duration:.2f}秒")

                            if save_result["success"]:
                                # 画像情報を返す
                                image_info = {
                                    "filename": filename,
                                    "filepath": save_result.get("filepath", save_result.get("gcs_path")),
                                    "public_url": save_result.get("public_url"),
                                    "size_bytes": len(image_data),
                                    "image_size": image_size,
                                    "format": "png", # Gemini APIはPNGを返すため
                                    "timestamp": datetime.now().isoformat(),
                                    "prompt": enhanced_prompt,
                                    "reference_image_path": reference_image_path,
                                    "strength": strength,
                                    "processing_times": {
                                        "api_duration": api_duration,
                                        "save_duration": save_duration
                                    }
                                }
                                print(f"✅ Image-to-Image生成成功: {filename}")
                                return image_info
                            else:
                                print(f"❌ Image-to-Image画像保存失敗: {save_result.get('error')}")
                                return {
                                    "error": f"画像保存に失敗しました: {save_result.get('error')}",
                                    "filename": filename
                                }
            
            raise Exception("画像データが見つかりませんでした")
            
        except Exception as e:
            print(f"❌ Image-to-Image生成エラー: {e}")
            raise e
