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

def map_sys_prompt():
    system_prompt =  {
        "instructions": "Map each word or phrase in `source_segments` to its occurrences in `translated_text`, and verify full coverage of the translated text.",
        "input": {
            "source_segments": "a dict whose keys are segment IDs and whose values are lists of source words/phrases",
            "source_text": "the original text string (for reference)",
            "translated_text": "the translated text string to be mapped"
        },
        "process": [
            "Flatten and deduplicate all words/phrases from `source_segments` values",
            "For each source word/phrase, locate every occurrence in `translated_text`, recording start indices and counts",
            "Determine which spans of `translated_text` are not covered by any match"
        ],
        "example_input": "{\n\"0\": \"Go to \",\n\"1\": \"Effects \",\n\"2\": \"Room > \",\n\"3\": \"Video                    Effects \",\n\"4\": \"> \",\n\"5\": \"Face Blur\",\n\"6\": \".\"\n}",
        "example_output": "{\n\"0\": \"Vai a \",\n\"1\": \"Sala effetti \",\n\"2\": \"> \",\n\"3\": \"Effetti video \",\n\"4\": \"> \",\n\"5\": \"Sfocatura volto\",\n\"6\": \".\",\n\"translation\": \"Vai a Sala effetti > Effetti video > Sfocatura volto.\"\n}",
        "Note":[
            "The `source_segments` keys are segment IDs that correspond to specific parts of the original text.",
            "The `translated_text` should be a complete translation of the original text, with no missing segments.",
            "The output should be a JSON object with the same keys as `source_segments`, where each key maps to the corresponding translated word/phrase.",
            "The words/phrases in `translated_text` must be mapped to the segments in `source_segments` without losing any information or duplication.",
        ]
    }

    
    # Convert to JSON string
    import json
    return json.dumps(system_prompt, ensure_ascii=False, indent=2)


def map_prompt(trans_str, ori_str, shreds_str):
    prompt = {
        "source_text": ori_str,
        "source_segments": shreds_str,
        "translated_text": trans_str,
        }
    
    # Convert to JSON string
    import json
    return json.dumps(prompt, ensure_ascii=False, indent=2)

