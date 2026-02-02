import pandas as pd
import os
from utils.hash_utils import generate_transaction_hash

class Deduplicator:
    def __init__(self, master_file_path):
        self.master_file_path = master_file_path
        self.existing_hashes = set()
        self.load_existing_hashes()

    def load_existing_hashes(self):
        """
        Loads hashes from the master excel file to memory.
        """
        if os.path.exists(self.master_file_path):
            try:
                df = pd.read_excel(self.master_file_path)
                if 'Hash' in df.columns:
                    self.existing_hashes = set(df['Hash'].astype(str).tolist())
            except Exception as e:
                print(f"Error loading existing hashes: {e}")

    def is_duplicate(self, transaction):
        """
        Checks if a transaction is a duplicate.
        """
        trans_hash = generate_transaction_hash(
            transaction['date'], 
            transaction['amount'], 
            transaction['description'], 
            transaction['source']
        )
        return trans_hash in self.existing_hashes

    def get_transaction_hash(self, transaction):
        return generate_transaction_hash(
            transaction['date'], 
            transaction['amount'], 
            transaction['description'], 
            transaction['source']
        )
