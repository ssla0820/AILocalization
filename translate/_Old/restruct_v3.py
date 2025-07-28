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
import re


def validate_fit_in_v3(
        shreds_in: dict[str, str],
        trans_str: str,
        shreds_out: dict[str, str],
) -> tuple[float, str]:
    """
    Enhanced validation for restructured text.
    """
    if len(shreds_in) != len(shreds_out):
        return 0., f'Length not match, in({len(shreds_in)}) != out({len(shreds_out)}).'

    sorted_shreds_out = {k: v for k, v in sorted(shreds_out.items(), key=lambda x: int(x[0]))}
    fit_str = ''.join([v for v in sorted_shreds_out.values()])
    
    # More strict validation
    if (score := match_score(trans_str, fit_str)) < 0.8:
        return score, f'String not match, to_fit="{trans_str}" | fit="{fit_str}"'
    
    # Check if important content is not lost
    important_words = extract_important_words(trans_str)
    fit_words = extract_important_words(fit_str)
    
    if not all(word in fit_words for word in important_words):
        return 0.5, 'Important words missing in restructured text'
    
    return 1., ''


def match_score(s1, s2):
    """
    Calculates the similarity between two strings.
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


def extract_important_words(text):
    """
    Extract important words from text (excluding common words).
    """
    # Remove punctuation and split into words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out common words (basic stopwords)
    stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'cannot', 'this', 'that', 'these', 'those'}
    
    return [word for word in words if word not in stopwords and len(word) > 2]


def analyze_element_structure(group: InlineGroup):
    """
    Analyze the structure of elements to identify semantic relationships.
    """
    element_analysis = {}
    unique_elements = {}
    
    for i, element in enumerate(group.elements):
        element_id = id(element)
        
        # Track unique elements and their occurrences
        if element_id not in unique_elements:
            unique_elements[element_id] = {
                'element': element,
                'indices': [],
                'text_parts': [],
                'tag_name': getattr(element, 'name', 'unknown')
            }
        
        unique_elements[element_id]['indices'].append(i)
        unique_elements[element_id]['text_parts'].append(group.text_shreds[i])
        
        # Analyze individual element
        element_analysis[i] = {
            'element_id': element_id,
            'tag_name': getattr(element, 'name', 'unknown'),
            'is_semantic': getattr(element, 'name', '') in ['strong', 'em', 'b', 'i', 'code', 'mark'],
            'text': group.text_shreds[i],
            'cid': group.cids[i]
        }
    
    return element_analysis, unique_elements


async def semantic_aware_restruct(group: InlineGroup, ori: str, trans: str):
    """
    Smart restructuring that preserves HTML formatting while ensuring correct content.
    """
    print(f"=== Semantic Aware Restruct ===")
    print(f"Original: {ori}")
    print(f"Translation: {trans}")
    print(f"Text shreds: {group.text_shreds}")
    
    element_analysis, unique_elements = analyze_element_structure(group)
    
    # Case 1: All segments belong to the same element
    if len(unique_elements) == 1:
        print("All segments belong to the same element - using simplified approach")
        element_info = list(unique_elements.values())[0]
        element = element_info['element']
        first_cid = group.cids[0]
        
        element.contents[first_cid].replace_with(trans)
        
        # Clear other positions
        for i in range(1, len(group.elements)):
            group.elements[i].contents[group.cids[i]].replace_with("")
        
        return 'S'
    
    # Case 2: Analyze semantic tags
    semantic_elements = [info for info in element_analysis.values() if info['is_semantic']]
    
    print(f"Found {len(semantic_elements)} semantic tags")
    
    if len(semantic_elements) == 0:
        # No semantic tags - use simple approach
        print("No semantic tags found - using simple approach")
        return await simple_multi_element_restruct(group, ori, trans, element_analysis)
    
    elif len(semantic_elements) == 1:
        # One semantic tag - try to preserve it
        print("One semantic tag found - attempting to preserve")
        return await handle_single_semantic_tag(group, ori, trans, semantic_elements[0], element_analysis)
    
    elif len(semantic_elements) == 2:
        # Two semantic tags - smart mapping (your main problem case)
        print("Two semantic tags found - attempting smart mapping")
        return await handle_two_semantic_tags(group, ori, trans, semantic_elements, element_analysis)
    
    else:
        # Too many semantic tags - conservative approach
        print(f"Too many semantic tags ({len(semantic_elements)}) - using conservative approach")
        return await conservative_fallback(group, trans)


async def handle_single_semantic_tag(group, ori, trans, semantic_element, element_analysis):
    """
    Handle case with one semantic tag.
    """
    semantic_index = semantic_element['index'] if 'index' in semantic_element else None
    
    # Find the semantic element in element_analysis
    if semantic_index is None:
        for i, info in element_analysis.items():
            if info['is_semantic']:
                semantic_index = i
                break
    
    if semantic_index is None:
        return await conservative_fallback(group, trans)
    
    semantic_info = element_analysis[semantic_index]
    original_semantic_content = semantic_info['text'].strip()
    
    print(f"Semantic tag <{semantic_info['tag_name']}>: '{original_semantic_content}'")
    
    # Try to find semantic content in translation using simple keyword matching
    trans_words = trans.lower().split()
    semantic_words = original_semantic_content.lower().split()
    
    # Find overlapping words
    matching_words = []
    for s_word in semantic_words:
        for t_word in trans_words:
            if len(s_word) > 2 and (s_word in t_word or t_word in s_word):
                matching_words.append(t_word)
    
    if matching_words:
        # Found matching content
        semantic_content_trans = " ".join(matching_words)
        print(f"Mapped semantic content: '{semantic_content_trans}'")
        
        # Apply to semantic tag
        group.elements[semantic_index].contents[group.cids[semantic_index]].replace_with(semantic_content_trans)
        
        # Remove semantic content from translation for remaining text
        remaining_trans = trans
        for word in matching_words:
            remaining_trans = remaining_trans.replace(word, "", 1).strip()
        remaining_trans = " ".join(remaining_trans.split())  # Clean up extra spaces
        
        # Put remaining text in first non-semantic position
        for i, info in element_analysis.items():
            if not info['is_semantic'] and i != semantic_index:
                group.elements[i].contents[group.cids[i]].replace_with(remaining_trans)
                break
        
        # Clear other positions
        for i, info in element_analysis.items():
            if i != semantic_index and (not info['is_semantic'] or group.elements[i].contents[group.cids[i]].string != remaining_trans):
                group.elements[i].contents[group.cids[i]].replace_with("")
        
        return 'S'
    
    else:
        # Couldn't map semantic content - use conservative
        print("Could not map semantic content - using conservative approach")
        return await conservative_fallback(group, trans)


async def handle_two_semantic_tags(group, ori, trans, semantic_elements, element_analysis):
    """
    Handle case with two semantic tags - the most problematic case.
    """
    # Get semantic tag information
    semantic_tags = []
    for i, info in element_analysis.items():
        if info['is_semantic']:
            semantic_tags.append({
                'index': i,
                'tag_name': info['tag_name'],
                'original_text': info['text'].strip(),
                'element': group.elements[i],
                'cid': group.cids[i]
            })
    
    if len(semantic_tags) != 2:
        return await conservative_fallback(group, trans)
    
    tag1, tag2 = semantic_tags[0], semantic_tags[1]
    
    print(f"Mapping two tags:")
    print(f"  Tag 1: <{tag1['tag_name']}>'{tag1['original_text']}'</{tag1['tag_name']}>")
    print(f"  Tag 2: <{tag2['tag_name']}>'{tag2['original_text']}'</{tag2['tag_name']}>")
    
    # Extract key words from each tag
    tag1_words = set(word.lower().strip('.,!?()') for word in tag1['original_text'].split() if len(word) > 2)
    tag2_words = set(word.lower().strip('.,!?()') for word in tag2['original_text'].split() if len(word) > 2)
    
    trans_words = trans.split()
    trans_words_lower = [word.lower().strip('.,!?()') for word in trans_words]
    
    # Find words in translation that match each tag
    tag1_matches = []
    tag2_matches = []
    tag1_positions = []
    tag2_positions = []
    
    for i, word in enumerate(trans_words):
        word_clean = word.lower().strip('.,!?()') 
        
        # Check if word matches tag1
        if any(tw in word_clean or word_clean in tw for tw in tag1_words):
            tag1_matches.append(word)
            tag1_positions.append(i)
        
        # Check if word matches tag2  
        elif any(tw in word_clean or word_clean in tw for tw in tag2_words):
            tag2_matches.append(word)
            tag2_positions.append(i)
    
    print(f"Tag1 matches: {tag1_matches}")
    print(f"Tag2 matches: {tag2_matches}")
    
    if tag1_matches and tag2_matches:
        # Both tags have matches - create mapping
        tag1_content = " ".join(tag1_matches).strip()
        tag2_content = " ".join(tag2_matches).strip()
        
        print(f"Final mapping:")
        print(f"  Tag 1 → '{tag1_content}'")
        print(f"  Tag 2 → '{tag2_content}'")
        
        # Apply mappings
        tag1['element'].contents[tag1['cid']].replace_with(tag1_content)
        tag2['element'].contents[tag2['cid']].replace_with(tag2_content)
        
        # Handle remaining text
        used_words = set(tag1_matches + tag2_matches)
        remaining_words = [word for word in trans_words if word not in used_words]
        remaining_text = " ".join(remaining_words).strip()
        
        print(f"Remaining text: '{remaining_text}'")
        
        # Put remaining text in first non-semantic position
        if remaining_text:
            for i, info in element_analysis.items():
                if not info['is_semantic']:
                    group.elements[i].contents[group.cids[i]].replace_with(remaining_text)
                    break
        
        # Clear other non-semantic positions
        placed_remaining = False
        for i, info in element_analysis.items():
            if not info['is_semantic']:
                if not placed_remaining and remaining_text:
                    group.elements[i].contents[group.cids[i]].replace_with(remaining_text)
                    placed_remaining = True
                else:
                    group.elements[i].contents[group.cids[i]].replace_with("")
        
        return 'S'  # Success with preserved semantics
    
    else:
        # Couldn't find good matches - use conservative approach
        print("Could not find good semantic matches - using conservative approach")
        return await conservative_fallback(group, trans)


async def handle_multiple_semantic_tags(group: InlineGroup, ori: str, trans: str, element_analysis):
    """
    Handle cases with multiple semantic tags (strong, em, etc.).
    """
    # Extract semantic tag contents from original and translation
    semantic_mappings = []
    
    for i, info in element_analysis.items():
        if info['is_semantic'] and info['text'].strip():
            semantic_mappings.append({
                'index': i,
                'original_text': info['text'].strip(),
                'tag_name': info['tag_name'],
                'element': group.elements[i],
                'cid': group.cids[i]
            })
    
    if len(semantic_mappings) <= 1:
        return await simple_multi_element_restruct(group, ori, trans, element_analysis)
    
    # Use AI to map semantic content
    try:
        semantic_prompt = create_semantic_mapping_prompt(ori, trans, semantic_mappings)
        
        chat = OpenaiAPIChat(
            model_name=conf.RESTRUCT_MODEL,
            system_prompt="You are an expert in HTML structure preservation and semantic content mapping."
        )
        
        response = ''
        async for chunk, stop_reason in chat.get_stream_aresponse(semantic_prompt, temperature=0.1):
            response += chunk
        
        semantic_result = as_json_obj(response)
        
        if semantic_result and validate_semantic_mapping(semantic_result, semantic_mappings):
            return await apply_semantic_mapping(group, trans, semantic_result, semantic_mappings, element_analysis)
        
    except Exception as e:
        print(f"Semantic mapping failed: {e}")
    
    # Fallback to conservative approach
    return await conservative_fallback(group, trans)


def create_semantic_mapping_prompt(ori: str, trans: str, semantic_mappings):
    """
    Create a focused prompt for semantic tag content mapping.
    """
    semantic_info = []
    for mapping in semantic_mappings:
        semantic_info.append(f"Index {mapping['index']}: '{mapping['original_text']}' (<{mapping['tag_name']} tag>)")
    
    prompt = f"""
CRITICAL SEMANTIC MAPPING TASK

Original text: "{ori}"
Translation: "{trans}"

Semantic elements that must be preserved:
{chr(10).join(semantic_info)}

RULES:
1. Each <strong>, <em>, <b>, <i> tag must contain semantically equivalent content
2. Identify which part of the translation corresponds to each original semantic element
3. Do NOT mix content between different semantic tags
4. If word order changes in translation, map accordingly

Example:
Original: "Add a <strong>Face Cover</strong> <strong>sticker</strong>"
Translation: "Aggiungi uno sticker Face Cover"
Mapping: Index 1 → "Face Cover", Index 3 → "sticker"

Return JSON mapping each index to its translated content:
{{
    "1": "translated_content_for_index_1",
    "3": "translated_content_for_index_3"
}}

Focus ONLY on semantic tags. Return valid JSON.
"""
    return prompt


def validate_semantic_mapping(result, semantic_mappings):
    """
    Validate that the semantic mapping result is reasonable.
    """
    if not isinstance(result, dict):
        return False
    
    expected_indices = {str(mapping['index']) for mapping in semantic_mappings}
    result_indices = set(result.keys())
    
    # Should have mappings for all semantic elements
    if not result_indices.issubset(expected_indices):
        return False
    
    # Check that no content is empty for important tags
    for index, content in result.items():
        if not content or not content.strip():
            print(f"Warning: Empty content for semantic tag at index {index}")
            return False
    
    return True


async def apply_semantic_mapping(group: InlineGroup, trans: str, semantic_result, semantic_mappings, element_analysis):
    """
    Apply the semantic mapping result to the HTML structure.
    """
    print(f"Applying semantic mapping: {semantic_result}")
    
    # Apply semantic tag mappings
    mapped_indices = set()
    
    for mapping in semantic_mappings:
        index_str = str(mapping['index'])
        if index_str in semantic_result:
            content = semantic_result[index_str]
            mapping['element'].contents[mapping['cid']].replace_with(content)
            mapped_indices.add(mapping['index'])
    
    # Handle remaining non-semantic elements
    remaining_text = trans
    for mapping in semantic_mappings:
        index_str = str(mapping['index'])
        if index_str in semantic_result:
            # Remove mapped content from remaining text
            mapped_content = semantic_result[index_str]
            remaining_text = remaining_text.replace(mapped_content, '', 1).strip()
    
    # Distribute remaining text to non-semantic elements
    non_semantic_indices = [i for i in element_analysis.keys() 
                           if not element_analysis[i]['is_semantic'] and i not in mapped_indices]
    
    if non_semantic_indices and remaining_text:
        # Put remaining text in the first non-semantic element
        first_non_semantic = non_semantic_indices[0]
        group.elements[first_non_semantic].contents[group.cids[first_non_semantic]].replace_with(remaining_text)
        
        # Clear other non-semantic elements
        for i in non_semantic_indices[1:]:
            group.elements[i].contents[group.cids[i]].replace_with("")
    
    return 'S'


async def simple_multi_element_restruct(group: InlineGroup, ori: str, trans: str, element_analysis):
    """
    Simple multi-element restructuring for cases without complex semantic tags.
    """
    print("Using simple multi-element restructuring")
    
    # Put complete translation in the first element, clear others
    group.elements[0].contents[group.cids[0]].replace_with(trans)
    
    for i in range(1, len(group.elements)):
        group.elements[i].contents[group.cids[i]].replace_with("")
    
    return 'C'  # Mark as compromise


async def conservative_fallback(group: InlineGroup, trans: str):
    """
    Conservative fallback approach when all else fails.
    """
    print("Using conservative fallback approach")
    
    # Put complete translation in the first position, clear all others
    group.elements[0].contents[group.cids[0]].replace_with(trans)
    
    for i in range(1, len(group.elements)):
        group.elements[i].contents[group.cids[i]].replace_with("")
    
    return 'F'  # Mark as fallback


async def group_fit_in_v3(
        group: InlineGroup,
        ori: str,
        trans: str
):
    """
    Enhanced group fitting function with semantic awareness.
    """
    print(f'=== Group Fit In V3 ===')
    print(f'Group text shreds: {group.text_shreds}')
    print(f'Original: {ori}')
    print(f'Translation: {trans}')
    
    # Skip if no translation needed
    if match_score(str(group), trans) >= 0.95:
        print("No translation needed - texts are nearly identical")
        return 'S'
    
    # Single element case
    if len(group) == 1:
        print("Single element case")
        str_content = group.elements[0].contents[group.cids[0]]
        str_content.replace_with(trans)
        return 'S'
    
    # Multi-element case with semantic awareness
    return await semantic_aware_restruct(group, ori, trans)


async def restruct_process(is_excel_translation, groups_in, groups_out, groups_map):
    """
    Enhanced restructuring process using the new v3 approach.
    """
    print(f"=== Restruct Process V3 ===")
    print(f"Processing {len(groups_in)} groups...")
    
    if is_excel_translation:
        # For Excel translation, just return the translated texts without DOM manipulation
        results = []
        for i, trans in groups_out.items():
            results.append(trans)
        print(f'Excel translation results: {results}')
        return results
    else:
        # For HTML/XML translation, perform the enhanced fitting back into the DOM
        fit_in_tasks = []
        for i, trans in groups_out.items():
            group = groups_map[i]
            print(f"Processing group {i}: {group.text_shreds[:2]}..." if len(group.text_shreds) > 2 else f"Processing group {i}: {group.text_shreds}")
            fit_in_tasks.append(group_fit_in_v3(group, groups_in[i], trans))
        
        results = await asyncio.gather(*fit_in_tasks, return_exceptions=True)
        
        # Log results summary
        success_count = sum(1 for r in results if r == 'S')
        compromise_count = sum(1 for r in results if r == 'C')
        failure_count = sum(1 for r in results if r == 'F')
        
        print(f"=== Restruct Results Summary ===")
        print(f"Success: {success_count}, Compromise: {compromise_count}, Failure: {failure_count}")
        
        return results


# Utility function for debugging
def debug_group_structure(group: InlineGroup):
    """
    Debug function to print detailed group structure information.
    """
    print("=== Group Structure Debug ===")
    print(f"Text shreds: {group.text_shreds}")
    print(f"CIDs: {group.cids}")
    
    for i, element in enumerate(group.elements):
        print(f"Element {i}: <{getattr(element, 'name', 'unknown')}> - ID: {id(element)} - Text: '{group.text_shreds[i] if i < len(group.text_shreds) else 'N/A'}'")
    
    # Check for duplicate elements
    element_ids = [id(element) for element in group.elements]
    unique_ids = set(element_ids)
    
    if len(unique_ids) < len(element_ids):
        print(f"WARNING: Duplicate elements detected!")
        for element_id in unique_ids:
            count = element_ids.count(element_id)
            if count > 1:
                indices = [i for i, eid in enumerate(element_ids) if eid == element_id]
                print(f"  Element ID {element_id} appears {count} times at indices: {indices}")
    
    print("=== End Debug ===")
