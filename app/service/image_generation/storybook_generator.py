import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from PIL import Image
from io import BytesIO
from datetime import datetime
from .base_image_generator import BaseImageGenerator

class StoryBookGenerator(BaseImageGenerator):
    """StoryBook専用の画像生成機能を提供するクラス"""
    
    def generate_storybook_images(self, story_pages: List[str], storybook_id: str, user_id: str = None) -> List[Dict[str, Any]]:
        """絵本用の画像を生成（ストーリーページごと）"""
        # 全体の処理時間計測開始
        overall_start_time = time.time()
        total_pages = len(story_pages)
        print(f"📚 [{datetime.now().strftime('%H:%M:%S')}] 絵本画像生成開始... (ページ数: {total_pages})")
        
        # プロンプトを作成
        prompts = []
        for i, page_content in enumerate(story_pages, 1):
            # ページ数情報をプロンプトに追加
            page_info = f" This is page {i} of {total_pages} in a {total_pages}-page children's book. "
            
            # 絵本風のプロンプトを作成（2:3アスペクト比指定）
            prompt = (
                f"Create a beautiful children's book illustration depicting the scene described here (DO NOT render this text in the image): {page_content}. "
                f"Style: children's book illustration, warm and friendly, bright colors, "
                f"simple and clean design, suitable for children. "
                f"{page_info}"
                f"Image format: 2:3 aspect ratio (portrait orientation). "
                f"MANDATORY: The image must be exactly 2:3 ratio, tall and portrait, NOT landscape or square. "
                f"The composition should be vertical with elements arranged from top to bottom. "
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
                # ページごとの処理時間計測開始
                page_start_time = time.time()
                print(f"\n📝 [{datetime.now().strftime('%H:%M:%S')}] ページ {i}/{len(prompts)} 生成開始...")
                
                # プロンプト全文をターミナルに表示
                print("=" * 80)
                print(f"【Gemini API プロンプト全文 - 絵本画像生成 ページ {i}】")
                print("=" * 80)
                print(prompt)
                print("=" * 80)
                
                # API処理時間計測
                api_start_time = time.time()
                response = self.model.generate_content(prompt)
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
                                    image_data = part.inline_data.data
                                    filename = f"storybook_{storybook_id}_page_{i}.png"
                                    
                                    # storybook_idを整数に変換してstory_idとして渡す（絵本ごとにフォルダを分けるため）
                                    story_id = int(storybook_id) if isinstance(storybook_id, str) else storybook_id
                                    
                                    # 保存処理時間計測
                                    save_start_time = time.time()
                                    save_result = self.save_image_to_storage(
                                        image_data=image_data,
                                        filename=filename,
                                        user_id=user_id,
                                        story_id=story_id,  # 絵本ごとにフォルダを分ける
                                        content_type="image/png",
                                        page_index=i
                                    )
                                    save_end_time = time.time()
                                    save_duration = save_end_time - save_start_time
                                    print(f"💾 保存処理時間: {save_duration:.2f}秒")
                                    
                                    # ページ処理時間計算
                                    page_duration = time.time() - page_start_time
                                    print(f"📄 ページ {i} 処理時間: {page_duration:.2f}秒")
                                    
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
                                            "prompt": prompt,
                                            "page_content": story_pages[i-1],
                                            "storybook_id": storybook_id,
                                            "processing_times": {
                                                "api_duration": api_duration,
                                                "save_duration": save_duration,
                                                "page_duration": page_duration
                                            }
                                        }
                                        generated_images.append(image_info)
                                        print(f"✅ 絵本ページ {i} 生成成功: {filename}")
                                    else:
                                        print(f"❌ 絵本ページ {i} 保存失敗: {save_result.get('error')}")
                                        generated_images.append({
                                            "page_number": i,
                                            "error": f"画像保存に失敗しました: {save_result.get('error')}",
                                            "filename": None
                                        })
                                else:
                                    print(f"❌ 絵本ページ {i} 画像データが見つかりません")
                                    generated_images.append({
                                        "page_number": i,
                                        "error": "画像データが見つかりません",
                                        "filename": None
                                    })
                            break
                else:
                    print(f"❌ 絵本ページ {i} レスポンスエラー")
                    generated_images.append({
                        "page_number": i,
                        "error": "APIレスポンスエラー",
                        "filename": None
                    })
                    
            except Exception as e:
                print(f"❌ 絵本ページ {i} 生成エラー: {e}")
                generated_images.append({
                    "page_number": i,
                    "error": f"画像生成に失敗しました: {str(e)}",
                    "filename": None
                })
        
        successful_count = len([img for img in generated_images if "error" not in img])
        overall_duration = time.time() - overall_start_time
        print(f"\n🎉 [{datetime.now().strftime('%H:%M:%S')}] 絵本画像生成完了! 成功: {successful_count}/{len(story_pages)}")
        print(f"⏱️ 総処理時間: {overall_duration:.2f}秒 (平均: {overall_duration/len(story_pages):.2f}秒/ページ)")
        return generated_images

    def generate_image_for_story_plot_page(self, db: Session, story_plot_id: int, page_number: int, user_id: str = None) -> Dict[str, Any]:
        """StoryPlotの指定ページの画像を生成"""
        try:
            from app.models.story.story_plot import StoryPlot
            
            # story_plotを取得
            story_plot = db.query(StoryPlot).filter(StoryPlot.id == story_plot_id).first()
            if not story_plot:
                raise ValueError(f"StoryPlot ID {story_plot_id} が見つかりません")
            
            # 指定されたページの内容を取得
            page_content = self._get_page_content(story_plot, page_number)
            if not page_content:
                raise ValueError(f"ページ {page_number} の内容が空です")
            
            # ストーリー設定の情報を取得してプロンプトを強化
            story_setting = story_plot.story_setting
            protagonist_name = story_setting.protagonist_name if story_setting else "主人公"
            protagonist_type = story_setting.protagonist_type if story_setting else "子供"
            setting_place = story_setting.setting_place if story_setting else "公園"
            
            # 総ページ数を計算
            total_pages = self._get_total_pages(story_plot)
            
            # ページ数情報をプロンプトに追加
            page_info = f" This is page {page_number} of {total_pages} in a {total_pages}-page children's book. "
            
            # 絵本風のプロンプトを作成
            enhanced_prompt = (
                f"Create a beautiful children's book illustration depicting the scene described here (DO NOT render this text in the image): {page_content}. "
                f"Style: children's book illustration, warm and friendly, bright colors, "
                f"simple and clean design, suitable for children. "
                f"Character: {protagonist_name} (a {protagonist_type}). "
                f"Setting: {setting_place}. "
                f"{page_info}"
                f"Image format: 2:3 aspect ratio (portrait orientation), vertical composition. "
                f"MANDATORY: The image must be exactly 2:3 ratio, tall and portrait, NOT landscape or square. "
                f"The composition should be vertical with elements arranged from top to bottom. "
                f"CRITICAL REQUIREMENTS: Absolutely NO text, NO letters, NO words, NO writing, NO captions, "
                f"NO speech bubbles, NO signs, NO labels, NO symbols, NO numbers, NO typography, "
                f"NO written language of any kind. This must be a pure visual illustration only. "
                f"The image should be completely text-free and contain only visual elements, characters, "
                f"objects, and scenes without any written content whatsoever."
            )
            
            print(f"🎨 [{datetime.now().strftime('%H:%M:%S')}] StoryPlotページ画像生成開始 (ID: {story_plot_id}, ページ: {page_number})")
            
            # プロンプト全文をターミナルに表示
            print("=" * 80)
            print(f"【Gemini API プロンプト全文 - StoryPlotページ画像生成】")
            print("=" * 80)
            print(enhanced_prompt)
            print("=" * 80)
            
            # 処理時間計測開始
            start_time = time.time()
            
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
                                filename = f"storyplot_{story_plot_id}_page_{page_number}.png"
                                
                                # 保存処理時間計測
                                save_start_time = time.time()
                                save_result = self.save_image_to_storage(
                                    image_data=image_data,
                                    filename=filename,
                                    user_id=user_id,
                                    content_type="image/png",
                                    page_index=page_number
                                )
                                save_end_time = time.time()
                                save_duration = save_end_time - save_start_time
                                print(f"💾 保存処理時間: {save_duration:.2f}秒")
                                
                                # 総処理時間計算
                                total_duration = time.time() - start_time
                                print(f"🎉 StoryPlotページ画像生成完了! 総処理時間: {total_duration:.2f}秒")
                                
                                if save_result["success"]:
                                    image_info = {
                                        "story_plot_id": story_plot_id,
                                        "page_number": page_number,
                                        "filename": filename,
                                        "filepath": save_result.get("filepath", save_result.get("gcs_path")),
                                        "public_url": save_result.get("public_url"),
                                        "size_bytes": len(image_data),
                                        "image_size": Image.open(BytesIO(image_data)).size,
                                        "format": "png",
                                        "timestamp": datetime.now().isoformat(),
                                        "page_content": page_content,
                                        "title": story_plot.title,
                                        "protagonist_name": protagonist_name,
                                        "setting_place": setting_place,
                                        "description": story_plot.description,
                                        "selected_theme": story_plot.selected_theme,
                                        "processing_times": {
                                            "api_duration": api_duration,
                                            "save_duration": save_duration,
                                            "total_duration": total_duration
                                        }
                                    }
                                    print(f"✅ StoryPlotページ画像生成成功: {filename}")
                                    return image_info
                                else:
                                    return {
                                        "error": f"画像保存に失敗しました: {save_result.get('error')}",
                                        "filename": filename
                                    }
            
            return {
                "error": "画像データが見つかりませんでした",
                "filename": None
            }
            
        except Exception as e:
            print(f"❌ StoryPlotページ画像生成エラー: {e}")
            return {
                "error": f"画像生成に失敗しました: {str(e)}",
                "filename": None
            }

    def _normalize_keywords(self, keywords: Any) -> List[str]:
        """キーワードの型ゆらぎを吸収して文字列配列として整形する"""
        normalized: List[str] = []

        if not keywords:
            return normalized

        if isinstance(keywords, str):
            items = [keywords]
        elif isinstance(keywords, dict):
            items = [keywords]
        elif isinstance(keywords, (list, tuple, set)):
            items = list(keywords)
        else:
            items = [keywords]

        for item in items:
            if isinstance(item, str):
                candidate = item.strip()
                if candidate:
                    normalized.append(candidate)
            elif isinstance(item, dict):
                # よく使われるキーを優先的に参照
                for key in ("keyword", "name", "value", "label"):
                    value = item.get(key)
                    if isinstance(value, str):
                        candidate = value.strip()
                        if candidate:
                            normalized.append(candidate)
                        break
                else:
                    candidate = str(item).strip()
                    if candidate:
                        normalized.append(candidate)
            else:
                candidate = str(item).strip()
                if candidate:
                    normalized.append(candidate)

        # 重複を除去しつつ順序は維持
        seen = set()
        unique_keywords: List[str] = []
        for kw in normalized:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords

    def _create_cover_prompt(self, title: str, description: str, keywords: Any, protagonist_name: str, protagonist_type: str, setting_place: str, tone: str) -> str:
        """物語全体の世界観が伝わる表紙用プロンプトを生成"""
        tone_desc = {
            "gentle": "gentle and warm",
            "fun": "fun and cheerful",
            "adventure": "adventurous and dynamic",
            "mystery": "mysterious and intriguing",
            "heartwarming": "heartwarming and touching",
            "dreamy": "dreamy and ethereal",
            "magical": "magical and enchanting",
            "brave": "brave and courageous"
        }.get(tone or "gentle", "gentle and warm")

        normalized_keywords = self._normalize_keywords(keywords)
        keywords_text = ", ".join(normalized_keywords)
        keywords_phrase = f"Keywords: {keywords_text}. " if keywords_text else ""

        base = (
            f"Create a striking children's book cover illustration that conveys the overall world of the story titled '{title}'. "
            f"It should evoke the theme and atmosphere of the entire story at a glance. "
            f"Main character: {protagonist_name} (a {protagonist_type}). Setting: {setting_place}. "
            f"Mood: {tone_desc}. {keywords_phrase}"
            f"Avoid any text or typography (no title text). "
            f"Style: children's book cover, iconic, memorable silhouette, strong composition, clear focal point, warm colors. "
            f"Image format: 2:3 aspect ratio (portrait orientation). "
            f"CRITICAL REQUIREMENTS: Absolutely NO text, NO letters, NO words, NO writing, NO captions, NO labels, NO numbers."
        )
        if description:
            base += f" Story summary: {description}."
        return base

    def generate_cover_for_story_plot(self, db: Session, story_plot_id: int, user_id: str = None, prefix: str = "storyplot_i2i_all", reference_image_path: str = None, strength: float = 1.0) -> Dict[str, Any]:
        """表紙画像を生成し、page_00で保存
        
        Args:
            db: データベースセッション
            story_plot_id: StoryPlotのID
            user_id: ユーザーID
            prefix: ファイル名のプレフィックス
            reference_image_path: 参考画像のパス（指定された場合は優先的に使用）
            strength: 参考画像の強度（0.0-1.0、デフォルトは1.0）
        """
        try:
            from app.models.story.story_plot import StoryPlot
            from app.models.story.story_book import StoryBook

            # プロットと、あれば生成済みえほん本体を参照
            story_plot = db.query(StoryPlot).filter(StoryPlot.id == story_plot_id).first()
            if not story_plot:
                raise ValueError(f"StoryPlot ID {story_plot_id} が見つかりません")

            # タイトル・説明・キーワードなど（生成物があれば優先）
            generated = (
                db.query(StoryBook)
                .filter(StoryBook.story_plot_id == story_plot_id)
                .order_by(StoryBook.id.desc())
                .first()
            )

            # storybook_idを取得（story_idとして使用）
            story_id = generated.id if generated else story_plot_id  # storybookが存在しない場合はstory_plot_idを使用

            title = (generated.title if generated and getattr(generated, "title", None) else story_plot.title) or ""
            description = (generated.description if generated and getattr(generated, "description", None) else story_plot.description) or ""
            keywords = (generated.keywords if generated and getattr(generated, "keywords", None) else story_plot.keywords) or []

            story_setting = story_plot.story_setting
            protagonist_name = story_setting.protagonist_name if story_setting else "主人公"
            protagonist_type = story_setting.protagonist_type if story_setting else "子供"
            setting_place = story_setting.setting_place if story_setting else "公園"
            tone = story_setting.tone if story_setting else "gentle"

            prompt = self._create_cover_prompt(
                title=title,
                description=description,
                keywords=keywords,
                protagonist_name=protagonist_name,
                protagonist_type=protagonist_type,
                setting_place=setting_place,
                tone=tone
            )

            print("=" * 80)
            print("【Gemini API プロンプト全文 - 表紙画像生成】")
            print("=" * 80)
            print(prompt)
            print("=" * 80)

            # 参照画像（アップロード画像）の取得
            # 引数で指定されたreference_image_pathを優先的に使用
            api_start = time.time()
            reference_url = reference_image_path
            i2i_prompt = None  # 関数スコープで初期化
            
            # reference_image_pathが指定されていない場合は、story_settingから取得
            if not reference_url:
                if story_setting and getattr(story_setting, "upload_image", None):
                    reference_url = getattr(story_setting.upload_image, "public_url", None)

            if reference_url:
                print(f"🖼️ 参考画像: {reference_url}")
                print(f"💪 強度: {strength} (型: {type(strength).__name__}, 値: {strength})")
                
                # 参照画像のMIME判定
                import os
                if reference_url.startswith("https://") or reference_url.startswith("http://"):
                    ext = os.path.splitext(reference_url.split('?')[0])[1].lower()
                else:
                    ext = os.path.splitext(reference_url)[1].lower()
                
                mime = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                }.get(ext, 'image/jpeg')

                # Image-to-Image生成のためのプロンプト（画像が先にあるので、より直接的に）
                # 日本語訳:
                # 以下の説明で新しいイラストを作成してください: {prompt}
                # 参考画像に示されているキャラクターの外見、コスチューム、スタイルを完全に同じに保ってください
                # 上記で説明された新しいシーンに適応しながら、キャラクターのすべての視覚的特徴
                # （コスチュームの詳細、色、デザインを含む）を保持してください
                i2i_prompt = (
                    f"Create a new illustration with the following description: {prompt}. "
                    f"Maintain the exact same character appearance, costume, and style as shown in the reference image. "
                    f"Preserve all visual characteristics of the character (including costume details, colors, and design) "
                    f"while adapting to the new scene described above."
                )
                
                print("=" * 80)
                print("【Gemini API プロンプト全文 - 表紙Image-to-Image生成】")
                print("=" * 80)
                print(i2i_prompt)
                print("=" * 80)

                ref_base64 = self.encode_image_to_base64(reference_url)
                # 画像を先に、プロンプトを後に配置（Geminiアプリの動作に合わせる）
                response = self.model.generate_content([
                    {"mime_type": mime, "data": ref_base64},
                    i2i_prompt  # 画像の後にプロンプト
                ])
            else:
                response = self.model.generate_content(prompt)
            api_duration = time.time() - api_start
            print(f"⏱️ API処理時間: {api_duration:.2f}秒")

            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                    for idx, part in enumerate(candidate.content.parts):
                        # テキストデータをスキップ
                        if not hasattr(part, 'inline_data') or part.inline_data is None:
                            if hasattr(part, 'text') and part.text:
                                print(f"⚠️ part[{idx}] テキストデータをスキップ: {part.text[:50]}...")
                            continue
                        
                        # MIMEタイプの確認
                        mime = getattr(part.inline_data, 'mime_type', None)
                        if mime and not str(mime).startswith('image/'):
                            print(f"⚠️ part[{idx}] は画像ではないためスキップ (mime={mime})")
                            continue
                        
                        # 画像データを取得
                        image_data = part.inline_data.data
                        
                        # 画像サイズを取得
                        try:
                            image_size = Image.open(BytesIO(image_data)).size
                            image_format = "png"
                        except Exception as e:
                            print(f"⚠️ part[{idx}] 画像バイトが不正のためスキップ: {e}")
                            continue
                        
                        size_bytes = len(image_data)
                        cover_page_content = f"表紙: {title}" if title else "表紙イラスト"
                        
                        # page_index=0でpage_00.pngが自動生成される
                        save_result = self.save_image_to_storage(
                            image_data=image_data,
                            filename="cover.png",
                            user_id=user_id,
                            story_id=story_id,
                            content_type="image/png",
                            page_index=0
                        )
                        
                        if save_result.get("success"):
                            # 使用したプロンプトを決定（i2i_promptが存在する場合はそれを使用）
                            used_prompt = i2i_prompt if i2i_prompt else prompt
                            
                            return {
                                "story_plot_id": story_plot_id,
                                "page_number": 0,
                                "filename": save_result.get("filename", "page_00.png"),
                                "filepath": save_result.get("filepath", save_result.get("gcs_path")),
                                "public_url": save_result.get("public_url"),
                                "size_bytes": size_bytes,
                                "image_size": image_size,
                                "format": image_format,
                                "timestamp": datetime.now().isoformat(),
                                "prompt": used_prompt,
                                "page_content": cover_page_content,
                                "title": title or story_plot.title,
                                "protagonist_name": protagonist_name,
                                "setting_place": setting_place,
                                "description": description,
                                "selected_theme": getattr(story_plot, "selected_theme", None),
                                "reference_image_path": reference_url,
                                "strength": strength if reference_url else None
                            }
                        else:
                            return {"error": save_result.get("error"), "filename": "page_00.png"}

            return {"error": "画像データが見つかりませんでした", "filename": None}

        except Exception as e:
            print(f"❌ 表紙画像生成エラー: {e}")
            return {"error": f"画像生成に失敗しました: {str(e)}", "filename": None}

    def generate_all_pages_for_story_plot(self, db: Session, story_plot_id: int, user_id: str = None, story_pages: int = 5) -> List[Dict[str, Any]]:
        """StoryPlotの全ページの画像を一括生成
        
        Args:
            db: データベースセッション
            story_plot_id: StoryPlotのID
            user_id: ユーザーID
            story_pages: 生成するページ数（3, 5, 7, 10のいずれか、デフォルトは5）
        """
        try:
            from app.models.story.story_plot import StoryPlot
            
            # story_plotを取得
            story_plot = db.query(StoryPlot).filter(StoryPlot.id == story_plot_id).first()
            if not story_plot:
                raise ValueError(f"StoryPlot ID {story_plot_id} が見つかりません")
            
            print(f"🎨 [{datetime.now().strftime('%H:%M:%S')}] StoryPlot全ページ画像生成開始 (ID: {story_plot_id}, ページ数: {story_pages})")
            
            # 全体の処理時間計測開始
            overall_start_time = time.time()
            
            generated_images = []
            
            # 各ページの画像を生成（動的ページ数に対応、最大10ページまで）
            max_pages = min(story_pages, 10)  # 最大10ページまで対応
            for page_num in range(1, max_pages + 1):
                page_content = self._get_page_content(story_plot, page_num)
                
                if page_content:  # 内容があるページのみ生成
                    try:
                        image_info = self.generate_image_for_story_plot_page(
                            db=db,
                            story_plot_id=story_plot_id,
                            page_number=page_num,
                            user_id=user_id
                        )
                        generated_images.append(image_info)
                        print(f"✅ ページ {page_num} 生成成功")
                    except Exception as e:
                        print(f"❌ ページ {page_num} 生成エラー: {e}")
                        generated_images.append({
                            "page_number": page_num,
                            "error": f"画像生成に失敗しました: {str(e)}",
                            "filename": None
                        })
                else:
                    print(f"⚠️ ページ {page_num} は内容が空のためスキップ")
            
            successful_count = len([img for img in generated_images if "error" not in img])
            overall_duration = time.time() - overall_start_time
            print(f"🎉 [{datetime.now().strftime('%H:%M:%S')}] StoryPlot全ページ画像生成完了! 成功: {successful_count}/{max_pages}")
            if max_pages > 0:
                print(f"⏱️ 総処理時間: {overall_duration:.2f}秒 (平均: {overall_duration/max_pages:.2f}秒/ページ)")
            return generated_images
            
        except Exception as e:
            print(f"❌ StoryPlot全ページ画像生成エラー: {e}")
            raise e

    def _get_total_pages(self, story_plot) -> int:
        """StoryPlotから実際に存在するページ数を取得（PlotPage リレーション経由）"""
        if story_plot.pages:
            return len([p for p in story_plot.pages if p.content and p.content.strip()])
        return 5  # デフォルトは5ページ

    def _get_page_content(self, story_plot, page_number: int) -> str:
        """指定されたページの内容を取得（PlotPage リレーション経由）"""
        for page in story_plot.pages:
            if page.page_number == page_number:
                return page.content or ""
        return ""

