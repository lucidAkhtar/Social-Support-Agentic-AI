#!/usr/bin/env python3
"""
Comprehensive import check for all modules
"""
import sys
from pathlib import Path

results = {
    "missing": [],
    "available": [],
    "errors": []
}

# Test external dependencies
external_deps = {
    "langgraph": "from langgraph.graph import StateGraph, END",
    "langchain_core": "from langchain_core.messages import HumanMessage",
    "langchain_community": "from langchain_community.llms import Ollama",
    "chromadb": "import chromadb",
    "neo4j": "from neo4j import GraphDatabase",
    "pdfplumber": "import pdfplumber",
    "pytesseract": "import pytesseract",
    "openpyxl": "import openpyxl",
    "shap": "import shap",
    "sklearn": "from sklearn.ensemble import RandomForestClassifier",
    "langfuse": "from langfuse import Langfuse",
    "pandas": "import pandas as pd",
    "numpy": "import numpy as np",
}

print("=" * 70)
print("EXTERNAL DEPENDENCIES CHECK")
print("=" * 70)

for name, import_stmt in external_deps.items():
    try:
        exec(import_stmt)
        print(f"✓ {name}")
        results["available"].append(name)
    except ImportError as e:
        print(f"✗ {name}: {e}")
        results["missing"].append(name)
    except Exception as e:
        print(f"⚠ {name}: {e}")
        results["errors"].append(name)

# Test internal imports
print("\n" + "=" * 70)
print("INTERNAL MODULES CHECK")
print("=" * 70)

internal_modules = [
    ("src.orchestration.langgraph_orchestrator", ["LangGraphOrchestrator", "ApplicationProcessingState"]),
    ("src.agents.extraction_agent", ["ExtractionAgent"]),
    ("src.agents.validation_agent", ["ValidationAgent"]),
    ("src.agents.decision_agent", ["DecisionAgent"]),
    ("src.database.database_manager", ["DatabaseManager"]),
    ("src.database.sqlite_client", ["SQLiteClient"]),
    ("src.database.chromadb_manager", ["ChromaDBManager"]),
    ("src.database.neo4j_manager", ["Neo4jManager"]),
    ("src.ml.explainability", ["ExplainableML"]),
    ("src.observability.langfuse_tracker", ["LangfuseTracker", "ObservabilityIntegration"]),
    ("src.models.extraction_models", ["ApplicationExtraction"]),
]

for module_name, classes in internal_modules:
    try:
        module = __import__(module_name, fromlist=classes)
        for cls in classes:
            if hasattr(module, cls):
                print(f"✓ {module_name}.{cls}")
                results["available"].append(f"{module_name}.{cls}")
            else:
                print(f"✗ {module_name}.{cls} - NOT FOUND in module")
                results["missing"].append(f"{module_name}.{cls}")
    except ImportError as e:
        print(f"✗ {module_name}: {e}")
        results["missing"].append(module_name)
    except Exception as e:
        print(f"⚠ {module_name}: {e}")
        results["errors"].append(module_name)

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Available: {len(results['available'])}")
print(f"Missing: {len(results['missing'])}")
print(f"Errors: {len(results['errors'])}")

if results["missing"]:
    print("\n⚠️  MISSING DEPENDENCIES:")
    for item in results["missing"]:
        print(f"  - {item}")

if results["errors"]:
    print("\n⚠️  ERROR ITEMS:")
    for item in results["errors"]:
        print(f"  - {item}")

if not results["missing"] and not results["errors"]:
    print("\n✓ ALL IMPORTS SUCCESSFUL!")
    sys.exit(0)
else:
    print("\n✗ SOME IMPORTS FAILED - SEE ABOVE")
    sys.exit(1)
