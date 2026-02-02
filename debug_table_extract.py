import pdfplumber
import sys
import os

def debug_tables(file_path, password=None):
    try:
        with pdfplumber.open(file_path, password=password) as pdf:
            print(f"Opening {os.path.basename(file_path)}...")
            for i, page in enumerate(pdf.pages):
                print(f"--- Page {i+1} ---")
                tables = page.extract_tables()
                if tables:
                    print(f"  Found {len(tables)} tables.")
                    for t_idx, table in enumerate(tables):
                        print(f"  Table {t_idx}:")
                        for r_idx, row in enumerate(table[:5]): # First 5 rows only
                            print(f"    Row {r_idx}: {row}")
                else:
                    print("  No tables found.")
    except Exception as e:
        print(f"Error opening {os.path.basename(file_path)}: {e}")

if __name__ == "__main__":
    # Try multiple files
    targets = [
        "data/raw_pdfs/9441175415575068_06122025.pdf",
        "data/raw_pdfs/AxisBank_December_2025.pdf" 
    ]
    
    for t in targets:
        if os.path.exists(t):
            debug_tables(t)
            print("="*50)
