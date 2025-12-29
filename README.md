Python is pinned to 3.11 to ensure maximum compatibility with open-weight LLM tooling and stable local execution on constrained Apple Silicon(M1).

XGBoost is included as an optional enhancement; default models use scikit-learn for lower memory usage.

LangChain, LangGraph, and related packages are version-aligned to avoid known dependency conflicts introduced after the LangChain package split.

mistral:latest with model size of  4.4 GB is used as the LLM
First, run the ollama server by below step:
1. OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1 ollama serve
To kill , use pkill ollama

- The stack is intentionally optimized for local execution on constrained Apple Silicon(M1) hardware while still demonstrating full agentic orchestration, multimodal processing, explainability, and observability as required by the problem statement.

Tool substitutions rationale
----------------------------
Due to local execution constraints (Apple Silicon M1, 8 GB RAM) and the prototyping nature of the assignment, lightweight local alternatives were used (SQLite, TinyDB, NetworkX, ChromaDB). These preserve the same data modeling and interaction semantics as PostgreSQL, MongoDB, Neo4j, and Qdrant, while enabling reliable local demos. The architecture is database-agnostic and can be swapped with enterprise-grade systems without changes to business logic.
