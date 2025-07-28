import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

def restruct_sys_prompt():
    '''
    The character assigned to LLM for Restructuring.
    :return: Formatted system prompt string in JSON format
    '''
    system_prompt = {
        "role": "translation_restructuring_expert",
        "expertise": ["translation", "markup_language", "json_structure"],
        "task_description": "Split translation into parts and fit each part into the fields in JSON",
        "preservation_requirements": [
            "original structure",
            "element order",
            "list structure",
            "table format",
            "nested elements"
        ]
    }
    
    # Convert to JSON string
    import json
    return json.dumps(system_prompt, ensure_ascii=False, indent=2)


def restruct_prompt(trans_str, ori_str, shreds_str, structure_info=None, map_seg_out=None):
    '''
    The task assigned to LLM for Restructuring.
    :param trans_str: Translated string
    :param ori_str: Original string
    :param shreds_str: Shredded string (JSON format)
    :param structure_info: Optional JSON string containing structural information about the elements
    :return: Formatted restructuring prompt string in JSON format
    '''
    
    # Create the JSON prompt structure
    restructuring_prompt = {
        "task": "translation_restructuring",
        "translation": trans_str,
        "original_text": ori_str,
        "segments_json": shreds_str,
        "map_segments_json": map_seg_out if map_seg_out else None,
        "has_structural_context": structure_info is not None
    }
    if structure_info:
        restructuring_prompt["structural_context"] = structure_info
        restructuring_prompt["structural_guidelines"] = [
            "Pay close attention to hierarchical relationships between elements",
            "The order should follow 'translation', not maintain exact order of text fragments in the original structure",
            "Do not move text between different list items or paragraphs",
            # "Preserve hierarchical nesting of elements",
            "Each segment ID corresponds to content within a specific XML/HTML element",
            "Element boundaries must be strictly preserved - do not mix content between different elements",
            "Consider element attributes and types when distributing translated text"
        ]
        restructuring_prompt["requirements"] = [
        "Each segment must receive appropriate translated text",
        # "No text should be moved between different list items or structural elements",
        "No characters in the translation should be dropped",
        # "Text order must match the original structure perfectly",
        # "Text order must match 'translation' order, not the original structure",
        "Text order should follow the order of 'translation', not the structure_info",
        "Text format should follow 'sturcutre_info' content",
        "The result must be valid JSON with the same keys as the input",
        "CRITICAL: Do not mix content between different XML elements",
        "CRITICAL: Each segment corresponds to content within a specific XML element boundary",
        "CRITICAL: Maintain the exact semantic boundaries - text that belongs to one element should not leak into another element's content"
    ]
    
    restructuring_prompt["output_format"] = "Valid JSON object with the same keys as the input"
    
    # Convert to JSON string
    import json
    return json.dumps(restructuring_prompt, ensure_ascii=False, indent=2)

def map_sys_prompt():
    system_prompt = {
        "role": "translation_mapper",
        "instructions": "Map translated text into source_segments structure by analyzing word-by-word semantic correspondence",
        
        "input": {
            "source_segments": "a dict whose keys are segment IDs and whose values are source text fragments",
            "source_text": "the complete original text string",
            "translated_text": "the complete translated text string"
        },
        
        "critical_requirements": [
            "OUTPUT MUST BE IN TARGET LANGUAGE: Fill source_segments structure with TRANSLATED content",
            "WORD-BY-WORD MAPPING: Establish semantic correspondence between source_text and translated_text",
            "STRUCTURE PRESERVATION: Use source_segments as the structural framework",
            "COMPLETE COVERAGE: All translated content must be distributed into the structure",
            "SEMANTIC ACCURACY: Ensure translated words go to semantically appropriate segments"
        ],
        
        "four_step_process": [
            "1. ANALYZE TEXTS: Read source_text and translated_text to understand complete meaning",
            "2. WORD MAPPING: Map source_text and translated_text word by word by semantic meaning",
            "3. SEGMENT ANALYSIS: Compare source_segments structure with source_text relationships",
            "4. STRUCTURE FILLING: Place corresponding translated_text content into source_segments framework"
        ],
        
        "mapping_principles": [
            "Identify semantic relationships between source and translated words",
            "Preserve the structural boundaries defined by source_segments",
            "Ensure each segment receives semantically appropriate translated content",
            "Maintain proper spacing and punctuation from translated_text"
        ],
        
        "output_requirements": [
            "Return JSON with same keys as source_segments",
            "Values must be TRANSLATED text fragments, not source language",
            "Preserve source_segments structural framework",
            "Ensure complete coverage of translated_text with no loss"
        ]
    }

    # Convert to JSON string
    import json
    return json.dumps(system_prompt, ensure_ascii=False, indent=2)


def map_prompt(trans_str, ori_str, shreds_str):
    prompt = {
        "task": "map_translated_content_to_source_segments_structure", 
        "CRITICAL_OUTPUT_REQUIREMENT": "Fill source_segments structure with TRANSLATED content using semantic word mapping",
        
        "input_data": {
            "source_text": ori_str,
            "source_segments": shreds_str,
            "translated_text": trans_str
        },
        
        "FOUR_STEP_MAPPING_PROCESS": [
            "1. READ AND ANALYZE: Read source_text and translated_text to understand complete meaning and context",
            "2. WORD-BY-WORD MAPPING: Map source_text and translated_text word by word based on semantic meaning",
            "3. SEGMENT RELATIONSHIP ANALYSIS: Compare how source_segments relate to and fragment the source_text",
            "4. STRUCTURE FILLING: Place corresponding translated_text content into the source_segments framework"
        ],
        
        "detailed_instructions": {
            "step_1_analysis": {
                "description": "Understand complete text meaning",
                "action": f"Read '{ori_str}' and '{trans_str}' to understand full context and meaning"
            },
            "step_2_word_mapping": {
                "description": "Establish word-level semantic correspondence",
                "action": f"Map each word/phrase in '{ori_str}' to its semantic equivalent in '{trans_str}'"
            },
            "step_3_segment_analysis": {
                "description": "Understand structural relationships",
                "action": "Analyze how source_segments break down the source_text into fragments"
            },
            "step_4_structure_filling": {
                "description": "Fill structure with translated content",
                "action": "Place semantically corresponding translated content into each source_segments position"
            }
        },
        
        "semantic_mapping_guidelines": [
            "Identify which translated words correspond to which source words by meaning",
            "Consider context and semantic relationships, not just literal word order",
            "Ensure proper nouns and technical terms are correctly mapped",
            "Maintain grammatical structure appropriate for the target language"
        ],
        
        "structure_preservation": [
            "Use source_segments keys exactly as provided",
            "Respect the structural boundaries defined by source_segments",
            "Each segment should receive semantically appropriate translated content",
            "Maintain proper spacing and punctuation within segments"
        ],
        
        "example_workflow": {
            "given_source_text": "Add a Face Cover sticker",
            "given_translated_text": "Aggiungi un adesivo Face Cover", 
            "given_source_segments": {"0": "Add a ", "1": "Face Cover", "2": " ", "3": "sticker"},
            "step_1_analysis": "Understand: English -> Italian translation",
            "step_2_word_mapping": "Add->Aggiungi, a->un, Face Cover->Face Cover, sticker->adesivo",
            "step_3_segment_analysis": "Segment 0: prefix, Segment 1: semantic term, Segment 2: space, Segment 3: semantic term",
            "step_4_result": {"0": "Aggiungi un ", "1": "Face Cover", "2": " ", "3": "adesivo"},
            "explanation": "Translated content placed in structurally appropriate segments"
        },
        
        "critical_requirements": [
            "OUTPUT LANGUAGE: Must be in target language (translated), not source language",
            "SEMANTIC ACCURACY: Ensure translated content is semantically appropriate for each segment",
            "COMPLETE COVERAGE: All translated content must be distributed",
            "STRUCTURE RESPECT: Follow source_segments framework exactly"
        ],
        
        "validation_checklist": [
            "All output values are in target language",
            "Segment keys match input keys exactly",
            "All translated content is covered without loss",
            "Semantic relationships are preserved",
            "Structural boundaries are respected"
        ],
        
        "output_format": "Valid JSON object with same keys as source_segments, filled with semantically appropriate translated content"
    }
    
    # Convert to JSON string
    import json
    return json.dumps(prompt, ensure_ascii=False, indent=2)


def sys_reorder_group_out_prompt():
    """
    System prompt for reordering groups_map based on translated text word order.
    """
    system_prompt = {
        "role": "translation_structure_reorderer",
        "expertise": ["translation", "html_structure", "array_synchronization", "word_order_analysis"],
        "task_description": "Reorder translated_text_shreds, cids, and elements_info arrays to match trans_str word order while maintaining structural correspondence",
        
        "CORE_MISSION": [
            "Use original structure as reference baseline",
            "Reorder translated content to match trans_str word sequence exactly", 
            "Maintain synchronization between text_shreds, cids, and elements_info arrays",
            "Update elements_info to reflect translated language content"
        ],
        
        "UNDERSTANDING": {
            "original_text_shreds": "Reference structure - shows original order and relationships",
            "translated_text_shreds": "Translated content - needs reordering to match trans_str",
            "trans_str": "Target word sequence - the GOLD STANDARD for final order",
            "cids": "Content indices - must be reordered with text_shreds",
            "elements_info": "HTML element info - must be updated to translated language and reordered"
        },
        
        "REORDERING_PRINCIPLES": [
            "REFERENCE FIRST: Start with original structure as baseline",
            "COMPARE AND ANALYZE: Identify differences between current translated order and trans_str order",
            "REORDER TEXT: Arrange translated_text_shreds to match trans_str sequence",
            "SYNCHRONIZE ARRAYS: Apply same reordering to cids and elements_info",
            "UPDATE LANGUAGE: Convert elements_info content to translated language",
            "VALIDATE RESULT: Ensure concatenated result flows like trans_str"
        ],
        
        "CRITICAL_RULES": [
            "TRANS_STR IS THE WORD ORDER AUTHORITY - follow its sequence exactly",
            "MAINTAIN ARRAY CORRESPONDENCE - all arrays must be reordered together",
            "PRESERVE ALL CONTENT - no text should be lost or duplicated",
            "UPDATE LANGUAGE CONTEXT - elements_info should reflect translated language",
            "EXACT SPACING - preserve spacing and punctuation from trans_str"
        ],
        
        "ARRAY_SYNCHRONIZATION": [
            "reordered_text_shreds[i] corresponds to reordered_cids[i]",
            "reordered_text_shreds[i] corresponds to reordered_elements_info[i]",
            "All three arrays must have the same length",
            "Reordering mapping must be applied consistently to all arrays"
        ],
        
        "VALIDATION_REQUIREMENTS": [
            "Concatenated reordered_text_shreds must read exactly like trans_str",
            "All arrays must maintain equal length and correspondence",
            "No content should be missing from trans_str",
            "Spacing and punctuation must match trans_str exactly"
        ],
        
        "OUTPUT_SPECIFICATION": {
            "format": "Valid JSON object only",
            "required_fields": {
                "reordered_text_shreds": "Dictionary with reordered translated text matching trans_str sequence",
                "reordered_cids": "List of cids reordered to correspond with text_shreds",
                "reordered_elements_info": "List of element info reordered and updated for translated language",
                "reordering_explanation": "Brief explanation of the reordering logic"
            }
        }
    }
    
    # Convert to JSON string
    import json
    return json.dumps(system_prompt, ensure_ascii=False, indent=2)


def reorder_group_out_prompt(trans_str, original_text_shreds, translated_text_shreds, cids, elements_info):
    """
    Prompt for reordering groups_map based on translated text word order.
    """
    import json
    
    reorder_prompt = {
        "task": "reorder_groups_map_for_translation",
        "objective": "Reorder translated_text_shreds, cids, and elements_info to match trans_str word order while maintaining structural correspondence",
        
        "input_data": {
            "trans_str": trans_str,
            "original_text_shreds": original_text_shreds, 
            "translated_text_shreds": translated_text_shreds,
            "cids": cids,
            "elements_info": elements_info,
        },
        
        "STEP_BY_STEP_INSTRUCTIONS": [
            "1. REFERENCE: Use original_text_shreds, cids, elements_info as the baseline structure and order",
            "2. COMPARE: Analyze the difference between translated_text_shreds order and trans_str word sequence",
            "3. REORDER TRANSLATED_TEXT_SHREDS: Adjust translated_text_shreds order to match trans_str sequence exactly",
            "4. SYNC CIDS: Reorder cids array to correspond with the newly ordered translated_text_shreds",
            "5. UPDATE ELEMENTS_INFO: Change element content to translated language",
            "6. SYNC ELEMENTS_INFO: Reorder elements_info to correspond with the newly ordered translated_text_shreds"
        ],
        
        "DETAILED_PROCESS": {
            "step_1_reference": {
                "description": "Use original structure as baseline",
                "action": "Keep original_text_shreds, cids, elements_info as reference for structural relationships"
            },
            "step_2_comparison": {
                "description": "Compare translated order vs trans_str order",
                "action": f"Identify how translated_text_shreds should be reordered to match: '{trans_str}'"
            },
            "step_3_reorder_text": {
                "description": "Reorder translated text fragments",
                "action": "Arrange translated_text_shreds so that when concatenated, they flow exactly like trans_str"
            },
            "step_4_sync_cids": {
                "description": "Synchronize cids with reordered text",
                "action": "Reorder cids array to maintain correspondence with newly ordered translated_text_shreds"
            },
            "step_5_update_elements": {
                "description": "Convert elements_info to translated language",
                "action": "Update element content/attributes to reflect translated language if applicable"
            },
            "step_6_sync_elements": {
                "description": "Synchronize elements_info with reordered text",
                "action": "Reorder elements_info to maintain correspondence with newly ordered translated_text_shreds"
            }
        },
        
        "CRITICAL_REQUIREMENTS": [
            f"WORD ORDER TARGET: Final translated_text_shreds must flow exactly like: '{trans_str}'",
            "STRUCTURAL INTEGRITY: Maintain cids and elements_info correspondence with text_shreds",
            "ARRAY SYNCHRONIZATION: All three arrays (text_shreds, cids, elements_info) must be reordered together",
            "CONTENT PRESERVATION: No translated content should be lost or duplicated",
            "SPACING PRESERVATION: Maintain exact spacing and punctuation from trans_str"
        ],
        
        "REORDERING_STRATEGY": [
            f"1. Parse trans_str word by word: '{trans_str}'",
            "2. For each word/phrase in trans_str sequence, identify which translated_text_shreds contains it",
            "3. Create mapping: original_index -> new_position_based_on_trans_str_order",
            "4. Apply same reordering mapping to cids and elements_info arrays",
            "5. Ensure all arrays maintain their structural relationships"
        ],
        
        "VALIDATION_CHECKS": [
            "Concatenated reordered_text_shreds must read exactly like trans_str",
            "reordered_cids length must equal reordered_text_shreds length",
            "reordered_elements_info length must equal reordered_text_shreds length",
            "Array indices must maintain one-to-one correspondence",
            "No content should be lost or duplicated"
        ],
        
        "EXAMPLE_WORKFLOW": {
            "given_trans_str": "Aggiungi uno adesivo Face Cover",
            "if_translated_text_shreds_are": {"0": "Aggiungi uno ", "1": "Face Cover", "2": " ", "3": "adesivo"},
            "and_trans_str_order_is": "Aggiungi uno adesivo Face Cover",
            "then_reorder_to": {"0": "Aggiungi uno ", "1": "adesivo", "2": " ", "3": "Face Cover"},
            "explanation": "Reorder to match trans_str sequence: 'Aggiungi uno adesivo Face Cover'"
        },
        
        "OUTPUT_FORMAT": {
            "reordered_text_shreds": "Dictionary with same keys, but values reordered to match trans_str sequence",
            "reordered_cids": "List reordered to correspond with reordered_text_shreds",
            "reordered_elements_info": "List reordered and updated to correspond with reordered_text_shreds (with translated language content)",
            "reordering_explanation": "Brief explanation of how the reordering matches trans_str word sequence"
        },
        
        "FINAL_VALIDATION": {
            "test_concatenation": "Join all reordered_text_shreds values and verify it reads exactly like trans_str",
            "test_array_sync": "Verify all three arrays have the same length and corresponding indices",
            "test_content_coverage": "Verify all translated content from trans_str is preserved"
        }
    }
    
    return json.dumps(reorder_prompt, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print("=====================Reordering system prompt:")
    print(sys_reorder_group_out_prompt())
    print("=====================Reorder group out prompt:")
    # trans_str = "Aggiungi un adesivo Face Cover (ad es. Face Cover 02, Face Cover 04, ecc.) dalla Overlays Room a una traccia inferiore (sotto il video) nella timeline."
    # shreds_in = {'0': 'Add a ', '1': 'Face Cover', '2': ' ', '3': 'sticker ', '4': '(e.g.,                  Face Cover 02, Face Cover 04, etc)', '5': ' ', '6': 'from the                  ', '7': 'Overlays ', '8': 'Room to a lower track (below the                  video) in the timeline.'}











    # ]        {"index": 4, "tag_name": "span", "element_id": "444555666", "attributes": {}, "is_semantic": False}        {"index": 3, "tag_name": "strong", "element_id": "111222333", "attributes": {}, "is_semantic": True},        {"index": 2, "tag_name": "span", "element_id": "555666777", "attributes": {}, "is_semantic": False},        {"index": 1, "tag_name": "strong", "element_id": "987654321", "attributes": {}, "is_semantic": True},        {"index": 0, "tag_name": "strong", "element_id": "123456789", "attributes": {}, "is_semantic": True},    elements_info = [    cids = [0, 0, 2, 0, 4, 0, 6, 0, 8]    shreds_out = {'0': 'Aggiungi un ', '1': 'Face Cover', '2': ' ', '3': 'adesivo ', '4': '(ad es. Face Cover 02, Face Cover 04, ecc.)', '5': ' ', '6': 'dalla ', '7': 'Overlays ', '8': 'Room a una traccia inferiore (sotto il video) nella timeline.'}    print(reorder_group_out_prompt(trans_str, shreds_in, shreds_out, cids, elements_info))
