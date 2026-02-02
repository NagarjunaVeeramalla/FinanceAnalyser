from abc import ABC, abstractmethod
import pdfplumber

class BaseExtractor(ABC):
    def __init__(self, file_path, password=None):
        self.file_path = file_path
        self.password = password
        self.transactions = []
        self.debug_logs = []

    def extract_text(self):
        """
        Helper to extract raw text from all pages.
        """
        text = ""
        with pdfplumber.open(self.file_path, password=self.password) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text

    @abstractmethod
    def extract_transactions(self):
        """
        Abstract method to extract transactions.
        Should return a list of dictionaries with keys:
        - date
        - description
        - amount
        - type (DEBIT/CREDIT)
        - balance (optional)
        """
        pass
