from flask import Flask, render_template, request, jsonify, redirect, url_for
import subprocess
import sys
import os
from pathlib import Path
import threading
import time
import webbrowser

# Add the parent directory to Python path to import config
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.translate_config import LANGUAGE_MAP

# Import tool modules - delay import until needed
# This will make startup faster
tool_modules = {}

def load_tool_module(module_name, file_path):
    """Load a tool module on-demand"""
    if module_name not in tool_modules:
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tool_modules[module_name] = module
    return tool_modules[module_name]

app = Flask(__name__, template_folder='templates', static_folder='static')

# Global variable to track process status
process_status = {"running": False, "message": ""}

@app.route('/')
def index():
    return render_template('index.html', languages=list(LANGUAGE_MAP.keys()))

@app.route('/execute', methods=['POST'])
def execute():
    global process_status
    
    try:
        data = request.json
        tool_type = data.get('tool_type')
        tool_subtype = data.get('tool_subtype')
        params = data.get('params', {})
        
        # Validate required fields
        if not all(value.strip() if isinstance(value, str) else value for value in params.values()):
            return jsonify({"success": False, "message": "All fields are required!"})
        
        # Set process status
        process_status["running"] = True
        process_status["message"] = "Process started..."
        
        # Execute in a separate thread
        thread = threading.Thread(target=execute_tool, args=(tool_type, tool_subtype, params))
        thread.daemon = True
        thread.start()
        
        return jsonify({"success": True, "message": "Process started successfully!"})
    
    except Exception as e:
        process_status["running"] = False
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

def execute_tool(tool_type, tool_subtype, params):
    global process_status
    
    try:
        # Execute the tool functions directly with on-demand loading
        if tool_subtype == "tmx_to_xlsx":
            module = load_tool_module("tmx_csv_convertor", 
                Path(__file__).parent.parent / "Translation_Memory_Related" / "tmx_csv_convertor.py")
            module.main(
                params["tmx_file_path"],
                params["output_xlsx_path"],
                params["source_language"],
                params["target_language"]
            )
        elif tool_subtype == "xlsx_to_json":
            # Convert language names to abbreviations
            target_languages = []
            for lang in params["target_languages"]:
                if lang in LANGUAGE_MAP:
                    target_languages.append(LANGUAGE_MAP[lang])
            
            module = load_tool_module("create_json_from_xlsx", 
                Path(__file__).parent.parent / "Translation_Memory_Related" / "create_json_from_xlsx.py")
            module.main(
                params["xlsx_file_path"],
                params["output_folder_path"],
                target_languages,
                params["product"]
            )
        elif tool_subtype == "combine_xlsx":
            module = load_tool_module("combine_xlsx_files", 
                Path(__file__).parent.parent / "Translation_Memory_Related" / "combine_xlsx_files.py")
            module.main(
                params["source_folder_path"],
                params["output_file_path"]
            )
        elif tool_subtype == "copy_source":
            # Convert language names to abbreviations
            target_languages = []
            for lang in params["target_languages"]:
                if lang in LANGUAGE_MAP:
                    target_languages.append(LANGUAGE_MAP[lang])
            
            # Get all files from source folder
            source_folder = params["source_folder_path"]
            if os.path.exists(source_folder):
                file_list = [os.path.join(source_folder, file) for file in os.listdir(source_folder) 
                           if os.path.isfile(os.path.join(source_folder, file))]
            else:
                raise Exception(f"Source folder '{source_folder}' does not exist.")
            
            module = load_tool_module("copy_source", 
                Path(__file__).parent.parent / "Source_File_Related" / "copy_source.py")
            module.main(
                file_list,
                params["output_folder_path"],
                target_languages
            )
        elif tool_subtype == "generate_general":
            module = load_tool_module("generate_general_prompts", 
                Path(__file__).parent.parent / "Prompt" / "generate_general_prompts.py")
            module.main(
                params["tm_file_path"],
                params["source_language"],
                params["target_language"],
                params["output_xlsx_path"]
            )
        elif tool_subtype == "create_table":
            module = load_tool_module("create_region_table", 
                Path(__file__).parent.parent / "Common_Usage_Table" / "create_region_table.py")
            module.main(
                params["tm_file_path"]
            )
        elif tool_subtype == "segment_for_refer":
            module = load_tool_module("get_segment", 
                Path(__file__).parent.parent / "Refer_Text_n_Image_Related" / "get_segment.py")
            module.main(
                params["source_folder"],
                params["output_folder"]
            )
        
        process_status["message"] = "Process completed successfully!"
            
    except Exception as e:
        process_status["message"] = f"Error executing tool: {str(e)}"
    
    finally:
        process_status["running"] = False

@app.route('/status')
def status():
    return jsonify(process_status)

@app.route('/close')
def close():
    # Give a moment for the response to be sent, then shutdown
    def shutdown():
        time.sleep(1)
        # Use os._exit() to force shutdown the application
        import os
        os._exit(0)
    
    thread = threading.Thread(target=shutdown)
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "Server shutting down..."})

if __name__ == '__main__':
    # Create templates and static directories if they don't exist
    templates_dir = Path(__file__).parent / 'templates'
    static_dir = Path(__file__).parent / 'static'
    templates_dir.mkdir(exist_ok=True)
    static_dir.mkdir(exist_ok=True)
    
    # Check if this is the main process (not a reloader subprocess)
    # This prevents multiple browser windows from opening
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Function to open browser after a short delay
        def open_browser():
            time.sleep(1)  # Reduced delay for faster opening
            webbrowser.open('http://127.0.0.1:5000')
        
        # Start browser opening in a separate thread
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
    
    # Run the Flask app with reloader disabled to prevent multiple windows
    app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
