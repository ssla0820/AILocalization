import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from bs4 import BeautifulSoup
from collections import OrderedDict
from chat.openai_api_chat import OpenaiAPIChat
from database.search_similar_pair import main as search_similar_pair_main
from pages.general_functions import get_relevant_specific_names, as_json_obj, InlineGroup, get_text_group_inline, load_specific_names, detect_file_encoding
from prompts.translate_prompts import *
from prompts.restruct_prompts import *
from translate.restruct import *
from review.review import *
import asyncio
import re
import math
import pandas as pd
import openpyxl
from openpyxl.styles import Alignment
from config import translate_config as conf

def get_data_set(datapath):
    '''
    Read the database and return a list of sentence pairs.
    :param datapath: Path to the database file
    :return: List of sentence pairs
    '''
    #  Read datapath (json file)
    if not os.path.exists(datapath):
        raise FileNotFoundError(f"Database file not found at {datapath}")
    if datapath.endswith('.json'):
        with open(datapath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    return data


def get_compare_system_prompt(source_lang='English', target_lang='German'):
    return f"""This system analyzes the relationship between an {source_lang} sentence and its {target_lang} translation. It provides a detailed breakdown of the translation principles used, including:
     - Context Analysis: Examines how the context of both sentences affects their translation. It checks whether the translation preserves or adjusts the meaning based on the surrounding context.
     - Tone Matching: Analyzes whether the tone (formal, informal, neutral, etc.) is consistent between the English and German sentences.
     - Target Audience Understanding: Assesses whether the translation takes into account the target audience's cultural and linguistic preferences and understanding.
     - Use of Contextual Text: Looks at whether the translation relies on contextual understanding, like idiomatic expressions, regional variations, or cultural references, to convey the intended meaning.
     - For each sentence pair, the system will provide a detailed evaluation of how these principles have been applied.

    Notice:
     - Please don't mention something like: A words should be translated to B words
     - Return ONLY the JSON object without any markdown formatting, backticks, or code block indicators

    Response Format:
    The output should be in a dictionary format where:
    The key is the translation principle (e.g., "Context Analysis", "Tone Matching", "Target Audience Understanding", "Use of Contextual Text").
    The value is a list containing detailed content for each principle.

    For example, the response format will be as follows:
    {{
        "Context Analysis": [
            "Detailed content on how context is analyzed and applied in the translation."
        ],
        "Tone Matching": [
            "Detailed content on how tone is preserved or changed in the translation."
        ],
        "Target Audience Understanding": [
            "Explanation of how the translation reflects an understanding of the target audience."
        ],
        "Use of Contextual Text": [
            "Explanation of how contextual text was used or adapted in the translation."
        ]
    }}
"""

def get_compare_prompt(source_lang='English', target_lang='German', source_sentence=None, target_sentence=None):
    return f'''Please analyze the following {source_lang}-{target_lang} sentence pair and provide the translation principles used:

{source_lang}: "{source_sentence}"
{target_lang}: "{target_sentence}"
'''

def extract_json_from_markdown(text):
    """
    Extract JSON from markdown code blocks or plain text.
    
    Args:
        text (str): The text containing JSON data possibly in code blocks
        
    Returns:
        str: Extracted JSON string
    """
    # Try to extract JSON from code blocks (```json or ```python)
    code_block_pattern = r'```(?:json|python)?\s*([\s\S]*?)```'
    code_block_matches = re.findall(code_block_pattern, text)
    
    if code_block_matches:
        return code_block_matches[0].strip()
    
    # If no code blocks found, return the original text
    return text

async def compare_sentence(source_lang='English', target_lang='German',source_sentence: str=None, target_sentence: str=None):
        sys_prompt = get_compare_system_prompt(source_lang, target_lang)
        prompt = get_compare_prompt(source_lang, target_lang, source_sentence, target_sentence)

        # Initialize the chat with image_path if provided
        chat = OpenaiAPIChat(
            model_name=conf.TRANSLATE_MODEL,
            system_prompt=sys_prompt,
        )

        response, stop_reason = '', ''
        try:
            async for chunk, stop_reason in chat.get_stream_aresponse(prompt, temperature=0.01):
                response += chunk
            
            if stop_reason == 'length':
                raise RuntimeError
        except RuntimeError:
            raise RuntimeError("Guidedline exceeded length limit.")
        # print("===========================Used Prompt=============================")
        # print(f"{p}")
        # print("===========================Used Prompt=============================")
        print(f"Guidedline:\n {response}")
        
        # Extract JSON from markdown code blocks if present
        extracted_json = extract_json_from_markdown(response)
        
        guidelines = as_json_obj(extracted_json)
        
        if guidelines:
            print(guidelines)
            return guidelines
        else:
            print("Failed to parse guidelines JSON")
            return None
        


def get_combine_system_prompt():
     return f"""This system combines translation guidelines extracted from multiple sentence pairs to create a comprehensive set of guidelines.
     Notice:
      - Please don't mention something like: A words should be translated to B words
      - Please extract the items in the list, summary the content, and combine them back.
      - Return ONLY the JSON object without any markdown formatting, backticks, or code block indicators
     
     The output should be in a dictionary format similar to the input guidelines, where:
        The key is the translation principle (e.g., "Context Analysis", "Tone Matching", "Target Audience Understanding", "Use of Contextual Text").
        The value is a list containing consolidated content for each principle.
    """


def get_combine_prompt(guided_line=None, new_guidelines=None):
    guided_line_json = json.dumps(guided_line, ensure_ascii=False) if guided_line else "{}"
    new_guidelines_json = json.dumps(new_guidelines, ensure_ascii=False) if new_guidelines else "{}"
    
    return f"""Please combine the following translation guidelines into a comprehensive set of guidelines:
        1. {guided_line_json}
        2. {new_guidelines_json}
    The output should be in a dictionary format where:
        The key is the translation principle (e.g., "Context Analysis", "Tone Matching", "Target Audience Understanding", "Use of Contextual Text").
        The value is a list containing consolidated content for each principle.
        
    Please respond with ONLY the JSON object, without any markdown code blocks or additional text.
"""


async def combine_guidedline(guided_line=None, new_guidelines=None):
        sys_prompt = get_combine_system_prompt()
        prompt = get_combine_prompt(guided_line=guided_line, new_guidelines=new_guidelines)

        # Initialize the chat with image_path if provided
        chat = OpenaiAPIChat(
            model_name=conf.TRANSLATE_MODEL,
            system_prompt=sys_prompt,
        )

        response, stop_reason = '', ''
        try:
            async for chunk, stop_reason in chat.get_stream_aresponse(prompt, temperature=0.01):
                response += chunk
            
            if stop_reason == 'length':
                raise RuntimeError
        except RuntimeError:
            raise RuntimeError("Guidedline exceeded length limit.")
        # print("===========================Used Prompt=============================")
        # print(f"{p}")
        # print("===========================Used Prompt=============================")
        print(f"Guidedline:\n {response}")
        
        # Extract JSON from markdown code blocks if present
        extracted_json = extract_json_from_markdown(response)
        
        combined_guidelines = as_json_obj(extracted_json)
        
        if not combined_guidelines:
            print("Combined guideline is empty.")
            return None
            
        return combined_guidelines

def main(datapath, source_lang='English', target_lang='German', output_file=None):
    '''
    1. Read database
    2. Compare sentences
    3. Combine guidelines
    4. Save combined guidelines to a file
    
    :param datapath: Path to the database file
    :param source_lang: Source language
    :param target_lang: Target language
    :param output_file: Path to save the combined guidelines
    '''
    # Step 1: Read database
    data_dict = get_data_set(datapath)

    # Dictionary to accumulate guidelines
    guided_line = {}
    
    # Limit the number of sentence pairs to process (to avoid rate limiting)
    max_pairs = 500
    count = 0
    
    print(f"Processing up to {max_pairs} sentence pairs from {datapath}")
    
    for key, value in data_dict.items():
        if count >= max_pairs:
            break
            
        sentences = [value[0], value[1]]
        print(f"\nProcessing pair {count+1}/{max_pairs}: {key}")
        print(f"Source: {sentences[0]}")
        print(f"Target: {sentences[1]}")
        
        # Process each sentence pair and get the guidelines
        new_guidelines = asyncio.run(compare_sentence(source_lang=source_lang, target_lang=target_lang, 
                                 source_sentence=sentences[0], target_sentence=sentences[1]))
        
        if not new_guidelines:
            print(f"No guidelines found for pair {key}. Skipping...")
        else:
            print("\nCombining all guidelines...")
            combined_guided_line = asyncio.run(combine_guidedline(guided_line, new_guidelines))
            if combined_guided_line:
                guided_line = combined_guided_line
            else:
                print(f"Combined guidelines are empty for pair {key}. Skipping...")
                
        count += 1

        # Append the response to a xlsx file with new_guidelines, guided_line
        if output_file:
            if not os.path.exists(output_file):
                # Create a new workbook and add headers
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.append(['new_guidelines', 'guided_line'])
            else:
                # Load existing workbook
                wb = openpyxl.load_workbook(output_file)
                ws = wb.active
            
            # Append the new guidelines to the worksheet
            ws.append([json.dumps(new_guidelines, ensure_ascii=False), json.dumps(guided_line, ensure_ascii=False)])
            wb.save(output_file)

    



if __name__ == '__main__':
    datapath = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v11\database\PHD_enu_deu_database.json"
    source_lang = 'English'
    target_lang = 'German'
    output_file = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v11\combined_guidelines.xlsx"
    main(datapath, source_lang, target_lang, output_file=output_file)
