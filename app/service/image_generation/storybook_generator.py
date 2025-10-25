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
        print(f"📚 [{datetime.now().strftime('%H:%M:%S')}] 絵本画像生成開始... (ページ数: {len(story_pages)})")
        
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
                # ページごとの処理時間計測開始
                page_start_time = time.time()
                print(f"\n📝 [{datetime.now().strftime('%H:%M:%S')}] ページ {i}/{len(prompts)} 生成開始...")
                
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
            from app.models.story.supabase_story_plot import SupabaseStoryPlot
            
            # story_plotを取得
            story_plot = db.query(SupabaseStoryPlot).filter(SupabaseStoryPlot.id == story_plot_id).first()
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
            
            # 絵本風のプロンプトを作成
            enhanced_prompt = (
                f"Create a beautiful children's book illustration for: {page_content}. "
                f"Style: children's book illustration, warm and friendly, bright colors, "
                f"simple and clean design, suitable for children. "
                f"Character: {protagonist_name} (a {protagonist_type}). "
                f"Setting: {setting_place}. "
                f"Image format: 16:9 aspect ratio (landscape orientation), horizontal composition. "
                f"MANDATORY: The image must be exactly 16:9 ratio, wide and landscape, NOT portrait or square. "
                f"The composition should be horizontal with elements spread across the width. "
                f"CRITICAL REQUIREMENTS: Absolutely NO text, NO letters, NO words, NO writing, NO captions, "
                f"NO speech bubbles, NO signs, NO labels, NO symbols, NO numbers, NO typography, "
                f"NO written language of any kind. This must be a pure visual illustration only. "
                f"The image should be completely text-free and contain only visual elements, characters, "
                f"objects, and scenes without any written content whatsoever."
            )
            
            print(f"🎨 [{datetime.now().strftime('%H:%M:%S')}] StoryPlotページ画像生成開始 (ID: {story_plot_id}, ページ: {page_number})")
            print(f"📝 プロンプト: {enhanced_prompt[:100]}...")
            
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
                                    content_type="image/png"
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

    def generate_all_pages_for_story_plot(self, db: Session, story_plot_id: int, user_id: str = None) -> List[Dict[str, Any]]:
        """StoryPlotの全ページの画像を一括生成"""
        try:
            from app.models.story.supabase_story_plot import SupabaseStoryPlot
            
            # story_plotを取得
            story_plot = db.query(SupabaseStoryPlot).filter(SupabaseStoryPlot.id == story_plot_id).first()
            if not story_plot:
                raise ValueError(f"StoryPlot ID {story_plot_id} が見つかりません")
            
            print(f"🎨 [{datetime.now().strftime('%H:%M:%S')}] StoryPlot全ページ画像生成開始 (ID: {story_plot_id})")
            
            # 全体の処理時間計測開始
            overall_start_time = time.time()
            
            generated_images = []
            
            # 各ページの画像を生成
            for page_num in range(1, 6):  # 1-5ページ
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
            print(f"🎉 [{datetime.now().strftime('%H:%M:%S')}] StoryPlot全ページ画像生成完了! 成功: {successful_count}/5")
            print(f"⏱️ 総処理時間: {overall_duration:.2f}秒 (平均: {overall_duration/5:.2f}秒/ページ)")
            return generated_images
            
        except Exception as e:
            print(f"❌ StoryPlot全ページ画像生成エラー: {e}")
            raise e

    def _get_page_content(self, story_plot, page_number: int) -> str:
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
            return ""
