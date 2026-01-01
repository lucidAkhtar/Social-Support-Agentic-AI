#!/usr/bin/env python3
"""
Project Cleanup Analysis Tool
Identifies unused files, dependencies, and provides cleanup recommendations
"""
import os
import re
from pathlib import Path
from collections import defaultdict
import json

PROJECT_ROOT = Path("/Users/marghubakhtar/Documents/social_support_agentic_ai")

# Core production files that should NEVER be deleted
CORE_PRODUCTION_FILES = {
    'src/api/main.py',  # FastAPI server
    'src/core/orchestrator.py',  # Main orchestrator
    'src/core/types.py',  # Core data types
    'src/agents/extraction_agent.py',
    'src/agents/validation_agent.py',
    'src/agents/eligibility_agent.py',
    'src/agents/recommendation_agent.py',
    'src/agents/explanation_agent.py',
    'src/agents/rag_chatbot_agent.py',
    'src/databases/prod_sqlite_manager.py',
    'src/databases/unified_database_manager.py',
    'src/services/document_extractor.py',
    'pyproject.toml',
    'README.md',
    'start.sh',
}

def analyze_project():
    """Comprehensive project analysis"""
    
    results = {
        'markdown_files': [],
        'test_files': [],
        'python_files_in_src': [],
        'database_managers': [],
        'unused_files': [],
        'import_map': defaultdict(list),
        'file_sizes': {}
    }
    
    print("=" * 80)
    print("PROJECT CLEANUP ANALYSIS")
    print("=" * 80)
    
    # 1. Find all markdown files
    print("\n1. Analyzing Markdown Documentation...")
    md_files = list(PROJECT_ROOT.glob("*.md"))
    results['markdown_files'] = sorted([f.name for f in md_files])
    print(f"   Found {len(md_files)} markdown files in root")
    
    # 2. Find all test files
    print("\n2. Analyzing Test Files...")
    test_patterns = ['test*.py', '*test.py', '*_test.py']
    test_files = []
    for pattern in test_patterns:
        test_files.extend(PROJECT_ROOT.glob(pattern))
    results['test_files'] = sorted([f.name for f in test_files])
    print(f"   Found {len(test_files)} test files in root")
    
    # 3. Analyze src/ directory
    print("\n3. Analyzing src/ Directory...")
    src_path = PROJECT_ROOT / 'src'
    if src_path.exists():
        # Find all Python files
        all_py_files = list(src_path.rglob("*.py"))
        results['python_files_in_src'] = sorted([str(f.relative_to(PROJECT_ROOT)) for f in all_py_files])
        
        # Find database managers
        db_files = list(src_path.glob("databases/*.py"))
        results['database_managers'] = sorted([f.name for f in db_files])
        print(f"   Found {len(db_files)} database manager files")
        
        # Check for duplicate/old database managers
        db_managers = [f for f in db_files if 'manager' in f.name.lower()]
        if len(db_managers) > 3:
            print(f"   ⚠️  Warning: {len(db_managers)} database managers found (might have duplicates)")
    
    # 4. Analyze imports to build dependency graph
    print("\n4. Building Import Dependency Graph...")
    import_map = defaultdict(set)
    
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if '.venv' in str(py_file) or '__pycache__' in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find all imports
            imports = re.findall(r'from\s+(src\.[^\s]+)\s+import', content)
            imports += re.findall(r'import\s+(src\.[^\s]+)', content)
            
            rel_path = str(py_file.relative_to(PROJECT_ROOT))
            for imp in imports:
                # Convert import path to file path
                file_path = imp.replace('.', '/') + '.py'
                import_map[rel_path].add(file_path)
        except Exception as e:
            pass
    
    results['import_map'] = {k: list(v) for k, v in import_map.items()}
    
    # 5. Identify unused files
    print("\n5. Identifying Unused Files...")
    all_py_in_src = set(results['python_files_in_src'])
    imported_files = set()
    for imports in import_map.values():
        imported_files.update(imports)
    
    # Files that are never imported
    potentially_unused = all_py_in_src - imported_files
    
    # Filter out special files
    potentially_unused = {
        f for f in potentially_unused 
        if '__init__.py' not in f and 'main.py' not in f
    }
    
    results['unused_files'] = sorted(list(potentially_unused))
    print(f"   Found {len(results['unused_files'])} potentially unused Python files")
    
    # 6. Calculate file sizes
    print("\n6. Calculating File Sizes...")
    large_files = []
    for f in PROJECT_ROOT.rglob("*"):
        if f.is_file() and '.venv' not in str(f) and '__pycache__' not in str(f):
            size = f.stat().st_size
            if size > 50000:  # Files larger than 50KB
                large_files.append((str(f.relative_to(PROJECT_ROOT)), size))
    
    large_files.sort(key=lambda x: x[1], reverse=True)
    results['large_files'] = large_files[:20]  # Top 20 largest
    
    return results

def generate_cleanup_report(results):
    """Generate detailed cleanup recommendations"""
    
    print("\n" + "=" * 80)
    print("CLEANUP RECOMMENDATIONS")
    print("=" * 80)
    
    # Category 1: Markdown Documentation
    print("\n📄 MARKDOWN FILES (100 files)")
    print("=" * 80)
    
    # Categorize markdown files
    phase_docs = [f for f in results['markdown_files'] if 'PHASE' in f.upper()]
    status_docs = [f for f in results['markdown_files'] if 'STATUS' in f.upper() or 'COMPLETE' in f.upper()]
    guide_docs = [f for f in results['markdown_files'] if 'GUIDE' in f.upper() or 'INSTRUCTIONS' in f.upper()]
    other_docs = [f for f in results['markdown_files'] if f not in phase_docs + status_docs + guide_docs and f != 'README.md']
    
    print(f"\n  Phase Documentation: {len(phase_docs)} files")
    print("  📌 RECOMMENDATION: Move to docs/archive/phases/")
    for f in phase_docs[:5]:
        print(f"     - {f}")
    if len(phase_docs) > 5:
        print(f"     ... and {len(phase_docs) - 5} more")
    
    print(f"\n  Status Reports: {len(status_docs)} files")
    print("  📌 RECOMMENDATION: Move to docs/archive/status/")
    for f in status_docs[:5]:
        print(f"     - {f}")
    if len(status_docs) > 5:
        print(f"     ... and {len(status_docs) - 5} more")
    
    print(f"\n  Guides/Instructions: {len(guide_docs)} files")
    print("  📌 RECOMMENDATION: Keep in docs/ (actively used)")
    
    print(f"\n  Other Documentation: {len(other_docs)} files")
    print("  📌 RECOMMENDATION: Review individually")
    
    # Category 2: Test Files
    print("\n🧪 TEST FILES")
    print("=" * 80)
    test_categories = defaultdict(list)
    for f in results['test_files']:
        if 'phase' in f.lower():
            test_categories['Phase Tests'].append(f)
        elif 'integration' in f.lower():
            test_categories['Integration Tests'].append(f)
        elif 'e2e' in f.lower() or 'end_to_end' in f.lower():
            test_categories['E2E Tests'].append(f)
        elif 'complete' in f.lower() or 'full' in f.lower():
            test_categories['Complete Tests'].append(f)
        else:
            test_categories['Other Tests'].append(f)
    
    for category, files in test_categories.items():
        print(f"\n  {category}: {len(files)} files")
        if len(files) > 3:
            print(f"     Latest: {files[-1]}")
            print(f"  📌 RECOMMENDATION: Keep only latest 2-3, move rest to tests/archive/")
    
    # Category 3: Database Managers
    print("\n💾 DATABASE MANAGERS")
    print("=" * 80)
    db_managers = results['database_managers']
    print(f"  Found: {len(db_managers)} files")
    
    active_managers = ['prod_sqlite_manager.py', 'unified_database_manager.py', 
                      'tinydb_manager.py', 'chroma_manager.py', 'networkx_manager.py']
    
    for f in db_managers:
        if f in active_managers:
            print(f"  ✓ {f} - KEEP (actively used)")
        elif 'old' in f.lower() or 'backup' in f.lower():
            print(f"  ✗ {f} - DELETE (old/backup)")
        else:
            print(f"  ? {f} - REVIEW (unknown usage)")
    
    # Category 4: Unused Python Files
    print("\n🔍 POTENTIALLY UNUSED FILES")
    print("=" * 80)
    if results['unused_files']:
        print(f"  Found {len(results['unused_files'])} files not imported by any other file")
        print("  📌 RECOMMENDATION: Review and move to archive/ or delete")
        for f in results['unused_files'][:10]:
            print(f"     - {f}")
        if len(results['unused_files']) > 10:
            print(f"     ... and {len(results['unused_files']) - 10} more")
    else:
        print("  ✓ No obviously unused files found")
    
    # Category 5: Large Files
    print("\n📦 LARGEST FILES")
    print("=" * 80)
    print("  Top 10 largest files:")
    for file_path, size in results['large_files'][:10]:
        size_mb = size / (1024 * 1024)
        print(f"     {size_mb:6.2f} MB - {file_path}")

def generate_cleanup_script(results):
    """Generate automated cleanup script"""
    
    script = """#!/bin/bash
# Automated Project Cleanup Script
# Generated by analyze_project_cleanup.py

set -e  # Exit on error

echo "========================================"
echo "PROJECT CLEANUP SCRIPT"
echo "========================================"
echo ""
echo "This script will:"
echo "  1. Archive phase documentation"
echo "  2. Archive old test files"
echo "  3. Remove duplicate database managers"
echo "  4. Clean up unused Python files"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 0
fi

cd /Users/marghubakhtar/Documents/social_support_agentic_ai

# Create archive directories
mkdir -p docs/archive/phases
mkdir -p docs/archive/status
mkdir -p docs/archive/guides
mkdir -p tests/archive

echo ""
echo "1. Archiving phase documentation..."
"""
    
    # Add commands to move phase docs
    phase_docs = [f for f in results['markdown_files'] if 'PHASE' in f.upper()]
    for doc in phase_docs:
        script += f'mv "{doc}" docs/archive/phases/ 2>/dev/null || true\n'
    
    script += """
echo "   ✓ Phase docs archived"

echo ""
echo "2. Archiving status reports..."
"""
    
    # Add commands to move status docs
    status_docs = [f for f in results['markdown_files'] if 'STATUS' in f.upper() or 'COMPLETE' in f.upper()]
    for doc in status_docs:
        if doc != 'README.md':  # Never archive README
            script += f'mv "{doc}" docs/archive/status/ 2>/dev/null || true\n'
    
    script += """
echo "   ✓ Status reports archived"

echo ""
echo "3. Archiving old test files (keeping latest)..."
"""
    
    # Archive old test files (keep only latest 2)
    test_files = sorted(results['test_files'])
    if len(test_files) > 5:
        for test in test_files[:-5]:  # Keep last 5
            script += f'mv "{test}" tests/archive/ 2>/dev/null || true\n'
    
    script += """
echo "   ✓ Old tests archived"

echo ""
echo "4. Removing duplicate database managers..."
"""
    
    # Remove old database managers
    db_managers = results['database_managers']
    old_managers = [f for f in db_managers if 'old' in f.lower() or 'backup' in f.lower()]
    for mgr in old_managers:
        script += f'rm -f src/databases/{mgr}\n'
    
    script += """
echo "   ✓ Old database managers removed"

echo ""
echo "========================================"
echo "CLEANUP COMPLETE"
echo "========================================"
echo ""
echo "Summary:"
echo "  - Moved phase docs to docs/archive/phases/"
echo "  - Moved status reports to docs/archive/status/"
echo "  - Moved old tests to tests/archive/"
echo "  - Removed duplicate database managers"
echo ""
echo "Next steps:"
echo "  1. Review archived files"
echo "  2. Delete archives after verification"
echo "  3. Commit changes to git"
"""
    
    return script

if __name__ == "__main__":
    results = analyze_project()
    generate_cleanup_report(results)
    
    # Save detailed results
    output_file = PROJECT_ROOT / "cleanup_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n\n📊 Detailed analysis saved to: {output_file}")
    
    # Generate cleanup script
    script = generate_cleanup_script(results)
    script_file = PROJECT_ROOT / "cleanup_project.sh"
    with open(script_file, 'w') as f:
        f.write(script)
    os.chmod(script_file, 0o755)
    print(f"🔧 Cleanup script generated: {script_file}")
    print(f"\nTo execute cleanup: ./cleanup_project.sh")
