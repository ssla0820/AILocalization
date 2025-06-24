import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import subprocess
import time
import json


def run_translation_interface():
    """
    Run the translation interface and wait for user input.
    Returns the translation tasks configured by the user.
    """
    # Start the interface in a separate process
    interface_script = os.path.join(os.path.dirname(__file__), 'interface.py')
    proc = subprocess.Popen([sys.executable, interface_script])
    
    # Wait for the interface to initialize and for the user to input data
    translation_tasks = []
    max_wait_time = 3600  # Maximum wait time in seconds (1 hour)
    check_interval = 2  # Check every 2 seconds
    
    print("Waiting for user to configure translation tasks in the web interface...")
    
    for _ in range(int(max_wait_time / check_interval)):
        # Check if the process is still running
        if proc.poll() is not None:
            # Process has exited
            break
              # Try to read the tasks file
        temp_file_path = os.path.join(os.path.dirname(__file__), 'temp_translation_tasks.json')
        if os.path.exists(temp_file_path):
            try:
                with open(temp_file_path, 'r') as f:
                    translation_tasks = json.load(f)
                    # If we have tasks, we can break out of the loop
                    if translation_tasks:
                        break
            except Exception as e:
                print(f"Error reading tasks file: {e}")

        
        # Wait before checking again
        time.sleep(check_interval)
    # remove the temporary file if it exists
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
    
    # If the process is still running, we need to terminate it
    if proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    
    return translation_tasks

if __name__ == "__main__":
    # Run the interface and get the translation tasks
    tasks = run_translation_interface()
    
    if tasks:
        print(f"Received {len(tasks)} translation tasks from the interface:")
        for i, task in enumerate(tasks):
            print(f"\nTask {i+1}:")
            # print(f"  Source Type: {task.get('source_type')}")
            # print(f"  Product Name: {task.get('product_name')}")
            # print(f"  Source Language: {task.get('source_lang')}")
            # print(f"  Target Language: {task.get('target_lang')}")
            print(task)

            # Add more details as needed
            
        # Here you would process the tasks with your translation system
        print("\nNow you can process these tasks with your translation system.")
    else:
        print("No translation tasks were configured or the interface was closed without submitting.")
