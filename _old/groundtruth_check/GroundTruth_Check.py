"""
Ground Truth and Translation Comparison Module.

This module provides two main functionalities:
1. Ground Truth Verification: Checks translated text against predefined expected values
   from a ground truth Excel file. Used to validate translation quality against reference values.
2. Translation Comparison: Compares two HTML/XML/Excel translations and generates an HTML
   report with the comparison results.

Both modes generate output files that highlight differences and validation results.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from bs4 import BeautifulSoup
import os
import asyncio
import pandas as pd
from config import translate_config as conf



async def compare_with_ground_truth(
        source_file_path: str,
        translated_file_path: str, 
        ground_truth_result: str,
        software_type: str,
        specific_names: dict = None,
        model_name: str = conf.COMPARISON_MODEL,
        temperature: float = 0.3,
        seed: int = None,
        source_lang: str = conf.SOURCE_LANGUAGE,
        target_lang: str = conf.TARGET_LANGUAGE,
        ground_truth_path: str = None,
) -> None:
    """
    Compare a translated file against ground truth values from an Excel file.
    
    :param source_file_path: Path to the original source file (source language)
    :param file1_path: Path to the translated file (target language)
    :param output_path: Path to save the comparison result Excel file
    :param software_type: Type of software being translated
    :param specific_names: Dictionary of specific terms to translate in a specific way
    :param model_name: Model to use for comparison (not used in ground truth comparison)
    :param temperature: Temperature parameter (not used in ground truth comparison)
    :param seed: Seed parameter (not used in ground truth comparison)
    :param source_lang: Source language (e.g., 'English')
    :param target_lang: Target language (e.g., 'Traditional Chinese')
    :return: None
    """
    print(f"Starting ground truth verification")
    print(f"Using source file: {source_file_path}")
    print(f"Using translated file: {translated_file_path}")
    print(f"Output will be saved to: {ground_truth_result}")
    
    # 1. Read the ground truth Excel file
    try:
        print(f"Reading ground truth file: {ground_truth_path}")
        ground_truth_df = pd.read_excel(ground_truth_path)
        
        # Validate the ground truth file has the required columns
        required_columns = ["Batch", "Sources", "GroundTruth List", "Severity"]
        for col in required_columns:
            if col not in ground_truth_df.columns:
                raise ValueError(f"Ground truth file missing required column: {col}")
                
        print(f"Successfully read ground truth file with {len(ground_truth_df)} entries")
    except Exception as e:
        print(f"Error reading ground truth file: {e}")
        return
    
    # 2. Create a copy of the ground truth file for results
    result_df = ground_truth_df.copy()
    
    # Add new columns if they don't exist
    if "Translated Result" not in result_df.columns:
        result_df["Translated Result"] = ""
    if "Compare Result" not in result_df.columns:
        result_df["Compare Result"] = ""
    
    # 3. Read the translated file
    try:
        # Check if the translated file is an Excel file
        if translated_file_path.lower().endswith(('.xlsx', '.xls')):
            translated_df = pd.read_excel(translated_file_path)
            
            # Process each row in the ground truth file
            for idx, row in ground_truth_df.iterrows():
                source_text = row["Sources"]
                ground_truth_list = row["GroundTruth List"]
                
                # Find the translated text in the translated file
                # Assuming the first column has the source text and the second has the translation
                match_rows = translated_df[translated_df.iloc[:, 0] == source_text]
                
                if not match_rows.empty:
                    # Get the translated text (from the second column)
                    translated_text = match_rows.iloc[0, 1] if len(match_rows.iloc[0]) > 1 else ""
                    
                    # Update the result DataFrame
                    result_df.at[idx, "Translated Result"] = translated_text
                    
                    # 5. Check if translated text matches any ground truth in the list
                    ground_truth_items = [gt.strip() for gt in str(ground_truth_list).split(';') if gt.strip()]
                    
                    # 6. Compare with ground truth
                    if any(translated_text.strip() == gt for gt in ground_truth_items):
                        result_df.at[idx, "Compare Result"] = True
                    else:
                        result_df.at[idx, "Compare Result"] = False
                else:
                    print(f"Warning: Could not find source text in translated file: {source_text}")
                    result_df.at[idx, "Compare Result"] = "Not Found"
                    
        # If it's an HTML/XML file, we need different processing
        elif translated_file_path.lower().endswith(('.html', '.xml')):
            # Use the encoding detection function to open files
            from translate.translate import detect_file_encoding, get_text_group_inline
            _, html_content = detect_file_encoding(translated_file_path)
            
            # Parse the HTML/XML
            parser = 'xml' if translated_file_path.lower().endswith('.xml') else 'html.parser'
            bs = BeautifulSoup(html_content, parser)                
            # Extract text groups
            translated_groups = get_text_group_inline(bs)
            
            # Debug translated_groups
            print(f"Found {len(translated_groups)} text groups in the translated file")
            for key, group in translated_groups.items():
                print(f"Group {key}: Type={type(group)}, Text={str(group)[:50]}...")
            # Process each row in the ground truth file
            for idx, row in ground_truth_df.iterrows():
                source_text = row["Sources"]
                ground_truth_list = row["GroundTruth List"]
                
                # InlineGroup objects need to be converted to string
                translated_text = ""
                for key, text_group in translated_groups.items():
                    if str(key) == str(idx):
                        print(f'key {key} == idx {idx}')
                        translated_text = str(text_group)  # Convert InlineGroup to string
                        break
                    
                # If no match by index, try to find by content
                if not translated_text:
                    for key, text_group in translated_groups.items():
                        group_text = str(text_group)
                        if source_text in group_text:
                            translated_text = group_text
                            print(f'Found match by content in group {key}')
                            break
                            
                print(f"Translated text for source '{source_text}': {translated_text}")                # Update the result DataFrame
                result_df.at[idx, "Translated Result"] = translated_text
                
                # Check if translated text matches any ground truth in the list
                ground_truth_items = [gt.strip() for gt in str(ground_truth_list).split(';') if gt.strip()]
                
                # Compare with ground truth - Add fallback checks
                match_found = False
                # Try exact match first
                if translated_text:
                    for gt in ground_truth_items:
                        if gt in translated_text:
                            match_found = True
                            break
                
                result_df.at[idx, "Compare Result"] = match_found

                print(f"Processed row {idx + 1}/{len(ground_truth_df)}: Source: {source_text}, "
                      f"Translated: {translated_text}, Compare Result: {result_df.at[idx, 'Compare Result']}")
                print(f'The row is: {result_df.iloc[idx]}')
        else:
            print(f"Unsupported file type: {translated_file_path}")
            return
            
    except Exception as e:
        print(f"Error processing translated file: {e}")
        return
    
    # Save the result to Excel
    try:
        result_file_path = ground_truth_result
        
        # Calculate summary statistics
        total_items = len(result_df)
        matched_items = sum(result_df["Compare Result"] == True)
        not_matched_items = sum(result_df["Compare Result"] == False)
        not_found_items = sum(result_df["Compare Result"] == "Not Found")
        
        # Additional statistics by severity
        s1_false_items = sum((result_df["Compare Result"] == False) & (result_df["Severity"] == "S1"))
        s2_false_items = sum((result_df["Compare Result"] == False) & (result_df["Severity"] == "S2"))
        s3_false_items = sum((result_df["Compare Result"] == False) & (result_df["Severity"] == "S3"))
        none_false_items = sum((result_df["Compare Result"] == False) & (result_df["Severity"].isna()))
        
        # Calculate percentages for the summary report
        false_percentage = (not_matched_items / total_items * 100) if total_items > 0 else 0
        s1_percentage = (s1_false_items / not_matched_items * 100) if not_matched_items > 0 else 0
        s2_percentage = (s2_false_items / not_matched_items * 100) if not_matched_items > 0 else 0
        s3_percentage = (s3_false_items / not_matched_items * 100) if not_matched_items > 0 else 0
        none_percentage = (none_false_items / not_matched_items * 100) if not_matched_items > 0 else 0
        
        # Add empty rows as separator
        empty_rows = 3
        for _ in range(empty_rows):
            empty_row = pd.Series([""] * len(result_df.columns), index=result_df.columns)
            result_df = pd.concat([result_df, pd.DataFrame([empty_row])], ignore_index=True)
        
        # Get the exact number of columns in the dataframe
        num_cols = len(result_df.columns)
        
        # Create summary header with appropriate length
        summary_header_values = [""] * num_cols
        summary_header_values[0] = "SUMMARY REPORT"  # Put the text in the first column
        summary_header = pd.Series(summary_header_values, index=result_df.columns)
        result_df = pd.concat([result_df, pd.DataFrame([summary_header])], ignore_index=True)
        
        # Create summary rows - ensure headers align with the right number of columns
        # Calculate the starting index for the summary columns (last 3 columns)
        summary_col_idx = max(0, num_cols - 3)
        
        # Create header row with appropriate length
        header_values = [""] * num_cols
        if summary_col_idx < num_cols:
            header_values[summary_col_idx] = "Summary Title"
        if summary_col_idx + 1 < num_cols:
            header_values[summary_col_idx + 1] = "Count"
        if summary_col_idx + 2 < num_cols:
            header_values[summary_col_idx + 2] = "Percentage"
            
        header_row = pd.Series(header_values, index=result_df.columns)
        result_df = pd.concat([result_df, pd.DataFrame([header_row])], ignore_index=True)
        
        # Function to create summary rows with appropriate length
        def create_summary_row(title, count, percentage):
            values = [""] * num_cols
            if summary_col_idx < num_cols:
                values[summary_col_idx] = title
            if summary_col_idx + 1 < num_cols:
                values[summary_col_idx + 1] = str(count)
            if summary_col_idx + 2 < num_cols:
                values[summary_col_idx + 2] = f"{percentage:.2f}%"
            return pd.Series(values, index=result_df.columns)
        
        # Add All False summary
        all_false_row = create_summary_row("All False", not_matched_items, false_percentage)
        result_df = pd.concat([result_df, pd.DataFrame([all_false_row])], ignore_index=True)
        
        # Add S1 severity summary
        s1_row = create_summary_row("S1 severity", s1_false_items, s1_percentage)
        result_df = pd.concat([result_df, pd.DataFrame([s1_row])], ignore_index=True)
        
        # Add S2 severity summary
        s2_row = create_summary_row("S2 severity", s2_false_items, s2_percentage)
        result_df = pd.concat([result_df, pd.DataFrame([s2_row])], ignore_index=True)
        
        # Add S3 severity summary
        s3_row = create_summary_row("S3 severity", s3_false_items, s3_percentage)
        result_df = pd.concat([result_df, pd.DataFrame([s3_row])], ignore_index=True)
        
        # Add No severity summary
        none_row = create_summary_row("No severity", none_false_items, none_percentage)
        result_df = pd.concat([result_df, pd.DataFrame([none_row])], ignore_index=True)
        
        # Save to Excel
        print(f"Saving comparison results to: {result_file_path}")
        result_df.to_excel(result_file_path, index=False)
        print(f"Ground truth verification completed. Results saved to {result_file_path}")
        
        # Print summary statistics for console output
        print(f"\nSummary:")
        print(f"Total items: {total_items}")
        print(f"Matched items: {matched_items} ({matched_items/total_items*100:.2f}%)")
        print(f"Not matched items: {not_matched_items} ({not_matched_items/total_items*100:.2f}%)")
        print(f"False by severity:")
        print(f"  - S1 severity: {s1_false_items}")
        print(f"  - S2 severity: {s2_false_items}")
        print(f"  - S3 severity: {s3_false_items}")
        print(f"  - No severity: {none_false_items}")
        if not_found_items > 0:
            print(f"Items not found: {not_found_items} ({not_found_items/total_items*100:.2f}%)")
            
    except Exception as e:
        print(f"Error saving comparison results: {e}")
        
    return


def main(input_file_path=None, output_file_path=None, ground_truth_result=None, specific_names_xlsx_path=None, software_type=None, source_lang=None, target_lang=None, ground_truth_path=None):
    """
    Command-line entry point for ground truth verification functionality.
    This function is designed to be called by batch_processor.py.
    
    :param input_file_path: Path to the source file
    :param output_file_path: Path to the translated file to verify
    :param ground_truth_result: Path to save the ground truth verification results
    :param specific_names_xlsx_path: Path to Excel with specific names translations
    :param software_type: Type of software being translated
    :param source_lang: Source language code
    :param target_lang: Target language code
    :return: None
    """
    # Use provided parameters or fallback to config values
    if not input_file_path:
        input_file_path = conf.INPUT_FILE_PATH
    if not output_file_path:
        output_file_path = conf.OUTPUT_FILE_PATH
    if not ground_truth_result:
        ground_truth_result = conf.COMPARE_FILE_PATH
    if not specific_names_xlsx_path:
        specific_names_xlsx_path = conf.SPECIFIC_NAMES_XLSX
    if not software_type:
        software_type = conf.SOFTWARE_TYPE
    if not source_lang:
        source_lang = conf.SOURCE_LANGUAGE
    if not target_lang:
        target_lang = conf.TARGET_LANGUAGE
    if not ground_truth_path:
        ground_truth_path = conf.GROUND_TRUTH_EXCEL_PATH
        
    # For backward compatibility, use ground_truth_result as compare_file_path
    if hasattr(conf, 'CHECK_GROUND_TRUTH') and conf.CHECK_GROUND_TRUTH or ground_truth_result:
        print("Running in ground truth verification mode...")
        print(f"Source file: {input_file_path}")
        print(f"Translated file: {output_file_path}")
        print(f"Output comparison to: {ground_truth_result}")
        print(f"Using software type: {software_type}")
        print(f"Using source language: {source_lang}")
        print(f"Using target language: {target_lang}")
        print(f"Using ground truth path: {ground_truth_path}")
        print(f"Save Ground Truth Result to: {ground_truth_result}")
        
        # Ensure the ground truth Excel path is defined
        if not hasattr(conf, 'GROUND_TRUTH_EXCEL_PATH') or not conf.GROUND_TRUTH_EXCEL_PATH:
            print("Error: GROUND_TRUTH_EXCEL_PATH not defined in config file.")
            return False
            
        # Load specific names if configured
        specific_names = {}
        if specific_names_xlsx_path:
            try:
                from translate.translate import load_specific_names
                specific_names = load_specific_names(specific_names_xlsx_path, source_lang, target_lang)
                print(f"Loaded {len(specific_names)} specific name translations for ground truth verification")
            except Exception as e:
                print(f"Warning: Could not load specific names: {e}")
        
        # Call the compare_with_ground_truth function
        asyncio.run(compare_with_ground_truth(
            input_file_path,
            output_file_path,
            ground_truth_result,
            software_type,
            specific_names,
            source_lang=source_lang,
            target_lang=target_lang,
            ground_truth_path=ground_truth_path,
        ))
        
        print(f"Ground truth verification completed and saved to {ground_truth_result}")
        # Return True if the operation was successful (file was created)
        return os.path.exists(ground_truth_result)

if __name__ == '__main__':
    main()