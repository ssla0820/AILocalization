# Translate HTML/XML Project - Module Architecture

## Overview
This document describes the complete module architecture for the Translation system, with `batch_processor.py` as the main entry point. The system is designed with a layered architecture that supports batch translation processing, quality review, and various utility tools.

## System Architecture Tree

```
batch_processor.py (Main Entry Point)
├── chat/
│   └── openai_api_chat.py                  # OpenAI API communication
├── config/
│   ├── __init__.py                         # Configuration package initialization
│   ├── translate_config.py                 # Main translation configuration
│   ├── gemini_api_conf.py                  # Gemini API configuration
│   └── openai_api_conf.py                  # OpenAI API configuration
├── data/                                   # Data storage directory
├── interface/
│   ├── run_interface.py                    # User interface entry point
│   ├── interface.py                        # Web interface implementation
│   ├── static/                            # Static web assets
│   └── templates/                         # HTML templates
├── logs/                                   # Log files directory
├── pages/
│   └── general_functions.py               # Shared utility functions
├── prompts/
│   ├── translate_prompts.py               # Translation prompts
│   ├── restruct_prompts.py                # Restructuring prompts
│   └── review_prompts.py                  # Review prompts
├── review/
│   └── review.py                          # Translation quality review
├── tool/                                  # Utility tools (dynamically loaded)
│   ├── Translation_Memory_Related/
│   │   ├── tmx_csv_convertor.py           # TMX to Excel converter
│   │   ├── create_json_from_xlsx.py       # Excel to JSON converter
│   │   └── combine_xlsx_files.py          # Excel file combiner
│   ├── Common_Usage_Table/
│   │   ├── create_region_table.py         # Regional table creator
│   │   └── create_region_table2.py        # Regional table creator v2
│   ├── Source_File_Related/
│   │   └── copy_source.py                 # Source file copy utility
│   ├── Prompt/
│   │   └── generate_general_prompts.py    # General prompt generator
│   ├── Refer_Text_n_Image_Related/
│   │   ├── get_segment.py                 # Segment extractor
│   │   └── interface/                     # Sub-interface system
│   └── interface/
│       ├── interface.py                   # Tool interface web app
│       ├── static/                        # Tool interface assets
│       └── templates/                     # Tool interface templates
└── translate/
    ├── translate.py                       # Main translation engine
    ├── restruct.py                        # Structure reconstruction
    └── translation_memory/
        ├── search_similar_pair.py         # Similar pair search
        └── classify_string.py             # String classification
```

## Layer Description

### Layer 1: Entry Point
- **`batch_processor.py`** - Main batch processing controller that orchestrates the entire translation workflow

### Layer 2: Core System Folders

#### Configuration Layer (`config/`)
- **`translate_config.py`** - Main translation configuration and settings
- **`openai_api_conf.py`** - OpenAI API configuration
- **`gemini_api_conf.py`** - Gemini API configuration

> **Note**: For OpenAI API pricing and model information, visit: https://platform.openai.com/docs/pricing

#### Communication Layer (`chat/`)
- **`openai_api_chat.py`** - AI conversation handling and API communication

#### Interface Layer (`interface/`)
- **`run_interface.py`** - Primary user interface entry point
- **`interface.py`** - Web interface implementation
- **`static/`** - Static web assets (CSS, JS, images)
- **`templates/`** - HTML template files

#### Utility Layer (`pages/`)
- **`general_functions.py`** - Shared utility functions used across modules

#### Translation Engine (`translate/`)
- **`translate.py`** - Core translation engine and main processing logic
- **`restruct.py`** - Structure reconstruction for maintaining file formatting
- **`translation_memory/`** - Translation memory management
  - **`search_similar_pair.py`** - Similar translation pair search
  - **`classify_string.py`** - String classification and processing

#### Prompt Engineering (`prompts/`)
- **`translate_prompts.py`** - Translation-specific prompts for AI models
- **`restruct_prompts.py`** - Restructuring prompts for formatting
- **`review_prompts.py`** - Quality review and evaluation prompts

#### Quality Assurance (`review/`)
- **`review.py`** - Translation quality review and evaluation

#### Storage (`data/` & `logs/`)
- **`data/`** - Data storage directory for processed files and databases
- **`logs/`** - System logging and batch processing logs

### Layer 3: Tool Ecosystem (`tool/`)
Specialized utility tools accessible through the web interface:

#### Translation Memory Tools
- **`tmx_csv_convertor.py`** - Converts TMX files to Excel format
- **`create_json_from_xlsx.py`** - Converts Excel files to JSON format
- **`combine_xlsx_files.py`** - Combines multiple Excel files

#### Common Usage Table Tools
- **`create_region_table.py`** - Creates regional terminology tables
- **`create_region_table2.py`** - Enhanced regional table creator

#### Source File Tools
- **`copy_source.py`** - Handles source file copying operations

#### Prompt Tools
- **`generate_general_prompts.py`** - Generates general-purpose prompts

#### Reference Tools
- **`get_segment.py`** - Extracts text segments for reference
- **`interface/`** - Sub-interface system for tool management

## Translation Workflow

The system follows a structured workflow that processes files through multiple stages for high-quality translation output:

### Step 1: Initialize System
```
Start batch_processor.py
├── Launch interface/run_interface.py
├── Load config/translate_config.py
└── Display web interface for configuration
```

### Step 2: User Configuration
User provides the following inputs through the web interface:
- **Source File(s)**: HTML, XML, or Excel files to be translated
- **Target Language**: Destination language for translation
- **Translation Memory**: Database of previous translations (optional)
- **Glossary**: Terminology mapping table (optional)
- **Refer Text and Image**: Reference materials and context (optional)
- **Regional Table**: Region-specific terminology and phrases (optional)

### Step 3: Initialize Processing
```
batch_processor.py → process_batch_file()
├── Load heavy imports (translate_main, pandas, openpyxl, etc.)
├── Create output directories
├── Initialize logging in logs/
└── Validate input files and configurations
```

### Step 4: File Segmentation
```
translate/translate.py → main()
├── Detect file encoding using pages/general_functions.py
├── Parse file structure (HTML/XML/Excel)
├── Extract translatable text segments
├── Create InlineGroup objects for each text segment
└── Maintain original structure mapping
```

### Step 5: Translation Process (Sentence-by-Sentence)
For each text segment:

```
translate/translate.py → translate_groups()
├── Load relevant resources:
│   ├── translation_memory/search_similar_pair.py (find similar translations)
│   ├── pages/general_functions.py → get_relevant_specific_names() (apply glossary)
│   ├── Regional table lookup (if provided)
│   └── Reference text and image context (if provided)
├── Generate translation prompt:
│   ├── prompts/translate_prompts.py (get appropriate prompt template)
│   ├── Include context from translation memory
│   ├── Include glossary terms
│   └── Include reference materials
├── Send to AI model:
│   ├── chat/openai_api_chat.py → get_stream_aresponse()
│   ├── Process AI response
│   └── Extract translated text
└── Store translated segment
```

### Step 6: Quality Review (Optional)
```
review/review.py → main()
├── Load review prompts from prompts/review_prompts.py
├── Compare source and translated text
├── Generate quality score and feedback
├── chat/openai_api_chat.py → send review request to AI
├── Analyze translation quality
└── Generate review report (if enabled)
```

### Step 7: Structure Reconstruction
For HTML/XML files:

```
translate/restruct.py
├── Load restructuring prompts from prompts/restruct_prompts.py
├── Map translated segments back to original structure
├── Maintain HTML/XML tags and formatting
├── Preserve element attributes and hierarchy
└── Generate final translated file
```

### Step 8: Output Generation
```
batch_processor.py
├── Save translated file(s) to output directory
├── Generate translation results Excel report
├── Create review report (if review enabled)
├── Merge multi-language Excel files (if applicable)
├── Log process results to logs/ directory
└── Display completion summary
```

## Workflow Module Dependencies

Each workflow step utilizes specific modules:

| Step | Primary Modules | Supporting Modules |
|------|----------------|-------------------|
| 1. Initialize | `batch_processor.py`, `interface/run_interface.py` | `config/translate_config.py` |
| 2. Configuration | `interface/interface.py` | `config/`, `pages/general_functions.py` |
| 3. Processing Setup | `batch_processor.py` | `pages/general_functions.py`, `config/` |
| 4. Segmentation | `translate/translate.py` | `pages/general_functions.py` |
| 5. Translation | `translate/translate.py`, `chat/openai_api_chat.py` | `prompts/translate_prompts.py`, `translation_memory/` |
| 6. Review | `review/review.py` | `prompts/review_prompts.py`, `chat/openai_api_chat.py` |
| 7. Restructure | `translate/restruct.py` | `prompts/restruct_prompts.py` |
| 8. Output | `batch_processor.py` | `pages/general_functions.py` |

## How to Extend the System

The system is designed to be easily extensible for new products and languages. Follow these procedures to add support for new products or languages:

## Extending Product Support

### Step 1: Add Product Name Option in Interface
1. **Edit `interface/interface.py`**:
   - Locate the product selection dropdown in the HTML template
   - Add your new product option to the product list
   - Example: Add "PhotoDirector Mobile" to existing options

2. **Update Interface Templates**:
   - Modify `interface/templates/index.html`
   - Add the new product option in the product selection dropdown:
   ```html
   <option value="PDM">PhotoDirector Mobile</option>
   ```

### Step 2: Add Product-Software Type Mapping
1. **Edit `config/translate_config.py`**:
   - Locate the `SOFTWARE_TYPE_MAP` dictionary
   - Add mapping between your product code and software type
   ```python
   SOFTWARE_TYPE_MAP = {
       'PDR': 'Video Editing Software',
       'PHD': 'Image Editing Software',
       'PDM': 'Photo Editing Software on Mobile',  # New mapping
   }
   ```

### Step 3: Modify Translation Prompts (Optional)
If the translation style differs from PC products (e.g., mobile vs desktop terminology):

1. **Edit `prompts/translate_prompts.py`**:
   - Add conditional logic for mobile-specific terminology
   - Create mobile-specific prompt templates if needed
   ```python
   def get_translation_prompt(software_type, source_lang, target_lang):
       if "Mobile" in software_type:
           # Use mobile-specific prompts
           return mobile_translation_prompt(source_lang, target_lang)
       else:
           # Use standard desktop prompts
           return standard_translation_prompt(source_lang, target_lang)
   ```

2. **Create Mobile-Specific Terminology**:
   - Update glossary files to include mobile-specific terms
   - Consider UI differences (tap vs click, swipe vs drag, etc.)

## Extending Language Support

### Step 1: Download Microsoft Translation Guide
1. **Obtain Official Translation Guidelines**:
   - Download Microsoft's official translation guide for the target language
   - Focus on UI translation principles and terminology standards
   - Note any culture-specific considerations

### Step 2: Generate Translation Principles Using Notebook LLM
1. **Create Language-Specific Principles**:
   - Use a Jupyter notebook with LLM integration
   - Process the Microsoft translation guide
   - Generate specific translation principles for the target language
   

### Step 3: Use Generate General Prompt Tool (Optional)
For fine-tuning translation prompts based on actual translation data:

1. **Prepare Translation Memory**:
   - Ensure you have at least 50 high-quality translation pairs
   - Store them in the translation memory database

2. **Run the Prompt Generation Tool**:
   - Navigate to: **Tool > Prompt > Generate General Prompt**
   - Located in: `tool/Prompt/generate_general_prompts.py`
   - The tool analyzes the first 50 translation pairs to generate optimized prompts

3. **Process Raw Response**:
   - The tool generates raw prompt suggestions
   - Manual review and refinement is needed

4. **Integration Steps**:
   - Review and refine the generated prompts manually
   - Test with sample translations
   - Integrate approved prompts into `prompts/translate_prompts.py`
   - Update language configuration in `config/translate_config.py`

### Step 4: Update Configuration Files
1. **Add Language to Configuration**:
   - Edit `config/translate_config.py`
   - Add language to `LANGUAGE_MAP`:
   ```python
   LANGUAGE_MAP = {
       # Existing languages...
       'New Language Name': 'NLG',  # Add your language
   }
   ```

2. **Update Multi-language Options** (if applicable):
   ```python
   MULTI_LANGUAGE_OPTIONS = {
       # Existing options...
       '16L': [existing_languages + ['New Language Name']],
   }
   ```

### Step 5: Testing and Validation
1. **Test Translation Quality**:
   - Run sample translations with the new configuration
   - Validate terminology consistency
   - Check cultural appropriateness

2. **Update Documentation**:
   - Document any language-specific considerations
   - Update user guides with new language support
