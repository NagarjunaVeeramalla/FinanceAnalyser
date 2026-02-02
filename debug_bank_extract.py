from extractors.bank_extractor import BankExtractor
import sys
import os

# Mock the parser selection and just run BankExtractor directly
def test_bank_extractor(file_path, password=None):
    print(f"--- Testing BankExtractor on {os.path.basename(file_path)} ---")
    
    extractor = BankExtractor(file_path, password=password)
    
    try:
        # We want to see what happens INSIDE. 
        # Since I can't easily modify the class to print without affecting prod,
        # I'll replicate the fallback logic here with print statements to see why it fails.
        import pdfplumber
        from utils.date_utils import parse_date
        
        with pdfplumber.open(file_path, password=password) as pdf:
            print(f"Opened PDF. Pages: {len(pdf.pages)}")
            
            for page_num, page in enumerate(pdf.pages):
                print(f"\n--- Page {page_num+1} ---")
                text = page.extract_text()
                if not text:
                    print("  No text found on page.")
                    continue
                
                lines = text.split('\n')
                print(f"  Found {len(lines)} lines of text.")
                
                # Check first 20 lines to see structure
                print("  First 10 lines preview:")
                for i, line in enumerate(lines[:10]):
                    print(f"    [{i}] {line}")
                    
                print("\n  Analyzing lines for transactions:")
                for line in lines:
                    parts = line.split()
                    if len(parts) < 3:
                        # Too short
                        continue
                        
                    # Check extraction logic
                    date_part = parts[0]
                    # Try to parse date
                    date = parse_date(parts[0])
                    date_source = "Token 0"
                    
                    if not date:
                        date = parse_date(parts[1])
                        date_source = "Token 1"
                    
                    if date:
                        print(f"    ✅ DATE FOUND ({date_source}): {date} | Line: {line[:50]}...")
                        
                        # Now check amount logic
                        amount_found = False
                        for i in range(1, 4):
                             if len(parts) < i + 2: continue
                             token = parts[-i]
                             clean_token = token.replace(',', '').lower().replace('cr','').replace('dr','')
                             try:
                                 val = float(clean_token)
                                 print(f"      Potential Amount token [-{i}]: '{token}' -> {val}")
                                 
                                 # Replicate heuristic
                                 if val > 1900 and val < 2100 and float(token.replace(',','')) == val and '.' not in token:
                                     print("      -> Rejected as Year")
                                     continue
                                     
                                 print("      -> ACCEPTED as Amount")
                                 amount_found = True
                             except:
                                 pass
                        
                        if not amount_found:
                            print("      ❌ NO AMOUNT found in last 3 tokens.")
                    else:
                        # Only print misses that look promising (start with digits)
                        if parts[0][0].isdigit():
                            print(f"    ❌ Date Parse Failed: '{parts[0]}' & '{parts[1]}' | Line: {line[:40]}...")

    except Exception as e:
        print(f"Error during test: {repr(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 debug_bank_extract.py <pdf_path> [password]")
    else:
        fpath = sys.argv[1]
        pwd = sys.argv[2] if len(sys.argv) > 2 else None
        if pwd == "None": pwd = None
        test_bank_extractor(fpath, pwd)
