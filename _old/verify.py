"""
Translation comparison module to compare two HTML/XML/Excel translations.
This module provides functionality to compare two files with translations
and generate an HTML report with the comparison results.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from bs4 import BeautifulSoup
import os
import asyncio
import pandas as pd
from chat.openai_api_chat import OpenaiAPIChat
from chat.gemini_api_chat import GeminiAPIChat
from prompts.translate_prompts import comparison_sys_prompt, comparison_prompt
from config import translate_config as conf
from translate.translate import get_text_group_inline, as_json_obj
from database.search_similar_pair import main as search_similar_pair_main

def extract_text_from_excel(file_path, is_source_file=True):
    """
    Extract text data from an Excel file.
    
    :param file_path: Path to the Excel file
    :param is_source_file: If True, read all columns; if False, read only target language columns
    :return: Dictionary mapping row indices to cell values
    """
    print(f"Extracting text from Excel file: {file_path}")
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Convert DataFrame to a dictionary with row indices as keys
        text_groups = {}
        
        if is_source_file:
            # For source file, extract all text
            for i, row in df.iterrows():
                # Convert row to string, join non-null values
                row_text = ' | '.join([str(val) for val in row.values if pd.notna(val)])
                if row_text.strip():  # Only include non-empty rows
                    text_groups[str(i+1)] = row_text
        else:
            # For target file, only extract target language text (assumed to be in the second column)
            for i, row in df.iterrows():
                # Check if there are at least 2 columns and the second column has a value
                if len(row) >= 2 and pd.notna(row[1]):
                    # Only take the second column (target language)
                    text_groups[str(i+1)] = str(row[1])
        
        print(f"Extracted {len(text_groups)} text segments from Excel file")
        return text_groups
    
    except Exception as e:
        print(f"Error extracting text from Excel file: {e}")
        return {}
    
def get_relevant_specific_names(specific_names, source_text):
    """
    Identify specific named entities in the current segment.
    :param specific_names: Dictionary of specific terms to translate in a specific way
    :param source_text: Source text content
    :return: Dictionary of relevant specific names
    """
    relevant_specific_names = {}
    if specific_names:
        for source_term, target_term in specific_names.items():
            # Deal with special cases
            special_cases = {0: ("&quot;", '"'), 1: (" &lt; ", " < "), 2: (" &gt; ", " > "), 3: (" &amp; ", " & "), 4: (" &amp;amp; ", " & ")}
            
            source_term_special = None
            for index, value in special_cases.items():
                if value[1] in source_term:
                    source_term_special = source_term.replace(value[1], value[0])

            if source_term_special:
                if source_term_special.lower() in source_text.lower() or source_term.lower() in source_text.lower():
                    relevant_specific_names[source_term] = target_term
                    relevant_specific_names[source_term_special] = target_term
            else:
                if source_term.lower() in source_text.lower():
                    relevant_specific_names[source_term] = target_term

    if relevant_specific_names:
        print(f"Source text '{source_text}'': Found {len(relevant_specific_names)} relevant specific names")
        print(f'Relevant specific names: {relevant_specific_names}')
    return relevant_specific_names

def make_model_object(model_list, software_type, source_type, source_lang, target_lang):
    chat_obj_list = []
    # Create LLM chat instance
    for model_name in model_list:
        if 'gemini' in model_name:
            # Create Gemini API chat instance
            chat_obj_list.append(
                GeminiAPIChat(
                    model_name=model_name,
                    system_prompt=comparison_sys_prompt(software_type, source_type, source_lang, target_lang)
                )
            )
        else:
            # Create LLM chat instance
            chat_obj_list.append(
                OpenaiAPIChat(
                    model_name=model_name,
                    system_prompt=comparison_sys_prompt(software_type, source_type, source_lang, target_lang)
                )
        )
    
    print(f'======================Used System Prompt======================')
    print(chat_obj_list[0].sys_prompt)
    print(f'======================Used System Prompt======================')
    return chat_obj_list

def get_refer_data(translate_refer, source_text, database_path):
    if translate_refer:
        return translate_refer
    elif not database_path:
        return []
    else:
        relevant_pair_database = search_similar_pair_main(
                tranlate_dict={"0": source_text}, 
                database_path=database_path, 
                grammar_top_n=5, 
                term_top_n=5
            )
        print(f"Relevant specific names for translation: {relevant_pair_database}")
        return relevant_pair_database


async def compare_result(
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
) -> None:
    """
    Compare two translated HTML files and generate a comparison report in HTML format.
    
    :param source_file_path: Path to the original source file (source language)
    :param target_file_path: Path to the first HTML file (target language)
    :param output_path_list: Path to save the comparison report HTML
    :param mode_list: List of modes to use for comparison (e.g., 'UI', 'Help', etc.)
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
    print(f"Starting comparison using source: {source_file_path}")
    print(f"Comparing source file with target file: {source_file_path} and {target_file_path}")
    print(f"Using source language: {source_lang}")
    print(f"Using target language: {target_lang}")
    print(f"Using software type: {software_type}")
    print(f"Using source type: {source_type}")
    
    # Import language detection and encoding functions from translate module
    from translate.translate import get_language_preferred_encodings, detect_file_encoding

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
        
    # Initialize comparison results
    comparison_results = []
    for model in model_list:
        comparison_results.append([])
    
    chat_obj_list = make_model_object(model_list, software_type, source_type, source_lang, target_lang)
    print(f'chat_obj_list: {chat_obj_list}')

    # Compare each segment
    print("Comparing segments...")
    for i, key in enumerate(sorted(common_keys, key=lambda x: int(x))):
        print(f"Comparing segment {i+1}/{len(common_keys)}")
        # try:
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
        
        # Identify specific named entities in the current segment
        relevant_specific_names = get_relevant_specific_names(specific_names, source_text)

        # Create the prompt
        relevant_pair_database = get_refer_data(translate_refer, source_text, database_path)
        prompt = comparison_prompt(source_text, translated_text, key, relevant_specific_names, source_lang, target_lang, relevant_pair_database)
        print('========================Used Prompt========================')
        print(prompt)
        print('========================Used Prompt========================')

        # Estimate token count - this is an approximation
        estimated_tokens = len(prompt) / 3  # Rough estimate: ~3 characters per token
        
        # Check if we might exceed token limit (using a conservative threshold)
        if estimated_tokens > 120000:  # Setting a conservative limit below the model's max
            print(f"  Segment {i+1}: Skipping comparison - estimated {int(estimated_tokens)} tokens exceeds safe limit")
            for _ in range(len(model_list)):
                comparison_results[_].append({
                    'segment_id': key,
                    'source_text': source_text,
                    'translation1': translated_text,
                    'translation2': None,
                    'same_meaning': False,
                    'better_translation': 'error',
                    'reason': f'Unable to compare: Text is too long (approximately {int(estimated_tokens)} tokens)'
                })
                continue
    

        for _ in range(len(model_list)):
            model_name = model_list[_]
            chat = chat_obj_list[_]
            comparison_result = comparison_results[_]
            print(comparison_result)


            print(f'start to ask LLM for response to {model_name}') 
            print(f'using chat obj: {chat}')
            kwargs = {"temperature": temperature}
            if 'gemini' in model_name:
                pass
            else:
                if seed is not None:
                    kwargs["seed"] = seed
            response, _ = await chat.get_aresponse(prompt, **kwargs)
            print(f'response from {model_name}: {response}')

            # Extract JSON response
            result = as_json_obj(response)
            if not result or 'same_meaning' not in result:
                print(f"  Segment {i+1}: Invalid response format from LLM")
                result = {
                    'same_meaning': False,
                    'better_translation': 'unknown',
                    'reason': 'Unable to determine (invalid LLM response format)'
                }
            # Add to results
            comparison_result.append({
                'segment_id': key,
                'source_text': source_text,
                'translation1': translated_text,
                'translation2': None,
                'same_meaning': result.get('same_meaning', False),
                'better_translation': result.get('better_translation', 'unknown'),
                'reason': result.get('reason', '')
            })
            
            accuracy_status = "ACCURATE" if result.get('same_meaning', False) else "ISSUES FOUND"
            # print(f"  Segment {i+1}: {accuracy_status} - {result.get('reason', '')[:30]}...")
                
        # except Exception as e:
        #     error_message = str(e)
        #     print(f"  Error comparing segment {i+1}: {error_message}")
            
        #     # Check if the error is related to token limit
        #     if "maximum context length" in error_message and "tokens" in error_message:
        #         reason = f'Unable to compare: {error_message}'
        #     else:
        #         reason = f'Error during comparison: {error_message}'
        #     for _ in range(len(model_list)):
        #         comparison_results[_].append({
        #             'segment_id': key,
        #             'source_text': source_text,
        #             'translation1': translated_text,
        #             'translation2': None,
        #             'same_meaning': False,
        #             'better_translation': 'error',
        #             'reason': reason
        #         })
        # Generate comparison HTML report
        for _ in range(len(model_list)):
            try:
                if 'gemini' in model_list[_]: model_name = 'Gemini'
                else: model_name = 'gpt4o'
                html_report = generate_comparison_report(comparison_results[_], source_file_path, target_file_path, source_lang, target_lang, model_name)
                # Use the same encoding as the source file for writing the report
                # This ensures compatibility with the original file's encoding
                if is_xlsx_file:
                    source_encoding = 'utf-8'
                with open(output_path_list[_], 'w', encoding=source_encoding) as f:
                    f.write(html_report)
                print(f"Comparison report saved to {output_path_list[_]} using {source_encoding} encoding")
            except Exception as e:
                print(f"Error generating comparison report: {e}")
        
    return comparison_results

def generate_comparison_report(comparison_results, source_file_path, file1_path, source_lang=None, target_lang=None, model_name=None):
    """
    Generate an HTML report from comparison results.
    
    :param comparison_results: List of comparison result dictionaries
    :param source_file_path: Path to the original source file
    :param file1_path: Path to the first HTML file
    :param source_lang: Source language name (e.g., 'English')
    :param target_lang: Target language name (e.g., 'Traditional Chinese')
    :param model_name: The name of the model used for comparison
    :return: HTML report as string
    """
    file1_name = os.path.basename(file1_path)
    source_file_name = os.path.basename(source_file_path)
      # Use provided language names or defaults
    source_lang_display = source_lang if source_lang else "Source Language"
    target_lang_display = target_lang if target_lang else "Target Language"
    model_display = model_name if model_name else "Unknown Model"
    
    # Count statistics
    same_meaning_count = 0
    diff_meaning_count = 0
    stats = {
        'both': 0,
        'file1': 0,
        'file2': 0,
        'unknown': 0,
        'error': 0,
        'total': len(comparison_results)
    }
    
    for result in comparison_results:
        better = result.get('better_translation', 'unknown')
        # Convert any 'neither' to 'unknown' since we're removing that option
        if better == 'neither':
            better = 'unknown'
            result['better_translation'] = 'unknown'
        
        stats[better] = stats.get(better, 0) + 1
        
        # Count same meaning vs different meaning
        if result.get('same_meaning', False):
            same_meaning_count += 1
        else:
            diff_meaning_count += 1
    
    # Create HTML report
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Translation Comparison Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        .stats {{
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }}
        .segment {{
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-bottom: 20px;
            padding: 15px;
            background-color: #fff;
        }}
        .segment-header {{
            background-color: #f1f1f1;
            padding: 10px;
            margin: -15px -15px 15px -15px;
            border-bottom: 1px solid #ddd;
            border-radius: 5px 5px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .comparison-container {{
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            margin-bottom: 15px;
            gap: 10px;
        }}
        .translation-column {{
            flex: 1;
            min-width: 30%;
            padding: 10px;
            border-radius: 5px;
            box-sizing: border-box;
        }}
        .source {{
            background-color: #f0f0f0;
            border-left: 5px solid #6c757d;
        }}
        .file1 {{
            background-color: #f2f9f2;
            border-left: 5px solid #28a745;
        }}
        .file2 {{
            background-color: #f2f9ff;
            border-left: 5px solid #007bff;
        }}
        .assessment {{
            background-color: #e9f7ef;
            padding: 10px;
            border-radius: 5px;
            border-left: 5px solid #16a085;
            clear: both;
        }}
        .same-meaning {{
            background-color: #d1f2eb;
        }}
        .different-meaning {{
            background-color: #f8d7da;
        }}
        .better-both {{
            background-color: #d1f2eb;
        }}
        .better-file1 {{
            background-color: #d4edda;
        }}
        .better-file2 {{
            background-color: #d1ecf1;
        }}
        .better-unknown, .better-error {{
            background-color: #fff3cd;
        }}
        .tag {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
            color: white;
        }}
        .tag-same {{
            background-color: #16a085;
        }}
        .tag-different {{
            background-color: #dc3545;
        }}
        .tag-both {{
            background-color: #16a085;
        }}
        .tag-file1 {{
            background-color: #28a745;
        }}
        .tag-file2 {{
            background-color: #007bff;
        }}
        .tag-unknown, .tag-error {{
            background-color: #ffc107;
            color: #333;
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 0;
            padding: 0;
        }}
        @media (max-width: 992px) {{
            .translation-column {{
                min-width: 100%;
                margin-bottom: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Translation Comparison Report</h1>
        <p>            Comparing translations between:<br>
            Source File ({source_lang_display}): <strong>{source_file_name}</strong><br>
            Target File ({target_lang_display}): <strong>{file1_name}</strong><br>
            Comparison Model: <strong>{model_display}</strong><br>
        </p>
        
        <div class="stats">
            <h2>Summary</h2>
            <p>Total segments compared: <strong>{stats['total']}</strong></p>
            <p>
                <strong>Same meaning: {same_meaning_count}</strong> segments<br>
                <strong>Different meaning: {diff_meaning_count}</strong> segments<br>
            </p>
        </div>
        
        <h2>Detailed Comparison</h2>
"""
    
    # Add each segment comparison
    for result in comparison_results:
        segment_id = result['segment_id']
        source_text = result['source_text']
        translation1 = result['translation1']
        same_meaning = result.get('same_meaning', False)
        better = result.get('better_translation', 'unknown')
        # Convert any 'neither' to 'unknown'
        if better == 'neither':
            better = 'unknown'
        reason = result.get('reason', '')
        
        # Determine CSS class for assessment box
        meaning_class = "same-meaning" if same_meaning else "different-meaning"
        
        # Determine tag text and class for meaning
        if same_meaning:
            meaning_tag_text = "SAME MEANING"
            meaning_tag_class = "tag-same"
        else:
            meaning_tag_text = "DIFFERENT MEANING"
            meaning_tag_class = "tag-different"
        
        quality_tag = ""
        
        html += f"""
        <div class="segment">
            <div class="segment-header">
                <span>Segment #{segment_id}</span>
                <div>
                    <span class="tag {meaning_tag_class}">{meaning_tag_text}</span>
                    {quality_tag}
                </div>
            </div>
            
            <div class="comparison-container">
                <div class="translation-column source">
                    <strong>{source_lang_display}:</strong><br>
                    <pre>{source_text}</pre>
                </div>
                <div class="translation-column file1">
                    <strong>{target_lang_display}:</strong><br>
                    <pre>{translation1}</pre>
                </div>
            </div>
            
            <div class="assessment {meaning_class}">
                <strong>Assessment:</strong><br>{reason}
            </div>
        </div>
"""
    
    # Close HTML
    html += """
    </div>
</body>
</html>
"""
    
    return html


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
         mode_list="default"):
    
    """Command-line entry point for comparison functionality"""
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
    if mode_list=="default":
        mode_list = conf.COMPARISON_MODEL
    print("Running in comparison mode...")
    print(f"Comparing Source file: {input_file_path}")
    print(f"Comparing Translated file: {output_file_path}")
    print(f"Output comparison base path: {compare_file_path}")
    print(f"Using software type: {software_type}")
    print(f"Using source language: {source_lang}")
    print(f"Using target language: {target_lang}")
    print(f"Using source type: {source_type}")
    print(f"Using database path: {database_path}")
    
    # Load specific names if configured
    specific_names = {}
    if specific_names_xlsx_path:
        try:
            from translate.translate import load_specific_names
            specific_names = load_specific_names(specific_names_xlsx_path, source_lang, target_lang)
            print(f"Loaded {len(specific_names)} specific name translations for comparison")
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
    for model_name in mode_list:
        model_output_path_list.append(f"{file_base}_{model_name.replace('-', '_')}{file_ext}")
    
    print(f"Output will be saved to: {model_output_path_list}")
    
    # Run the appropriate comparison based on file types
    asyncio.run(compare_result(
        input_file_path,
        output_file_path,
        model_output_path_list,
        mode_list,
        software_type,
        specific_names,
        temperature=temperature,                
        seed=seed,
        source_lang=source_lang,
        target_lang=target_lang,
        source_type=source_type,
        translate_refer=translate_refer,
        database_path=database_path
    ))

    print(f"Comparison completed")


if __name__ == '__main__':
    main()