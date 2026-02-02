from utils.date_utils import parse_date
import re

def test_line_parsing():
    lines = [
        "01-12-2025 B/F 1,57,733.02",
        "01-12-2025 BAN/540552103355/AXIe396bcd1aa8b4390bad17650cb1088 530.00 1,57,203.02",
        "04-12-2025 Bank/868138181575/YBL9fc8110aa4a445e6a96af99df5b7a2 10,000.00 1,71,203.02"
    ]
    
    print("Testing Lines:")
    for line in lines:
        print(f"\nLine: {line}")
        parts = line.split()
        if len(parts) < 3:
            print("  Skipped: Too short")
            continue
            
        date = parse_date(parts[0])
        if not date:
            print(f"  Skipped: Date not found in '{parts[0]}'")
            continue
        
        print(f"  Date Found: {date}")
        
        amount_candidates = []
        for k in range(1, 5):
            if len(parts) < k + 2: break
            token = parts[-k]
            clean_token = token.replace(',', '').lower()
            
            is_credit = False
            if 'cr' in clean_token: 
                is_credit = True
                clean_token = clean_token.replace('cr', '')
                
            try:
                val = float(clean_token)
                amount_candidates.append({
                    'val': val,
                    'k': k,
                    'token': token
                })
            except ValueError:
                continue
                
        print(f"  Candidates: {amount_candidates}")
        
        if not amount_candidates:
            print("  Skipped: No amount candidates")
            continue
            
        selected = amount_candidates[0]
        if len(amount_candidates) > 1:
            # We expect [Balance, Amount]. Balance is k=1 (index 0). Amount is k=2 (index 1).
            # So we choose candidates[1]
            selected = amount_candidates[1]
            print("  Selected Candidate 1 (Assuming second from right is Amount)")
        else:
            print("  Selected Candidate 0 (Only one number)")
            
        print(f"  Final Amount: {selected['val']}")
        
        # Description
        desc_start = 1
        desc_end = -selected['k']
        desc = " ".join(parts[desc_start:desc_end])
        print(f"  Description: {desc}")

if __name__ == "__main__":
    test_line_parsing()
