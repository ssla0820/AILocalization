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
        system_prompt = {
            "task": "Based on the provided source text and reference translation, evaluate the quality of the target translation. Please use a chain-of-thought approach, conducting detailed analysis first, then providing the final score.",

            "evaluation_dimensions": {
                "accuracy": "Correctness of meaning conveyance, retention of key information, accuracy of facts and data",
                "fluency": "Naturalness of language expression, grammatical correctness, appropriateness of vocabulary usage",
                "completeness": "Completeness of information conveyance, presence of omissions or additions, preservation of tone and style",
                "cultural_adaptation": "Appropriate handling of cultural elements, conformity to target language conventions, contextual adaptation",
                "terminology_compliance": "Adherence to mandatory glossary terms and preference for common usage table terms"
            },

            "scoring_scale": {
                "5": "Excellent quality, nearly perfect, ready for direct use",
                "4": "Good quality, only minor issues, requires slight modification",
                "3": "Average quality, obvious room for improvement, needs modification",
                "2": "Major issues, requires significant modification to be usable",
                "1": "Serious problems, unacceptable, needs complete retranslation"
            },

            "chain_of_thought_steps": [
                {
                    "step": "1",
                    "title": "Source Text Comprehension Analysis",
                    "instruction": "Analyze the source text for: core meaning and key information, tone and style characteristics, cultural background and context, special terminology or expressions"
                },
                {
                    "step": "2", 
                    "title": "Reference Translation Analysis",
                    "instruction": "Analyze the reference translation for: meaning conveyance approach, language expression choices, cultural adaptation handling, overall quality level"
                },
                {
                    "step": "3",
                    "title": "Target Translation Analysis", 
                    "instruction": "Examine the target translation for: correspondence with source text meaning, language expression quality, comparison with reference translation, identification of strengths and weaknesses"
                },
                {
                    "step": "4",
                    "title": "Dimensional Comparative Assessment",
                    "instruction": "Compare each evaluation dimension: accuracy comparison (target vs reference vs source), fluency comparison (naturalness and readability), completeness comparison (information conveyance), cultural adaptation comparison (cultural handling approaches)"
                },
                {
                    "step": "5",
                    "title": "Comprehensive Judgment",
                    "instruction": "Based on the above analysis, consider: importance weights of each dimension, overall translation quality, practical usability assessment, improvement suggestions"
                }
            ],

            "output_format": {
                "evaluation_process": {
                    "step_1_source_analysis": "[Detailed analysis of source text's core meaning, style characteristics, cultural background, etc.]",
                    "step_2_reference_analysis": "[Analysis of reference translation's approach and quality level]",
                    "step_3_target_analysis": "[Analysis of target translation's characteristics and quality]",
                    "step_4_dimensional_assessment": {
                        "accuracy_evaluation": {
                            "meaning_conveyance": "[Analysis explanation]",
                            "score": "_/5"
                        },
                        "fluency_evaluation": {
                            "language_quality": "[Analysis explanation]",
                            "score": "_/5"
                        },
                        "completeness_evaluation": {
                            "information_integrity": "[Analysis explanation]",
                            "score": "_/5"
                        },
                        "cultural_adaptation_evaluation": {
                            "cultural_handling": "[Analysis explanation]",
                            "score": "_/5"
                        },
                        "terminology_compliance_evaluation": {
                            "glossary_compliance": "[Analysis of adherence to mandatory glossary terms]",
                            "common_usage_preference": "[Analysis of preference for common usage table terms]",
                            "score": "_/5"
                        }
                    },
                    "step_5_comprehensive_judgment": {
                        "overall_analysis": "[Comprehensive performance across all dimensions, explaining overall translation quality]",
                        "main_strengths": "[List main advantages of the translation]",
                        "main_weaknesses": "[List main issues with the translation]",
                        "improvement_suggestions": "[Provide specific improvement recommendations]",
                        "final_score": "_/5",
                        "scoring_rationale": "[Brief explanation of the final score basis]"
                    }
                }
            },

            "evaluation_guidelines": [
                "Maintain objectivity: Base evaluation on concrete evidence, avoid subjective bias",
                "Consider context: Fully consider the usage scenario and target audience of the translation",
                "Balance dimensions: Do not overemphasize any single evaluation dimension",
                "Provide constructive feedback: Evaluation should help improve translation quality",
                "Consistency principle: Apply consistent evaluation standards to similar issues"
            ],
            }


        # Convert to JSON string
        return json.dumps(system_prompt, ensure_ascii=False, indent=2)


    
    def review_prompt(self):
        review_prompt = {
            "input_data": {
                "source_text": f"{self.source_text}",
                "reference_translation": f"{self.translate_refer}",
                "target_translation": f"{self.translation}",
                "glossary": f"{self.specific_names}",
                "common_usage_table": f"{self.region_table}"
            }
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
    print("System Prompt:")
    # print(review_prompt_obj.sys_prompt)
    print("Review Prompt:")
    # source_text = "When you apply Auto Retouch, the portrait feature below will also be adjusted automatically."
    # reference_translation = """
    #     [
    #         [
    #             "Portrait mode",
    #             "Mode portrait",
    #         ],
    #         [
    #             "Click the [Apply] button below to auto remove imperfections and enhance smoothness in portrait photos.",
    #             "Cliquez sur le bouton [Appliquer] ci-dessous pour supprimer automatiquement les imperfections et améliorer la finesse des photos de portrait.",
    #         ],
    #         [
    #             "You can also click and drag your mouse on the photo to rotate it.",
    #             "Vous pouvez également cliquer et faire glisser votre souris sur la photo pour la faire pivoter.",
    #         ],
    #         [
    #             "Set default view using the controls or dragging on the photo.",
    #             "Définissez la vue par défaut en utilisant les commandes ou en faisant glisser la photo.",
    #         ],
    #         [
    #             "Click and hold to show original photo",
    #             "Cliquez et maintenez pour afficher la photo d'origine",
    #         ],
    #         [
    #             "Do you want to remove the folder \"%s\" from the library?",
    #             "Voulez-vous supprimer le dossier \"%s\" de la bibliothèque ?",
    #         ],
    #         [
    #             "Show mask",
    #             "Afficher le masque",
    #         ],
    #         [
    #             "Slideshow Video Production",
    #             "Production d'une vidéo diaporama",
    #         ],
    #         [
    #             "The face in your photo is too small, which may result in poor quality.\\n\\nAre you sure you want to continue?",
    #             "Le visage de votre photo est trop petit, ce qui peut conduire à une mauvaise qualité.\\n\\nÊtes-vous sûr de vouloir continuer ?",
    #         ]
    #         ]
    #     """
    # glossary = """"
    # [
    #   {
    #     "term": "Auto Retouch",
    #     "translation": "Retouche automatique"
    #   }
    # ],
    # """
    # target_translation = "Lorsque vous appliquez la Retouche automatique, la fonction portrait ci-dessous sera également ajustée automatiquement."
    # common_usage_table = None
    # print(review_prompt_obj.review_prompt(source_text, reference_translation, target_translation, glossary, common_usage_table))



# source_text = "Kick-start your projects with a brand-new launcher and streamlined access to all AI tools in the organized AI Toolbox. Create faster and more effortlessly than ever."

# target_translation = "Lancez vos projets grâce à un lanceur tout neuf et à un accès simplifié à tous les outils IA regroupés dans l’AI Toolbox. Créez plus vite et plus facilement que jamais."
# reference_translation = """[
#       [
#         "Click [Start Now] to start generating your AI Images.",
#         "Cliquez sur [Démarrer maintenant] pour commencer à générer vos images IA.",
#       ],
#       [
#         "Click [Start Now] to start generating your AI Videos.",
#         "Cliquez sur [Démarrer maintenant] pour commencer à générer vos vidéos IA.",
#       ],
#       [
#         "AI feature processor",
#         "Processeur de fonctions IA",
#       ],
#       [
#         "Generating your AI images",
#         "Générez vos propres images IA",
#       ],
#       [
#         "Generating your AI music",
#         "Génération de votre musique IA",
#       ]
#     ]"""
# glossary = None
# common_usage_table = None
# print(review_prompt_obj.review_prompt(source_text, reference_translation, target_translation, glossary, common_usage_table))


# source_text = "The following items have been deleted:\n- Imported image\n- Text prompt\n\nPlease re-import the image or enter a similar prompt if you want to generate a similar video."
# target_translation = "Les éléments suivants ont été supprimés :\n- Image importée\n- Invite textuelle\n\nVeuillez réimporter l’image ou saisir une invite similaire si vous souhaitez générer une vidéo similaire."
# reference_translation = """
#     [
#         We couldn't generate your video as your content may violate our Terms of Service. The credits have been refunded. Adjust your prompt or image, and then generate again. You can also delete this task.,
#         Nous n’avons pas pu générer votre vidéo car son contenu pourrait enfreindre nos Conditions de service. Les crédits ont été remboursés. Ajustez votre invite ou votre image, puis générez à nouveau. Vous pouvez également supprimer cette tâche.,
#       ],
#       [
#         We couldn't generate your video due to an unexpected error or unsupported image format. The credits have been refunded. Please try again later or delete the task.,
#         Nous n’avons pas pu générer votre vidéo en raison d’une erreur inattendue ou d’un format d’image non pris en charge. Les crédits ont été remboursés. Veuillez réessayer plus tard ou supprimez la tâche.,
#       ],
#       [
#         You will not be able to retrieve the video once deleted, so make sure you have saved a copy. Are you sure you want to delete the video?,
#         Vous ne pourrez pas récupérer la vidéo une fois qu'elle aura été supprimée, assurez-vous donc d'en avoir enregistré une copie. Êtes-vous sûr de vouloir supprimer la vidéo ?,
#       ],
#       [
#         You must import a video before you can use the Video-to-Photo feature.\\nDo you want to import a video now?,
#         Vous devez importer une vidéo avant de pouvoir utiliser la fonction Vidéo à Photo.\\nVoulez-vous importer une vidéo maintenant ?,
#       ],
#       [
#         The server is too busy to generate the video. The credits have been refunded. Please try again later or delete the task.,
#         Le serveur est trop occupé pour générer la vidéo. Les crédits ont été remboursés. Veuillez réessayer plus tard ou supprimez la tâche.,
#       ],
#       [
#         The photo import was unsuccessful. The following errors occurred during the import process:,
#         L'importation de photos a échoué. Les erreurs suivantes sont survenues au cours du processus d'importation :,
#       ],
#       [
#         $C $P could not load the following file:,
#         $C $P n'a pas pu charger le fichier suivant:,
#       ],
#       [
#         How to Upload,
#         Comment transférer,
#       ],
#       [
#         How to upload,
#         Comment transférer,
#       ],
#       [
#         Import photos into the library,
#         Importer les photos dans la bibliothèque,
#       ]
#     ]
# """
# glossary = None
# common_usage_table = None

# print(review_prompt_obj.review_prompt(source_text, reference_translation, target_translation, glossary, common_usage_table))