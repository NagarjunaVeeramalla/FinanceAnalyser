import re
import pdfplumber
from .base_extractor import BaseExtractor
from utils.date_utils import parse_date

class BankExtractor(BaseExtractor):
    def extract_transactions(self):
        """
        Tries to extract transactions from table-like structures in bank statements.
        """
        transactions = []
        
        with pdfplumber.open(self.file_path, password=self.password) as pdf:
            self.previous_balance = None
            for i, page in enumerate(pdf.pages):
                page_transactions = []
                print(f"  Processing Page {i+1}...")
                
                # Reset balance tracking per page? No, it should be continuous if logical order.
                # But typically PDFs flow linearly.
                # We need to be careful if pages are out of order, but usually they are not.
                # We'll initialize it to None at start of method (which it is).
                
                # Method A: Table Extraction
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            if not row or len(row) < 3: continue
                            
                            # (Existing table row logic...)
                            # Simplified for brevity, need to copy the FULL logic from before?
                            # YES, I must include the full logic or I will delete it.
                            # Since I am using replace_file_content, I need to provide the full replacement block 
                            # or be very careful with lines.
                            # It's better to wrap the logic in a helper or just copy-paste.
                            # Given the tool's constraints, I will inline the table logic here.
                            
                            # Smart Column Merging Logic
                            row = [str(cell) if cell else "" for cell in row]
                            self.debug_logs.append(f"Row: {row}")
                            
                            # 1. Identify Date Column
                            date = parse_date(row[0])
                            date_idx = 0
                            if not date: 
                                date = parse_date(row[1])
                                date_idx = 1
                            if not date: 
                                self.debug_logs.append(f"  Skipped (No Date): {row}")
                                continue
                            
                            # 2. Identify Amounts (Scan all columns)
                            # We collect ALL numbers in the row to distinguish Amount vs Balance
                            numerical_cells = []
                            for i in range(len(row)):
                                if i <= date_idx: continue
                                col_val = row[i].strip()
                                clean_val = col_val.replace(',', '').replace('Cr', '').replace('Dr', '')
                                if not clean_val: continue
                                try:
                                    val = float(clean_val)
                                    # Filter simple integers that look like years or IDs if needed, 
                                    # but inside a table, numbers are usually money.
                                    numerical_cells.append({'val': val, 'idx': i, 'txt': col_val})
                                except ValueError:
                                    pass
                            
                            current_balance = None
                            amount = 0.0
                            trans_type = "DEBIT" # Default, but math will override
                            amount_idx = -1
                            
                            if not numerical_cells:
                                 # No numbers, skip
                                 continue
                                 
                            # Logic:
                            # If >= 2 numbers: Right-most is Balance, Second-right is Amount.
                            # If 1 number: Could be just Balance (B/F line) or just Amount (if Balance col missing).
                            
                            if len(numerical_cells) >= 2:
                                current_balance = numerical_cells[-1]['val']
                                amount = numerical_cells[-2]['val']
                                amount_idx = numerical_cells[-2]['idx']
                                
                                # Math Check for Type (Crucial for Deposit vs Withdrawal columns)
                                if self.previous_balance is not None:
                                    diff = current_balance - self.previous_balance
                                    if abs(diff - amount) < 1.0: # lenient float
                                        trans_type = "CREDIT"
                                    elif abs(diff + amount) < 1.0:
                                        trans_type = "DEBIT"
                                    # Else: Math didn't match perfectly. Trust explicit markers if any, or default.
                                    
                                # explicit markers check
                                target_cell_txt = numerical_cells[-2]['txt']
                                if 'Cr' in target_cell_txt or 'Cr' in str(row): trans_type = "CREDIT"
                                elif 'Dr' in target_cell_txt: trans_type = "DEBIT"
                                
                            elif len(numerical_cells) == 1:
                                # Only 1 number.
                                val = numerical_cells[0]['val']
                                # If B/F line, it's balance.
                                if "B/F" in str(row) or "BROUGHT FORWARD" in str(row).upper():
                                    current_balance = val
                                    self.debug_logs.append(f"  Start Balance (Table): {current_balance}")
                                    if self.previous_balance is None: self.previous_balance = current_balance
                                    continue
                                else:
                                    # Ambiguous. Is it Amount or Balance?
                                    # If we have previous balance, check if this val is close to it?
                                    if self.previous_balance is not None and abs(val - self.previous_balance) < (val * 0.1):
                                        # Likely just a balance update line?
                                        current_balance = val
                                        # Skip transaction
                                        amount = 0.0
                                    else:
                                        # Assume Amount?
                                        amount = val
                                        amount_idx = numerical_cells[0]['idx']
                                        if 'Cr' in numerical_cells[0]['txt']: trans_type = "CREDIT"
                                
                            # Update Balance State
                            if current_balance is not None:
                                self.previous_balance = current_balance
                            
                            if amount <= 0:
                                continue

                            # 3. Join Description Columns
                            # Everything between date_idx and amount_idx
                            desc_parts = []
                            
                            # Check merging in date cell
                            date_cell_text = row[date_idx]
                            date_regex = r'\d{2}[/-]\d{2}[/-]\d{4}'
                            date_match = re.search(date_regex, date_cell_text)
                            if date_match:
                                leftover = date_cell_text.replace(date_match.group(0), "").strip()
                                if leftover:
                                    desc_parts.append(leftover)

                            # Add intermediate columns
                            for k in range(date_idx + 1, amount_idx):
                                if row[k].strip():
                                    desc_parts.append(row[k].strip())
                                    
                            full_desc = " ".join(desc_parts)
                            self.debug_logs.append(f"  Raw Desc: '{full_desc}'")
                            
                            if amount > 0:
                                description = self._clean_description(full_desc.replace("\n", " "))
                                self.debug_logs.append(f"  Cleaned: '{description}'")
                                page_transactions.append({
                                    "date": date,
                                    "description": description,
                                    "amount": amount,
                                    "type": trans_type,
                                    "source": "Bank"
                                })

                # Method B: Text Fallback (if A failed for this page)
                if not page_transactions:
                    # print(f"    No table transactions on Page {i+1}. Trying text fallback...")
                    text = page.extract_text()
                    if text:
                        lines = text.split('\n')
                        self.previous_line_content = None
                        for line in lines:
                             # (Existing text logic)
                            parts = line.split()
                            if len(parts) < 3: continue
                            
                            date = parse_date(parts[0])
                            if not date: 
                                date = parse_date(parts[1])
                                if not date: 
                                    # Store content before skipping
                                    self.previous_line_content = " ".join(parts)
                                    # self.debug_logs.append(f"  Skipped (No Date, Stored): {self.previous_line_content}")
                                    continue
                                
                            # self.debug_logs.append(f"Processing Line: {line[:50]}... | Date: {date}")

                            # Logic to handle "Amount" vs "Balance" columns
                            # We scan from the end. If we find TWO numbers, the last one is likely Balance.
                            amount_candidates = [] # List of (val, index_k, token)
                            
                            for k in range(1, 5): # Check last 4 tokens
                                if len(parts) < k + 2: break
                                token = parts[-k]
                                clean_token = token.replace(',', '').lower()
                                
                                # Check for Credit/Debit suffixes
                                is_credit_suffix = False
                                is_debit_suffix = False
                                if 'cr' in clean_token: 
                                    is_credit_suffix = True
                                    clean_token = clean_token.replace('cr', '')
                                if 'dr' in clean_token:
                                    clean_token = clean_token.replace('dr', '')
                                    is_debit_suffix = True
                                    
                                try:
                                    val = float(clean_token)
                                    # Heuristics to reject non-amounts
                                    # 1. Year check (1900-2100) if looks like integer
                                    if val > 1900 and val < 2100 and float(token.replace(',','')) == val and '.' not in token:
                                        # self.debug_logs.append(f"  Rejected token {token} (Year-like)")
                                        continue
                                    # 2. Pincode check (large integer, no decimal) - e.g., 500062
                                    if val > 10000 and float(token.replace(',','')) == val and '.' not in token:
                                        # self.debug_logs.append(f"  Rejected token {token} (Pincode-like)")
                                        continue
                                        
                                    amount_candidates.append({
                                        'val': val,
                                        'k': k,
                                        'token': token,
                                        'is_credit': is_credit_suffix,
                                        'is_debit': is_debit_suffix,
                                        'clean_token': clean_token
                                    })
                                except ValueError:
                                    continue
                            
                            if not amount_candidates:
                                self.previous_line_content = " ".join(parts)
                                self.debug_logs.append(f"Skipped Line (No Valid Amount Candidates): {line[:30]}... Params: {parts[-4:]}")
                                continue
                                
                            # Decision Logic:
                            # If 2+ candidates -> The one with smaller 'k' (right-most) is Balance. The one to its left is Amount.
                            # If 1 candidate -> It is likely just the Balance (Amount missing or header/footer line).
                            # We should NOT use it as a transaction amount to avoid corrupting data with balance values.
                            
                            current_balance = None
                            amount = None
                            k = 0
                            selected = None

                            if len(amount_candidates) == 1:
                                # Only one number found. Assume it's Balance.
                                current_balance = amount_candidates[0]['val']
                                self.debug_logs.append(f"  Skipped Line (Single Number): Found {current_balance} (treated as Balance). Transaction Amount missing.")
                                # We treat this as a balance update but NO transaction.
                                # Update previous balance and continue?
                                if self.previous_balance is None:
                                     self.previous_balance = current_balance
                                else:
                                     # Optionally check continuity?
                                     self.previous_balance = current_balance
                                
                                # Store this line too? Maybe the description is here but amount missing?
                                self.previous_line_content = " ".join(parts)
                                continue

                            elif len(amount_candidates) > 1:
                                # Candidate 0 is right-most (Balance). Candidate 1 is to its left (Amount).
                                self.debug_logs.append(f"  Found Multiple Amounts: {[c['val'] for c in amount_candidates]}. Choosing {amount_candidates[1]['val']} over {amount_candidates[0]['val']}")
                                
                                current_balance = amount_candidates[0]['val']
                                selected = amount_candidates[1]
                                amount = selected['val']
                                k = selected['k']
                                
                            if amount is None:
                                continue
                            
                            # 1. Check intrinsic suffixes
                            if selected['is_credit']: trans_type = "CREDIT"
                            elif selected['token'].lower().endswith('cr'): trans_type = "CREDIT"
                            
                            # 2. Check detached marker (next token, i.e., k-1)
                            if k > 1: # if we are not at the very end
                                next_token = parts[-k+1].lower()
                                if 'cr' in next_token: trans_type = "CREDIT"
                                elif 'dr' in next_token: trans_type = "DEBIT"
                                
                            # 3. Balance Math Check (The specific fix for ICICI without Cr/Dr markers)
                            if current_balance is not None and hasattr(self, 'previous_balance') and self.previous_balance is not None:
                                diff = current_balance - self.previous_balance
                                # Allow small float error
                                if abs(diff - amount) < 0.1:
                                    trans_type = "CREDIT"
                                elif abs(diff + amount) < 0.1:
                                    trans_type = "DEBIT"
                                else:
                                    # Fallback: Maybe balance logic is out of sync? Keep default or heuristic.
                                    pass
                            
                            # Update previous balance if we found one
                            if current_balance is not None:
                                self.previous_balance = current_balance
                            elif amount > 0 and len(parts) == 3 and "B/F" in line:
                                # Start of statement balance line? "01-12-2025 B/F 1,57,733.02"
                                # If this was parsed as amount, treat it as balance initialization
                                self.previous_balance = amount
                                # Don't add B/F as a transaction usually?
                                # Return/Continue?
                                # If description is "B/F", skip adding content but keep balance.
                                if "B/F" in line or "BROUGHT FORWARD" in line.upper():
                                     continue

                            desc_end_index = -k
                            desc_start_index = 1
                            if parse_date(parts[1]): desc_start_index = 2
                            
                            self.debug_logs.append(f"  Tokens: {parts} (len={len(parts)})")
                            self.debug_logs.append(f"  Slice: [{desc_start_index}:{desc_end_index}] -> {parts[desc_start_index:desc_end_index]}")
                            
                            # Store the current line for next iteration if we skip it
                            # But we are inside the loop. We need 'previous_line_content' variable.
                            # Initialize 'previous_line_content' outside the loop.
                            
                            description = " ".join(parts[desc_start_index:desc_end_index])
                            found_amount = True
                            
                            # Explicit B/F Check (Text Mode)
                            if "B/F" in description or "BROUGHT FORWARD" in description.upper() or "B/F" in line:
                                self.debug_logs.append(f"  Skipped Text Line (B/F): {description}")
                                continue

                            if found_amount and amount > 0:
                                # Multi-line Description Handling (Lookback)
                                # If description starts with 'BANK/' or doesn't have UPI, check previous line
                                if self.previous_line_content and (not re.search(r'UPI/', description) and not re.search(r'ACH/', description)):
                                    # Heuristic: If previous line was skipped and looks like text
                                    # Prepend it.
                                    combined = self.previous_line_content + " " + description
                                    # self.debug_logs.append(f"  [Lookback] Combined '{self.previous_line_content}' + '{description}'")
                                    description = combined
                                    # Clear it after using
                                    self.previous_line_content = None
                                
                                # Clean the description before storing
                                description = self._clean_description(description)
                                self.debug_logs.append(f"  [Text] Cleaned: '{description}'")
                                self.debug_logs.append(f"  [ACCEPTED] Date: {date} | Amt: {amount} | Type: {trans_type} | Bal: {current_balance}")
                                page_transactions.append({
                                    "date": date,
                                    "description": description,
                                    "amount": amount,
                                    "type": trans_type,
                                    "source": "Bank"
                                })
                                continue # Move to next line after finding transaction

                            # If we reached here, line is skipped. Store it.
                            self.previous_line_content = " ".join(parts)
                            self.debug_logs.append(f"Skipped Line (Stored for Lookback): {self.previous_line_content}")
                            continue

                        # End of lines loop
                        self.previous_line_content = None # Reset per page

                # Add this page's results
                if page_transactions:
                    transactions.extend(page_transactions)

        self.transactions = transactions
        return transactions

    def _clean_description(self, description):
        """
        Simplifies bank statement descriptions, specifically for UPI and ACH.
        """
        if not description:
            return ""
        
        # self.debug_logs.append(f"    _clean input: '{description}'") 
            
        # Regex 1: Standard UPI format UPI/PAYEE/ID/...
        # Also try lenient spacing: UPI / PAYEE / ...
        match = re.search(r'UPI/\s*([^/]+)\s*/', description)
        if match:
            payee = match.group(1)
            # self.debug_logs.append(f"    _clean matched UPI: {payee}")
            return f"UPI - {payee}"
            
        # Regex 2: ACH format ACH/PAYEE/...
        match = re.search(r'ACH/\s*([^/]+)\s*/', description)
        if match:
            payee = match.group(1)
            return f"ACH - {payee}"
            
        return description
