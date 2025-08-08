from flask import Flask, render_template, request, jsonify
import os
import json
import sys
import webbrowser
import threading
import time
import signal
from pathlib import Path
from threading import Timer

# Add parent directories to sys.path to import project modules
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, project_root)
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.translate_config import LANGUAGE_MAP, MULTI_LANGUAGE_OPTIONS
from tool.Refer_Text_n_Image_Related.chatroom.call_chat_room import run_translation_chat_rooms

app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
           static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Store the translation results
translation_results = {}
shutdown_server = False
server_thread = None

@app.route('/')
def home():
    return render_template('translation_interface.html', 
                         language_map=LANGUAGE_MAP)

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        source_text = data.get('source_text', '').strip()
        target_language = data.get('target_language', '')
        refer_text = data.get('refer_text', '').strip() or None
        refer_image_path = data.get('refer_image_path', '').strip() or None
        software_type = data.get('software_type', 'PDR')
        source_type = data.get('source_type', 'UI')
        
        # Validate required fields
        if not source_text:
            return jsonify({'status': 'error', 'message': 'Source text is required'})
        
        if not target_language:
            return jsonify({'status': 'error', 'message': 'Target language is required'})
        
        # Validate image path if provided
        if refer_image_path and not os.path.exists(refer_image_path):
            return jsonify({'status': 'error', 'message': f'Image file not found: {refer_image_path}'})
        
        # Run translation with 4 different chat rooms
        result = run_translation_chat_rooms(
            source_text=source_text,
            target_language=target_language,
            refer_text=refer_text,
            refer_image_path=refer_image_path,
            software_type=software_type,
            source_type=source_type
        )
        
        # Store results globally for debugging if needed
        global translation_results
        translation_results = result
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/submit', methods=['POST'])
def submit():
    """Legacy endpoint for backward compatibility"""
    try:
        data = request.json
        blocks = data.get('blocks', [])
        
        result = {
            'status': 'success',
            'message': 'Translation process started successfully.',
            'data': blocks
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/shutdown', methods=['POST'])
def shutdown():
    global shutdown_server
    shutdown_server = True
    
    # Return a success response first
    response = jsonify({'status': 'success', 'message': 'Server shutting down...'})
    
    # Schedule the server to exit after responding
    def shutdown_server():
        # Give the response time to be sent
        time.sleep(0.5)
        # Force exit the process
        os._exit(0)
    
    # Start the shutdown in a separate thread
    threading.Thread(target=shutdown_server).start()
    
    return response

def get_translation_results():
    """Return the latest translation results"""
    return translation_results

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create static directory for CSS/JS if it doesn't exist
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    os.makedirs(static_dir, exist_ok=True)
    
    # Define the URL to open
    port = 5000
    url = f"http://127.0.0.1:{port}"
    
    # Open browser after a short delay to ensure the server is up
    # But only if we're the main Flask process (not a reloader)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        def open_browser():
            webbrowser.open(url)
        
        Timer(1.0, open_browser).start()
    
    # Start the Flask app
    app.run(debug=True, port=port, use_reloader=False)