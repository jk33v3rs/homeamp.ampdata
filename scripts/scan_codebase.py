#!/usr/bin/env python3
"""
Comprehensive Codebase Structure Extractor
Reads all Python files and extracts: classes, methods, functions, imports, line counts
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Any
import json

def extract_file_structure(file_path: Path) -> Dict[str, Any]:
    """Extract structural information from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        structure = {
            'path': str(file_path.relative_to(Path('e:/homeamp.ampdata/software/homeamp-config-manager'))),
            'lines': len(content.splitlines()),
            'classes': [],
            'functions': [],
            'imports': []
        }
        
        for node in ast.walk(tree):
            # Extract classes
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append({
                            'name': item.name,
                            'line': item.lineno,
                            'args': [arg.arg for arg in item.args.args]
                        })
                
                structure['classes'].append({
                    'name': node.name,
                    'line': node.lineno,
                    'methods': methods,
                    'bases': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
                })
            
            # Extract top-level functions
            elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                structure['functions'].append({
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args]
                })
            
            # Extract imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    structure['imports'].append({
                        'type': 'import',
                        'module': alias.name,
                        'asname': alias.asname
                    })
            
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    structure['imports'].append({
                        'type': 'from',
                        'module': node.module,
                        'name': alias.name,
                        'asname': alias.asname
                    })
        
        return structure
    
    except Exception as e:
        return {
            'path': str(file_path),
            'error': str(e),
            'lines': 0,
            'classes': [],
            'functions': [],
            'imports': []
        }

def scan_codebase(root_dir: Path) -> List[Dict[str, Any]]:
    """Scan all Python files in codebase"""
    structures = []
    
    for py_file in root_dir.rglob('*.py'):
        structure = extract_file_structure(py_file)
        structures.append(structure)
    
    return structures

# Run scan
root = Path('e:/homeamp.ampdata/software/homeamp-config-manager/src')
results = scan_codebase(root)

# Sort by path
results.sort(key=lambda x: x['path'])

# Output as JSON
output_file = Path('e:/homeamp.ampdata/WIP_PLAN/codebase_structure.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

# Print summary
print(f"Scanned {len(results)} Python files")
print(f"Total lines: {sum(r['lines'] for r in results)}")
print(f"Total classes: {sum(len(r['classes']) for r in results)}")
print(f"Total functions: {sum(len(r['functions']) for r in results)}")
print(f"\nResults saved to: {output_file}")

# Print file breakdown
print("\n=== FILE BREAKDOWN ===")
for r in results:
    print(f"{r['path']:60s} {r['lines']:5d} lines, {len(r['classes'])} classes, {len(r['functions'])} funcs")
