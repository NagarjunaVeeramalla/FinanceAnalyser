from .base_extractor import BaseExtractor
from utils.date_utils import parse_date
import pdfplumber

class CreditCardExtractor(BaseExtractor):
    def extract_transactions(self):
        transactions = []
        with pdfplumber.open(self.file_path, password=self.password) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                # text = page.extract_text()    
                # (Processed in loop)

                for line in text.split('\n'):
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                        
                    desc_start_index = 1
                    
                    # 1. Try Date parsing
                    # Case A: Date is one token (e.g. 25/11/2025)
                    date = parse_date(parts[0])
                    
                    if not date:
                        date = parse_date(parts[1])
                        desc_start_index = 2
                    
                    # Case B: Date is 3 tokens (e.g. 25 Nov 25)
                    if not date and len(parts) >= 3:
                        # Try combining first 3 tokens
                        combined_date = f"{parts[0]} {parts[1]} {parts[2]}"
                        date = parse_date(combined_date)
                        if date:
                            desc_start_index = 3
                        else:
                            # Maybe starts at index 1? (e.g. "1. 25 Nov 25")
                            if len(parts) >= 4:
                                combined_date_2 = f"{parts[1]} {parts[2]} {parts[3]}"
                                date = parse_date(combined_date_2)
                                if date:
                                    desc_start_index = 4

                    if not date:
                         # self.debug_logs.append(f"Skipped CC Line (No Date): {line[:40]}...")
                         continue
                        
                    # 2. Search for Amount from the end
                    # Credit Card statements usually have Amount at very end, or Amount CR/DR
                    amount = 0.0
                    trans_type = "DEBIT"
                    found_amount = False
                    
                    # Look at last 3 tokens
                    for i in range(1, 4):
                        if len(parts) < i + desc_start_index: break
                        
                        token = parts[-i]
                        # Clean token
                        clean_token = token.replace(',', '').lower()
                        
                        is_credit = False
                        if 'cr' in clean_token or clean_token.endswith('c'):
                            # SBI format: 36,089.00 C
                            is_credit = True
                            clean_token = clean_token.replace('cr', '').replace('c', '', 1) 
                            # Be careful stripping 'c' from generic words, but here we assume it's suffix
                            # Actually, safely handle "C" or "Cr"
                        
                        if 'dr' in clean_token or clean_token.endswith('d'):
                             clean_token = clean_token.replace('dr', '').replace('d', '', 1)

                        # Validate structure before converting float
                        # Must have decimal or be explicitly marked cr/dr, or be standard currency format
                        # Reject plain Pincodes (6 digits, no punctuation)
                        if not any(c in token for c in ['.', ',', 'Cr', 'Dr', 'cr', 'dr', 'C', 'D']) and token.isdigit() and len(token) >= 4:
                            continue

                        try:
                            val = float(clean_token)
                             # Reject years 2024, 2025 etc if they appear as amount
                            if val > 2000 and val < 2030 and val.is_integer():
                                continue

                            amount = val
                            
                            # Check credit/debit markers
                            # Case 1: Marker is part of the token (e.g., "123.00Cr" or "123.00C")
                            if is_credit or token.endswith('C') or token.lower().endswith('cr'): 
                                trans_type = "CREDIT"
                            elif token.endswith('D') or token.lower().endswith('dr'):
                                trans_type = "DEBIT"
                                
                            # Case 2: Marker is the NEXT token (e.g., "123.00" then "Cr" or "C")
                            # We are at i (backwards 1-based index).
                            # If i > 1, there is a token after this one at parts[-i+1]
                            if i > 1:
                                next_token = parts[-i+1]
                                if next_token.lower() in ['cr', 'c']:
                                    trans_type = "CREDIT"
                                elif next_token.lower() in ['dr', 'd']:
                                    trans_type = "DEBIT" # Explicitly debit
                            
                            # Determine Description
                            desc_end_index = -i
                            description = " ".join(parts[desc_start_index:desc_end_index])
                            
                            # Final sanity check on description
                            if not description.strip():
                                continue
                                
                            found_amount = True
                            
                            # Use internal debug logs instead of file
                            self.debug_logs.append(f"  [ACCEPTED-CC] Date: {date} | Amt: {amount} | Type: {trans_type}")
                            break
                        except ValueError:
                             continue
                            
                    if not found_amount:
                        self.debug_logs.append(f"  [FAIL-AMT-CC] Date found ({date}) but no amount in last 3 tokens: {parts[-3:]}")

                    if found_amount:
                        transactions.append({
                            "date": date,
                            "description": description,
                            "amount": amount,
                            "type": trans_type,
                            "source": "Credit Card"
                        })
                        
        self.transactions = transactions
        return transactions
