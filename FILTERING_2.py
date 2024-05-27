import streamlit as st
import pandas as pd
import os
import re
import numpy as np

# Set environment variables
st.set_page_config(layout="wide")
os.environ['PANDASAI_API_KEY'] = 'your_secure_api_key_here'

# Function to replace 'Tokio' with 'Tokio Marines' in sentences
def replace_tokio(sentences):
    modified_sentences = []
    for sentence in sentences:
        if "TOKIO" in sentence.upper() or "TOKIA" in sentence.upper():
            modified_sentences.append("Tokio Marines")
        else:
            modified_sentences.append(sentence)
      
    return modified_sentences

# Function to trim name
def trim_name(name):
    if pd.isna(name):
        return name

    if isinstance(name, str):
        # Load unwanted suffixes from a file
        with open('unwanted_suffixes.txt', 'r') as file:
            suffixes = [line.strip() for line in file.readlines()]

        # Replace all unwanted suffixes in the name
        for suffix in suffixes:
            name = name.replace(suffix, '').replace('(oman)','').replace('REINSURANCE','RE').replace('(RE)INSURANCE','RE').replace('BANCA-','').replace('BANCA','').replace('-','').replace('.','')

    return name.strip()  # Clean any leading/trailing whitespace


# Function to load data with caching
def load_data(file_path):
    with st.spinner("Loading and filtering data..."):
        # Load data from Excel with specified columns
        df = pd.read_excel(file_path)

        # Debugging: Check data types
       

        # Trimming names
        df['CUSTOMER_NAME'] = df['CUSTOMER_NAME'].apply(trim_name)
        df = df.applymap(lambda x: trim_name(x) if isinstance(x, str) else x)

        # Replace sentences containing 'Tokio' with 'Tokio Marines'
        df['CUSTOMER_NAME'] = replace_tokio(df['CUSTOMER_NAME'])

        st.text("Data loaded and filtered successfully.")
        return df

# Function to download file
def download_file(default_filename):
    # Generate filename with .xlsx extension
    base, ext = os.path.splitext(default_filename)
    if ext.lower() != '.xlsx':
        default_filename = base + '.xlsx'
    
    i = 1
    new_filename = default_filename
    while os.path.exists(new_filename):
        new_filename = f"{base}_{i}.xlsx"
        i += 1
    
    return new_filename

# Main function
def main():
    st.title("Data Filtering and Trimming 1")
    file_path = st.file_uploader("Upload Excel file", type=['xlsx'])
    if file_path is not None:
        df = load_data(file_path)
        st.dataframe(df)

        # Add a button to download the filtered and trimmed data as Excel
        if st.button("Download Filtered Data as Excel"):
            excel_file_path = download_file("filtered_data.xlsx")
            df.to_excel(excel_file_path, index=False)
            st.success(f"Filtered data downloaded successfully as '{os.path.basename(excel_file_path)}'.")

# Entry point
if __name__ == "__main__":
    main()
