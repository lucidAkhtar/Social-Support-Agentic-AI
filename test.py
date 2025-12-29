#!/usr/bin/env python3
"""
Complete Environment Test Script
Tests all components required by the assignment
Run: poetry run python scripts/test_setup.py
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_section(title: str):
    """Print section header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result"""
    icon = f"{GREEN}✅{RESET}" if passed else f"{RED}❌{RESET}"
    print(f"{icon} {test_name}")
    if details:
        print(f"   {details}")

def test_python_version() -> Tuple[bool, str]:
    """Test Python version is 3.11.x"""
    try:
        version = sys.version_info
        if version.major == 3 and version.minor == 11:
            return True, f"Python {version.major}.{version.minor}.{version.micro}"
        else:
            return False, f"Python {version.major}.{version.minor}.{version.micro} (need 3.11.x)"
    except Exception as e:
        return False, str(e)

def test_imports() -> Tuple[bool, str]:
    """Test all critical imports (Assignment Required)"""
    try:
        # Core frameworks
        import fastapi
        import streamlit
        import uvicorn
        
        # LLM & Agents (Assignment Required)
        import langchain
        import langgraph
        from langchain_community.llms import Ollama
        
        # ML (Assignment Required - Scikit-learn)
        import sklearn
        import pandas
        import numpy
        import xgboost
        import shap
        
        # Document processing (Multi-modal)
        import pytesseract
        import PIL
        import PyPDF2
        import pdfplumber
        
        # Other required
        import sqlalchemy
        import chromadb
        
        return True, "All required packages imported successfully"
    except ImportError as e:
        return False, f"Import failed: {str(e)}"

def test_ollama_mistral() -> Tuple[bool, str]:
    """Test Ollama with Mistral model (Your Configuration)"""
    try:
        import ollama
        
        # Check if Ollama is running
        try:
            models = ollama.list()
            model_names = [model.get('model', '') for model in models.get('models', [])]
            
            if not any('mistral' in name.lower() for name in model_names):
                return False, "Mistral model not found. Run: ollama pull mistral"
            
            # Test generation
            response = ollama.generate(
                model='mistral:latest',
                prompt='Respond with only: WORKING',
                options={'num_predict': 10}
            )
            
            if 'response' in response and response['response']:
                return True, f"Mistral responding (Model size: 4.4GB)"
            else:
                return False, "Mistral not responding correctly"
                
        except Exception as conn_error:
            return False, f"Ollama not running. Start: ollama serve. Error: {str(conn_error)}"
            
    except ImportError:
        return False, "Ollama package not installed. Run: poetry add ollama"
    except Exception as e:
        return False, str(e)

def test_cohere_embeddings() -> Tuple[bool, str]:
    """Test Cohere embeddings (Your Configuration)"""
    try:
        import cohere
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv('.env.local')
        api_key = os.getenv('COHERE_API_KEY')
        
        if not api_key:
            return False, "COHERE_API_KEY not found in .env file"
        
        # Test Cohere connection
        co = cohere.Client(api_key)
        
        # Test embedding (small test)
        response = co.embed(
            texts=["test"],
            model="embed-english-v3.0",
            input_type="search_query"
        )
        
        if response.embeddings and len(response.embeddings) > 0:
            return True, f"Cohere working (Model: embed-english-v3.0, Dim: {len(response.embeddings[0])})"
        else:
            return False, "Cohere not returning embeddings"
            
    except ImportError:
        return False, "Cohere package not installed. Run: poetry add cohere"
    except Exception as e:
        return False, f"Cohere error: {str(e)}"

# def test_langfuse() -> Tuple[bool, str]:
#     """Test Langfuse observability (Assignment Required)"""
#     try:
#         from langfuse import Langfuse
#         from dotenv import load_dotenv
        
#         load_dotenv()
#         public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
#         secret_key = os.getenv('LANGFUSE_SECRET_KEY')
        
#         if not public_key or not secret_key:
#             return True, f"{YELLOW}Langfuse keys not configured (optional for local dev){RESET}"
        
#         # Test connection (if keys provided)
#         langfuse = Langfuse(
#             public_key=public_key,
#             secret_key=secret_key
#         )
        
#         return True, "Langfuse configured (observability ready)"
        
#     except ImportError:
#         return False, "Langfuse not installed. Run: poetry add langfuse"
#     except Exception as e:
#         return True, f"{YELLOW}Langfuse connection skipped: {str(e)}{RESET}"

# def test_langgraph() -> Tuple[bool, str]:
#     """Test LangGraph agent orchestration (Assignment Required)"""
#     try:
#         from langgraph.graph import StateGraph, END
#         from typing import TypedDict
        
#         # Create minimal test graph
#         class TestState(TypedDict):
#             value: int
        
#         def increment(state: TestState) -> TestState:
#             state['value'] += 1
#             return state
        
#         workflow = StateGraph(TestState)
#         workflow.add_node("increment", increment)
#         workflow.set_entry_point("increment")
#         workflow.add_edge("increment", END)
        
#         app = workflow.compile()
#         result = app.invoke({"value": 0})
        
#         if result['value'] == 1:
#             return True, "LangGraph orchestration working"
#         else:
#             return False, "LangGraph test failed"
            
#     except Exception as e:
#         return False, f"LangGraph error: {str(e)}"

# def test_scikit_learn() -> Tuple[bool, str]:
#     """Test Scikit-learn ML (Assignment Required)"""
#     try:
#         from sklearn.ensemble import RandomForestClassifier
#         from sklearn.datasets import make_classification
#         import numpy as np
        
#         # Create small test dataset
#         X, y = make_classification(n_samples=100, n_features=10, random_state=42)
        
#         # Train simple model
#         clf = RandomForestClassifier(n_estimators=10, random_state=42)
#         clf.fit(X, y)
        
#         # Test prediction
#         accuracy = clf.score(X, y)
        
#         if accuracy > 0.8:
#             return True, f"Scikit-learn working (Test accuracy: {accuracy:.2%})"
#         else:
#             return False, "ML model accuracy too low"
            
#     except Exception as e:
#         return False, f"Scikit-learn error: {str(e)}"

# def test_document_processing() -> Tuple[bool, str]:
#     """Test multi-modal document processing (Assignment Required)"""
#     try:
#         # Test OCR availability
#         import pytesseract
#         from PIL import Image
#         import numpy as np
        
#         # Create test image
#         img = Image.new('RGB', (100, 50), color='white')
        
#         # Try OCR
#         try:
#             text = pytesseract.image_to_string(img)
#             ocr_status = "✓ Tesseract"
#         except Exception:
#             ocr_status = "✗ Tesseract not configured"
        
#         # Test PDF
#         import PyPDF2
#         pdf_status = "✓ PDF parsing"
        
#         # Test Excel
#         import openpyxl
#         excel_status = "✓ Excel processing"
        
#         return True, f"{ocr_status}, {pdf_status}, {excel_status}"
        
#     except Exception as e:
#         return False, f"Document processing error: {str(e)}"

# def test_databases() -> Tuple[bool, str]:
#     """Test database setup (Assignment Required)"""
#     try:
#         # Test SQLite (lightweight)
#         import sqlite3
#         conn = sqlite3.connect(':memory:')
#         conn.execute("CREATE TABLE test (id INTEGER)")
#         conn.close()
        
#         # Test ChromaDB (vector DB)
#         import chromadb
#         client = chromadb.Client()
        
#         # Test NetworkX (graph processing, instead of Neo4j for M1)
#         import networkx as nx
#         G = nx.Graph()
#         G.add_edge(1, 2)
        
#         return True, "SQLite, ChromaDB (vectors), NetworkX (graphs)"
        
#     except Exception as e:
#         return False, f"Database error: {str(e)}"

def test_memory() -> Tuple[bool, str]:
    """Test available memory (Critical for M1 8GB)"""
    try:
        import psutil
        
        mem = psutil.virtual_memory()
        available_gb = mem.available / (1024**3)
        total_gb = mem.total / (1024**3)
        percent = mem.percent
        
        if available_gb < 3:
            return False, f"Low memory: {available_gb:.1f}GB available (need 4GB+)"
        elif available_gb < 4:
            return True, f"{YELLOW}Marginal: {available_gb:.1f}GB / {total_gb:.1f}GB ({100-percent:.0f}% free){RESET}"
        else:
            return True, f"Good: {available_gb:.1f}GB / {total_gb:.1f}GB available ({100-percent:.0f}% free)"
            
    except Exception as e:
        return False, f"Memory check failed: {str(e)}"

def test_disk_space() -> Tuple[bool, str]:
    """Test disk space"""
    try:
        import shutil
        
        total, used, free = shutil.disk_usage("/")
        free_gb = free / (1024**3)
        
        if free_gb < 20:
            return False, f"Low disk space: {free_gb:.1f}GB free (need 20GB+)"
        else:
            return True, f"{free_gb:.1f}GB free"
            
    except Exception as e:
        return False, f"Disk check failed: {str(e)}"

def test_fastapi() -> Tuple[bool, str]:
    """Test FastAPI setup (Assignment Required)"""
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
        
        # Create test app
        app = FastAPI()
        
        class TestModel(BaseModel):
            value: int
        
        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}
        
        return True, "FastAPI ready for model serving"
        
    except Exception as e:
        return False, f"FastAPI error: {str(e)}"

def test_streamlit() -> Tuple[bool, str]:
    """Test Streamlit (Assignment Required)"""
    try:
        import streamlit
        return True, f"Streamlit {streamlit.__version__} installed"
    except ImportError:
        return False, "Streamlit not installed"

def check_environment_file() -> Tuple[bool, str]:
    """Check if .env file exists"""
    if Path('.env').exists():
        return True, ".env file found"
    else:
        return False, ".env file missing (copy from .env.example)"

def main():
    """Run all tests"""
    print(f"\n{BLUE}╔{'═'*58}╗{RESET}")
    print(f"{BLUE}║  Social Support AI - Environment Test Suite            ║{RESET}")
    print(f"{BLUE}║  M1 MacBook Air 8GB - Python 3.11.10                   ║{RESET}")
    print(f"{BLUE}╚{'═'*58}╝{RESET}")
    
    # Track results
    results = []
    
    # System Tests
    print_section("1. System Requirements")
    tests = [
        ("Python Version", test_python_version),
        ("Available Memory", test_memory),
        ("Disk Space", test_disk_space),
        ("Environment File", check_environment_file),
    ]
    
    for name, test_func in tests:
        passed, details = test_func()
        print_result(name, passed, details)
        results.append((name, passed))
    
    # Package Tests
    print_section("2. Python Packages")
    tests = [
        ("Core Imports", test_imports),
        ("FastAPI (Model Serving)", test_fastapi),
        ("Streamlit (Frontend)", test_streamlit),
    ]
    
    for name, test_func in tests:
        passed, details = test_func()
        print_result(name, passed, details)
        results.append((name, passed))
    
    ## AI/ML Tests
    print_section("3. AI/ML Stack (Assignment Required)")
    tests = [
        ("Ollama + Mistral (Your Config)", test_ollama_mistral),
        ("Cohere Embeddings (Your Config)", test_cohere_embeddings),
        # ("LangGraph (Agent Orchestration)", test_langgraph),
        # ("Scikit-learn (ML Models)", test_scikit_learn),
        # ("Langfuse (Observability)", test_langfuse),
    ]
    
    for name, test_func in tests:
        passed, details = test_func()
        print_result(name, passed, details)
        results.append((name, passed))
    
    # # Data Processing Tests
    # print_section("4. Multi-Modal Processing")
    # tests = [
    #     ("Document Processing (OCR, PDF, Excel)", test_document_processing),
    #     ("Databases (SQL, Vector, Graph)", test_databases),
    # ]
    
    # for name, test_func in tests:
    #     passed, details = test_func()
    #     print_result(name, passed, details)
    #     results.append((name, passed))
    
    # # Summary
    # print_section("Summary")
    
    # passed_tests = sum(1 for _, passed in results if passed)
    # total_tests = len(results)
    # percentage = (passed_tests / total_tests) * 100
    
    # print(f"\n{BLUE}Results:{RESET}")
    # print(f"  Passed: {GREEN}{passed_tests}{RESET}/{total_tests}")
    # print(f"  Success Rate: {percentage:.0f}%\n")
    
    # if passed_tests == total_tests:
    #     print(f"{GREEN}╔{'═'*58}╗{RESET}")
    #     print(f"{GREEN}║  ✅ ALL TESTS PASSED - READY TO BUILD! 🚀              ║{RESET}")
    #     print(f"{GREEN}╚{'═'*58}╝{RESET}")
    #     print("\nNext steps:")
    #     print("  1. Start Ollama (if not running): ollama serve")
    #     print("  2. Start API: poetry run start-api")
    #     print("  3. Start UI: poetry run start-ui")
    #     return 0
    # elif percentage >= 80:
    #     print(f"{YELLOW}╔{'═'*58}╗{RESET}")
    #     print(f"{YELLOW}║  ⚠️  MOSTLY READY - Fix minor issues                    ║{RESET}")
    #     print(f"{YELLOW}╚{'═'*58}╝{RESET}")
        
    #     print("\nFailed tests:")
    #     for name, passed in results:
    #         if not passed:
    #             print(f"  - {name}")
    #     return 1
    # else:
    #     print(f"{RED}╔{'═'*58}╗{RESET}")
    #     print(f"{RED}║  ❌ SETUP INCOMPLETE - Fix critical issues              ║{RESET}")
    #     print(f"{RED}╚{'═'*58}╝{RESET}")
        
    #     print("\nCritical failures:")
    #     for name, passed in results:
    #         if not passed:
    #             print(f"  - {name}")
    #     return 1

if __name__ == "__main__":
    sys.exit(main())