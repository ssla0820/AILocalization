import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from prompts.prompts_utils import get_lang_specific_review_sys_prompt

def get_language_review_guidance(target_lang):
    '''
    Fetches language-specific review guidance for the given target language.
    
    :param target_lang: Target language code (e.g., 'Traditional Chinese')
    :return: JSON string containing the review guidance
    '''
    import json
    guidance_str = get_lang_specific_review_sys_prompt(target_lang)
    default_guidance = {
        'language_style': {},
        'translation_principles': [],
        'terminology_guidelines': {},
        'grammar_rules': [],
        'ui_guidelines': {}
    }
    try:
        language_review_guidance = json.loads(guidance_str) if guidance_str else default_guidance
    except (ValueError, TypeError):
        language_review_guidance = default_guidance
    return language_review_guidance
        
def default_sys_prompt(source_lang, target_lang, software_type, source_type, language_review_guidance):
    # Fetch and parse language-specific guidance; use default structure if empty or invalid
    # print(f"Generating review system prompt for {software_type}, {source_type} localization from {source_lang} to {target_lang}...")

    if source_type == "UI":
        specific_type_name = "User Interface text"
        specific_type_instruction = [
            "Check where and how the UI string is used to translate it appropriately.",
            "Make the translation simple and brief to fit UI spaces like buttons or menus.",
            "Use the same words and style throughout the UI for clarity.",
            "Adjust the translation to suit the culture and habits of the target users.",
            "Do not change placeholders, variables, or formatting codes in the string.",
            "Focus on the intended meaning, not literal word-by-word translation.",]
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
    
    # Create the JSON prompt structure
    system_prompt = {
        "role": "localization_reviewer",
        "department": 
            [software_type + " localization for " + specific_type_name,
             "Please review the translation carefully.",
             "CRITICAL: You MUST output VALID JSON only. No explanatory text before or after the JSON."],
        "task": {
            "type": "translation_review",
            "source_language": source_lang,
            "target_language": target_lang,
            "output_format_requirements": [
                "Your response must be valid JSON that follows the exact format specified.",
                "Do not include any explanatory text, markdown formatting, or backticks in your response.",
                "The response must begin with a single '{' and end with a single '}'.",
                "All property names and string values must use double quotes, not single quotes.",
                "Use proper JSON syntax for lists, objects, numbers, and null values.",
                "If a category score is less than 10.0, its corresponding suggestion list must contain at least one item.",
                "If a category score is 10.0, its corresponding suggestion should be null, not an empty array."
            ]
        },       
        "language_style": language_review_guidance.get('language_style', []),
        "specific_type_instructions": specific_type_instruction if 'specific_type_instruction' in locals() else [],
        "image_review_guidelines": [
            "Validate terminology accuracy using interface screenshots",
            "Verify UI element references match visual elements",
            "Ensure directional descriptions align with visual layout",
            "Check workflow descriptions against visual process",
            "Confirm translation clarity for interactive elements"
        ],
    }

    return system_prompt

def default_review_prompt(source_lang, target_lang, source_text, translation, specific_names=None, translate_refer=None):
    review_prompt = {
        "task": [
            "translation_review",
        ],
        "text": {
            "source": {
                "language": source_lang,
                "content": source_text
            },
            "translation": {
                "language": target_lang,
                "content": translation
            }
        },
        "guidelines": {
            "steps":[
                "Read the source text carefully.",
                "Read the translation carefully.",
                "Compare the translation with the source text.",
                "Follow the evaluation criteria to score the translation.",
                "Provide Suggestions if the score is less than 10.0 in any category.",
                "If the words is in 'specific_term_translations', use the translation in 'specific_term_translations' to translate the source text.",
                "If the words is in 'specific_term_translations', don't add any words to 'Suggestions'.",
                ]
        },
        "translation_references": {
            "rules": [
                "Use previously established translation patterns and terminology for consistency.",
                "If there is a conflict with any terms in 'specific_term_translations', always prioritize the terms specified there.",
                "Refer this section only. The most important thing is to keep the translation consistent with the original text.",
            ],
            "terms": translate_refer
        },
        "strict_json_response": [
            "YOUR RESPONSE MUST BE VALID JSON ONLY. Do not include any text before or after the JSON.",
            "The response must begin with a single opening curly brace '{' and end with a single closing curly brace '}'.",
            "Use double quotes for all keys and string values, not single quotes.",
            "All numeric values must be numbers without quotes.",
            "All lists must be enclosed in square brackets [], even if there's only one item.",
            "If a score value is less than 10.0, the corresponding suggestion list MUST be a valid array with at least one item.",
            "If a score value is 10.0, set the corresponding suggestion value to null, not an empty array.",
            "Do not include trailing commas at the end of JSON objects or arrays.",
            "CRITICAL: Ensure your entire response is valid JSON that can be parsed by json.loads()."
        ],
        "required_output_format": {
            "Rules": [
                "MUST Follow the output format strictly. Do not add any explanations, comments, or other text outside the JSON.",
                "The entire response must be a valid JSON object with the exact fields specified below.",
                "If you include any text before or after the JSON, it will cause parsing errors.",
            ],
        }
    }
    
    if specific_names and len(specific_names) > 0:
        review_prompt["specific_term_translations"] = [
            {"term": k, "required_translation": v} for k, v in specific_names.items()
        ]
    
    return review_prompt
    
def review_sys_prompt_accuracy(source_lang, target_lang, software_type, source_type):
    '''
    Enhanced version of the review system prompt with stricter JSON formatting requirements.
    
    :param software_type: Type of software being localized
    :param source_lang: Source language (e.g., 'English')
    :param target_lang: Target language (e.g., 'Traditional Chinese')
    :return: Formatted system prompt string in JSON format
    '''
    import json
    language_review_guidance = get_language_review_guidance(target_lang)
    # print('='*40)
    # print(language_review_guidance)
    # print('='*40)
    system_prompt = default_sys_prompt(source_lang, target_lang, software_type, source_type, language_review_guidance)
    system_prompt["evaluation_criteria"] = [
            "If the translation conveys the same meaning as the original text, score it higher.",
            "If the translation does not match the original text, score it lower.",
            "Other Rules: ",
        ] + [f"  {rule}" for rule in language_review_guidance.get('Accuracy', [])],          
       
    system_prompt["json_response_example"] = {
            "Score": 9.5, 
            "Suggestions": ["incorrect phrase 1", "word 2"],
        }

    # Convert to JSON string
    return json.dumps(system_prompt, ensure_ascii=False, indent=2)

def review_prompt_accuracy(source_lang, target_lang, source_text, translation, specific_names=None, translate_refer=None):
    '''
    Enhanced version of the review prompt with stricter JSON formatting requirements.
    
    :param source_text: Source text in the source language
    :param translation: Translated text in the target language
    :param specific_names: Dictionary of specific names and their translations
    :param source_lang: Source language (e.g., 'English')
    :param target_lang: Target language (e.g., 'Traditional Chinese')
    :return: Formatted review prompt string in JSON format
    '''

    review_prompt = default_review_prompt(source_lang, target_lang, source_text, translation, specific_names, translate_refer)
    review_prompt["required_output_format"]["example_response"] = {
                "Score": 9.5, 
                "Suggestions": ["incorrect phrase 1", "word 2"],
            }
    review_prompt["required_output_format"]["format"] = {
            "Score": "Float (Score from 0 to 10, where 0 means no accuracy and 10 means perfect accuracy)",
            "Suggestions":[
                "a list of ERROR WORDS or PHRASES ONLY if 'Accuracy Score' less than 10.0 else None",
                "Must be a list of strings (e.g., [\"word1\", \"word2\"]), not a single string.",
                "If score is less than 10.0, the list MUST NOT be empty or None."
            ]
        }
       
    # Convert to JSON string
    import json
    return json.dumps(review_prompt, ensure_ascii=False, indent=2)

def review_sys_prompt_native(source_lang, target_lang, software_type, source_type):
    '''
    Enhanced version of the review system prompt with stricter JSON formatting requirements.
    
    :param software_type: Type of software being localized
    :param source_lang: Source language (e.g., 'English')
    :param target_lang: Target language (e.g., 'Traditional Chinese')
    :return: Formatted system prompt string in JSON format
    '''
    import json
    language_review_guidance = get_language_review_guidance(target_lang)
    system_prompt = default_sys_prompt(source_lang, target_lang, software_type, source_type, language_review_guidance)
    system_prompt["evaluation_criteria"] = [
                    "If the sentence structure, word choice, and word order sound natural and like how a native speaker would say it, score it higher.",
                    "If the words used are in 'eavaluation_guidelines', 'specific_term_translations' or 'translation_references', score it higher.",
                    "If the translation sounds awkward or unnatural, score it lower.",
                    "Other Rules: ",
                ] + [f"  {rule}" for rule in language_review_guidance.get('Native Usage', [])]       
       
    system_prompt["json_response_example"] = {
            "Score": 8.5, 
            "Suggestions": ["awkward phrase 1", "word 2"],
        }

    # Convert to JSON string
    return json.dumps(system_prompt, ensure_ascii=False, indent=2)

def review_prompt_native(source_lang, target_lang, source_text, translation, specific_names=None, translate_refer=None):
    '''
    Enhanced version of the review prompt with stricter JSON formatting requirements.
    
    :param source_text: Source text in the source language
    :param translation: Translated text in the target language
    :param specific_names: Dictionary of specific names and their translations
    :param source_lang: Source language (e.g., 'English')
    :param target_lang: Target language (e.g., 'Traditional Chinese')
    :return: Formatted review prompt string in JSON format
    '''

    review_prompt = default_review_prompt(source_lang, target_lang, source_text, translation, specific_names, translate_refer)
    review_prompt["required_output_format"]["example_response"] = {
                "Score": 8.5, 
                "Suggestions": ["awkward phrase 1", "word 2"],
            }
    review_prompt["required_output_format"]["format"] = {
            "Score": "Float (Score from 0 to 10, where 0 means no native usage and 10 means perfect native usage)",
            "Suggestions":[
                "a list of ERROR WORDS or PHRASES ONLY if 'Native Usage Score' less than 10.0 else None",
                "Must be a list of strings (e.g., [\"word1\", \"word2\"]), not a single string.",
                "If score is less than 10.0, the list MUST NOT be empty or None."
            ]
        }
       
    # Convert to JSON string
    import json
    return json.dumps(review_prompt, ensure_ascii=False, indent=2)

def review_sys_prompt_word(source_lang, target_lang, software_type, source_type):
    '''
    Enhanced version of the review system prompt with stricter JSON formatting requirements.
    
    :param software_type: Type of software being localized
    :param source_lang: Source language (e.g., 'English')
    :param target_lang: Target language (e.g., 'Traditional Chinese')
    :return: Formatted system prompt string in JSON format
    '''
    import json
    language_review_guidance = get_language_review_guidance(target_lang)
    system_prompt = default_sys_prompt(source_lang, target_lang, software_type, source_type, language_review_guidance)
    system_prompt["evaluation_criteria"] = [
                    "If the translation uses the correct words and terminology, score it higher.",
                    "If the words used are in 'evaluation_guidelines', 'specific_term_translations' or 'translation_references', score it higher.",
                    "If the translation uses incorrect or inappropriate words, score it lower.",
                    "Other Rules: ",
                ] + [f"  {rule}" for rule in language_review_guidance.get('Word Correctness', [])]    
       
    system_prompt["json_response_example"] = {
            "Score": 9.0, 
            "Suggestions": ["wrong term 1", "word 2"],
        }

    # Convert to JSON string
    return json.dumps(system_prompt, ensure_ascii=False, indent=2)

def review_prompt_word(source_lang, target_lang, source_text, translation, specific_names=None, translate_refer=None):
    '''
    Enhanced version of the review prompt with stricter JSON formatting requirements.
    
    :param source_text: Source text in the source language
    :param translation: Translated text in the target language
    :param specific_names: Dictionary of specific names and their translations
    :param source_lang: Source language (e.g., 'English')
    :param target_lang: Target language (e.g., 'Traditional Chinese')
    :return: Formatted review prompt string in JSON format
    '''

    review_prompt = default_review_prompt(source_lang, target_lang, source_text, translation, specific_names, translate_refer)
    review_prompt["required_output_format"]["example_response"] = {
                "Score": 9.0, 
                "Suggestions": ["wrong term 1", "word 2"],
            }
    review_prompt["required_output_format"]["format"] = {
            "Score": "Float (Score from 0 to 10, where 0 means no word correctness and 10 means perfect word correctness)",
            "Suggestions":[
                "a list of ERROR WORDS or PHRASES ONLY if 'Word Correctness Score' less than 10.0 else None",
                "Must be a list of strings (e.g., [\"word1\", \"word2\"]), not a single string.",
                "If score is less than 10.0, the list MUST NOT be empty or None."
            ]
        }
       
    # Convert to JSON string
    import json
    return json.dumps(review_prompt, ensure_ascii=False, indent=2)

def review_sys_prompt_grammar(source_lang, target_lang, software_type, source_type):
    '''
    Enhanced version of the review system prompt with stricter JSON formatting requirements.
    
    :param software_type: Type of software being localized
    :param source_lang: Source language (e.g., 'English')
    :param target_lang: Target language (e.g., 'Traditional Chinese')
    :return: Formatted system prompt string in JSON format
    '''
    import json
    language_review_guidance = get_language_review_guidance(target_lang)
    system_prompt = default_sys_prompt(source_lang, target_lang, software_type, source_type, language_review_guidance)
    system_prompt["evaluation_criteria"] = [
                "If the translation uses correct grammar and sentence structure, score it higher.",
                "If the sentences are in 'evaluation_guidelines', 'specific_term_translations' or 'translation_references', score it higher.",
                "If the translation uses incorrect grammar or sentence structure, score it lower.",
                "Other Rules: ",
                ] + [f"  {rule}" for rule in language_review_guidance.get('Sentence Structure', [])]  
       
    system_prompt["json_response_example"] = {
            "Score": 9.0, 
            "Suggestions": ["wrong term 1", "word 2"],
        }

    # Convert to JSON string
    return json.dumps(system_prompt, ensure_ascii=False, indent=2)

def review_prompt_grammar(source_lang, target_lang, source_text, translation, specific_names=None, translate_refer=None):
    '''
    Enhanced version of the review prompt with stricter JSON formatting requirements.
    
    :param source_text: Source text in the source language
    :param translation: Translated text in the target language
    :param specific_names: Dictionary of specific names and their translations
    :param source_lang: Source language (e.g., 'English')
    :param target_lang: Target language (e.g., 'Traditional Chinese')
    :return: Formatted review prompt string in JSON format
    '''

    review_prompt = default_review_prompt(source_lang, target_lang, source_text, translation, specific_names, translate_refer)
    review_prompt["required_output_format"]["example_response"] = {
                "Score": 9.0, 
                "Suggestions": ["wrong term 1", "word 2"],
            }
    review_prompt["required_output_format"]["format"] = {
            "Score": "Float (Score from 0 to 10, where 0 means no sentence structure and 10 means perfect sentence structure)",
            "Suggestions": [
                "a list of ERROR WORDS or PHRASES ONLY if 'Sentence Structure Score' less than 10.0 else None",
                "Must be a list of strings (e.g., [\"word1\", \"word2\"]), not a single string.",
                "If score is less than 10.0, the list MUST NOT be empty or None."
            ]
        }
       
    # Convert to JSON string
    import json
    return json.dumps(review_prompt, ensure_ascii=False, indent=2)

def review_sys_prompt_consistency(source_lang, target_lang, software_type, source_type):
    '''
    Enhanced version of the review system prompt with stricter JSON formatting requirements.
    
    :param software_type: Type of software being localized
    :param source_lang: Source language (e.g., 'English')
    :param target_lang: Target language (e.g., 'Traditional Chinese')
    :return: Formatted system prompt string in JSON format
    '''
    import json
    language_review_guidance = get_language_review_guidance(target_lang)
    system_prompt = default_sys_prompt(source_lang, target_lang, software_type, source_type, language_review_guidance)
    system_prompt["evaluation_criteria"] = [
                "If the translation uses the same terminology, sentence patterns, and vocabulary as the provided reference data, score it higher.",
                "If the translation is similar to the 'translation_references' but uses different terminology, sentence patterns, or vocabulary, score it higher.",
                "If the translation is similar to 'evaluation_guidelines', 'specific_term_translations' or 'translation_references', score it higher.",
                "If the translation uses different terminology, sentence patterns, or vocabulary from the provided reference data, score it lower.",
                "Other Rules: ",
                ] + [f"  {rule}"  for rule in language_review_guidance.get('Consistency with Reference', [])]
       
    system_prompt["json_response_example"] = {
            "Score": 8.0, 
            "Suggestions": ["inconsistent term 1"],
        }

    # Convert to JSON string
    return json.dumps(system_prompt, ensure_ascii=False, indent=2)

def review_prompt_consistency(source_lang, target_lang, source_text, translation, specific_names=None, translate_refer=None):
    '''
    Enhanced version of the review prompt with stricter JSON formatting requirements.
    
    :param source_text: Source text in the source language
    :param translation: Translated text in the target language
    :param specific_names: Dictionary of specific names and their translations
    :param source_lang: Source language (e.g., 'English')
    :param target_lang: Target language (e.g., 'Traditional Chinese')
    :return: Formatted review prompt string in JSON format
    '''

    review_prompt = default_review_prompt(source_lang, target_lang, source_text, translation, specific_names, translate_refer)
    review_prompt["required_output_format"]["example_response"] = {
                "Score": 8.0, 
                "Suggestions": ["inconsistent term 1"],
            }
    review_prompt["required_output_format"]["format"] = {
            "Score": "Float (Score from 0 to 10, where 0 means no consistency with reference and 10 means perfect consistency with reference)",
            "Suggestions": [
                "a list of ERROR WORDS or PHRASES ONLY if 'Consistency with Reference Score' less than 10.0 else None",
                "Must be a list of strings (e.g., [\"word1\", \"word2\"]), not a single string.",
                "If score is less than 10.0, the list MUST NOT be empty or None."
            ]
        }
       
    # Convert to JSON string
    import json
    return json.dumps(review_prompt, ensure_ascii=False, indent=2)

def review_sys_prompt_gender(source_lang, target_lang, software_type, source_type):
    '''
    Enhanced version of the review system prompt with stricter JSON formatting requirements.
    
    :param software_type: Type of software being localized
    :param source_lang: Source language (e.g., 'English')
    :param target_lang: Target language (e.g., 'Traditional Chinese')
    :return: Formatted system prompt string in JSON format
    '''
    import json
    language_review_guidance = get_language_review_guidance(target_lang)
    system_prompt = default_sys_prompt(source_lang, target_lang, software_type, source_type, language_review_guidance)
    system_prompt["evaluation_criteria"] = [
                "Check if the translation uses the correct gender for all words that change by gender.",
                "Look at nouns, adjectives, articles, and pronouns to make sure their gender matches.",
                "Make sure words that go together agree in gender (like 'the big house' uses matching forms).",
                "If the original text shows a specific gender, the translation should keep it.",
                "If the gender is unclear in the original, the translation should still sound natural and correct.",
                "Give a high score if all genders are correct and match well.",
                "Give a lower score if there are mistakes in gender that make the sentence wrong or confusing.",
                "Even one gender mistake should lower the score.",
                "Check each gendered word carefully, one by one."
            ]
       
    system_prompt["json_response_example"] = {
            "Score": 8.0, 
            "Suggestions": ["word 1"],
        }

    # Convert to JSON string
    return json.dumps(system_prompt, ensure_ascii=False, indent=2)

def review_prompt_gender(source_lang, target_lang, source_text, translation, specific_names=None, translate_refer=None):
    '''
    Enhanced version of the review prompt with stricter JSON formatting requirements.
    
    :param source_text: Source text in the source language
    :param translation: Translated text in the target language
    :param specific_names: Dictionary of specific names and their translations
    :param source_lang: Source language (e.g., 'English')
    :param target_lang: Target language (e.g., 'Traditional Chinese')
    :return: Formatted review prompt string in JSON format
    '''

    review_prompt = default_review_prompt(source_lang, target_lang, source_text, translation, specific_names, translate_refer)
    review_prompt["required_output_format"]["example_response"] = {
                "Score": 8.0, 
                "Suggestions": ["word 1"],
            }
    review_prompt["required_output_format"]["format"] = {
            "Score": "Float (Score from 0 to 10, where 0 means incorrect gender and 10 means correct gender)",
            "Suggestions": [
                "a list of ERROR WORDS or PHRASES ONLY if 'Gender Score' less than 10.0 else None",
                "Must be a list of strings (e.g., [\"word1\", \"word2\"]), not a single string.",
                "If score is less than 10.0, the list MUST NOT be empty or None."
            ]
        }
       
    # Convert to JSON string
    import json
    return json.dumps(review_prompt, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    source_lang = "English"
    target_lang = "Spanish"
    software_type = "Software"
    source_type = "UI"
    print(review_sys_prompt_accuracy(source_lang, target_lang, software_type, source_type))
    print(review_sys_prompt_native(source_lang, target_lang, software_type, source_type))
    print(review_sys_prompt_word(source_lang, target_lang, software_type, source_type))
    print(review_sys_prompt_grammar(source_lang, target_lang, software_type, source_type))
    print(review_sys_prompt_consistency(source_lang, target_lang, software_type, source_type))

