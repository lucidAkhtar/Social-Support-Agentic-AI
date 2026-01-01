#!/usr/bin/env python
"""
Social Support Application - Startup Script (Python Version)

This script starts both FastAPI backend and Streamlit frontend.

Usage:
    python startup.py              # Start both services
    python startup.py --api-only    # Start only FastAPI
    python startup.py --ui-only     # Start only Streamlit
"""

import subprocess
import sys
import time
import socket
import os
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color

def print_info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")

def print_success(msg):
    print(f"{Colors.GREEN}[✓]{Colors.NC} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}[⚠]{Colors.NC} {msg}")

def print_error(msg):
    print(f"{Colors.RED}[✗]{Colors.NC} {msg}")

def is_port_open(port):
    """Check if port is open"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

def start_fastapi():
    """Start FastAPI backend"""
    print_info("Checking for FastAPI on port 8000...")
    
    if is_port_open(8000):
        print_warning("FastAPI already running on port 8000")
        return None
    
    print("")
    print_info("Starting FastAPI backend...")
    print(f"  Command: python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload")
    print("")
    
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.api.main:app",
             "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Wait for FastAPI to start
        print(f"{Colors.YELLOW}[⏳]{Colors.NC} Waiting for FastAPI to initialize...")
        time.sleep(3)
        
        if is_port_open(8000):
            print_success(f"FastAPI backend started successfully (PID: {process.pid})")
            print(f"  Available at: {Colors.BLUE}http://localhost:8000{Colors.NC}")
            print(f"  API Docs at: {Colors.BLUE}http://localhost:8000/docs{Colors.NC}")
            return process
        else:
            print_warning("FastAPI may not have started. Check output above for errors.")
            return process
            
    except Exception as e:
        print_error(f"Failed to start FastAPI: {e}")
        return None

def start_streamlit():
    """Start Streamlit frontend"""
    print("")
    print("=" * 64)
    print("")
    print_info("Starting Streamlit frontend...")
    print(f"  Command: streamlit run streamlit_app/main_app.py --logger.level=info")
    print("")
    
    try:
        process = subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "streamlit_app/main_app.py",
             "--logger.level=info"],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return process.returncode
        
    except Exception as e:
        print_error(f"Failed to start Streamlit: {e}")
        return 1

def main():
    """Main startup logic"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Parse arguments
    api_only = "--api-only" in sys.argv
    ui_only = "--ui-only" in sys.argv
    
    print("=" * 64)
    print("Social Support Application - Startup")
    print("=" * 64)
    print("")
    
    print_info("Project Directory: " + os.getcwd())
    print_info("Python: " + sys.executable)
    print("")
    
    fastapi_process = None
    
    try:
        # Start FastAPI if not UI-only
        if not ui_only:
            fastapi_process = start_fastapi()
        
        # Start Streamlit if not API-only
        if not api_only:
            print("")
            print("=" * 64)
            print("")
            print_info("Opening Streamlit in browser...")
            print_info("If browser doesn't open, visit: " + Colors.BLUE + "http://localhost:8501" + Colors.NC)
            print("")
            
            exit_code = start_streamlit()
            sys.exit(exit_code)
        
        # If API-only, wait indefinitely
        if api_only:
            print("")
            print("=" * 64)
            print("")
            print_success("FastAPI is running!")
            print_info("Press Ctrl+C to stop")
            
            while True:
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("")
        print_warning("Shutting down...")
        if fastapi_process:
            fastapi_process.terminate()
            fastapi_process.wait()
        print_success("Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
