import os
import pandas as pd
from utils.file_utils import list_pdf_files, move_file
from processors.parser import Parser
from processors.categorizer import Categorizer
from processors.deduplicator import Deduplicator
from utils.hash_utils import generate_transaction_hash

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw_pdfs')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
MASTER_FILE = os.path.join(BASE_DIR, 'data', 'master_transactions.xlsx')

import re

def scan_and_process(file_paths=None, password=None, source=None):
    """
    Scans PDF files, extracts transactions, categorizes, but DOES NOT save to master.
    Args:
        file_paths (list): Optional list of specific file paths to process. If None, scans all in RAW_DIR.
    Returns: (DataFrame of new transactions, List of log messages)
    """
    print("Scaning and Processing PDFs...")
    logs = []
    
    # Ensure directories exist
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    # Initialize components
    categorizer = Categorizer()
    deduplicator = Deduplicator(MASTER_FILE)
    
    if file_paths:
        # Validate paths
        pdf_files = [p for p in file_paths if os.path.exists(p) and p.endswith('.pdf')]
    else:
        pdf_files = list_pdf_files(RAW_DIR)
    
    if not pdf_files:
        msg = "No PDF files found to process."
        print(msg)
        logs.append(msg)
        return pd.DataFrame(), logs

    new_transactions = []
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"Processing {filename}...")
        logs.append(f"Processing **{filename}**...")
        
        try:
            parser = Parser(pdf_path, password=password)
            extracted = parser.parse()
            count = len(extracted)
            print(f"  Extracted {count} transactions.")
            
            # Check for extractor-specific debug logs (from BaseExtractor)
            if hasattr(parser, 'extractor') and hasattr(parser.extractor, 'debug_logs'):
                 # ALWAYS show logs for debugging "No Changes" issue
                 logs.append("🔍 Detailed Extraction Trace:")
                 # Show last 50 logs
                 for debug_log in parser.extractor.debug_logs[-50:]: 
                     logs.append(f"- `{debug_log}`")
                 logs.append("--- End Trace ---")

            if count == 0:
                logs.append(f"⚠️ Extracted 0 transactions from {filename}. Check password or format.")
                # Show debug info
                if hasattr(parser, 'raw_text_debug') and parser.raw_text_debug:
                    logs.append("--- PDF Content Preview (First 3000 chars) ---")
                    logs.append(f"```{parser.raw_text_debug[:3000]}```")
                    logs.append("---------------------------------------------")
                continue
                
            dup_count = 0
            credit_skipped = 0
            
            for trans in extracted:
                # 0. Filter ONLY Debits
                # Assume parsers return 'type': 'DEBIT' or 'CREDIT'
                if trans.get('type') == 'CREDIT':
                    credit_skipped += 1
                    continue

                # Apply Source Override if provided
                if source:
                    trans['source'] = source

                # 1. Clean Description (Remove leading IDs)
                # Matches start of string, digits, optional space/hyphen
                original_desc = trans['description']
                cleaned_desc = re.sub(r'^\d+\s*[-]?\s*', '', original_desc).strip()
                # Also remove "UPI-" or similar prefixes if they remain? 
                # User's example had "UPI-2177..." inside the text? 
                # Let's clean standard ID first. User example: "12495376778 UPI-217748023465-NATURALS SS 7"
                # After removing leading digits: "UPI-217748023465-NATURALS SS 7"
                # Maybe generic regex for "UPI-xxxx-"? 
                cleaned_desc = re.sub(r'UPI-\d+-?', '', cleaned_desc).strip()
                
                trans['description'] = cleaned_desc

                # 2. Deduplicate (using cleaned description)
                if deduplicator.is_duplicate(trans):
                    print(f"  Skipping duplicate: {cleaned_desc} ({trans['amount']})")
                    dup_count += 1
                    continue
                    
                # 3. Categorize
                category = categorizer.categorize(cleaned_desc)
                
                # 4. Generate Hash (for storage)
                trans_hash = deduplicator.get_transaction_hash(trans)
                
                # 5. Format Date (remove time)
                date_val = trans['date']
                if hasattr(date_val, 'date'):
                    date_val = date_val.date() # YYYY-MM-DD object
                else:
                    try:
                        date_val = pd.to_datetime(date_val).date()
                    except:
                        pass # keep as is if fail
                
                new_transactions.append({
                    "Date": date_val,
                    "Transaction made at": cleaned_desc, # Renamed from Description
                    "Amount": trans['amount'],
                    "Category": category,
                    "Source": trans['source'],
                    "Hash": trans_hash,
                    "_filepath": pdf_path # Keep track of file to move later
                })
            
            if dup_count > 0 or credit_skipped > 0:
                logs.append(f"ℹ️ {filename}: Extracted {count}. New: {len(new_transactions)}. Skipped: {dup_count} Duplicates, {credit_skipped} Credits.")
            else:
                logs.append(f"✅ {filename}: Found {count} new transactions.")
                
        except Exception as e:
            err_msg = f"❌ Failed to process {filename}: {repr(e)}"
            if "Password" in repr(e) or "algorithm" in repr(e):
                err_msg += " (Check Password?)"
            print(err_msg)
            logs.append(err_msg)
            
    if new_transactions:
        return pd.DataFrame(new_transactions), logs
    else:
        return pd.DataFrame(), logs

def append_to_master(new_df):
    """
    Appends the provided DataFrame to the master excel file and moves processed PDFs.
    """
    if new_df.empty:
        return False
        
    # Valid columns only (exclude _filepath helper)
    # Note: 'Description' column is now 'Transaction made at'
    required_cols = ["Date", "Transaction made at", "Amount", "Category", "Source", "Hash"]
    
    # Load existing data or create new structure
    if os.path.exists(MASTER_FILE):
        try:
            master_df = pd.read_excel(MASTER_FILE)
            # Handle schema migration if needed
            if "Description" in master_df.columns and "Transaction made at" not in master_df.columns:
                master_df.rename(columns={"Description": "Transaction made at"}, inplace=True)
        except Exception:
             master_df = pd.DataFrame(columns=required_cols)
    else:
        master_df = pd.DataFrame(columns=required_cols)
        
    # Concatenate
    updated_df = pd.concat([master_df, new_df[required_cols]], ignore_index=True)
    
    # Ensure Date column is just date (no time)
    updated_df['Date'] = pd.to_datetime(updated_df['Date']).dt.date
    
    updated_df.to_excel(MASTER_FILE, index=False)
    print(f"Successfully added {len(new_df)} transactions to {MASTER_FILE}")
    
    # Move processed files
    if '_filepath' in new_df.columns:
        processed_files = new_df['_filepath'].unique()
        for pdf_path in processed_files:
            if os.path.exists(pdf_path):
                move_file(pdf_path, PROCESSED_DIR)
                print(f"Moved {os.path.basename(pdf_path)} to processed.")
                
    return True

if __name__ == "__main__":
    # CLI behavior - automatic
    df = scan_and_process()
    if not df.empty:
        append_to_master(df)
