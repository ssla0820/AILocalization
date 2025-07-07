import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from collections import OrderedDict
from chat.openai_api_chat import OpenaiAPIChat
from pages.general_functions import as_json_obj, InlineGroup
from prompts.translate_prompts import *
from prompts.restruct_prompts import *
import json
import asyncio
import difflib
from config import translate_config as conf


def validate_fit_in(
        shreds_in: dict[str, str],
        trans_str: str,
        shreds_out: dict[str, str],
) -> (float, str):
    """
    Validates if translated text fit correctly into the original structure.
    :param shreds_in: dict of pieces of original text before translation
    :param trans_str: translated text of grouped inline shreds
    :param shreds_out: dict of pieces of translated text
    :return: A tuple of a fit score and the reason of not perfectly fit.
             score of 1 indicates perfectly fit, 0 indicates it is not
             able to fit at all, score between 0 and 1 indicate partially fit.
    """
    if len(shreds_in) != len(shreds_out):
        return 0., f'Length not match, in({len(shreds_in)}) != out({len(shreds_out)}).'

    sorted_shreds_out = {k: v for k, v in sorted(shreds_out.items(), key=lambda x: int(x[0]))}
    fit_str = ''.join([v for v in sorted_shreds_out.values()])
    # if (score := match_score(trans_str, fit_str)) != 1.0:
    if (score := match_score(trans_str, fit_str)) < 0.7:
        return score, f'String not match, to_fit="{trans_str}" | fit="{fit_str}"'
    return 1., ''

def match_score(s1, s2):
    """
    Calculates the similarity between two strings.
    Returns 1.0 if two strings matches, ignore casing,
    symbols and spacing.
    :param s1: string 1 for comparison
    :param s2: string 2 for comparison
    :return: match score, 1.0 for best match.
    """
    compact_tab = str.maketrans({
        ' ': '',
        '\n': '',
        '\t': '',
        ',': '',
        '，': '',
        '.': ''
    })
    s1 = s1.translate(compact_tab).lower()
    s2 = s2.translate(compact_tab).lower()
    return difflib.SequenceMatcher(None, s1, s2).ratio()


async def restruct(
        group: InlineGroup,
        ori: str,
        trans: str
):
    """
    Restructures the translated text to fit the original structure.
    :param group: inline group to be fit back into
    :param ori: original grouped text before translation
    :param trans: translated text
    :return: restruct result
    """
    max_retry = 10
    retry = 0
    chat = OpenaiAPIChat(
        model_name=conf.RESTRUCT_MODEL,
        system_prompt=restruct_sys_prompt()
    )
    
    chat_map = OpenaiAPIChat(
        model_name=conf.RESTRUCT_MODEL,
        system_prompt=map_sys_prompt()
    )

    # Create a deterministic ordering of shreds to maintain structure
    shreds_in = OrderedDict({})
    for i, shred in enumerate(group.text_shreds):
        shreds_in[str(i)] = shred
      # Create a structure map to track the hierarchical relationships
    structure_map = {}
    for i, element in enumerate(group.elements):
        # If this is a list item or has specific parent-child relationship, track it
        parent_id = None
        if element.parent and element.parent.name in ['ul', 'ol', 'li']:
            parent_id = str(id(element.parent))
        
        # Get element attributes to help preserve structure
        element_attrs = dict(element.attrs) if hasattr(element, 'attrs') else {}
        
        structure_map[str(i)] = {
            'parent': parent_id,
            'tag': element.name,
            'position': i,  # Preserve original position order
            'attributes': element_attrs,
            'element_id': str(id(element))  # Unique identifier for this specific element
        }
    
    shreds_in_str = json.dumps(shreds_in, ensure_ascii=False, indent=0)
    # Include structure information in the prompt to help maintain order
    structure_info = json.dumps(structure_map, ensure_ascii=False, indent=0) if structure_map else "{}"
    
    temperature = 0.01

    fit_candidates = []
    while True:
        try:
            chat_map.clear()
            # Enhanced prompt with structure information
            map_p = map_prompt(trans, ori, shreds_in_str)
            # print('==================Used Map Prompt=========================')
            # print(map_p)
            # print('==================Used Map Prompt=========================')

            response_map = ''
            async for chunk, stop_reason in chat_map.get_stream_aresponse(map_p, temperature=temperature):
                response_map += chunk
            map_seg_out = as_json_obj(response_map)
            # print('==================Used Map Seg Out=========================')
            # print(map_seg_out)
            # print('==================Used Map Seg Out=========================')
            # map_seg_out = None

            p = restruct_prompt(trans, ori, shreds_in_str, structure_info, map_seg_out)
            # print('==================Used Resturct Prompt=========================')
            # print(p)
            # print('==================Used Resturct Prompt=========================')
            chat.clear()
            response = ''
            async for chunk, stop_reason in chat.get_stream_aresponse(p, temperature=temperature):
                response += chunk
            shreds_out = as_json_obj(response)

            print('==================Used Resturct Response=========================')
            print(shreds_in)
            print(shreds_out)
            print('==================Used Resturct Response=========================')

            # response validation check
            if not shreds_out:
                raise ValueError('Invalid model response as JSON object.')
                
            # Make sure all original keys are present in the response
            if set(shreds_in.keys()) != set(shreds_out.keys()):
                missing_keys = set(shreds_in.keys()) - set(shreds_out.keys())
                extra_keys = set(shreds_out.keys()) - set(shreds_in.keys())
                
                if missing_keys:
                    print(f"Warning: Missing keys in restructured text: {missing_keys}")
                    # Add missing keys with empty strings or original content
                    for key in missing_keys:
                        shreds_out[key] = "" # or shreds_in[key] to keep original
                
                if extra_keys:
                    print(f"Warning: Extra keys in restructured text: {extra_keys}")
                    # Remove extra keys
                    for key in extra_keys:
                        del shreds_out[key]
            print('========= keys value are correct, start fit =======')
            score, err = validate_fit_in(
                shreds_in,
                trans,
                shreds_out
            )
            print('========= fit score is:', score, 'err:', err, '========')
            fit_candidates.append([score, shreds_out])
            print('========= fit candidates are:', fit_candidates, '========')
            if err:
                raise ValueError(err)
            break


        except Exception as e:
            print(f"Restructuring attempt {retry+1} failed: {str(e)}")
            retry += 1
            temperature *= 1.6  # exponential increase temperature
            if retry > max_retry:
                break

    # replace contents
    if fit_candidates:
        max_score, shreds_out = max(fit_candidates, key=lambda x: x[0])
        
        # Sort by original position before replacing to maintain order
        sorted_items = sorted(shreds_out.items(), key=lambda x: int(x[0]))
        
        for k, v in sorted_items:
            cid = group.cids[int(k)]
            ele = group.elements[int(k)]
            ele.contents[cid].replace_with(v)
        return 'C' if max_score < 1.0 else 'S'
    else:
        return 'F'


async def group_fit_in(
        group: InlineGroup,
        ori: str,
        trans: str
):
    """
    Fits translated text into the original structure.
    :param group: inline group to be fit back into
    :param ori: original grouped text before translation
    :param trans: translated text
    :return: fit-in result
    """
    if match_score(str(group), trans) == 1.0:  # no translation is needed, e.g. function name, special symbols, etc.
        return 'S'
    elif len(group) == 1:  # single element text
        str_content = group.elements[0].contents[group.cids[0]]
        str_content.replace_with(trans)
        return 'S'
    else:  # multi element text: restruct is needed
        return await restruct(group, ori, trans)


async def restruct_process(is_excel_translation, groups_in, groups_out, groups_map):
    
    if is_excel_translation:
        # For Excel translation, just return the translated texts without DOM manipulation
        results = []
        for i, trans in groups_out.items():
            results.append(trans)
        return results
    else:
        # For HTML/XML translation, perform the fitting back into the DOM
        fit_in_tasks = []
        for i, trans in groups_out.items():
            group = groups_map[i]
            fit_in_tasks.append(group_fit_in(group, groups_in[i], trans))
        results = await asyncio.gather(*fit_in_tasks, return_exceptions=True)
        return results
