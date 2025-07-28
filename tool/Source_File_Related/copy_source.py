import os
import shutil

file_path = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\0728_Source"

pdr_file_nams = r'DEU_PDR_UIString_July.xlsx'
phd_file_nams = r'DEU_PHD_UIString_July.xlsx'

language = ['FRA', 'KOR', 'ITA', 'ESP']

for lang in language:
    ori_pdr_file = os.path.join(file_path, pdr_file_nams)
    ori_phd_file = os.path.join(file_path, phd_file_nams)

    tar_pdr_file = os.path.join(file_path, pdr_file_nams.replace('DEU', lang))
    tar_phd_file = os.path.join(file_path, phd_file_nams.replace('DEU', lang))

    shutil.copy(ori_pdr_file, tar_pdr_file)
    shutil.copy(ori_phd_file, tar_phd_file)