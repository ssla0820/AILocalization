import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

from bs4 import BeautifulSoup
from collections import OrderedDict
import pandas as pd
import openpyxl
from openpyxl.styles import Alignment, Font
import glob
import logging
from datetime import datetime

# Import required functions from the main project
from pages.general_functions import get_text_group_inline, detect_file_encoding
from translate.translate import segment_groups_map, detect_file_type
from chat.openai_api_chat import OpenaiAPIChat
from config import translate_config as conf


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('segment_extraction.log'),
            logging.StreamHandler()
        ]
    )

def get_source_file_list(source_folder):
    """Get a list of all source files (XML and HTML) in the given folder."""
    if not os.path.exists(source_folder):
        logging.error(f"Source folder does not exist: {source_folder}")
        return []

    xml_files = glob.glob(os.path.join(source_folder, "*.xml"))
    html_files = glob.glob(os.path.join(source_folder, "*.html")) + glob.glob(os.path.join(source_folder, "*.htm"))
    
    return xml_files + html_files

def read_and_process_files(source_folder, source_file):
    """
    Read all XML and HTML files from the given folder path and process them
    like translate.py does.
    
    :param source_folder: Path to the folder containing XML and HTML files
    :param source_file: Name of the source file to process
    :return: Dictionary with processed segment data
    """
    try:
        file_path = os.path.join(source_folder, source_file)
        logging.info(f"Processing file: {file_path}")
        
        # Read file with encoding detection (same as translate.py)
        used_encoding, file_content = detect_file_encoding(file_path, "English")
        logging.info(f"Using {used_encoding} encoding for file: {os.path.basename(file_path)}")
        
        # Detect file type (same as translate.py)
        file_type, is_pomo_xml, is_xlsx = detect_file_type(file_content, file_path)
        logging.info(f"Detected file type: {file_type}, Is POMO XML: {is_pomo_xml}")
        
        # Skip XLSX files as they are handled differently
        if is_xlsx:
            logging.info(f"Skipping XLSX file: {file_path}")
            return {}
        
        # Parse with BeautifulSoup (same as translate.py)
        if file_type == 'html':
            soup = BeautifulSoup(file_content, 'html.parser')
        else:
            soup = BeautifulSoup(file_content, file_type)
        
        logging.info(f"Parsed soup, starting text group extraction...")
        
        # Extract text groups using get_text_group_inline (as requested)
        groups_map = get_text_group_inline(soup)
        logging.info(f"Extracted {len(groups_map)} text groups from {os.path.basename(file_path)}")
        
        if not groups_map:
            logging.warning(f"No text groups found in {file_path}")
            return {}
        
        logging.info(f"Starting segmentation...")
        
        # Segment the groups using segment_groups_map (as requested)
        groups_map_segments = segment_groups_map(
            groups_map,
            int(conf.N_INPUT_TOKEN),
            OpenaiAPIChat(conf.TRANSLATE_MODEL).n_tokens
        )
        logging.info(f"Created {len(groups_map_segments)} segments from {os.path.basename(file_path)}")
        
        # Convert segments to the format expected by save_to_excel
        groups_in = {}
        segment_counter = 0
        for segment in groups_map_segments:
            for k, v in segment.items():
                groups_in[k] = str(v).replace('\n', '')
                segment_counter += 1
        
        return groups_in

    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")

    return {}


def save_to_excel(output_folder, source_file, groups_in):
    """Save the segmented source text to Excel file"""
    # Create DataFrame with the correct structure
    data = {
        'ENU': list(groups_in.values()),  # Use values (the actual text) instead of keys
        'Refer_Text': [''] * len(groups_in),
        'Refer_Image': [''] * len(groups_in)
    }
    df = pd.DataFrame(data)

    # Extract just the filename without the full path
    file_name = os.path.splitext(os.path.basename(source_file))[0]

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_file = os.path.join(output_folder, f"{file_name}_segmented.xlsx")
    df.to_excel(output_file, index=False)
    logging.info(f"Saved segmented data to Excel: {output_file}")


def main(source_folder, output_folder):
    """
    Main function to process files and save segmented source text.
    """
    setup_logging()

    if not source_folder:
        logging.error("No source folder path provided")
        return

    logging.info(f"Starting segmentation process...")
    logging.info(f"Input folder: {source_folder}")
    logging.info(f"Output folder: {output_folder}")
    
    source_file_list = get_source_file_list(source_folder)

    if not source_file_list:
        logging.error("No source files found")
        return
    
    for source_file_path in source_file_list:
        source_file = os.path.basename(source_file_path)
        logging.info(f"Processing file: {source_file}")
        groups_in = read_and_process_files(source_folder, source_file)

        # logging.info(f"Extracted {len(groups_in)} segments from {source_file}")
        logging.info(f"Segment details: {groups_in}")

        if not groups_in:
            logging.warning(f"No valid groups found for file: {source_file}")
            continue

        save_to_excel(output_folder, source_file, groups_in)


    logging.info("Segmentation process completed successfully!")


if __name__ == '__main__':
    source_folder = r'E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\0731_Source\test'
    output_folder = r'E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\0731_Source'
    main(source_folder=source_folder, output_folder=output_folder)
