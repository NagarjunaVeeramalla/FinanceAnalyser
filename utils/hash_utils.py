import hashlib

def generate_transaction_hash(date, amount, description, source):
    """
    Generates a unique hash for a transaction based on key fields.
    """
    # Normalize inputs to string and handle None
    date_str = str(date) if date else ""
    amount_str = str(amount) if amount else ""
    desc_str = str(description).strip().lower() if description else ""
    source_str = str(source).strip().lower() if source else ""

    # Create a unique string
    unique_str = f"{date_str}|{amount_str}|{desc_str}|{source_str}"
    
    # Generate SHA-256 hash
    return hashlib.sha256(unique_str.encode('utf-8')).hexdigest()
