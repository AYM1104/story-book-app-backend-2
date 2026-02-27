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
            
            # storybook_idを取得（story_idとして使用）
            storybook = db.query(StoryBook).filter(StoryBook.story_plot_id == story_plot_id).first()
            story_id = storybook.id if storybook else story_plot_id  # storybookが存在しない場合はstory_plot_idを使用
            
            # 指定されたページの内容を取得
            page_content = self._get_page_content(story_plot, page_number)
            
            # ストーリー設定の情報を取得してプロンプトを強化
            story_setting = story_plot.story_setting
            protagonist_name = story_setting.protagonist_name if story_setting else "主人公"
            protagonist_type = story_setting.protagonist_type if story_setting else "子供"
            setting_place = story_setting.setting_place if story_setting else "公園"
            
            # 総ページ数を計算
            total_pages = self._get_total_pages(story_plot)
            
            # 進捗更新: プロンプト生成開始
            self._update_generation_progress(db, story_plot_id, page_number, "prompt", total_pages)
            
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
            
            # 進捗更新: API呼び出し開始
            self._update_generation_progress(db, story_plot_id, page_number, "api_call", total_pages)
            
            # Image-to-Image生成を実行
            image_info = self.generate_image_to_image(
                prompt=enhanced_prompt,
                reference_image_path=reference_image_path,
                strength=strength,
                prefix=f"{prefix}_{story_plot_id}_page_{page_number:02d}",
                user_id=user_id,
                story_id=story_id,  # storybook_idまたはstory_plot_idを使用
                page_index=page_number  # ページ番号を指定してpage_XX.png形式のファイル名を生成
            )
            
            # 進捗更新: ストレージ保存開始
            self._update_generation_progress(db, story_plot_id, page_number, "saving", total_pages)
            
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
            
            # 進捗更新: 完了
            self._update_generation_progress(db, story_plot_id, page_number, "completed", total_pages)
            
            return image_info
            
        except Exception as e:
            print(f"❌ StoryPlot Image-to-Image生成エラー: {e}")
            raise e

    def _get_page_content(self, story_plot: StoryPlot, page_number: int) -> str:
        """指定されたページの内容を取得（PlotPage リレーション経由）"""
        for page in story_plot.pages:
            if page.page_number == page_number:
                return page.content or ""
        return ""
    
    def _get_total_pages(self, story_plot: StoryPlot) -> int:
        """StoryPlotから実際に存在するページ数を取得（PlotPage リレーション経由）"""
        if story_plot.pages:
            return len([p for p in story_plot.pages if p.content and p.content.strip()])
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
        
        # 基本の絵本風プロンプト（スマホ画面向け2:3縦長）
        # 【プロンプト構成】
        # - CONTENT: ページ内容（ストーリー）
        # - STYLE: 絵本イラストのスタイル指定
        # - CHARACTERS & SETTING: キャラクターと舞台設定
        # - FORMAT: 画像のアスペクト比と構図指定
        # - CRITICAL REQUIREMENTS: テキスト除外などの重要な制約
        enhanced_prompt = (
            # 美しい子供向け絵本イラストを作成
            f"Create a beautiful children's book illustration.\n\n"
            
            # 内容: このページのストーリー内容
            f"CONTENT: {page_content}\n\n"
            
            # スタイル: 絵本イラスト、温かく親しみやすい、明るい色彩、シンプルで清潔なデザイン
            f"STYLE:\n"
            f"- Children's book illustration style\n"
            f"- Warm, friendly, and inviting atmosphere\n"
            f"- Bright, vibrant colors\n"
            f"- Simple, clean design suitable for young children\n\n"
            
            # キャラクターと設定: 主人公の名前・種類、舞台となる場所
            f"CHARACTERS & SETTING:\n"
            f"- Main character: {protagonist_name} (a {protagonist_type})\n"
            f"- Setting: {setting_place}\n"
            f"{page_info}\n\n"
            
            # 形式: 2:3の縦長（スマホ表示用）、縦方向の空間を効果的に活用
            f"FORMAT:\n"
            f"- Aspect ratio: 2:3 (portrait/vertical orientation for mobile viewing)\n"
            f"- Composition should be vertical with thoughtful use of vertical space\n\n"
            
            # 重要な要件: テキスト・文字・記号などは一切含めない（純粋なビジュアルイラストのみ）
            f"CRITICAL REQUIREMENTS:\n"
            f"- ABSOLUTELY NO text, letters, words, numbers, symbols, signs, labels, "
            f"captions, speech bubbles, or any form of written language\n"
            f"- This must be a completely text-free visual illustration\n"
            f"- Only include visual elements: characters, objects, and scenic elements"
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
            
            # 総ページ数を計算（表紙 + 実際のページ数）
            total_pages = 1 + min(story_pages, 10)  # 表紙 + 最大10ページ
            
            # 画像生成開始時に進捗を初期化
            storybook = db.query(StoryBook).filter(StoryBook.story_plot_id == story_plot_id).first()
            if storybook:
                # 生成開始を明示的に記録（pending のままにならないようにする）
                storybook.image_generation_status = "generating"
                storybook.generation_progress = {
                    "current_page": 0,
                    "current_step": "prompt",
                    "completed_pages": 0,
                    "total_pages": total_pages
                }
                db.commit()
            
            generated_images = []

            # 先に表紙を生成（page_00）: StoryBookGenerator を用いて参照画像ありのカバー生成
            try:
                from .storybook_generator import StoryBookGenerator
                sbg = StoryBookGenerator()
                # 他のページと同じprefix形式、reference_image_path、strengthを渡す
                cover_info = sbg.generate_cover_for_story_plot(
                    db=db, 
                    story_plot_id=story_plot_id, 
                    user_id=user_id,
                    prefix=prefix,
                    reference_image_path=reference_image_path,
                    strength=strength
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
                        # 1枚目の場合は特にログ出力
                        if page_num == 1:
                            print(f"🔍 [DEBUG] 1枚目（ページ{page_num}）の強度パラメータ: {strength} (型: {type(strength).__name__})")
                        
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

    def _update_generation_progress(
        self, 
        db: Session, 
        story_plot_id: int, 
        current_page: int, 
        current_step: str, 
        total_pages: int,
        completed_pages: int = None
    ):
        """画像生成の進捗を更新
        
        Args:
            current_step: "prompt", "api_call", "saving", "completed"のいずれか
        """
        try:
            storybook = db.query(StoryBook).filter(
                StoryBook.story_plot_id == story_plot_id
            ).first()
            
            if not storybook:
                return
            
            # 完了ページ数を計算（未指定の場合）
            if completed_pages is None:
                completed_pages = (1 if storybook.cover_image_url else 0) + sum(
                    1 for page in storybook.pages if page.image_url
                )
                # 現在処理中のページが完了している場合は除外
                if current_step == "completed":
                    completed_pages = max(0, completed_pages - 1)
            
            # 進捗情報を更新
            storybook.generation_progress = {
                "current_page": current_page,
                "current_step": current_step,
                "completed_pages": completed_pages,
                "total_pages": total_pages
            }
            
            # 画像生成状態を更新
            if current_step == "completed":
                # 全ページ完了かチェック
                if completed_pages + 1 >= total_pages:
                    storybook.image_generation_status = "completed"
                else:
                    storybook.image_generation_status = "generating"
            else:
                storybook.image_generation_status = "generating"
            
            db.commit()
            
            # Live Activity APNs更新を送信（バックグラウンドでもDynamic Islandを更新）
            try:
                from app.service.push_notification_service import push_notification_service
                
                # 進捗率を計算（0.0〜1.0）
                # 15%〜95%の範囲にマッピング（フロントエンドと同じ計算）
                if total_pages > 0:
                    raw_progress = completed_pages / total_pages
                else:
                    raw_progress = 0.0
                mapped_progress = 0.15 + (0.80 * raw_progress)
                mapped_progress = min(mapped_progress, 0.95)
                
                # ステップに応じたメッセージ
                la_status = "in_progress"
                if current_step == "completed" and completed_pages + 1 >= total_pages:
                    progress_text = "絵本が完成しました！"
                    la_status = "completed"
                    mapped_progress = 1.0
                elif current_page == 0:
                    progress_text = "表紙を描いています..."
                else:
                    progress_text = f"絵を描いています... ({current_page}/{total_pages}ページ)"
                
                push_notification_service.send_live_activity_progress(
                    db=db,
                    storybook_id=storybook.id,
                    progress_text=progress_text,
                    progress_value=mapped_progress,
                    status=la_status
                )
            except Exception as la_error:
                print(f"⚠️ Live Activity APNs送信エラー（進捗更新は継続）: {la_error}")
            
        except Exception as e:
            print(f"⚠️ 進捗更新エラー: {e}")
            db.rollback()
    
    def _save_image_url_to_storybook(self, db: Session, story_plot_id: int, page_number: int, image_url: str, user_id: str = None):
        """生成された画像URLを StoryPage テーブルに保存"""
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
            
            # StoryPage を page_number で検索して image_url を更新
            from app.models.story.story_page import StoryPage
            story_page = db.query(StoryPage).filter(
                StoryPage.story_book_id == storybook.id,
                StoryPage.page_number == page_number
            ).first()
            
            if story_page:
                story_page.image_url = image_url
            else:
                print(f"⚠️ StoryPage が見つかりません: storybook_id={storybook.id}, page={page_number}")
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
        """全ページの画像URLを StoryPage テーブルに一括保存"""
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
            
            from app.models.story.story_page import StoryPage
            updated_pages = []
            
            for image_info in generated_images:
                page_number = image_info.get('page_number')
                image_url = image_info.get('public_url')
                
                if page_number is None or not image_url:
                    continue
                
                if page_number == 0:
                    # 表紙画像
                    storybook.cover_image_url = image_url
                    updated_pages.append("cover")
                else:
                    # ページ画像 → StoryPage の image_url を更新
                    story_page = db.query(StoryPage).filter(
                        StoryPage.story_book_id == storybook.id,
                        StoryPage.page_number == page_number
                    ).first()
                    if story_page:
                        story_page.image_url = image_url
                        updated_pages.append(f"page_{page_number}")
                    else:
                        print(f"⚠️ StoryPage が見つかりません: storybook_id={storybook.id}, page={page_number}")
            
            # 画像生成状態を完了に更新
            if updated_pages:
                storybook.image_generation_status = "completed"
            
            db.commit()
            print(f"✅ 全画像URL保存完了: story_plot_id={story_plot_id}, 更新ページ={updated_pages}")
            
        except Exception as e:
            print(f"❌ 全画像URL保存エラー: {e}")
            db.rollback()
            raise e
