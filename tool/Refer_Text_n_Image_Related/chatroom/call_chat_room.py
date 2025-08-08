import sys
import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add parent directories to sys.path to import project modules
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, project_root)
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from chat.openai_api_chat import OpenaiAPIChat
from prompts.translate_prompts import translate_sys_prompt, translate_prompt
from config.translate_config import TRANSLATE_MODEL
from pages.general_functions import as_json_obj, get_relevant_refer_text_from_image_table

# Setup basic logging
logging.basicConfig(level=logging.DEBUG)


class TranslationChatRoom:
    """
    Manages 4 different translation chat rooms with different reference configurations
    """
    
    def __init__(self, source_text: str, target_language: str, refer_text: Optional[str] = None, 
                 refer_image_path: Optional[str] = None, software_type: str = "UI", source_type: str = "UI"):
        self.source_text = source_text
        self.target_language = target_language
        self.refer_text = refer_text
        self.refer_image_path = refer_image_path
        self.software_type = software_type
        self.source_type = source_type
        
        # Initialize 4 chat rooms with different configurations
        self.chat_rooms = {
            'no_reference': None,
            'text_only': None,
            'image_only': None,
            'both_references': None
        }
        
        self.results = {}

        image_refer_text_table = {
                self.source_text: ["", self.refer_image_path]  # Empty refer_text, with image_path
            }
            
        # Get relevant refer text from image table
        self.relevant_refer_text_from_image_table = get_relevant_refer_text_from_image_table(
            image_refer_text_table, self.source_text
        )


        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for translation"""
        return translate_sys_prompt(
            src_lang="English",
            tgt_lang=self.target_language,
            software_type=self.software_type,
            source_type=self.source_type
        )
        
    def _create_user_prompt(self, include_refer_text: bool = False, include_refer_image: bool = False) -> str:
        """Create user prompt based on reference configuration using translate_prompt"""
        
        # Prepare refer_text_table based on configuration
        refer_text_table = {}
        if include_refer_text and self.refer_text:
            refer_text_table = {"refer_text": self.refer_text}
        
        # Handle image reference processing
        if include_refer_image and self.refer_image_path:
            refer_text_table.update(self.relevant_refer_text_from_image_table)
        
        # Create user prompt using translate_prompt
        user_prompt = translate_prompt(
            src_lang="English",
            tgt_lang=self.target_language,
            json_str=self.source_text,
            refer_data_list=[],  # Empty list for translation references
            specific_names=None,  # No specific names provided
            region_table=None,   # No region table provided
            refer_text_table=refer_text_table if refer_text_table else None,
            is_xlsx=False,
            suggestions=[],
            pre_translated_text=None
        )
        
        return user_prompt
    
    async def _get_translation_async(self, config_name: str, include_refer_text: bool, include_refer_image: bool) -> str:
        """Get translation from a specific chat room configuration"""
        try:
            # Get system prompt first
            system_prompt = self._get_system_prompt()
            
            # Create user prompt (image processing is handled within this method now)
            user_prompt = self._create_user_prompt(include_refer_text, include_refer_image)

            logging.debug(f"============================")
            logging.debug(f'for case, refer text= {include_refer_text}, refer image= {include_refer_image}')
            logging.debug(f"User prompt:")
            logging.debug(user_prompt)
            logging.debug(f"============================")

            # Create chat room with standard parameters (no image_path needed here anymore)
            chat_room = OpenaiAPIChat(
                model_name=TRANSLATE_MODEL,
                system_prompt=system_prompt,
                max_retry=10
            )
            
            # Get response
            response, finish_reason = await chat_room.get_aresponse(
                user_prompt=user_prompt
            )

            if not as_json_obj(response):
                logging.warning("Translation response is empty, breaking the loop.")

            translated_text = list(as_json_obj(response).values())[-1]

            return translated_text
            
        except Exception as e:
            error_msg = f"Error in {config_name}: {str(e)}"
            print(error_msg)
            logging.error(error_msg)
            return error_msg
    
    async def get_all_translations(self) -> Dict[str, str]:
        """Get translations from all 4 chat room configurations"""
        tasks = []
        
        # Create async tasks for all 4 configurations
        tasks.append(
            self._get_translation_async('no_reference', False, False)
        )
        tasks.append(
            self._get_translation_async('text_only', True, False)
        )
        tasks.append(
            self._get_translation_async('image_only', False, True)
        )
        tasks.append(
            self._get_translation_async('both_references', True, True)
        )
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Store results
        self.results = {
            'no_reference': str(results[0]) if not isinstance(results[0], Exception) else f"Error: {results[0]}",
            'text_only': str(results[1]) if not isinstance(results[1], Exception) else f"Error: {results[1]}",
            'image_only': str(results[2]) if not isinstance(results[2], Exception) else f"Error: {results[2]}",
            'both_references': str(results[3]) if not isinstance(results[3], Exception) else f"Error: {results[3]}"
        }
        
        return self.results
    
    def compare_translations(self) -> Dict[str, Any]:
        """Compare translations and highlight differences"""
        if not self.results:
            return {"error": "No translations available to compare"}
        
        translations = list(self.results.values())
        comparison_data = {
            'translations': self.results,
            'differences': []
        }
        
        # Find unique translations
        unique_translations = list(set(translations))
        if len(unique_translations) == 1:
            comparison_data['differences'].append("All translations are identical")
        else:
            comparison_data['differences'].append(f"Found {len(unique_translations)} unique translations")
            
            # Identify which configurations produced which results
            for i, (config, translation) in enumerate(self.results.items()):
                similar_configs = [k for k, v in self.results.items() if v == translation and k != config]
                if similar_configs:
                    comparison_data['differences'].append(
                        f"{config} matches with: {', '.join(similar_configs)}"
                    )
        
        return comparison_data


def run_translation_chat_rooms(source_text: str, target_language: str, 
                              refer_text: Optional[str] = None, 
                              refer_image_path: Optional[str] = None,
                              software_type: str = "UI",
                              source_type: str = "UI") -> Dict[str, Any]:
    """
    Main function to run translation with 4 different chat room configurations
    
    Args:
        source_text: The English text to translate
        target_language: Target language for translation
        refer_text: Optional reference text for context
        refer_image_path: Optional path to reference image
        software_type: Type of software (default: "UI")
        source_type: Type of source content (default: "UI")
    
    Returns:
        Dictionary containing all translation results and comparisons
    """
    
    # Create translation chat room manager
    translator = TranslationChatRoom(
        source_text=source_text,
        target_language=target_language,
        refer_text=refer_text,
        refer_image_path=refer_image_path,
        software_type=software_type,
        source_type=source_type
    )
    
    # Run all translations
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        translations = loop.run_until_complete(translator.get_all_translations())
        comparison = translator.compare_translations()
        
        return {
            'status': 'success',
            'translations': translations,
            'comparison': comparison,
            'input_data': {
                'source_text': source_text,
                'target_language': target_language,
                'refer_text': refer_text,
                'refer_image_path': refer_image_path,
                'software_type': software_type,
                'source_type': source_type
            }
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'translations': {},
            'comparison': {},
            'input_data': {
                'source_text': source_text,
                'target_language': target_language,
                'refer_text': refer_text,
                'refer_image_path': refer_image_path,
                'software_type': software_type,
                'source_type': source_type
            }
        }
    finally:
        loop.close()


if __name__ == "__main__":
    # Example usage
    result = run_translation_chat_rooms(
        source_text="Upgrade to Export Without Watermark",
        target_language="Traditional Chinese",
        refer_text="Revise the wording to better highlight the benefits and encourage user action.",
        refer_image_path=r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\0731_Source\refer_image\001.jpg",
        software_type="PHD",
        source_type="UI"
    )
    
    print("Translation Results:")
    for config, translation in result['translations'].items():
        print(f"\n{config}: {translation}")
    
    print(f"\nComparison: {result['comparison']}")
