#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TMX to Excel Converter

This script converts TMX (Translation Memory eXchange) files to Excel (XLSX) format,
supporting multiple languages.

Usage:
    python tmx_csv_convertor.py <input_tmx_file> <output_xlsx_file> <source_lang> <target_lang>

Example:
    python tmx_csv_convertor.py input.tmx output.xlsx en zh-TW
"""

import argparse
import csv
import os
import sys
import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Tuple, Optional

try:
    import openpyxl
    from openpyxl import Workbook
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    print("WARNING: openpyxl is not installed. Excel export will not be available.")
    print("To enable Excel export, install openpyxl using: pip install openpyxl")


# Language code mappings
LANGUAGE_CODES = {
    'English': 'en',
    'Traditional Chinese': 'zh-TW',
    'Simplified Chinese': 'zh-CN',
    'German': 'de',
    'French': 'fr',
    'Spanish': 'es',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Italian': 'it',
    'Dutch': 'nl',
    'Portuguese (Brazil)': 'pt-BR',
    'Russian': 'ru',
    'Hindi': 'hi',
    'Indonesian': 'id',
    'Malay': 'ms',
    'Thai': 'th'
}

# Reverse mapping for looking up by code
LANGUAGE_NAMES = {code: name for name, code in LANGUAGE_CODES.items()}


def parse_tmx(tmx_file: str) -> List[Dict[str, str]]:
    """
    Parse a TMX file and extract translation units.
    
    Args:
        tmx_file: Path to the TMX file
        
    Returns:
        List of dictionaries containing translation segments keyed by language code
    """
    try:
        # Parse the TMX file
        tree = ET.parse(tmx_file)
        root = tree.getroot()
        
        # Register XML namespace
        ET.register_namespace('xml', 'http://www.w3.org/XML/1998/namespace')
        
        # Debug info
        print(f"Processing TMX file: {tmx_file}")
        print(f"Root tag: {root.tag}")
        
        # Find the body element which contains translation units
        body = root.find('body') or root.find('.//body')
        if body is None:
            print("WARNING: No 'body' element found in TMX file")
            # Try to find translation units directly in the root
            tu_elements = root.findall('.//tu')
        else:
            print(f"Found 'body' element with {len(list(body))} children")
            # Find translation units in the body
            tu_elements = body.findall('.//tu')
        
        print(f"Found {len(tu_elements)} translation units")
        
        # Process each translation unit
        translation_units = []
        
        for tu in tu_elements:
            segments = {}
            
            # Process each tuv (translation unit variant)
            tuv_elements = tu.findall('.//tuv')
            
            for tuv in tuv_elements:
                # Get language code - try both with and without namespace
                xml_lang = None
                for attr_name in ['{http://www.w3.org/XML/1998/namespace}lang', 'xml:lang', 'lang']:
                    try:
                        xml_lang = tuv.get(attr_name)
                        if xml_lang:
                            print(f"Found language code using {attr_name}: {xml_lang}")
                            break
                    except Exception as e:
                        print(f"Error getting attribute {attr_name}: {e}")
                        continue
                if not xml_lang:
                    print("WARNING: No language code found for TUV element")
                    continue
                
                # Normalize language code
                lang_code = normalize_language_code(xml_lang)
                print(f"Normalized language code: {xml_lang} -> {lang_code}")
                
                # Extract segment text
                seg_elements = tuv.findall('.//seg')
                if seg_elements:
                    seg = seg_elements[0]
                    # Get the text, joining all text content if there are sub-elements
                    raw_text = ''.join(seg.itertext()).strip()
                    
                    # Clean the text by removing tags and markup
                    cleaned_text = clean_text(raw_text)
                    
                    # Store the cleaned text
                    segments[lang_code] = cleaned_text
                    
                    # Only show a preview of the text to keep logs manageable
                    preview_len = 30
                    if len(cleaned_text) > preview_len:
                        print(f"Found text for {lang_code}: {cleaned_text[:preview_len]}...")
                    else:
                        print(f"Found text for {lang_code}: {cleaned_text}")
            if segments:
                translation_units.append(segments)
                print(f"Added translation unit with languages: {list(segments.keys())}")
        
        print(f"Extracted {len(translation_units)} translation pairs")
        
        # Check if we found any translation units
        if not translation_units:
            print("WARNING: No translation pairs were extracted.")
        
        return translation_units
    
    except ET.ParseError as e:
        print(f"Error parsing TMX file: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error processing TMX file: {e}")
        import traceback
        traceback.print_exc()
        return []


def normalize_language_code(code: str) -> str:
    """
    Normalize language codes to a standard format.
    
    Args:
        code: Language code from TMX file
        
    Returns:
        Normalized language code
    """
    if not code:
        return ""
    
    # Debug output to see what's coming in
    print(f"Original language code: '{code}'")
      # Special handling for codes in your specific TMX file
    if code == "EN-US":
        print(f"  Converting {code} -> en")
        return "en"
    elif code == "ZH-CN":
        print(f"  Converting {code} -> zh-CN")
        return "zh-CN"
    elif code == "ZH-TW":
        print(f"  Converting {code} -> zh-TW")
        return "zh-TW"
    elif code == "ES-ES":
        print(f"  Converting {code} -> es")
        return "es"
    
    # Convert to lowercase for consistent processing
    code_lower = code.lower()
      # Handle common variations
    mapping = {
        'zh-hans': 'zh-CN',
        'zh-hant': 'zh-TW',
        'zh_tw': 'zh-TW',
        'zh_cn': 'zh-CN',
        'zh_hk': 'zh-TW',  # Group Hong Kong with Traditional Chinese
        'zh-chs': 'zh-CN',  # Simplified Chinese
        'zh-cht': 'zh-TW',  # Traditional Chinese
        'zh': 'zh-CN',      # Default Chinese to Simplified
        'en-us': 'en',      # US English
        'en-gb': 'en',      # British English
        'pt_br': 'pt-BR',
        'pt-pt': 'pt',
        'es-es': 'es',      # Spanish (Spain)
        'es-mx': 'es',      # Spanish (Mexico)
        'es-419': 'es',     # Spanish (Latin America)
        'es_es': 'es',      # Spanish with underscore
        'spa': 'es',        # ISO 639-2 code for Spanish
    }
    
    # Check if the code exists in our mapping
    if code_lower in mapping:
        mapped_code = mapping[code_lower]
        print(f"  Mapping {code} -> {mapped_code}")
        return mapped_code
      # Replace underscores with hyphens for consistency
    normalized_code = code.replace('_', '-')
    
    # Extract the base language code from language-COUNTRY format (e.g., es-ES → es)
    if '-' in normalized_code and len(normalized_code) >= 4:
        parts = normalized_code.split('-', 1)
        base_lang = parts[0].lower()
        
        # Check if this is a known language code
        for lang_code in LANGUAGE_CODES.values():
            if lang_code == base_lang or lang_code.startswith(base_lang + '-'):
                print(f"  Auto-converting {code} → {base_lang}")
                return base_lang
    
    # Return the code as is for unknown codes
    print(f"  Keeping as is: {normalized_code}")
    return normalized_code


def export_to_csv(translation_units: List[Dict[str, str]], 
                 csv_file: str, 
                 source_lang: str, 
                 target_lang: str) -> None:
    """
    Export translation units to CSV file.
    
    Args:
        translation_units: List of dictionaries containing translations
        csv_file: Output CSV file path
        source_lang: Source language code
        target_lang: Target language code
    """
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header - using language names
            source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
            target_name = LANGUAGE_NAMES.get(target_lang, target_lang)
            writer.writerow([source_name, target_name])
            
            # Write translation pairs
            count = 0
            for unit in translation_units:
                if source_lang in unit and target_lang in unit:
                    writer.writerow([unit[source_lang], unit[target_lang]])
                    count += 1
            
            print(f"Exported {count} translation pairs to {csv_file}")
    
    except IOError as e:
        print(f"Error writing to CSV file: {e}")
    except Exception as e:
        print(f"Unexpected error exporting to CSV: {e}")


def export_to_excel(translation_units: List[Dict[str, str]], 
                   excel_file: str, 
                   source_lang: str, 
                   target_lang: str) -> None:
    """
    Export translation units to Excel file.
    
    Args:
        translation_units: List of dictionaries containing translations
        excel_file: Output Excel file path
        source_lang: Source language code
        target_lang: Target language code
    """
    if not EXCEL_AVAILABLE:
        print("ERROR: Excel export is not available. Please install openpyxl with 'pip install openpyxl'")
        return
    
    try:
        # Create a new workbook and select the active worksheet
        wb = Workbook()
        ws = wb.active
        
        # Write header - using language names
        source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
        target_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        ws.append([source_name, target_name])
        
        # Write translation pairs
        count = 0
        for unit in translation_units:
            if source_lang in unit and target_lang in unit:
                ws.append([unit[source_lang], unit[target_lang]])
                count += 1
        
        # Save the workbook to the specified file
        wb.save(excel_file)
        print(f"Exported {count} translation pairs to {excel_file}")
    
    except IOError as e:
        print(f"Error writing to Excel file: {e}")
    except Exception as e:
        print(f"Unexpected error exporting to Excel: {e}")
        import traceback
        traceback.print_exc()


def get_available_languages(translation_units: List[Dict[str, str]]) -> List[str]:
    """
    Get a list of available languages in the TMX file.
    
    Args:
        translation_units: List of dictionaries containing translations
        
    Returns:
        List of language codes found in the TMX file
    """
    languages = set()
    for unit in translation_units:
        languages.update(unit.keys())
    
    return sorted(list(languages))


def debug_tmx_structure(tmx_file: str) -> None:
    """
    Analyze the TMX file structure and print detailed debug information.
    
    Args:
        tmx_file: Path to the TMX file
    """
    try:
        print("\n-------- TMX FILE DEBUG INFO --------")
        tree = ET.parse(tmx_file)
        root = tree.getroot()
        
        print(f"Root element: {root.tag}")
        
        # Check for body element
        body = root.find('body')
        if body is not None:
            print(f"Found body element with {len(list(body))} children")
        else:
            print("No body element found")
            
        # Check for tu elements
        tu_elements = root.findall('.//tu')
        print(f"Found {len(tu_elements)} tu elements")
        
        if tu_elements:
            # Analyze the first tu element
            first_tu = tu_elements[0]
            print(f"\nFirst TU element attributes: {first_tu.attrib}")
            
            # Find tuv elements inside the first tu
            tuv_elements = first_tu.findall('.//tuv')
            print(f"Found {len(tuv_elements)} tuv elements in first tu")
            
            for i, tuv in enumerate(tuv_elements):
                lang_attr = None
                # Try different attribute formats
                for attr in ['xml:lang', '{http://www.w3.org/XML/1998/namespace}lang', 'lang']:
                    if attr in tuv.attrib:
                        lang_attr = tuv.attrib[attr]
                        break
                
                print(f"TUV {i+1} language attribute: {lang_attr}")
                print(f"TUV {i+1} all attributes: {tuv.attrib}")
                
                # Check for seg elements
                seg_elements = tuv.findall('.//seg')
                if seg_elements:
                    seg_text = ''.join(seg_elements[0].itertext()).strip()
                    print(f"SEG text: {seg_text[:50]}..." if len(seg_text) > 50 else f"SEG text: {seg_text}")
        
        print("-------- END TMX DEBUG INFO --------\n")
    except Exception as e:
        print(f"Error debugging TMX file: {e}")
        import traceback
        traceback.print_exc()


def clean_text(text: str) -> str:
    """
    Clean text by removing HTML tags, special markup, and other non-text elements.
    
    Args:
        text: The text to clean
        
    Returns:
        Cleaned text with only words and basic punctuation
    """
    # Keep original for debugging
    original_text = text
    
    # Remove HTML tags (like <strong>, <a>, <br>, etc.) more aggressively
    # This uses a non-greedy pattern to handle nested tags
    text = re.sub(r'<.*?>', '', text)
    
    # Remove special markup like {\cs6\f1\cf6\lang1024 } that appears in the TMX file
    text = re.sub(r'{\\[^}]+}', '', text)
    
    # Remove \ut markup including their content
    text = re.sub(r'<ut>.*?</ut>', '', text)
    
    # Remove RTF formatting codes
    text = re.sub(r'\\[a-zA-Z0-9]+', '', text)
    
    # Handle common escaped HTML entities (extended list)
    html_entities = {
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&amp;': '&',
        '&apos;': "'",
        '&nbsp;': ' ',
        '&copy;': '©',
        '&reg;': '®',
        '&trade;': '™',
        '&bull;': '•',
        '&mdash;': '—',
        '&ndash;': '–',
        '&lsquo;': ''',
        '&rsquo;': ''',
        '&ldquo;': '"',
        '&rdquo;': '"',
    }
    
    for entity, replacement in html_entities.items():
        text = text.replace(entity, replacement)
    
    # Handle numeric HTML entities (like &#39; for apostrophe)
    text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
    text = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), text)
    
    # Fix special character sequences
    text = re.sub(r'\\&apos;([a-z0-9]{2})\\&apos;', lambda m: chr(int(m.group(1), 16)), text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Trim whitespace
    cleaned_text = text.strip()
    
    # Debug output if there was significant cleaning
    if len(original_text) > len(cleaned_text) * 1.5:  # If at least 33% was removed
        print(f"Text cleaning - Original ({len(original_text)} chars): {original_text[:50]}..." if len(original_text) > 50 else f"Original: {original_text}")
        print(f"Text cleaning - Cleaned ({len(cleaned_text)} chars): {cleaned_text[:50]}..." if len(cleaned_text) > 50 else f"Cleaned: {cleaned_text}")
    
    return cleaned_text


def main():
    # Local parameters instead of command-line arguments
    input_file = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v10\database\PDR FAQ_ITA.tmx" # Path to the TMX file in your workspace
    output_file = r"e:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v10\database\PDR FAQ_ITA_result.xlsx"  # Output Excel file path
    source_lang_name = "English"  # Source language name
    target_lang_name = "Italian"  # Target language name (e.g., 'Traditional Chinese')
    
    # Check if input file exists
    if not os.path.isfile(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    # Debug the TMX file structure first
    print("\nAnalyzing TMX file structure...")
    debug_tmx_structure(input_file)
    
    # Parse the TMX file
    translation_units = parse_tmx(input_file)
    
    # Always print available languages for debugging
    languages = get_available_languages(translation_units)
    print("\nAvailable languages in the TMX file:")
    for lang in languages:
        lang_name = LANGUAGE_NAMES.get(lang, f"Unknown ({lang})")
        print(f"  {lang}: {lang_name}")
    
    if not translation_units:
        print("No translation units found in the TMX file")
        sys.exit(1)
    
    # Convert source language name to code
    source_lang = LANGUAGE_CODES.get(source_lang_name)
    if not source_lang:
        print(f"Error: Source language '{source_lang_name}' not supported")
        sys.exit(1)
    
    # Convert target language name to code
    target_lang = LANGUAGE_CODES.get(target_lang_name)
    if not target_lang:
        print(f"Error: Target language '{target_lang_name}' not supported")
        sys.exit(1)
    
    print(f"Processing {source_lang_name} -> {target_lang_name}...")
    print(f"Using source language code: {source_lang}")
    print(f"Using target language code: {target_lang}")
    
    # Export to Excel
    export_to_excel(translation_units, output_file, source_lang, target_lang)
    
    print("Processing complete.")


if __name__ == "__main__":
    main()