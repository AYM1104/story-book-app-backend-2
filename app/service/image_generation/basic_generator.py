import os
import time
from typing import Dict, Any, List
from PIL import Image
from io import BytesIO
from datetime import datetime
from .base_image_generator import BaseImageGenerator

class BasicImageGenerator(BaseImageGenerator):
    """基本的な画像生成機能を提供するクラス"""
    
    def generate_single_image(self, prompt: str, prefix: str = "storybook_image", user_id: str = None) -> Dict[str, Any]:
        """単一の画像を生成"""
        try:
            # 処理時間計測開始
            start_time = time.time()
            
            # プロンプトにアスペクト比を追加
            enhanced_prompt = f"{prompt}. Image format: 3:4 aspect ratio. MANDATORY: The image must be exactly 3:4 ratio. No text, letters, words, captions, labels, symbols, or numbers."
            print(f"🕐 [{datetime.now().strftime('%H:%M:%S')}] 画像生成開始: {enhanced_prompt}")
            
            # プロンプト全文をターミナルに表示
            print("=" * 80)
            print("【Gemini API プロンプト全文 - 単一画像生成】")
            print("=" * 80)
            print(enhanced_prompt)
            print("=" * 80)
            
            # 画像生成のリクエストを作成
            api_start_time = time.time()
            response = self.model.generate_content(enhanced_prompt)
            api_end_time = time.time()
            api_duration = api_end_time - api_start_time
            print(f"⏱️ API処理時間: {api_duration:.2f}秒")
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data is not None:
                                # 画像データを取得
                                image_data = part.inline_data.data
                                
                                # PILで画像を開いてサイズを取得
                                image = Image.open(BytesIO(image_data))
                                filename = self.generate_unique_filename(prefix, "png")
                                
                                # ストレージに保存
                                save_start_time = time.time()
                                save_result = self.save_image_to_storage(
                                    image_data=image_data,
                                    filename=filename,
                                    user_id=user_id,
                                    content_type="image/png"
                                )
                                save_end_time = time.time()
                                save_duration = save_end_time - save_start_time
                                print(f"💾 保存処理時間: {save_duration:.2f}秒")
                                
                                # 総処理時間を計算
                                total_duration = time.time() - start_time
                                print(f"🎉 画像生成完了! 総処理時間: {total_duration:.2f}秒")
                                
                                if save_result["success"]:
                                    return {
                                        "filename": filename,
                                        "filepath": save_result.get("filepath", save_result.get("gcs_path")),
                                        "public_url": save_result.get("public_url"),
                                        "size_bytes": len(image_data),
                                        "image_size": image.size,
                                        "format": "png",
                                        "timestamp": datetime.now().isoformat(),
                                        "prompt": enhanced_prompt,
                                        "processing_times": {
                                            "api_duration": api_duration,
                                            "save_duration": save_duration,
                                            "total_duration": total_duration
                                        }
                                    }
                                else:
                                    return {
                                        "error": f"画像保存に失敗しました: {save_result.get('error')}",
                                        "filename": None
                                    }
            
            return {
                "error": "画像データが見つかりませんでした",
                "filename": None
            }
            
        except Exception as e:
            print(f"❌ 画像生成エラー: {e}")
            return {
                "error": f"画像生成に失敗しました: {str(e)}",
                "filename": None
            }

    def generate_multiple_images(self, prompts: List[str], prefix: str = "storybook_page", user_id: str = None) -> List[Dict[str, Any]]:
        """複数の画像を一括生成（リトライ機能付き）"""
        # 全体の処理時間計測開始
        overall_start_time = time.time()
        print(f"🚀 [{datetime.now().strftime('%H:%M:%S')}] 複数画像生成開始... (プロンプト数: {len(prompts)})")
        
        generated_images = []
        max_retries = 3  # 最大リトライ回数
        
        for i, prompt in enumerate(prompts, 1):
            success = False
            for attempt in range(max_retries):
                try:
                    # プロンプトに文字なしの指示とアスペクト比を追加
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
                    
                    print(f"\n📝 [{datetime.now().strftime('%H:%M:%S')}] プロンプト {i}/{len(prompts)} (試行 {attempt + 1}/{max_retries}): {enhanced_prompt[:50]}...")
                    
                    # プロンプト全文をターミナルに表示
                    print("=" * 80)
                    print(f"【Gemini API プロンプト全文 - 複数画像生成 {i}/{len(prompts)}】")
                    print("=" * 80)
                    print(enhanced_prompt)
                    print("=" * 80)
                    
                    # API処理時間計測
                    api_start_time = time.time()
                    response = self.client.models.generate_content(
                        model="gemini-2.5-flash-image-preview",
                        contents=[enhanced_prompt]
                    )
                    api_end_time = time.time()
                    api_duration = api_end_time - api_start_time
                    print(f"⏱️ API処理時間: {api_duration:.2f}秒")
                    
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content:
                            content = candidate.content
                            if hasattr(content, 'parts') and content.parts:
                                for part in content.parts:
                                    if hasattr(part, 'inline_data') and part.inline_data is not None:
                                        # 画像データを取得
                                        image_data = part.inline_data.data
                                        filename = f"{prefix}_{i}.png"
                                        
                                        # 保存処理時間計測
                                        save_start_time = time.time()
                                        save_result = self.save_image_to_storage(
                                            image_data=image_data,
                                            filename=filename,
                                            user_id=user_id,
                                            content_type="image/png"
                                        )
                                        save_end_time = time.time()
                                        save_duration = save_end_time - save_start_time
                                        print(f"💾 保存処理時間: {save_duration:.2f}秒")
                                        
                                        if save_result["success"]:
                                            generated_images.append({
                                                "prompt_index": i,
                                                "filename": filename,
                                                "filepath": save_result.get("filepath", save_result.get("gcs_path")),
                                                "public_url": save_result.get("public_url"),
                                                "size_bytes": len(image_data),
                                                "image_size": Image.open(BytesIO(image_data)).size,
                                                "format": "png",
                                                "timestamp": datetime.now().isoformat(),
                                                "prompt": enhanced_prompt,
                                                "processing_times": {
                                                    "api_duration": api_duration,
                                                    "save_duration": save_duration,
                                                    "total_duration": api_duration + save_duration
                                                }
                                            })
                                            success = True
                                            print(f"✅ プロンプト {i} 生成成功: {filename}")
                                        else:
                                            print(f"❌ プロンプト {i} 画像保存失敗: {save_result.get('error')}")
                                            if attempt < max_retries - 1:
                                                wait_time = (attempt + 1) * 2
                                                print(f"⏳ {wait_time}秒待機後にリトライします...")
                                                time.sleep(wait_time)
                                            else:
                                                generated_images.append({
                                                    "prompt_index": i,
                                                    "filename": filename,
                                                    "error": f"画像保存に失敗しました: {save_result.get('error')}"
                                                })
                                            break
                    else:
                        print(f"❌ プロンプト {i} レスポンスエラー (試行 {attempt + 1})")
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2
                            print(f"⏳ {wait_time}秒待機後にリトライします...")
                            time.sleep(wait_time)
                    
                except Exception as e:
                    print(f"❌ プロンプト {i} エラー (試行 {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        print(f"⏳ {wait_time}秒待機後にリトライします...")
                        time.sleep(wait_time)
                
                if success:
                    break
            
            if not success:
                print(f"❌ プロンプト {i} の生成に失敗しました（{max_retries}回試行後）")
                generated_images.append({
                    "prompt_index": i,
                    "error": f"プロンプト {i} の生成に失敗しました（{max_retries}回試行後）",
                    "filename": None
                })
            
            # API制限を避けるため、各画像生成後に少し待機
            if i < len(prompts):  # 最後のプロンプト以外は待機
                print(f"⏳ API制限を避けるため2秒待機...")
                time.sleep(2)
        
        successful_count = len([img for img in generated_images if "error" not in img])
        overall_duration = time.time() - overall_start_time
        print(f"\n🎉 [{datetime.now().strftime('%H:%M:%S')}] 画像生成完了! 成功: {successful_count}/{len(prompts)}")
        print(f"⏱️ 総処理時間: {overall_duration:.2f}秒 (平均: {overall_duration/len(prompts):.2f}秒/画像)")
        return generated_images
