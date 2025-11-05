from typing import Dict, Any, List
import time
from sqlalchemy.orm import Session
from app.models.story.story_plot import StoryPlot
from app.models.story.story_setting import StorySetting
from app.models.story.story_book import StoryBook
from .image_to_image_generator import ImageToImageGenerator

class StoryPlotGenerator(ImageToImageGenerator):
    """StoryPlot専用の画像生成機能を提供するクラス"""
    
    def generate_storyplot_image_to_image(
        self, 
        db: Session, 
        story_plot_id: int, 
        page_number: int, 
        reference_image_path: str,
        strength: float = 1.0,
        prefix: str = "storyplot_i2i",
        user_id: str = None
    ) -> Dict[str, Any]:
        """StoryPlot用Image-to-Image生成（1ページずつ）"""
        try:
            # ページごとの処理時間計測開始
            page_start_time = time.time()
            
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
            
            # 総ページ数を計算
            total_pages = self._get_total_pages(story_plot)
            
            # 絵本風のプロンプトを作成（story_plotsデータを活用、アップロード画像の特徴を反映）
            enhanced_prompt = self._create_storyplot_prompt(
                page_content, protagonist_name, protagonist_type, setting_place, story_plot, 
                page_number=page_number, total_pages=total_pages, reference_image_path=reference_image_path
            )
            
            print(f"🎨 StoryPlot Image-to-Image生成開始 (ID: {story_plot_id}, ページ: {page_number})")
            
            # プロンプト全文をターミナルに表示
            print("=" * 80)
            print(f"【Gemini API プロンプト全文 - StoryPlot Image-to-Image生成 ページ {page_number}】")
            print("=" * 80)
            print(enhanced_prompt)
            print("=" * 80)
            
            print(f"🖼️ 参考画像: {reference_image_path}")
            print(f"💪 強度: {strength}")
            
            # Image-to-Image生成を実行
            image_info = self.generate_image_to_image(
                prompt=enhanced_prompt,
                reference_image_path=reference_image_path,
                strength=strength,
                prefix=f"{prefix}_{story_plot_id}_page_{page_number:02d}",
                user_id=user_id,
                story_id=None  # 日付ベースのフォルダに保存
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
            
            # 生成された画像URLをSupabaseのstory_booksテーブルに自動保存
            self._save_image_url_to_storybook(db, story_plot_id, page_number, image_info.get('public_url'), user_id)
            
            return image_info
            
        except Exception as e:
            print(f"❌ StoryPlot Image-to-Image生成エラー: {e}")
            raise e

    def _get_page_content(self, story_plot: StoryPlot, page_number: int) -> str:
        """指定されたページの内容を取得（最大10ページまで対応）"""
        page_map = {
            1: story_plot.page_1,
            2: story_plot.page_2,
            3: story_plot.page_3,
            4: story_plot.page_4,
            5: story_plot.page_5,
            6: getattr(story_plot, 'page_6', None),
            7: getattr(story_plot, 'page_7', None),
            8: getattr(story_plot, 'page_8', None),
            9: getattr(story_plot, 'page_9', None),
            10: getattr(story_plot, 'page_10', None),
        }
        return page_map.get(page_number, "") or ""  # バリデーションはエンドポイント層で行う

    def _get_total_pages(self, story_plot: StoryPlot) -> int:
        """StoryPlotから実際に存在するページ数を取得（最大10ページまで）"""
        for i in range(10, 0, -1):
            page_content = getattr(story_plot, f'page_{i}', None)
            if page_content and page_content.strip():
                return i
        return 5  # デフォルトは5ページ

    def _create_storyplot_prompt(
        self, 
        page_content: str, 
        protagonist_name: str, 
        protagonist_type: str, 
        setting_place: str,
        story_plot: StoryPlot,
        page_number: int = None,
        total_pages: int = None,
        reference_image_path: str = None
    ) -> str:
        """StoryPlot用のプロンプトを作成"""
        # 総ページ数を計算（未指定の場合）
        if total_pages is None:
            total_pages = self._get_total_pages(story_plot)
        
        # ページ数情報をプロンプトに追加
        page_info = ""
        if page_number is not None and total_pages is not None:
            page_info = f" This is page {page_number} of {total_pages} in a {total_pages}-page children's book. "
        
        # 基本の絵本風プロンプト
        enhanced_prompt = (
            f"Create a beautiful children's book illustration for: {page_content}. "
            f"Style: children's book illustration, warm and friendly, bright colors, "
            f"simple and clean design, suitable for children. "
            f"Character: {protagonist_name} (a {protagonist_type}). "
            f"Setting: {setting_place}. "
            f"{page_info}"
            f"Image format: 3:4 aspect ratio. "
            f"MANDATORY: The image must be exactly 3:4 ratio, wide and landscape, NOT portrait or square. "
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
        strength: float = 1.0,
        prefix: str = "storyplot_i2i_all",
        user_id: str = None,
        story_pages: int = 5
    ) -> List[Dict[str, Any]]:
        """StoryPlotの全ページをi2iで一括生成
        
        Args:
            story_pages: 生成するページ数（3, 5, 7, 10のいずれか、デフォルトは5）
        """
        try:
            # 全体の処理時間計測開始
            overall_start_time = time.time()
            
            # story_plotを取得
            story_plot = db.query(StoryPlot).filter(StoryPlot.id == story_plot_id).first()
            if not story_plot:
                raise ValueError(f"StoryPlot ID {story_plot_id} が見つかりません")
            
            print(f"🎨 StoryPlot全ページi2i生成開始 (ID: {story_plot_id}, ページ数: {story_pages})")
            print(f"🖼️ 参考画像: {reference_image_path}")
            print(f"💪 強度: {strength}")
            
            generated_images = []

            # 先に表紙を生成（page_00）: StoryBookGenerator を用いて参照画像ありのカバー生成
            try:
                from .storybook_generator import StoryBookGenerator
                sbg = StoryBookGenerator()
                # 他のページと同じprefix形式を渡す
                cover_info = sbg.generate_cover_for_story_plot(
                    db=db, 
                    story_plot_id=story_plot_id, 
                    user_id=user_id,
                    prefix=prefix
                )
                # 正常に生成できた場合のみ追記（page_number=0 として扱う）
                if cover_info and not cover_info.get("error"):
                    cover_info["page_number"] = 0
                    generated_images.append(cover_info)
                    print("✅ 表紙（page_00）生成成功")
                else:
                    print(f"⚠️ 表紙生成スキップ: {cover_info.get('error') if cover_info else 'unknown error'}")
            except Exception as e:
                print(f"⚠️ 表紙生成エラーのためスキップ: {e}")
            
            # 各ページの画像を生成（動的ページ数に対応、最大10ページまで）
            max_pages = min(story_pages, 10)  # 最大10ページまで対応
            for page_num in range(1, max_pages + 1):
                page_content = self._get_page_content(story_plot, page_num)
                
                if page_content:  # 内容があるページのみ生成
                    try:
                        # 引数で指定された強度を使用
                        
                        # 軽いリトライロジック（失敗時は強度をそのまま再試行）
                        try:
                            image_info = self.generate_storyplot_image_to_image(
                                db=db,
                                story_plot_id=story_plot_id,
                                page_number=page_num,
                                reference_image_path=reference_image_path,
                                strength=strength,
                                prefix=prefix,
                                user_id=user_id
                            )
                        except Exception as first_e:
                            print(f"⏳ ページ {page_num} リトライ: 強度{strength}のまま再試行 ({first_e})")
                            image_info = self.generate_storyplot_image_to_image(
                                db=db,
                                story_plot_id=story_plot_id,
                                page_number=page_num,
                                reference_image_path=reference_image_path,
                                strength=strength,
                                prefix=prefix,
                                user_id=user_id
                            )
                        generated_images.append(image_info)
                        print(f"✅ ページ {page_num} i2i生成成功 (強度: {strength})")
                    except Exception as e:
                        print(f"❌ ページ {page_num} i2i生成エラー: {e}")
                else:
                    print(f"⚠️ ページ {page_num} は内容が空のためスキップ")
            
            # 全体処理時間計算
            overall_duration = time.time() - overall_start_time
            print(f"🎉 StoryPlot全ページi2i生成完了! 生成件数: {len(generated_images)} (表紙+{max_pages}ページ)")
            print(f"⏱️ 全体処理時間: {overall_duration:.2f}秒")
            
            # 生成された画像URLをSupabaseのstory_booksテーブルに自動保存
            self._save_all_images_to_storybook(db, story_plot_id, generated_images, user_id)
            
            return generated_images
            
        except Exception as e:
            print(f"❌ StoryPlot全ページi2i生成エラー: {e}")
            raise e

    def _save_image_url_to_storybook(self, db: Session, story_plot_id: int, page_number: int, image_url: str, user_id: str = None):
        """生成された画像URLをSupabaseのstory_booksテーブルに保存（最大10ページまで対応）"""
        try:
            if not image_url:
                print(f"⚠️ 画像URLが空のためスキップ: story_plot_id={story_plot_id}, page={page_number}")
                return
            
            # story_plotに対応するstory_bookを検索
            storybook = db.query(StoryBook).filter(
                StoryBook.story_plot_id == story_plot_id
            ).first()
            
            if not storybook:
                print(f"⚠️ StoryBookが見つかりません: story_plot_id={story_plot_id}")
                return
            
            # ページ番号に応じてURLを更新（最大10ページまで対応）
            page_image_url_map = {
                1: 'page_1_image_url',
                2: 'page_2_image_url',
                3: 'page_3_image_url',
                4: 'page_4_image_url',
                5: 'page_5_image_url',
                6: 'page_6_image_url',
                7: 'page_7_image_url',
                8: 'page_8_image_url',
                9: 'page_9_image_url',
                10: 'page_10_image_url',
            }
            
            if page_number in page_image_url_map:
                setattr(storybook, page_image_url_map[page_number], image_url)
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
        """全ページの画像URLをSupabaseのstory_booksテーブルに一括保存"""
        try:
            if not generated_images:
                print(f"⚠️ 生成された画像が空のためスキップ: story_plot_id={story_plot_id}")
                return
            
            # story_plotに対応するstory_bookを検索
            storybook = db.query(StoryBook).filter(
                StoryBook.story_plot_id == story_plot_id
            ).first()
            
            if not storybook:
                print(f"⚠️ StoryBookが見つかりません: story_plot_id={story_plot_id}")
                return
            
            # 各画像のURLを保存（最大10ページまで対応）
            updated_pages = []
            page_image_url_map = {
                0: 'cover_image_url',
                1: 'page_1_image_url',
                2: 'page_2_image_url',
                3: 'page_3_image_url',
                4: 'page_4_image_url',
                5: 'page_5_image_url',
                6: 'page_6_image_url',
                7: 'page_7_image_url',
                8: 'page_8_image_url',
                9: 'page_9_image_url',
                10: 'page_10_image_url',
            }
            
            for image_info in generated_images:
                page_number = image_info.get('page_number')
                image_url = image_info.get('public_url')
                
                if page_number is None or not image_url:
                    continue
                
                # ページ番号に応じてURLを更新
                if page_number in page_image_url_map:
                    setattr(storybook, page_image_url_map[page_number], image_url)
                    if page_number == 0:
                        updated_pages.append("cover")
                    else:
                        updated_pages.append(f"page_{page_number}")
                else:
                    print(f"⚠️ 無効なページ番号: {page_number}")
            
            # 画像生成状態を完了に更新
            if updated_pages:
                storybook.image_generation_status = "completed"
            
            db.commit()
            print(f"✅ 全画像URL保存完了: story_plot_id={story_plot_id}, 更新ページ={updated_pages}")
            
        except Exception as e:
            print(f"❌ 全画像URL保存エラー: {e}")
            db.rollback()
            raise e
