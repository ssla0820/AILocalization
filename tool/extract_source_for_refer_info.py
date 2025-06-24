import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from bs4 import BeautifulSoup
from collections import OrderedDict
from chat.openai_api_chat import OpenaiAPIChat
from pages.general_functions import InlineGroup, get_text_group_inline, detect_file_encoding
import math
import pandas as pd
from config import translate_config as conf
import os

def segment_groups_map(
        groups_map: dict[str, InlineGroup],
        max_token: int,
        token_counter: callable
) -> list[OrderedDict]:
    """
    Segments a map of inline groups based on token count, hoping the
    translation response of each segment won't exceed context length
    of the model. Also, run each segments currently also speeds up the job.
    :param groups_map: Dictionary of inline groups and their id
    :param max_token: max number of token in each segment
    :param token_counter: a function that takes a string as input and output number of tokens
    :return: A list of segmented inline groups
    """
    if not (token_all := sum([token_counter(str(g)) for g in groups_map.values()])):
        return []
    n_seg = math.ceil(token_all / max_token)
    len_seg = math.ceil(token_all / n_seg)
    ret = []
    token_cnt = 0
    cnt = 0
    seg = OrderedDict({})
    for k, group in groups_map.items():
        n = token_counter(str(group))
        if n > max_token:
            # raise ValueError(f'Length of single paragraph [{n}] exceed max length [{max_token}].')
            print(f'Single paragraph exceed max length [{n} > {max_token}]. Skip this one!')
            continue
        if (token_cnt > len_seg) and seg:
            ret.append(seg)
            token_cnt = 0
            cnt = 0
            seg = OrderedDict({})
        seg[str(cnt)] = group
        cnt += 1
        token_cnt += n
    ret.append(seg)
    return ret

def extract_content(soup):
    groups_map = get_text_group_inline(soup)
    groups_map_segments = segment_groups_map(
        groups_map,
        int(conf.N_INPUT_TOKEN),
        OpenaiAPIChat(conf.TRANSLATE_MODEL).n_tokens
    )

    source_text_list = []
    for seg in groups_map_segments:
        groups_in = {
            k: str(v).replace('\n', '') for k, v in seg.items()
        }
        for source_text_index, source_text in groups_in.items():
            source_text_list.append([source_text, "", ""])

    return source_text_list

def extract_content_from_xlsx(input_file):
    df = pd.read_excel(input_file, engine='openpyxl')
    source_text_list = []
    for index, row in df.iterrows():
        source_text = row[0]  # Assuming the first column contains the source text
        source_text_list.append([source_text, "", ""])
    return source_text_list

def get_output_file_name(input_file):
    base_filename, _ = os.path.splitext(input_file)
    output_file = f"{base_filename}_refer_info.xlsx"
    return output_file

def save_to_xlsx(source_lang, source_text_list, output_file):
    df = pd.DataFrame(source_text_list, columns=[source_lang, 'Refer_Text', 'Refer_Image'])
    df.to_excel(output_file, index=False)


def extract_to_xlsx_process(input_file, source_lang):
    detect_file_type = os.path.splitext(input_file)[1].lower()
    if detect_file_type == '.xlsx':
        source_text_list = extract_content_from_xlsx(input_file)
    else:
        used_encoding, file_content = detect_file_encoding(input_file, source_lang)
        bs = BeautifulSoup(file_content)
        source_text_list =  extract_content(bs)
    output_file = get_output_file_name(input_file)
    save_to_xlsx(source_lang, source_text_list, output_file)

def main(input_file, source_lang):
    extract_to_xlsx_process(input_file, source_lang)

if __name__ == '__main__':
    # ==================Input Information ============================
    source_lang = 'ENU'
    input_file = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\0623_Source\DEU_PDR_UIString_June.xlsx"
    # ==================Input Information ============================

    main(input_file, source_lang)

