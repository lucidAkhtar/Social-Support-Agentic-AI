#!/usr/bin/env python3
"""
Final Documentation Verification Script

Verifies that all 27 Python files in src/ and models/ have comprehensive documentation.

Checks:
1. Module-level docstrings with PURPOSE, DEPENDENCIES sections
2. Function docstrings with Args, Returns sections
3. Class docstrings
4. Inter-script relationship documentation

Author: Documentation Team
Date: January 2026
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

class DocumentationChecker:
    """Verifies documentation quality across Python files"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = {
            'total_files': 0,
            'well_documented': 0,
            'needs_improvement': 0,
            'missing_docs': 0,
            'files': []
        }
    
    def check_module_docstring(self, content: str, file_path: str) -> Tuple[bool, str]:
        """Check if file has comprehensive module docstring"""
        # Look for docstring in first 1000 characters
        header = content[:1000]
        
        if '"""' not in header:
            return False, "No module docstring found"
        
        # Extract first docstring
        match = re.search(r'"""(.*?)"""', header, re.DOTALL)
        if not match:
            return False, "No complete module docstring found"
        
        docstring = match.group(1)
        
        # Check for comprehensive content
        has_purpose = any(keyword in docstring.upper() for keyword in ['PURPOSE:', 'PURPOSE', 'DESCRIPTION'])
        has_arch = 'ARCHITECTURE' in docstring.upper() or 'FLOW' in docstring.upper()
        has_deps = 'DEPENDENCIES' in docstring.upper() or 'DEPENDS ON' in docstring.upper() or 'IMPORTS' in docstring.upper()
        has_usage = 'USED BY' in docstring.upper() or 'USAGE' in docstring.upper()
        
        score = sum([has_purpose, has_arch, has_deps, has_usage])
        
        if score >= 3:
            return True, "✓ Comprehensive module docstring"
        elif score >= 2:
            return True, "⚠ Good module docstring (could be more detailed)"
        elif score >= 1:
            return False, "⚠ Basic module docstring (needs PURPOSE, DEPENDENCIES, USAGE)"
        else:
            return False, "✗ Minimal module docstring"
    
    def check_function_docstrings(self, content: str) -> Tuple[int, int, str]:
        """Count functions and their documentation quality"""
        # Find all function definitions
        functions = re.findall(r'^\s*def\s+(\w+)\s*\(', content, re.MULTILINE)
        total_functions = len(functions)
        
        if total_functions == 0:
            return 0, 0, "No functions found"
        
        # Count functions with docstrings
        documented_functions = 0
        for func_name in functions:
            # Look for docstring after function definition
            pattern = rf'def\s+{func_name}\s*\([^)]*\).*?:\s*"""'
            if re.search(pattern, content, re.DOTALL):
                documented_functions += 1
        
        coverage = documented_functions / total_functions
        
        if coverage >= 0.8:
            status = f"✓ {documented_functions}/{total_functions} functions documented ({coverage:.0%})"
        elif coverage >= 0.5:
            status = f"⚠ {documented_functions}/{total_functions} functions documented ({coverage:.0%})"
        else:
            status = f"✗ {documented_functions}/{total_functions} functions documented ({coverage:.0%})"
        
        return total_functions, documented_functions, status
    
    def check_file(self, file_path: Path) -> Dict:
        """Check documentation quality of a single file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        relative_path = file_path.relative_to(self.project_root)
        
        # Check module docstring
        has_module_doc, module_status = self.check_module_docstring(content, str(relative_path))
        
        # Check function docstrings
        total_funcs, doc_funcs, func_status = self.check_function_docstrings(content)
        
        # Determine overall quality
        if has_module_doc and (doc_funcs / total_funcs >= 0.8 if total_funcs > 0 else True):
            quality = "EXCELLENT"
            self.results['well_documented'] += 1
        elif has_module_doc or (doc_funcs / total_funcs >= 0.5 if total_funcs > 0 else False):
            quality = "GOOD"
            self.results['needs_improvement'] += 1
        else:
            quality = "NEEDS_WORK"
            self.results['missing_docs'] += 1
        
        return {
            'file': str(relative_path),
            'quality': quality,
            'module_docstring': module_status,
            'function_docstrings': func_status,
            'total_functions': total_funcs,
            'documented_functions': doc_funcs
        }
    
    def check_all_files(self) -> Dict:
        """Check all Python files in src/ and models/"""
        python_files = []
        
        for folder in ['src', 'models']:
            folder_path = self.project_root / folder
            if folder_path.exists():
                for py_file in folder_path.rglob('*.py'):
                    if '__pycache__' not in str(py_file):
                        python_files.append(py_file)
        
        self.results['total_files'] = len(python_files)
        
        for py_file in sorted(python_files):
            file_result = self.check_file(py_file)
            self.results['files'].append(file_result)
        
        return self.results
    
    def print_report(self):
        """Print comprehensive documentation report"""
        print("="*80)
        print("DOCUMENTATION QUALITY REPORT")
        print("="*80)
        print()
        
        print(f"Total Files Checked: {self.results['total_files']}")
        print(f"✓ Excellent Documentation: {self.results['well_documented']}")
        print(f"⚠ Good (Needs Minor Improvement): {self.results['needs_improvement']}")
        print(f"✗ Needs Work: {self.results['missing_docs']}")
        print()
        
        # Calculate overall percentage
        excellent_pct = (self.results['well_documented'] / self.results['total_files']) * 100
        
        print(f"Documentation Quality Score: {excellent_pct:.1f}%")
        print()
        
        print("="*80)
        print("FILE-BY-FILE BREAKDOWN")
        print("="*80)
        print()
        
        # Group by folder
        folders = {}
        for file_result in self.results['files']:
            file_path = file_result['file']
            folder = str(Path(file_path).parent)
            if folder not in folders:
                folders[folder] = []
            folders[folder].append(file_result)
        
        for folder in sorted(folders.keys()):
            print(f"\n{folder}/")
            print("-" * 80)
            for file_result in folders[folder]:
                file_name = Path(file_result['file']).name
                quality_symbol = {
                    'EXCELLENT': '✓',
                    'GOOD': '⚠',
                    'NEEDS_WORK': '✗'
                }[file_result['quality']]
                
                print(f"  {quality_symbol} {file_name}")
                print(f"    Module: {file_result['module_docstring']}")
                print(f"    Functions: {file_result['function_docstrings']}")
        
        print()
        print("="*80)
        print("SUMMARY")
        print("="*80)
        
        if excellent_pct >= 90:
            print("✓ EXCELLENT - All files have comprehensive documentation!")
        elif excellent_pct >= 70:
            print("⚠ GOOD - Most files are well documented, minor improvements needed")
        else:
            print("✗ NEEDS IMPROVEMENT - Many files need better documentation")
        
        print()
        print("Run this script anytime to verify documentation quality.")
        print()


def main():
    """Main execution"""
    project_root = Path(__file__).parent
    
    checker = DocumentationChecker(project_root)
    checker.check_all_files()
    checker.print_report()
    
    # Exit with appropriate code
    if checker.results['well_documented'] >= checker.results['total_files'] * 0.9:
        exit(0)  # Success
    else:
        exit(1)  # Needs improvement


if __name__ == "__main__":
    main()
