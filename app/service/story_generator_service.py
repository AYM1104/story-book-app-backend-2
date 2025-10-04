import json
import google.generativeai as genai
from typing import Dict, Any, Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

class StoryGeneratorService:
    """Gemini 2.5 Flashを使用してストーリーを生成するサービス"""

    def __init__(self):
        # Gemini APIの設定
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEYまたはGOOGLE_API_KEYが設定されていません")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def generate_complete_story(self, story_setting: Dict[str, Any]) -> Dict[str, Any]:
        """テーマ案と物語本文を一緒に生成"""
        
        protagonist_name = story_setting.get("protagonist_name", "主人公")
        protagonist_type = story_setting.get("protagonist_type", "子供")
        setting_place = story_setting.get("setting_place", "公園")
        tone = story_setting.get("tone", "gentle")
        target_age = story_setting.get("target_age", "preschool")
        reading_level = story_setting.get("reading_level", "hiragana_only")

        # プロンプトを作成
        prompt = self._create_complete_story_prompt(
            protagonist_name, protagonist_type, setting_place, 
            tone, target_age, reading_level
        )

        try:
            # Gemini 2.5 Flashで完全なストーリーを生成
            response = self.model.generate_content(prompt)
            story_data = self._parse_complete_story_response(response.text)
            return story_data

        except Exception as e:
            print(f"Gemini API エラー: {e}")
            # エラー時はフォールバック
            return self._generate_fallback_complete_story(protagonist_name, protagonist_type, setting_place, tone)

    def generate_single_story(self, story_setting: Dict[str, Any], selected_theme: str) -> Dict[str, Any]:
        """選択されたテーマの物語本文を生成"""
        
        protagonist_name = story_setting.get("protagonist_name", "主人公")
        protagonist_type = story_setting.get("protagonist_type", "子供")
        setting_place = story_setting.get("setting_place", "公園")
        tone = story_setting.get("tone", "gentle")
        target_age = story_setting.get("target_age", "preschool")
        reading_level = story_setting.get("reading_level", "hiragana_only")

        # プロンプトを作成
        prompt = self._create_single_story_prompt(
            protagonist_name, protagonist_type, setting_place, 
            tone, target_age, reading_level, selected_theme
        )

        try:
            # Gemini 2.5 Flashで単一ストーリーを生成
            response = self.model.generate_content(prompt)
            story_data = self._parse_single_story_response(response.text)
            return story_data

        except Exception as e:
            print(f"Gemini API エラー: {e}")
            # エラー時はフォールバック
            return self._generate_fallback_single_story(protagonist_name, protagonist_type, setting_place, selected_theme)

    def _create_complete_story_prompt(self, protagonist_name: str, protagonist_type: str, 
                                    setting_place: str, tone: str, target_age: str, reading_level: str) -> str:
        """完全なストーリー生成用のプロンプトを作成"""
        
        tone_descriptions = {
            "gentle": "優しく温かい雰囲気",
            "fun": "楽しく明るい雰囲気", 
            "adventure": "冒険的でワクワクする雰囲気",
            "mystery": "謎解きでドキドキする雰囲気"
        }
        
        age_descriptions = {
            "preschool": "3-6歳の未就学児向け",
            "elementary_low": "7-9歳の小学生低学年向け"
        }

        prompt = f"""
あなたは子供向けの絵本のストーリー企画者です。
以下の設定を元に、3つの異なるテーマの物語案と、それぞれの完全な物語本文（5ページ）を作成してください。

【基本設定】
- 主人公: {protagonist_name}（{protagonist_type}）
- 舞台: {setting_place}
- 雰囲気: {tone_descriptions.get(tone, '優しく温かい雰囲気')}
- 対象年齢: {age_descriptions.get(target_age, '3-6歳の未就学児向け')}
- 読みやすさ: {reading_level}

【要求事項】
1. 3つの異なるテーマ（冒険、友情、発見など）
2. 各テーマで5ページの完全な物語本文
3. 子供が楽しめる内容
4. 教育的な要素を含む
5. 読みやすく、感情に訴える文章

【出力形式】
以下のJSON形式で出力してください：
{{
  "theme_options": {{
    "theme1": {{
      "theme_id": "adventure",
      "title": "タイトル",
      "description": "物語の概要",
      "keywords": ["キーワード1", "キーワード2", "キーワード3"]
    }},
    "theme2": {{...}},
    "theme3": {{...}}
  }},
  "generated_stories": {{
    "theme1": {{
      "title": "タイトル",
      "story_pages": [
        {{"page_1": "1ページ目の完全な物語本文"}},
        {{"page_2": "2ページ目の完全な物語本文"}},
        {{"page_3": "3ページ目の完全な物語本文"}},
        {{"page_4": "4ページ目の完全な物語本文"}},
        {{"page_5": "5ページ目の完全な物語本文"}}
      ]
    }},
    "theme2": {{...}},
    "theme3": {{...}}
  }}
}}

必ずJSON形式で出力し、他の説明文は含めないでください。
"""

        return prompt

    def _create_single_story_prompt(self, protagonist_name: str, protagonist_type: str, 
                                  setting_place: str, tone: str, target_age: str, reading_level: str, selected_theme: str) -> str:
        """単一ストーリー生成用のプロンプトを作成"""
        
        prompt = f"""
以下の設定で「{selected_theme}」テーマの物語を5ページで作成してください。

【基本設定】
- 主人公: {protagonist_name}（{protagonist_type}）
- 舞台: {setting_place}
- テーマ: {selected_theme}

【出力形式】
以下のJSON形式で出力してください：
{{
  "title": "物語のタイトル",
  "story_pages": [
    {{"page_1": "1ページ目の完全な物語本文"}},
    {{"page_2": "2ページ目の完全な物語本文"}},
    {{"page_3": "3ページ目の完全な物語本文"}},
    {{"page_4": "4ページ目の完全な物語本文"}},
    {{"page_5": "5ページ目の完全な物語本文"}}
  ]
}}

必ずJSON形式で出力し、他の説明文は含めないでください。
"""

        return prompt

    def _parse_complete_story_response(self, response_text: str) -> Dict[str, Any]:
        """完全なストーリー生成のレスポンスをパース"""
        try:
            # JSON部分を抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.rfind("```")
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()

            story_data = json.loads(json_text)
            return story_data

        except json.JSONDecodeError as e:
            print(f"JSON解析エラー: {e}")
            print(f"レスポンステキスト: {response_text}")
            raise ValueError("Geminiからのレスポンスが正しいJSON形式ではありません")

    def _parse_single_story_response(self, response_text: str) -> Dict[str, Any]:
        """単一ストーリー生成のレスポンスをパース"""
        return self._parse_complete_story_response(response_text)

    def _generate_fallback_complete_story(self, protagonist_name: str, protagonist_type: str, setting_place: str, tone: str) -> Dict[str, Any]:
        """エラー時のフォールバック用完全ストーリー"""
        return {
            "theme_options": {
                "theme1": {
                    "theme_id": "adventure",
                    "title": f"{protagonist_name}の冒険",
                    "description": f"{protagonist_name}が{setting_place}で冒険に出かける物語",
                    "keywords": ["冒険", "勇気", "挑戦"]
                },
                "theme2": {
                    "theme_id": "friendship",
                    "title": f"{protagonist_name}の新しい友達",
                    "description": f"{protagonist_name}が{setting_place}で新しい友達と出会う物語",
                    "keywords": ["友情", "優しさ", "協力"]
                },
                "theme3": {
                    "theme_id": "discovery",
                    "title": f"{protagonist_name}の不思議な発見",
                    "description": f"{protagonist_name}が{setting_place}で不思議なものを見つける物語",
                    "keywords": ["発見", "探求", "好奇心"]
                }
            },
            "generated_stories": {
                "theme1": {
                    "title": f"{protagonist_name}の冒険",
                    "story_pages": [
                        {"page_1": f"むかしむかし、{protagonist_name}が{setting_place}で遊んでいました。"},
                        {"page_2": "すると、不思議な道を発見しました。"},
                        {"page_3": "勇気を出して道を進んでいきます。"},
                        {"page_4": "新しい友達と出会い、力を合わせました。"},
                        {"page_5": "冒険を通じて大切なことを学びました。"}
                    ]
                },
                "theme2": {
                    "title": f"{protagonist_name}の新しい友達",
                    "story_pages": [
                        {"page_1": f"{protagonist_name}は{setting_place}で一人で遊んでいました。"},
                        {"page_2": "そこで新しい友達に出会いました。"},
                        {"page_3": "最初はうまく話せませんでしたが..."},
                        {"page_4": "一緒に遊ぶことで仲良くなりました。"},
                        {"page_5": "友情の大切さを学びました。"}
                    ]
                },
                "theme3": {
                    "title": f"{protagonist_name}の不思議な発見",
                    "story_pages": [
                        {"page_1": f"{protagonist_name}は{setting_place}で不思議なものを発見しました。"},
                        {"page_2": "それが何なのか調べてみました。"},
                        {"page_3": "調べていくうちに驚くべきことがわかりました。"},
                        {"page_4": "その発見をみんなに伝えました。"},
                        {"page_5": "学ぶことの楽しさを知りました。"}
                    ]
                }
            }
        }

    def _generate_fallback_single_story(self, protagonist_name: str, protagonist_type: str, setting_place: str, selected_theme: str) -> Dict[str, Any]:
        """エラー時のフォールバック用単一ストーリー"""
        return {
            "title": f"{protagonist_name}の{selected_theme}",
            "story_pages": [
                {"page_1": f"むかしむかし、{protagonist_name}が{setting_place}で遊んでいました。"},
                {"page_2": "そこで素敵な出来事が起こりました。"},
                {"page_3": "主人公は勇気を出して立ち向かいました。"},
                {"page_4": "友達と協力して問題を解決しました。"},
                {"page_5": "大切なことを学んで成長しました。"}
            ]
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
        
        # 人間の顔が検出されている場合、Gemini APIで性別を判定
        if has_human_face:
            try:
                # 画像ファイルのパスを取得（upload_image_idから）
                from sqlalchemy.orm import Session
                from app.database.session import get_db
                from app.models.images.images import UploadImages
                
                # データベースセッションを取得
                db_gen = get_db()
                db = next(db_gen)
                try:
                    upload_image = db.query(UploadImages).filter(UploadImages.id == upload_image_id).first()
                    if upload_image and upload_image.file_path:
                        gender_result = self._detect_gender_with_gemini(upload_image.file_path)
                        if gender_result in ["男の子", "女の子"]:
                            protagonist_type = gender_result
                finally:
                    db.close()
            except Exception as e:
                print(f"性別判定エラー: {e}")
                # エラー時はデフォルトの「子供」のまま
        else:
            # 人間の顔が検出されない場合でも、子供が描いた絵の場合は性別判定を試行
            # labelsから判定
            lower_labels = [l.lower() for l in labels]
            is_cartoon_character = any(k in lower_labels for k in ["cartoon", "animation", "animated cartoon", "fictional character", "toy"])
            is_child_drawing = any(k in lower_labels for k in ["drawing", "art", "illustration", "sketch", "painting"])
            
            if is_cartoon_character or is_child_drawing:
                try:
                    # 画像ファイルのパスを取得（upload_image_idから）
                    from sqlalchemy.orm import Session
                    from app.database.session import get_db
                    from app.models.images.images import UploadImages
                    
                    # データベースセッションを取得
                    db_gen = get_db()
                    db = next(db_gen)
                    try:
                        upload_image = db.query(UploadImages).filter(UploadImages.id == upload_image_id).first()
                        if upload_image and upload_image.file_path:
                            gender_result = self._detect_gender_from_drawing(upload_image.file_path)
                            if gender_result in ["男の子", "女の子"]:
                                protagonist_type = gender_result
                    finally:
                        db.close()
                except Exception as e:
                    print(f"絵からの性別判定エラー: {e}")
                    # エラー時は従来のロジックにフォールバック
        
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