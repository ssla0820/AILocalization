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
            score, err = validate_fit_in(
                shreds_in,
                trans,
                shreds_out
            )
            fit_candidates.append([score, shreds_out])
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
        print(f'sorted_items: {sorted_items}')
        for k, v in sorted_items:
            print(f'k: {k}, v: {v}')
            cid = group.cids[int(k)]
            ele = group.elements[int(k)]
            ele.contents[cid].replace_with(v)

            print(f"cid: {cid}")
            print(f"element: {ele}")
            print(f"content: {ele.contents[cid]}")
        return 'C' if max_score < 1.0 else 'S'
    else:
        return 'F'


async def new_restruct(group, trans):
    """
    A simplified restructuring function that replaces content in the group elements.
    
    :param group: inline group to be fit back into
    :param trans: translated text
    :return: status code indicating success
    """
    try:
        # 1. For each element in the group, replace its content
        if len(group.elements) == 1:
            # If there's only one element, simply replace its content
            element = group.elements[0]
            cid = group.cids[0]
            element.contents[cid].replace_with(trans)
            return 'S'
            
        # 2. For multiple elements, we need to distribute the translation across them
        # Simple approach: calculate proportion of text in each element and distribute accordingly
        total_original_length = sum(len(shred) for shred in group.text_shreds)
        if total_original_length == 0:
            return 'F'  # Nothing to replace
        
        trans_chars = list(trans)
        current_pos = 0
        
        # 3. Distribute translated content to each element proportionally
        for i, shred in enumerate(group.text_shreds):
            if i >= len(group.elements) or i >= len(group.cids):
                break
                
            # Calculate how much of the translation should go to this element
            # based on the proportion of the original text
            shred_proportion = len(shred) / total_original_length
            chars_for_shred = max(1, int(len(trans) * shred_proportion))
            
            # Make sure we don't exceed the translation length
            if current_pos + chars_for_shred > len(trans):
                chars_for_shred = len(trans) - current_pos
                
            # Extract the portion of translation for this element
            shred_trans = trans[current_pos:current_pos + chars_for_shred]
            current_pos += chars_for_shred
            
            # Replace the content in the element
            element = group.elements[i]
            cid = group.cids[i]
            element.contents[cid].replace_with(shred_trans)
        
        # Handle any remaining translation text (assign to the last element)
        if current_pos < len(trans):
            remaining_trans = trans[current_pos:]
            last_idx = len(group.elements) - 1
            if last_idx >= 0 and last_idx < len(group.cids):
                element = group.elements[last_idx]
                cid = group.cids[last_idx]
                
                # Append the remaining translation to the last element's content
                existing_content = element.contents[cid].string or ""
                element.contents[cid].replace_with(existing_content + remaining_trans)
        
        return 'S'  # Success
    
    except Exception as e:
        print(f"Error in new_restruct: {str(e)}")
        return 'F'  # Failure

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
        return 'S'
    elif len(group) == 1:  # single element text
        str_content = group.elements[0].contents[group.cids[0]]
        str_content.replace_with(trans)
        return 'S'
    else:  # multi element text: restruct is needed
        # return await restruct(group, ori, trans)
        # return await new_restruct(group, trans)
        for i, element in enumerate(group.elements):
            # element = trans
            group.elements[i].replace_with(trans)
        # print('group_fit_in completed with group:', group.text_shreds)
            
        return 'S'


async def restruct_process(is_excel_translation, groups_in, groups_out, groups_map):
    
    if is_excel_translation:
        # For Excel translation, just return the translated texts without DOM manipulation
        results = []
        for i, trans in groups_out.items():
            results.append(trans)
        print(f'result is: {results}')
        return results
    else:
        # For HTML/XML translation, perform the fitting back into the DOM
        fit_in_tasks = []
        for i, trans in groups_out.items():
            group = groups_map[i]
            fit_in_tasks.append(group_fit_in(group, groups_in[i], trans))
        results = await asyncio.gather(*fit_in_tasks, return_exceptions=True)
        return results
    
# async def restruct_process(is_excel_translation, groups_in, groups_out, groups_map):
#     # # print(f"Restructuring {len(groups_in)} groups...")
#     # print(f"=================================Groups in\n: {groups_in}")
#     # # print(f"=================================Groups out\n: {groups_out}")
#     # print(f"=================================Groups map: {groups_map}")
    
#     if is_excel_translation:
#         # For Excel translation, just return the translated texts without DOM manipulation
#         results = []
#         for i, trans in groups_out.items():
#             results.append(trans)
#         return results
#     else:
#         # For HTML/XML translation, perform the fitting back into the DOM
#         fit_in_tasks = []
#         for i, trans in groups_out.items():
#             group = groups_map[i]
#             print(f"Processing group {i} with text: {group.text_shreds}")
#             fit_in_tasks.append(group_fit_in(group, groups_in[i], trans))

#         # print('============Fit In Tasks=============')
#         # print(fit_in_tasks)
#         # print('============Fit In Tasks=============')
#         results = await asyncio.gather(*fit_in_tasks, return_exceptions=True)
#         # print('============Fit In Results=============')
#         # print(results)
#         # print('============Fit In Results=============')

#         # print('=============Group Map=============')
#         # print(groups_map)
#         # print('=============Group Map=============')

#         return results


# Groups map: OrderedDict({'0': InlineGroup(text_shreds=['body {\ttext-align: center;\tpadding: 0px;\tmargin: 0px auto;}#container {    margin: 0 auto !important;    margin-left: auto;\tmargin-right: auto;\twidth: 980px;\ttext-align: left;}.star {\tcolor: #FF0000;}'], cids=[0], elements=[<style type="text/css">
# body
# {
#         text-align: center;
#         padding: 0px;
#         margin: 0px auto;
# }
# #container {
#     margin: 0 auto !important;
#     margin-left: auto;
#         margin-right: auto;
#         width: 980px;
#         text-align: left;
# }
# .star {
#         color: #FF0000;
# }
# </style>]), '1': InlineGroup(text_shreds=[' ', 'ENU'], cids=[0, 0], elements=[<div id="container"> <span id="language">ENU</span><br/>
# <table border="1" name="faq">
# <tbody>
# <tr>
# <td align="right" nowrap="nowrap">FAQID(CS):</td>
# <td name="csfaqid">Q25-00012<br/>
# </td>
# <td align="right">FAQ ID:</td>
# <td name="faqid"><br/>
# </td>
# <td align="right">Weight:</td>
# <td name="faqweight">1000</td>
# </tr>
# <tr>
# <td align="right" valign="top">Question:</td>
# <td colspan="5" name="faqQ" valign="top">
# <p align="left">How do I blur out (add mosaic effect) people or
#                 objects in a video in CyberLink PowerDirector 365?</p>
# </td>
# </tr>
# <tr>
# <td align="right" valign="top">Answer:</td>
# <td colspan="5" name="faqA" valign="top">
# <p>In the new version of PowerDirector 365 (released after Apr.
#                 2025), the Motion Tracker has been redesigned and moved to the
#                 "Tracking" tab on the top of the quick editing panel. This new
#                 Motion Tracking feature does not include the FX option to add a
#                 mosaic or blur effect, which was available in the old Motion
#                 Tracker. As an alternative, we suggest you follow the steps
#                 below to apply a blur effect to your video:<br/>
# </p>
# <p>To blur out people's faces in video in PowerDirector 365, do
#                 this: </p>
# <ol>
# <li>Add the video that has people's faces on the timeline.</li>
# <li>Go to <strong>Effects </strong>Room &gt; <strong>Video
#                     Effects </strong>&gt; <strong>Face Blur</strong>.</li>
# <li>Select an effect and drag it onto the video clip on the
#                   timeline.</li>
# <li>After analyzing, select the video on the timeline and then
#                   click the <img alt="" src="https://assist.cyberlink.com/cs/faq/PDR/2025/Motion%20tracking/effect%20settings.png" style="width: 25px; height: 21px;"/> button above the
#                   timeline to modify the effect settings if needed.</li>
# </ol>
# <p>To blur out an object in video in PowerDirector 365, do this: </p>
# <ol>
# <li>Add the video you want to blur the object on the timeline.</li>
# <li>Add a <strong>Face Cover</strong> <strong>sticker </strong>(e.g.,
#                   Face Cover 02, Face Cover 04, etc)<strong> </strong>from the
#                   <strong>Overlays </strong>Room to a lower track (below the
#                   video) in the timeline.</li>
# <li>Select the Face Cover sticker and then click <strong>Edit</strong>
#                   &gt; <strong>Tracking</strong> tab.</li>
# <li>Enable the <strong>Apply Motion Tracking</strong> option</li>
# <li>A yellow tracking box will then display in the preview
#                   window. Drag and resize this box to fit over the object in
#                   your video that you want to track.</li>
# <li>Adjust the position and size of the Face Cover sticker in
#                   the preview window to cover the tracked object.</li>
# <li>Click the <strong>Track </strong>button to start the
#                   motion tracking process.</li>
# <li>After tracking, check the preview window to see if the added
#                   Face Cover sticker is following the video element the way you
#                   expect.</li>
# </ol>
# </td>
# </tr>
# </tbody>
# </table>
# </div>, <span id="language">ENU</span>]), '2': InlineGroup(text_shreds=['FAQID(CS):'], cids=[0], elements=[<td align="right" nowrap="nowrap">FAQID(CS):</td>]), '3': InlineGroup(text_shreds=['Q25-00012'], cids=[0], elements=[<td name="csfaqid">Q25-00012<br/>
# </td>]), '4': InlineGroup(text_shreds=['FAQ ID:'], cids=[0], elements=[<td align="right">FAQ ID:</td>]), '5': InlineGroup(text_shreds=['Weight:'], cids=[0], elements=[<td align="right">Weight:</td>]), '6': InlineGroup(text_shreds=['1000'], cids=[0], elements=[<td name="faqweight">1000</td>]), '7': InlineGroup(text_shreds=['Question:'], cids=[0], elements=[<td align="right" valign="top">Question:</td>]), '8': InlineGroup(text_shreds=['How do I blur out (add mosaic effect) people or                objects in a video in CyberLink PowerDirector 365?'], cids=[0], elements=[<p align="left">How do I blur out (add mosaic effect) people or
#                 objects in a video in CyberLink PowerDirector 365?</p>]), '9': InlineGroup(text_shreds=['Answer:'], cids=[0], elements=[<td align="right" valign="top">Answer:</td>]), '10': InlineGroup(text_shreds=['In the new version of PowerDirector 365 (released after Apr.                2025), the Motion Tracker has been redesigned and moved to the                "Tracking" tab on the top of the quick editing panel. This new                
# Motion Tracking feature does not include the FX option to add a                mosaic or blur effect, which was available in the old Motion          
#       Tracker. As an alternative, we suggest you follow the steps                below to apply a blur effect to your video:'], cids=[0], elements=[<p>In the new version of PowerDirector 365 (released after Apr.
#                 2025), the Motion Tracker has been redesigned and moved to the
#                 "Tracking" tab on the top of the quick editing panel. This new
#                 Motion Tracking feature does not include the FX option to add a
#                 mosaic or blur effect, which was available in the old Motion
#                 Tracker. As an alternative, we suggest you follow the steps
#                 below to apply a blur effect to your video:<br/>
# </p>]), '11': InlineGroup(text_shreds=["To blur out people's faces in video in PowerDirector 365, do                this: "], cids=[0], elements=[<p>To blur out people's faces in video in PowerDirector 365, do
#                 this: </p>]), '12': InlineGroup(text_shreds=["Add the video that has people's faces on the timeline."], cids=[0], elements=[<li>Add the video that has people's faces on the timeline.</li>]), '13': InlineGroup(text_shreds=['Go to ', 'Effects ', 'Room > ', 'Video                    Effects ', '> ', 'Face Blur', '.'], cids=[0, 0, 2, 0, 4, 0, 6], elements=[<li>Go to <strong>Effects </strong>Room &gt; <strong>Video
#                     Effects </strong>&gt; <strong>Face Blur</strong>.</li>, <strong>Effects </strong>, <li>Go to <strong>Effects </strong>Room &gt; <strong>Video
#                     Effects </strong>&gt; <strong>Face Blur</strong>.</li>, <strong>Video
#                     Effects </strong>, <li>Go to <strong>Effects </strong>Room &gt; <strong>Video
#                     Effects </strong>&gt; <strong>Face Blur</strong>.</li>, <strong>Face Blur</strong>, <li>Go to <strong>Effects </strong>Room &gt; <strong>Video
#                     Effects </strong>&gt; <strong>Face Blur</strong>.</li>]), '14': InlineGroup(text_shreds=['Select an effect and drag it onto the video clip on the                  timeline.'], cids=[0], elements=[<li>Select an effect and drag it onto the video clip on the
#                   timeline.</li>]), '15': InlineGroup(text_shreds=['After analyzing, select the video on the timeline and then                  click the ', ' button above the                  timeline to modify the effect settings if needed.'], cids=[0, 2], elements=[<li>After analyzing, select the video on the timeline and then
#                   click the <img alt="" src="https://assist.cyberlink.com/cs/faq/PDR/2025/Motion%20tracking/effect%20settings.png" style="width: 25px; height: 21px;"/> button above the
#                   timeline to modify the effect settings if needed.</li>, <li>After analyzing, select the video on the timeline and then
#                   click the <img alt="" src="https://assist.cyberlink.com/cs/faq/PDR/2025/Motion%20tracking/effect%20settings.png" style="width: 25px; height: 21px;"/> button above the
#                   timeline to modify the effect settings if needed.</li>]), '16': InlineGroup(text_shreds=['To blur out an object in video in PowerDirector 365, do this: '], cids=[0], elements=[<p>To blur out an object in video in PowerDirector 365, do this: </p>]), '17': InlineGroup(text_shreds=['Add the video you want to blur the object on the timeline.'], cids=[0], elements=[<li>Add the video you want to blur the object on the timeline.</li>]), '18': InlineGroup(text_shreds=['Add a ', 'Face Cover', ' ', 'sticker ', '(e.g.,                  Face Cover 02, Face Cover 04, etc)', ' ', 'from the                  ', 'Overlays ', 'Room to a lower track (below the                  video) in the timeline.'], cids=[0, 0, 2, 0, 4, 0, 6, 0, 8], elements=[<li>Add a <strong>Face Cover</strong> <strong>sticker </strong>(e.g.,
#                   Face Cover 02, Face Cover 04, etc)<strong> </strong>from the
#                   <strong>Overlays </strong>Room to a lower track (below the
#                   video) in the timeline.</li>, <strong>Face Cover</strong>, <li>Add a <strong>Face Cover</strong> <strong>sticker </strong>(e.g.,   
#                   Face Cover 02, Face Cover 04, etc)<strong> </strong>from the
#                   <strong>Overlays </strong>Room to a lower track (below the
#                   video) in the timeline.</li>, <strong>sticker </strong>, <li>Add a <strong>Face Cover</strong> <strong>sticker </strong>(e.g.,     
#                   Face Cover 02, Face Cover 04, etc)<strong> </strong>from the
#                   <strong>Overlays </strong>Room to a lower track (below the
#                   video) in the timeline.</li>, <strong> </strong>, <li>Add a <strong>Face Cover</strong> <strong>sticker </strong>(e.g.,
#                   Face Cover 02, Face Cover 04, etc)<strong> </strong>from the
#                   <strong>Overlays </strong>Room to a lower track (below the
#                   video) in the timeline.</li>, <strong>Overlays </strong>, <li>Add a <strong>Face Cover</strong> <strong>sticker </strong>(e.g.,    
#                   Face Cover 02, Face Cover 04, etc)<strong> </strong>from the
#                   <strong>Overlays </strong>Room to a lower track (below the
#                   video) in the timeline.</li>]), '19': InlineGroup(text_shreds=['Select the Face Cover sticker and then click ', 'Edit', '          
#         > ', 'Tracking', ' tab.'], cids=[0, 0, 2, 0, 4], elements=[<li>Select the Face Cover sticker and then click <strong>Edit</strong>
#                   &gt; <strong>Tracking</strong> tab.</li>, <strong>Edit</strong>, <li>Select the Face Cover sticker and then click <strong>Edit</strong>
#                   &gt; <strong>Tracking</strong> tab.</li>, <strong>Tracking</strong>, <li>Select the Face Cover sticker and then click <strong>Edit</strong>
#                   &gt; <strong>Tracking</strong> tab.</li>]), '20': InlineGroup(text_shreds=['Enable the ', 'Apply Motion Tracking', ' option'], cids=[0, 0, 2], elements=[<li>Enable the <strong>Apply Motion Tracking</strong> option</li>, <strong>Apply Motion Tracking</strong>, <li>Enable the <strong>Apply Motion Tracking</strong> option</li>]), '21': InlineGroup(text_shreds=['A yellow tracking box will then display in the preview              
#     window. Drag and resize this box to fit over the object in                  your video that you want to track.'], cids=[0], elements=[<li>A yellow tracking box will then display in the preview
#                   window. Drag and resize this box to fit over the object in
#                   your video that you want to track.</li>]), '22': InlineGroup(text_shreds=['Adjust the position and size of the Face Cover sticker in                  the preview window to cover the tracked object.'], cids=[0], elements=[<li>Adjust the position and size of the Face Cover sticker in
#                   the preview window to cover the tracked object.</li>]), '23': InlineGroup(text_shreds=['Click the ', 'Track ', 'button to start the                  motion tracking process.'], cids=[0, 0, 2], elements=[<li>Click the <strong>Track </strong>button to start the
#                   motion tracking process.</li>, <strong>Track </strong>, <li>Click the <strong>Track </strong>button to start the
#                   motion tracking process.</li>]), '24': InlineGroup(text_shreds=['After tracking, check the preview window to see if the added                  Face Cover sticker is following the video element the way you                  expect.'], cids=[0], elements=[<li>After tracking, check the preview window to see if the added
#                   Face Cover sticker is following the video element the way you
#                   expect.</li>])})



#     {
#     "task": "translation_restructuring",
#     "translation": "Vai a Sala effetti > Effetti video > Sfocatura volto.",
#     "original_text": "Go to Effects Room > Video         Effects > Face Blur.",
#     "segments_json": "{\n\"0\": \"Go to \",\n\"1\": \"Effects \",\n\"2\": \"Room > \",\n\"3\": \"Video                    Effects \",\n\"4\": \"> \",\n\"5\": \"Face Blur\",\n\"6\": \".\"\n}",
#     "has_structural_context": True,
#     "structural_context": "{\n\"0\": {\n\"parent\": \"2100463320400\",\n\"tag\": \"li\",\n\"position\": 0,\n\"attributes\": {},\n\"element_id\": \"2100463861840\"\n},\n\"1\": {\n\"parent\": \"2100463861840\",\n\"tag\": \"strong\",\n\"position\": 1,\n\"attributes\": {},\n\"element_id\": \"2100463862096\"\n},\n\"2\": {\n\"parent\": \"2100463320400\",\n\"tag\": \"li\",\n\"position\": 2,\n\"attributes\": {},\n\"element_id\": \"2100463861840\"\n},\n\"3\": {\n\"parent\": \"2100463861840\",\n\"tag\": \"strong\",\n\"position\": 3,\n\"attributes\": {},\n\"element_id\": \"2100463862352\"\n},\n\"4\": {\n\"parent\": \"2100463320400\",\n\"tag\": \"li\",\n\"position\": 4,\n\"attributes\": {},\n\"element_id\": \"2100463861840\"\n},\n\"5\": {\n\"parent\": \"2100463861840\",\n\"tag\": \"strong\",\n\"position\": 5,\n\"attributes\": {},\n\"element_id\": \"2100463862608\"\n},\n\"6\": {\n\"parent\": \"2100463320400\",\n\"tag\": \"li\",\n\"position\": 6,\n\"attributes\": {},\n\"element_id\": \"2100463861840\"\n}\n}",
#     "structural_guidelines": [
#         "Pay close attention to hierarchical relationships between elements",
#         "Maintain exact order of text fragments in the original structure",
#         "Do not move text between different list items or paragraphs",
#         "Preserve hierarchical nesting of elements",
#         "Each segment ID corresponds to content within a specific XML/HTML element",
#         "Element boundaries must be strictly preserved - do not mix content between different elements",
#         "Consider element attributes and types when distributing translated text"
#     ],
#     "requirements": [
#         "Each segment must receive appropriate translated text",
#         "No text should be moved between different list items or structural elements",
#         "No characters in the translation should be dropped",
#         "Text order must match the original structure perfectly",
#         "The result must be valid JSON with the same keys as the input",
#         "CRITICAL: Do not mix content between different XML elements",
#         "CRITICAL: Each segment corresponds to content within a specific XML element boundary",
#         "CRITICAL: Maintain the exact semantic boundaries - text that belongs to one element should not leak into another element's content"
#     ],
#     "output_format": "Valid JSON object with the same keys as the input"
#     }


# '10': InlineGroup(text_shreds=['In the new version of PowerDirector 365 (released after Apr.                2025), the Motion Tracker has been redesigned and moved to the                "Tracking" tab on the top of the quick editing panel. This new                
# Motion Tracking feature does not include the FX option to add a                mosaic or blur effect, which was available in the old Motion          
#       Tracker. As an alternative, we suggest you follow the steps                below to apply a blur effect to your video:'], cids=[0], elements=[<p>In the new version of PowerDirector 365 (released after Apr.
#                 2025), the Motion Tracker has been redesigned and moved to the
#                 "Tracking" tab on the top of the quick editing panel. This new
#                 Motion Tracking feature does not include the FX option to add a
#                 mosaic or blur effect, which was available in the old Motion
#                 Tracker. As an alternative, we suggest you follow the steps
#                 below to apply a blur effect to your video:<br/>