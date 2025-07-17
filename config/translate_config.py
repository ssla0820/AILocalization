LANGUAGE_MAP = {
    # 'Full Language Name to provide to LLM': 'Language that on Mapping Table row title (specific_name.xlsx)'
    'English': 'ENU',
    'Traditional Chinese': 'CHT',
    'Simplified Chinese': 'CHS',
    'German': 'DEU',
    'French': 'FRA',
    'Spanish': 'ESP',
    'Japanese': 'JPN',
    'Korean': 'KOR',
    'Italian': 'ITA',
    'Dutch': 'NLD',
    'Portuguese (Brazil)': 'PTB',
    'Russian': 'RUS',
    'Hindi': 'HIN',
    'Indonesian': 'IND',
    'Malay': 'MSL',
    'Thai': 'THA',
}

# Multi-language option definitions
MULTI_LANGUAGE_OPTIONS = {
    '5L': ['German', 'Spanish', 'French', 'Italian', 'Korean'],
    '9L': ['Traditional Chinese', 'Simplified Chinese', 'German', 'French', 
           'Spanish', 'Japanese', 'Korean', 'Italian'],
    '11L': ['Traditional Chinese', 'Simplified Chinese', 'German', 'French', 
           'Spanish', 'Japanese', 'Korean', 'Italian', 'Dutch', 'Portuguese (Brazil)'],
    '15L': ['Traditional Chinese', 'Simplified Chinese', 'German', 'French',
              'Spanish', 'Japanese', 'Korean', 'Italian', 'Dutch', 'Portuguese (Brazil)', 
              'Russian', 'Hindi', 'Indonesian', 'Malay', 'Thai'],
}

SOFTWARE_TYPE_MAP = {
    'PDR': 'Video Editing Software',
    'PHD': 'Image Editing Software',
}

# TRANSLATE_MODEL = 'gpt-4o'
TRANSLATE_MODEL = 'o3-2025-04-16'
# COMPARISON_MODEL = ['gpt-4o', 'gemini-pro-vision']  # Models used for translation and comparison

COMPARISON_MODEL = ['o3-2025-04-16', 'gemini-2.0-flash']

# COMPARISON_MODEL = ['gpt-4o']
N_INPUT_TOKEN = 4096 * 0.4
RESTRUCT_MODEL = 'gpt-4o'

# LLM response parameters
TEMPERATURE = 0.0
SEED = 42

CHECK_VERIFICATION = True  # Set to True to run verification after translation
CHECK_GROUND_TRUTH = True  # Set to True to check the ground truth
GROUND_TRUTH_EXCEL_PATH = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v6\ground_truth.xlsx"  # Path to the ground truth Excel file

# ========= Information for [Run Batch] (Batch Files)==========
BATCH_EXCEL_PATH = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v11\translate_files.xlsx"  # Default Excel file for batch processing
# ========= Information for [Run Batch] (Batch Files)==========

# ========= Information for [Run Program] (Single File)==========
SOURCE_LANGUAGE = 'English' # Provide the source language of the file to be translated
TARGET_LANGUAGE = 'Italian' # Provide the target language for translation, e.g., 'Traditional Chinese', 'Simplified Chinese', etc.
# NOTE: The language names should be consistent with the ones used in the language_map.

SOFTWARE_TYPE = 'video editing software'  # Type of software being translated (e.g., 'video editing software', 'image editing software', etc.)
# SOFTWARE_TYPE = 'image editing software'
SOURCE_TYPE = 'UI' # Type of source file (e.g., 'UI', 'Help', etc.)
# SPECIFIC_NAMES_XLSX = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\Mapping_Table\PHD 16.5 UI_4L_20250527.xlsx" # The path of mapping table
SPECIFIC_NAMES_XLSX = r"e:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\Mapping_Table\specific_name_pdr365_short.xlsx" # The path of mapping table
REGION_TABLE_PATH = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v11\region_table\region_table.xlsx"
REFER_TEXT_TABLE_PATH = r""


# Input and output file paths
INPUT_FILE_PATH = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\0526_Source\0526_Batch1n2n3_ProblemTest_ITA_PDR.xlsx" # Path to the original file
OUTPUT_FILE_PATH = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\0526_Source\0526_Batch1n2n3_ProblemTest_ITA_PDR_Result.xlsx" # Path to save the translated file
COMPARE_FILE_PATH = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\Sources_CHT\0520_Batch1n2_CHT_PHD.xlsx"# Path to save the comparison file, please leave as html format
IMAGE_PATH = r""
DATABASE_PATH = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v10\database\PDR_enu_ita_database.json"  # Path to the database folder
REVIEW_REPORT_PATH = r""
# ========= Information for [Run Program] (Single File)==========