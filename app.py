import streamlit as st
import os
import pandas as pd
from main import scan_and_process, append_to_master
import shutil

st.set_page_config(page_title="Personal Finance Analyzer", page_icon="💰", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw_pdfs')
MASTER_FILE = os.path.join(BASE_DIR, 'data', 'master_transactions.xlsx')

st.title("💰 Offline Personal Finance Analyzer")
st.markdown("Upload your Bank, Credit Card, or Wallet statements to analyze your finances securely and offline.")

# Initialize session state for staging data
if 'staging_data' not in st.session_state:
    st.session_state['staging_data'] = None

# Sidebar for controls
with st.sidebar:
    st.header("Actions")
    password = st.text_input("PDF Password (if protected)", type="password", help="If your PDFs are password protected, enter the password here.")
    source_options = [
        "Auto",
        "Rupay ICICI Credit Card", 
        "Amazon Pay ICICI Credit Card", 
        "Axis Bank Credit Card", 
        "SBI Credit Card", 
        "ICICI Savings Account", 
        "HDFC Savings Account", 
        "Other"
    ]
    selected_source = st.selectbox("Select Source (Optional)", source_options, help="Override the source for all uploaded files.")
    
    custom_source = None
    if selected_source == "Other":
        custom_source = st.text_input("Enter Custom Source Name")
    
    final_source = None
    if selected_source != "Auto":
        final_source = custom_source if selected_source == "Other" else selected_source

    # Step 1: Select Files
    import glob
    # Get PDFs in raw folder
    pdf_files = [f for f in os.listdir(RAW_DIR) if f.endswith('.pdf')]
    
    selected_files = st.multiselect(
        "Select Files to Process", 
        pdf_files, 
        default=pdf_files,
        help="Choose which files to scan."
    )

    # Step 2: Scan and Preview
    if st.button("🔎 Scan & Preview"):
        if not selected_files:
            st.warning("Please select at least one file.")
        else:
            with st.spinner("Scanning files..."):
                try:
                    # Construct full paths
                    target_paths = [os.path.join(RAW_DIR, f) for f in selected_files]
                    
                    # Call scan with specific paths
                    df_new, logs = scan_and_process(file_paths=target_paths, password=password, source=final_source)
                    
                    # Display logs
                    with st.expander("Process Logs", expanded=True):
                        for log in logs:
                            st.markdown(log)
                    
                    if not df_new.empty:
                        st.session_state['staging_data'] = df_new
                        st.success(f"Found {len(df_new)} new transactions!")
                    else:
                        st.warning("No new transactions found.")
                except Exception as e:
                    st.error(f"Error during scanning: {e}")
                
    st.divider()
    
    # Step 3: Commit (Visible only if data exists)
    if st.session_state['staging_data'] is not None and not st.session_state['staging_data'].empty:
        st.info(f"Ready to add {len(st.session_state['staging_data'])} transactions.")
        if st.button("💾 Add to Master Sheet"):
             with st.spinner("Saving to Master Record..."):
                 try:
                     success = append_to_master(st.session_state['staging_data'])
                     if success:
                         st.success("Successfully saved to Master Sheet!")
                         st.session_state['staging_data'] = None # Clear staging
                         st.rerun()
                 except Exception as e:
                     st.error(f"Error saving: {e}")

    st.divider()
    st.info("Workflow: Upload -> Scan & Preview -> Add to Master.")
    
    st.divider()
    st.header("Manage Categories")
    from processors.categorizer import Categorizer
    cat_engine = Categorizer()
    
    # Add new keyword
    st.subheader("Add Keyword")
    target_cat = st.selectbox("Category", cat_engine.get_categories() + ["New Category"])
    
    if target_cat == "New Category":
        target_cat = st.text_input("Enter New Category Name")
    
    new_keyword = st.text_input("New Keyword", help="Enter a keyword to map to this category").strip()
    
    if st.button("➕ Add Keyword"):
        if new_keyword and target_cat:
            success, existing_cat = cat_engine.add_keyword(target_cat, new_keyword)
            if success:
                st.success(f"Added '{new_keyword}' to '{target_cat}'")
            else:
                st.error(f"Keyword '{new_keyword}' already exists in '{existing_cat}'")
        else:
            st.warning("Please enter both category and keyword.")
            
    if st.button("🔄 Re-categorize All Existing Data"):
        if os.path.exists(MASTER_FILE):
            with st.spinner("Re-applying categories to all transactions..."):
                try:
                    df = pd.read_excel(MASTER_FILE)
                    if not df.empty:
                        # Handle potential column name migration for old files
                        if "Description" in df.columns and "Transaction made at" not in df.columns:
                             df.rename(columns={"Description": "Transaction made at"}, inplace=True)
                             
                        if "Transaction made at" in df.columns:
                            df['Category'] = df['Transaction made at'].apply(cat_engine.categorize)
                            df.to_excel(MASTER_FILE, index=False)
                            st.success("Successfully re-categorized all transactions!")
                            st.rerun()
                        else:
                            st.error("Column 'Transaction made at' (or 'Description') not found in Master File.")
                    else:
                        st.warning("No data to re-categorize.")
                except Exception as e:
                    st.error(f"Error re-categorizing: {e}")
        else:
            st.warning("No master data file found.")

    st.divider()
    st.header("Manage Data")

    # Use a checkbox for confirmation state that persists across reruns
    confirm_clear = st.checkbox("I understand this deletes all data permanently")
    
    if st.button("🗑️ Clear All Data", disabled=not confirm_clear):
        from utils.file_utils import clear_data, reset_processed_files
        PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
        RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw_pdfs')
        
        # 1. Reset Processed Files (Move back to Raw)
        count = reset_processed_files(PROCESSED_DIR, RAW_DIR)
        
        # 2. Clear Master File
        clear_data([], [MASTER_FILE])
        
        st.success(f"All data cleared! {count} files moved back to 'Pending' for re-scanning.")
        st.rerun()

# Main area
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Upload Statements")
    uploaded_files = st.file_uploader("Drop PDF files here", type="pdf", accept_multiple_files=True)
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Save uploaded file to raw_pdfs
            if not os.path.exists(RAW_DIR):
                os.makedirs(RAW_DIR)
                
            file_path = os.path.join(RAW_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        if st.button("Save to Processing Folder"):
            st.success(f"Saved {len(uploaded_files)} files to {RAW_DIR}")
            # Clear uploader state workaround (experimental) or just let user trigger process

with col2:
    # Section: Preview (Staging)
    if st.session_state['staging_data'] is not None and not st.session_state['staging_data'].empty:
        st.subheader("📝 New Data Preview (Staging)")
        
        # Staged Files Management
        if '_filepath' in st.session_state['staging_data'].columns:
            staged_files = st.session_state['staging_data']['_filepath'].unique()
            st.caption("Transactions from these files:")
            
            for fpath in staged_files:
                fname = os.path.basename(fpath)
                c1, c2 = st.columns([0.8, 0.2])
                c1.text(f"📄 {fname}")
                if c2.button("❌ Remove", key=f"del_{fname}", help=f"Remove transactions from {fname}"):
                    # Filter out this file's data
                    st.session_state['staging_data'] = st.session_state['staging_data'][
                        st.session_state['staging_data']['_filepath'] != fpath
                    ]
                    st.rerun()

        if st.session_state['staging_data'] is not None and not st.session_state['staging_data'].empty:
            st.caption("Review data below. Click 'Add to Master Sheet' in sidebar to save.")
            st.dataframe(st.session_state['staging_data'], use_container_width=True)
        else:
            st.info("Preview cleared.")
        st.divider()

    st.subheader("📚 Master Records")
    if os.path.exists(MASTER_FILE):
        try:
            df = pd.read_excel(MASTER_FILE)
            st.write(f"Total Transactions: **{len(df)}**")
            
            # Simple metrics
            if not df.empty:
                # Ensure date
                df['Date'] = pd.to_datetime(df['Date'])
                
                # Filters
                selected_category = st.selectbox("Filter by Category", ["All"] + list(df['Category'].unique()))
                if selected_category != "All":
                    filtered_df = df[df['Category'] == selected_category]
                else:
                    filtered_df = df
                    
                st.dataframe(filtered_df.sort_values(by="Date", ascending=False), use_container_width=True)
                
                # Download button
                with open(MASTER_FILE, "rb") as f:
                    st.download_button(
                        label="Download Excel",
                        data=f,
                        file_name="master_transactions.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.info("Master file is empty.")
        except Exception as e:
            st.error(f"Error reading master file: {e}")
    else:
        st.warning("No data found. Upload and process files to get started.")

# Footer
st.divider()
st.caption("🔒 Fully Offline | Python Powered | Secure")
