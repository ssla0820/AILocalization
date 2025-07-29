import pandas as pd
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def combine_xlsx_files(file_paths, output_path, sheet_name=None, method='concat'):
    """
    Combine multiple XLSX files into a single file.
    
    Args:
        file_paths (list): List of paths to XLSX files to combine
        output_path (str): Path where the combined file will be saved
        sheet_name (str, optional): Specific sheet name to read from each file. 
                                   If None, reads the first sheet
        method (str): Method to combine files. Options:
                     - 'concat': Concatenate all data vertically (default)
                     - 'separate_sheets': Keep each file as a separate sheet
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        combined_data = []
        file_info = []
        
        # Validate input files
        valid_files = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue
            if not file_path.lower().endswith('.xlsx'):
                logger.warning(f"Not an XLSX file: {file_path}")
                continue
            valid_files.append(file_path)
        
        if not valid_files:
            logger.error("No valid XLSX files found")
            return False
        
        logger.info(f"Processing {len(valid_files)} files...")
        
        # Read and process each file
        for i, file_path in enumerate(valid_files):
            try:
                logger.info(f"Reading file {i+1}/{len(valid_files)}: {os.path.basename(file_path)}")
                
                # Read the Excel file
                if sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                else:
                    df = pd.read_excel(file_path)
                
                # Add source file information
                df['source_file'] = os.path.basename(file_path)
                df['source_file_index'] = i + 1
                
                combined_data.append(df)
                file_info.append({
                    'file_name': os.path.basename(file_path),
                    'file_path': file_path,
                    'rows': len(df),
                    'columns': len(df.columns)
                })
                
                logger.info(f"  - Shape: {df.shape}")
                
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {str(e)}")
                continue
        
        if not combined_data:
            logger.error("No data was successfully read from any file")
            return False
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Save combined data based on method
        if method == 'concat':
            # Concatenate all data vertically
            combined_df = pd.concat(combined_data, ignore_index=True, sort=False)
            logger.info(f"Combined data shape: {combined_df.shape}")
            
            # Save to Excel file
            combined_df.to_excel(output_path, index=False)
            logger.info(f"Combined file saved to: {output_path}")
            
        elif method == 'separate_sheets':
            # Save each file as a separate sheet
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for i, df in enumerate(combined_data):
                    sheet_name = f"Sheet_{i+1}_{Path(valid_files[i]).stem}"
                    # Excel sheet names have a 31 character limit
                    if len(sheet_name) > 31:
                        sheet_name = sheet_name[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    logger.info(f"Added sheet: {sheet_name}")
            
            logger.info(f"Combined file with separate sheets saved to: {output_path}")
        
        else:
            logger.error(f"Unknown method: {method}")
            return False
        
        # Print summary
        logger.info("=== COMBINATION SUMMARY ===")
        logger.info(f"Total files processed: {len(combined_data)}")
        for info in file_info:
            logger.info(f"  - {info['file_name']}: {info['rows']} rows, {info['columns']} columns")
        
        if method == 'concat':
            total_rows = sum(info['rows'] for info in file_info)
            logger.info(f"Total combined rows: {total_rows}")
        
        logger.info(f"Output saved to: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error combining files: {str(e)}")
        return False

def combine_xlsx_files_advanced(file_paths, output_path, options=None):
    """
    Advanced XLSX file combination with more options.
    
    Args:
        file_paths (list): List of paths to XLSX files to combine
        output_path (str): Path where the combined file will be saved
        options (dict): Additional options:
            - sheet_name: Specific sheet to read from each file
            - method: 'concat' or 'separate_sheets'
            - add_filename_column: Whether to add source filename column
            - remove_duplicates: Whether to remove duplicate rows
            - sort_by: Column name to sort the combined data by
    
    Returns:
        bool: True if successful, False otherwise
    """
    if options is None:
        options = {}
    
    sheet_name = options.get('sheet_name', None)
    method = options.get('method', 'concat')
    add_filename_column = options.get('add_filename_column', True)
    remove_duplicates = options.get('remove_duplicates', False)
    sort_by = options.get('sort_by', None)
    
    try:
        combined_data = []
        
        # Read and process each file
        for file_path in file_paths:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue
                
            try:
                logger.info(f"Reading: {os.path.basename(file_path)}")
                
                if sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                else:
                    df = pd.read_excel(file_path)
                
                if add_filename_column:
                    df['source_file'] = os.path.basename(file_path)
                
                combined_data.append(df)
                
            except Exception as e:
                logger.error(f"Error reading {file_path}: {str(e)}")
                continue
        
        if not combined_data:
            logger.error("No data was successfully read")
            return False
        
        # Combine data
        if method == 'concat':
            combined_df = pd.concat(combined_data, ignore_index=True, sort=False)
            
            # Remove duplicates if requested
            if remove_duplicates:
                original_rows = len(combined_df)
                combined_df = combined_df.drop_duplicates()
                logger.info(f"Removed {original_rows - len(combined_df)} duplicate rows")
            
            # Sort if requested
            if sort_by and sort_by in combined_df.columns:
                combined_df = combined_df.sort_values(sort_by)
                logger.info(f"Sorted by column: {sort_by}")
            
            # Save to Excel
            combined_df.to_excel(output_path, index=False)
            logger.info(f"Combined file saved: {output_path}")
            
        elif method == 'separate_sheets':
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for i, df in enumerate(combined_data):
                    sheet_name = f"Sheet_{i+1}"
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            logger.info(f"File with separate sheets saved: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in advanced combination: {str(e)}")
        return False

def main(file_path, output_path):
    """
    Main function to execute the file combination with the predefined paths.
    """
    logger.info("Starting XLSX file combination...")
    xlsx_path_file_list = os.listdir(file_path)
    xlsx_path_list = [os.path.join(file_path, file) for file in xlsx_path_file_list if file.lower().endswith('.xlsx')]


    # Method 1: Basic combination
    success = combine_xlsx_files(xlsx_path_list, output_path, method='concat')
    
    if success:
        logger.info("File combination completed successfully!")
    else:
        logger.error("File combination failed!")
    
if __name__ == "__main__":
    file_path = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v11\database\raw_data\0721_TillJune2"
    output_path = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v11\database\raw_data\0721_TillJune2\PDR23_June_DEU.xlsx"

    main(file_path, output_path)