import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from prompts.prompts_utils import get_lang_specific_translate_sys_prompt


def translate_sys_prompt(src_lang, tgt_lang, software_type, source_type):
    '''
    The character assigned to LLM for Translation.
    :param src_lang: Source language code (e.g., 'English')
    :param tgt_lang: Target language code (e.g., 'Traditional Chinese')
    :param software_type: Type of software being localized
    :return: Formatted system prompt string in JSON format
    '''
    import json
    
    # Fetch and parse language-specific guidance; use default structure if empty or invalid
    guidance_str = get_lang_specific_translate_sys_prompt(tgt_lang)
    default_guidance = {
        'language_style': {},
        'translation_principles': [],
        'terminology_guidelines': {},
        'grammar_rules': [],
        'ui_guidelines': {}
    }
    try:
        language_guidance = json.loads(guidance_str) if guidance_str else default_guidance
    except (ValueError, TypeError):
        language_guidance = default_guidance

    if source_type == "UI":
        specific_type_name = "User Interface text"
        specific_type_instruction = [
            "Check where and how the UI string is used to translate it appropriately.",
            "Make the translation simple and brief to fit UI spaces like buttons or menus.",
            "Use the same words and style throughout the UI for clarity.",
            "Adjust the translation to suit the culture and habits of the target users.",
            "Do not change placeholders, variables, or formatting codes in the string.",
            "Focus on the intended meaning, not literal word-by-word translation.",
            "Don't add the words that are not in the source text."]
    elif source_type == "Help" or source_type == "FAQ":
        specific_type_name = "Instruction text"
        specific_type_instruction = [
            "Use simple and clear language. Avoid difficult words or jargon unless users will understand them.",
            "Translate exactly what the original text says. Do not add or remove any technical details.",
            "Always use the same words for technical terms and buttons throughout the help files.",
            "Cultural Adaptation",
            "Change examples and phrases to fit the culture and habits of the target users.",
            "Think about what users need. Write instructions that help users complete tasks step-by-step.",
            "Keep the same headings, lists, buttons, and commands as in the original help file.",
            "Check the glossary or list of terms to use the correct technical words and product names.",
            "Ask native speakers or actual users to read the translation and check if it is easy to understand and use."
        ]

        
    system_prompt_json = {
        "role": "translator",
        "specialization": [
            software_type + " localization",
            f"The source texts are used in {software_type} and {source_type}, please consider the context of the {software_type} and {source_type} when translating.",
        ],
        "task": {
            "type": "translation",
            "source_language": src_lang,
            "target_language": tgt_lang
        },
        "translation_guidelines": {
            "tone": "professional but accessible",
            "audience": "software users of all expertise levels",
            "technical_accuracy": "preserve technical meaning",
            "adaptation": f"adapt to target language conventions for software {specific_type_name}",
            "terminology": "consistent with industry standards"
            
        },
        "specific_type_instructions": specific_type_instruction if 'specific_type_instruction' in locals() else [],
        "image_processing_guidelines": [
            "Examine UI elements and their context within the software",
            "Understand visual workflow and interface components referenced in the text",
            "Identify specific features or tools shown in the screenshots",
            "Note text visible in screenshots for consistent reference",
            "Observe spatial relationships and organization of elements"
        ],
        "language_specific_guidance": language_guidance
    }

    # Convert to JSON string
    system_prompt_json_str = json.dumps(system_prompt_json, ensure_ascii=False, indent=2)
    
    # print("Translation system prompt (JSON format):")
    # print(system_prompt_json_str)

    return system_prompt_json_str


def translate_prompt(src_lang, tgt_lang, json_str, refer_data_list, 
                     specific_names=None, region_table=None, refer_text_table=None, 
                     is_xlsx=False, suggestions=[], pre_translated_text=None):
    '''
    The task assigned to LLM for Translation.
    :param src_lang: Source language code (e.g., 'English')
    :param tgt_lang: Target language code (e.g., 'Traditional Chinese')
    :param json_str: JSON string to be translated
    :param specific_names: Dictionary of specific names and their translations
    :return: Formatted translation prompt string in JSON format
    '''
    
    specific_names_list = []
    if specific_names and len(specific_names) > 0:
        specific_names_list = [{"term": k, "translation": v} for k, v in specific_names.items()]

    region_table_list = []
    if region_table and len(region_table) > 0:
        region_table_list = [{"Original": k, "Use": v[0], "Avoid": v[1]} for k, v in region_table.items()]

    refer_text_condition= None
    if refer_text_table and len(refer_text_table) > 0:
        refer_text_condition = list(refer_text_table.values())

    translate_refer = []
    translate_refer.extend(
        [(refer_data[1], refer_data[2]) for refer_data in refer_data_list]
    )
    # Create the JSON prompt structure
    translation_prompt = {
        "task": "translation",
        "instruction": {
            "source_language": src_lang,
            "target_language": tgt_lang,
            "content_type": "json",
            "source_context": "software interface text"
        },
        "guidelines": {
            "preserve_technical_terms": True,
            "maintain_formatting": True,
            "preserve_camelcase_pascalcase_snakecase": True,
            "If ONLY a single word is provided, translate it as a verb.": True,
        },
        "specific_term_translations": {
            "terms": specific_names_list,
            "rule": [
                "Use singular and lowercase for all specific terms.",
                "If a specific term appears in the source text, translate it using the provided term.",
                "Please refer the specific term carefully. Don't tranlate error to similar source texts"
                "If the specific term is not found, use the general translation instead.",
                "Match the case (uppercase/lowercase) and number (singular/plural) of the original text when translating."
            ]
        },
        "region_table": {
            "terms": region_table_list,
            "rule": [
                "When translating 'Original' terms, use the 'Use' translation. Don't use the 'Avoid' translation.",
                "If the 'Original' term is not found, use the general translation instead.",
                "Match the case (uppercase/lowercase) and number (singular/plural) of the original text when translating."
            ]
        },
        "image_processing_instructions": [
            "Examine screenshots to understand UI context",
            "Use image context for accurate UI element translation",
            "Ensure translation consistency with visible UI labels",
            "Maintain terminology consistency between text and visuals",
            "Reference images when translating visual element descriptions"
        ],
        "translation_references": {
            "rules": [
                "Always use a translation from `specific_term_translations` if the source term appears there.",
                "If it’s not in `specific_term_translations` but the entire source text exactly matches an entry in `translation_references.terms`, use that translation.",
                "If the source text doesn’t exactly match any entry in either list, translate so you preserve the original meaning.",
                "Follow the phrasing, vocabulary, and grammar guidelines in `translation_references` for consistent style.",
                "If a term isn’t listed in either list, choose an appropriate alternative translation."
            ],
            "terms": translate_refer
        },
        "source_text": json_str,
        "output_format": "json (key: 'translation' with translated text as value)"
    }
    if refer_text_condition:
        translation_prompt["use condition"] = {
            "condition": refer_text_condition,
            "rules":[
                "Please refer to the condition when translating the source text.",
                "When translating, please use the condition to determine the translation.",
            ]
        }

    if is_xlsx:
        translation_prompt["instruction"]["format"] = "You MUST preserve all line breaks (\\n), bullet points, and formatting exactly as they appear in the original text."
    
    if suggestions and len(suggestions) > 0:

        translation_prompt["suggestions"] = {
            "rules": [
                "Please base on 'last translation' and 'Error Words' to translate the source text.",
                "Please do not add any words that are not in the source text.",
                "Please do not use the words in 'Error Words' to translate the source text.",
            ],
            "last translation": pre_translated_text if pre_translated_text else None,
            "Error Words": suggestions,
        }

    # Convert to JSON string
    import json
    prompt_json_str = json.dumps(translation_prompt, ensure_ascii=False, indent=2)
    
    # print(f"Source language: {src_lang}")
    # print(f"Target language: {tgt_lang}")
    # print(f"JSON prompt: {prompt_json_str}")
    
    return prompt_json_str
