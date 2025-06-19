import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from bs4 import BeautifulSoup, Tag, NavigableString, Doctype, Comment
from dataclasses import dataclass
from collections import OrderedDict
import json
import re
import pandas as pd
from config import translate_config as conf
import logging

@dataclass
class InlineGroup:
    """
    A group of adjacent inline elements extracted from a BeautifulSoup soup object.
    """
    text_shreds: list[NavigableString]
    cids: list[int]
    elements: list[Tag]

    def __post_init__(self):
        assert len(self.text_shreds) == len(self.cids) == len(self.elements)

    def __str__(self):
        return ''.join(self.text_shreds)

    def __len__(self):
        return len(self.text_shreds)



def is_inline_ele(ele: Tag):
    """check if an element is inline or not."""
    return True if ele.name in \
                   {'a', 'abbr', 'acronym', 'b',
                    'bdo', 'big', 'br', 'button',
                    'cite', 'code', 'dfn', 'em', 'i',
                    'img', 'input', 'kbd', 'label',
                    'map', 'object', 'output', 'q',
                    'samp', 'script', 'select', 'small',
                    'span', 'strong', 'sub', 'sup',
                    'textarea', 'time', 'tt', 'var',
                    'text', 'link'} else False

def get_text_group_inline(
        element: Tag
) -> OrderedDict[str, InlineGroup]:
    """
    Extracts and groups adjacent inline elements from a BeautifulSoup soup object,
    based on the inductive bias that adjacent inline elements tend to form complete sentences.
    :param element: BeautifulSoup Tag object representing the root element to extract inline elements from
    :return: OrderedDict containing grouped inline elements
    """

    all_groups = []
    cnt = 0
    ignore_char_set = {
        '\n', '\xa0'
    }

    def traversal(ele: Tag):
        nonlocal cnt, all_groups
        group = []
        inline = is_inline_ele(ele)
        for cid, c in enumerate(ele.contents):
            if isinstance(c, (Doctype, Comment)) or c.name == 'script':
                continue
            elif isinstance(c, NavigableString) and not set(c).issubset(ignore_char_set):
                group.append([c.replace('\n', ''), cid, ele, cnt])
                cnt += 1
            elif isinstance(c, Tag):
                sub_shreds = traversal(c)
                if sub_shreds is not None:  # non-None return indicates inline child tag
                    group += sub_shreds
                elif (not inline) and group:
                    all_groups.append(group)
                    group = []
        if not inline:
            if group:
                all_groups.append(group)
            return None
        else:
            return group

    traversal(element)
    all_groups.sort(key=lambda x: x[0][3])
    groups_map = OrderedDict({})
    for i, g in enumerate(all_groups):
        groups_map[str(i)] = InlineGroup(
            [item[0] for item in g],
            [item[1] for item in g],
            [item[2] for item in g]
        )
    return groups_map



def as_json_obj(raw_string):
    """
    Extract and parse JSON from a string, with improved error handling and formatting fixes.
    
    Args:
        raw_string (str): The raw string containing JSON data
        
    Returns:
        dict: Parsed JSON object or None if parsing fails
    """
    if not raw_string:
        logging.warning("Empty string provided to as_json_obj")
        return None
    
    # Attempt to find JSON content using more precise regex patterns
    try:
        # Try to find a JSON object between { and } including all nested structures
        json_pattern = r'(\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\})'
        matches = re.findall(json_pattern, raw_string, re.DOTALL)
        
        if matches:
            # Try each match until we find a valid JSON
            for potential_json in matches:
                # Fix common JSON formatting issues
                fixed_json = potential_json
                # Fix trailing commas which are invalid in JSON
                fixed_json = re.sub(r',\s*}', '}', fixed_json)
                fixed_json = re.sub(r',\s*]', ']', fixed_json)
                # Fix single quotes to double quotes
                fixed_json = re.sub(r'\'([^\']+)\':', r'"\1":', fixed_json)
                fixed_json = re.sub(r': \'([^\']*)\'', r': "\1"', fixed_json)
                
                try:
                    return json.loads(fixed_json)
                except json.JSONDecodeError as e:
                    logging.debug(f"Failed to parse JSON match: {e}")
                    continue
        
        # If no matches found with regex or all matches failed to parse,
        # try to parse the entire string as JSON (it might be a clean JSON already)
        try:
            return json.loads(raw_string)
        except json.JSONDecodeError:
            # Last resort: try to fix and parse the entire string
            # Replace single quotes with double quotes for JSON keys and string values
            fixed_string = re.sub(r'\'([^\']+)\':', r'"\1":', raw_string)
            fixed_string = re.sub(r': \'([^\']*)\'', r': "\1"', fixed_string)
            fixed_string = re.sub(r',\s*}', '}', fixed_string)
            fixed_string = re.sub(r',\s*]', ']', fixed_string)
            
            try:
                return json.loads(fixed_string)
            except json.JSONDecodeError as e:
                logging.warning(f"All attempts to parse JSON failed: {e}")
                
    except Exception as e:
        logging.error(f"Unexpected error in as_json_obj: {e}")
    
    return None


def clean_text(text: str) -> str:
    """
    Remove all unexpected characters from the text. Like %S, %d, etc.
    :param text: The text to be cleaned
    :return: Cleaned text
    """

    special_cases = {
                        0: ("&quot;", '"'), 
                        1: (" &lt; ", " < "), 
                        2: (" &gt; ", " > "), 
                        3: (" &amp; ", " & "), 
                        4: (" &amp;amp; ", " & "),
                        # 5: ("[%][a-zA-Z]", " "),
                        6: ("\\n", ""),
                        7: ("\\r", ""),
                        8: ("\\t", ""),
                        9: ("\n", ""),
                        10: ("\r", ""),
                        11: ("\t", ""),
                        12: ("\\", ""),
                    }
    
    for index, value in special_cases.items():
        if value[0] in text:
            text = text.replace(value[0], value[1])
    return text.strip()


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


def get_relevant_region_table(region_table, source_text):
    """
    Identify relevant region table entries in the current segment.
    :param region_table: Dictionary of region table entries
    :param source_text: Source text content
    :return: Dictionary of relevant region table entries
    """
    relevant_mapping_table = {}
    if region_table:
        for source_term, target_term in region_table.items():
            # Deal with special cases
            special_cases = {0: ("&quot;", '"'), 1: (" &lt; ", " < "), 2: (" &gt; ", " > "), 3: (" &amp; ", " & "), 4: (" &amp;amp; ", " & "),
                             5: ("&apos;", "'")}
            
            source_term_special = None
            for index, value in special_cases.items():
                if value[1] in source_term:
                    source_term_special = source_term.replace(value[1], value[0])

            if source_term.lower() in source_text.lower() or\
                  (source_term_special and source_term_special.lower() in source_text.lower()):
                relevant_mapping_table[source_term] = target_term
                if source_term_special:
                    relevant_mapping_table[source_term_special] = target_term

            if " ... " in source_term:
                source_term_list = source_term.split(" ... ")
                # if all items in source_term_list are in source_text, add the whole source_term
                if all(item.lower() in source_text.lower() for item in source_term_list):
                    relevant_mapping_table[source_term] = target_term
 
            if source_term_special and " ... " in source_term_special:
                source_term_list = source_term_special.split(" ... ")
                # if all items in source_term_list are in source_text, add the whole source_term_special
                if all(item.lower() in source_text.lower() for item in source_term_list):
                    relevant_mapping_table[source_term_special] = target_term

    if relevant_mapping_table:
        print(f"Source text '{source_text}'': Found {len(relevant_mapping_table)} relevant region table")
        print(f'Relevant region table: {relevant_mapping_table}')
    return relevant_mapping_table
    

def get_relevant_refer_text_table(refer_text_table, source_text):
    """
    Identify relevant refer text entries in the current segment.
    :param refer_text_table: Dictionary of refer text entries
    :param source_text: Source text content
    :return: Dictionary of relevant refer text entries
    """
    print(f"the table is {refer_text_table}")

    relevant_refer_text_table = {}
    if refer_text_table:
        for source_term, target_term in refer_text_table.items():
            print(f"Source term: {source_term}, Target term: {target_term}")
            if source_term.lower() == source_text.lower():
                relevant_refer_text_table[source_term] = target_term

    if relevant_refer_text_table:
        print(f"Source text '{source_text}'': Found {len(relevant_refer_text_table)} relevant refer text table")
        print(f'Relevant refer text table: {relevant_refer_text_table}')
    return relevant_refer_text_table

    
def load_specific_names(excel_path, source_lang, target_lang):
    """
    Load specific name translations from an Excel file based on the configured source and target languages.
    The Excel should have columns with language codes (ENU, CHT, CHS, etc.).
    Extracts only the translation pair corresponding to SOURCE_LANGUAGE and TARGET_LANGUAGE.
    
    :param excel_path: Path to the Excel file containing specific names
    :return: Dictionary mapping source language terms to target language terms
    """
    specific_names = {}
    if not os.path.exists(excel_path):
        print(f"Warning: Excel file '{excel_path}' does not exist.")
        return specific_names
    
    # Use language_map from config
    source_col_name = conf.LANGUAGE_MAP.get(source_lang, source_lang)
    target_col_name = conf.LANGUAGE_MAP.get(target_lang, target_lang)
    
    print(f"Looking for source column: '{source_col_name}', target column: '{target_col_name}'")
    
    try:
        # Read the Excel file
        df = pd.read_excel(excel_path)
        
        # Find the appropriate columns
        source_col = None
        target_col = None
        
        for col in df.columns:
            if col.upper() == source_col_name.upper():
                source_col = col
            elif col.upper() == target_col_name.upper():
                target_col = col
        
        if source_col is None or target_col is None:
            print(f"Warning: Could not find columns for {source_col_name} and/or {target_col_name} in Excel file.")
            print(f"Available columns: {', '.join(df.columns)}")
            return specific_names
        
        # Create a dictionary from the dataframe using only the source and target columns
        for _, row in df.iterrows():
            source_term = str(row[source_col]).strip()
            target_term = str(row[target_col]).strip()
            
            # Skip empty or nan values
            if source_term and target_term and source_term.lower() != 'nan' and target_term.lower() != 'nan':
                specific_names[source_term] = target_term
                
        print(f"Successfully loaded '{excel_path}' with {len(specific_names)} specific name translations for {source_col_name}->{target_col_name}.")
    except Exception as e:
        print(f"Error loading Excel file '{excel_path}': {e}")
    
    return specific_names

def load_region_table(excel_path, source_lang):
    """
    :param excel_path: Path to the Excel file containing specific names
    :return: Dictionary mapping source language terms to target language terms
    """

    print(f"Loading region table from '{excel_path}' for source language '{source_lang}'")
    region_table = {}
    if not os.path.exists(excel_path):
        print(f"Warning: Excel file '{excel_path}' does not exist.")
        return region_table
    
    # Use language_map from config
    source_col_name = conf.LANGUAGE_MAP.get(source_lang, source_lang)
    use_col_name = conf.LANGUAGE_MAP.get('Use', 'Use')
    avoid_col_name = conf.LANGUAGE_MAP.get('Avoid', 'Avoid')
    
    print(f"Looking for source column: '{source_col_name}', use column: '{use_col_name}', avoid column: '{avoid_col_name}'")

    try:
        # Read the Excel file
        df = pd.read_excel(excel_path)
        
        # Find the appropriate columns
        source_col = None
        use_col = None
        avoid_col = None
        
        for col in df.columns:
            if col.upper() == source_col_name.upper():
                source_col = col
            elif col.upper() == use_col_name.upper():
                use_col = col
            elif col.upper() == avoid_col_name.upper():
                avoid_col = col
        
        if source_col is None or use_col is None or avoid_col is None:
            print(f"Warning: Could not find columns for {source_col_name} and/or {use_col} and/or {avoid_col} in Excel file.")
            print(f"Available columns: {', '.join(df.columns)}")
            return region_table
        
        # Create a dictionary from the dataframe using only the source and target columns
        for _, row in df.iterrows():
            source_term = str(row[source_col]).strip()
            use_term = str(row[use_col]).strip()
            avoid_term = str(row[avoid_col]).strip()
            
            # Skip empty or nan values
            if source_term and use_term  and avoid_term\
                and source_term.lower() != 'nan' and use_term.lower() != 'nan' and avoid_term.lower() != 'nan':
                region_table[source_term] = (use_term, avoid_term)
                
        print(f"Successfully loaded '{excel_path}' with {len(region_table)} specific name translations for {source_col_name}-> ({use_term}, {avoid_term}).")
    except Exception as e:
        print(f"Error loading Excel file '{excel_path}': {e}")
    
    return region_table

def load_refer_text_table(excel_path, source_lang):
    """
    :param excel_path: Path to the Excel file containing specific names
    :return: Dictionary mapping source language terms to target language terms
    """
    refer_text_table = {}
    if not os.path.exists(excel_path):
        print(f"Warning: Excel file '{excel_path}' does not exist.")
        return refer_text_table
    
    # Use language_map from config
    source_col_name = conf.LANGUAGE_MAP.get(source_lang, source_lang)
    refer_col_name = conf.LANGUAGE_MAP.get("Refer", "Refer")
    
    print(f"Looking for source column: '{source_col_name}', refer column: '{refer_col_name}'")
    
    try:
        # Read the Excel file
        df = pd.read_excel(excel_path)
        
        # Find the appropriate columns
        source_col = None
        refer_col = None
        
        for col in df.columns:
            if col.upper() == source_col_name.upper():
                source_col = col
            elif col.upper() == refer_col_name.upper():
                refer_col = col
        
        if source_col is None or refer_col is None:
            print(f"Warning: Could not find columns for {source_col_name} and/or {refer_col_name} in Excel file.")
            print(f"Available columns: {', '.join(df.columns)}")
            return refer_text_table
        
        # Create a dictionary from the dataframe using only the source and refer columns
        for _, row in df.iterrows():
            source_term = str(row[source_col]).strip()
            refer_term = str(row[refer_col]).strip()
            
            # Skip empty or nan values
            if source_term and refer_term and source_term.lower() != 'nan' and refer_term.lower() != 'nan':
                refer_text_table[source_term] = refer_term
                
        print(f"Successfully loaded '{excel_path}' with {len(refer_text_table)} specific name translations for {source_col_name}->{refer_col_name}.")
    except Exception as e:
        print(f"Error loading Excel file '{excel_path}': {e}")
    
    return refer_text_table

def get_language_preferred_encodings(language_code=None):
    """
    Returns a list of preferred encodings to try for a given language.
    
    :param language_code: ISO language code or None for default encodings
    :return: List of encoding names to try
    """
    # Default encoding list to try
    default_encodings = ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'iso-8859-1', 'cp1252']
    
    # Language-specific encoding preferences 
    language_encodings = {
        'zh': ['utf-8', 'utf-16', 'gb18030', 'gbk', 'gb2312'],  # Chinese
        'ja': ['utf-8', 'utf-16', 'shift-jis', 'euc-jp', 'iso-2022-jp'],  # Japanese
        'ko': ['utf-8', 'utf-16', 'euc-kr', 'cp949'],  # Korean
        'ru': ['utf-8', 'utf-16', 'koi8-r', 'windows-1251', 'iso-8859-5'],  # Russian
        'de': ['utf-8', 'utf-16', 'iso-8859-1', 'cp1252'],  # German
        'fr': ['utf-8', 'utf-16', 'iso-8859-1', 'cp1252'],  # French
    }
    
    # If a language code is provided and exists in our mapping, use that
    if language_code and language_code.lower()[:2] in language_encodings:
        return language_encodings[language_code.lower()[:2]]
    
    # Otherwise return default encodings
    return default_encodings


def detect_file_encoding(file_path, language_code=None):
    """
    Attempt to detect and use the correct encoding for a file.
    Tries multiple encodings based on language preference.
    
    :param file_path: Path to the file to read
    :param language_code: Optional language code to prioritize encodings
    :return: tuple of (encoding_used, file_content)
    """
    # Get preferred encodings list based on language
    encodings_to_try = get_language_preferred_encodings(language_code)
    
    # Try each encoding until one works
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                print(f"Successfully read file using {encoding} encoding")
                return encoding, content
        except UnicodeDecodeError:
            continue
    
    # If we get here, none of the encodings worked
    raise ValueError(f"Could not decode {file_path} with any of the supported encodings: {encodings_to_try}")

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