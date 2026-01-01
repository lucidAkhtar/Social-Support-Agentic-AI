#!/bin/bash
# Final Professional Cleanup for Recruiter Presentation
# This script organizes the project structure

set -e  # Exit on any error

echo "=== Final Cleanup Starting ==="

# Create necessary directories
echo "Creating directory structure..."
mkdir -p scripts
mkdir -p tests/archive
mkdir -p docs/archive
mkdir -p models_archive

# ===== 1. Clean up models/ directory =====
echo "📦 Cleaning models/ directory..."

# Archive old v1 model
mv models/eligibility_model.pkl models_archive/eligibility_model_v1_backup.pkl || true

# Remove redundant .pkl version of json file (keep json only)
mv models/feature_names.pkl models_archive/ || true

echo "✅ Models cleaned - Keeping: eligibility_model_v2.pkl, feature_scaler.pkl, feature_names.json, model_metadata.json, training_report.json"

# ===== 2. Remove .bak file =====
echo "🗑️  Removing backup file..."
rm -f src/agents/recommendation_agent.py.bak
echo "✅ Deleted recommendation_agent.py.bak"

# ===== 3. Organize root Python files =====
echo "🐍 Organizing root Python files..."

# Keep in root (essential)
KEEP_IN_ROOT=(
    "startup.py"
    "start.sh"
    "pyproject.toml"
)

# Move to scripts/ (utility scripts)
MOVE_TO_SCRIPTS=(
    "populate_databases.py"
    "index_chromadb.py"
    "generate_full_dataset.py"
    "run_data_generation.py"
    "check_imports.py"
    "analyze_project_cleanup.py"
)

# Move to tests/ (test scripts - keep only essential test)
MOVE_TO_TESTS_ARCHIVE=(
    "test.py"
    "test_data_generation.py"
    "test_decision.py"
    "test_extraction.py"
    "test_validation.py"
    "test_all_components.py"
    "rigorous_test.py"
    "phase4_ml_training.py"
    "phase6_fast_test.py"
    "phase6_test_suite.py"
    "phase7_integration_test.py"
    "phase7_lightweight_test.py"
    "phase8_governance_test.py"
    "phase8_verification_test.py"
    "phase9_fastapi_test.py"
    "phase9_integration_verification.py"
)

# Keep in tests/ (main E2E test)
KEEP_TEST="test_real_files_e2e.py"

# Keep training scripts in scripts/
MOVE_TO_SCRIPTS+=(
    "train_ml_model.py"
    "train_ml_model_v2.py"
)

# Move utility scripts
for script in "${MOVE_TO_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" scripts/
        echo "  Moved $script → scripts/"
    fi
done

# Move old tests to archive
for test in "${MOVE_TO_TESTS_ARCHIVE[@]}"; do
    if [ -f "$test" ]; then
        mv "$test" tests/archive/
        echo "  Moved $test → tests/archive/"
    fi
done

# Keep main test in tests/
if [ -f "$KEEP_TEST" ]; then
    mv "$KEEP_TEST" tests/
    echo "  Moved $KEEP_TEST → tests/"
fi

# Move cleanup scripts to scripts/
if [ -f "archive_src_manual.sh" ]; then
    mv archive_src_manual.sh scripts/
    echo "  Moved archive_src_manual.sh → scripts/"
fi

echo "✅ Python files organized"

# ===== 4. Organize root Markdown files =====
echo "📝 Organizing markdown files..."

# Keep in root
KEEP_MD_ROOT=(
    "README.md"
)

# Move to docs/ (important references)
MOVE_TO_DOCS=(
    "SRC_CLEANUP_FINAL.md"
    "CLEANUP_GUIDE.md"
    "DEMO_INSTRUCTIONS.md"
    "END_TO_END_TESTING_GUIDE.md"
    "QUICK_TEST_DATA.md"
    "README_COMPLETE_GUIDE.md"
    "STREAMLIT_FASTAPI_INTEGRATION.md"
    "SYSTEM_ARCHITECTURE_DATA_FLOW.md"
    "UI_FEATURE_SHOWCASE.md"
)

# Archive old phase documentation
ARCHIVE_DOCS=(
    "PHASE1_COMPLETE.md"
    "PHASE1_DATA_PLAN.md"
    "PHASE2_COMPLETE.md"
    "PHASE2_EXTRACTION_COMPLETE.md"
    "PHASE2_OCR_OPTIMIZATION.md"
    "PHASE2_RESULTS.md"
    "PHASE3_CHECKLIST.md"
    "PHASE3_COMPLETE.md"
    "PHASE3_NEXT_STEPS.md"
    "PHASE3_OPTION_A_COMPLETE.md"
    "PHASE3_TEST_SUMMARY.md"
    "PHASE3_VALIDATION_ANALYSIS.md"
    "PHASE5_COMPLETE.md"
    "PHASE6_DATABASE_ARCHITECTURE.md"
    "PHASE6_IMPLEMENTATION.md"
    "PHASE7_COMPLETE.md"
    "PHASE8_COMPLETE.md"
    "PHASE8_QUICK_REFERENCE.md"
    "PHASE8_VERIFICATION_REPORT.md"
    "PHASE9_ASSESSMENT.md"
    "PHASE9_COMPLETION_REPORT.md"
    "PHASE9_DELIVERABLES_SUMMARY.md"
    "PHASE9_QUICK_REFERENCE.md"
    "PROJECT_STATUS_PHASE5.md"
    "PROJECT_STATUS.md"
    "REAL_SOLUTION_COMPLETE.md"
    "CODEBASE_ASSESSMENT.md"
    "assignment_deliverables.md"
)

# Move important docs
for doc in "${MOVE_TO_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        mv "$doc" docs/
        echo "  Moved $doc → docs/"
    fi
done

# Archive old documentation
for doc in "${ARCHIVE_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        mv "$doc" docs/archive/
        echo "  Moved $doc → docs/archive/"
    fi
done

echo "✅ Markdown files organized"

# ===== 5. Archive JSON and TXT files from root =====
echo "📄 Organizing data files..."

# Move test results to archive
JSON_TO_ARCHIVE=(
    "compliance_report.json"
    "decision_results.json"
    "extraction_results_test.json"
    "extraction_results.json"
    "ml_training_results.json"
    "phase6_test_results.json"
    "phase7_test_results.json"
    "phase8_audit_report.json"
    "phase8_governance_test_results.json"
    "phase8_verification_results.json"
    "phase9_integration_verification_results.json"
    "rigorous_test_results.json"
    "validation_test_results.json"
)

for json in "${JSON_TO_ARCHIVE[@]}"; do
    if [ -f "$json" ]; then
        mv "$json" tests/archive/
        echo "  Moved $json → tests/archive/"
    fi
done

# Move misc text files
TXT_FILES=(
    "ai_case_study.txt"
    "OCR_CAPABILITY_SUMMARY.txt"
)

for txt in "${TXT_FILES[@]}"; do
    if [ -f "$txt" ]; then
        mv "$txt" docs/archive/
        echo "  Moved $txt → docs/archive/"
    fi
done

echo "✅ Data files organized"

# ===== 6. Create logs/ directory (if needed) =====
echo "📋 Creating logs directory..."
mkdir -p logs
touch logs/.gitkeep
echo "✅ logs/ directory ready"

# ===== 7. Summary =====
echo ""
echo "=== ✅ Final Cleanup Complete ==="
echo ""
echo "📁 Project Structure:"
echo "   ├── README.md                 # Main entry point"
echo "   ├── start.sh                  # Quick start"
echo "   ├── pyproject.toml           # Dependencies"
echo "   ├── src/                     # 21 production files"
echo "   ├── models/                  # Active ML model (v2)"
echo "   ├── models_archive/          # Old models"
echo "   ├── data/                    # Databases"
echo "   ├── logs/                    # Application logs"
echo "   ├── tests/                   # Main test"
echo "   │   └── archive/            # Old tests"
echo "   ├── scripts/                 # Utility scripts"
echo "   ├── docs/                    # Documentation"
echo "   │   └── archive/            # Old docs"
echo "   └── streamlit_app/          # UI"
echo ""
echo "✨ Project is now recruiter-ready!"
echo ""
echo "Next steps:"
echo "1. Review Dockerfile, docker-compose.yml, deploy.sh (will be updated separately)"
echo "2. Test the application: ./start.sh"
echo "3. Run E2E test: python tests/test_real_files_e2e.py"
