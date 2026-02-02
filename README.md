# Offline Personal Finance Analyzer

A fully offline tool to analyze personal finance data from PDF statements (Bank, Credit Card, UPI).

## Features
- **PDF Extraction**: Automatically extracts transactions from various PDF formats.
- **Normalization**: Standardizes data into `Date | Description | Amount | Type | Category | Source`.
- **Deduplication**: Prevents duplicate entries using transaction hashing.
- **Categorization**: Automatically categorizes expenses (Food, Travel, etc.).
- **Local Storage**: Stores data in an Excel file (`data/master_transactions.xlsx`).
- **Privacy**, **Offline-First**: No data leaves your machine.
- **UI**: Streamlit-based interface for easy file upload and management.

## Setup

1.  **Prerequisites**: Python 3.10+ installed.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `tabula-py` requires Java to be installed on your system.*

## Usage

### Using the UI (Recommended)
1.  Run the Streamlit app:
    ```bash
    streamlit run app.py
    ```
2.  Upload your PDF statements via the web interface.
3.  Click "Process Files" to extract and save transactions.
4.  Download the updated master Excel file if needed.

### Using the Command Line
1.  Place your PDF statements in `data/raw_pdfs/`.
2.  Run the main script:
    ```bash
    python main.py
    ```
3.  Processed files will be moved to `data/processed/`.
4.  Check `data/master_transactions.xlsx` for the results.

## Project Structure
- `data/`: Stores raw PDFs, processed PDFs, and the master Excel file.
- `extractors/`: logic for parsing specific statement formats.
- `processors/`: Logic for parsing, deduplicating, and categorizing data.
- `utils/`: Helper functions.
- `app.py`: Streamlit UI entry point.
- `main.py`: CLI entry point.
