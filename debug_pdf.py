import pdfplumber
import sys
import os

def debug_pdf(file_path, password=None):
    print(f"--- Debugging {os.path.basename(file_path)} ---")
    
    try:
        with pdfplumber.open(file_path, password=password) as pdf:
            print(f"Pages: {len(pdf.pages)}")
            
            if not pdf.pages:
                print("No pages found.")
                return

            page = pdf.pages[0]
            text = page.extract_text()
            tables = page.extract_tables()
            
            print("\n--- First Page Text Preview (First 500 chars) ---")
            if text:
                print(text[:500])
            else:
                print("[No text extracted]")
                
            print("\n--- Table Extraction Preview ---")
            if tables:
                print(f"Found {len(tables)} tables on page 1.")
                # Print first row of first table
                print("First table, first row:", tables[0][0])
            else:
                print("No tables found on page 1.")
                
            # Heuristic Checks
            lower_text = (text or "").lower()
            if "credit card" in lower_text:
                print("\nHeuristic: Detected 'Credit Card'")
            elif "account statement" in lower_text:
                 print("\nHeuristic: Detected 'Account Statement'")
            elif "upi" in lower_text:
                 print("\nHeuristic: Detected 'UPI'")
            else:
                 print("\nHeuristic: Unsure, defaulting to BankExtractor")

    except Exception as e:
        print(f"\n❌ Error opening PDF: {repr(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 debug_pdf.py <pdf_path> [password]")
    else:
        fpath = sys.argv[1]
        pwd = sys.argv[2] if len(sys.argv) > 2 else None
        if pwd == "None": pwd = None
        debug_pdf(fpath, pwd)
