import os
import uuid
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from google.generativeai import types
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.models.story.stroy_plot import StoryPlot
from app.models.story.story_setting import StorySetting
from app.core.config import STORAGE_TYPE
from app.service.gcs_storage_service import GCSStorageService

load_dotenv()

class ImageGeneratorService:
    """Gemini APIを使用して高品質な画像を生成するサービス"""

    def __init__(self):
        # APIキーを設定
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEYが設定されていません")
        
        # Gemini クライアントを初期化
        genai.configure(api_key=api_key)
        self.client = genai
        self.model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        # ストレージタイプに応じてディレクトリを設定
        if STORAGE_TYPE == "gcs":
            # GCSを使用する場合はローカルディレクトリは不要
            self.images_dir = None
            self.reference_images_dir = None
            self.upload_images_dir = None
            # GCSサービスを初期化
            self.gcs_service = GCSStorageService()
        else:
            # ローカルストレージを使用
            self.images_dir = "app/uploads/generated_images"
            self.reference_images_dir = "app/uploads/reference_images"
            self.upload_images_dir = "app/uploads/upload_images"
            os.makedirs(self.images_dir, exist_ok=True)
            os.makedirs(self.reference_images_dir, exist_ok=True)
            os.makedirs(self.upload_images_dir, exist_ok=True)
            self.gcs_service = None

    def create_save_directory(self, subdir: str = None):
        """画像保存用ディレクトリを作成（ローカルストレージの場合のみ）"""
        if STORAGE_TYPE == "gcs":
            return None
        
        if subdir:
            save_dir = os.path.join(self.images_dir, subdir)
        else:
            save_dir = self.images_dir
        os.makedirs(save_dir, exist_ok=True)
        return save_dir

    def generate_unique_filename(self, prefix: str = "generated_image", extension: str = "png"):
        """ユニークなファイル名を生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{prefix}_{timestamp}_{unique_id}.{extension}"


    def save_image_to_storage(self, image_data: bytes, filename: str, user_id: int = 2, story_id: Optional[int] = None, content_type: str = "image/png") -> Dict[str, Any]:
        """画像をストレージに保存（GCSまたはローカル）"""
        if STORAGE_TYPE == "gcs":
            # Google Cloud Storageに保存
            return self.gcs_service.upload_generated_image(
                file_content=image_data,
                filename=filename,
                user_id=user_id,
                story_id=story_id,
                content_type=content_type
            )
        else:
            # ローカルストレージに保存
            filepath = os.path.join(self.images_dir, filename)
            with open(filepath, "wb") as f:
                f.write(image_data)
            
            return {
                "success": True,
                "filename": filename,
                "filepath": filepath,
                "size_bytes": len(image_data),
                "content_type": content_type,
                "timestamp": datetime.now().isoformat()
            }

    def generate_single_image(self, prompt: str, prefix: str = "storybook_image") -> Dict[str, Any]:
        """単一の画像を生成"""
        try:
            # プロンプトにアスペクト比を追加
            enhanced_prompt = f"{prompt}. Image format: 16:9 aspect ratio (landscape orientation), horizontal composition. MANDATORY: The image must be exactly 16:9 ratio, wide and landscape, NOT portrait or square. The composition should be horizontal with elements spread across the width."
            print(f"画像生成開始: {enhanced_prompt}")
            
            # 画像生成のリクエストを作成
            response = self.model.generate_content(enhanced_prompt)
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data is not None:
                                # 画像データを取得
                                image_data = part.inline_data.data
                                
                                # 画像をPILで開いて情報を取得
                                image = Image.open(BytesIO(image_data))
                                filename = self.generate_unique_filename(prefix, "png")
                                
                                # ストレージに保存
                                save_result = self.save_image_to_storage(
                                    image_data=image_data,
                                    filename=filename,
                                    user_id=2,  # デフォルトユーザーID
                                    content_type="image/png"
                                )
                                
                                if save_result["success"]:
                                    # 成功時の情報を返す
                                    image_info = {
                                        "filename": filename,
                                        "filepath": save_result.get("filepath", save_result.get("gcs_path")),
                                        "public_url": save_result.get("public_url"),
                                        "size_bytes": len(image_data),
                                        "image_size": image.size,
                                        "format": image.format,
                                        "timestamp": datetime.now().isoformat(),
                                        "prompt": prompt
                                    }
                                    print(f"画像生成成功: {filename}")
                                    return image_info
                                else:
                                    print(f"画像保存失敗: {save_result.get('error')}")
                                    return {
                                        "error": f"画像保存に失敗しました: {save_result.get('error')}",
                                        "filename": filename
                                    }
            
            return {
                "error": "画像生成に失敗しました: レスポンスに画像データが含まれていません",
                "filename": None
            }
            
        except Exception as e:
            print(f"画像生成エラー: {str(e)}")
            return {
                "error": f"画像生成に失敗しました: {str(e)}",
                "filename": None
            }

    def generate_multiple_images(self, prompts: List[str], prefix: str = "storybook_page") -> List[Dict[str, Any]]:
        """複数の画像を一括生成"""
        print(f"🚀 複数画像生成開始... (プロンプト数: {len(prompts)})")
        
        generated_images = []
        
        for i, prompt in enumerate(prompts, 1):
            try:
                # プロンプトに文字なしの指示とアスペクト比を追加
                enhanced_prompt = (
                    f"{prompt}. "
                    f"Image format: 16:9 aspect ratio (landscape orientation), horizontal composition. "
                    f"MANDATORY: The image must be exactly 16:9 ratio, wide and landscape, NOT portrait or square. "
                    f"The composition should be horizontal with elements spread across the width. "
                    f"CRITICAL REQUIREMENTS: Absolutely NO text, NO letters, NO words, NO writing, NO captions, "
                    f"NO speech bubbles, NO signs, NO labels, NO symbols, NO numbers, NO typography, "
                    f"NO written language of any kind. This must be a pure visual illustration only. "
                    f"The image should be completely text-free and contain only visual elements, characters, "
                    f"objects, and scenes without any written content whatsoever."
                )
                
                print(f"\n📝 プロンプト {i}/{len(prompts)}: {enhanced_prompt[:50]}...")
                
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash-image-preview",
                    contents=[enhanced_prompt]
                )
                
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        content = candidate.content
                        if hasattr(content, 'parts') and content.parts:
                            for part in content.parts:
                                if hasattr(part, 'inline_data') and part.inline_data is not None:
                                    image_data = part.inline_data.data
                                    filename = self.generate_unique_filename(f"{prefix}_{i}", "png")
                                    
                                    save_result = self.save_image_to_storage(
                                        image_data=image_data,
                                        filename=filename,
                                        user_id=2,  # デフォルトユーザーID
                                        content_type="image/png"
                                    )
                                    
                                    if save_result["success"]:
                                        image_info = {
                                            "prompt_index": i,
                                            "filename": filename,
                                            "filepath": save_result.get("filepath", save_result.get("gcs_path")),
                                            "public_url": save_result.get("public_url"),
                                            "size_bytes": len(image_data),
                                            "image_size": Image.open(BytesIO(image_data)).size,
                                            "format": "png", # Gemini APIはPNGを返すため
                                            "timestamp": datetime.now().isoformat(),
                                            "prompt": enhanced_prompt
                                        }
                                        generated_images.append(image_info)
                                        print(f"✅ 画像 {i} 生成成功: {filename}")
                                        break
                                    else:
                                        print(f"❌ プロンプト {i} 画像保存失敗: {save_result.get('error')}")
                                        generated_images.append({
                                            "prompt_index": i,
                                            "filename": filename,
                                            "error": f"画像保存に失敗しました: {save_result.get('error')}"
                                        })
                                        break
            except Exception as e:
                print(f"❌ プロンプト {i} エラー: {e}")
        
        print(f"\n🎉 画像生成完了! 成功: {len(generated_images)}/{len(prompts)}")
        return generated_images

    def generate_storybook_images(self, story_pages: List[str], storybook_id: str) -> List[Dict[str, Any]]:
        """絵本用の画像を生成（ストーリーページごと）"""
        # 絵本専用のサブディレクトリを作成
        storybook_dir = self.create_save_directory(f"storybook_{storybook_id}")
        
        prompts = []
        for i, page_content in enumerate(story_pages, 1):
            # 絵本風のプロンプトを作成（16:9アスペクト比指定）
            prompt = (
                f"Create a beautiful children's book illustration for: {page_content}. "
                f"Style: children's book illustration, warm and friendly, bright colors, "
                f"simple and clean design, suitable for children. "
                f"Image format: 16:9 aspect ratio (landscape orientation), horizontal composition. "
                f"MANDATORY: The image must be exactly 16:9 ratio, wide and landscape, NOT portrait or square. "
                f"The composition should be horizontal with elements spread across the width. "
                f"CRITICAL REQUIREMENTS: Absolutely NO text, NO letters, NO words, NO writing, NO captions, "
                f"NO speech bubbles, NO signs, NO labels, NO symbols, NO numbers, NO typography, "
                f"NO written language of any kind. This must be a pure visual illustration only. "
                f"The image should be completely text-free and contain only visual elements, characters, "
                f"objects, and scenes without any written content whatsoever."
            )
            prompts.append(prompt)
        
        generated_images = []
        
        for i, prompt in enumerate(prompts, 1):
            try:
                response = self.model.generate_content(prompt)
                
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        content = candidate.content
                        if hasattr(content, 'parts') and content.parts:
                            for part in content.parts:
                                if hasattr(part, 'inline_data') and part.inline_data is not None:
                                    image_data = part.inline_data.data
                                    filename = f"storybook_{storybook_id}_page_{i}.png"
                                    
                                    save_result = self.save_image_to_storage(
                                        image_data=image_data,
                                        filename=filename,
                                        user_id=2,  # デフォルトユーザーID
                                        content_type="image/png"
                                    )
                                    
                                    if save_result["success"]:
                                        image_info = {
                                            "page_number": i,
                                            "filename": filename,
                                            "filepath": save_result.get("filepath", save_result.get("gcs_path")),
                                            "public_url": save_result.get("public_url"),
                                            "size_bytes": len(image_data),
                                            "image_size": Image.open(BytesIO(image_data)).size,
                                            "format": "png", # Gemini APIはPNGを返すため
                                            "timestamp": datetime.now().isoformat(),
                                            "storybook_id": storybook_id,
                                            "page_content": story_pages[i-1]
                                        }
                                        generated_images.append(image_info)
                                        print(f"✅ 絵本ページ {i} 生成成功: {filename}")
                                        break
                                    else:
                                        print(f"❌ 絵本ページ {i} 画像保存失敗: {save_result.get('error')}")
                                        generated_images.append({
                                            "page_number": i,
                                            "filename": filename,
                                            "error": f"画像保存に失敗しました: {save_result.get('error')}"
                                        })
                                        break
            except Exception as e:
                print(f"❌ 絵本ページ {i} エラー: {e}")
        
        return generated_images

    def generate_image_for_story_plot_page(self, db: Session, story_plot_id: int, page_number: int) -> Dict[str, Any]:
        """story_plotsテーブルの指定ページの内容で画像を生成"""
        try:
            # story_plotを取得
            story_plot = db.query(StoryPlot).filter(StoryPlot.id == story_plot_id).first()
            if not story_plot:
                raise ValueError(f"StoryPlot ID {story_plot_id} が見つかりません")
            
            # 指定されたページの内容を取得
            page_content = None
            if page_number == 1:
                page_content = story_plot.page_1
            elif page_number == 2:
                page_content = story_plot.page_2
            elif page_number == 3:
                page_content = story_plot.page_3
            elif page_number == 4:
                page_content = story_plot.page_4
            elif page_number == 5:
                page_content = story_plot.page_5
            else:
                raise ValueError(f"ページ番号 {page_number} は無効です。1-5の範囲で指定してください")
            
            if not page_content:
                raise ValueError(f"ページ {page_number} の内容が空です")
            
            # ストーリー設定の情報を取得してプロンプトを強化
            story_setting = story_plot.story_setting
            protagonist_name = story_setting.protagonist_name if story_setting else "主人公"
            protagonist_type = story_setting.protagonist_type if story_setting else "子供"
            setting_place = story_setting.setting_place if story_setting else "公園"
            
            # 絵本風のプロンプトを作成（16:9アスペクト比指定）
            enhanced_prompt = (
                f"Create a beautiful children's book illustration for: {page_content}. "
                f"Character: {protagonist_name} (a {protagonist_type}), "
                f"Setting: {setting_place}. "
                f"Style: children's book illustration, warm and friendly, bright colors, "
                f"simple and clean design, suitable for children, consistent character design. "
                f"Image format: 16:9 aspect ratio (landscape orientation), horizontal composition. "
                f"MANDATORY: The image must be exactly 16:9 ratio, wide and landscape, NOT portrait or square. "
                f"The composition should be horizontal with elements spread across the width. "
                f"CRITICAL REQUIREMENTS: Absolutely NO text, NO letters, NO words, NO writing, NO captions, "
                f"NO speech bubbles, NO signs, NO labels, NO symbols, NO numbers, NO typography, "
                f"NO written language of any kind. This must be a pure visual illustration only. "
                f"The image should be completely text-free and contain only visual elements, characters, "
                f"objects, and scenes without any written content whatsoever."
            )
            
            print(f"🎨 StoryPlot画像生成開始 (ID: {story_plot_id}, ページ: {page_number})")
            print(f"📝 プロンプト: {enhanced_prompt[:100]}...")
            
            # 画像生成を実行
            response = self.model.generate_content(enhanced_prompt)
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data is not None:
                                # 画像データを取得
                                image_data = part.inline_data.data
                                filename = self.generate_unique_filename(
                                    f"storyplot_{story_plot_id}_page_{page_number}", 
                                    "png"
                                )
                                
                                save_result = self.save_image_to_storage(
                                    image_data=image_data,
                                    filename=filename,
                                    user_id=story_plot.user_id,  # ストーリープロットのユーザーID
                                    story_id=story_plot_id,  # ストーリープロットID
                                    content_type="image/png"
                                )
                                
                                if save_result["success"]:
                                    # 画像情報を返す
                                    image_info = {
                                        "story_plot_id": story_plot_id,
                                        "page_number": page_number,
                                        "filename": filename,
                                        "filepath": save_result.get("filepath", save_result.get("gcs_path")),
                                        "public_url": save_result.get("public_url"),
                                        "size_bytes": len(image_data),
                                        "image_size": Image.open(BytesIO(image_data)).size,
                                        "format": "png", # Gemini APIはPNGを返すため
                                        "timestamp": datetime.now().isoformat(),
                                        "page_content": page_content,
                                        "title": story_plot.title,
                                        "protagonist_name": protagonist_name,
                                        "setting_place": setting_place
                                    }
                                    print(f"✅ StoryPlot画像生成成功: {filename}")
                                    return image_info
                                else:
                                    print(f"❌ StoryPlot画像保存失敗: {save_result.get('error')}")
                                    return {
                                        "error": f"画像保存に失敗しました: {save_result.get('error')}",
                                        "story_plot_id": story_plot_id,
                                        "page_number": page_number,
                                        "filename": filename
                                    }
            
            raise Exception("画像データが見つかりませんでした")
            
        except Exception as e:
            print(f"❌ StoryPlot画像生成エラー: {e}")
            raise e

    def generate_all_pages_for_story_plot(self, db: Session, story_plot_id: int) -> List[Dict[str, Any]]:
        """story_plotsテーブルの全ページの画像を生成"""
        try:
            # story_plotを取得
            story_plot = db.query(StoryPlot).filter(StoryPlot.id == story_plot_id).first()
            if not story_plot:
                raise ValueError(f"StoryPlot ID {story_plot_id} が見つかりません")
            
            print(f"🚀 StoryPlot全ページ画像生成開始 (ID: {story_plot_id})")
            
            generated_images = []
            
            # 各ページの画像を生成
            for page_num in range(1, 6):  # 1-5ページ
                page_content = None
                if page_num == 1:
                    page_content = story_plot.page_1
                elif page_num == 2:
                    page_content = story_plot.page_2
                elif page_num == 3:
                    page_content = story_plot.page_3
                elif page_num == 4:
                    page_content = story_plot.page_4
                elif page_num == 5:
                    page_content = story_plot.page_5
                
                if page_content:  # 内容があるページのみ生成
                    try:
                        image_info = self.generate_image_for_story_plot_page(db, story_plot_id, page_num)
                        generated_images.append(image_info)
                        print(f"✅ ページ {page_num} 生成成功")
                    except Exception as e:
                        print(f"❌ ページ {page_num} 生成エラー: {e}")
                else:
                    print(f"⚠️ ページ {page_num} は内容が空のためスキップ")
            
            print(f"🎉 StoryPlot全ページ画像生成完了! 成功: {len(generated_images)}/5")
            return generated_images
            
        except Exception as e:
            print(f"❌ StoryPlot全ページ画像生成エラー: {e}")
            raise e

    def encode_image_to_base64(self, image_path: str) -> str:
        """画像ファイルをBase64エンコード（GCSのURLとローカルパスの両方に対応）"""
        try:
            if image_path.startswith("https://") or image_path.startswith("http://"):
                # 古いURL形式を新しい形式に変換
                if "storage.cloud.google.com" in image_path:
                    image_path = image_path.replace("storage.cloud.google.com", "storage.googleapis.com")
                    print(f"🔄 URL形式を変換: {image_path}")
                
                # GCSのURLの場合はHTTPリクエストで取得
                import requests
                print(f"📥 GCS画像を取得中: {image_path}")
                response = requests.get(image_path, timeout=30)
                response.raise_for_status()
                
                # レスポンスの内容タイプを確認
                content_type = response.headers.get('content-type', '')
                print(f"📋 取得した画像のContent-Type: {content_type}")
                
                # 画像データのサイズを確認
                image_data = response.content
                print(f"📏 画像データサイズ: {len(image_data)} bytes")
                
                # 画像データの先頭部分を確認（デバッグ用）
                if len(image_data) > 0:
                    print(f"🔍 画像データ先頭: {image_data[:20].hex()}")
                else:
                    raise Exception("画像データが空です")
                
                return base64.b64encode(image_data).decode('utf-8')
            else:
                # ローカルファイルの場合
                print(f"📁 ローカル画像を読み込み中: {image_path}")
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
                    print(f"📏 ローカル画像データサイズ: {len(image_data)} bytes")
                    return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            print(f"❌ 画像エンコードエラー: {e}")
            print(f"画像パス: {image_path}")
            raise e

    def generate_image_to_image(
        self, 
        prompt: str, 
        reference_image_path: str, 
        strength: float = 0.8,
        prefix: str = "i2i_image"
    ) -> Dict[str, Any]:
        """Image-to-Image生成"""
        try:
            
            # プロンプトに文字なしの指示とアスペクト比を追加（強化版）
            enhanced_prompt = (
                f"{prompt}. "
                f"Image format: 16:9 aspect ratio (landscape orientation), horizontal composition. "
                f"MANDATORY: The image must be exactly 16:9 ratio, wide and landscape, NOT portrait or square. "
                f"The composition should be horizontal with elements spread across the width. "
                f"CRITICAL REQUIREMENTS: Absolutely NO text, NO letters, NO words, NO writing, NO captions, "
                f"NO speech bubbles, NO signs, NO labels, NO symbols, NO numbers, NO typography, "
                f"NO written language of any kind. This must be a pure visual illustration only. "
                f"The image should be completely text-free and contain only visual elements, characters, "
                f"objects, and scenes without any written content whatsoever."
            )
            
            print(f"🎨 Image-to-Image生成開始")
            print(f"📝 プロンプト: {enhanced_prompt[:50]}...")
            print(f"🖼️ 参考画像: {reference_image_path}")
            print(f"💪 強度: {strength}")
            
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
            i2i_prompt = f"Based on this reference image, create a new illustration with the following description: {enhanced_prompt}. " \
                        f"Maintain the style and composition similar to the reference image with {strength*100}% similarity. " \
                        f"Reference image characteristics should be preserved while adapting to the new scene."
            
            
            response = self.model.generate_content([
                i2i_prompt,
                {
                    "mime_type": mime_type,
                    "data": reference_image_base64
                }
            ])
            
            # 詳細なレスポンスログ
            print(f"🔍 Gemini API レスポンス詳細:")
            print(f"📋 レスポンス型: {type(response)}")
            print(f"📋 レスポンス属性: {dir(response)}")
            
            if hasattr(response, 'candidates'):
                print(f"📋 candidates 数: {len(response.candidates) if response.candidates else 0}")
                if response.candidates:
                    for i, candidate in enumerate(response.candidates):
                        print(f"📋 candidate[{i}] 型: {type(candidate)}")
                        print(f"📋 candidate[{i}] 属性: {dir(candidate)}")
                        
                        if hasattr(candidate, 'content'):
                            content = candidate.content
                            print(f"📋 candidate[{i}].content 型: {type(content)}")
                            print(f"📋 candidate[{i}].content 属性: {dir(content)}")
                            
                            if hasattr(content, 'parts'):
                                print(f"📋 candidate[{i}].content.parts 数: {len(content.parts) if content.parts else 0}")
                                if content.parts:
                                    for j, part in enumerate(content.parts):
                                        print(f"📋 candidate[{i}].content.parts[{j}] 型: {type(part)}")
                                        print(f"📋 candidate[{i}].content.parts[{j}] 属性: {dir(part)}")
                                        
                                        if hasattr(part, 'inline_data'):
                                            print(f"📋 candidate[{i}].content.parts[{j}].inline_data: {part.inline_data}")
                                        if hasattr(part, 'text'):
                                            print(f"📋 candidate[{i}].content.parts[{j}].text: {part.text}")
                        else:
                            print(f"📋 candidate[{i}] に content 属性がありません")
                else:
                    print(f"📋 candidates が空です")
            else:
                print(f"📋 レスポンスに candidates 属性がありません")
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data is not None:
                                # 画像データを取得
                                image_data = part.inline_data.data
                                filename = self.generate_unique_filename(prefix, "png")
                                
                                save_result = self.save_image_to_storage(
                                    image_data=image_data,
                                    filename=filename,
                                    user_id=2,  # デフォルトユーザーID
                                    content_type="image/png"
                                )
                                
                                if save_result["success"]:
                                    # 画像情報を返す
                                    image_info = {
                                        "filename": filename,
                                        "filepath": save_result.get("filepath", save_result.get("gcs_path")),
                                        "public_url": save_result.get("public_url"),
                                        "size_bytes": len(image_data),
                                        "image_size": Image.open(BytesIO(image_data)).size,
                                        "format": "png", # Gemini APIはPNGを返すため
                                        "timestamp": datetime.now().isoformat(),
                                        "prompt": enhanced_prompt,
                                        "reference_image_path": reference_image_path,
                                        "strength": strength
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

    def generate_storyplot_image_to_image(
        self, 
        db: Session, 
        story_plot_id: int, 
        page_number: int, 
        reference_image_path: str,
        strength: float = 0.8,
        prefix: str = "storyplot_i2i"
    ) -> Dict[str, Any]:
        """StoryPlot用Image-to-Image生成（1ページずつ）"""
        try:
            # story_plotを取得
            story_plot = db.query(StoryPlot).filter(StoryPlot.id == story_plot_id).first()
            if not story_plot:
                raise ValueError(f"StoryPlot ID {story_plot_id} が見つかりません")
            
            # 指定されたページの内容を取得
            page_content = self._get_page_content(story_plot, page_number)
            
            # ストーリー設定の情報を取得してプロンプトを強化
            story_setting = story_plot.story_setting
            protagonist_name = story_setting.protagonist_name if story_setting else "主人公"
            protagonist_type = story_setting.protagonist_type if story_setting else "子供"
            setting_place = story_setting.setting_place if story_setting else "公園"
            
            # 絵本風のプロンプトを作成（story_plotsデータを活用、アップロード画像の特徴を反映）
            enhanced_prompt = self._create_storyplot_prompt(
                page_content, protagonist_name, protagonist_type, setting_place, story_plot, reference_image_path
            )
            
            print(f"🎨 StoryPlot Image-to-Image生成開始 (ID: {story_plot_id}, ページ: {page_number})")
            print(f"📝 プロンプト: {enhanced_prompt[:100]}...")
            print(f"🖼️ 参考画像: {reference_image_path}")
            print(f"💪 強度: {strength}")
            
            # Image-to-Image生成を実行
            image_info = self.generate_image_to_image(
                prompt=enhanced_prompt,
                reference_image_path=reference_image_path,
                strength=strength,
                prefix=f"{prefix}_{story_plot_id}_page_{page_number}"
            )
            
            # StoryPlot固有の情報を追加
            image_info.update({
                "story_plot_id": story_plot_id,
                "page_number": page_number,
                "page_content": page_content,
                "title": story_plot.title,
                "protagonist_name": protagonist_name,
                "setting_place": setting_place,
                "description": story_plot.description,
                "selected_theme": story_plot.selected_theme
            })
            
            print(f"✅ StoryPlot Image-to-Image生成成功: {image_info['filename']}")
            return image_info
            
        except Exception as e:
            print(f"❌ StoryPlot Image-to-Image生成エラー: {e}")
            raise e

    def _get_page_content(self, story_plot: StoryPlot, page_number: int) -> str:
        """指定されたページの内容を取得"""
        if page_number == 1:
            return story_plot.page_1
        elif page_number == 2:
            return story_plot.page_2
        elif page_number == 3:
            return story_plot.page_3
        elif page_number == 4:
            return story_plot.page_4
        elif page_number == 5:
            return story_plot.page_5
        else:
            return ""  # バリデーションはエンドポイント層で行う

    def _create_storyplot_prompt(
        self, 
        page_content: str, 
        protagonist_name: str, 
        protagonist_type: str, 
        setting_place: str,
        story_plot: StoryPlot,
        reference_image_path: str = None
    ) -> str:
        """StoryPlotデータを活用したプロンプトを作成（アップロード画像の特徴を反映）"""
        
        # テーマ情報を取得
        theme_info = ""
        if story_plot.description:
            theme_info = f"Theme: {story_plot.description}. "
        
        # キーワード情報を取得
        keywords_info = ""
        if story_plot.keywords:
            keywords = story_plot.keywords if isinstance(story_plot.keywords, list) else []
            if keywords:
                keywords_info = f"Keywords: {', '.join(keywords)}. "
        
        # アップロード画像の特徴をプロンプトに追加
        reference_style_info = ""
        if reference_image_path:
            reference_style_info = (
                f"IMPORTANT: Maintain the visual style, color palette, and artistic characteristics "
                f"from the reference image. The reference image shows the desired art style, "
                f"color scheme, and visual approach that should be consistently applied. "
                f"Preserve the artistic elements, composition style, and visual mood from the reference. "
            )
        
        # 強化されたプロンプトを作成
        enhanced_prompt = (
            f"Create a beautiful children's book illustration for: {page_content}. "
            f"Character: {protagonist_name} (a {protagonist_type}), "
            f"Setting: {setting_place}. "
            f"{theme_info}"
            f"{keywords_info}"
            f"{reference_style_info}"
            f"Style: children's book illustration, warm and friendly, bright colors, "
            f"simple and clean design, suitable for children, consistent character design. "
            f"CRITICAL REQUIREMENTS: Absolutely NO text, NO letters, NO words, NO writing, NO captions, "
            f"NO speech bubbles, NO signs, NO labels, NO symbols, NO numbers, NO typography, "
            f"NO written language of any kind. This must be a pure visual illustration only. "
            f"The image should be completely text-free and contain only visual elements, characters, "
            f"objects, and scenes without any written content whatsoever."
        )
        
        return enhanced_prompt

    def generate_storyplot_all_pages_i2i(
        self, 
        db: Session, 
        story_plot_id: int, 
        reference_image_path: str,
        strength: float = 0.8,
        prefix: str = "storyplot_i2i_all"
    ) -> List[Dict[str, Any]]:
        """StoryPlotの全ページをi2iで一括生成"""
        try:
            # story_plotを取得
            story_plot = db.query(StoryPlot).filter(StoryPlot.id == story_plot_id).first()
            if not story_plot:
                raise ValueError(f"StoryPlot ID {story_plot_id} が見つかりません")
            
            print(f"🚀 StoryPlot全ページi2i生成開始 (ID: {story_plot_id})")
            print(f"🖼️ 参考画像: {reference_image_path}")
            print(f"💪 強度: {strength}")
            
            generated_images = []
            
            # 各ページの画像を生成（ページごとに強度を調整）
            for page_num in range(1, 6):  # 1-5ページ
                page_content = self._get_page_content(story_plot, page_num)
                
                if page_content:  # 内容があるページのみ生成
                    try:
                        # ページごとに強度を調整（1ページ目は高め、2-4ページ目は中程度、5ページ目は高め）
                        if page_num == 1:
                            page_strength = min(strength + 0.1, 1.0)  # 1ページ目は参考画像の影響を強く
                        elif page_num in [2, 3, 4]:
                            page_strength = max(strength  + 0.1, 1.0)  # 2-4ページ目は中程度の強度
                        else:  # page_num == 5
                            page_strength = min(strength  + 0.1, 1.0)  # 5ページ目は少し高め
                        
                        image_info = self.generate_storyplot_image_to_image(
                            db=db,
                            story_plot_id=story_plot_id,
                            page_number=page_num,
                            reference_image_path=reference_image_path,
                            strength=page_strength,
                            prefix=f"{prefix}_{story_plot_id}"
                        )
                        generated_images.append(image_info)
                        print(f"✅ ページ {page_num} i2i生成成功 (強度: {page_strength})")
                    except Exception as e:
                        print(f"❌ ページ {page_num} i2i生成エラー: {e}")
                else:
                    print(f"⚠️ ページ {page_num} は内容が空のためスキップ")
            
            print(f"🎉 StoryPlot全ページi2i生成完了! 成功: {len(generated_images)}/5")
            return generated_images
            
        except Exception as e:
            print(f"❌ StoryPlot全ページi2i生成エラー: {e}")
            raise e

    def upload_reference_image(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """参考画像をアップロードして保存"""
        try:
            # ファイル拡張子を取得
            file_extension = filename.split(".")[-1].lower() if "." in filename else "jpg"
            
            # ユニークなファイル名を生成
            unique_filename = self.generate_unique_filename("uploaded_image", file_extension)
            filepath = os.path.join(self.upload_images_dir, unique_filename)
            
            # ファイルを保存
            with open(filepath, "wb") as f:
                f.write(file_content)
            
            # 画像情報を取得
            try:
                image = Image.open(filepath)
                image_size = image.size
                image_format = image.format
            except Exception as e:
                print(f"⚠️ 画像情報取得エラー: {e}")
                image_size = (0, 0)
                image_format = file_extension.upper()
            
            # 画像情報を返す
            image_info = {
                "filename": unique_filename,
                "filepath": filepath,
                "size_bytes": len(file_content),
                "image_size": image_size,
                "format": image_format,
                "timestamp": datetime.now().isoformat(),
                "original_filename": filename
            }
            
            print(f"✅ 参考画像アップロード成功: {unique_filename}")
            return image_info
            
        except Exception as e:
            print(f"❌ 参考画像アップロードエラー: {e}")
            raise e

    def get_uploaded_images_list(self) -> List[Dict[str, Any]]:
        """アップロードされた画像のリストを取得"""
        try:
            uploaded_images = []
            
            if STORAGE_TYPE == "gcs":
                # GCSから画像を取得
                bucket = self.gcs_service.client.bucket(self.gcs_service.bucket_name)
                blobs = bucket.list_blobs(prefix="uploads/")
                
                for blob in blobs:
                    if blob.name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                        image_info = {
                            "filename": os.path.basename(blob.name),
                            "filepath": blob.name,
                            "size_bytes": blob.size,
                            "image_size": (0, 0), # GCSからは直接サイズを取得できないため
                            "format": "unknown",
                            "timestamp": datetime.fromtimestamp(blob.updated).isoformat(),
                            "public_url": self.gcs_service.get_public_url(blob.name)
                        }
                        uploaded_images.append(image_info)
            else:
                if os.path.exists(self.upload_images_dir):
                    for filename in os.listdir(self.upload_images_dir):
                        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                            filepath = os.path.join(self.upload_images_dir, filename)
                            file_stats = os.stat(filepath)
                            
                            try:
                                image = Image.open(filepath)
                                image_size = image.size
                                image_format = image.format
                            except Exception:
                                image_size = (0, 0)
                                image_format = filename.split(".")[-1].upper()
                            
                            image_info = {
                                "filename": filename,
                                "filepath": filepath,
                                "size_bytes": file_stats.st_size,
                                "image_size": image_size,
                                "format": image_format,
                                "timestamp": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                            }
                            uploaded_images.append(image_info)
            
            # タイムスタンプでソート（新しい順）
            uploaded_images.sort(key=lambda x: x["timestamp"], reverse=True)
            
            print(f"📁 アップロード画像一覧: {len(uploaded_images)}枚")
            return uploaded_images
            
        except Exception as e:
            print(f"❌ アップロード画像一覧取得エラー: {e}")
            raise e

# シングルトンインスタンス
image_generator_service = ImageGeneratorService()
