"""
Translation review module to compare two HTML/XML/Excel translations.
This module provides functionality to compare two files with translations
and generate an HTML report with the review results.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from bs4 import BeautifulSoup
import os
import asyncio
import re
import pandas as pd
from chat.openai_api_chat import OpenaiAPIChat
from chat.gemini_api_chat import GeminiAPIChat
from prompts.review_prompts import *
from prompts.improve_prompts import *
from config import translate_config as conf
from pages.general_functions import *
from database.search_similar_pair import main as search_similar_pair_main
import json


def parse_json_column(value):
    """
    Parse a JSON string from Excel back to a Python dictionary/list.
    """
    if isinstance(value, str) and value.strip().startswith('{') and value.strip().endswith('}'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def make_model_object(model_list, software_type, source_type, source_lang, target_lang, image_path):
    chat_obj_list = []
    # Create LLM chat instance
    for model_name in model_list:
        if 'gemini' in model_name:
            # Create Gemini API chat instance
            
            chat_obj_list.append(
                [
                    GeminiAPIChat(
                        model_name=model_name,
                        system_prompt=review_sys_prompt_accuracy(source_lang, target_lang, software_type, source_type),
                        image_path=image_path
                    ),
                    GeminiAPIChat(
                        model_name=model_name,
                        system_prompt=review_sys_prompt_native(source_lang, target_lang, software_type, source_type),
                        image_path=image_path
                    ),
                    GeminiAPIChat(
                        model_name=model_name,
                        system_prompt=review_sys_prompt_word(source_lang, target_lang, software_type, source_type),
                        image_path=image_path
                    ),
                    GeminiAPIChat(
                        model_name=model_name,
                        system_prompt=review_sys_prompt_grammar(source_lang, target_lang, software_type, source_type),
                        image_path=image_path
                    ),
                    GeminiAPIChat(
                        model_name=model_name,
                        system_prompt=review_sys_prompt_consistency(source_lang, target_lang, software_type, source_type),
                        image_path=image_path
                    ),
                    GeminiAPIChat(
                        model_name=model_name,
                        system_prompt=review_sys_prompt_gender(source_lang, target_lang, software_type, source_type),
                        image_path=image_path
                    ),
                ]
            )
        else:
            # Create LLM chat instance
            chat_obj_list.append(
                [
                    OpenaiAPIChat(
                        model_name=model_name,
                        system_prompt= review_sys_prompt_accuracy(source_lang, target_lang, software_type, source_type),
                        image_path=image_path
                    ),
                    OpenaiAPIChat(
                        model_name=model_name,
                        system_prompt= review_sys_prompt_native(source_lang, target_lang, software_type, source_type),
                        image_path=image_path
                    ),
                    OpenaiAPIChat(
                        model_name=model_name,
                        system_prompt= review_sys_prompt_word(source_lang, target_lang, software_type, source_type),
                        image_path=image_path
                    ),
                    OpenaiAPIChat(
                        model_name=model_name,
                        system_prompt= review_sys_prompt_grammar(source_lang, target_lang, software_type, source_type),
                        image_path=image_path
                    ),
                    OpenaiAPIChat(
                        model_name=model_name,
                        system_prompt= review_sys_prompt_consistency(source_lang, target_lang, software_type, source_type),
                        image_path=image_path
                    ),
                    OpenaiAPIChat(
                        model_name=model_name,
                        system_prompt= review_sys_prompt_gender(source_lang, target_lang, software_type, source_type),
                        image_path=image_path
                    ),
                ]
        )

    # print(f'======================Used System Prompt======================')
    # print(chat_obj_list[0].sys_prompt)
    # print(f'======================Used System Prompt======================')
    return chat_obj_list

def get_refer_data(translate_refer, source_text, database_path):
    if translate_refer:
        return translate_refer
    elif not database_path:
        return []
    else:
        relevant_pair_database = search_similar_pair_main(
                translate_dict={"0": source_text}, 
                database_path=database_path, 
                grammar_top_n=5, 
                term_top_n=5
            )
        print(f"Relevant specific names for translation: {relevant_pair_database}")
        return relevant_pair_database

def get_text_group(source_file_path, target_file_path):
    is_xlsx_file = source_file_path.lower().endswith('.xlsx')
    #  Extract data from Excel file
    if is_xlsx_file:
        source_groups = extract_text_from_excel(source_file_path, is_source_file=True)
        target_groups = extract_text_from_excel(target_file_path, is_source_file=False)
        # Find common keys (row indices) that exist in both files
        common_keys = set(source_groups.keys()) & set(target_groups.keys())
        print(f"Found {len(common_keys)} common rows to compare")

    # Extract text data from HTML/ XML files
    else:
        # Determine file type for source and target files
        is_xml_source = source_file_path.lower().endswith('.xml')
        is_xml_target = target_file_path.lower().endswith('.xml')
        source_parser = 'xml' if is_xml_source else 'html.parser'
        target_parser = 'xml' if is_xml_target else 'html.parser'
        print(f"Source file type: {'XML' if is_xml_source else 'HTML'}, using {source_parser} parser")
        print(f"Target file type: {'XML' if is_xml_target else 'HTML'}, using {target_parser} parser")
    
        # Read files with encoding detection
        try:
            # Use the encoding detection function to open files
            source_encoding, source_html = detect_file_encoding(source_file_path)
            target_encoding, html1 = detect_file_encoding(target_file_path)
            
            print(f"Source file encoding: {source_encoding}")
            print(f"Target file encoding: {target_encoding}")
            
        except Exception as e:
            print(f"Error reading HTML/XML files: {e}")
            return
            
        # Parse HTML/XML with BeautifulSoup using appropriate parsers
        bs_source = BeautifulSoup(source_html, source_parser)
        bs1 = BeautifulSoup(html1, target_parser)
        
        # Extract text groups from files
        source_groups = get_text_group_inline(bs_source)
        target_groups = get_text_group_inline(bs1)
    
        # Find groups that exist in both files
        common_keys = set(source_groups.keys()) & set(target_groups.keys())
        print(f"Found {len(common_keys)} common text segments to compare")

    return source_groups, target_groups, common_keys, is_xlsx_file

def truncate_text_for_token_limit(text, max_length=1000):
    """
    Truncates text to fit within token limits.
    For very long texts, tries to preserve the beginning and end which often contain critical context.
    
    Args:
        text (str): The text to truncate
        max_length (int): Maximum allowed length
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Keep first and last parts, omit middle
    half_length = max_length // 2
    return text[:half_length] + "\n...[Content truncated for token limit]...\n" + text[-half_length:]

def compress_prompt_for_token_limit(prompt, level=1):
    """
    Applies different levels of compression to reduce token usage in prompts.
    
    Args:
        prompt (str): The original prompt
        level (int): Compression level (1-3, with 3 being most aggressive)
        
    Returns:
        str: Compressed prompt
    """
    if level == 1:
        # Level 1: Basic compression - remove unnecessary whitespace and shorten instructions
        compressed = re.sub(r'\s+', ' ', prompt)  # Replace multiple whitespaces with single space
        compressed = compressed.replace("Please provide a detailed analysis", "Analyze")
        compressed = compressed.replace("Please review the following translation", "Review this translation")
        return compressed
    
    elif level == 2:
        # Level 2: Medium compression - truncate examples and lengthy instructions
        compressed = re.sub(r'\s+', ' ', prompt)
        compressed = re.sub(r'For example:.*?(?=\n|$)', 'Be concise.', compressed)
        compressed = re.sub(r'Here are some guidelines.*?(?=\n|$)', '', compressed)
        return compressed
    
    elif level == 3:
        # Level 3: Maximum compression - reduce to core instruction only
        # Extract the essential parts - source text and translation only, with minimal instruction
        source_match = re.search(r'Source Text:.*?(?=\n|$)', prompt)
        source_text = source_match.group(0) if source_match else ""
        
        translation_match = re.search(r'Translation:.*?(?=\n|$)', prompt)
        translation_text = translation_match.group(0) if translation_match else ""
        
        return f"Review concisely: {source_text} {translation_text} List only critical errors."
    
    return prompt  # Default case


async def review_n_improve_process(source_lang,
                                    target_lang,
                                    software_type,
                                    source_type,
                                    source_text, 
                                    translated_text, 
                                    relevant_specific_names,
                                    relevant_pair_database,
                                    image_path,
                                    model_list=None, 
                                    review_chat_obj_list=None, 
                                    improve_chat=None,
                                    temperature=0.3, 
                                    seed=None,
                                    review_path=None,
                                    max_retry_times=3):
    
    # 如果沒有提供聊天對象，則創建新的
    if not review_chat_obj_list:
        review_chat_obj_list = make_model_object(model_list, software_type, source_type, source_lang, target_lang, image_path)
    
    if not improve_chat:
        improve_chat = OpenaiAPIChat(
                    model_name='gpt-4o',
                    system_prompt=improve_sys_prompt(source_lang, target_lang, software_type, source_type),
                    image_path=image_path
                )
    print(f'review_chat_obj_list: {review_chat_obj_list}')
    print(f'improve_chat_obj_list: {improve_chat}')
    print(f'Get translated text: {translated_text}')

    # try:
    review_result_dict = {"source_text": source_text}
    reviewed_dict = {}
    improved_dict = {0: translated_text}
    process_pass_flag = False

    for retry_time in range(max_retry_times):
        print(f'Current Doing {retry_time+1} times translation...')
        
        for _ in range(len(model_list)):
            model_name = model_list[_]
            print(f'========================Used Model: {model_name}========================')
            check_item_index_dict = {
                    0: 'accuracy',
                    1: 'native usage',
                    2: 'word correctness',
                    3: 'sentence structure',
                    4: 'consistency',
                    5: 'gender neutrality'
                }
            raw_review_response_dict ={}
            for check_item_index in range(len(review_chat_obj_list[_])):
                print(f'===========Checking Point: {check_item_index_dict[check_item_index]}===========')

                review_chat = review_chat_obj_list[_][check_item_index]
                kwargs = {"temperature": temperature}
                if seed is not None:
                    kwargs["seed"] = seed

                # First - do the review
                review_response = ''
                review_stop_reason = ''
                if check_item_index == 0:
                    prompt_text = review_prompt_accuracy(source_lang, target_lang, source_text, translated_text, relevant_specific_names, relevant_pair_database)
                elif check_item_index == 1:
                    prompt_text = review_prompt_native(source_lang, target_lang, source_text, translated_text, relevant_specific_names, relevant_pair_database)
                elif check_item_index == 2:
                    prompt_text = review_prompt_word(source_lang, target_lang, source_text, translated_text, relevant_specific_names, relevant_pair_database)
                elif check_item_index == 3:
                    prompt_text = review_prompt_grammar(source_lang, target_lang, source_text, translated_text, relevant_specific_names, relevant_pair_database)
                elif check_item_index == 4:
                    prompt_text = review_prompt_consistency(source_lang, target_lang, source_text, translated_text, relevant_specific_names, relevant_pair_database)
                elif check_item_index == 5:
                    prompt_text = review_prompt_gender(source_lang, target_lang, source_text, translated_text, relevant_specific_names, relevant_pair_database)

                # print('='*40)
                # print(f'Current review prompt:\n{prompt_text}')
                # print('='*40)

                # Handle possible token limitation
                try:
                    async for chunk, review_stop_reason in review_chat.get_stream_aresponse(prompt_text, **kwargs):
                        review_response += chunk
                        
                    if review_stop_reason == 'length':
                        print("Review response exceeded length limit but received partial content.")
                        raise RuntimeError("Review response too short after hitting length limit.")
                    
                except RuntimeError as e:
                    print(f"Review process failed: {str(e)}")
                    raise RuntimeError("Translation review failed due to length limit or other issues.")
                        
                print(f"Review response:\n {review_response}")
                
                # Parse the review response
                review_response_json = as_json_obj(review_response)
                raw_review_response_dict[check_item_index_dict[check_item_index]] = review_response_json

            print(f"Raw review response dictionary for {retry_time+1} times: {raw_review_response_dict}")

            if retry_time+1 not in reviewed_dict.keys():
                reviewed_dict[retry_time+1] = {model_name: None}

            if all (value is None for value in raw_review_response_dict.values()):
                print("Review response is empty or invalid JSON, attempting to extract useful information.")
                # Try to salvage some information from non-JSON response
                process_pass_flag = f'Error in review response with {model_name}'
                reviewed_dict[retry_time+1][model_name] = review_response
                continue
                    
            else:
                # # Check if the key exists in the dictionary
                # if key not in reviewed_dict[retry_time+1][model_name]:
                #     reviewed_dict[retry_time+1][model_name] = {}
                review_response_dict = {}
                for key, value in raw_review_response_dict.items():
                    if value is None or not isinstance(value, dict):
                        review_response_dict[key] = None
                    else:
                        review_response_dict[key] = value['Suggestions']
                        
                # Store the improvement suggestions
                reviewed_dict[retry_time+1][model_name] = review_response_dict
                print(f'reviewed_dict for {retry_time+1} times: {reviewed_dict}')

        print(f'Current reviewed_dict: {reviewed_dict}')

        if type(process_pass_flag) == str and 'Error in review response' in process_pass_flag:
            print("Error in review response, skipping re-translation.")
            break
        
        if (retry_time+1) in reviewed_dict and all(value is None for val in reviewed_dict[retry_time+1].values() for value in val.values()):
            print(f"All models returned None for review in attempt {retry_time+1}, skipping re-translation.")
            process_pass_flag = True
            break

        # Second - do the re-translation
        improve_response = ''
        improve_stop_reason = ''
        

        # Combine the review suggestions into a single string
        suggestions = []
        for model_name, suggestions_list in reviewed_dict[retry_time+1].items():
            if isinstance(suggestions_list, str):
                suggestions.append(suggestions_list)
            elif isinstance(suggestions_list, list):
                suggestions.extend(suggestions_list)
            elif isinstance(suggestions_list, dict):
                suggestions.extend(list(suggestions_list.values()))
        # suggestions = [s.strip() for s in suggestions if s.strip()]
        print(f"Suggestions for re-translation: {suggestions}")

        # Combine translated text (improved_dict) to a list
        translated_text_list_str = str(list(improved_dict.values()))
        print(f"Translated text list for re-translation: {translated_text_list_str}")

        improve_text = improve_prompt(source_lang, target_lang, source_text, translated_text, relevant_specific_names, relevant_pair_database, suggestions=suggestions, translated_text=translated_text_list_str)
        
        # print(f'='*40)
        # print(f'Current improve_text:\n{improve_text}')
        # print(f'='*40)
        try:
            async for chunk, improve_stop_reason in improve_chat.get_stream_aresponse(improve_text, temperature=0.01):
                improve_response += chunk
            
            if improve_stop_reason == 'length':
                raise RuntimeError("Improve response too short after hitting length limit.")
            
        except RuntimeError as e:
            print(f"Improve process failed: {str(e)}")
        
        print(f"Improve raw response:\n {improve_response}")
        
        # Parse the re-translation response                
        improve_json = as_json_obj(improve_response)
        if not improve_json:
            print("Improve response is not in expected JSON format, trying to extract translation.")
            translated_text = improve_response
            improved_dict[retry_time+1] = translated_text
            process_pass_flag = 'Error in improve response'
            break

        else:
            translated_text = list(improve_json.values())[-1]
            improved_dict[retry_time+1] = translated_text

        if retry_time == 2:
            process_pass_flag = False

    if 2 not in reviewed_dict.keys(): reviewed_dict[2] = {}
    if 3 not in reviewed_dict.keys(): reviewed_dict[3] = {}

    for model_name in model_list:
        if model_name not in reviewed_dict[2].keys():
            reviewed_dict[2][model_name] = 'N/A'
        if model_name not in reviewed_dict[3].keys():
            reviewed_dict[3][model_name] = 'N/A'

    if 1 not in improved_dict.keys(): improved_dict[1] = 'N/A'
    if 2 not in improved_dict.keys(): improved_dict[2] = 'N/A'
    if 3 not in improved_dict.keys(): improved_dict[3] = 'N/A'

    print(f'Current review result: {reviewed_dict}')
    print(f'Current improved result: {improved_dict}')

    for key, value in reviewed_dict.items():
        for model_name, suggestions in value.items():
            # Format suggestions dictionary with proper indentation if it's a dictionary
            if isinstance(suggestions, dict):
                import json
                # Store as a formatted JSON string with indentation
                review_result_dict[f"{model_name}_review_{key}"] = json.dumps(suggestions, indent=4)
            else:
                review_result_dict[f"{model_name}_review_{key}"] = suggestions
        
        review_result_dict[f"improved_{key}"] = improved_dict[key]

    review_result_dict["review_pass_flag"] = process_pass_flag
    review_result_dict["final_translated_text"] = translated_text

    print('='*40)
    print(review_result_dict)
    print('='*40)
    # Append review_result_dict to the "review_results.xlsx" file
    if review_path:
        # Load existing results if the file exists, otherwise create a new DataFrame
        if os.path.exists(review_path):
            try:
                existing_df = pd.read_excel(review_path)
                # Parse any JSON strings in the DataFrame
                for col in existing_df.columns:
                    if "_review_" in col:
                        existing_df[col] = existing_df[col].apply(parse_json_column)
            except Exception as e:
                print(f"Error reading {review_path}: {e}")
                existing_df = pd.DataFrame()
        else:
            existing_df = pd.DataFrame()

        # Convert the review result into a DataFrame row
        new_df = pd.DataFrame([review_result_dict])

        # Append the new data
        final_df = pd.concat([existing_df, new_df], ignore_index=True)

        # Save the updated results back to the Excel file
        final_df.to_excel(review_path, index=False)
    return translated_text, process_pass_flag

    # except Exception as e:
    #     error_message = str(e)
    #     print(f"{error_message}")
    #     return 'exception', error_message

# 修改後的 compare_result 函數，修復了事件循環問題
async def process_segments(
        source_groups,
        target_groups,
        common_keys,
        is_xlsx_file,
        model_list,
        software_type,
        source_type,
        source_lang,
        target_lang,
        specific_names,
        translate_refer,
        database_path,
        temperature,
        seed,
        review_report_path
):
    review_results = []
    
    # # 建立模型物件，在循環外部只建立一次
    # review_chat_obj_list = make_model_object(model_list, software_type, source_type, source_lang, target_lang, image_path=None)

    for i, key in enumerate(sorted(common_keys, key=lambda x: int(x))):
        print(f"Comparing segment {i+1}/{len(common_keys)}")
        
        # Get the corresponding group from each file
        if is_xlsx_file:
            source_text = source_groups.get(key, "Source text not available")
            translated_text = target_groups.get(key)
        else:
            source_group = source_groups.get(key)
            group1 = target_groups[key]
            
            # Get text content
            source_text = str(source_group) if source_group else "Source text not available"
            translated_text = str(group1)
            
        print(f'Current is doing source text {source_text}')
        
        # Identify specific named entities in the current segment
        relevant_specific_names = get_relevant_specific_names(specific_names, source_text)

        # Create the prompt
        relevant_pair_database = get_refer_data(translate_refer, source_text, database_path)
        
        # 使用 await 而不是 asyncio.run() 來呼叫 review_n_improve_process
        result = await review_n_improve_process(
            source_lang=source_lang,
            target_lang=target_lang,
            software_type=software_type,
            source_type=source_type,
            source_text=source_text,
            translated_text=translated_text,
            relevant_specific_names=relevant_specific_names,
            relevant_pair_database=relevant_pair_database,
            image_path=None,
            model_list=model_list,
            # review_chat_obj_list=review_chat_obj_list,
            # improve_chat=improve_chat,
            temperature=temperature,
            seed=seed,
            review_path=review_report_path
        )
        
        review_results.append(result)
    
    return review_results

def compare_result(
        source_file_path: str,
        target_file_path: str, 
        output_path_list: list,
        model_list: list,
        software_type: str,
        specific_names: dict = None,
        temperature: float = 0.3,
        seed: int = None,
        source_lang: str = conf.SOURCE_LANGUAGE,
        target_lang: str = conf.TARGET_LANGUAGE,
        source_type: str = conf.SOURCE_TYPE,
        translate_refer: list = None,
        database_path: str = None,
        review_report_path: str = None
) -> None:
    """
    Compare two translated HTML files and generate a review report in HTML format.
    
    :param source_file_path: Path to the original source file (source language)
    :param target_file_path: Path to the first HTML file (target language)
    :param output_path_list: Path to save the review report HTML
    :param mode_list: List of modes to use for review (e.g., 'UI', 'Help', etc.)
    :param specific_names: Dictionary of specific terms to translate in a specific way
    :param temperature: Temperature parameter for controlling randomness (0.0-2.0, lower is more deterministic)
    :param seed: Optional seed value for reproducible results
    :param source_lang: Source language (e.g., 'English')
    :param target_lang: Target language (e.g., 'Traditional Chinese')
    :param source_type: Type of source file (e.g., 'UI', 'Help', etc.)
    :param software_type: Type of software being translated (e.g., 'video editing software', 'image editing software', etc.)
    :param translate_refer: List of references for translation
    :param database_path: Path to the database for translation references
    :return: None
    """
    print(f"Starting review using source: {source_file_path}")
    print(f"Comparing source file with target file: {source_file_path} and {target_file_path}")
    print(f"Using source language: {source_lang}")
    print(f"Using target language: {target_lang}")
    print(f"Using software type: {software_type}")
    print(f"Using source type: {source_type}")
    
    source_groups, target_groups, common_keys, is_xlsx_file = get_text_group(source_file_path, target_file_path)
    print(f'Source groups: {len(source_groups)} segments found')
    
    # Initialize review results
    review_results = []
    for model in model_list:
        review_results.append([])
    
    # 正確設置和管理事件循環
    print("Comparing segments...")
    # try:
    # 使用一個新的事件循環
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 運行非同步處理函數
    results = loop.run_until_complete(
        process_segments(
            source_groups,
            target_groups,
            common_keys,
            is_xlsx_file,
            model_list,
            software_type,
            source_type,
            source_lang,
            target_lang,
            specific_names,
            translate_refer,
            database_path,
            temperature,
            seed,
            review_report_path
        )
    )
    
    # 最後關閉事件循環
    loop.close()
    
    # 處理結果
    review_results.extend(results)
        
    # except Exception as e:
    #     print(f"Error during review: {e}")
    
    # 可以在這裡處理和保存比較結果
    print("review processing completed")


def main(
        input_file_path="default", 
         output_file_path="default", 
         compare_file_path="default", 
         specific_names_xlsx_path="default", 
         software_type="default", 
         source_lang="default", 
         target_lang="default",
         source_type="default",
         translate_refer="default",
         database_path="default",
         model_list="default",
         review_report_path="default"):
    
    """Command-line entry point for review functionality"""
    if input_file_path=="default":
        input_file_path = conf.INPUT_FILE_PATH
    if output_file_path=="default":
        output_file_path = conf.OUTPUT_FILE_PATH
    if compare_file_path=="default":
        compare_file_path = conf.COMPARE_FILE_PATH
    if specific_names_xlsx_path=="default":
        specific_names_xlsx_path = conf.SPECIFIC_NAMES_XLSX
    if software_type=="default":
        software_type = conf.SOFTWARE_TYPE
    if source_lang=="default":
        source_lang = conf.SOURCE_LANGUAGE
    if target_lang=="default":
        target_lang = conf.TARGET_LANGUAGE
    if source_type=="default":
        source_type = conf.SOURCE_TYPE
    if database_path=="default":
        database_path = conf.DATABASE_PATH
    if model_list=="default":
        model_list = conf.COMPARISON_MODEL
    print("Running in review mode...")
    print(f"Comparing Source file: {input_file_path}")
    print(f"Comparing Translated file: {output_file_path}")
    print(f"Output review base path: {compare_file_path}")
    print(f"Using software type: {software_type}")
    print(f"Using source language: {source_lang}")
    print(f"Using target language: {target_lang}")
    print(f"Using source type: {source_type}")
    print(f"Using database path: {database_path}")
    
    # Load specific names if configured
    specific_names = {}
    if specific_names_xlsx_path:
        try:
            specific_names = load_specific_names(specific_names_xlsx_path, source_lang, target_lang)
            print(f"Loaded {len(specific_names)} specific name translations for review")
        except Exception as e:
            print(f"Warning: Could not load specific names: {e}")
    
    # Get temperature and seed from config if available
    temperature = getattr(conf, 'TEMPERATURE', 0.3)
    seed = getattr(conf, 'SEED', None)
    
    if temperature != 0.3:
        print(f"Using temperature: {temperature}")
    if seed is not None:
        print(f"Using seed: {seed}")
      # Check file extensions to determine file type

    # Create model-specific output file path by appending model name to the filename
    file_base, file_ext = os.path.splitext(compare_file_path)
    model_output_path_list = []
    for model_name in model_list:
        model_output_path_list.append(f"{file_base}_{model_name.replace('-', '_')}{file_ext}")
    
    print(f"Output will be saved to: {model_output_path_list}")
    
    # Run the appropriate review based on file types
    compare_result(
        input_file_path,
        output_file_path,
        model_output_path_list,
        model_list,
        software_type,
        specific_names,
        temperature=temperature,                
        seed=seed,
        source_lang=source_lang,
        target_lang=target_lang,
        source_type=source_type,
        translate_refer=translate_refer,
        database_path=database_path,
        review_report_path=review_report_path
    )

    print(f"review completed")


if __name__ == '__main__':
    main()
