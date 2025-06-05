"""
Language-specific utilities for the translation pipeline.
Contains functions for language detection, guidance, and processing.
"""
import json

def get_lang_specific_translate_sys_prompt(target_lang):
    """
    Provides language-specific translation guidance based on target language.
    
    :param target_lang: Target language for translation
    :return: JSON string with language-specific translation instructions
    """

    # Language-specific guidance dictionary
    language_guidance = {
        'English': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        },
        'Traditional Chinese': {
            'language_style': {
                'tone': 'natural and conversational',
                'formality': "using formal '您' form",
                'audience': 'adapt tone to context, avoiding overly formal or technical language unless needed'
            },
            'translation_principles': [
                'Use everyday, conversational language appropriate to the audience',
                'Ensure translations sound natural for Traditional Chinese customers',
                'Adapt meaning rather than translating literally',
                'Prefer short, simple words for clarity and readability',
                'Omit pronouns when context is clear'
            ],
            'terminology_guidelines': {
                'preferred_terms': [
                    {'English': 'PC', 'Chinese': '電腦'},
                    {'English': 'customer service', 'Chinese': '客服'},
                    {'English': 'template', 'Chinese': '範本'},
                    {'English': 'video', 'Chinese': '影片'},
                    {'English': 'quality', 'Chinese': '品質'}
                ],
                'product_names': 'Keep product names and trademarks in English unless an approved translation exists',
                'components': 'Distinguish built-in component labels from general terms',
                'avoid': 'Avoid awkward colloquialisms and incorrect terminology'
            },
            'grammar_rules': [
                'Follow Traditional Chinese grammar and punctuation rules',
                'Use half-width spaces around English text',
                'Use proper Chinese punctuation marks',
                'Handle articles, possessives, and conjunctions correctly',
                'Avoid gendered pronouns in generic references',
                "Address the user directly with '您'"
            ],
            'ui_guidelines': {
                'error_messages': "Use consistent terminology with phrases like '無法…', '找不到…', '記憶體不足'",
                'keyboard_shortcuts': [
                    "Translate key names like 'Spacebar' to '空格鍵'",
                    'Keep technical key names in English (Alt, Ctrl)',
                    'Format UI elements in square brackets [ ]',
                    "For strings with shortcuts, use '文字(快捷鍵符號+大寫鍵字)', e.g., '結束(&E)'"
                ],
                'placeholders': 'Handle placeholders properly while maintaining grammatical correctness'
            }
        },
        'Simplified Chinese': {
            'language_style': {
                'tone': 'natural and conversational',
                'formality': "using direct '你' form",
                'audience': 'adapt tone to context, avoiding overly formal or technical phrasing unless needed'
            },
            'translation_principles': [
                'Use natural, conversational tone appropriate to the context',
                'Never translate word-for-word; capture overall intent and style',
                'Rewrite as needed for CHS readers to ensure natural flow',
                'Omit pronouns when context is clear',
                "Use neutral role terms (e.g., '人员', '个人') to avoid gendered pronouns"
            ],
            'terminology_guidelines': {
                'preferred_terms': [
                    {'English': 'app', 'Chinese': '应用'},
                    {'English': 'PC', 'Chinese': '电脑'},
                    {'English': 'select', 'Chinese': '选择'},
                    {'English': 'USB drive', 'Chinese': 'U 盘'}
                ],
                'product_names': 'Keep product names and trademarks in English unless an approved CHS name exists',
                'components': 'Localize built-in component labels only where appropriate',
                'avoid': 'Steer clear of disallowed colloquialisms or network slang'
            },
            'grammar_rules': [
                'Adhere to Simplified Chinese grammar and punctuation rules',
                'Use full-width punctuation marks （，。！？：”“、《》）',
                'Use wave dash (~) for ranges, en dash (–) for minus signs',
                'Add half-width spaces between Chinese and English/numbers',
                'Maintain consistent quotation marks',
                "Directly address the user with '你'"
            ],
            'ui_guidelines': {
                'error_messages': "Standardize with phrases like '无法…', handle placeholders correctly",
                'version_strings': 'Translate version strings with copyright information',
                'ui_elements': 'Ensure UI elements remain consistent',
                'keyboard_shortcuts': [
                    "Format shortcuts as '名称(&大写字母)'",
                    'Retain English key names (Alt, Ctrl)',
                    "Translate others (e.g., Spacebar → '空格键', Windows key → 'Windows 键')",
                    'Use industry-standard translations for common shortcut combinations'
                ]
            }
        },
        'German': {
            'language_style': {
                'tone': 'formal, natural, and empathetic',
                'formality': "using formal 'Sie' form for adults, 'du' for children/teens under 18",
                'audience': "adapt tone to context, using 'wir' when a personal touch is needed"
            },
            'translation_principles': [
                'Use natural, everyday conversational language that does not sound robotic',
                'Avoid word-for-word translation; adapt sentences for natural German flow',
                'Split or shorten sentences when needed for clarity and conciseness',
                'Prefer short, simple words from everyday language',
                'Integrate English technical terms according to German grammar and syntax rules',
                'Avoid false friends and awkward anglicisms'
            ],
            'terminology_guidelines': {
                'product_names': 'Keep application and product names in English unless a legally required German form exists',
                'technical_terms': 'Integrate English technical terms according to German grammar rules',
                'specific_translations': "Always translate 'AI' consistently into German"
            },
            'grammar_rules': [
                'Follow German grammar and syntax rules strictly',
                'Pay attention to articles, compound words, genitive case, agreement, verbs, prepositions, punctuation',
                'Maintain proper German sentence structure',
                'Format error messages consistently using established German patterns'
            ],
            'ui_guidelines': {
                'error_messages': 'Use consistent, non-literal phrasing following standard German patterns',
                'placeholders': 'Pay attention to placeholders (%s, %d) and their grammatically correct integration'
            }
        },
        'French': {
            'language_style': {
                'tone': 'natural and conversational',
                'formality': "using formal 'vous' form",
                'audience': 'tailor vocabulary to audience (general vs technical)'
            },
            'translation_principles': [
                'Use everyday conversational language tailored to the audience',
                'Prefer simple words for general audiences, technical terms for professionals',
                'Do not translate word-for-word; prioritize natural French expression',
                'Adapt content by merging, splitting, or removing elements as needed',
                'Prefer short and common words over lengthy or rare expressions',
                'Avoid impersonal forms like \'on\', \'il faut\', \'c\'est\'',
                'Maintain consistent terminology and style throughout the translation'
            ],
            'terminology_guidelines': {
                'product_names': 'Keep product names and brands in English unless legally required',
                'vocabulary_choices': [
                    'Avoid terms like \'invariablement\', \'pléthore\'',
                    'Use precise, common French vocabulary'
                ]
            },
            'grammar_rules': [
                'Follow French grammar, syntax and punctuation rules precisely',
                'Use proper articles, capitalization, and liaisons',
                'Prefer simple tenses (present, passé composé)',
                'Use proper spacing with French-style quotation marks « »',
                'Add non-breaking spaces before punctuation marks ; ! : ?'
            ],
            'ui_guidelines': {
                'user_address': "Address the user directly using 'vous' (masculine singular), never 'on'",
                'error_messages': 'Make error messages empathetic and natural; always end with a period',
                'placeholders': 'Handle reserved spaces (%s, %d) correctly with proper grammar',
                'keyboard_shortcuts': 'Carefully preserve or adapt key names and shortcuts (« Suppr », « Maj »)'
            }
        },
        'Spanish': {
            "language_style": {
                "tone": "natural and conversational",
                "formality": "informal, using 'tú' and 'vosotros'",
                "region": "Spain"
            },
            "translation_principles": [
                "Avoid literal word-for-word translations",
                "Focus on conveying overall meaning and intent clearly",
                "Use simple, common words and phrases",
                "Prefer short, everyday vocabulary",
                "Do not use English abbreviations unless a natural Spanish equivalent exists",
                "Use synonyms for natural and fluid tone",
                "Use primarily simple present tense",
                "Translate fragments into simple, natural Spanish expressions",
                "Localize cultural idioms by meaning, not literal translation",
                "Translate 'media' as 'contenido multimedia' when referring to digital content (not mass media)",
                "Use 'video' without an accent, not 'vídeo'",
                "Use 'Ropa gruesa' for 'Heavy Clothing' instead of 'pesada'",
                "Improve flow and precision for terms like 'highlights' and 'matching captions'; prefer idiomatic phrases for 'instantly' in promos",
                "Make translations concise and idiomatic for terms like 'Professional Headshot' (e.g., 'Retrato profesional')",
                "Ensure possessive pronouns and nouns are correctly translated, integrating 'GenAI' naturally",
                "In software/UI context, use the correct term for 'feature' (avoid 'rasgo' unless referring to human or facial features)",
                "Rephrase messages about unsaved changes for clarity and naturalness in UI contexts"
            ],
            "terminology_guidelines": {
                "forbidden_replacements": [
                    {
                        "avoid": "abortar",
                        "use": "anular"
                    },
                    {
                        "avoid": "entrenamiento",
                        "use": "formación"
                    },
                    {
                        "avoid": "subtítulos acordes",
                        "use": "subtítulos sincronizados"
                    },
                    {
                        "avoid": "ardiente",
                        "use": "en llamas"
                    }
                ],
                "product_names": "Keep in English, do not translate",
                "trademarks": "Keep in English, do not translate"
            },
            "grammar_rules": [
                "Follow Spanish grammar, orthography, punctuation precisely",
                "Minimize use of pronouns, especially formal ones like 'usuario'",
                "Omit pronouns if context is clear"
            ],
            "ui_guidelines": {
                "error_messages": "Make natural, empathetic, concise, and properly punctuated; avoid exclamation marks",
                "keyboard_shortcuts": "Follow instructions exactly for keyboard shortcuts and key names formatting"
            }
        },
        'Japanese': {
            'language_style': {
                'tone': 'natural and conversational',
                'formality': "using Desu-masu style (ですます調) for general content",
                'audience': 'tailor vocabulary to audience (general vs technical)'
            },
            'translation_principles': [
                'Use everyday conversational tone; avoid formal or technical jargon in consumer content',
                'Capture intent and rewrite for natural Japanese flow, not word-for-word translation',
                'Split or simplify sentences and omit unnecessary descriptors as needed',
                'Localize colloquialisms, idioms, and metaphors by conveying their meaning',
                'Prefer simple everyday words (e.g., アプリ vs. アプリケーション, 選ぶ vs. 選択する)',
                'Avoid formal expressions like \'可能です\', \'推奨します\', \'無効です\'',
                'Avoid \'および\' after lists and superlatives/absolutes (完全, 最高, 永久, 世界一)',
                'Omit explicit subjects when natural; use \'管理者\', \'ユーザー\', or \'お客様\' for clarity',
                'Avoid \'あなた\' unless absolutely necessary; omit \'私たち\' unless needed',
                'Be polite and friendly; ask questions with \'…しますか?\' instead of \'…してもよろしいですか?\''
            ],
            'terminology_guidelines': {
                'product_names': 'Do not translate placeholders ({1}, %s), escape characters (\\n, \\r), registry keys',
                'preservation_rules': [
                    'Do not translate version strings (except FileDescription), version numbers (e.g., 4.2)',
                    'Do not translate URLs (\'http://\', \'www\', \'dot\')',
                    'Apply trademark notation (TM or ®) correctly according to resources'
                ]
            },
            'grammar_rules': [
                'Follow Japanese grammar and orthography rules',
                'Use full-width Katakana vs. half-width English',
                'Apply proper hyphenation and compound spacing rules',
                'Use ideographic commas/periods (、。) and proper punctuation',
                'Apply correct numeric rules (Arabic vs. Chinese numerals, half-width digits)',
                'Use simple verb forms (present tense preferred)',
                'Avoid causative \'～させる\' unless necessary',
                'Use \'～します\' instead of \'nounを実行します\'',
                'Avoid double negatives',
                'Translate gerunds as \'～しています\' or \'～中\'',
                'Express \'must\' as \'～する必要がある\' and \'may\' as \'～場合がある\'',
                'Use passive voice for system actions and active voice for user actions'
            ],
            'ui_guidelines': {
                'ui_text': [
                    'Apply Desu-masu style for general sentences and explanatory UI text',
                    'Use Dearu style (である調) or noun phrases (体言止め) for brief UI elements',
                    'Prompt actions with \'…してください。\'',
                    'Translate UI labels using bracket conventions: [メニュー], [チェックボックス]',
                    'Use full-width 「」 or 『』 for section titles, angle brackets (<>) for variables',
                    'Include Japanese translation for English UI terms in parentheses (例: Save（保存）)'
                ],
                'error_messages': [
                    'Start with \'申し訳ございません\' in Desu-masu style',
                    'Guide actions with \'…してください。\'',
                    'Use noun-phrase titles/buttons',
                    'Handle placeholders correctly, preserving or reordering as needed'
                ],
                'keyboard_shortcuts': [
                    "Capitalize English names + 'キー' (例: Enterキー, Arrowキー)",
                    'Use 方向キー for arrow keys',
                    "Combine shortcuts with half-width plus sign (+) without spaces",
                    "Format access keys as Term(C) with key in parentheses (例: 保存(S))"
                ]
            }
        },
        "Korean": {
            "language_style": {
                "tone": "natural and conversational",
                "formality": "use '-세요' endings for general content",
                "audience": "adjust vocabulary based on the audience (general vs. technical)"
                },
            "translation_principles": [
                "Use simple words for general consumers and technical terms for technical audiences",
                "Focus on producing natural, idiomatic Korean rather than translating word-for-word",
                "Rephrase sentences to sound like they were originally written in Korean",
                "Avoid archaic Hanja and complex terminology",
                "Use active verbs and simple, short words"
                ],
            "terminology_guidelines": {
                "product_names": "Keep product names in English as they are",
                "version_strings": "Translate version and copyright notices accurately",
                "examples": [
                    {"Korean": "'모션 트래킹' 또는 '모션 추적'의 경우 일관성을 위해 '지원하지 않습니다'를 사용하세요.","avoid": "'지원하지 않습니다'는 피하세요."},
                    {"Korean": "'객체'는 '분할', '개체'는 '분류'를 사용할 때 객체 추적 또는 분류의 특정 맥락에 맞게 사용하세요.","avoid": "'객체'와 '개체'의 혼용을 피하세요."},
                    {"Korean": "'힌디어'를 사용하고 '힌디'는 피하세요.","avoid": "'힌디' 사용을 피하세요."},
                    {"Korean": "'말레이시아어'를 사용하고 '말레이어'는 덜 정확하므로 피하세요.","avoid": "'말레이어' 사용을 피하세요."},
                    {"Korean": "'차원을 넘는'을 사용하여 문장을 더 시적이고 덜 문자 그대로 전달하세요.","avoid": "'차원을 여행하며'는 피하세요."},
                    {"Korean": "'가져온'을 사용하고 '수입된'은 피하세요.","avoid": "'수입된' 사용을 피하세요."},
                    {"Korean": "'드래그하여'를 사용하여 이미지를 추가하고, 이미지를 드롭하는 경우 '이미지를 추가하려면 드롭하세요'를 사용하세요.","avoid": "'이미지를 드래그하여'와 같은 불분명한 표현은 피하세요."},
                    {"Korean": "'음소거'는 오디오를 음소거하고, '음소거 해제'는 음소거를 해제할 때 사용하세요.","avoid": "'소리 끄기'와 같은 불명확한 표현은 피하세요."},
                    {"Korean": "'클릭하여 마스크 선택에 추가하거나 제거하세요'를 사용하여 더 명확한 지침을 제공하세요.","avoid": "'마스크를 선택하거나 제거'는 피하세요."},
                    {"Korean": "'객체 추적'에서는 '객체'를 사용하세요. 이는 더 공식적입니다.","avoid": "'개체 추적'을 피하세요."},
                    {"Korean": "'가져오는 중'은 더 구어체로 들리며, '임포트하는 중'은 더 격식 있는 표현입니다.","avoid": "'임포트하는 중'을 사용할 때는 문맥에 맞게 사용하세요."},
                    {"Korean": "'리빌'은 비공식적이거나 브랜드에 특화된 용어에서 사용되며, '밝히기'는 더 공식적이고 전통적인 표현입니다.","avoid": "'밝히기'만 사용할 때는 너무 공식적이지 않게 표현해야 합니다."},
                    {"Korean": "'읽기'는 일반적인 읽기의 행위를 나타내고, '읽음'은 읽었다는 상태를 나타냅니다.","avoid": "'읽음'을 사용할 때는 상태를 명확히 구분하세요."},
                    {"Korean": "'되돌아가기'는 내비게이션이나 역사에서 돌아가는 것에 대해 사용하고, '반환'은 객체나 항목의 반환에 대해 사용하세요.","avoid": "'뒤로 가기'와 같은 일반적인 표현은 피하세요."},
                    {"Korean": "'리턴'은 이전 단계나 상태로 돌아갈 때 사용하고, '뒤로'는 물리적으로나 비유적으로 뒤로 갈 때 사용하세요.","avoid": "'뒤로 가기'는 문맥에 맞게 피하세요."},
                    {"Korean": "'자세히 보기'는 더 자세한 정보를 볼 때 사용하고, '더 보기'는 '보기 더 보기'로 해석됩니다.","avoid": "'더 보기'만 사용할 때는 과도하게 간결한 표현으로 피하세요."}
                ]
            },
            "grammar_rules": [
                "Use '~하고 있습니다' or '~하는 중' to indicate ongoing actions",
                "Match tenses to the source text, defaulting to simple present when appropriate",
                "End sentences with '~하세요' or '~합니다' and use a period",
                "Preserve punctuation from the source text in non-full sentences"
                ],
            "ui_guidelines": {
                "acronyms": [
                    "Format acronyms as 'ABC (full spelling)'",
                    "Use Korean full spelling for acronyms commonly used in Korean, otherwise use English",
                    "Keep acronyms in uppercase and drop plural 's' when needed",
                    "Follow English conventions for English abbreviations",
                    "Use Korean abbreviations for weekdays and English for months/days"
                ],
                "ui_elements": "Enclose UI terms in square brackets [ ] and preserve double quotes for quoted strings",
                "placeholders": [
                    "For numbered placeholders (%1, %2), reorder them as needed to match natural sentence flow",
                    "For non-numbered placeholders (%s), keep their original order",
                    "Attach measurement units directly after numeric placeholders (%d) without a space",
                    "Add appropriate postpositions (은(는), 이(가), 을(를), 과(와), (으)로) after placeholders"
                ],
                "keyboard_shortcuts": [
                    "Add '키' after single key names (e.g., Shift, Ctrl, Alt, Enter)",
                    "Wrap key names in angle brackets (<Shift 키>)",
                    "Avoid using angle brackets in manuals or help text",
                    "For ampersand (&) shortcuts, append '&X' (e.g., '저장&S')"
                ]
            }
        },
        "Italian": {
            "language_style": {
                "tone": "informal and friendly",
                "formality": "use 'tu' and 'voi' forms",
                "naturalness": "focus on natural flow, not literal translation"
            },
            "translation_principles": [
                "Avoid word-for-word translations that sound weird",
                "Focus on meaning and natural Italian phrases",
                "Use short, simple, common Italian words",
                "It's okay to use sentence fragments sometimes, but not too much",
                "Avoid very formal, technical, or rare words",
                "Translate phrases like 'stored on the cloud' and 'local storage' naturally",
                "Replace '&' with 'e' (and)",
                "Use a neutral subject ('i video generati') instead of 'tuoi video generati'",
                "Prefer 'salvare' over 'archiviare'",
                "Use 'cloud' rather than 'server cloud'",
                "Use 'disco fisso' instead of 'memoria locale'",
                "Frame download suggestion in imperative form: 'Ti consigliamo di scaricare sul tuo disco fisso quelli che vuoi salvare'",
                "Prefer 'celeste infuocata' over 'celestiale infuocata' when describing the goddess",
                "Place the adjective 'eterea' before 'regina oceanica' to mirror the desired rhythm",
                "Use 'fino alle profondità di' instead of 'nelle profondità di' to emphasize extension of the journey",
                "***Additional English notes to force specific structures***",
                "- Use 'salvare' instead of 'archiviare' so the output reads 'saranno salvati' rather than 'saranno archiviati'.",
                "- Replace 'server cloud' with 'cloud' so it reads 'saranno salvati nella cloud'.",
                "- Replace 'memoria locale' with 'disco fisso' so it reads 'sul tuo disco fisso'.",
                "- Use 'quelli che vuoi salvare' instead of 'quelli che desideri conservare' for a more direct, informal suggestion.",
                "- For media-import messages, always append 'in corso' after 'Importazione dei file multimediali' and use the single-character ellipsis '…' so it reads exactly: 'Importazione dei file multimediali in corso…'",
                "***Prefer the following stylistic choices to match the second sentence versions***",
                "- Use 'sorprendenti e artistiche' instead of 'straordinarie' when describing images with rich details.",
                "- Use the inclusive or neutral pronoun form 'te stessə' rather than 'te stesso' or 'te stessa'.",
                "- Prefer 'È richiesto' over 'È necessario' when stating requirements for visible faces.",
                "- Use the more concise and informal phrasing such as 'somiglianza volto' and 'stile ad hoc' instead of the more formal 'somiglianza del volto' and 'stile personalizzato'.",
                "- Prefer adjective order 'uno stile nuovo' instead of 'un nuovo stile'.",
            ],
            "terminology_guidelines": {
                "product_names": "Keep in English unless there is a common Italian name",
                "loanwords": "Use common Italian loanwords used in the field",
                "examples": [
                    {"english": "Motion Tracking", "italian": "Tracking di Movimento", "avoid": "Inseguitore movimento"},
                    {"english": "Script", "italian": "Testo", "context": "UI", "avoid": "Sceneggiatura"},
                    {"english": "Key Highlights", "italian": "Caratteristiche Chiave", "avoid": "Punti Salienti"},
                    {"english": "media", "italian": "Contenuti", "context": "digital content", "avoid": "Media"},
                    {"english": "outline", "italian": "linee generali", "context": "image generation", "avoid": "contorno"},
                    {"english": "outline reference", "italian": "linee generali di riferimento"},
                    {"english": "face/pose", "italian": "volto/viso"},
                    {"english": "download", "italian": "download", "context": "noun"},
                    {"english": "download", "italian": "scarica", "context": "verb"},
                    {"english": "trimmed", "italian": "accorciata", "context": "video clip"},
                    {"english": "delete the task", "italian": "annulla l'operazione"},
                    {"english": "task", "italian": "operazione", "context": "software UI and workflow"},
                    {"english": "sound", "italian": "suoni"},
                    {"english": "AI", "italian": "l'AI"},
                    {"english": "celestial goddess", "italian": "dea celeste"},
                    {"english": "fiery", "italian": "infuocata"},
                    {"english": "ethereal", "italian": "eterea"},
                    {"english": "ocean queen", "italian": "regina oceanica"},
                    {"english": "enchanted underwater realm", "italian": "regno sottomarino incantato"},
                    {"english": "descend from the sky into the depths", "italian": "scendere dal cielo fino alle profondità"}
                ]
            },
            "grammar_rules": [
                "Follow Italian grammar rules carefully",
                "Use correct articles, gender, plurals, prepositions, and pronouns",
                "Use natural sentence order and punctuation",
                "Prefer present tense and simple verbs",
                "Put adjectives after nouns (except where overridden by translation_principles)",
                "Avoid unnecessary 'di'",
                "Use singular/plural as sounds natural",
                "For 'task' assume '%s' means 'regola' (rule), match gender/number",
                "Use 'l'' before 'AI' (dall'AI)",
                "Say 'è inferiore a' for 'less than' and 'di almeno' for 'larger than' in minimum resolution",
                "Translate 'face and pose references are used' as 'volto sia posa di riferimento'",
                "Use plural 'suoni' for 'sound' and always include article for 'AI' ('l'AI')"
            ],
            "ui_guidelines": {
                "consistency": "Use same terms everywhere",
                "messages": "Make messages clear, friendly, and kind",
                "error_format": "Format errors as '[ProductName]: [message]' when needed",
                "placeholders": "Keep placeholders (%s, %d, %@) and adjust grammar naturally",
                "capitalization": "Use Italian capitalization rules – lowercase common nouns/adjectives except at sentence start or official names",
                "example_translation": "Translate 'Drag the clips to arrange their order for your video' naturally, e.g. 'stabilirne l'ordine nel tuo video'"
            }
        },
        'Dutch': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        },
        'Portuguese (Brazil)': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        },
        'Russian': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        },
        'Hindi': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        },
        'Indonesian': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        },
        'Malay': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        },
        'Thai': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        }
    }

    
    # Check for specific language match or fallback to general language category
    for lang_key, guidance in language_guidance.items():
        if lang_key in target_lang:
            print(f"Matched language: {lang_key}")
            # If guidance is empty, return empty string
            if not guidance:
                return ""
            # Otherwise, return JSON string
            json_guidance = json.dumps(guidance, ensure_ascii=False, indent=2)
            print(f"Generated language-specific guidance in JSON format")
            return json_guidance
            
    # Default guidance if no specific match is found
    return ""


def get_lang_specific_review_sys_prompt(target_lang):
    """
    Provides language-specific translation guidance based on target language.
    
    :param target_lang: Target language for translation
    :return: JSON string with language-specific translation instructions
    """

    # Language-specific guidance dictionary
    language_guidance = {
        'English': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        },
        'Traditional Chinese': {
            'language_style': {
                'tone': 'natural and conversational',
                'formality': "using formal '您' form",
                'audience': 'adapt tone to context, avoiding overly formal or technical language unless needed'
            },
            'translation_principles': [
                'Use everyday, conversational language appropriate to the audience',
                'Ensure translations sound natural for Traditional Chinese customers',
                'Adapt meaning rather than translating literally',
                'Prefer short, simple words for clarity and readability',
                'Omit pronouns when context is clear'
            ],
            'terminology_guidelines': {
                'preferred_terms': [
                    {'English': 'PC', 'Chinese': '電腦'},
                    {'English': 'customer service', 'Chinese': '客服'},
                    {'English': 'template', 'Chinese': '範本'},
                    {'English': 'video', 'Chinese': '影片'},
                    {'English': 'quality', 'Chinese': '品質'}
                ],
                'product_names': 'Keep product names and trademarks in English unless an approved translation exists',
                'components': 'Distinguish built-in component labels from general terms',
                'avoid': 'Avoid awkward colloquialisms and incorrect terminology'
            },
            'grammar_rules': [
                'Follow Traditional Chinese grammar and punctuation rules',
                'Use half-width spaces around English text',
                'Use proper Chinese punctuation marks',
                'Handle articles, possessives, and conjunctions correctly',
                'Avoid gendered pronouns in generic references',
                "Address the user directly with '您'"
            ],
            'ui_guidelines': {
                'error_messages': "Use consistent terminology with phrases like '無法…', '找不到…', '記憶體不足'",
                'keyboard_shortcuts': [
                    "Translate key names like 'Spacebar' to '空格鍵'",
                    'Keep technical key names in English (Alt, Ctrl)',
                    'Format UI elements in square brackets [ ]',
                    "For strings with shortcuts, use '文字(快捷鍵符號+大寫鍵字)', e.g., '結束(&E)'"
                ],
                'placeholders': 'Handle placeholders properly while maintaining grammatical correctness'
            }
        },
        'Simplified Chinese': {
            'language_style': {
                'tone': 'natural and conversational',
                'formality': "using direct '你' form",
                'audience': 'adapt tone to context, avoiding overly formal or technical phrasing unless needed'
            },
            'translation_principles': [
                'Use natural, conversational tone appropriate to the context',
                'Never translate word-for-word; capture overall intent and style',
                'Rewrite as needed for CHS readers to ensure natural flow',
                'Omit pronouns when context is clear',
                "Use neutral role terms (e.g., '人员', '个人') to avoid gendered pronouns"
            ],
            'terminology_guidelines': {
                'preferred_terms': [
                    {'English': 'app', 'Chinese': '应用'},
                    {'English': 'PC', 'Chinese': '电脑'},
                    {'English': 'select', 'Chinese': '选择'},
                    {'English': 'USB drive', 'Chinese': 'U 盘'}
                ],
                'product_names': 'Keep product names and trademarks in English unless an approved CHS name exists',
                'components': 'Localize built-in component labels only where appropriate',
                'avoid': 'Steer clear of disallowed colloquialisms or network slang'
            },
            'grammar_rules': [
                'Adhere to Simplified Chinese grammar and punctuation rules',
                'Use full-width punctuation marks （，。！？：”“、《》）',
                'Use wave dash (~) for ranges, en dash (–) for minus signs',
                'Add half-width spaces between Chinese and English/numbers',
                'Maintain consistent quotation marks',
                "Directly address the user with '你'"
            ],
            'ui_guidelines': {
                'error_messages': "Standardize with phrases like '无法…', handle placeholders correctly",
                'version_strings': 'Translate version strings with copyright information',
                'ui_elements': 'Ensure UI elements remain consistent',
                'keyboard_shortcuts': [
                    "Format shortcuts as '名称(&大写字母)'",
                    'Retain English key names (Alt, Ctrl)',
                    "Translate others (e.g., Spacebar → '空格键', Windows key → 'Windows 键')",
                    'Use industry-standard translations for common shortcut combinations'
                ]
            }
        },
        'German': {
            'language_style': {
                'tone': 'formal, natural, and empathetic',
                'formality': "using formal 'Sie' form for adults, 'du' for children/teens under 18",
                'audience': "adapt tone to context, using 'wir' when a personal touch is needed"
            },
            'translation_principles': [
                'Use natural, everyday conversational language that does not sound robotic',
                'Avoid word-for-word translation; adapt sentences for natural German flow',
                'Split or shorten sentences when needed for clarity and conciseness',
                'Prefer short, simple words from everyday language',
                'Integrate English technical terms according to German grammar and syntax rules',
                'Avoid false friends and awkward anglicisms'
            ],
            'terminology_guidelines': {
                'product_names': 'Keep application and product names in English unless a legally required German form exists',
                'technical_terms': 'Integrate English technical terms according to German grammar rules',
                'specific_translations': "Always translate 'AI' consistently into German"
            },
            'grammar_rules': [
                'Follow German grammar and syntax rules strictly',
                'Pay attention to articles, compound words, genitive case, agreement, verbs, prepositions, punctuation',
                'Maintain proper German sentence structure',
                'Format error messages consistently using established German patterns'
            ],
            'ui_guidelines': {
                'error_messages': 'Use consistent, non-literal phrasing following standard German patterns',
                'placeholders': 'Pay attention to placeholders (%s, %d) and their grammatically correct integration'
            }
        },
        "French": {
            "language_style": {
                "tone": "natural and conversational",
                "formality": "using formal 'vous' form",
                "audience": "tailor vocabulary to audience (general vs technical)"
                },
            "translation_principles": [
                "Use conversational language suited to the audience",
                "Use simple words for general audiences, technical terms for professionals",
                "Don't translate word-for-word, focus on natural French",
                "Adapt content by merging, splitting, or removing parts as needed",
                "Use short, common words over rare or long ones",
                "Avoid impersonal forms like 'on', 'il faut', 'c'est'",
                "Maintain consistent style and terminology"
                ],
            "terminology_guidelines": {
                "product_names": "Keep product names and brands in English unless legally required",
                "vocabulary_choices": [
                    "Avoid complex words like 'invariablement', 'pléthore'",
                    "Use clear, precise vocabulary"
                    ]
                },
            "grammar_rules": [
                "Follow French grammar, syntax, and punctuation rules precisely",
                "Use proper articles, capitalization, and liaisons",
                "Prefer simple tenses (present, passé composé)",
                "Use French-style quotation marks « »",
                "Add non-breaking spaces before punctuation marks ; ! : ?"
                ],
            "ui_guidelines": {
                "user_address": "Address the user directly using 'vous', never 'on'",
                "error_messages": "Keep error messages empathetic and natural, ending with a period",
                "placeholders": "Handle reserved spaces correctly (%s, %d) with proper grammar",
                "keyboard_shortcuts": "Adapt key names like « Suppr », « Maj » carefully"
                },
            "translation_tips": [
                { "term": "cloud", "description": "Use 'cloud' instead of 'à distance' or 'nuagique.'" },
                { "term": "Les crédits ont été remboursés", "description": "Include 'credits refunded' for completeness." },
                { "term": "D'origine", "description": "Use for original content. Avoid 'section découpée.'" },
                { "term": "Début et de fin", "description": "For video start and end. Avoid 'cadres.'" },
                { "term": "Média", "description": "Use for media/files. Avoid 'données' (data)." },
                { "term": "Nuagique", "description": "'Cloud' is the more accurate term for cloud services." },
                { "term": "À ajouter ou à supprimer", "description": "This is the standard phrasing for adding/removing." },
                { "term": "Effet de frappe", "description": "Use this for typing effect. Avoid 'tapement.'" },
                { "term": "Révéler", "description": "Use for revealing or showing something hidden." },
                { "term": "Mise au point", "description": "This refers to focus in photography. Avoid 'focaliser.'" },
                { "term": "Revenir en arrière", "description": "Use this for 'go back.' Avoid 'rebrousser chemin.'" },
                { "term": "Retour", "description": "Use for 'return.' Avoid 'reculer,' which means retreat." },
                { "term": "Retourner", "description": "Use for 'return' or 'turn back.' Avoid 'revenir.'" },
                { "term": "Voir plus", "description": "This means 'see more.' Avoid 'explorer davantage.'" },
                { "term": "Sélectionnée", "description": "Ensure this agrees with the number (singular/plural)." },
                { "term": "Commencer à générer", "description": "Use this instead of 'débuter la création.'" },
                { "term": "Composition de l'image", "description": "Refers to image structure. Avoid 'structure de l'image.'" },
                { "term": "Portrait photo", "description": "This is the correct term for a personal portrait." },
                { "term": "À l'aide de l'IA", "description": "Clearly indicates using AI." },
                { "term": "Look", "description": "Use 'apparence' for a more professional term." },
                { "term": "Appareils photo", "description": "Correct term for cameras. Avoid 'caméras.'" },
                { "term": "Pack", "description": "Refers to a package or bundle." },
                { "term": "Photo", "description": "Use 'photo' for a picture. Avoid 'visuel.'" },
                { "term": "Sélectionnée(s)", "description": "Must match the number (singular/plural)." },
                { "term": "Pourrait", "description": "'Could' expresses possibility. Avoid 'peut.'" },
                { "term": "Style artistique", "description": "Refers to artistic style. Avoid 'style esthétique.'" },
                { "term": "Commencer à générer", "description": "Use for starting generation, not 'commencer à créer.'" },
                { "term": "Images", "description": "Use 'images' for pictures, not 'fichiers.'" }
            ]
        },
        'Spanish': {
            "language_style": {
                "tone": "natural and conversational",
                "formality": "informal (use 'tú' and 'vosotros')",
                "region": "Spain"
            },
            "Accuracy": [
                "Don't translate word-for-word; focus on clear meaning",
                "Use simple, natural Spanish phrases",
                "Use mainly simple present tense",
                "Translate possessives correctly, include 'GenAI' naturally"
            ],
            "Native Usage": [
                "Use common, simple words and everyday phrases",
                "Use synonyms to sound natural and fluent",
                "Translate idioms by meaning, not literally",
                "Use idiomatic phrases for things like 'instantly' in promos",
                "Translate 'Professional Headshot' as 'Retrato profesional'",
                "Use 'video' without accent",
                "Say 'Ropa gruesa' for 'Heavy Clothing'",
                "Use correct word for software 'feature' (not 'rasgo' unless facial/human feature)"
            ],
            "Word Correctness": [
                "Avoid English abbreviations unless Spanish equivalent exists",
                "Translate 'media' as 'contenido multimedia' (for digital content)",
                "Keep product names and trademarks in English",
                "Never use 'abortar', use 'anular'",
                "Never use 'entrenamiento', use 'formación'"
            ],
            "Sentence Structure": [
                "Make sentences flow well, especially for terms like 'highlights' and 'matching captions'",
                "Rewrite UI messages about unsaved changes clearly and naturally",
                "Follow Spanish grammar and punctuation strictly",
                "Use few pronouns, avoid formal ones like 'usuario'",
                "Skip pronouns if context is clear",
                "Only capitalize the first letter of nouns or the first word of a sentence; all other letters should be lowercase"
            ],
            "Consistency with Reference": [
                "Always keep product names and trademarks in English",
                "Follow exact keyboard shortcut and key name instructions",
                "Make error messages natural, kind, short, and without exclamation marks"
            ]
        },
        'Japanese': {
            'language_style': {
                'tone': 'natural and conversational',
                'formality': "using Desu-masu style (ですます調) for general content",
                'audience': 'tailor vocabulary to audience (general vs technical)'
            },
            'translation_principles': [
                'Use everyday conversational tone; avoid formal or technical jargon in consumer content',
                'Capture intent and rewrite for natural Japanese flow, not word-for-word translation',
                'Split or simplify sentences and omit unnecessary descriptors as needed',
                'Localize colloquialisms, idioms, and metaphors by conveying their meaning',
                'Prefer simple everyday words (e.g., アプリ vs. アプリケーション, 選ぶ vs. 選択する)',
                'Avoid formal expressions like \'可能です\', \'推奨します\', \'無効です\'',
                'Avoid \'および\' after lists and superlatives/absolutes (完全, 最高, 永久, 世界一)',
                'Omit explicit subjects when natural; use \'管理者\', \'ユーザー\', or \'お客様\' for clarity',
                'Avoid \'あなた\' unless absolutely necessary; omit \'私たち\' unless needed',
                'Be polite and friendly; ask questions with \'…しますか?\' instead of \'…してもよろしいですか?\''
            ],
            'terminology_guidelines': {
                'product_names': 'Do not translate placeholders ({1}, %s), escape characters (\\n, \\r), registry keys',
                'preservation_rules': [
                    'Do not translate version strings (except FileDescription), version numbers (e.g., 4.2)',
                    'Do not translate URLs (\'http://\', \'www\', \'dot\')',
                    'Apply trademark notation (TM or ®) correctly according to resources'
                ]
            },
            'grammar_rules': [
                'Follow Japanese grammar and orthography rules',
                'Use full-width Katakana vs. half-width English',
                'Apply proper hyphenation and compound spacing rules',
                'Use ideographic commas/periods (、。) and proper punctuation',
                'Apply correct numeric rules (Arabic vs. Chinese numerals, half-width digits)',
                'Use simple verb forms (present tense preferred)',
                'Avoid causative \'～させる\' unless necessary',
                'Use \'～します\' instead of \'nounを実行します\'',
                'Avoid double negatives',
                'Translate gerunds as \'～しています\' or \'～中\'',
                'Express \'must\' as \'～する必要がある\' and \'may\' as \'～場合がある\'',
                'Use passive voice for system actions and active voice for user actions'
            ],
            'ui_guidelines': {
                'ui_text': [
                    'Apply Desu-masu style for general sentences and explanatory UI text',
                    'Use Dearu style (である調) or noun phrases (体言止め) for brief UI elements',
                    'Prompt actions with \'…してください。\'',
                    'Translate UI labels using bracket conventions: [メニュー], [チェックボックス]',
                    'Use full-width 「」 or 『』 for section titles, angle brackets (<>) for variables',
                    'Include Japanese translation for English UI terms in parentheses (例: Save（保存）)'
                ],
                'error_messages': [
                    'Start with \'申し訳ございません\' in Desu-masu style',
                    'Guide actions with \'…してください。\'',
                    'Use noun-phrase titles/buttons',
                    'Handle placeholders correctly, preserving or reordering as needed'
                ],
                'keyboard_shortcuts': [
                    "Capitalize English names + 'キー' (例: Enterキー, Arrowキー)",
                    'Use 方向キー for arrow keys',
                    "Combine shortcuts with half-width plus sign (+) without spaces",
                    "Format access keys as Term(C) with key in parentheses (例: 保存(S))"
                ]
            }
        },
        "Korean": {
            "language_style": {
                "tone": "natural and conversational",
                "formality": "use '-세요' endings for general content",
                "audience": "adjust vocabulary based on the audience (general vs. technical)"
                },
            "translation_principles": [
                "Use simple words for general consumers and technical terms for technical audiences",
                "Focus on producing natural, idiomatic Korean rather than translating word-for-word",
                "Rephrase sentences to sound like they were originally written in Korean",
                "Avoid archaic Hanja and complex terminology",
                "Use active verbs and simple, short words"
                ],
            "terminology_guidelines": {
                "product_names": "Keep product names in English as they are",
                "version_strings": "Translate version and copyright notices accurately",
                "examples": [
                    {"Korean": "'모션 트래킹' 또는 '모션 추적'의 경우 일관성을 위해 '지원하지 않습니다'를 사용하세요.","avoid": "'지원하지 않습니다'는 피하세요."},
                    {"Korean": "'객체'는 '분할', '개체'는 '분류'를 사용할 때 객체 추적 또는 분류의 특정 맥락에 맞게 사용하세요.","avoid": "'객체'와 '개체'의 혼용을 피하세요."},
                    {"Korean": "'힌디어'를 사용하고 '힌디'는 피하세요.","avoid": "'힌디' 사용을 피하세요."},
                    {"Korean": "'말레이시아어'를 사용하고 '말레이어'는 덜 정확하므로 피하세요.","avoid": "'말레이어' 사용을 피하세요."},
                    {"Korean": "'차원을 넘는'을 사용하여 문장을 더 시적이고 덜 문자 그대로 전달하세요.","avoid": "'차원을 여행하며'는 피하세요."},
                    {"Korean": "'가져온'을 사용하고 '수입된'은 피하세요.","avoid": "'수입된' 사용을 피하세요."},
                    {"Korean": "'드래그하여'를 사용하여 이미지를 추가하고, 이미지를 드롭하는 경우 '이미지를 추가하려면 드롭하세요'를 사용하세요.","avoid": "'이미지를 드래그하여'와 같은 불분명한 표현은 피하세요."},
                    {"Korean": "'음소거'는 오디오를 음소거하고, '음소거 해제'는 음소거를 해제할 때 사용하세요.","avoid": "'소리 끄기'와 같은 불명확한 표현은 피하세요."},
                    {"Korean": "'클릭하여 마스크 선택에 추가하거나 제거하세요'를 사용하여 더 명확한 지침을 제공하세요.","avoid": "'마스크를 선택하거나 제거'는 피하세요."},
                    {"Korean": "'객체 추적'에서는 '객체'를 사용하세요. 이는 더 공식적입니다.","avoid": "'개체 추적'을 피하세요."},
                    {"Korean": "'가져오는 중'은 더 구어체로 들리며, '임포트하는 중'은 더 격식 있는 표현입니다.","avoid": "'임포트하는 중'을 사용할 때는 문맥에 맞게 사용하세요."},
                    {"Korean": "'리빌'은 비공식적이거나 브랜드에 특화된 용어에서 사용되며, '밝히기'는 더 공식적이고 전통적인 표현입니다.","avoid": "'밝히기'만 사용할 때는 너무 공식적이지 않게 표현해야 합니다."},
                    {"Korean": "'읽기'는 일반적인 읽기의 행위를 나타내고, '읽음'은 읽었다는 상태를 나타냅니다.","avoid": "'읽음'을 사용할 때는 상태를 명확히 구분하세요."},
                    {"Korean": "'되돌아가기'는 내비게이션이나 역사에서 돌아가는 것에 대해 사용하고, '반환'은 객체나 항목의 반환에 대해 사용하세요.","avoid": "'뒤로 가기'와 같은 일반적인 표현은 피하세요."},
                    {"Korean": "'리턴'은 이전 단계나 상태로 돌아갈 때 사용하고, '뒤로'는 물리적으로나 비유적으로 뒤로 갈 때 사용하세요.","avoid": "'뒤로 가기'는 문맥에 맞게 피하세요."},
                    {"Korean": "'자세히 보기'는 더 자세한 정보를 볼 때 사용하고, '더 보기'는 '보기 더 보기'로 해석됩니다.","avoid": "'더 보기'만 사용할 때는 과도하게 간결한 표현으로 피하세요."}
                ]
            },
            "grammar_rules": [
                "Use '~하고 있습니다' or '~하는 중' to indicate ongoing actions",
                "Match tenses to the source text, defaulting to simple present when appropriate",
                "End sentences with '~하세요' or '~합니다' and use a period",
                "Preserve punctuation from the source text in non-full sentences"
                ],
            "ui_guidelines": {
                "acronyms": [
                    "Format acronyms as 'ABC (full spelling)'",
                    "Use Korean full spelling for acronyms commonly used in Korean, otherwise use English",
                    "Keep acronyms in uppercase and drop plural 's' when needed",
                    "Follow English conventions for English abbreviations",
                    "Use Korean abbreviations for weekdays and English for months/days"
                ],
                "ui_elements": "Enclose UI terms in square brackets [ ] and preserve double quotes for quoted strings",
                "placeholders": [
                    "For numbered placeholders (%1, %2), reorder them as needed to match natural sentence flow",
                    "For non-numbered placeholders (%s), keep their original order",
                    "Attach measurement units directly after numeric placeholders (%d) without a space",
                    "Add appropriate postpositions (은(는), 이(가), 을(를), 과(와), (으)로) after placeholders"
                ],
                "keyboard_shortcuts": [
                    "Add '키' after single key names (e.g., Shift, Ctrl, Alt, Enter)",
                    "Wrap key names in angle brackets (<Shift 키>)",
                    "Avoid using angle brackets in manuals or help text",
                    "For ampersand (&) shortcuts, append '&X' (e.g., '저장&S')"
                ]
            }
        },
        "Italian": {
            "language_style": {
                "tone": "Use a casual and friendly tone.",
                "formality": "Use informal 'tu' and plural 'voi' forms.",
                "naturalness": "Make the translation sound natural, not a word-by-word copy."
            },
            "Accuracy": [
                "Don't translate word-for-word if it sounds strange.",
                "Keep the original meaning clear.",
                "Follow Italian grammar rules carefully.",
                "Use correct articles, genders, plurals, and prepositions.",
                "Use mostly present tense and simple verbs.",
                "Translate special phrases like 'stored on the cloud' naturally."
            ],
            "Native Usage": [
                "Use simple and common Italian words.",
                "It's okay to use sentence fragments sometimes, but not too many.",
                "Avoid very formal or rare words.",
                "Use natural sentence order and punctuation.",
                "Place adjectives after nouns.",
                "Avoid using unnecessary 'di'.",
                "Follow Italian capitalization rules."
            ],
            "Word Correctness": [
                "Use the same words consistently everywhere.",
                "Keep placeholders (%s, %d, %@) and make grammar fit naturally.",
                "Replace '&' with 'e' (and).",
                "Use these preferred translations for common terms:",
                "  - 'Motion Tracking' → 'Tracking di Movimento'",
                "  - 'Script' (UI) → 'Testo'",
                "  - 'Key Highlights' → 'Caratteristiche Chiave'",
                "  - 'media' (digital content) → 'Contenuti'",
                "  - 'outline' (image generation) → 'linee generali'",
                "  - 'face/pose' → 'volto/viso'",
                "  - 'download' (noun) → 'download'; (verb) → 'scarica'",
                "  - 'trimmed' (video clip) → 'accorciata'",
                "  - 'delete the task' → 'annulla l'operazione'",
                "  - 'task' (software) → 'operación'",
                "  - 'sound' → 'suoni'",
                "  - 'AI' → 'l'AI'",
                "Match gender and number when using 'task' as 'regola'.",
                "Always include the article with 'l'AI'."
            ],
            "Sentence Structure": [
                "Use natural sentence order and punctuation.",
                "Use simple verbs in present tense.",
                "Put adjectives after nouns.",
                "Avoid unnecessary 'di'.",
                "Use singular or plural forms that sound natural.",
                "Make messages clear, kind, and easy to understand."
            ],
            "Consistency with Reference": [
                "Use the same terms consistently throughout.",
                "Format error messages as '[ProductName]: [message]' when needed.",
                "Translate UI instructions naturally, for example:",
                "  - 'Drag the clips to arrange their order for your video' → 'stabilirne l'ordine nel tuo video'."
            ]
        },
        'Dutch': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        },
        'Portuguese (Brazil)': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        },
        'Russian': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        },
        'Hindi': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        },
        'Indonesian': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        },
        'Malay': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        },
        'Thai': {
            'language_style': {},
            'translation_principles': [],
            'terminology_guidelines': {},
            'grammar_rules': [],
            'ui_guidelines': {}
        }
    }

    
    # Check for specific language match or fallback to general language category
    for lang_key, guidance in language_guidance.items():
        if lang_key in target_lang:
            print(f"Matched language: {lang_key}")
            # If guidance is empty, return empty string
            if not guidance:
                return ""
            # Otherwise, return JSON string
            json_guidance = json.dumps(guidance, ensure_ascii=False, indent=2)
            print(f"Generated language-specific guidance in JSON format")
            return json_guidance
            
    # Default guidance if no specific match is found
    return ""