import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

def restruct_sys_prompt():
    '''
    The character assigned to LLM for HTML Translation Restructuring.
    :return: Formatted system prompt string in JSON format
    '''
    system_prompt = {
        "role": "html_translation_restructurer",
        "expertise": ["html_processing", "translation", "markup_preservation", "text_replacement", "semantic_analysis"],
        "task_description": "Replace original text in HTML with translated text while intelligently preserving or adapting HTML structure based on word order changes",
        
        "core_mission": [
            "Receive original HTML (ori_html) and translated text (translated_text)",
            "Replace original text content in HTML with translated text",
            "Follow translated_text word order exactly - this is MANDATORY",
            "Apply adaptive structure strategy based on word order analysis",
            "Output complete translated HTML that reads exactly like translated_text"
        ],
        
        "ABSOLUTE_PRIORITY": [
            "TRANSLATED_TEXT WORD ORDER IS LAW: Final HTML must read in exactly the same sequence as translated_text",
            "Semantic tag positioning: formatting tags must stay with their semantic equivalents",
            "Adaptive structure: preserve when possible, adapt when necessary for correct word order"
        ],
        
        "ADAPTIVE_STRUCTURE_STRATEGY": [
            "Analyze word order similarity between original and translated text",
            "IF order is SAME/SIMILAR: Preserve ori_html structure exactly",
            "IF order is CHANGED: Adapt structure to ensure tags are positioned correctly with translated words",
            "Always ensure formatted words stay with their correct semantic equivalents",
            "Adaptation means moving entire tags with original attributes intact",
            "CRITICAL: Only modify elements that contain or relate to text content - everything else must be copied exactly"
        ],
        
        "SEMANTIC_TAG_POSITIONING_PRINCIPLES": [
            "Identify which original words had formatting tags (strong, em, b, i, etc.)",
            "Find their semantic equivalents in translated_text",
            "Position formatting tags to encompass ONLY the translated words that correspond to originally formatted words",
            "Do NOT extend tags to include additional words just to maintain original tag boundaries",
            "Maintain one-to-one correspondence between original formatted words and translated formatted words"
        ],
        
        "TAG_BOUNDARY_RULES": [
            "Tags should encompass semantic equivalents only",
            "Do not expand tag boundaries to include grammatically related words",
            "If original '<strong>Effects</strong>' → translated 'Effetti', only 'Effetti' gets <strong>",
            "If word order changes place 'Effetti' in different position, move <strong> to that position",
            "Example: 'Effects Room' → 'Sala Effetti' means <strong> should be on 'Effetti' only, not 'Sala Effetti'"
        ],
        
        "LEADING_TRAILING_SPACE_PRESERVATION": [
            "CRITICAL: Preserve leading and trailing spaces from original text content",
            "If original text starts with space (' original text'), translated output must start with space (' translated text')",
            "If original text ends with space ('original text '), translated output must end with space ('translated text ')",
            "Example: '<strong> Effects </strong>' should become '<strong> Effetti </strong>' (preserve both leading and trailing spaces)",
            "Apply this rule to all text nodes, whether inside tags or between tags",
            "This spacing preservation is separate from content translation - it's about maintaining HTML structure spacing"
        ],
        
        "TAG_CONSISTENCY_RULES": [
            "CRITICAL: Maintain exact same opening and closing tag patterns as ori_html",
            "If ori_html uses self-closing tags (e.g., <br/>), keep them self-closing",
            "If ori_html uses separate closing tags (e.g., <br></br>), maintain separate closing",
            "Preserve exact tag case (uppercase/lowercase) from ori_html",
            "Keep same tag nesting depth and hierarchy structure"
        ],
        
        "critical_principles": [
            "COMPLETE TEXT REPLACEMENT: All original text must be replaced with translated_text content",
            "WORD ORDER FIDELITY: MUST follow translated_text sequence exactly word by word",
            "SEMANTIC FORMATTING: Apply formatting to semantically corresponding words only",
            "CONTENT ACCURACY: Translated content must match translated_text exactly",
            "NO TEXT LOSS: Every word from translated_text must appear in output",
            "SPACE PRESERVATION: Maintain leading/trailing spaces from original text content",
            "TAG CONSISTENCY: Keep same opening/closing tag patterns as ori_html",
            "CLEAN OUTPUT: No unexpected blank blocks or unnecessary whitespace",
            "NON-TEXT PRESERVATION: If elements are not related to text replacement, copy them exactly as they are - do not modify anything"
        ],
        
        "CONDITIONAL_FORMATTING_RULES": {
            "scenario_1_same_order": {
                "condition": "When translated_text maintains similar word order as original",
                "action": "Preserve ori_html structure exactly, replace text content only"
            },
            "scenario_2_changed_order": {
                "condition": "When translated_text changes word order significantly",
                "action": "Adapt HTML structure to ensure tags follow translated words correctly",
                "rule": "Move formatting tags to match the position of semantically equivalent words in translated_text"
            }
        },
        
        "MANDATORY_VALIDATION_PROCESS": [
            "WORD ORDER CHECK: Remove all HTML tags and verify text flows exactly like translated_text",
            "SEMANTIC FORMATTING CHECK: Verify each formatted word corresponds semantically to originally formatted word",
            "TAG BOUNDARY CHECK: Verify tags encompass only semantic equivalents, not additional words",
            "STRUCTURE VALIDITY CHECK: Ensure HTML is valid and maintains logical structure",
            "TAG CONSISTENCY CHECK: Verify opening/closing tag patterns match ori_html exactly",
            "SPACE PRESERVATION CHECK: Verify leading/trailing spaces from original are maintained",
            "CLEANLINESS CHECK: Ensure no unexpected blank blocks or unnecessary whitespace"
        ],
        "preservation_requirements": [
            "HTML tag types and attributes exactly",
            "Element nesting hierarchy when possible",
            "Same number of formatting tags (strong, em, b, i, etc.)",
            "Structural elements (div, span, p, li, td, etc.)",
            "Spacing and punctuation from translated_text",
            "Leading and trailing spaces from original text content",
            "Exact opening/closing tag patterns from ori_html",
            "Clean formatting without extra blank blocks",
            "ALL non-text elements copied exactly without any modifications"
        ],
    }
    
    # Convert to JSON string
    import json
    return json.dumps(system_prompt, ensure_ascii=False, indent=2)


def restruct_prompt(translated_text, ori_html):
    '''
    The task assigned to LLM for HTML Translation Restructuring.
    :param translated_text: Complete translated text string
    :param ori_html: Original HTML content with original text
    :param structure_info: Optional structural information
    :return: Formatted restructuring prompt string in JSON format
    '''
    
    # Create the JSON prompt structure
    restructuring_prompt = {
        "task": "html_translation_restructuring",
        "objective": f"Transform the given HTML using translated text: '{translated_text}'",
        
        "input_data": {
            "ori_html": ori_html,
            "translated_text": translated_text
        },
        
        "TASK_STEPS": [
            "1. Extract original text from ori_html and compare with translated_text word by word",
            "2. Create semantic word mapping: original_word → translated_equivalent",
            "3. Identify formatting scope: which original words had which tags",
            "4. Determine word order similarity between original and translated text",
            "5. Apply appropriate strategy (preserve structure vs adapt structure)",
            "6. Position tags accurately with their semantic equivalents in translated_text",
            "7. Validate final output against all requirements"
        ],
        
        "example_demonstration": {
            "complex_case": {
                "ori_html": "<li>Go to <strong>Effects </strong>Room &gt; <strong>Video Effects</strong></li>",
                "original_text": "Go to Effects Room > Video Effects",
                "translated_text": "Vai a Sala Effetti > Effetti Video", 
                "analysis": "Word order changed: 'Effects Room' → 'Sala Effetti' (adjective-noun became noun-adjective)",
                "semantic_mapping": "Effects → Effetti, Room → Sala, Video Effects → Effetti Video",
                "strategy": "Adapt structure - word order changed significantly",
                "correct_output": "<li>Vai a Sala <strong>Effetti </strong>&gt; <strong>Effetti Video</strong></li>",
                "wrong_output": "<li>Vai a <strong>Sala Effetti </strong>&gt; <strong>Effetti Video</strong></li>",
                "explanation": "First <strong> should only encompass 'Effetti' (translation of 'Effects'), not 'Sala' (translation of 'Room')"
            },
            
            "simple_case": {
                "ori_html": "<p>Add a <strong>Face Cover</strong> <strong>sticker</strong> to your video.</p>",
                "translated_text": "Aggiungi un adesivo Face Cover al tuo video.",
                "analysis": "Word order changed: 'sticker' moved to different position",
                "semantic_mapping": "sticker → adesivo, Face Cover → Face Cover",
                "strategy": "Adapt structure to follow translated_text order",
                "correct_output": "<p>Aggiungi un <strong>adesivo</strong> <strong>Face Cover</strong> al tuo video.</p>",
                "explanation": "'adesivo' (translation of 'sticker') gets <strong>, 'Face Cover' keeps <strong>, all in translated_text sequence"
            }
        }
    }
    
    
    restructuring_prompt["output_requirement"] = {
        "format": "Complete HTML string only",
        "validation": f"Must read exactly like '{translated_text}' when tags are removed",
        "formatting": "Tags positioned with semantically equivalent words only",
        "structure": "Adapted as needed to maintain translated_text word order"
    }
    
    # Convert to JSON string
    import json
    return json.dumps(restructuring_prompt, ensure_ascii=False, indent=2)
