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

    chat_reorder = OpenaiAPIChat(
        model_name=conf.RESTRUCT_MODEL,
        system_prompt=sys_reorder_group_out_prompt()
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
            async for chunk, stop_reason in chat_map.get_stream_aresponse(map_p):
                response_map += chunk
            map_seg_out = as_json_obj(response_map)
            print('==================Used Map Seg Out=========================')
            print('map_seg_out:', map_seg_out)
            print('==================Used Map Seg Out=========================')

            # p = restruct_prompt(trans, ori, shreds_in_str, structure_info, map_seg_out)
            # # print('==================Used Resturct Prompt=========================')
            # # print(p)
            # # print('==================Used Resturct Prompt=========================')
            # chat.clear()
            # response = ''
            # async for chunk, stop_reason in chat.get_stream_aresponse(p, temperature=temperature):
            #     response += chunk
            # shreds_out = as_json_obj(response)
            shreds_out = map_seg_out

            # print('==================Used Resturct Response=========================')
            # print('shreds_in:', shreds_in)
            # print('shreds_out:', shreds_out)
            # print('==================Used Resturct Response=========================')

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

            score, err = validate_fit_in(
                shreds_in,
                trans,
                shreds_out
            )
            fit_candidates.append([score, shreds_out])
            if err:
                print('Come in this error')
                raise ValueError(err)
            break


        except Exception as e:
            print(f"Restructuring attempt {retry+1} failed: {str(e)}")
            retry += 1
            temperature *= 1.6  # exponential increase temperature
            if retry > max_retry:
                break
    print(fit_candidates)


    # replace contents
    if fit_candidates:
        print('==================Data =====================')
        print('trans:', trans)
        print('shreds_in_str:', shreds_in_str)
        print('shreds_out:', shreds_out)
        print('group.cids:', group.cids)
        print('group.elements:', group.elements)
        print('==================Data =====================')

        max_score, shreds_out = max(fit_candidates, key=lambda x: x[0])
        
        # Convert elements to serializable format to avoid JSON serialization error
        elements_info = []
        for i, element in enumerate(group.elements):
            element_info = {
                'index': i,
                'tag_name': getattr(element, 'name', 'unknown'),
                'element_id': str(id(element)),
                'attributes': dict(element.attrs) if hasattr(element, 'attrs') else {},
                'is_semantic': getattr(element, 'name', '') in ['strong', 'em', 'b', 'i', 'code', 'mark']
            }
            elements_info.append(element_info)
        
        reorder_p = reorder_group_out_prompt(trans, shreds_in_str, shreds_out, group.cids, elements_info)


        chat_reorder.clear()
        response = ''
        async for chunk, stop_reason in chat_reorder.get_stream_aresponse(reorder_p):
            response += chunk

        reorder_group = as_json_obj(response)
        print('==================reorder Group out =========================')
        print('reorder_group:', reorder_group)
        print('==================reorder Group out =========================')

        # Use reordered text shreds from AI response if available
        final_shreds_out = shreds_out
        final_cids = group.cids
        final_elements = group.elements

        # final_shreds_out = reorder_group.get('reordered_text_shreds', shreds_out)
        # final_cids = reorder_group.get('reordered_cids', group.cids)
        # final_elements = reorder_group.get('reordered_elements_info', group.elements)
        
        if reorder_group and 'reordered_text_shreds' in reorder_group:
            final_shreds_out = reorder_group['reordered_text_shreds']
            print('==================Using AI reordered shreds =========================')
            print('final_shreds_out:', final_shreds_out)
            
            # Use reordered cids if available
            if 'reordered_cids' in reorder_group:
                final_cids = reorder_group['reordered_cids']
                print('final_cids:', final_cids)
            
            # Use reordered elements_info if available and reconstruct elements order
            if 'reordered_elements_info' in reorder_group:
                reordered_elements_info = reorder_group['reordered_elements_info']
                print('reordered_elements_info:', reordered_elements_info)
                
                # Map element_id back to actual elements
                element_id_map = {str(id(ele)): ele for ele in group.elements}
                final_elements = []
                for elem_info in reordered_elements_info:
                    if elem_info['element_id'] in element_id_map:
                        final_elements.append(element_id_map[elem_info['element_id']])
                    else:
                        # Fallback to original order if mapping fails
                        final_elements.append(group.elements[elem_info['index']])
                
                print('final_elements:', final_elements)
            
            print('==================Using AI reordered shreds =========================')

        # Use enumeration instead of dictionary keys to process in order
        print(f"Processing {len(final_shreds_out)} shreds with enumeration...")
        for i, (k, v) in enumerate(final_shreds_out.items()):
            try:
                print(f"Processing index {i} (key: {k}, value: {v})")
                print(f"Available keys in final_shreds_out: {list(final_shreds_out.keys())}")
                print(f"Length of final_cids: {len(final_cids)}")
                print(f"Length of final_elements: {len(final_elements)}")
                
                # Use enumeration index instead of dictionary key
                if i >= len(final_cids):
                    print(f"ERROR: Enumeration index {i} out of range for final_cids (length: {len(final_cids)})")
                    continue
                    
                if i >= len(final_elements):
                    print(f"ERROR: Enumeration index {i} out of range for final_elements (length: {len(final_elements)})")
                    continue
                    
                cid = final_cids[i]  # Use enumeration index i
                ele = final_elements[i]  # Use enumeration index i
                
                print(f"Using enumeration index {i} - cid: {cid}, element: {ele}")
                print(f"Element contents length: {len(ele.contents) if hasattr(ele, 'contents') else 'No contents'}")
                
                if hasattr(ele, 'contents') and cid < len(ele.contents):
                    ele.contents[cid].replace_with(v)
                    print(f"Successfully replaced content at index {cid} using enumeration index {i}")
                else:
                    print(f"ERROR: cid {cid} out of range for element contents (length: {len(ele.contents) if hasattr(ele, 'contents') else 0})")
                
            except Exception as e:
                print(f"ERROR processing enumeration index {i} (key {k}): {str(e)}")
                import traceback
                traceback.print_exc()
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
    print('entering group_fit_in with group:', group.text_shreds)
    if match_score(str(group), trans) == 1.0:  # no translation is needed, e.g. function name, special symbols, etc.
        print('========')
        print('Enter Method 1')
        print('========')
        return 'S'
    elif len(group) == 1:  # single element text
        print('========')
        print('Enter Method 2')
        print('========')
        print('trans is: ', trans)
        str_content = group.elements[0].contents[group.cids[0]]
        str_content.replace_with(trans)
        return 'S'
    else:  # multi element text: restruct is needed
        print('========')
        print('Enter Method 3')
        print('========')
        return await restruct(group, ori, trans)

async def restruct_process(is_excel_translation, groups_out, ori_html=None):

    if is_excel_translation:
        # For Excel translation, just return the translated texts without DOM manipulation
        results = []
        for i, trans in groups_out.items():
            results.append(trans)
        return results
    else:
        restruct_chat = OpenaiAPIChat(
            model_name=conf.RESTRUCT_MODEL,
            system_prompt=restruct_sys_prompt()
        )
        p = restruct_prompt(
            groups_out,
            ori_html,
            # structure_info=json.dumps(groups_map, ensure_ascii=False, indent=0) if groups_map else "{}",
        )

        # print('===============System Prompt=====================')
        # print(restruct_chat.sys_prompt)
        # print('===============System Prompt=====================')

        # print('===============Used Restruct Prompt=====================')
        # print(p)
        # print('===============Used Restruct Prompt=====================')


        restruct_chat.clear()
        response = ''
        async for chunk, stop_reason in restruct_chat.get_stream_aresponse(p):
            response += chunk