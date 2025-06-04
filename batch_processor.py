"""
Batch processor for HTML/XML translations using Excel configuration file.
This script processes an Excel file row by row, applying translation, verification,
and ground truth checking for each configuration row.

The batch Excel file can include the following columns:
- Required: INPUT_FILE_PATH_FOLDER, OUTPUT_FILE_PATH_FOLDER, COMPARE_FILE_PATH_FOLDER, 
  SOURCE_LANGUAGE, TARGET_LANGUAGE, SOFTWARE_TYPE
- Optional: SPECIFIC_NAMES_XLSX_PATH, IMAGE_PATH_FOLDER, CHECK_VERIFICATION, CHECK_GROUND_TRUTH, GROUND_TRUTH_PATH

Verification compares the source and translated files to check for translation quality.
To skip verification for a specific row, set CHECK_VERIFICATION column to "False".

Ground truth checking verifies translations against predefined expected values in a ground truth Excel file.
To enable ground truth checking, set CHECK_GROUND_TRUTH column to "True" for desired rows.
You can optionally specify a custom GROUND_TRUTH_PATH for each row.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
# import asyncio
import pandas as pd
from translate.translate import main as translate_main
# from verify import main as verify_main
from groundtruth_check.GroundTruth_Check import main as groundtruth_main
from config import translate_config
# import logging
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from config import translate_config as conf



def ensure_dir(dir_path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

def get_files_to_process(input_folder, extensions=['.html', '.htm', '.xml', '.xlsx', '.xls']):

    """
    Get list of files to process from the input folder.
    
    :param input_folder: Folder containing files to translate
    :param extensions: List of file extensions to include
    :return: List of file paths
    """
    files = []
    for root, _, filenames in os.walk(input_folder):
        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if ext.lower() in extensions:
                full_path = os.path.join(root, filename)
                files.append(full_path)
    return files

def get_output_filename(input_path, output_folder, target_language, is_compare_file=False, is_ground_truth_file=False, is_review_file=False):
    """
    Generate output filename with target language suffix.
    
    :param input_path: Input file path
    :param output_folder: Output folder
    :param target_language: Target language for translation
    :param is_compare_file: Whether this is a comparison file (always use .html extension)
    :return: Output file path
    """
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)
    
    # Create language suffix by removing spaces
    lang_suffix = target_language.replace(' ', '')
    
    # Handle file name conflicts with 2-digit counter (01, 02, etc.)
    counter = 1

    # For comparison files, always use .html extension
    if is_compare_file:
        ext = ".html"
    elif is_ground_truth_file or is_review_file:
        ext = ".xlsx"
    
    if is_review_file:
        output_filename = f"{name}_{lang_suffix}_Review_{counter:02d}{ext}"
        output_path = os.path.join(output_folder, output_filename)
    else:
        # Generate output filename
        output_filename = f"{name}_{lang_suffix}_{counter:02d}{ext}"
        output_path = os.path.join(output_folder, output_filename)
        

    while os.path.exists(output_path):
        output_filename = f"{name}_{lang_suffix}_{counter:02d}{ext}"
        output_path = os.path.join(output_folder, output_filename)
        counter += 1
        
    if is_compare_file or is_ground_truth_file or is_review_file:
        return output_path
    
    return output_path, f"{name}_{lang_suffix}"

def get_multi_language_xlsx_output(input_path, output_folder, target_languages, multi_language_code=None):
    """
    Generate output filename for multi-language Excel translations in a single file.
    
    :param input_path: Input file path
    :param output_folder: Output folder
    :param target_languages: List of target languages
    :param multi_language_code: Original multi-language code (e.g. '2L', '9L')
    :return: Output file path
    """
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)
    
    # Use the original multi-language code if provided, otherwise create a descriptive suffix
    if multi_language_code:
        lang_suffix = multi_language_code
    else:
        # For just two languages, show both names - for more than two, show count
        if len(target_languages) <= 2:
            lang_suffix = "_".join([lang.replace(' ', '') for lang in target_languages])
        else:
            lang_suffix = f"MultiLang_{len(target_languages)}"
    
    # Handle file name conflicts with 2-digit counter (01, 02, etc.)
    counter = 1
    
    # Generate output filename
    output_filename = f"{name}_{lang_suffix}_{counter:02d}{ext}"
    output_path = os.path.join(output_folder, output_filename)
    
    while os.path.exists(output_path):
        counter += 1
        output_filename = f"{name}_{lang_suffix}_{counter:02d}{ext}"
        output_path = os.path.join(output_folder, output_filename)
    
    return output_path

def create_results_excel(results_file_path):
    """
    Creates or updates the results Excel file with appropriate headers.
    
    :param results_file_path: Path to the results Excel file
    :return: None
    """
    # Check if file exists
    if not os.path.exists(results_file_path):
        # Create a new workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Translation Results"
          # Add headers
        headers = [
            "Source Path", 
            "Output Path", 
            "Source Language", 
            "Target Language", 
            "Translation Status", 
            "Verification Status",
            "Ground Truth Status",
            "Failed Sentences"
        ]
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
        
        # Save the file
        wb.save(results_file_path)
        print(f"Created new results file: {results_file_path}")

def add_result_to_excel(results_file_path, result_data):
    """
    Adds a result entry to the results Excel file.
    
    :param results_file_path: Path to the results Excel file
    :param result_data: Dictionary containing result data
    :return: None
    """
    # Create the file if it doesn't exist
    if not os.path.exists(results_file_path):
        create_results_excel(results_file_path)
    
    # Load the workbook
    wb = openpyxl.load_workbook(results_file_path)
    ws = wb.active
    
    # Get the next row
    next_row = ws.max_row + 1
    
    # Add data
    ws.cell(row=next_row, column=1).value = result_data.get('source_path', '')
    ws.cell(row=next_row, column=2).value = result_data.get('output_path', '')
    ws.cell(row=next_row, column=3).value = result_data.get('source_language', '')
    ws.cell(row=next_row, column=4).value = result_data.get('target_language', '')
    
    # Translation status with color coding
    translation_cell = ws.cell(row=next_row, column=5)
    translation_cell.value = result_data.get('translation_status', 'Failed')
    if translation_cell.value == 'Success':
        translation_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    else:
        translation_cell.fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")    # Verification status with color coding
    verification_cell = ws.cell(row=next_row, column=6)
    verification_cell.value = result_data.get('verification_status', 'Failed')
    if verification_cell.value == 'Success':
        verification_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    elif verification_cell.value == 'Failed':
        verification_cell.fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
    else:  # Skipped
        verification_cell.fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
    
    # Ground Truth status with color coding
    groundtruth_cell = ws.cell(row=next_row, column=7)
    groundtruth_cell.value = result_data.get('groundtruth_status', 'N/A')
    if groundtruth_cell.value == 'Success':
        groundtruth_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    elif groundtruth_cell.value == 'Failed':
        groundtruth_cell.fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
    else:  # N/A or skipped
        groundtruth_cell.fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
    
    # Failed sentences
    ws.cell(row=next_row, column=8).value = result_data.get('failed_sentences', '')
    
    # Save the workbook
    wb.save(results_file_path)

def extract_failed_sentences(compare_file_path):
    """
    Extracts failed sentences from comparison HTML file.
    
    :param compare_file_path: Path to the comparison HTML file
    :return: String of failed sentences, or empty string if none found or file doesn't exist
    """
    if not os.path.exists(compare_file_path):
        return ""
    
    try:
        from bs4 import BeautifulSoup
        
        # Try different encodings
        encodings = ['utf-8', 'utf-16', 'iso-8859-1', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                with open(compare_file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            print(f"Could not read comparison file with available encodings: {compare_file_path}")
            return ""
        
        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for elements with red background which typically indicate issues
        problem_elements = soup.find_all(style=lambda s: s and 'background-color: #ffcccc' in s)
        
        if not problem_elements:
            # Try different approach - find table rows with issues
            problem_rows = soup.find_all('tr', class_=lambda c: c and 'issue' in c.lower() if c else False)
            problem_elements = []
            for row in problem_rows:
                cells = row.find_all('td')
                if cells and len(cells) >= 2:
                    problem_elements.append(cells[1])  # Assuming second cell contains the translation
        
        failed_sentences = [elem.get_text().strip() for elem in problem_elements]
        return "; ".join(failed_sentences)
    
    except Exception as e:
        print(f"Error extracting failed sentences from {compare_file_path}: {str(e)}")
        return ""

def merge_xlsx_translations(original_file, translated_files, output_file):
    """
    Merge multiple translated Excel files into a single file with all languages as columns
    
    :param original_file: Path to the original input Excel file
    :param translated_files: List of translated Excel files to merge
    :param output_file: Path to save the merged output file
    :return: True if successful, False otherwise
    """
    try:
        print(f"Merging {len(translated_files)} translated XLSX files into: {output_file}")
        
        # Read the original file to get the base structure
        original_df = pd.read_excel(original_file)
        
        # Create a new dataframe starting with the original content
        merged_df = original_df.copy()
        
        # Process each translated file
        for trans_file in translated_files:
            try:
                # Get the language from the filename
                filename = os.path.basename(trans_file)
                name_parts = os.path.splitext(filename)[0].split('_')
                
                # The language should be in the second-to-last part (before the counter)
                if len(name_parts) < 3:
                    print(f"Warning: Could not determine language from filename: {filename}")
                    lang_name = f"Translation_{len(merged_df.columns) + 1}"
                else:
                    lang_name = name_parts[-2]
                
                # Read the translated file
                trans_df = pd.read_excel(trans_file)
                
                # Check if the dataframe has at least 2 columns (source + translation)
                if len(trans_df.columns) < 2:
                    print(f"Warning: Translated file has insufficient columns: {trans_file}")
                    continue
                
                # Get the second column (translation column)
                trans_column = trans_df.columns[1]
                
                # Add this column to the merged dataframe
                merged_df[lang_name] = trans_df[trans_column]
                
                print(f"Added {lang_name} translations from {trans_file}")
                
            except Exception as e:
                print(f"Error processing translated file {trans_file}: {str(e)}")
        
        # Save the merged dataframe
        merged_df.to_excel(output_file, index=False)
        
        # Apply formatting using openpyxl
        wb = openpyxl.load_workbook(output_file)
        ws = wb.active
        
        # Format the header row
        for col in range(1, ws.max_column + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
            
            # Auto-fit column width based on content
            max_length = 0
            for row in range(1, ws.max_row + 1):
                cell_value = ws.cell(row=row, column=col).value
                if cell_value:
                    max_length = max(max_length, len(str(cell_value)))
            adjusted_width = min(max(max_length + 2, 10), 80)  # Min 10, Max 80
            ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = adjusted_width
        
        wb.save(output_file)
        print(f"Successfully created merged Excel file: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error merging Excel files: {str(e)}")
        return False

def process_batch_file(batch_excel_path):
    """
    Process a batch Excel file with translation configurations.
    
    :param batch_excel_path: Path to the batch Excel file
    :return: Dictionary with results (success and error counts)
    """
    print(f"Starting batch processing using: {batch_excel_path}")
    
    if not os.path.exists(batch_excel_path):
        print(f"Batch Excel file not found: {batch_excel_path}")
        return {"success": 0, "error": 0}
    
    try:
        # Read batch Excel file
        df = pd.read_excel(batch_excel_path)
        
        # Check if required columns exist
        required_columns = [
            'SOURCE_TYPE',
            'INPUT_FILE_PATH_FOLDER', 
            'OUTPUT_FILE_PATH_FOLDER', 
            # 'COMPARE_FILE_PATH_FOLDER', 
            'SOURCE_LANGUAGE',
            'TARGET_LANGUAGE', 
            'SOFTWARE_TYPE',
            'REVIEW_PATH', 
        ]        # Optional column
        optional_columns = ['SPECIFIC_NAMES_XLSX_PATH', 'IMAGE_PATH_FOLDER', 'CHECK_VERIFICATION', 'CHECK_GROUND_TRUTH', 'GROUND_TRUTH_PATH', 'DATABASE_PATH']
        
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            print(f"Missing required columns in batch Excel: {', '.join(missing_cols)}")
            return {"success": 0, "error": 1}
        
        success_count = 0
        error_count = 0
        results_files = []
        
        # Process each row in the Excel file
        for index, row in df.iterrows():
            print(f"Processing row {index+1} of {len(df)}")
            
            # Extract configuration from the current row
            source_type = str(row['SOURCE_TYPE'])
            input_folder = str(row['INPUT_FILE_PATH_FOLDER'])
            output_folder = str(row['OUTPUT_FILE_PATH_FOLDER'])
            # compare_folder = str(row['COMPARE_FILE_PATH_FOLDER'])
            compare_folder = ''
            source_language = str(row['SOURCE_LANGUAGE'])
            target_language = str(row['TARGET_LANGUAGE'])
            software_type = str(row['SOFTWARE_TYPE'])
            review_folder = str(row['REVIEW_PATH'])

            
            # Check if this is a multi-language option
            target_languages = [target_language]
            is_multi_language = False
            if target_language in conf.MULTI_LANGUAGE_OPTIONS:
                print(f"Multi-language option '{target_language}' detected. Will translate to {len(conf.MULTI_LANGUAGE_OPTIONS[target_language])} languages.")
                target_languages = conf.MULTI_LANGUAGE_OPTIONS[target_language]
                is_multi_language = True
            
            # Get specific names Excel path if provided
            specific_names_xlsx = str(row.get('SPECIFIC_NAMES_XLSX_PATH', None) if 'SPECIFIC_NAMES_XLSX_PATH' in df.columns else None)
            
            # Get image path folder if provided
            image_path_folder = str(row.get('IMAGE_PATH_FOLDER', None) if 'IMAGE_PATH_FOLDER' in df.columns else None)
            database_path = str(row.get('DATABASE_PATH', None) if 'DATABASE_PATH' in df.columns else None)
            
            print(f"Configuration: {source_language} -> {', '.join(target_languages)}, Software: {software_type}")
            print(f"Source type: {source_type}")
            print(f"Input folder: {input_folder}")
            print(f"Output folder: {output_folder}")
            print(f"Compare folder: {compare_folder}")
            print(f"Review folder: {review_folder}")
            if image_path_folder:
                if str(image_path_folder) == 'nan':
                    print(f"Image path folder is nan, relocate to None")
                    image_path_folder = None
                print(f"Image path folder: {image_path_folder}")
            if database_path:
                if str(database_path) == 'nan':
                    print(f"Database path folder is nan, relocate to None")
                    database_path = None
                print(f"Database path folder: {database_path}")


            # Create output directories if they don't exist
            ensure_dir(output_folder)
            # ensure_dir(compare_folder)
            
            # Create results Excel file in the output folder for this row
            results_file = os.path.join(output_folder, f"translation_results_{source_language}_to_{target_language}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            create_results_excel(results_file)
            results_files.append(results_file)
            
            # For tracking XLSX files translations that need merging
            xlsx_files_to_merge = {}  # input_file -> list of translated files
            
            # Process each target language
            for current_target_language in target_languages:
                print(f"\n--- Processing language: {current_target_language} ---")
                
                # Get all files to process from input folder
                files_to_process = get_files_to_process(input_folder)
                print(f"Found {len(files_to_process)} files to process")
                
                if not files_to_process:
                    print(f"No files found in input folder: {input_folder}")
                    continue
                
                # Process each file
                for i, input_file in enumerate(files_to_process, 1):
                    try:
                        print('='*100)
                        print(f"Processing file {i} of {len(files_to_process)}: {input_file}")
                        print('='*100)

                        # Check if this is an Excel file
                        is_excel = input_file.lower().endswith(('.xlsx', '.xls'))
                        
                        # Generate output and compare file paths
                        output_file, ground_truth_file_name = get_output_filename(input_file, output_folder, current_target_language)
                        # compare_file = get_output_filename(input_file, compare_folder, f"{current_target_language}_Comparison", is_compare_file=True)
                        review_file = get_output_filename(input_file, review_folder, current_target_language, is_review_file=True)

                        print(f"Output file: {output_file}")
                        # print(f"Compare file: {compare_file}")
                        print(f"Ground truth file name: {ground_truth_file_name}")
                        
                        # Get the file-specific image path folder if available
                        file_specific_image_path = False
                        if image_path_folder:
                            # Get the base filename without extension to match with image folder name
                            base_filename = os.path.basename(input_file)
                            name_without_ext, _ = os.path.splitext(base_filename)
                            
                            # Construct the potential image folder path for this file
                            file_specific_image_path = os.path.join(image_path_folder, name_without_ext)
                            if not os.path.exists(file_specific_image_path) or not os.path.isdir(file_specific_image_path):
                                print(f"Warning: Image folder for {name_without_ext} not found at {file_specific_image_path}")
                                file_specific_image_path = False
                            else:
                                print(f"Found image folder for {name_without_ext} at {file_specific_image_path}")
                        
                        # Prepare result data dictionary
                        result_data = {
                            'source_path': input_file,
                            'output_path': output_file,
                            'source_language': source_language,
                            'target_language': current_target_language,
                            'translation_status': 'Failed',
                            'verification_status': 'Failed',
                            'groundtruth_status': 'N/A',
                            'failed_sentences': ''
                        }
                        
                        # Run translation
                        print(f"Starting translation...")
                        translation_success = False
                        try:
                            translate_main(input_file, output_file, source_language, current_target_language, 
                                        specific_names_xlsx, software_type, image_path=file_specific_image_path,
                                        source_type=source_type, database_path=database_path, review_report_path=review_file)
                            
                            translation_success = os.path.exists(output_file)
                            result_data['translation_status'] = 'Success' if translation_success else 'Failed'
                            print(f"Translation completed: {output_file}")
                            
                            # If this is an Excel file and it's part of a multi-language translation,
                            # add it to the list of files to merge later
                            if is_excel and is_multi_language and translation_success:
                                if input_file not in xlsx_files_to_merge:
                                    xlsx_files_to_merge[input_file] = []
                                xlsx_files_to_merge[input_file].append(output_file)
                                print(f"Added {output_file} to Excel files to be merged later")
                            
                        except Exception as e:
                            print(f"Error in translation: {str(e)}")
                            result_data['translation_status'] = 'Failed'
                        #   # Run verification only if translation succeeded
                        verification_success = None

                        # # Check if verification is enabled for this row (default to True)
                        # check_verification = True
                        # if 'CHECK_VERIFICATION' in df.columns:
                        #     check_verification_value = row.get('CHECK_VERIFICATION')
                        #     if isinstance(check_verification_value, str) and check_verification_value.lower() == 'false':
                        #         check_verification = False
                        #     elif isinstance(check_verification_value, bool) and not check_verification_value:
                        #         check_verification = False
                        
                        # if translation_success and check_verification:
                        #     print(f"Starting verification...")
                        #     try:
                        #         verify_main(
                        #             input_file, 
                        #             output_file, 
                        #             compare_file, 
                        #             specific_names_xlsx, 
                        #             software_type, 
                        #             source_language,  # Pass source language 
                        #             current_target_language,  # Pass target language
                        #             source_type=source_type,
                        #             translate_refer=None, 
                        #             database_path=database_path,
                        #         )

                        #         verification_success = os.path.exists(compare_file)
                        #         result_data['verification_status'] = 'Success' if verification_success else 'Failed'
                                
                        #         # Extract failed sentences if verification succeeded
                        #         if verification_success:
                        #             result_data['failed_sentences'] = extract_failed_sentences(compare_file)
                                    
                        #         print(f"Verification completed: {compare_file}")
                        #     except Exception as e:
                        #         print(f"Error in verification: {str(e)}")
                        #         result_data['verification_status'] = 'Failed'
                        # elif translation_success and not check_verification:
                        #     print(f"Verification skipped as per configuration")
                        #     result_data['verification_status'] = 'Skipped'
                        
                        # Run ground truth check if enabled
                        groundtruth_success = False
                        check_ground_truth = False
                        
                        # Check if ground truth verification is enabled for this row
                        if 'CHECK_GROUND_TRUTH' in df.columns:
                            check_ground_truth_value = row.get('CHECK_GROUND_TRUTH')
                            if isinstance(check_ground_truth_value, str) and check_ground_truth_value.lower() == 'true':
                                check_ground_truth = True
                            elif isinstance(check_ground_truth_value, bool) and check_ground_truth_value:
                                check_ground_truth = True
                        
                        # Get custom ground truth path if provided
                        ground_truth_path = None
                        if 'GROUND_TRUTH_PATH' in df.columns:
                            ground_truth_folder_path = row.get('GROUND_TRUTH_PATH')
                            ground_truth_path = os.path.join(ground_truth_folder_path, f'{ground_truth_file_name}.xlsx')

                        # Only run ground truth check if translation succeeded and it's enabled
                        if translation_success and check_ground_truth:
                            print(f"Starting ground truth verification...")
                            
                            try:
                                # Generate ground truth result file path
                                ground_truth_result = get_output_filename(
                                    input_file, 
                                    output_folder, 
                                    f"{current_target_language}_GroundTruth",
                                    is_ground_truth_file=True
                                )
                                
                                print(f"Ground truth output file: {ground_truth_result}")
                                
                                # Temporarily modify config if custom ground truth path provided
                                original_ground_truth_path = None
                                if ground_truth_path and hasattr(translate_config, 'GROUND_TRUTH_EXCEL_PATH'):
                                    original_ground_truth_path = translate_config.GROUND_TRUTH_EXCEL_PATH
                                    translate_config.GROUND_TRUTH_EXCEL_PATH = ground_truth_path
                                
                                # Set CHECK_GROUND_TRUTH to True temporarily if needed
                                original_check_ground_truth = getattr(translate_config, 'CHECK_GROUND_TRUTH', False)
                                translate_config.CHECK_GROUND_TRUTH = True
                                
                                # Run ground truth verification
                                groundtruth_main(                                    
                                    input_file,
                                    output_file,
                                    ground_truth_result,
                                    specific_names_xlsx,
                                    software_type,
                                    source_language,
                                    current_target_language,
                                    ground_truth_path=ground_truth_path,  # Use custom path if provided
                                )

                                # Restore original config values
                                translate_config.CHECK_GROUND_TRUTH = original_check_ground_truth
                                if original_ground_truth_path is not None:
                                    translate_config.GROUND_TRUTH_EXCEL_PATH = original_ground_truth_path
                                
                                groundtruth_success = os.path.exists(ground_truth_result)
                                result_data['groundtruth_status'] = 'Success' if groundtruth_success else 'Failed'
                                print(f"Ground truth verification completed: {ground_truth_result}")
                                
                            except Exception as e:
                                print(f"Error in ground truth verification: {str(e)}")
                                result_data['groundtruth_status'] = 'Failed'
                        else:
                            result_data['groundtruth_status'] = 'Skipped'
                          # Add result to Excel file
                        add_result_to_excel(results_file, result_data)
                        
                        # Track overall success/error counts
                        process_success = translation_success
                        # Verification is considered a success if it was done and succeeded, or if it was skipped
                        # Ground truth is considered a success if it succeeded or was skipped/not applicable
                        if process_success and (verification_success or result_data['verification_status'] == 'Skipped'):
                            if (groundtruth_success or result_data['groundtruth_status'] in ['Skipped', 'N/A']):
                                success_count += 1
                            else:
                                error_count += 1
                        else:
                            error_count += 1
                    except Exception as e:
                        print(f"Error processing file {input_file}: {str(e)}")
                        
                        # Add failed result to Excel
                        result_data = {
                            'source_path': input_file,
                            'output_path': output_file if 'output_file' in locals() else '',
                            'source_language': source_language,
                            'target_language': current_target_language,
                            'translation_status': 'Failed',
                            'verification_status': 'Failed',
                            'groundtruth_status': 'Failed',
                            'failed_sentences': str(e)
                        }
                        add_result_to_excel(results_file, result_data)
                        
                        error_count += 1
            
            # After processing all languages, merge the Excel files if needed
            if xlsx_files_to_merge:
                print(f"\n--- Merging Excel files for multi-language translations ---")
                
                for input_file, translated_files in xlsx_files_to_merge.items():
                    # Only merge if we have multiple files
                    if len(translated_files) > 1:
                        # Generate output filename for merged file with the original multi-language code
                        merged_output = get_multi_language_xlsx_output(input_file, output_folder, target_languages, target_language)
                        
                        print(f"Merging translations for {os.path.basename(input_file)} into {os.path.basename(merged_output)}")
                        
                        # Merge the files
                        merge_result = merge_xlsx_translations(input_file, translated_files, merged_output)
                          # Add result to Excel file
                        merge_result_data = {
                            'source_path': input_file,
                            'output_path': merged_output,
                            'source_language': source_language,
                            'target_language': target_language,  # Use the original multi-language code (e.g. '2L', '9L')
                            'translation_status': 'Success' if merge_result else 'Failed',
                            'verification_status': 'N/A',
                            'groundtruth_status': 'N/A',
                            'failed_sentences': ''
                        }
                        add_result_to_excel(results_file, merge_result_data)
                        
                        if merge_result:
                            print(f"Successfully merged Excel translations into: {merged_output}")
                        else:
                            print(f"Failed to merge Excel translations")
            
            print(f"Completed row {index+1} of {len(df)}")
        
        print(f"Batch processing completed. Success: {success_count}, Errors: {error_count}")
        print(f"Results saved to:")
        for results_file in results_files:
            print(f"  - {results_file}")
            
        return {"success": success_count, "error": error_count, "results_files": results_files}
        
    except Exception as e:
        print(f"Error processing batch file: {str(e)}")
        return {"success": 0, "error": 1}

def main(batch_excel_path=None):
    """
    Main entry point for batch processing.
    
    :param batch_excel_path: Path to the batch Excel file
    """
    # If no batch_excel_path provided, try to get it from translate_config
    if not batch_excel_path:
        if hasattr(translate_config, 'BATCH_EXCEL_PATH'):
            batch_excel_path = translate_config.BATCH_EXCEL_PATH
            print(f"Using BATCH_EXCEL_PATH from config: {batch_excel_path}")
        else:
            error_msg = "No BATCH_EXCEL_PATH parameter found in translate_config.py"
            print(error_msg)
            print(f"ERROR: {error_msg}")
            print("Please add BATCH_EXCEL_PATH to your translate_config.py file or provide it as an argument.")
            return {"success": 0, "error": 1}
    
    print(f"Starting batch processing with Excel: {batch_excel_path}")
    results = process_batch_file(batch_excel_path)
    
    print(f"Batch processing summary:")
    print(f"  Success: {results['success']} files")
    print(f"  Errors: {results['error']} files")
    
    if 'results_files' in results:
        print(f"  Results saved to:")
        for results_file in results['results_files']:
            print(f"    - {results_file}")
    
    return results

if __name__ == "__main__":

    # Check if BATCH_EXCEL_PATH exists in translate_config
    batch_excel_path = None
    if hasattr(translate_config, 'BATCH_EXCEL_PATH'):
        batch_excel_path = translate_config.BATCH_EXCEL_PATH
    
    # Run batch processing
    main(batch_excel_path)