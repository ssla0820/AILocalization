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


def restruct_prompt(trans_str, ori_str, shreds_str, structure_info=None):
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
        "has_structural_context": structure_info is not None
    }
    if structure_info:
        restructuring_prompt["structural_context"] = structure_info
        restructuring_prompt["structural_guidelines"] = [
            "Pay close attention to hierarchical relationships between elements",
            "Maintain exact order of text fragments in the original structure",
            "Do not move text between different list items or paragraphs",
            "Preserve hierarchical nesting of elements",
            "Each segment ID corresponds to content within a specific XML/HTML element",
            "Element boundaries must be strictly preserved - do not mix content between different elements",
            "Consider element attributes and types when distributing translated text"
        ]
        restructuring_prompt["requirements"] = [
        "Each segment must receive appropriate translated text",
        "No text should be moved between different list items or structural elements",
        "No characters in the translation should be dropped",
        "Text order must match the original structure perfectly",
        "The result must be valid JSON with the same keys as the input",
        "CRITICAL: Do not mix content between different XML elements",
        "CRITICAL: Each segment corresponds to content within a specific XML element boundary",
        "CRITICAL: Maintain the exact semantic boundaries - text that belongs to one element should not leak into another element's content"
    ]
    
    restructuring_prompt["output_format"] = "Valid JSON object with the same keys as the input"
    
    # Convert to JSON string
    import json
    return json.dumps(restructuring_prompt, ensure_ascii=False, indent=2)
