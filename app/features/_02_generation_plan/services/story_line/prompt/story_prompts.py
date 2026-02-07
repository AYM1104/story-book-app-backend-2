# ストーリー生成用のプロンプトテンプレート

from app.core.prompt.constants import TONE_DESCRIPTIONS, AGE_DESCRIPTIONS, READING_LEVEL_DESCRIPTIONS

# 英語版の定数マッピング
TONE_DESCRIPTIONS_EN = {
    "gentle": "gentle and warm",
    "heartwarming": "heartwarming",
    "adventure": "adventurous",
    "brave": "brave and courageous",
    "mystery": "mysterious and exciting",
    "fun": "fun and playful",
    "dreamy": "dreamy and magical",
    "magical": "magical and fantastical"
}

AGE_DESCRIPTIONS_EN = {
    "infant": "for infants (0-2 years)",
    "toddler": "for toddlers (2-3 years)",
    "preschool": "for preschoolers (3-6 years)",
    "early_elementary": "for early elementary (6-8 years)"
}


def create_single_story_prompt(
    protagonist_name: str,
    protagonist_type: str,
    setting_place: str,
    tone: str,
    target_age: str,
    reading_level: str,
    selected_theme: str,
    story_pages: int = 5,
    language: str = "ja"
) -> str:
    """単一ストーリー生成用のプロンプトを作成
    
    Args:
        protagonist_name: 主人公の名前
        protagonist_type: キャラクターの特徴（外見・種族）
        setting_place: 舞台
        tone: 雰囲気の種類
        target_age: 対象年齢
        reading_level: 読みやすさレベル
        selected_theme: 選択されたテーマのタイトル
        story_pages: 生成するページ数（3, 5, 7, 10のいずれか）
        language: 出力言語 ("ja" または "en")
        
    Returns:
        プロンプト文字列
    """
    
    # 言語に応じてプロンプトを生成
    if language == "en":
        return _create_single_story_prompt_en(
            protagonist_name, protagonist_type, setting_place,
            tone, target_age, reading_level, selected_theme, story_pages
        )
    else:
        return _create_single_story_prompt_ja(
            protagonist_name, protagonist_type, setting_place,
            tone, target_age, reading_level, selected_theme, story_pages
        )


def _create_single_story_prompt_ja(
    protagonist_name: str,
    protagonist_type: str,
    setting_place: str,
    tone: str,
    target_age: str,
    reading_level: str,
    selected_theme: str,
    story_pages: int = 5
) -> str:
    """日本語版ストーリー生成プロンプト"""
    
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
    
    # 共通定数を使用
    reading_level_desc = READING_LEVEL_DESCRIPTIONS.get(reading_level, reading_level)
    
    # tone（雰囲気）に応じた適応ガイドを生成
    tone_adaptation = ""
    if tone in ["gentle", "heartwarming"]:
        tone_adaptation = """
◆ 雰囲気「優しく温かい/感動的」への適応：
- 「事件」や「問題」は「小さな出来事」「気づき」という優しい表現に
- 「クライマックス」は派手さより「心の交流」「温かい解決」を重視
- 結末は穏やかで安心感があり、読後にほっこりする余韻を
- 全体的に急がず、ゆったりとした時間の流れを大切に"""
    
    elif tone in ["adventure", "brave"]:
        tone_adaptation = """
◆ 雰囲気「冒険的/勇気をもって」への適応：
- 「事件」は「冒険への誘い」「新しい世界への一歩」として描く
- 「挑戦」では試練や困難を乗り越える過程を丁寧に
- 「クライマックス」は勇気を出して突破する達成感を強調
- ワクワク感、成長、「やればできる」という前向きなメッセージを"""
    
    elif tone == "mystery":
        tone_adaptation = """
◆ 雰囲気「謎解きでドキドキ」への適応：
- 「事件」は「謎の発見」「不思議な手がかり」として提示
- 「挑戦」は「調査」「推理」「手がかり集め」の過程に
- 「クライマックス」は「真相の解明」「謎が解ける瞬間」の驚きと達成感
- ドキドキ感、知的好奇心、発見の喜びを大切に"""
    
    elif tone == "fun":
        tone_adaptation = """
◆ 雰囲気「楽しく明るい」への適応：
- 全体的にユーモアと笑いの要素を散りばめる
- 「事件」や「挑戦」も深刻にならず、楽しさを保つ
- キャラクターの明るさ、ポジティブさを前面に
- 読んでいて自然と笑顔になれる展開を"""
    
    elif tone in ["dreamy", "magical"]:
        tone_adaptation = """
◆ 雰囲気「幻想的/魔法のような」への適応：
- 不思議な出来事、現実離れした描写を積極的に
- 色彩豊かで、夢の中のような雰囲気を大切に
- 「クライマックス」は魔法や奇跡のような特別な瞬間に
- 想像力をかき立てる、非日常的な世界観を"""
    
    else:
        tone_adaptation = f"""
◆ 雰囲気「{TONE_DESCRIPTIONS.get(tone, tone)}」への適応：
- この雰囲気の特徴を物語全体に反映させてください
- 言葉選び、テンポ、描写の濃淡で雰囲気を表現"""
    
    # setting_place（舞台）に応じた適応ガイドを生成
    setting_adaptation = ""
    if setting_place in ["space", "宇宙"]:
        setting_adaptation = """
◆ 舞台「宇宙」の活用：
- スケールの大きさ、広大さを表現
- 星、惑星、宇宙船など宇宙特有の要素を活かす
- 未知との出会い、冒険の壮大さを強調"""
    
    elif setting_place in ["house", "おうち"]:
        setting_adaptation = """
◆ 舞台「おうち」の活用：
- 身近で親しみやすい、安心感のある描写
- 家族との関係、日常の延長として自然に
- 部屋、庭、窓からの景色など具体的な場所を活かす"""
    
    elif setting_place in ["forest", "森"]:
        setting_adaptation = """
◆ 舞台「森」の活用：
- 木々、動物、自然の音など五感を刺激する描写
- 季節感、木漏れ日、森の神秘的な雰囲気
- 生き物との出会い、自然との触れ合いを大切に"""
    
    elif setting_place in ["sea", "海"]:
        setting_adaptation = """
◆ 舞台「海」の活用：
- 波の音、潮の香り、広がる水平線
- 海の生き物、砂浜、海中など多様なシーンを
- 開放感、夏の雰囲気、海特有のワクワク感"""
    
    elif setting_place in ["park", "公園"]:
        setting_adaptation = """
◆ 舞台「公園」の活用：
- 遊具、広場、ベンチなど子供に馴染みのある場所
- 他の子供たちとの交流、社会性の芽生え
- 身近だけど、小さな冒険ができる場所として"""
    
    elif setting_place in ["school", "学校"]:
        setting_adaptation = """
◆ 舞台「学校」の活用：
- 友達、先生、教室など社会性を育む環境
- 学びの場としての要素、新しい発見
- 集団の中での成長、協力の大切さ"""
    
    elif setting_place in ["city", "まち"]:
        setting_adaptation = """
◆ 舞台「まち」の活用：
- 建物、お店、人々など多様な要素
- 都会の活気、にぎやかさ、出会いの多様性
- 探検する楽しさ、新しい場所の発見"""
    
    elif setting_place in ["mountain", "山"]:
        setting_adaptation = """
◆ 舞台「山」の活用：
- 登山、自然の雄大さ、頂上からの景色
- 季節の変化、山特有の生き物や植物
- 挑戦、達成感、自然との一体感"""
    
    elif setting_place in ["garden", "庭"]:
        setting_adaptation = """
◆ 舞台「庭」の活用：
- 花、虫、小さな生き物との出会い
- 身近な自然、四季の移り変わり
- 観察の楽しさ、小さな世界の豊かさ"""
    
    else:
        setting_adaptation = f"""
◆ 舞台「{setting_place}」の活用：
- この場所ならではの特徴を物語に活かしてください
- 具体的な景色、音、雰囲気を丁寧に描写"""
    
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

【構成ガイド（基本の流れ）】
以下の流れに沿って、物語のリズムを作ってください：
{structure_guide}

【重要：雰囲気と舞台への適応】
基本構成を守りつつ、以下の点を意識して物語を調整してください：

{tone_adaptation}

{setting_adaptation}

【重要：執筆ルール】
1. **「説明」禁止、「描写」重視**: 状況を説明するのではなく、キャラのセリフや音、見た目で表現してください。
2. **オノマトペ必須**: 全ページに必ず1つ以上、効果音（擬音語・擬態語）を入れてください。
3. **10ページの場合の注意**: 文章が長くなりすぎないように。1ページあたりの文字数は子供が飽きない分量に抑えてください。
4. **背景との連動**: 各ページの`background_prompt`は、物語の進行に合わせて景色や色味が変わるように詳細に指定してください。
   **重要**: `background_prompt`は背景・環境・景色の描写のみに集中してください。キャラクターの詳細（年齢、名前、服装、外見の特徴など）は含めないでください。場所、時間、天候、色合い、雰囲気、背景の要素（建物、自然、小物など）のみを記述してください。

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


def _create_single_story_prompt_en(
    protagonist_name: str,
    protagonist_type: str,
    setting_place: str,
    tone: str,
    target_age: str,
    reading_level: str,
    selected_theme: str,
    story_pages: int = 5
) -> str:
    """英語版ストーリー生成プロンプト"""
    
    # ページ数に応じた構成ガイド（英語版）
    structure_guide = ""
    
    if story_pages == 3:
        structure_guide = """
        【3-Page Structure (Short)】
        - page_1: [Introduction] Introduce the protagonist and set up the situation.
        - page_2: [Action] The protagonist uses their special trait to do something.
        - page_3: [Resolution] Happy ending and resolution.
        """
    elif story_pages == 5:
        structure_guide = """
        【5-Page Structure (Standard)】
        - page_1: [Introduction] Daily life. What is the protagonist doing?
        - page_2: [Incident] Something strange or problematic happens.
        - page_3: [Challenge] They try to solve it but face a difficulty.
        - page_4: [Climax] The protagonist's best quality helps solve the problem!
        - page_5: [Ending] Everyone smiles. Happy ending.
        """
    elif story_pages == 7:
        structure_guide = """
        【7-Page Structure (Dramatic)】
        - page_1: [Introduction] Peaceful daily life.
        - page_2: [Incident] An invitation to adventure or a problem occurs.
        - page_3: [Journey/Trial] Heading toward the goal or first attempt.
        - page_4: [Trouble] Things don't go well. Facing difficulties.
        - page_5: [Turning Point] Unexpected help or a new idea.
        - page_6: [Resolution] Overcoming the problem and achieving the goal.
        - page_7: [Return] Coming back home or returning to normal life safely.
        """
    elif story_pages == 10:
        structure_guide = """
        【10-Page Structure (Grand Adventure)】
        - page_1: [Prologue] Careful introduction of protagonist and setting.
        - page_2: [End of Normal] Incident occurs. Reason to go on adventure.
        - page_3: [Beginning] Exciting departure.
        - page_4: [Meeting] Encountering new friends or items.
        - page_5: [Minor Trouble] Small mistake or detour (humor).
        - page_6: [Greatest Challenge] A strong enemy or big obstacle appears.
        - page_7: [Setback and Recovery] Almost giving up, but getting encouraged.
        - page_8: [Climax] Breaking through with the protagonist's special power!
        - page_9: [Celebration] Moment of joy and achievement.
        - page_10: [Epilogue] Returning to daily life, having grown. Lingering feeling.
        """
    
    tone_en = TONE_DESCRIPTIONS_EN.get(tone, "gentle and warm")
    age_en = AGE_DESCRIPTIONS_EN.get(target_age, "for preschoolers (3-6 years)")
    
    prompt = f"""
You are an expert picture book author who captivates children's hearts.

Based on the following settings and structure guide, please create a picture book titled "{selected_theme}".

【Basic Settings】
- Protagonist: {protagonist_name}
- Character traits: {protagonist_type} (use this trait as a key element in the story)
- Setting: {setting_place}
- Mood: {tone_en}
- Target age: {age_en}

【Structure Guide (Story Flow)】
Follow this flow to create the rhythm of the story:
{structure_guide}

【Important: Writing Rules】
1. **Show, don't tell**: Express through dialogue, sounds, and visuals rather than explanations.
2. **Sound effects required**: Include at least one sound effect (like "Whoosh!", "Splash!", "Crackle!") on every page.
3. **For 10 pages**: Keep each page's text short enough that children won't get bored.
4. **Background connection**: Make the `background_prompt` detailed, showing how scenery and colors change with the story.
   **Important**: The `background_prompt` should focus ONLY on background, environment, and scenery. 
   Do NOT include character details (age, name, clothing, physical features). 
   Only describe location, time, weather, colors, atmosphere, and background elements (buildings, nature, objects).

【Output Format】
Output only in the following JSON format (no Markdown):

{{
  "title": "Story title (simple, easy to read)",
  "story_pages": [
    {{
      "page_no": 1,
      "story_text": "Story text in English...",
      "background_prompt": "English prompt for image generation..." 
    }},
    ... (repeat for {story_pages} pages)
  ]
}}
"""

    return prompt
