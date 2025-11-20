#!/usr/bin/env python3
"""
Comprehensive Documentation Summarizer
Reads all markdown files and creates a consolidated summary
"""

import os
from pathlib import Path
from datetime import datetime

def summarize_file(filepath):
    """Read and summarize a markdown file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract first 150 lines or 3000 chars for summary
        lines = content.split('\n')
        if len(lines) > 150:
            summary = '\n'.join(lines[:150]) + '\n\n... [File continues beyond 150 lines]'
        elif len(content) > 3000:
            summary = content[:3000] + '\n\n... [Content truncated]'
        else:
            summary = content
        
        return summary
    except Exception as e:
        return f"Error reading file: {e}"

def main():
    # Get all markdown files
    md_files = list(Path('.').rglob('*.md'))
    
    # Exclude specific files
    exclude = {'DOCUMENTATION_SUMMARY.md', 'markdown_files.txt'}
    md_files = [f for f in md_files if f.name not in exclude and '.conda' not in str(f)]
    
    # Sort by category
    root_docs = [f for f in md_files if f.parent == Path('.')]
    wip_docs = [f for f in md_files if 'WIP_PLAN' in str(f)]
    software_docs = [f for f in md_files if 'software' in str(f)]
    other_docs = [f for f in md_files if f not in root_docs + wip_docs + software_docs]
    
    # Create summary
    summary = f"""# ArchiveSMP Complete Documentation Summary

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Files**: {len(md_files)}

---

# Table of Contents

1. [Root Documentation](#root-documentation) ({len(root_docs)} files)
2. [WIP Planning Documents](#wip-planning-documents) ({len(wip_docs)} files)
3. [Software Documentation](#software-documentation) ({len(software_docs)} files)
4. [Other Documentation](#other-documentation) ({len(other_docs)} files)

---

"""
    
    # Process each category
    categories = [
        ("Root Documentation", root_docs),
        ("WIP Planning Documents", wip_docs),
        ("Software Documentation", software_docs),
        ("Other Documentation", other_docs)
    ]
    
    for cat_name, files in categories:
        if not files:
            continue
            
        summary += f"\n# {cat_name}\n\n"
        
        for filepath in sorted(files):
            rel_path = filepath.relative_to('.')
            summary += f"\n## 📄 {rel_path}\n\n"
            summary += summarize_file(filepath)
            summary += "\n\n---\n"
    
    # Write summary
    with open('DOCUMENTATION_SUMMARY.md', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"✅ Summary created: DOCUMENTATION_SUMMARY.md")
    print(f"   Total files processed: {len(md_files)}")
    print(f"   - Root: {len(root_docs)}")
    print(f"   - WIP: {len(wip_docs)}")
    print(f"   - Software: {len(software_docs)}")
    print(f"   - Other: {len(other_docs)}")

if __name__ == '__main__':
    main()
