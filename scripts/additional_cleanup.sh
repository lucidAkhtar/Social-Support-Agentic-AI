#!/bin/bash
# Additional cleanup for remaining root files

set -e

echo "=== Additional Root Cleanup ==="

# Create archive directories
mkdir -p scripts/archive
mkdir -p docs/archive

# Move remaining Python utility scripts to scripts/
echo "📦 Moving remaining Python files..."

SCRIPTS_TO_MOVE=(
    "add_policy_scores.py"
    "analyze_src_cleanup.py"
    "build_networkx_graph.py"
    "fix_dataset_generation.py"
    "generate_diverse_dataset.py"
    "generate_stratified_dataset.py"
    "initialize_databases.py"
    "load_data_to_databases.py"
    "migrate_database_schema.py"
    "trace_data_flow.py"
    "validate_full_pipeline.py"
)

for script in "${SCRIPTS_TO_MOVE[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" scripts/archive/
        echo "  Moved $script → scripts/archive/"
    fi
done

# Keep in root (essential for deployment)
# - startup.py (used by start.sh)
# - README.md (main documentation)

# Move old test files to tests/archive
TEST_FILES=(
    "test_production_e2e.py"
    "test_rag_chatbot.py"
    "test_unified_manager.py"
    "fastapi_test_endpoints.py"
)

for test in "${TEST_FILES[@]}"; do
    if [ -f "$test" ]; then
        mv "$test" tests/archive/
        echo "  Moved $test → tests/archive/"
    fi
done

# Move remaining markdown docs to docs/archive
echo "📝 Moving remaining markdown files..."

DOCS_TO_ARCHIVE=(
    "DATA_PIPELINE_ARCHITECTURE.md"
    "DATABASE_ARCHITECTURE_GUIDE.md"
    "FAANG_RAG_QUICK_REFERENCE.md"
    "FINAL_SYSTEM_REPORT.md"
    "ML_MODELING_DOCUMENTATION.md"
    "POLICY_ML_ARCHITECTURE.md"
    "PRODUCTION_ENHANCEMENTS.md"
    "PRODUCTION_TEST_RESULTS.md"
    "SRC_CLEANUP_REPORT.md"
)

for doc in "${DOCS_TO_ARCHIVE[@]}"; do
    if [ -f "$doc" ]; then
        mv "$doc" docs/archive/
        echo "  Moved $doc → docs/archive/"
    fi
done

echo ""
echo "✅ Additional cleanup complete!"
echo ""
echo "📁 Remaining in root:"
ls -1 *.py *.md *.sh 2>/dev/null | grep -v "^start.sh\|^README.md\|^final_cleanup.sh\|^additional_cleanup.sh" || echo "  Only essential files remain"
