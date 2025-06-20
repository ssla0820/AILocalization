import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))


def image_analysis_sys_prompt():
    '''
    The character assigned to LLM for analyze the image for asist string translation.
    :return: Formatted system prompt string in JSON format
    '''
    import json
    
    
    system_prompt_json = {
        "role": "Image Analysis Expert",
    }

    # Convert to JSON string
    system_prompt_json_str = json.dumps(system_prompt_json, ensure_ascii=False, indent=2)

    return system_prompt_json_str


def image_analysis_prompt(target_string):
    '''
    The task assigned to LLM for provide prompts that would help ensure an accurate translation.
    :param target_string: The target string to be translated
    :param image_path: Path to the image file that contains the text to be translated (a list of image paths)
    :return: Formatted image analysis prompt string in JSON format
    '''

    translation_prompt = {
        "task": "image_analysis for translation",
        "target_string": target_string,
        "output_format": "a string of concise description",
        # "questions": [
        #     "1. Which UI element is the string applied to? (e.g., button, label, drop-down list option, title, etc.)",
        #     f"2. Describe the context of target string in the image that would help ensure an accurate translation."
        # ]
        "questions": [
            "Which UI element is the string applied to? (e.g., button, label, drop-down list option, title, etc.) and describe the context of target string in the image that would help ensure an accurate translation."
        ]
    }
    

    # Convert to JSON string
    import json
    prompt_json_str = json.dumps(translation_prompt, ensure_ascii=False, indent=2)
    
    return prompt_json_str
