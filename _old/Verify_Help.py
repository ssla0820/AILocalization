import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
import asyncio
import pandas as pd
from translate.translate import main as translate_main
from verify import main as verify_main
from groundtruth_check.GroundTruth_Check import main as groundtruth_main
from config import translate_config
import logging
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from config import translate_config as conf



file_list = [
    ("01.00.00_Introduction.xml", "01.00.00_Introduction_Spanish_01.xml"),
    ("01.01.00_Latest_Features.xml", "01.01.00_Latest_Features_Spanish_01.xml"),
    ("01.02.00_Whats_Different.xml", "01.02.00_Whats_Different_Spanish_01.xml"),
    ("03.03.03_GenAI_Room.xml", "03.03.03_GenAI_Room_Spanish_01.xml"),
    ("05.02.01_AI_Video_Generator.xml", "05.02.01_AI_Video_Generator_Spanish_01.xml"),
    ("09.01.00_Using_VI_Tools.xml", "09.01.00_Using_VI_Tools_Spanish_01.xml"),
    ("09.01.14_Anime_Video.xml", "09.01.14_Anime_Video_Spanish_01.xml"),
    ("10.00.00_PowerDirector_Plug-in.xml", "10.00.00_PowerDirector_Plug-in_Spanish_01.xml"),
    ("10.02.00_Auto_Edit.xml", "10.02.00_Auto_Edit_Spanish_01.xml"),
    ("10.02.03_Creating_Recorded_Con.xml", "10.02.03_Creating_Recorded_Con_Spanish_01.xml"),
    ('PDR & Credit_May25_FAQ_ENU_strings.html', 'PDR & Credit_May25_FAQ_ENU_strings_Italian_01.html'),
    ('PDR & Credit_May25_FAQ_ENU_strings.html', 'PDR & Credit_May25_FAQ_ENU_strings_Spanish_01.html'),
    ('PDR_May25_FAQ_ENU.html', 'PDR_May25_FAQ_ENU_Italian_01.html'),
    ('PDR_May25_FAQ_ENU.html', 'PDR_May25_FAQ_ENU_Spanish_01.html'),
]

input_file_folder = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\0522_Help_Source"
output_file_folder = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\0522_Help_Output"
compare_file_folder = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\0522_Help_Verify"
database_path = None

#  get index from arguments
if len(sys.argv) > 1:
    try:
        index = int(sys.argv[1])
    except ValueError:
        print("Invalid index provided. Using default index 0.")
        index = 0

input_file_path = os.path.join(input_file_folder, file_list[index][0])
output_file_path = os.path.join(output_file_folder, file_list[index][1])
if file_list[index][0].endswith('.xml'):
    compare_file_path = os.path.join(compare_file_folder, file_list[index][1].replace('.xml', '_Compare.html'))
else:
    compare_file_path = os.path.join(compare_file_folder, file_list[index][1].replace('.html', '_Compare.html'))

software_type = 'video editing software'

if 'PDR' in output_file_path:
    specific_names_xlsx_path = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\Mapping_Table\specific_name_pdr365_short_faq.xlsx"
else:
    specific_names_xlsx_path = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\Mapping_Table\specific_name_pdr365_0521_help.xlsx"

source_lang = 'English'


if 'Spanish' in output_file_path: target_lang = 'Spanish'
elif 'Italian' in output_file_path: target_lang = 'Italian'

print(input_file_path, 
    output_file_path, 
    compare_file_path, 
    specific_names_xlsx_path, 
    software_type, 
    source_lang, 
    target_lang,
    database_path)


verify_main(input_file_path, 
            output_file_path, 
            compare_file_path, 
            specific_names_xlsx_path, 
            software_type, 
            source_lang, 
            target_lang,
            source_type='UI',
            translate_refer=None,
            database_path=database_path)
