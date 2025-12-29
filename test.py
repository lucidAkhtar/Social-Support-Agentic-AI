import subprocess
import sys
import os
from pathlib import Path

# def check_system():
#     """Verify system requirements"""
#     print("🔍 Checking system requirements...")
    
#     # Check Python version
#     if sys.version_info < (3, 9):
#         print("❌ Python 3.9+ required")
#         sys.exit(1)
#     print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
#     # Check available memory
#     try:
#         import psutil
#         mem = psutil.virtual_memory()
#         available_gb = mem.available / (1024**3)
#         print(f"✅ Available RAM: {available_gb:.1f}GB")
        
#         if available_gb < 4:
#             print("⚠️  WARNING: Low memory. Close other applications!")
#             return False
#     except ImportError:
#         print("⚠️  Install psutil: pip install psutil")
#         return False
    
#     # Check disk space
#     total, used, free = os.statvfs('/').f_blocks, os.statvfs('/').f_bavail, os.statvfs('/').f_bfree
#     free_gb = (free * os.statvfs('/').f_frsize) / (1024**3)
#     print(f"✅ Free disk space: {free_gb:.1f}GB")
    
#     if free_gb < 20:
#         print("⚠️  WARNING: Low disk space. Clean up some files!")
#         return False
    
#     return True

def check_ollama():
    """Verify Ollama and Mistral are installed"""
    print("\n🤖 Checking Ollama...")
    
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'mistral' in result.stdout:
            print("✅ Mistral model found")
            return True
        else:
            print("❌ Mistral not found. Run: ollama pull mistral")
            return False
            
    except FileNotFoundError:
        print("❌ Ollama not installed. Install from: https://ollama.ai")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Ollama not responding. Run: ollama serve")
        return False

def test_mistral():
    """Test Mistral model"""
    print("\n🧪 Testing Mistral...")
    
    try:
        import ollama
        response = ollama.chat(
            model='mistral',
            messages=[{
                'role': 'user',
                'content': 'Respond with only the word: WORKING'
            }]
        )
        
        if 'WORKING' in response['message']['content'].upper():
            print("✅ Mistral is working!")
            return True
        else:
            print("⚠️  Mistral responded but output unexpected")
            print(f"Response: {response['message']['content']}")
            return True  # Still working, just different response
            
    except Exception as e:
        print(f"❌ Mistral test failed: {str(e)}")
        return False

def create_project_structure():
    """Create minimal project structure"""
    print("\n📁 Creating project structure...")
    
    dirs = [
        'src/agents',
        'src/api',
        'src/models',
        'src/database',
        'data',
        'streamlit_app',
        'tests'
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        (Path(dir_path) / '__init__.py').touch()
    
    print("✅ Project structure created")

def create_requirements_m1():
    """Create M1-optimized requirements.txt"""
    print("\n📝 Creating requirements.txt...")
    
    requirements = """# M1 MacBook Air 8GB - Optimized Dependencies
# Core Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
python-multipart==0.0.6

# Streamlit UI
streamlit==1.31.0

# LLM & Agents (Lightweight)
langchain==0.1.6
langchain-community==0.0.20
langgraph==0.0.25
ollama==0.1.7

# ML (Essential Only)
scikit-learn==1.4.0
pandas==2.2.0
numpy==1.26.3

# Document Processing (Lightweight)
pytesseract==0.3.10
PyPDF2==3.0.1
pillow==10.2.0

# Lightweight Databases
sqlalchemy==2.0.25
tinydb==4.8.0
chromadb==0.4.22

# Utilities
python-dotenv==1.0.1
psutil==5.9.8
aiofiles==23.2.1

# Testing
pytest==8.0.0
httpx==0.26.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    
    print("✅ requirements.txt created")

if __name__ == "__main__":
    #check_system()
    #check_ollama()
    #test_mistral()
    #create_project_structure()
    create_requirements_m1()

# install psutil
