import subprocess
import sys
import time
import os

def run_servers():
    # Set environment variables
    my_env = os.environ.copy()
    my_env["FLASK_APP"] = "app:flask_app"
    my_env["FLASK_DEBUG"] = "1"
    
    # Start Flask server (frontend) on port 5000
    print("Starting Flask frontend server on port 5000...")
    flask_process = subprocess.Popen(
        [sys.executable, '-m', 'flask', 'run', '--port', '5000'],
        env=my_env
    )
    
    # Wait a bit for Flask to start
    time.sleep(2)
    
    # Start FastAPI server (backend) on port 8001 (different from 8000)
    print("Starting FastAPI backend server on port 8001...")
    fastapi_process = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'app:app', '--port', '8001']
    )
    
    try:
        # Wait for both processes
        flask_process.wait()
        fastapi_process.wait()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nShutting down servers...")
        flask_process.terminate()
        fastapi_process.terminate()
        flask_process.wait()
        fastapi_process.wait()

if __name__ == "__main__":
    run_servers() 