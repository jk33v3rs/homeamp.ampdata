#!/usr/bin/env python3
"""
Extract actual database schema requirements from Python codebase.
Scans all SQL queries and documents what tables/columns the code expects.
"""

import re
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List, Tuple

class SchemaExtractor:
    def __init__(self, codebase_path: str):
        self.codebase_path = Path(codebase_path)
        self.tables = defaultdict(lambda: {
            'columns': set(),
            'files': set(),
            'create_statements': [],
            'insert_statements': [],
            'select_statements': [],
            'update_statements': [],
            'delete_statements': []
        })
        
    def scan_file(self, file_path: Path):
        """Scan a Python file for SQL queries"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Find all SQL strings (both single and triple quoted)
            sql_patterns = [
                r'"""(.*?)"""',  # Triple double quotes
                r"'''(.*?)'''",  # Triple single quotes
                r'"([^"]*(?:CREATE TABLE|INSERT INTO|SELECT.*?FROM|UPDATE|DELETE FROM)[^"]*)"',  # Double quotes
                r"'([^']*(?:CREATE TABLE|INSERT INTO|SELECT.*?FROM|UPDATE|DELETE FROM)[^']*)'",  # Single quotes
            ]
            
            for pattern in sql_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    sql = match.group(1)
                    self.analyze_sql(sql, file_path)
                    
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
    
    def analyze_sql(self, sql: str, source_file: Path):
        """Analyze SQL statement and extract schema info"""
        sql = sql.strip()
        if not sql:
            return
            
        # CREATE TABLE
        create_match = re.search(r'CREATE TABLE(?:\s+IF NOT EXISTS)?\s+([a-z_]+)', sql, re.IGNORECASE)
        if create_match:
            table_name = create_match.group(1)
            self.tables[table_name]['files'].add(str(source_file.relative_to(self.codebase_path)))
            self.tables[table_name]['create_statements'].append(sql)
            
            # Extract ALL column definitions from CREATE statement
            # Match: column_name DATATYPE or column_name INT/VARCHAR/etc
            col_patterns = [
                r'^\s*([a-z_][a-z0-9_]*)\s+(?:INT|VARCHAR|TEXT|TIMESTAMP|BOOLEAN|ENUM|CHAR|DECIMAL|FLOAT|DOUBLE|DATETIME|DATE|TIME|TINYINT|SMALLINT|MEDIUMINT|BIGINT|JSON|BLOB|LONGTEXT|MEDIUMTEXT)',
                r'^\s*([a-z_][a-z0-9_]*)\s+[A-Z]',  # Any capitalized type
            ]
            for pattern in col_patterns:
                columns = re.findall(pattern, sql, re.MULTILINE | re.IGNORECASE)
                for col in columns:
                    if col.upper() not in ('PRIMARY', 'FOREIGN', 'KEY', 'INDEX', 'UNIQUE', 'CONSTRAINT', 'ENGINE', 'DEFAULT', 'NULL'):
                        self.tables[table_name]['columns'].add(col.lower())
        
        # INSERT INTO
        insert_match = re.search(r'INSERT INTO\s+([a-z_]+)\s*\((.*?)\)', sql, re.IGNORECASE | re.DOTALL)
        if insert_match:
            table_name = insert_match.group(1)
            columns_str = insert_match.group(2)
            self.tables[table_name]['files'].add(str(source_file.relative_to(self.codebase_path)))
            self.tables[table_name]['insert_statements'].append(sql[:200])
            
            # Extract column names - be more aggressive
            columns = re.findall(r'([a-z_][a-z0-9_]*)', columns_str, re.IGNORECASE)
            for col in columns:
                if col.upper() not in ('INTO', 'VALUES', 'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'ON', 'DUPLICATE', 'KEY', 'UPDATE'):
                    self.tables[table_name]['columns'].add(col.lower())
        
        # SELECT FROM - extract columns from SELECT clause
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM\s+([a-z_]+)', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            columns_str = select_match.group(1)
            table_name = select_match.group(2)
            self.tables[table_name]['files'].add(str(source_file.relative_to(self.codebase_path)))
            self.tables[table_name]['select_statements'].append(sql[:200])
            
            # Extract column names (unless SELECT *)
            if '*' not in columns_str:
                # Remove function calls like COUNT(), MAX(), etc
                columns_str = re.sub(r'(COUNT|MAX|MIN|SUM|AVG|DISTINCT)\s*\([^)]*\)', '', columns_str, flags=re.IGNORECASE)
                # Extract column names
                columns = re.findall(r'([a-z_][a-z0-9_]*)', columns_str, re.IGNORECASE)
                for col in columns:
                    if col.upper() not in ('SELECT', 'DISTINCT', 'AS', 'FROM', 'WHERE', 'COUNT', 'MAX', 'MIN', 'SUM', 'AVG', 'AND', 'OR', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'):
                        self.tables[table_name]['columns'].add(col.lower())
        
        # WHERE clauses - extract columns used in conditions
        where_matches = re.finditer(r'WHERE\s+(.+?)(?:ORDER BY|GROUP BY|LIMIT|$)', sql, re.IGNORECASE | re.DOTALL)
        for match in where_matches:
            where_clause = match.group(1)
            # Look for column references in WHERE clause (column = value, column IN, etc)
            col_refs = re.findall(r'([a-z_][a-z0-9_]*)\s*(?:=|!=|<|>|<=|>=|IN|LIKE|IS)', where_clause, re.IGNORECASE)
            for col in col_refs:
                if col.upper() not in ('SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'NULL', 'TRUE', 'FALSE'):
                    # Try to determine which table this belongs to
                    # Look backward in SQL to find table name
                    for table in self.tables.keys():
                        if table in sql.lower():
                            self.tables[table]['columns'].add(col.lower())
        
        # UPDATE - extract columns from SET clause
        update_match = re.search(r'UPDATE\s+([a-z_]+)\s+SET\s+(.+?)(?:WHERE|$)', sql, re.IGNORECASE | re.DOTALL)
        if update_match:
            table_name = update_match.group(1)
            set_clause = update_match.group(2)
            self.tables[table_name]['files'].add(str(source_file.relative_to(self.codebase_path)))
            self.tables[table_name]['update_statements'].append(sql[:200])
            
            # Extract ALL column names from SET clause
            columns = re.findall(r'([a-z_][a-z0-9_]*)\s*=', set_clause, re.IGNORECASE)
            for col in columns:
                self.tables[table_name]['columns'].add(col.lower())
        
        # DELETE FROM
        delete_match = re.search(r'DELETE FROM\s+([a-z_]+)', sql, re.IGNORECASE)
        if delete_match:
            table_name = delete_match.group(1)
            self.tables[table_name]['files'].add(str(source_file.relative_to(self.codebase_path)))
            self.tables[table_name]['delete_statements'].append(sql[:200])
        
        # ORDER BY - extract columns
        order_matches = re.finditer(r'ORDER BY\s+([a-z_][a-z0-9_,\s]*)', sql, re.IGNORECASE)
        for match in order_matches:
            order_cols = re.findall(r'([a-z_][a-z0-9_]*)', match.group(1), re.IGNORECASE)
            for col in order_cols:
                if col.upper() not in ('ASC', 'DESC', 'BY'):
                    # Associate with any table mentioned in the query
                    for table in self.tables.keys():
                        if table in sql.lower():
                            self.tables[table]['columns'].add(col.lower())
    
    def scan_directory(self):
        """Recursively scan all Python files"""
        python_files = list(self.codebase_path.rglob('*.py'))
        print(f"Scanning {len(python_files)} Python files...")
        
        for py_file in python_files:
            self.scan_file(py_file)
        
        print(f"Found {len(self.tables)} unique tables")
    
    def generate_markdown_report(self, output_path: str):
        """Generate comprehensive markdown report"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Database Schema Requirements (Extracted from Code)\n\n")
            f.write(f"**Generated:** {Path.cwd()}\n\n")
            f.write(f"**Total Tables Found:** {len(self.tables)}\n\n")
            f.write("---\n\n")
            
            f.write("## Table Summary\n\n")
            f.write("| # | Table Name | Columns Found | Files Referencing |\n")
            f.write("|---|------------|---------------|-------------------|\n")
            
            for idx, (table, info) in enumerate(sorted(self.tables.items()), 1):
                f.write(f"| {idx} | `{table}` | {len(info['columns'])} | {len(info['files'])} |\n")
            
            f.write("\n---\n\n")
            f.write("## Detailed Table Analysis\n\n")
            
            for table_name in sorted(self.tables.keys()):
                info = self.tables[table_name]
                f.write(f"### {table_name}\n\n")
                
                # Columns
                if info['columns']:
                    f.write("**Columns Used:**\n")
                    for col in sorted(info['columns']):
                        f.write(f"- `{col}`\n")
                    f.write("\n")
                
                # Files
                f.write("**Referenced In:**\n")
                for file in sorted(info['files']):
                    f.write(f"- `{file}`\n")
                f.write("\n")
                
                # CREATE statements
                if info['create_statements']:
                    f.write("**CREATE TABLE Statements:**\n")
                    for stmt in info['create_statements']:
                        f.write("```sql\n")
                        f.write(stmt[:500])  # Truncate very long statements
                        if len(stmt) > 500:
                            f.write("\n... (truncated)")
                        f.write("\n```\n\n")
                
                # Sample queries
                if info['insert_statements']:
                    f.write(f"**INSERT Operations:** {len(info['insert_statements'])} found\n\n")
                if info['select_statements']:
                    f.write(f"**SELECT Operations:** {len(info['select_statements'])} found\n\n")
                if info['update_statements']:
                    f.write(f"**UPDATE Operations:** {len(info['update_statements'])} found\n\n")
                if info['delete_statements']:
                    f.write(f"**DELETE Operations:** {len(info['delete_statements'])} found\n\n")
                
                f.write("---\n\n")
            
            # Generate SQL for missing tables
            f.write("## Recommended Schema (Minimal)\n\n")
            f.write("```sql\n")
            f.write("-- Tables that MUST exist based on code analysis\n")
            f.write("-- This is the MINIMUM schema needed for code to work\n\n")
            
            for table_name in sorted(self.tables.keys()):
                info = self.tables[table_name]
                
                # If we have a CREATE statement, use it
                if info['create_statements']:
                    f.write(f"{info['create_statements'][0]}\n\n")
                else:
                    # Generate basic structure from columns
                    f.write(f"CREATE TABLE IF NOT EXISTS {table_name} (\n")
                    f.write(f"    id INT AUTO_INCREMENT PRIMARY KEY,\n")
                    for col in sorted(info['columns']):
                        if col != 'id':
                            f.write(f"    {col} TEXT,  -- TODO: Determine proper type\n")
                    f.write(f"    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n")
                    f.write(f") ENGINE=InnoDB;\n\n")
            
            f.write("```\n")

def main():
    # Scan the homeamp-config-manager codebase
    codebase_path = Path(__file__).parent.parent / "software" / "homeamp-config-manager"
    
    if not codebase_path.exists():
        print(f"ERROR: Codebase not found at {codebase_path}")
        return
    
    print(f"Scanning codebase: {codebase_path}")
    
    extractor = SchemaExtractor(str(codebase_path))
    extractor.scan_directory()
    
    # Generate report
    output_path = Path(__file__).parent.parent / "DATABASE_SCHEMA_FROM_CODE.md"
    extractor.generate_markdown_report(str(output_path))
    
    print(f"\n✅ Report generated: {output_path}")
    print(f"   Found {len(extractor.tables)} tables")
    print("\nTop 10 tables by column count:")
    sorted_tables = sorted(extractor.tables.items(), key=lambda x: len(x[1]['columns']), reverse=True)
    for table, info in sorted_tables[:10]:
        print(f"   - {table}: {len(info['columns'])} columns, {len(info['files'])} files")

if __name__ == "__main__":
    main()
