from typing import Dict, Any, List, Optional

class QuestionGeneratorService:
    """物語設定に関する質問を生成するサービス（常に全質問を返す）"""
    
    # 質問テキストの多言語対応
    QUESTIONS_I18N = {
        "ja": {
            "protagonist_gender": "主人公の性別を選んでください：",
            "protagonist_name": "主人公の名前を教えてください。{suggestion}",
            "protagonist_name_placeholder": "例: たろうくん",
            "setting_place": "物語の舞台となる場所を選んでください：",
            "tone": "物語の雰囲気を選んでください：",
            "target_age": "お子様の年齢を教えてください：",
            "reading_level": "読みやすさのレベルを選んでください：",
            # Options - Gender
            "option_boy": "男の子",
            "option_girl": "女の子",
            # Options - Place
            "option_forest": "森",
            "option_park": "公園",
            "option_sea": "海",
            "option_space": "宇宙",
            "option_home": "家",
            "option_school": "学校",
            "option_town": "まち",
            "option_mountain": "山",
            "option_garden": "庭",
            # Options - Tone
            "option_gentle": "優しく温かい",
            "option_fun": "楽しく明るい",
            "option_adventure": "冒険的でワクワク",
            "option_mystery": "謎解きでドキドキ",
            "option_heartwarming": "感動的で心が温まる",
            "option_dreamy": "幻想的で夢のような",
            "option_magical": "魔法のように不思議な",
            "option_brave": "勇気をもって挑戦する",
            # Options - Target Age
            "option_preschool": "未就学児（3-6歳）",
            "option_elementary_low": "小学生低学年（7-9歳）",
            # Options - Reading Level
            "option_hiragana_only": "ひらがなのみ",
            "option_hiragana_katakana": "ひらがな・カタカナ",
            "option_basic_kanji": "基本的な漢字も含む",
            "option_normal": "普通のレベル",
            # Name suggestions
            "name_suggestion_girl": "（例: あおいちゃん、みどりちゃん、はなちゃん）",
            "name_suggestion_boy": "（例: たろうくん、けんたくん、ゆうとくん）",
            "name_suggestion_child": "（例: たろうくん、はなちゃん）",
            "name_suggestion_animal": "（例: こねこちゃん、わんちゃん、うさちゃん）",
            "name_suggestion_robot": "（例: ロボちゃん、テックくん、ビームちゃん）",
            "name_suggestion_default": "（例: 主人公の名前）",
        },
        "en": {
            "protagonist_gender": "Please select the protagonist's gender:",
            "protagonist_name": "Please tell us the protagonist's name. {suggestion}",
            "protagonist_name_placeholder": "Example: Taro",
            "setting_place": "Please select the story's setting:",
            "tone": "Please select the story's atmosphere:",
            "target_age": "Please tell us your child's age:",
            "reading_level": "Please select the reading level:",
            # Options - Gender
            "option_boy": "Boy",
            "option_girl": "Girl",
            # Options - Place
            "option_forest": "Forest",
            "option_park": "Park",
            "option_sea": "Sea",
            "option_space": "Space",
            "option_home": "Home",
            "option_school": "School",
            "option_town": "Town",
            "option_mountain": "Mountain",
            "option_garden": "Garden",
            # Options - Tone
            "option_gentle": "Gentle and warm",
            "option_fun": "Fun and bright",
            "option_adventure": "Exciting adventure",
            "option_mystery": "Thrilling mystery",
            "option_heartwarming": "Touching and heartwarming",
            "option_dreamy": "Dreamy and fantastical",
            "option_magical": "Wonderfully magical",
            "option_brave": "Brave and challenging",
            # Options - Target Age
            "option_preschool": "Preschool (3-6 years)",
            "option_elementary_low": "Early elementary (7-9 years)",
            # Options - Reading Level
            "option_hiragana_only": "Hiragana only",
            "option_hiragana_katakana": "Hiragana and Katakana",
            "option_basic_kanji": "Including basic Kanji",
            "option_normal": "Normal level",
            # Name suggestions
            "name_suggestion_girl": "(Example: Aoi, Midori, Hana)",
            "name_suggestion_boy": "(Example: Taro, Kenta, Yuto)",
            "name_suggestion_child": "(Example: Taro, Hana)",
            "name_suggestion_animal": "(Example: Kitty, Puppy, Bunny)",
            "name_suggestion_robot": "(Example: Robo, Tech, Beam)",
            "name_suggestion_default": "(Example: protagonist's name)",
        }
    }
    
    def _get_text(self, key: str, lang: str = "ja") -> str:
        """言語に応じたテキストを取得"""
        texts = self.QUESTIONS_I18N.get(lang, self.QUESTIONS_I18N["ja"])
        return texts.get(key, self.QUESTIONS_I18N["ja"].get(key, key))
    
    def generate_questions_for_missing_info(self, story_setting: Dict[str, Any], lang: str = "ja") -> List[Dict[str, str]]:
        """常に全ての質問を生成して返す（言語対応）"""
        
        # 言語が対応していない場合は日本語にフォールバック
        if lang not in self.QUESTIONS_I18N:
            lang = "ja"
        
        questions = []
        
        # 主人公のタイプを取得
        protagonist_type = story_setting.get("protagonist_type", "主人公")
        
        # 主人公の性別（protagonist_typeが「子供」の場合のみ質問）
        if protagonist_type == "子供":
            questions.append({
                "field": "protagonist_type",
                "question": self._get_text("protagonist_gender", lang),
                "type": "select",
                "options": [
                    {"value": "男の子", "label": self._get_text("option_boy", lang)},
                    {"value": "女の子", "label": self._get_text("option_girl", lang)}
                ],
                "required": True
            })
        
        # 主人公の名前（常に質問）
        name_suggestion = self._get_name_suggestion(protagonist_type, lang)
        questions.append({
            "field": "protagonist_name",
            "question": self._get_text("protagonist_name", lang).format(suggestion=name_suggestion),
            "type": "text_input",
            "placeholder": self._get_text("protagonist_name_placeholder", lang),
            "required": True
        })
        
        # 舞台となる場所（常に質問）
        questions.append({
            "field": "setting_place",
            "question": self._get_text("setting_place", lang),
            "type": "select",
            "options": [
                {"value": "森", "label": self._get_text("option_forest", lang)},
                {"value": "公園", "label": self._get_text("option_park", lang)},
                {"value": "海", "label": self._get_text("option_sea", lang)},
                {"value": "宇宙", "label": self._get_text("option_space", lang)},
                {"value": "家", "label": self._get_text("option_home", lang)},
                {"value": "学校", "label": self._get_text("option_school", lang)},
                {"value": "まち", "label": self._get_text("option_town", lang)},
                {"value": "山", "label": self._get_text("option_mountain", lang)},
                {"value": "庭", "label": self._get_text("option_garden", lang)}
            ],
            "required": True
        })
        
        # 物語の雰囲気（常に質問）
        questions.append({
            "field": "tone",
            "question": self._get_text("tone", lang),
            "type": "select",
            "options": [
                {"value": "gentle", "label": self._get_text("option_gentle", lang)},
                {"value": "fun", "label": self._get_text("option_fun", lang)},
                {"value": "adventure", "label": self._get_text("option_adventure", lang)},
                {"value": "mystery", "label": self._get_text("option_mystery", lang)},
                {"value": "heartwarming", "label": self._get_text("option_heartwarming", lang)},
                {"value": "dreamy", "label": self._get_text("option_dreamy", lang)},
                {"value": "magical", "label": self._get_text("option_magical", lang)},
                {"value": "brave", "label": self._get_text("option_brave", lang)}
                
            ],
            "required": True
        })
        
        # 対象年齢の確認
        questions.append({
            "field": "target_age",
            "question": self._get_text("target_age", lang),
            "type": "select",
            "options": [
                {"value": "preschool", "label": self._get_text("option_preschool", lang)},
                {"value": "elementary_low", "label": self._get_text("option_elementary_low", lang)}
            ],
            "required": True
        })
        
        # 読みやすさレベルの設定
        questions.append({
            "field": "reading_level",
            "question": self._get_text("reading_level", lang),
            "type": "select",
            "options": [
                {"value": "hiragana_only", "label": self._get_text("option_hiragana_only", lang)},
                {"value": "hiragana_katakana", "label": self._get_text("option_hiragana_katakana", lang)},
                {"value": "basic_kanji", "label": self._get_text("option_basic_kanji", lang)},
                {"value": "normal", "label": self._get_text("option_normal", lang)}
            ],
            "required": False
        })
        
        return questions
    
    def _get_name_suggestion(self, protagonist_type: str, lang: str = "ja") -> str:
        """主人公タイプに応じた名前の提案"""
        type_to_key = {
            "女の子": "name_suggestion_girl",
            "男の子": "name_suggestion_boy",
            "子供": "name_suggestion_child",
            "girl": "name_suggestion_girl",
            "boy": "name_suggestion_boy",
            "animal": "name_suggestion_animal",
            "robot": "name_suggestion_robot"
        }
        key = type_to_key.get(protagonist_type, "name_suggestion_default")
        return self._get_text(key, lang)

# シングルトンインスタンス
question_generator_service = QuestionGeneratorService()
