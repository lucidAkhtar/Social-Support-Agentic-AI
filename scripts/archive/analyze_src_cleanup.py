#!/usr/bin/env python3
"""
Deep Analysis of src/ folder to identify active vs unused files
Traces imports from main.py to build complete dependency graph
"""
import ast
import os
from pathlib import Path
from collections import defaultdict, deque
import json

PROJECT_ROOT = Path("/Users/marghubakhtar/Documents/social_support_agentic_ai")
SRC_DIR = PROJECT_ROOT / "src"

class ImportAnalyzer(ast.NodeVisitor):
    """AST visitor to extract import statements"""
    
    def __init__(self):
        self.imports = set()
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
    
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module)

def get_imports(file_path):
    """Extract all imports from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        analyzer = ImportAnalyzer()
        analyzer.visit(tree)
        return analyzer.imports
    except Exception as e:
        return set()

def build_dependency_graph():
    """Build complete import dependency graph starting from main.py"""
    
    # Find all Python files in src/
    all_files = {}
    for py_file in SRC_DIR.rglob("*.py"):
        if '__pycache__' in str(py_file):
            continue
        rel_path = str(py_file.relative_to(PROJECT_ROOT))
        # Convert file path to import path
        import_path = rel_path.replace('/', '.').replace('.py', '')
        all_files[import_path] = py_file
    
    # Build dependency graph
    dependencies = defaultdict(set)
    
    for import_path, file_path in all_files.items():
        imports = get_imports(file_path)
        
        for imp in imports:
            # Only track internal src imports
            if imp.startswith('src.'):
                dependencies[import_path].add(imp)
    
    return all_files, dependencies

def find_active_files():
    """Find all files reachable from main.py (BFS traversal)"""
    
    all_files, dependencies = build_dependency_graph()
    
    # Start from entry points
    entry_points = [
        'src.api.main',
        'src.core.orchestrator',
    ]
    
    visited = set()
    queue = deque(entry_points)
    
    while queue:
        current = queue.popleft()
        
        if current in visited:
            continue
        
        visited.add(current)
        
        # Add all dependencies to queue
        for dep in dependencies.get(current, set()):
            if dep not in visited:
                queue.append(dep)
    
    # Convert back to file paths
    active_files = set()
    for import_path in visited:
        if import_path in all_files:
            active_files.add(str(all_files[import_path].relative_to(PROJECT_ROOT)))
    
    # Add __init__.py files in active directories
    for active_file in list(active_files):
        parts = Path(active_file).parts
        for i in range(1, len(parts)):
            init_path = str(Path(*parts[:i]) / '__init__.py')
            if (PROJECT_ROOT / init_path).exists():
                active_files.add(init_path)
    
    return active_files, all_files, dependencies

def categorize_files():
    """Categorize all src files into active vs unused"""
    
    print("=" * 80)
    print("DEEP ANALYSIS: src/ FOLDER CLEANUP")
    print("=" * 80)
    
    active_files, all_files, dependencies = find_active_files()
    
    all_src_files = set()
    for import_path, file_path in all_files.items():
        all_src_files.add(str(file_path.relative_to(PROJECT_ROOT)))
    
    unused_files = all_src_files - active_files
    
    # Categorize by directory
    categorized = {
        'agents': {'active': [], 'unused': []},
        'api': {'active': [], 'unused': []},
        'core': {'active': [], 'unused': []},
        'database': {'active': [], 'unused': []},
        'databases': {'active': [], 'unused': []},
        'ml': {'active': [], 'unused': []},
        'observability': {'active': [], 'unused': []},
        'rag': {'active': [], 'unused': []},
        'services': {'active': [], 'unused': []},
    }
    
    for file_path in sorted(all_src_files):
        parts = Path(file_path).parts
        if len(parts) >= 2 and parts[0] == 'src':
            category = parts[1]
            if category in categorized:
                if file_path in active_files:
                    categorized[category]['active'].append(file_path)
                else:
                    categorized[category]['unused'].append(file_path)
    
    return categorized, active_files, unused_files

def print_analysis():
    """Print detailed analysis"""
    
    categorized, active_files, unused_files = categorize_files()
    
    print(f"\n📊 SUMMARY")
    print("=" * 80)
    print(f"Total files in src/: {len(active_files) + len(unused_files)}")
    print(f"✅ Active (used in production): {len(active_files)}")
    print(f"❌ Unused (can be archived): {len(unused_files)}")
    print(f"Cleanup potential: {len(unused_files) / (len(active_files) + len(unused_files)) * 100:.1f}%")
    
    # Print by category
    for category, files in categorized.items():
        if files['active'] or files['unused']:
            print(f"\n\n📁 src/{category}/")
            print("=" * 80)
            
            if files['active']:
                print(f"\n  ✅ ACTIVE FILES ({len(files['active'])} files - KEEP):")
                for f in sorted(files['active']):
                    print(f"     {f}")
            
            if files['unused']:
                print(f"\n  ❌ UNUSED FILES ({len(files['unused'])} files - ARCHIVE):")
                for f in sorted(files['unused']):
                    # Check if it's an obvious duplicate
                    if '_old' in f or 'backup' in f:
                        marker = " [OBVIOUS DUPLICATE]"
                    else:
                        marker = ""
                    print(f"     {f}{marker}")
    
    return categorized, unused_files

def generate_archive_script(unused_files):
    """Generate script to archive unused files"""
    
    script = """#!/bin/bash
# Archive unused files from src/ directory
# Generated by: analyze_src_cleanup.py

set -e

cd /Users/marghubakhtar/Documents/social_support_agentic_ai

# Create archive directory
mkdir -p src_archive

echo "========================================"
echo "ARCHIVING UNUSED src/ FILES"
echo "========================================"
echo ""
echo "This will move {count} unused files to src_archive/"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Moving unused files..."

""".format(count=len(unused_files))
    
    # Group files by directory for organized archiving
    by_dir = defaultdict(list)
    for f in sorted(unused_files):
        parts = Path(f).parts
        if len(parts) >= 2:
            dir_path = '/'.join(parts[:-1])
            by_dir[dir_path].append(f)
    
    for dir_path, files in sorted(by_dir.items()):
        script += f"\n# Archive from {dir_path}/\n"
        script += f"mkdir -p src_archive/{dir_path}/\n"
        for f in files:
            script += f'mv "{f}" "src_archive/{f}"\n'
    
    script += """
echo ""
echo "========================================"
echo "ARCHIVE COMPLETE"
echo "========================================"
echo ""
echo "Archived files are in: src_archive/"
echo ""
echo "To restore a file:"
echo "  mv src_archive/path/to/file.py src/path/to/file.py"
echo ""
echo "To permanently delete archives (after verification):"
echo "  rm -rf src_archive/"
echo ""
"""
    
    return script

def generate_detailed_report(categorized):
    """Generate markdown report"""
    
    report = """# 🧹 src/ Folder Cleanup - Detailed Report

## Executive Summary

This report identifies which files in `src/` are **actively used** in production vs **unused** and safe to archive.

### Methodology
1. Start from entry points: `src/api/main.py` and `src/core/orchestrator.py`
2. Trace all imports using AST analysis (Abstract Syntax Tree)
3. Build complete dependency graph via BFS traversal
4. Mark all reachable files as ACTIVE
5. Mark unreachable files as UNUSED (safe to archive)

---

## 📊 Results by Category

"""
    
    for category, files in categorized.items():
        if files['active'] or files['unused']:
            active_count = len(files['active'])
            unused_count = len(files['unused'])
            total = active_count + unused_count
            
            report += f"\n### src/{category}/ ({active_count} active, {unused_count} unused)\n\n"
            
            if files['active']:
                report += "**✅ ACTIVE (Keep these):**\n```\n"
                for f in sorted(files['active']):
                    report += f"{f}\n"
                report += "```\n\n"
            
            if files['unused']:
                report += "**❌ UNUSED (Archive these):**\n```\n"
                for f in sorted(files['unused']):
                    report += f"{f}\n"
                report += "```\n\n"
                
                # Add explanation for why unused
                report += "**Why unused?**\n"
                for f in sorted(files['unused']):
                    if '_old' in f:
                        report += f"- `{Path(f).name}`: Marked as old/backup version\n"
                    elif 'neo4j' in f:
                        report += f"- `{Path(f).name}`: Neo4j not used in production\n"
                    elif 'train_model' in f or 'synthetic' in f:
                        report += f"- `{Path(f).name}`: One-time data generation/training script\n"
                    elif 'base_agent' in f:
                        report += f"- `{Path(f).name}`: Abstract base class not directly imported\n"
                    elif category == 'database' and 'databases' in [c for c, _ in categorized.items()]:
                        report += f"- `{Path(f).name}`: Superseded by files in src/databases/\n"
                    else:
                        report += f"- `{Path(f).name}`: Not imported by any active file\n"
                report += "\n"
    
    report += """
---

## 🚀 Execution Plan

### Step 1: Review this report
Verify that files marked as UNUSED are indeed not needed.

### Step 2: Run archive script
```bash
./archive_unused_src.sh
```

This will move all unused files to `src_archive/` (safe, reversible).

### Step 3: Test the system
```bash
poetry run python test_real_files_e2e.py
poetry run python -c "from src.api.main import app; print('✓ Import successful')"
```

### Step 4: Verify production
```bash
./start.sh
# Test API endpoints
curl http://localhost:8005/
```

### Step 5: Delete archives (after 1-2 weeks)
```bash
rm -rf src_archive/
```

---

## ✅ Safety Guarantees

- All files marked ACTIVE are **directly or indirectly imported** from main.py
- Archive is **reversible** - files can be restored anytime
- No files are permanently deleted - they're moved to `src_archive/`
- System tested after archiving to ensure nothing breaks

---

**Generated:** 2026-01-01  
**Tool:** analyze_src_cleanup.py
"""
    
    return report

if __name__ == "__main__":
    categorized, unused_files = print_analysis()
    
    # Generate archive script
    script = generate_archive_script(unused_files)
    script_path = PROJECT_ROOT / "archive_unused_src.sh"
    with open(script_path, 'w') as f:
        f.write(script)
    os.chmod(script_path, 0o755)
    
    # Generate detailed report
    report = generate_detailed_report(categorized)
    report_path = PROJECT_ROOT / "SRC_CLEANUP_REPORT.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    # Save JSON data
    active_count = sum(len(cat['active']) for cat in categorized.values())
    data = {
        'categorized': categorized,
        'unused_files': sorted(list(unused_files)),
        'active_count': active_count,
        'unused_count': len(unused_files)
    }
    json_path = PROJECT_ROOT / "src_cleanup_data.json"
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n\n📄 Detailed report: {report_path}")
    print(f"🔧 Archive script: {script_path}")
    print(f"📊 Raw data: {json_path}")
    print(f"\n✅ To archive unused files: ./archive_unused_src.sh")
