import os
import uuid
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.models.story.stroy_plot import StoryPlot
from app.models.story.story_setting import StorySetting

load_dotenv()

class ImageGeneratorService:
    """Gemini APIを使用して高品質な画像を生成するサービス"""

    def __init__(self):
        # APIキーを設定
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEYまたはGOOGLE_API_KEYが設定されていません")
        
        # Gemini クライアントを初期化
        self.client = genai.Client(api_key=api_key)
        
        # 画像保存用ディレクトリ
        self.images_dir = "app/uploads/generated_images"
        self.reference_images_dir = "app/uploads/reference_images"
        self.upload_images_dir = "app/uploads/upload_images"
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.reference_images_dir, exist_ok=True)
        os.makedirs(self.upload_images_dir, exist_ok=True)

    def create_save_directory(self, subdir: str = None):
        """画像保存用ディレクトリを作成"""
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

    def generate_single_image(self, prompt: str, prefix: str = "storybook_image") -> Dict[str, Any]:
        """単一の画像を生成"""
        try:
            # プロンプトに文字なしの指示を追加（強化版）
            enhanced_prompt = (
                f"{prompt}. "
                f"CRITICAL REQUIREMENTS: Absolutely NO text, NO letters, NO words, NO writing, NO captions, "
                f"NO speech bubbles, NO signs, NO labels, NO symbols, NO numbers, NO typography, "
                f"NO written language of any kind. This must be a pure visual illustration only. "
                f"The image should be completely text-free and contain only visual elements, characters, "
                f"objects, and scenes without any written content whatsoever."
            )
            
            print(f"🎨 画像生成開始: {enhanced_prompt[:50]}...")
            
            # 画像生成を実行
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
                                # 画像を保存
                                image = Image.open(BytesIO(part.inline_data.data))
                                filename = self.generate_unique_filename(prefix, "png")
                                filepath = os.path.join(self.images_dir, filename)
                                image.save(filepath)
                                
                                # 画像情報を返す
                                image_info = {
                                    "filename": filename,
                                    "filepath": filepath,
                                    "size_bytes": len(part.inline_data.data),
                                    "image_size": image.size,
                                    "format": image.format,
                                    "timestamp": datetime.now().isoformat(),
                                    "prompt": enhanced_prompt
                                }
                                
                                print(f"✅ 画像生成成功: {filename}")
                                return image_info
            
            raise Exception("画像データが見つかりませんでした")
            
        except Exception as e:
            print(f"❌ 画像生成エラー: {e}")
            raise e

    def generate_multiple_images(self, prompts: List[str], prefix: str = "storybook_page") -> List[Dict[str, Any]]:
        """複数の画像を一括生成"""
        print(f"🚀 複数画像生成開始... (プロンプト数: {len(prompts)})")
        
        generated_images = []
        
        for i, prompt in enumerate(prompts, 1):
            try:
                # プロンプトに文字なしの指示を追加
                enhanced_prompt = (
                    f"{prompt}. "
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
                                    image = Image.open(BytesIO(part.inline_data.data))
                                    filename = self.generate_unique_filename(f"{prefix}_{i}", "png")
                                    filepath = os.path.join(self.images_dir, filename)
                                    image.save(filepath)
                                    
                                    image_info = {
                                        "prompt_index": i,
                                        "filename": filename,
                                        "filepath": filepath,
                                        "size_bytes": len(part.inline_data.data),
                                        "image_size": image.size,
                                        "format": image.format,
                                        "timestamp": datetime.now().isoformat(),
                                        "prompt": enhanced_prompt
                                    }
                                    
                                    generated_images.append(image_info)
                                    print(f"✅ 画像 {i} 生成成功: {filename}")
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
            # 絵本風のプロンプトを作成
            prompt = (
                f"Create a beautiful children's book illustration for: {page_content}. "
                f"Style: children's book illustration, warm and friendly, bright colors, "
                f"simple and clean design, suitable for children. "
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
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash-image-preview",
                    contents=[prompt]
                )
                
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        content = candidate.content
                        if hasattr(content, 'parts') and content.parts:
                            for part in content.parts:
                                if hasattr(part, 'inline_data') and part.inline_data is not None:
                                    image = Image.open(BytesIO(part.inline_data.data))
                                    filename = f"storybook_{storybook_id}_page_{i}.png"
                                    filepath = os.path.join(storybook_dir, filename)
                                    image.save(filepath)
                                    
                                    image_info = {
                                        "page_number": i,
                                        "filename": filename,
                                        "filepath": filepath,
                                        "size_bytes": len(part.inline_data.data),
                                        "image_size": image.size,
                                        "format": image.format,
                                        "timestamp": datetime.now().isoformat(),
                                        "storybook_id": storybook_id,
                                        "page_content": story_pages[i-1]
                                    }
                                    
                                    generated_images.append(image_info)
                                    print(f"✅ 絵本ページ {i} 生成成功: {filename}")
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
            
            # 絵本風のプロンプトを作成
            enhanced_prompt = (
                f"Create a beautiful children's book illustration for: {page_content}. "
                f"Character: {protagonist_name} (a {protagonist_type}), "
                f"Setting: {setting_place}. "
                f"Style: children's book illustration, warm and friendly, bright colors, "
                f"simple and clean design, suitable for children, consistent character design. "
                f"CRITICAL REQUIREMENTS: Absolutely NO text, NO letters, NO words, NO writing, NO captions, "
                f"NO speech bubbles, NO signs, NO labels, NO symbols, NO numbers, NO typography, "
                f"NO written language of any kind. This must be a pure visual illustration only. "
                f"The image should be completely text-free and contain only visual elements, characters, "
                f"objects, and scenes without any written content whatsoever."
            )
            
            print(f"🎨 StoryPlot画像生成開始 (ID: {story_plot_id}, ページ: {page_number})")
            print(f"📝 プロンプト: {enhanced_prompt[:100]}...")
            
            # 画像生成を実行
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
                                # 画像を保存
                                image = Image.open(BytesIO(part.inline_data.data))
                                filename = self.generate_unique_filename(
                                    f"storyplot_{story_plot_id}_page_{page_number}", 
                                    "png"
                                )
                                filepath = os.path.join(self.images_dir, filename)
                                image.save(filepath)
                                
                                # 画像情報を返す
                                image_info = {
                                    "story_plot_id": story_plot_id,
                                    "page_number": page_number,
                                    "filename": filename,
                                    "filepath": filepath,
                                    "size_bytes": len(part.inline_data.data),
                                    "image_size": image.size,
                                    "format": image.format,
                                    "timestamp": datetime.now().isoformat(),
                                    "page_content": page_content,
                                    "title": story_plot.title,
                                    "protagonist_name": protagonist_name,
                                    "setting_place": setting_place
                                }
                                
                                print(f"✅ StoryPlot画像生成成功: {filename}")
                                return image_info
            
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
        """画像ファイルをBase64エンコード"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"❌ 画像エンコードエラー: {e}")
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
            
            # プロンプトに文字なしの指示を追加（強化版）
            enhanced_prompt = (
                f"{prompt}. "
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
            
            # 参考画像をBase64エンコード
            reference_image_base64 = self.encode_image_to_base64(reference_image_path)
            
            # 画像のMIMEタイプを自動検出
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
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=[
                    {
                        "text": f"Based on this reference image, create a new illustration with the following description: {enhanced_prompt}. "
                               f"Maintain the style and composition similar to the reference image with {strength*100}% similarity. "
                               f"Reference image characteristics should be preserved while adapting to the new scene."
                    },
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": reference_image_base64
                        }
                    }
                ]
            )
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data is not None:
                                # 画像を保存
                                image = Image.open(BytesIO(part.inline_data.data))
                                filename = self.generate_unique_filename(prefix, "png")
                                filepath = os.path.join(self.images_dir, filename)
                                image.save(filepath)
                                
                                # 画像情報を返す
                                image_info = {
                                    "filename": filename,
                                    "filepath": filepath,
                                    "size_bytes": len(part.inline_data.data),
                                    "image_size": image.size,
                                    "format": image.format,
                                    "timestamp": datetime.now().isoformat(),
                                    "prompt": enhanced_prompt,
                                    "reference_image_path": reference_image_path,
                                    "strength": strength
                                }
                                
                                print(f"✅ Image-to-Image生成成功: {filename}")
                                return image_info
            
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
            
            # 絵本風のプロンプトを作成（story_plotsデータを活用）
            enhanced_prompt = self._create_storyplot_prompt(
                page_content, protagonist_name, protagonist_type, setting_place, story_plot
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
        story_plot: StoryPlot
    ) -> str:
        """StoryPlotデータを活用したプロンプトを作成"""
        
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
        
        # 強化されたプロンプトを作成
        enhanced_prompt = (
            f"Create a beautiful children's book illustration for: {page_content}. "
            f"Character: {protagonist_name} (a {protagonist_type}), "
            f"Setting: {setting_place}. "
            f"{theme_info}"
            f"{keywords_info}"
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
            
            # 各ページの画像を生成
            for page_num in range(1, 6):  # 1-5ページ
                page_content = self._get_page_content(story_plot, page_num)
                
                if page_content:  # 内容があるページのみ生成
                    try:
                        image_info = self.generate_storyplot_image_to_image(
                            db=db,
                            story_plot_id=story_plot_id,
                            page_number=page_num,
                            reference_image_path=reference_image_path,
                            strength=strength,
                            prefix=f"{prefix}_{story_plot_id}"
                        )
                        generated_images.append(image_info)
                        print(f"✅ ページ {page_num} i2i生成成功")
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
