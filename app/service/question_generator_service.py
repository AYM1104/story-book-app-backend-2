from typing import Dict, Any, List, Optional

class QuestionGeneratorService:
    """物語設定の不足情報に対して質問を生成するサービス"""
    
    def generate_questions_for_missing_info(self, story_setting: Dict[str, Any]) -> List[Dict[str, str]]:
        """不足している情報に対して質問を生成"""
        
        questions = []
        
        # 主人公の名前が空の場合
        if not story_setting.get("protagonist_name"):
            protagonist_type = story_setting.get("protagonist_type", "主人公")
            name_suggestion = self._get_name_suggestion(protagonist_type)
            questions.append({
                "field": "protagonist_name",
                "question": f"主人公の名前を教えてください。{name_suggestion}",
                "type": "text_input",
                "placeholder": "例: たろうくん",
                "required": True
            })
        
        # 舞台となる場所が空の場合
        if not story_setting.get("setting_place"):
            questions.append({
                "field": "setting_place",
                "question": "物語の舞台となる場所を選んでください：",
                "type": "select",
                "options": [
                    {"value": "forest", "label": "森"},
                    {"value": "park", "label": "公園"},
                    {"value": "sea", "label": "海"},
                    {"value": "space", "label": "宇宙"},
                    {"value": "house", "label": "おうち"},
                    {"value": "school", "label": "学校"},
                    {"value": "city", "label": "まち"},
                    {"value": "mountain", "label": "山"},
                    {"value": "garden", "label": "庭"}
                ],
                "required": True
            })
        
        # 物語の雰囲気が不明確な場合（gentle以外）
        tone = story_setting.get("tone")
        if tone == "gentle":  # デフォルト値の場合、ユーザーに確認
            questions.append({
                "field": "tone",
                "question": "物語の雰囲気を選んでください：",
                "type": "select",
                "options": [
                    {"value": "gentle", "label": "優しく温かい"},
                    {"value": "fun", "label": "楽しく明るい"},
                    {"value": "adventure", "label": "冒険的でワクワク"},
                    {"value": "mystery", "label": "謎解きでドキドキ"}
                ],
                "required": True
            })
        
        # 対象年齢の確認
        questions.append({
            "field": "target_age",
            "question": "お子様の年齢を教えてください：",
            "type": "select",
            "options": [
                {"value": "preschool", "label": "未就学児（3-6歳）"},
                {"value": "elementary_low", "label": "小学生低学年（7-9歳）"}
            ],
            "required": True
        })
        
        # 読みやすさレベルの設定
        questions.append({
            "field": "reading_level",
            "question": "読みやすさのレベルを選んでください：",
            "type": "select",
            "options": [
                {"value": "hiragana_only", "label": "ひらがなのみ"},
                {"value": "hiragana_katakana", "label": "ひらがな・カタカナ"},
                {"value": "basic_kanji", "label": "基本的な漢字も含む"},
                {"value": "normal", "label": "普通のレベル"}
            ],
            "required": False
        })
        
        return questions
    
    def _get_name_suggestion(self, protagonist_type: str) -> str:
        """主人公タイプに応じた名前の提案"""
        suggestions = {
            "girl": "（例: あおいちゃん、みどりちゃん、はなちゃん）",
            "boy": "（例: たろうくん、けんたくん、ゆうとくん）",
            "animal": "（例: こねこちゃん、わんちゃん、うさちゃん）",
            "robot": "（例: ロボちゃん、テックくん、ビームちゃん）"
        }
        return suggestions.get(protagonist_type, "（例: 主人公の名前）")

# シングルトンインスタンス
question_generator_service = QuestionGeneratorService()
