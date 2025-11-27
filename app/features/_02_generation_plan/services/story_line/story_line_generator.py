import json
import google.generativeai as genai
from typing import Dict, Any, Optional, List
import os
import traceback
from dotenv import load_dotenv
from app.features._04_theme_selection.services.theme_generator import theme_generator, TONE_DESCRIPTIONS, AGE_DESCRIPTIONS, READING_LEVEL_DESCRIPTIONS

load_dotenv()

class StoryGeneratorService:
    """Gemini 2.5 Flashを使用してストーリーを生成するサービス"""

    def __init__(self):
        # Gemini APIの設定（物語生成用のFree APIキーを使用、なければPaid APIキーを使用）
        api_key = os.getenv("GOOGLE_API_KEY_Free") or os.getenv("GOOGLE_API_KEY_Paid")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY_FreeまたはGOOGLE_API_KEY_Paidが設定されていません")
        
        # 使用しているAPIキーの種類を判定
        api_key_type = "GOOGLE_API_KEY_Free" if os.getenv("GOOGLE_API_KEY_Free") else "GOOGLE_API_KEY_Paid"
        
        # APIキーのクリーンアップ（改行、スペース、引用符を削除）
        api_key = api_key.strip().strip('"').strip("'")
        
        # APIキーの形式検証
        if not api_key.startswith("AIza"):
            print(f"⚠️ 警告: APIキーの形式が正しくない可能性があります（AIzaで始まる必要があります）")
        
        # APIキーが空でないことを再確認
        if not api_key or len(api_key) < 20:
            error_msg = f"APIキーが無効です（長さ: {len(api_key)}文字）。APIキーは通常39文字以上です。"
            raise ValueError(error_msg)
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except Exception as e:
            error_msg = f"Gemini APIの初期化に失敗しました: {str(e)}"
            raise ValueError(error_msg) from e

    def generate_theme_options_only(self, story_setting: Dict[str, Any]) -> Dict[str, Any]:
        """3つのテーマ案のみを生成（物語本文は生成しない）- 高速化版"""
        # ThemeGeneratorに委譲
        return theme_generator.generate_theme_options_only(story_setting)

    def generate_complete_story(self, story_setting: Dict[str, Any], story_pages: int = 5) -> Dict[str, Any]:
        """テーマ案と物語本文を一緒に生成（非推奨 - 遅い）"""
        
        protagonist_name = story_setting.get("protagonist_name", "主人公")
        protagonist_type = story_setting.get("protagonist_type", "子供")
        setting_place = story_setting.get("setting_place", "公園")
        tone = story_setting.get("tone", "gentle")
        target_age = story_setting.get("target_age", "preschool")
        reading_level = story_setting.get("reading_level", "hiragana_only")

        # プロンプトを作成
        prompt = self._create_complete_story_prompt(
            protagonist_name, protagonist_type, setting_place, 
            tone, target_age, reading_level, story_pages
        )

        try:
            # プロンプト全文をターミナルに表示
            print("=" * 80)
            print("【Gemini API プロンプト全文 - 完全なストーリー生成】")
            print("=" * 80)
            print(prompt)
            print("=" * 80)
            
            # Gemini 2.5 Flashで完全なストーリーを生成
            response = self.model.generate_content(prompt)
            story_data = self._parse_complete_story_response(response.text)
            return story_data

        except Exception as e:
            print(f"Gemini API エラー: {e}")
            # エラー時はフォールバック
            return self._generate_fallback_complete_story(protagonist_name, protagonist_type, setting_place, tone, story_pages)

    def generate_single_story(self, story_setting: Dict[str, Any], selected_theme: str, story_pages: int = 5) -> Dict[str, Any]:
        """選択されたテーマの物語本文を生成
        
        Args:
            story_setting: ストーリー設定の辞書
            selected_theme: 選択されたテーマのタイトル
            story_pages: 生成するページ数（3, 5, 7, 10のいずれか、デフォルトは5）
        """
        
        # デバッグ: 受け取ったページ数を確認
        print(f"🔍 generate_single_story 受け取ったページ数: {story_pages}")
        
        protagonist_name = story_setting.get("protagonist_name", "主人公")
        protagonist_type = story_setting.get("protagonist_type", "子供")
        setting_place = story_setting.get("setting_place", "公園")
        tone = story_setting.get("tone", "gentle")
        target_age = story_setting.get("target_age", "preschool")
        reading_level = story_setting.get("reading_level", "hiragana_only")

        # プロンプトを作成
        prompt = self._create_single_story_prompt(
            protagonist_name, protagonist_type, setting_place, 
            tone, target_age, reading_level, selected_theme, story_pages
        )

        try:
            # プロンプト全文をターミナルに表示
            print("=" * 80)
            print("【Gemini API プロンプト全文 - 単一ストーリー生成】")
            print("=" * 80)
            print(prompt)
            print("=" * 80)
            
            # Gemini 2.5 Flashで単一ストーリーを生成
            response = self.model.generate_content(prompt)
            
            # レスポンスの検証
            if not response or not hasattr(response, 'text') or not response.text:
                raise ValueError("Gemini APIからのレスポンスが空です")
            
            # レスポンスの内容をログに出力（デバッグ用）
            print("=" * 80)
            print("【Gemini API レスポンス（最初の1000文字）】")
            print("=" * 80)
            print(response.text[:1000])
            print("=" * 80)
            
            story_data = self._parse_single_story_response(response.text)
            return story_data

        except ValueError as ve:
            # JSON解析エラーなど、ValueErrorの場合は詳細を出力してからフォールバック
            print(f"❌ Gemini API エラー（ValueError）: {ve}")
            print(f"エラーのトレースバック: {traceback.format_exc()}")
            # エラー時はフォールバック
            return self._generate_fallback_single_story(protagonist_name, protagonist_type, setting_place, selected_theme, story_pages)
        except Exception as e:
            print(f"❌ Gemini API エラー（予期しないエラー）: {e}")
            print(f"エラーのトレースバック: {traceback.format_exc()}")
            # エラー時はフォールバック
            return self._generate_fallback_single_story(protagonist_name, protagonist_type, setting_place, selected_theme, story_pages)


    def _create_complete_story_prompt(self, protagonist_name: str, protagonist_type: str, 
                                    setting_place: str, tone: str, target_age: str, reading_level: str, story_pages: int = 5) -> str:
        """完全なストーリー生成用のプロンプトを作成
        
        Args:
            story_pages: 生成するページ数（3, 5, 7, 10のいずれか）
        """
        
        # 共通定数を使用（theme_generator.pyからインポート）
        reading_level_desc = READING_LEVEL_DESCRIPTIONS.get(reading_level, reading_level)
        
        # ページ数のJSON配列を動的に生成（story_pagesに応じて動的に変更）
        pages_json_items = []
        for i in range(1, story_pages + 1):
            pages_json_items.append(f'{{"page_{i}": "{i}ページ目の完全な物語本文"}}')
        pages_json_array = ",\n        ".join(pages_json_items)

        prompt = f"""
あなたは子供向けの絵本のストーリー企画者です。
以下の設定を元に、3つの異なるテーマの物語案と、それぞれの完全な物語本文（{story_pages}ページ）を作成してください。

【基本設定】
- 主人公: {protagonist_name}（{protagonist_type}）
- 舞台: {setting_place}
- 雰囲気: {TONE_DESCRIPTIONS.get(tone, '優しく温かい雰囲気')}
- 対象年齢: {AGE_DESCRIPTIONS.get(target_age, '3-6歳の未就学児向け')}
- 読みやすさ: {reading_level_desc}

【要求事項】
1. 3つの異なるテーマ（冒険、友情、発見など）
2. 各テーマで{story_pages}ページの完全な物語本文
3. 子供が楽しめる内容
4. 教育的な要素を含む
5. 読みやすく、感情に訴える文章
6. 読みやすさの設定に従った文字種で作成

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
        {pages_json_array}
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
                                  setting_place: str, tone: str, target_age: str, reading_level: str, selected_theme: str, story_pages: int = 5) -> str:
        """単一ストーリー生成用のプロンプトを作成
        
        Args:
            story_pages: 生成するページ数（3, 5, 7, 10のいずれか）
        """
        
        # ページ数に応じた「構成テンプレート（物語の波）」を定義
        # ここが物語の面白さを決める「設計図」になります
        structure_guide = ""
        
        if story_pages == 3:
            structure_guide = """
        【3ページ構成（ショート）】
        - page_1: 【導入】主人公の紹介と、何かが起こるきっかけ。
        - page_2: 【展開】アクション！主人公が特徴を活かして動く。
        - page_3: 【結末】解決とハッピーエンド。
        """
        elif story_pages == 5:
            structure_guide = """
        【5ページ構成（スタンダード）】
        - page_1: 【導入】日常の描写。主人公は何をしている？
        - page_2: 【事件】不思議なことや困ったことが起きる。
        - page_3: 【挑戦】解決しようと頑張るが、壁にぶつかる。
        - page_4: 【クライマックス】主人公の「一番いいところ」が出て解決！
        - page_5: 【結末】みんな笑顔で終わる。
        """
        elif story_pages == 7:
            structure_guide = """
        【7ページ構成（ドラマチック）】
        - page_1: 【導入】平和な日常。
        - page_2: 【事件】冒険への誘い、または事件の発生。
        - page_3: 【旅立ち/試行】目的地へ向かう、または最初の挑戦。
        - page_4: 【ピンチ】うまくいかない！少し困った状況になる。
        - page_5: 【転機】意外な助けや、新しいアイデアを思いつく。
        - page_6: 【解決】ピンチを脱出し、目的を達成する。
        - page_7: 【帰還】お家に帰る、または日常に戻り安心する。
        """
        elif story_pages == 10:
            structure_guide = """
        【10ページ構成（大冒険）】
        - page_1: 【プロローグ】主人公と舞台の丁寧な描写。
        - page_2: 【日常の終わり】事件発生。冒険に出る理由ができる。
        - page_3: 【旅の始まり】ワクワクする出発。
        - page_4: 【出会い】新しい友達やアイテムとの出会い。
        - page_5: 【小ハプニング】ちょっとした失敗や寄り道（ユーモア）。
        - page_6: 【最大の試練】強敵や大きな壁が現れる（ドキドキ）。
        - page_7: 【挫折と再起】諦めそうになるが、励まされて立ち上がる。
        - page_8: 【クライマックス】主人公の「特別な力（特徴）」で突破する！
        - page_9: 【大団円】喜びの瞬間、達成感。
        - page_10: 【エピローグ】成長した姿で日常に戻る。余韻。
        """
        
        # 共通定数を使用（theme_generator.pyからインポート）
        reading_level_desc = READING_LEVEL_DESCRIPTIONS.get(reading_level, reading_level)
        
        prompt = f"""
あなたは子供たちの心を掴んで離さない、熟練の絵本作家です。

以下の設定と構成ガイドに基づき、「タイトル：{selected_theme}」の絵本を作成してください。

【基本設定】
- 主人公: {protagonist_name}
- キャラクターの特徴: {protagonist_type}（この特徴を物語の鍵にしてください）
- 舞台: {setting_place}
- 雰囲気: {TONE_DESCRIPTIONS.get(tone, '優しく温かい雰囲気')}
- 対象年齢: {AGE_DESCRIPTIONS.get(target_age, '3-6歳の未就学児向け')}
- 読みやすさ: {reading_level_desc}

【構成ガイド（厳守）】
以下の流れに沿って、物語のリズムを作ってください：
{structure_guide}

【重要：執筆ルール】
1. **「説明」禁止、「描写」重視**: 状況を説明するのではなく、キャラのセリフや音、見た目で表現してください。
2. **オノマトペ必須**: 全ページに必ず1つ以上、効果音（擬音語・擬態語）を入れてください。
3. **10ページの場合の注意**: 文章が長くなりすぎないように。1ページあたりの文字数は子供が飽きない分量に抑えてください。
4. **背景との連動**: 各ページの`background_prompt`は、物語の進行に合わせて景色や色味が変わるように詳細に指定してください。

【出力形式】
以下のJSON形式のみを出力してください（Markdown不要）：

{{
  "title": "物語のタイトル（ひらがな多め）",
  "story_pages": [
    {{
      "page_no": 1,
      "story_text": "本文...",
      "background_prompt": "English prompt for image generation..." 
    }},
    ... ({story_pages}ページ分まで繰り返し)
  ]
}}
"""

        return prompt


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
            print(f"レスポンステキスト（最初の500文字）: {response_text[:500]}")
            print(f"レスポンステキスト（最後の500文字）: {response_text[-500:]}")
            print(f"レスポンステキスト全体の長さ: {len(response_text)}文字")
            # デバッグ用: 抽出されたJSONテキストも表示
            if 'json_text' in locals():
                print(f"抽出されたJSONテキスト（最初の500文字）: {json_text[:500] if json_text else 'None'}")
            raise ValueError(f"Geminiからのレスポンスが正しいJSON形式ではありません: {str(e)}")
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
            print(f"レスポンステキスト（最初の500文字）: {response_text[:500]}")
            raise ValueError(f"レスポンスの解析に失敗しました: {str(e)}")

    def _parse_single_story_response(self, response_text: str) -> Dict[str, Any]:
        """単一ストーリー生成のレスポンスをパース"""
        return self._parse_complete_story_response(response_text)


    def _generate_fallback_complete_story(self, protagonist_name: str, protagonist_type: str, setting_place: str, tone: str, story_pages: int = 5) -> Dict[str, Any]:
        """エラー時のフォールバック用完全ストーリー"""
        
        # ページ数に応じたデフォルトストーリーを生成
        fallback_texts_theme1 = [
            f"むかしむかし、{protagonist_name}が{setting_place}で遊んでいました。",
            "すると、不思議な道を発見しました。",
            "勇気を出して道を進んでいきます。",
            "新しい友達と出会い、力を合わせました。",
            "冒険を通じて大切なことを学びました。",
            "さらに深く冒険を続けていきます。",
            "困難を乗り越えて、さらに成長しました。",
            "周りの人たちに感謝の気持ちを伝えました。",
            "たくさんのことを学び、心が豊かになりました。",
            "そして、毎日が楽しくなりました。"
        ]
        
        fallback_texts_theme2 = [
            f"{protagonist_name}は{setting_place}で一人で遊んでいました。",
            "そこで新しい友達に出会いました。",
            "最初はうまく話せませんでしたが...",
            "一緒に遊ぶことで仲良くなりました。",
            "友情の大切さを学びました。",
            "お互いを理解し合えるようになりました。",
            "一緒にいろいろなことに挑戦しました。",
            "困難な時も支え合いました。",
            "友情が深まっていきました。",
            "毎日が楽しくなりました。"
        ]
        
        fallback_texts_theme3 = [
            f"{protagonist_name}は{setting_place}で不思議なものを発見しました。",
            "それが何なのか調べてみました。",
            "調べていくうちに驚くべきことがわかりました。",
            "その発見をみんなに伝えました。",
            "学ぶことの楽しさを知りました。",
            "さらに詳しく調べていきました。",
            "新しい発見が次々とありました。",
            "知識がどんどん増えていきました。",
            "探求心が育っていきました。",
            "好奇心の大切さを学びました。"
        ]
        
        def create_pages(fallback_texts: List[str], pages: int) -> List[Dict[str, str]]:
            """ページ数のリストを生成"""
            page_list = []
            for i in range(1, min(pages + 1, 11)):
                if i <= len(fallback_texts):
                    page_list.append({f"page_{i}": fallback_texts[i - 1]})
                else:
                    page_list.append({f"page_{i}": "物語が続きます。"})
            return page_list
        
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
                    "story_pages": create_pages(fallback_texts_theme1, story_pages)
                },
                "theme2": {
                    "title": f"{protagonist_name}の新しい友達",
                    "story_pages": create_pages(fallback_texts_theme2, story_pages)
                },
                "theme3": {
                    "title": f"{protagonist_name}の不思議な発見",
                    "story_pages": create_pages(fallback_texts_theme3, story_pages)
                }
            }
        }

    def _generate_fallback_single_story(self, protagonist_name: str, protagonist_type: str, setting_place: str, selected_theme: str, story_pages: int = 5) -> Dict[str, Any]:
        """エラー時のフォールバック用単一ストーリー"""
        # ページ数に応じたデフォルトストーリーを生成
        fallback_pages = []
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
        
        for i in range(1, min(story_pages + 1, 11)):
            if i <= len(fallback_texts):
                fallback_pages.append({f"page_{i}": fallback_texts[i - 1]})
            else:
                fallback_pages.append({f"page_{i}": "物語が続きます。"})
        
        return {
            "title": f"{protagonist_name}の{selected_theme}",
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

