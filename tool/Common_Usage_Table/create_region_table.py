import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from translate.translate import main as translate_main
import shutil
import json
import pandas as pd
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from bs4 import BeautifulSoup
from collections import OrderedDict
from chat.openai_api_chat import OpenaiAPIChat
from translation_memory.search_similar_pair import main as search_similar_pair_main
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

database_path = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v11\database\PHD_enu_deu_database.json"
specific_names_xlsx_pdr = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\Mapping_Table\specific_name_pdr365_DeuFraKor_0603.xlsx"
specific_names_xlsx_phd = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\Mapping_Table\specific_name_phd365_0603.xlsx"


def get_source_texts_from_database(database_content, index):
    if str(index) not in database_content:
        return None
    source_sentence = database_content[str(index)][0]
    sentence_length = len(source_sentence.split())
    if sentence_length > 3:
        return source_sentence
    else:
        return None
    
def get_gt_texts_from_database(database_content, index):
    """
    Retrieves the ground truth text from the database for a given index.
    :param database_content: The content of the database as a dictionary.
    :param index: The index of the entry to retrieve.
    :return: The ground truth text if available, otherwise None.
    """
    if str(index) not in database_content:
        return None
    gt_sentence = database_content[str(index)][1]
    sentence_length = len(gt_sentence.split())
    if sentence_length > 3:
        return gt_sentence
    else:
        return None

def save_text_to_xlsx(text, file_path):
    """
    Saves the given text to an Excel file.
    :param text: Text to be saved.
    :param file_path: Path to the output Excel file.
    """
    import pandas as pd
    df = pd.DataFrame({'English': [text]})
    df.to_excel(file_path, index=False)
    print(f"Text saved to {file_path}")

def copy_n_remove_database(database_path, index):
    """
    Copies the database file and removes the entry at the specified index.
    :param database_path: Path to the database JSON file.
    :param index: Index of the entry to be removed.
    """
    # Copy the database file
    backup_path = database_path.replace('.json', f'_backup.json')
    shutil.copy(database_path, backup_path)

    # Read the original database
    with open(database_path, 'r', encoding='utf-8') as f:
        database_content = json.load(f)

    # Remove the entry at the specified index
    if str(index) in database_content:
        del database_content[str(index)]

    # Write the updated content back to the original database file
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(database_content, f, ensure_ascii=False, indent=4)

    print(f"Entry {index} removed from the database")
    return backup_path

def read_database_json(database_path):
    """
    Reads the database JSON file and returns its content.
    :param database_path: Path to the database JSON file.
    :return: Content of the database as a dictionary.
    """
    with open(database_path, 'r', encoding='utf-8') as f:
        return json.load(f)

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

def get_system_prompt():
    return """This system's purpose is to compare two pieces of text: gt_text (ground truth text) and translated_text. The task is to identify the differences in vocabulary usage between these two texts and suggest specific words from translated_text that should be avoided in future translations. It should also identify words in gt_text that are ideal to use and should be emphasized during the translation. Provide the output in the following structure:

Steps:
 - Compare the gt_text and translated_text.
 - List the words or phrases that are present in either text and compare their usage or meaning.
 - Extract the words or phrases from both texts that are important and format them as:
    "source": Words that exist in gt_text and appear in the translation contextually. These words should be represented in English.
    "use": Words from the gt_text that should be used in the translation for accuracy. These words should be represented in English.
    "avoid": Words from the translated_text that deviate from the intended meaning and should be avoided in future translations. These words should also be represented in English.
 - Change the result to the output format as JSON.

Output format:
[For Word1 (English), Should Use (Word in gt_text), Should Avoid (Word in translated_text),
For Word2 (English), Should Use (Word in gt_text), Should Avoid (Word in translated_text), ...]

Where Word1, Word2, etc. are the words or phrases that are different between the two texts, and Should Use and Should Avoid are the corresponding words from gt_text and translated_text respectively.

Notice:
 - The output should be in JSON format.
 - Only extract the words or phrases that are different between the two texts, and ensure these words are contextually aligned.
 - The words in "source", "use", and "avoid" should be pairs that directly correspond to their respective contexts in English.
 - The words in the source field must appear in the original gt_text, but should be translated to English.
"""



def get_prompt(source_text, gt_text, translated_text):
    return f"""You are provided with a piece of source_text, gt_text (ground truth text), and translated_text. Your task is to identify the words that are used in gt_text but missing in the translated_text, the words that should be retained in future translations, and the words that should be avoided in future translations. The goal is to make the translation closer to the ground truth text.
 - source_text: This is the original text that provides context.
 - gt_text: This is the ground truth text (reference translation).
 - translated_text: This is the translation that needs to be improved.

The task is to:
 - Compare the words between gt_text and translated_text.
 - Identify and list the words that are missing from translated_text but should be in line with gt_text (these should be in the "source" list).
 - Identify the words from translated_text that are correct and align with gt_text (these should be in the "use" list).
 - Identify the words from translated_text that should be avoided because they diverge from the intended meaning in gt_text (these should be in the "avoid" list).
 - The words in the source list should appear in English, even though they are originally from gt_text. The same applies to the "use" and "avoid" lists, which should contain their English equivalents.

Source text:
{source_text}

Ground truth text:
{gt_text}

Translated text:
{translated_text}
"""



async def compare_sentence(source_text, gt_text, translated_text):
        sys_prompt = get_system_prompt()
        # print('='*40)
        # print(sys_prompt)
        # print('='*40)
        prompt = get_prompt(source_text, gt_text, translated_text)
        
        # print('='*40)
        # print(prompt)
        # print('='*40)


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
        print(f"Compare:\n {response}")
        
        # Extract JSON from markdown code blocks if present
        extracted_json = extract_json_from_markdown(response)
        
        # compare_result = as_json_obj(extracted_json)
        compare_result = json.loads(extracted_json)
        
        if compare_result:
            print(compare_result)
            return compare_result
        else:
            print("Failed to parse guidelines JSON")
            return None
        

def main(database_path):

    database_content = read_database_json(database_path)

    max_count = len(database_content)+1
    print(f"Total entries in the database: {max_count}")


    for index in range(1, max_count):
        try:
            print(f"Processing index: {index}")
            source_text = get_source_texts_from_database(database_content, index)
            gt_text = get_gt_texts_from_database(database_content, index)
            if source_text:
                print(f"Source text for index {index}: {source_text}")
            else:
                print(f"No valid source text found for index {index}.")
                continue

            save_text_to_xlsx(source_text, f"source_text.xlsx")

            backup_database_path = copy_n_remove_database(database_path, index)

            # Traslate the source text
            output_file = f"translated_text.xlsx"
            translate_main(
                p_in=f"source_text.xlsx",
                p_out=output_file,
                source_lang="English",
                target_lang="German",
                specific_names_xlsx=specific_names_xlsx_phd,  # Assuming no specific names for this example
                software_type="image editing software",
                source_type='UI',
                database_path=backup_database_path,
                review_report_path=None  # Assuming no review report for this example
            )

            # Get the translated text from the output file
            translated_df = pd.read_excel(output_file)
            if not translated_df.empty:
                translated_text = translated_df.iloc[0, 1]
                print(f"Translated text for index {index}: {translated_text}")
            else:
                print(f"No translated text found in {output_file} for index {index}.")
                continue

            #  Check if GT text is the same as translated text
            if gt_text:
                print(f"Ground truth text for index {index}: {gt_text}")
                if translated_text == gt_text:
                    print(f"Translated text matches ground truth for index {index}.")
                    continue
                else:
                    print(f"Translated text does not match ground truth for index {index}.")
                    print(f"Start comparing GT text and translated text for index {index}.")
            else:
                print(f"No ground truth text found for index {index}.")
                continue


            # Compare the GT text and translated text
            compare_result = asyncio.run(compare_sentence(source_text, gt_text, translated_text))
            print(f"Comparison result for index {index}: {compare_result}")

            # Append the response to a xlsx file with new_guidelines, guided_line
            if compare_result:
                output_file = f"region_table.xlsx"
                if not os.path.exists(output_file):
                    # Create a new workbook and add headers
                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.append(['English', 'Use', 'Avoid', 'Source Text', 'GT Text', 'Translated Text'])
                else:
                    # Load existing workbook
                    wb = openpyxl.load_workbook(output_file)
                    ws = wb.active
                
                for index in range(len(compare_result)):
                    ws.append([
                        compare_result[index]['source'],
                        compare_result[index]['use'] if 'use' in compare_result[index] else '',
                        compare_result[index]['avoid'] if 'avoid' in compare_result[index] else '',
                        source_text,
                        gt_text,
                        translated_text
                    ])
                # Save the workbook
                wb.save(output_file)
                print(f"Comparison results saved to {output_file}")
            else:
                print(f"No valid comparison result for index {index}, skipping saving to xlsx.")
        except Exception as e:
            print(f"Error processing index {index}: {e}")
            continue



if __name__ == "__main__":
    main(database_path)
    # source_text = "By uploading, posting or otherwise providing your submission, including without limitation, text, data, graphics, images, photos, effects, objects, templates and other content and information, you are granting to the public unrestricted and unconditional permission to:\na. Use, copy, distribute, display, publish and modify your submission.\nb. Publish your name or portrait in connection with your submission.\nc. Grant these permissions to other persons."
    # gt_text = "Durch das Hochladen, Einstellen oder anderweitige Einsenden insbesondere von Text, Daten, Grafiken, Bildern, Fotos, Effekten, Objekten, Vorlagen und anderen Inhalten und Informationen erteilen Sie der Öffentlichkeit die unbeschränkte und bedingungslose Genehmigung:\na. Ihre Einsendung zu verwenden, zu kopieren, zu verteilen, anzuzeigen, zu veröffentlichen und zu ändern.\nb. Ihren Namen oder Ihr Portrait in Verbindung mit Ihrer Einsendung zu veröffentlichen.\nc. Diese Genehmigungen anderen Personen zu erteilen."
    # translated_text= "Durch das Hochladen, Posten oder anderweitige Bereitstellen Ihrer Einsendung, einschließlich, aber nicht beschränkt auf, Text, Daten, Grafiken, Bilder, Fotos, Effekte, Objekte, Vorlagen und andere Inhalte und Informationen, erteilen Sie der Öffentlichkeit uneingeschränkte und bedingungslose Erlaubnis, um:\na. Ihre Einsendung zu verwenden, zu kopieren, zu verteilen, anzuzeigen, zu veröffentlichen und zu modifizieren.\nb. Ihren Namen oder Ihr Porträt im Zusammenhang mit Ihrer Einsendung zu veröffentlichen.\nc. Diese Erlaubnisse an andere Personen zu erteilen."
    # compare_result = asyncio.run(compare_sentence(source_text, gt_text, translated_text))
    # print(f"Comparison result: {compare_result}")