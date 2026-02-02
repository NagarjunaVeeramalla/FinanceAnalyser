import pdfplumber
from extractors.bank_extractor import BankExtractor
from extractors.creditcard_extractor import CreditCardExtractor
from extractors.upi_extractor import UPIExtractor

class Parser:
    def __init__(self, file_path, password=None):
        self.file_path = file_path
        self.password = password
        self.raw_text_debug = ""
        self.extractor = self._select_extractor()

    def _select_extractor(self):
        """
        Heuristic to select the correct extractor based on file content.
        """
        # Allow errors (like invalid password) to bubble up to main.py
        with pdfplumber.open(self.file_path, password=self.password) as pdf:
            if not pdf.pages:
                raise ValueError("PDF has no pages.")
                
            first_page_text = pdf.pages[0].extract_text()
            if not first_page_text:
                first_page_text = ""
            
            # Save for debugging
            self.raw_text_debug = first_page_text[:3000] # First 3000 chars
            
            first_page_text_lower = first_page_text.lower()
            
            if "credit card" in first_page_text_lower or ("statement date" in first_page_text_lower and "payment due" in first_page_text_lower):
                return CreditCardExtractor(self.file_path, password=self.password)
            
            # Check for Bank Statement (stronger indicators)
            # "savings a/c", "current a/c", "account summary", "account balance"
            elif any(k in first_page_text_lower for k in ["savings a/c", "current a/c", "account summary", "account balance", "account statement"]):
                return BankExtractor(self.file_path, password=self.password)

            # UPI apps usually mention the app name
            elif "phonepe" in first_page_text_lower or "google pay" in first_page_text_lower or "paytm" in first_page_text_lower:
                return UPIExtractor(self.file_path, password=self.password)
            
            # Last resort fallback
            else:
                return BankExtractor(self.file_path, password=self.password)

    def parse(self):
        if self.extractor:
            return self.extractor.extract_transactions()
        return []
