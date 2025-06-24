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

# Add parent directory to sys.path to import project modules
sys.path.append(str(Path(__file__).parent.parent))
from config.translate_config import LANGUAGE_MAP, MULTI_LANGUAGE_OPTIONS

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

# Store the translation tasks
translation_tasks = []
shutdown_server = False
server_thread = None

@app.route('/')
def home():
    return render_template('index.html', 
                         language_map=LANGUAGE_MAP,
                         multi_language_options=MULTI_LANGUAGE_OPTIONS)

@app.route('/submit', methods=['POST'])
def submit():
    try:
        global translation_tasks
        data = request.json
        blocks = data.get('blocks', [])
        
        # Store the configuration data for processing
        translation_tasks = blocks
        
        # Save the data to a temporary file for debugging/backup
        temp_file_path = os.path.join(os.path.dirname(__file__), 'temp_translation_tasks.json')
        with open(temp_file_path, 'w') as f:
            json.dump(blocks, f, indent=4)
        
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

def get_translation_tasks():
    """Return the submitted translation tasks"""
    return translation_tasks

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
else:
    # This allows the module to be imported by other scripts
    # to get the translation tasks data
    pass
