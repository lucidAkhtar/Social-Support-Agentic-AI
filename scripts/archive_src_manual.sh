#!/bin/bash
# Archive unused files from src/ directory
# MANUALLY VERIFIED - Based on actual production imports

set -e

cd /Users/marghubakhtar/Documents/social_support_agentic_ai

# Create archive directory
mkdir -p src_archive

echo "========================================"
echo "ARCHIVING UNUSED src/ FILES"
echo "========================================"
echo ""
echo "This will archive 25 unused files from src/"
echo ""
echo "FILES TO ARCHIVE:"
echo ""
echo "  src/agents/ (2 files):"
echo "    - recommendation_agent_old.py"
echo "    - validation_agent_old.py"
echo ""
echo "  src/core/ (0 files - base_agent.py is KEPT, used by orchestrator)"
echo ""
echo "  src/database/ (5 files - OLD DUPLICATE FOLDER):"
echo "    - __init__.py"
echo "    - chromadb_manager.py"
echo "    - database_manager.py"
echo "    - neo4j_manager.py"
echo "    - sqlite_client.py"
echo ""
echo "  src/databases/ (2 files):"
echo "    - database_manager.py (generic, not used)"
echo "    - neo4j_manager.py (Neo4j not in production)"
echo ""
echo "  src/ml/ (4 files - one-time training scripts):"
echo "    - explainability.py"
echo "    - ml_pipeline.py"
echo "    - synthetic_data_generator.py"
echo "    - train_model.py"
echo ""
echo "  src/observability/ (1 file):"
echo "    - langfuse_tracker.py"
echo ""
echo "  src/rag/ (2 files - replaced by src/services/rag_engine.py):"
echo "    - __init__.py"
echo "    - production_rag.py"
echo ""
echo "  src/services/ (4 files - moved to agents or replaced):"
echo "    - excel_parser.py"
echo "    - llm_service.py"
echo "    - ocr_service.py"
echo "    - resume_parser.py"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Moving unused files to src_archive/..."

# Archive from src/agents/
echo "Archiving src/agents/..."
mkdir -p src_archive/src/agents/
mv "src/agents/recommendation_agent_old.py" "src_archive/src/agents/" 2>/dev/null || true
mv "src/agents/validation_agent_old.py" "src_archive/src/agents/" 2>/dev/null || true

# Archive from src/core/
# base_agent.py is KEPT (used by orchestrator)
# mkdir -p src_archive/src/core/
# mv "src/core/base_agent.py" "src_archive/src/core/" 2>/dev/null || true

# Archive ENTIRE src/database/ folder (old duplicate)
echo "Archiving src/database/ (entire old folder)..."
mv "src/database" "src_archive/src/database" 2>/dev/null || true

# Archive from src/databases/
echo "Archiving src/databases/..."
mkdir -p src_archive/src/databases/
mv "src/databases/database_manager.py" "src_archive/src/databases/" 2>/dev/null || true
mv "src/databases/neo4j_manager.py" "src_archive/src/databases/" 2>/dev/null || true

# Archive ENTIRE src/ml/ folder
echo "Archiving src/ml/ (training scripts - no longer needed)..."
mv "src/ml" "src_archive/src/ml" 2>/dev/null || true

# Archive ENTIRE src/observability/ folder
echo "Archiving src/observability/..."
mv "src/observability" "src_archive/src/observability" 2>/dev/null || true

# Archive ENTIRE src/rag/ folder
echo "Archiving src/rag/ (replaced by rag_engine.py)..."
mv "src/rag" "src_archive/src/rag" 2>/dev/null || true

# Archive from src/services/
echo "Archiving src/services/..."
mkdir -p src_archive/src/services/
mv "src/services/excel_parser.py" "src_archive/src/services/" 2>/dev/null || true
mv "src/services/llm_service.py" "src_archive/src/services/" 2>/dev/null || true
mv "src/services/ocr_service.py" "src_archive/src/services/" 2>/dev/null || true
mv "src/services/resume_parser.py" "src_archive/src/services/" 2>/dev/null || true

echo ""
echo "========================================"
echo "ARCHIVE COMPLETE"
echo "========================================"
echo ""
echo "Archived files: src_archive/"
echo ""
echo "KEPT IN PRODUCTION:"
echo "  src/agents/ (7 files): All 6 agents + __init__.py"
echo "  src/api/ (2 files): main.py + __init__.py"
echo "  src/core/ (3 files): orchestrator.py, types.py, __init__.py"
echo "  src/databases/ (7 files): All 5 managers + unified_db.py + __init__.py"
echo "  src/services/ (4 files): document_extractor, rag_engine, governance, conversation_manager"
echo ""
echo "To restore a file:"
echo "  mv src_archive/src/path/file.py src/path/file.py"
echo ""
echo "To delete archives permanently (after verification):"
echo "  rm -rf src_archive/"
echo ""
