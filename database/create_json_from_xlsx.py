"""
This script reads an Excel file, extracts ENU and CHT columns,
and saves the data to a JSON file with format {index: [ENU, CHT]}.
"""

import pandas as pd
import json
import os
from pathlib import Path

def create_json_from_xlsx(
    target_language,
    excel_path,
    output_json_path
):
    """
    Read Excel file, extract ENU and CHT columns, and save as JSON.
    
    Args:
        excel_path (str): Path to the Excel file
        output_json_path (str): Path where the JSON file will be saved
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_json_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # Read the Excel file
        print(f"Reading Excel file: {excel_path}")
        df = pd.read_excel(excel_path)
        
        # Check if the required columns exist
        if 'ENU' not in df.columns or target_language not in df.columns:
            print(f"Error: Excel file must contain both 'ENU' and '{target_language}' columns")
            columns = df.columns.tolist()
            print(f"Available columns: {columns}")
            return False
        
        # Extract ENU and CHT columns
        enu_cht_data = {}
        for i, row in enumerate(df.itertuples(), 1):
            enu_value = getattr(row, 'ENU', '')
            cht_value = getattr(row, target_language, '')
            
            # Skip rows where either value is missing
            if pd.isna(enu_value) or pd.isna(cht_value):
                continue
                
            # Convert to string to ensure JSON serialization
            enu_value = str(enu_value).strip()
            cht_value = str(cht_value).strip()
            
            # Skip empty values
            if not enu_value or not cht_value:
                continue
                
            enu_cht_data[i] = (enu_value, cht_value)
        
        # Save to JSON file
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(enu_cht_data, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully created JSON file with {len(enu_cht_data)} entries: {output_json_path}")
        return True
        
    except Exception as e:
        print(f"Error creating JSON file: {str(e)}")
        return False

if __name__ == "__main__":
    # Get the Excel file path from command line arguments if provided
    import sys
    
    target_language = 'ITA'  # Default target language
    excel_path = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v10\database\PDR FAQ_ITA_result.xlsx"
    output_json_path = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v10\database\PDR_enu_ita_FAQ_database.json"
    
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_json_path = sys.argv[2]
        
    create_json_from_xlsx(target_language, excel_path, output_json_path)