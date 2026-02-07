import json
import google.generativeai as genai
from typing import Dict, Any, Optional, List
import os
import traceback
from dotenv import load_dotenv
from app.core.gemini_config import initialize_gemini_model_2_5_flash
from app.features._02_generation_plan.services.story_line.prompt.story_prompts import (
    create_single_story_prompt
)

load_dotenv()

class StoryGeneratorService:
    """Gemini 2.5 Flashを使用してストーリーを生成するサービス"""

    def __init__(self):
        # Gemini APIの設定（共通のユーティリティ関数を使用）
        self.model = initialize_gemini_model_2_5_flash('gemini-2.5-flash')

    def generate_single_story(self, story_setting: Dict[str, Any], selected_theme: str, story_pages: int = 5, language: str = "ja") -> Dict[str, Any]:
        """選択されたテーマの物語本文を生成
        
        Args:
            story_setting: ストーリー設定の辞書
            selected_theme: 選択されたテーマのタイトル
            story_pages: 生成するページ数（3, 5, 7, 10のいずれか、デフォルトは5）
            language: 出力言語 ("ja" または "en")
        """
        
        # デバッグ: 受け取ったページ数と言語を確認
        print(f"🔍 generate_single_story 受け取ったページ数: {story_pages}, 言語: {language}")
        
        protagonist_name = story_setting.get("protagonist_name", "主人公")
        protagonist_type = story_setting.get("protagonist_type", "子供")
        setting_place = story_setting.get("setting_place", "公園")
        tone = story_setting.get("tone", "gentle")
        target_age = story_setting.get("target_age", "preschool")
        reading_level = story_setting.get("reading_level", "hiragana_only")

        # プロンプトを作成
        prompt = create_single_story_prompt(
            protagonist_name, protagonist_type, setting_place, 
            tone, target_age, reading_level, selected_theme, story_pages, language
        )

        try:
            # プロンプト全文をターミナルに表示
            print("=" * 80)
            print("【Gemini API プロンプト全文 - 単一ストーリー生成】")
            print("=" * 80)
            print(prompt)
            print("========================== 物語本文の生成完了 ==========================")
            print()  # 改行を追加
            
            # Gemini 2.5 Flashで単一ストーリーを生成
            response = self.model.generate_content(prompt)
            
            # レスポンスの検証
            if not response or not hasattr(response, 'text') or not response.text:
                raise ValueError("Gemini APIからのレスポンスが空です")
            
            # レスポンスの内容をログに出力（デバッグ用）
            print("=" * 80)
            print("【Gemini API レスポンス（全文）】")
            print("=" * 80)
            print(response.text)
            print("=" * 80)
            print()  # 改行を追加
            
            story_data = self._parse_single_story_response(response.text)
            return story_data

        except ValueError as ve:
            # JSON解析エラーなど、ValueErrorの場合は詳細を出力してからフォールバック
            print(f"❌ Gemini API エラー（ValueError）: {ve}")
            print(f"エラーのトレースバック: {traceback.format_exc()}")
            # エラー時はフォールバック
            return self._generate_fallback_single_story(protagonist_name, protagonist_type, setting_place, selected_theme, story_pages, language)
        except Exception as e:
            print(f"❌ Gemini API エラー（予期しないエラー）: {e}")
            print(f"エラーのトレースバック: {traceback.format_exc()}")
            # エラー時はフォールバック
            return self._generate_fallback_single_story(protagonist_name, protagonist_type, setting_place, selected_theme, story_pages, language)




    def _parse_complete_story_response(self, response_text: str) -> Dict[str, Any]:
        """完全なストーリー生成のレスポンスをパース"""
        try:
            # JSON部分を抽出（複数の方法を試行）
            json_text = None
            
            # 方法1: ```json コードブロックから抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end > json_start:
                    json_text = response_text[json_start:json_end].strip()
            
            # 方法2: ``` コードブロックから抽出
            if not json_text and "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.rfind("```")
                if json_end > json_start:
                    json_text = response_text[json_start:json_end].strip()
            
            # 方法3: { から始まる最初のJSONオブジェクトを探す（ロバストな実装）
            if not json_text:
                start_idx = response_text.find("{")
                if start_idx != -1:
                    # スタックを使用してネストと文字列内のブレースを正しく処理
                    stack = []
                    in_string = False
                    escape = False
                    end_idx = -1
                    
                    for i in range(start_idx, len(response_text)):
                        char = response_text[i]
                        
                        if in_string:
                            if escape:
                                escape = False
                            elif char == '\\':
                                escape = True
                            elif char == '"':
                                in_string = False
                        else:
                            if char == '"':
                                in_string = True
                            elif char == '{':
                                stack.append('{')
                            elif char == '}':
                                if stack:
                                    stack.pop()
                                    if not stack:
                                        # 対応する閉じ括弧が見つかった
                                        end_idx = i + 1
                                        break
                                else:
                                    # スタックが空なのに閉じ括弧が来た（無視またはエラー）
                                    pass
                    
                    if end_idx > start_idx:
                        json_text = response_text[start_idx:end_idx].strip()
            
            # 方法4: そのまま使用
            if not json_text:
                json_text = response_text.strip()
            
            # JSONの前後の不要な文字を削除
            json_text = json_text.strip()
            # 先頭の不要な文字を削除（説明文など）
            if json_text.startswith("JSON"):
                json_text = json_text[4:].strip()
            if json_text.startswith(":"):
                json_text = json_text[1:].strip()
            
            # JSONをパース
            story_data = json.loads(json_text)
            return story_data

        except json.JSONDecodeError as e:
            print(f"❌ JSON解析エラー: {e}")
            print(f"エラー位置: 行 {e.lineno}, 列 {e.colno}")
            print(f"レスポンステキスト全体の長さ: {len(response_text)}文字")
            print(f"レスポンステキスト（全文）:")
            print(response_text)
            # デバッグ用: 抽出されたJSONテキストも表示
            if 'json_text' in locals():
                print(f"抽出されたJSONテキスト（全文）:")
                print(json_text if json_text else 'None')
            raise ValueError(f"Geminiからのレスポンスが正しいJSON形式ではありません: {str(e)}")
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
            print(f"レスポンステキスト（全文）:")
            print(response_text)
            raise ValueError(f"レスポンスの解析に失敗しました: {str(e)}")

    def _parse_single_story_response(self, response_text: str) -> Dict[str, Any]:
        """単一ストーリー生成のレスポンスをパース"""
        return self._parse_complete_story_response(response_text)


    def _generate_fallback_single_story(self, protagonist_name: str, protagonist_type: str, setting_place: str, selected_theme: str, story_pages: int = 5, language: str = "ja") -> Dict[str, Any]:
        """エラー時のフォールバック用単一ストーリー"""
        # ページ数に応じたデフォルトストーリーを生成
        fallback_pages = []
        
        if language == "en":
            fallback_texts = [
                f"Once upon a time, {protagonist_name} was playing at the {setting_place}.",
                "Something wonderful happened there.",
                "The hero bravely faced the challenge.",
                "With the help of friends, the problem was solved.",
                "An important lesson was learned and growth happened.",
                "A new adventure began.",
                "Overcoming difficulties, they grew even more.",
                "Gratitude was shared with everyone around.",
                "So much was learned, and hearts became richer.",
                "And every day became more joyful."
            ]
            title = f"{protagonist_name}'s {selected_theme}"
            continuation_text = "The story continues."
        else:
            fallback_texts = [
                f"むかしむかし、{protagonist_name}が{setting_place}で遊んでいました。",
                "そこで素敵な出来事が起こりました。",
                "主人公は勇気を出して立ち向かいました。",
                "友達と協力して問題を解決しました。",
                "大切なことを学んで成長しました。",
                "新しい冒険が始まりました。",
                "困難を乗り越えて、さらに成長しました。",
                "周りの人たちに感謝の気持ちを伝えました。",
                "たくさんのことを学び、心が豊かになりました。",
                "そして、毎日が楽しくなりました。"
            ]
            title = f"{protagonist_name}の{selected_theme}"
            continuation_text = "物語が続きます。"
        
        for i in range(1, min(story_pages + 1, 11)):
            if i <= len(fallback_texts):
                fallback_pages.append({f"page_{i}": fallback_texts[i - 1]})
            else:
                fallback_pages.append({f"page_{i}": continuation_text})
        
        return {
            "title": title,
            "story_pages": fallback_pages
        }

    def generate_story_setting_from_analysis(self, meta_data: Dict[str, Any], upload_image_id: int) -> Dict[str, Any]:
        """画像解析結果（labels/objects/text）から物語設定を推定して返す"""
        # ラベル群
        labels: List[str] = []
        raw_labels = meta_data.get("labels")
        if isinstance(raw_labels, list):
            # Visionの形式に幅を持たせる（文字列配列 or {description: str} 配列）
            for item in raw_labels:
                if isinstance(item, str):
                    labels.append(item)
                elif isinstance(item, dict) and "description" in item:
                    labels.append(str(item["description"]))

        # オブジェクト群
        objects: List[str] = []
        raw_objects = meta_data.get("objects")
        if isinstance(raw_objects, list):
            for item in raw_objects:
                if isinstance(item, str):
                    objects.append(item)
                elif isinstance(item, dict) and "name" in item:
                    objects.append(str(item["name"]))

        # テキスト群
        texts: List[str] = []
        raw_text = meta_data.get("text")
        if isinstance(raw_text, list):
            for t in raw_text:
                if isinstance(t, str):
                    texts.append(t)
                elif isinstance(t, dict) and "description" in t:
                    texts.append(str(t["description"]))

        # 顔検出結果
        faces: List[Dict[str, Any]] = []
        raw_faces = meta_data.get("faces")
        if isinstance(raw_faces, list):
            faces = raw_faces

        # 推定ロジック（より詳細な判定）
        protagonist_type = "子供"
        
        # facesの情報を取得（人間の顔が検出されているかチェック）
        has_human_face = len(faces) > 0
        
        # 性別判定を試みる（失敗しても「子供」のままで問題なし）
        # 人間の顔が検出されている場合、または子供の絵の場合
        lower_labels = [l.lower() for l in labels]
        has_human_face_or_drawing = (
            has_human_face or 
            any(k in lower_labels for k in ["cartoon", "animation", "animated cartoon", "fictional character", "toy", "drawing", "art", "illustration"])
        )
        
        if has_human_face_or_drawing:
            try:
                print(f"性別判定を試行（失敗してもOK）: upload_image_id={upload_image_id}")
                # Note: Cloud Run環境ではfile_pathが存在しないため、この処理は失敗します
                # 失敗した場合は「子供」のままとし、後でユーザーに質問で聞きます
                from sqlalchemy.orm import Session
                from app.database.session import get_db
                from app.features._01_image_upload.models.images import UploadImages
                
                db_gen = get_db()
                db = next(db_gen)
                try:
                    upload_image = db.query(UploadImages).filter(UploadImages.id == upload_image_id).first()
                    if upload_image and upload_image.file_path:
                        # 顔検出がある場合は写真用、ない場合は絵用のメソッドを使用
                        if has_human_face:
                            gender_result = self._detect_gender_with_gemini(upload_image.file_path)
                        else:
                            gender_result = self._detect_gender_from_drawing(upload_image.file_path)
                        
                        if gender_result in ["男の子", "女の子"]:
                            protagonist_type = gender_result
                            print(f"性別判定成功: {gender_result}")
                finally:
                    db.close()
            except Exception as e:
                print(f"性別判定スキップ（エラー）: {e}")
                print("→ デフォルト「子供」を使用し、後でユーザーに質問します")
        
        # labelsから判定（従来のロジック）
        if any(k in lower_labels for k in ["cat", "dog", "animal"]):
            protagonist_type = "動物"
        elif any(k in lower_labels for k in ["robot", "machine"]):
            protagonist_type = "ロボット"
        
        # objectsからも判定（より正確な判定のため）
        lower_objects = [o.lower() for o in objects]
        
        # 人間の顔が検出されている場合は、動物の着ぐるみでも「子供」として判定
        if has_human_face:
            # 人間の顔がある場合、動物の着ぐるみでも子供として扱う
            if any(k in lower_objects for k in ["robot", "machine", "vehicle", "car", "truck", "airplane", "helicopter", "boat", "ship", "train", "bicycle", "motorcycle"]):
                protagonist_type = "ロボット"
            else:
                protagonist_type = "子供"  # 動物の着ぐるみでも人間の顔があれば子供
        else:
            # 人間の顔がない場合の判定
            # カートゥーン・アニメーション・架空キャラクターの場合は着ぐるみを着た子供の可能性が高い
            is_cartoon_character = any(k in lower_labels for k in ["cartoon", "animation", "animated cartoon", "fictional character", "toy"])
            
            if is_cartoon_character and any(k in lower_objects for k in ["animal", "cat", "dog", "bird", "fish", "bear", "rabbit", "mouse", "lion", "tiger", "elephant", "monkey", "panda", "fox", "wolf", "deer", "horse", "cow", "pig", "sheep", "goat", "duck", "chicken", "frog", "turtle", "snake", "butterfly", "bee", "spider"]):
                protagonist_type = "子供"  # カートゥーン + 動物 = 着ぐるみを着た子供
            elif any(k in lower_objects for k in ["animal", "cat", "dog", "bird", "fish", "bear", "rabbit", "mouse", "lion", "tiger", "elephant", "monkey", "panda", "fox", "wolf", "deer", "horse", "cow", "pig", "sheep", "goat", "duck", "chicken", "frog", "turtle", "snake", "butterfly", "bee", "spider"]):
                protagonist_type = "動物"  # リアルな動物
            elif any(k in lower_objects for k in ["robot", "machine", "vehicle", "car", "truck", "airplane", "helicopter", "boat", "ship", "train", "bicycle", "motorcycle"]):
                protagonist_type = "ロボット"

        setting_place = "公園"
        if any(k in lower_objects for k in ["house", "home"]):
            setting_place = "家"
        elif any(k in lower_objects for k in ["forest", "tree"]):
            setting_place = "森"
        elif any(k in lower_objects for k in ["sea", "ocean"]):
            setting_place = "海"
        elif any(k in lower_objects for k in ["mountain", "hill"]):
            setting_place = "山"

        protagonist_name = "主人公"
        if texts:
            cand = texts[0]
            if isinstance(cand, str) and 1 <= len(cand) <= 12:
                protagonist_name = cand

        return {
            "title_suggestion": f"{protagonist_name}の冒険",
            "protagonist_name": protagonist_name,
            "protagonist_type": protagonist_type,
            "setting_place": setting_place,
            "tone": "gentle",
            "target_age": "preschool",
            "language": "japanese",
            "reading_level": "hiragana_only",
            "style_guideline": "優しく温かい雰囲気で、子供が楽しめる内容にする"
        }

    def _detect_gender_with_gemini(self, image_path: str) -> str:
        """Gemini APIを使って画像から性別を判定（写真用）"""
        try:
            import base64
            from PIL import Image
            
            # 画像を読み込んでbase64エンコード
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Gemini APIで性別判定
            prompt = """
            この画像に写っている子供の性別を判定してください。
            以下のいずれかで回答してください：
            - 男の子
            - 女の子
            - 判定不可
            
            顔の特徴、髪型、服装、表情などを総合的に判断してください。
            """
            
            # プロンプト全文をターミナルに表示
            print("=" * 80)
            print("【Gemini API プロンプト全文 - 性別判定（写真用）】")
            print("=" * 80)
            print(prompt)
            print("=" * 80)
            
            # Gemini APIで画像解析
            response = self.model.generate_content([
                prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": image_data
                }
            ])
            
            result = response.text.strip()
            
            # 結果を正規化
            if "男の子" in result or "男" in result:
                return "男の子"
            elif "女の子" in result or "女" in result:
                return "女の子"
            else:
                return "子供"  # 判定不可の場合はデフォルト
                
        except Exception as e:
            print(f"Gemini性別判定エラー: {e}")
            return "子供"  # エラー時はデフォルト

    def _detect_gender_from_drawing(self, image_path: str) -> str:
        """Gemini APIを使って子供が描いた絵から主人公の性別を判定"""
        try:
            import base64
            from PIL import Image
            
            # 画像を読み込んでbase64エンコード
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Gemini APIで絵から性別判定
            prompt = """
            この画像は子供が描いた絵です。絵に描かれている主人公（人物）の性別を判定してください。
            以下のいずれかで回答してください：
            - 男の子
            - 女の子
            - 判定不可
            
            以下の要素を総合的に判断してください：
            - 髪型（短髪、長髪、ポニーテールなど）
            - 服装の色（青、ピンク、赤、緑など）
            - 服装のスタイル（ズボン、スカート、ドレスなど）
            - アクセサリー（リボン、帽子など）
            - 全体的な色使いや雰囲気
            - 絵の特徴（子供らしい描き方、色使いなど）
            
            子供が描いた絵なので、はっきりしない部分もありますが、できるだけ判定してください。
            """
            
            # プロンプト全文をターミナルに表示
            print("=" * 80)
            print("【Gemini API プロンプト全文 - 性別判定（絵用）】")
            print("=" * 80)
            print(prompt)
            print("=" * 80)
            
            # Gemini APIで画像解析
            response = self.model.generate_content([
                prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": image_data
                }
            ])
            
            result = response.text.strip()
            print(f"絵からの性別判定結果: {result}")
            
            # 結果を正規化
            if "男の子" in result or "男" in result:
                return "男の子"
            elif "女の子" in result or "女" in result:
                return "女の子"
            else:
                return "子供"  # 判定不可の場合はデフォルト
                
        except Exception as e:
            print(f"絵からの性別判定エラー: {e}")
            return "子供"  # エラー時はデフォルト

# シングルトンインスタンス
story_generator_service = StoryGeneratorService()

