#!/usr/bin/env python3
"""
Asset Registry PDF Reader
Extracts text and tables from the ArSMP Asset Registry PDF files
"""

import pdfplumber
import pandas as pd
import sys
import os
from pathlib import Path

def extract_pdf_text(pdf_path):
    """Extract all text from a PDF file"""
    print(f"\n📄 Reading PDF: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        print(f"📊 Total pages: {len(pdf.pages)}")
        
        for i, page in enumerate(pdf.pages):
            print(f"Processing page {i+1}...")
            page_text = page.extract_text()
            if page_text:
                full_text += f"\n--- PAGE {i+1} ---\n"
                full_text += page_text + "\n"
        
        return full_text

def extract_pdf_tables(pdf_path):
    """Extract tables from a PDF file"""
    print(f"\n📋 Extracting tables from: {pdf_path}")
    
    tables_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"Checking page {i+1} for tables...")
            
            # Try to extract tables from the page
            tables = page.extract_tables()
            
            if tables:
                print(f"  Found {len(tables)} table(s) on page {i+1}")
                
                for j, table in enumerate(tables):
                    if table and len(table) > 0:
                        table_info = {
                            'page': i+1,
                            'table_number': j+1,
                            'rows': len(table),
                            'columns': len(table[0]) if table[0] else 0,
                            'data': table
                        }
                        tables_data.append(table_info)
            else:
                print(f"  No tables found on page {i+1}")
    
    return tables_data

def save_text_output(text, output_path):
    """Save extracted text to a file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"💾 Text saved to: {output_path}")

def save_tables_as_csv(tables_data, base_path):
    """Save tables as CSV files"""
    if not tables_data:
        print("❌ No tables found to save")
        return
    
    for table_info in tables_data:
        # Create filename based on page and table number
        csv_filename = f"{base_path}_page{table_info['page']}_table{table_info['table_number']}.csv"
        
        try:
            # Convert to DataFrame and save
            df = pd.DataFrame(table_info['data'])
            df.to_csv(csv_filename, index=False, header=False)
            print(f"💾 Table saved to: {csv_filename}")
            print(f"   📏 Size: {table_info['rows']} rows × {table_info['columns']} columns")
        except Exception as e:
            print(f"❌ Error saving table: {e}")

def process_asset_registry_pdfs():
    """Process all Asset Registry PDF files in the current directory"""
    current_dir = Path(".")
    pdf_files = list(current_dir.glob("Asset Registry ArSMP - Jun25 - *.pdf"))
    
    if not pdf_files:
        print("❌ No Asset Registry PDF files found!")
        print("Expected files matching pattern: 'Asset Registry ArSMP - Jun25 - *.pdf'")
        return
    
    print(f"🔍 Found {len(pdf_files)} Asset Registry PDF files:")
    for pdf_file in pdf_files:
        print(f"  📄 {pdf_file.name}")
    
    # Create output directory
    output_dir = Path("asset_registry_extracted")
    output_dir.mkdir(exist_ok=True)
    print(f"\n📁 Output directory: {output_dir}")
    
    # Process each PDF
    for pdf_file in pdf_files:
        print(f"\n{'='*60}")
        base_name = pdf_file.stem
        
        try:
            # Extract text
            text = extract_pdf_text(pdf_file)
            if text.strip():
                text_output = output_dir / f"{base_name}.txt"
                save_text_output(text, text_output)
            
            # Extract tables
            tables = extract_pdf_tables(pdf_file)
            if tables:
                csv_base = output_dir / base_name
                save_tables_as_csv(tables, str(csv_base))
            
            print(f"✅ Completed processing: {pdf_file.name}")
            
        except Exception as e:
            print(f"❌ Error processing {pdf_file.name}: {e}")

def read_excel_file(excel_path):
    """Read Excel file and save sheets as CSV"""
    print(f"\n📊 Reading Excel file: {excel_path}")
    
    try:
        # Read all sheets
        excel_data = pd.read_excel(excel_path, sheet_name=None)
        
        print(f"📋 Found {len(excel_data)} sheets:")
        for sheet_name in excel_data.keys():
            print(f"  📄 {sheet_name}")
        
        # Create output directory
        output_dir = Path("excel_extracted")
        output_dir.mkdir(exist_ok=True)
        
        # Save each sheet as CSV
        for sheet_name, df in excel_data.items():
            # Clean sheet name for filename
            clean_name = sheet_name.replace(' ', '_').replace('/', '_')
            csv_path = output_dir / f"{clean_name}.csv"
            
            df.to_csv(csv_path, index=False)
            print(f"💾 Sheet '{sheet_name}' saved to: {csv_path}")
            print(f"   📏 Size: {len(df)} rows × {len(df.columns)} columns")
        
        return excel_data
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Asset Registry PDF/Excel Reader")
    print("=" * 50)
    
    # Check for Excel file first
    excel_file = Path("Asset Registry ArSMP - Jun25.xlsx")
    if excel_file.exists():
        print(f"\n🎯 Found Excel file: {excel_file}")
        read_excel_file(excel_file)
    else:
        print(f"\n❌ Excel file not found: {excel_file}")
    
    # Process PDF files
    process_asset_registry_pdfs()
    
    print(f"\n🎉 Processing complete!")
    print(f"Check the 'asset_registry_extracted/' and 'excel_extracted/' folders for output files.")
