import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))


def improve_sys_prompt(src_lang, tgt_lang, software_type, source_type):
    '''
    The character assigned to LLM for Re-Translation based on failure reason.
    :param src_lang: Source language code (e.g., 'English')
    :param tgt_lang: Target language code (e.g., 'Traditional Chinese')
    :param software_type: Type of software being localized
    :param source_type: Type of source text (e.g., UI, Help, FAQ)
    :param fail_reason: Explanation of why previous translation failed or needs revision
    :return: Formatted system prompt string in JSON format
    '''
    import json
    
    
    system_prompt_json = {
        "role": "Sentence Improvement Expert",
        "specialization": [
            software_type + " Sentence Improvement",
            f"The source texts are used in {software_type} and {source_type}, please consider the context of the {software_type} and {source_type} when re-translating.",
        ],
        "task": {
            "type": "Improve Translation",
            "source_language": src_lang,
            "target_language": tgt_lang,
            "Last Translation": "the last translation that needs revision",
            "instructions": "Improve the last translation by only changing the words are mentioned in the suggestions.",
        },
    }

    # Convert to JSON string
    system_prompt_json_str = json.dumps(system_prompt_json, ensure_ascii=False, indent=2)

    return system_prompt_json_str


def improve_prompt(
    src_lang, tgt_lang, json_str, refer_data_list, specific_names=None, 
    is_xlsx=False, suggestions=None, translated_text=None
):
    '''
    The task assigned to LLM for Re-Translation based on failure reason or error feedback.
    :param src_lang: Source language code (e.g., 'English')
    :param tgt_lang: Target language code (e.g., 'Traditional Chinese')
    :param json_str: JSON string to be translated
    :param specific_names: Dictionary of specific names and their translations
    :param suggestions: List of error words or phrases to avoid in re-translation
    :param pimproved_text: The previous translation that needs revision
    :param fail_reason: Reason why the previous translation failed or requires revision
    :return: Formatted re-translation prompt string in JSON format
    '''

    translation_prompt = {
        "task": "sentence_improvement",
        "source_text": json_str,
        "output_format": "json (key: 'translation' with translated text as value)",
        "suggestions":{
            "rules": [
                "Only improve the part in 'suggestions', don't change the rest of the 'last_translation'.", 
                "Use the 'last_translation' and 'suggestions' as references to translate the source text.",
                "Do not add any words that are not in the source text.",
                "Focus on fixing mistakes from the previous translation based on the suggestions.",
                "Avoid using any words listed in 'suggestions' when translating.",
                "If the source text contains words not in 'suggestions', translate them normally.",
                "If the source text contains words that are in 'suggestions', do not use those words in the translation."
            ],
            "steps": [
                "Read the 'last_translation' carefully.",
                "Identify the errors or issues based on the 'suggestions'.",
                "Translate the source text while avoiding the words in 'suggestions'.",
                "Ensure that the translation is clear and accurate.",
                "Review the translation to ensure it does not include any words from 'suggestions'.",
                "If the words in 'specific_term_translations', use the translation in 'specific_term_translations'.",
            ],
            "last_translation": translated_text if translated_text else None,
            "suggestions": suggestions,
        }
    }

    if specific_names and len(specific_names) > 0:
        translation_prompt["specific_term_translations"] = [
            {"term": k, "required_translation": v} for k, v in specific_names.items()
        ]

    # Convert to JSON string
    import json
    prompt_json_str = json.dumps(translation_prompt, ensure_ascii=False, indent=2)
    
    return prompt_json_str
