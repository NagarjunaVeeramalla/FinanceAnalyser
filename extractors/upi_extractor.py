from .base_extractor import BaseExtractor
from utils.date_utils import parse_date
import pdfplumber
import re

class UPIExtractor(BaseExtractor):
    def extract_transactions(self):
        transactions = []
        # UPI statements (like PhonePe/GPay) often have cleaner layouts but can be text-heavy
        with pdfplumber.open(self.file_path, password=self.password) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                # Pattern: Date ... Paid to/Received from ... Amount
                
                # Very simple regex for example
                # Date format: Feb 20, 2024
                # Amount: ₹100.00
                
                lines = text.split('\n')
                for line in lines:
                    # Simple heuristic: Look for lines starting with a date
                    # And containing an amount
                    
                    # Regex for date at start
                    # This is brittle and would need refining for real PDFs
                    date_match = re.search(r'^(\w{3}\s\d{1,2},?\s\d{4})', line)
                    if not date_match:
                         # Try DD/MM/YYYY
                        date_match = re.search(r'^(\d{2}/\d{2}/\d{4})', line)

                    if date_match:
                        date_str = date_match.group(1)
                        date = parse_date(date_str)
                        
                        # Look for Amount
                        # Matches ₹ 123 or Rs. 123 or just 123.00 at end
                        amount_match = re.search(r'(?:Rs\.?|₹)?\s?([\d,]+\.\d{2})', line)
                        
                        if amount_match and date:
                            amount = float(amount_match.group(1).replace(',', ''))
                            
                            # Description is everything else
                            # Decide type
                            trans_type = "DEBIT"
                            if "Received from" in line or "Credit" in line:
                                trans_type = "CREDIT"
                            
                            description = line.replace(date_str, "").replace(amount_match.group(0), "").strip()
                            
                            transactions.append({
                                "date": date,
                                "description": description,
                                "amount": amount,
                                "type": trans_type,
                                "source": "UPI Wallet"
                            })

        self.transactions = transactions
        return transactions
