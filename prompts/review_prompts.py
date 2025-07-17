import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from prompts.prompts_utils import get_lang_specific_review_sys_prompt

class ReviewPrompts:
    def __init__(self, source_lang, target_lang, software_type, source_type, 
                 source_text = None, translation=None, specific_names=None, 
                 region_table=None, refer_text_table=None, translate_refer=None):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.software_type = software_type
        self.source_type = source_type
        self.language_review_guidance = self.get_language_review_guidance()
        self.sys_prompt = self.review_sys_prompt()
        
        # self.sys_prompt_accuracy = self.review_sys_prompt_accuracy()
        # self.sys_prompt_native = self.review_sys_prompt_native()
        # self.sys_prompt_word = self.review_sys_prompt_word()
        # self.sys_prompt_grammar = self.review_sys_prompt_grammar()
        # self.sys_prompt_consistency = self.review_sys_prompt_consistency()
        # self.sys_prompt_gender = self.review_sys_prompt_gender()

        #  should be replaced with actual translation and specific names when calling the review prompts
        self.source_text = source_text
        self.translation = translation
        self.specific_names = specific_names
        self.region_table = region_table
        self.refer_text_table = refer_text_table
        self.translate_refer = translate_refer


        
    def get_language_review_guidance(self):
        '''
        Fetches language-specific review guidance for the given target language.
        
        :param target_lang: Target language code (e.g., 'Traditional Chinese')
        :return: JSON string containing the review guidance
        '''
        import json
        guidance_str = get_lang_specific_review_sys_prompt(self.target_lang)
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
        
    def default_sys_prompt(self):
        # Fetch and parse language-specific guidance; use default structure if empty or invalid
        # print(f"Generating review system prompt for {software_type}, {source_type} localization from {source_lang} to {target_lang}...")

        if self.source_type == "UI":
            specific_type_name = "User Interface text"
            specific_type_instruction = [
                "Check where and how the UI string is used to translate it appropriately.",
                "Make the translation simple and brief to fit UI spaces like buttons or menus.",
                "Use the same words and style throughout the UI for clarity.",
                "Adjust the translation to suit the culture and habits of the target users.",
                "Do not change placeholders, variables, or formatting codes in the string.",
                "Focus on the intended meaning, not literal word-by-word translation.",]
        elif self.source_type == "Help" or self.source_type == "FAQ":
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
                [self.software_type + " localization for " + specific_type_name,
                "Please review the translation carefully.",
                "CRITICAL: You MUST output VALID JSON only. No explanatory text before or after the JSON."],
            "task": {
                "type": "translation_review",
                "source_language": self.source_lang,
                "target_language": self.target_lang,
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
            "language_style": self.language_review_guidance.get('language_style', []),
            "specific_type_instructions": specific_type_instruction if 'specific_type_instruction' in locals() else [],
        }

        return system_prompt

    def default_review_prompt(self):
        specific_names_list = []
        if self.specific_names and len(self.specific_names) > 0:
            specific_names_list = [{"term": k, "translation": v} for k, v in self.specific_names.items()]

        region_table_list = []
        if self.region_table and len(self.region_table) > 0:
            region_table_list = [{"Original": k, "Use": v[0], "Avoid": v[1]} for k, v in self.region_table.items()]
        
        review_prompt = {
            "task": [
                "translation_review",
            ],
            "text": {
                "source": {
                    "language": self.source_lang,
                    "content": self.source_text
                },
                "translation": {
                    "language": self.target_lang,
                    "content": self.translation
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
                "terms": self.translate_refer
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
        }
        

        return review_prompt
    
    def review_sys_prompt(self):

        import json

        # print('='*40)
        # print(language_review_guidance)
        # print('='*40)
        system_prompt = self.default_sys_prompt()
        system_prompt["evaluation_criteria"] = {}
        system_prompt["evaluation_criteria"]["accuracy"] = [
                "If the translation conveys the same meaning as the original text, score it higher.",
                "If the translation does not match the original text, score it lower.",
                "Other Rules: ",
            ] + [f"  {rule}" for rule in self.language_review_guidance.get('Accuracy', [])],          


        system_prompt["evaluation_criteria"]["native"] = [
                        "If the sentence structure, word choice, and word order sound natural and like how a native speaker would say it, score it higher.",
                        "If the words used are in 'eavaluation_guidelines', 'specific_term_translations' or 'translation_references', score it higher.",
                        "If the translation sounds awkward or unnatural, score it lower.",
                        "Other Rules: ",
                    ] + [f"  {rule}" for rule in self.language_review_guidance.get('Native Usage', [])]       
        

        system_prompt["evaluation_criteria"]["word"] = [
                        "If the translation uses the correct words and terminology, score it higher.",
                        "If the words used are in 'evaluation_guidelines', 'specific_term_translations' or 'translation_references', score it higher.",
                        "If the translation uses incorrect or inappropriate words, score it lower.",
                        "Other Rules: ",
                    ] + [f"  {rule}" for rule in self.language_review_guidance.get('Word Correctness', [])]    
        
        system_prompt["evaluation_criteria"]["grammar"]= [
                    "If the translation uses correct grammar and sentence structure, score it higher.",
                    "If the sentences are in 'evaluation_guidelines', 'specific_term_translations' or 'translation_references', score it higher.",
                    "If the translation uses incorrect grammar or sentence structure, score it lower.",
                    "Other Rules: ",
                    ] + [f"  {rule}" for rule in self.language_review_guidance.get('Sentence Structure', [])]  
        
        system_prompt["evaluation_criteria"]["consistency"] = [
                    "If the translation uses the same terminology, sentence patterns, and vocabulary as the provided reference data, score it higher.",
                    "If the translation is similar to the 'translation_references' but uses different terminology, sentence patterns, or vocabulary, score it higher.",
                    "If the translation is similar to 'evaluation_guidelines', 'specific_term_translations' or 'translation_references', score it higher.",
                    "If the translation uses different terminology, sentence patterns, or vocabulary from the provided reference data, score it lower.",
                    "Other Rules: ",
                    ] + [f"  {rule}"  for rule in self.language_review_guidance.get('Consistency with Reference', [])]

        system_prompt["evaluation_criteria"]["gender"]= [
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
                # "Type": ["Accuracy", "Native Usage", "Word Correctness", "Grammar", "Consistency", "Gender"],
                "Suggestions": ["incorrect term 1 with reason and suggestion", "incorrect term 2 with reason and suggestion"],
            }

        # Convert to JSON string
        return json.dumps(system_prompt, ensure_ascii=False, indent=2)


    
    def review_prompt(self):
        review_prompt = self.default_review_prompt()
        review_prompt["required_output_format"]["example_response"] = {
                "Score": 8.0, 
                # "Type": ["Accuracy", "Native Usage", "Word Correctness", "Grammar", "Consistency", "Gender"],
                "Suggestions": ["incorrect term 1 with reason and suggestion", "incorrect term 2 with reason and suggestion"],
            }

        review_prompt["required_output_format"]["format"] = {
                "Score": "Float (Score from 0 to 10, where 0 means no accuracy and 10 means perfect accuracy)",
                "Suggestions":[
                    "a list of ERROR WORDS or PHRASES ONLY if 'Score' less than 10.0 else return []",
                    "a list of ERROR TYPE in 'Type' only if 'Score' less than 10.0 else return []",
                    # "Must be a list of strings (e.g., [\"word1\", \"word2\"]), not a single string.",
                    "If score is less than 10.0, the list MUST NOT be empty or None.",
                    "Response the incorrect phrases or words that cause the accuracy score to be less than 10.0.",
                    "Response the incorrect pharases and words, reasons, and suggestions to improve the translation accuracy.",
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
    review_prompt_obj = ReviewPrompts(source_lang, target_lang, software_type, source_type)


