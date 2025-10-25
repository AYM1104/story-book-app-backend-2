from typing import Dict, Any, List
import time
from sqlalchemy.orm import Session
from app.models.story.supabase_story_plot import SupabaseStoryPlot
from app.models.story.supabase_story_setting import SupabaseStorySetting
from app.models.story.supabase_generated_story_book import SupabaseGeneratedStoryBook
from .image_to_image_generator import ImageToImageGenerator

class StoryPlotGenerator(ImageToImageGenerator):
    """StoryPlot専用の画像生成機能を提供するクラス"""
    
    def generate_storyplot_image_to_image(
        self, 
        db: Session, 
        story_plot_id: int, 
        page_number: int, 
        reference_image_path: str,
        strength: float = 0.8,
        prefix: str = "storyplot_i2i",
        user_id: str = None
    ) -> Dict[str, Any]:
        """StoryPlot用Image-to-Image生成（1ページずつ）"""
        try:
            # ページごとの処理時間計測開始
            page_start_time = time.time()
            
            # story_plotを取得
            story_plot = db.query(SupabaseStoryPlot).filter(SupabaseStoryPlot.id == story_plot_id).first()
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
                prefix=f"{prefix}_{story_plot_id}_page_{page_number}",
                user_id=user_id
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
            
            # ページ処理時間計算
            page_duration = time.time() - page_start_time
            print(f"📄 ページ {page_number} 処理時間: {page_duration:.2f}秒")
            
            print(f"✅ StoryPlot Image-to-Image生成成功: {image_info['filename']}")
            
            # 生成された画像URLをSupabaseのgenerated_story_booksテーブルに自動保存
            self._save_image_url_to_storybook(db, story_plot_id, page_number, image_info.get('public_url'), user_id)
            
            return image_info
            
        except Exception as e:
            print(f"❌ StoryPlot Image-to-Image生成エラー: {e}")
            raise e

    def _get_page_content(self, story_plot: SupabaseStoryPlot, page_number: int) -> str:
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
        story_plot: SupabaseStoryPlot,
        reference_image_path: str = None
    ) -> str:
        """StoryPlot用のプロンプトを作成"""
        # 基本の絵本風プロンプト
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
        
        return enhanced_prompt

    def generate_storyplot_all_pages_i2i(
        self, 
        db: Session, 
        story_plot_id: int, 
        reference_image_path: str,
        strength: float = 0.8,
        prefix: str = "storyplot_i2i_all",
        user_id: str = None
    ) -> List[Dict[str, Any]]:
        """StoryPlotの全ページをi2iで一括生成"""
        try:
            # 全体の処理時間計測開始
            overall_start_time = time.time()
            
            # story_plotを取得
            story_plot = db.query(SupabaseStoryPlot).filter(SupabaseStoryPlot.id == story_plot_id).first()
            if not story_plot:
                raise ValueError(f"StoryPlot ID {story_plot_id} が見つかりません")
            
            print(f"🎨 StoryPlot全ページi2i生成開始 (ID: {story_plot_id})")
            print(f"🖼️ 参考画像: {reference_image_path}")
            print(f"💪 強度: {strength}")
            
            generated_images = []
            
            # 各ページの画像を生成（ページごとに強度を調整）
            for page_num in range(1, 6):  # 1-5ページ
                page_content = self._get_page_content(story_plot, page_num)
                
                if page_content:  # 内容があるページのみ生成
                    try:
                        # すべてのページで同一の最大強度を使用
                        page_strength = 1.0
                        
                        # 軽いリトライロジック（失敗時は強度を少し下げて再試行）
                        try:
                            image_info = self.generate_storyplot_image_to_image(
                                db=db,
                                story_plot_id=story_plot_id,
                                page_number=page_num,
                                reference_image_path=reference_image_path,
                                strength=page_strength,
                                prefix=f"{prefix}_{story_plot_id}",
                                user_id=user_id
                            )
                        except Exception as first_e:
                            print(f"⏳ ページ {page_num} リトライ: 強度を0.8に下げて再試行 ({first_e})")
                            image_info = self.generate_storyplot_image_to_image(
                                db=db,
                                story_plot_id=story_plot_id,
                                page_number=page_num,
                                reference_image_path=reference_image_path,
                                strength=0.8,
                                prefix=f"{prefix}_{story_plot_id}",
                                user_id=user_id
                            )
                        generated_images.append(image_info)
                        print(f"✅ ページ {page_num} i2i生成成功 (強度: {page_strength})")
                    except Exception as e:
                        print(f"❌ ページ {page_num} i2i生成エラー: {e}")
                else:
                    print(f"⚠️ ページ {page_num} は内容が空のためスキップ")
            
            # 全体処理時間計算
            overall_duration = time.time() - overall_start_time
            print(f"🎉 StoryPlot全ページi2i生成完了! 成功: {len(generated_images)}/5")
            print(f"⏱️ 全体処理時間: {overall_duration:.2f}秒")
            
            # 生成された画像URLをSupabaseのgenerated_story_booksテーブルに自動保存
            self._save_all_images_to_storybook(db, story_plot_id, generated_images, user_id)
            
            return generated_images
            
        except Exception as e:
            print(f"❌ StoryPlot全ページi2i生成エラー: {e}")
            raise e

    def _save_image_url_to_storybook(self, db: Session, story_plot_id: int, page_number: int, image_url: str, user_id: str = None):
        """生成された画像URLをSupabaseのgenerated_story_booksテーブルに保存"""
        try:
            if not image_url:
                print(f"⚠️ 画像URLが空のためスキップ: story_plot_id={story_plot_id}, page={page_number}")
                return
            
            # story_plotに対応するgenerated_story_bookを検索
            storybook = db.query(SupabaseGeneratedStoryBook).filter(
                SupabaseGeneratedStoryBook.story_plot_id == story_plot_id
            ).first()
            
            if not storybook:
                print(f"⚠️ GeneratedStoryBookが見つかりません: story_plot_id={story_plot_id}")
                return
            
            # ページ番号に応じてURLを更新
            if page_number == 1:
                storybook.page_1_image_url = image_url
            elif page_number == 2:
                storybook.page_2_image_url = image_url
            elif page_number == 3:
                storybook.page_3_image_url = image_url
            elif page_number == 4:
                storybook.page_4_image_url = image_url
            elif page_number == 5:
                storybook.page_5_image_url = image_url
            else:
                print(f"⚠️ 無効なページ番号: {page_number}")
                return
            
            # 画像生成状態を更新
            storybook.image_generation_status = "generating"
            
            db.commit()
            print(f"✅ 画像URL保存完了: story_plot_id={story_plot_id}, page={page_number}, url={image_url}")
            
        except Exception as e:
            print(f"❌ 画像URL保存エラー: {e}")
            db.rollback()
            raise e

    def _save_all_images_to_storybook(self, db: Session, story_plot_id: int, generated_images: List[Dict], user_id: str = None):
        """全ページの画像URLをSupabaseのgenerated_story_booksテーブルに一括保存"""
        try:
            if not generated_images:
                print(f"⚠️ 生成された画像が空のためスキップ: story_plot_id={story_plot_id}")
                return
            
            # story_plotに対応するgenerated_story_bookを検索
            storybook = db.query(SupabaseGeneratedStoryBook).filter(
                SupabaseGeneratedStoryBook.story_plot_id == story_plot_id
            ).first()
            
            if not storybook:
                print(f"⚠️ GeneratedStoryBookが見つかりません: story_plot_id={story_plot_id}")
                return
            
            # 各画像のURLを保存
            updated_pages = []
            for image_info in generated_images:
                page_number = image_info.get('page_number')
                image_url = image_info.get('public_url')
                
                if not page_number or not image_url:
                    continue
                
                # ページ番号に応じてURLを更新
                if page_number == 1:
                    storybook.page_1_image_url = image_url
                    updated_pages.append("page_1")
                elif page_number == 2:
                    storybook.page_2_image_url = image_url
                    updated_pages.append("page_2")
                elif page_number == 3:
                    storybook.page_3_image_url = image_url
                    updated_pages.append("page_3")
                elif page_number == 4:
                    storybook.page_4_image_url = image_url
                    updated_pages.append("page_4")
                elif page_number == 5:
                    storybook.page_5_image_url = image_url
                    updated_pages.append("page_5")
            
            # 画像生成状態を完了に更新
            if updated_pages:
                storybook.image_generation_status = "completed"
            
            db.commit()
            print(f"✅ 全画像URL保存完了: story_plot_id={story_plot_id}, 更新ページ={updated_pages}")
            
        except Exception as e:
            print(f"❌ 全画像URL保存エラー: {e}")
            db.rollback()
            raise e
