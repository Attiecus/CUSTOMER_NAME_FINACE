
"""
***********************************************************************
This code was created by Atharva Godkar(Data scientist) 
on the 21st of May 2024
for ADNIC information technology team.
The below code consists of various ML,fuzzy and data sorting techniques
to smoothen the process of data grouping and transformation

DATA MAY DISAPPOINT BUT IT NEVER LIES
ENJOY THE CODE!!
***********************************************************************
"""
import streamlit as st
import pandas as pd
import os
from io import BytesIO
import datetime
import pandas_dedupe

# Set environment variables
st.set_page_config(layout="wide")
os.environ['PANDASAI_API_KEY'] = 'your_secure_api_key_here'

def replace_tokio(names):
    modified_names = []
    for name in names:
        name_upper = name.upper()
        if "TOKIO" in name_upper or "TOKIA" in name_upper:
            name = "Tokio Marines"
        if "SWISS RE" in name_upper:
            name = "Swiss re"
        if "AON" in name_upper:
            name = "AON"
        if "GIG" in name_upper:
            name = "GIG INSURANCE"
        if "ADNIC" in name_upper:
            name = "ADNIC"
        if "MARSH" in name_upper:
            name = "MARSH ACCOUNTS"
        if "ADNOC" in name_upper:
            name = "ADNOC"
        modified_names.append(name)
    return modified_names

def trim_name(name):
    if pd.isna(name):
        return name

    if isinstance(name, str):
        try:
            with open('unwanted_suffixes.txt', 'r') as file:
                suffixes = [line.strip() for line in file.readlines()]

            for suffix in suffixes:
                name = name.replace(suffix, '').replace('CASH CUSTOMER', '').replace('REINSURANCE', 'RE').replace('(RE)INSURANCE', 'RE').replace('BANCA-', '').replace('BANCA', '').replace('-', '').replace('.', '')
        except FileNotFoundError:
            st.error("Unwanted suffixes file not found. Please ensure 'unwanted_suffixes.txt' is in the directory.")
            return name
    return name.strip()

def load_data(file_buffer):
    try:
        with st.spinner("Loading and filtering data..."):
            df = pd.read_csv(file_buffer)
            df = df[~df['CUSTOMER_NAME'].str.contains("CASH CUSTOMERS", na=False, case=False)]
            df['Original_Customer_Name'] = df['CUSTOMER_NAME']  # Retain original customer name
            df['CUSTOMER_NAME'] = df['CUSTOMER_NAME'].apply(trim_name)
            df['CUSTOMER_NAME'] = replace_tokio(df['CUSTOMER_NAME'])

            st.text("Data loaded and filtered successfully.")
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def process_file(df):
    try:
        with st.spinner("Deduplicating data..."):
            deduped_df = pandas_dedupe.dedupe_dataframe(df, ['CUSTOMER_NAME', 'XOFPARTY_ID', 'TAX_REG_NUMBER'], sample_size=0.3)
            deduped_df['confidence_level'] = deduped_df['confidence'].apply(classify_confidence)
        st.success("Data deduplicated successfully.")
        return deduped_df.sort_values(by="cluster id", ascending=True)
    except Exception as e:
        st.error(f"Error during deduplication: {e}")
        return pd.DataFrame()

def classify_confidence(score):
    if score <= 0.4:
        return 'Low'
    elif 0.4 < score < 0.7:
        return 'Medium'
    else:
        return 'High'

def get_most_frequent_xof_party_number(df):
    most_frequent_numbers = df.groupby('cluster id')['XOFPARTY_ID'].agg(lambda x: x.mode().iloc[0] if not x.empty else None).reset_index()
    most_frequent_numbers.rename(columns={'XOFPARTY_ID': 'Most Frequent XOFPARTY_ID'}, inplace=True)
    
    df = df.merge(most_frequent_numbers, on='cluster id', how='left')
    
    return df

def deduped_sam_mapped_df(df):
    try:
        with st.spinner("Deduplicating SAM mapped data..."):
            deduped_df = pandas_dedupe.dedupe_dataframe(df, ['CUSTOMER_NAME', 'Matched SAM Group'], sample_size=0.3)
        st.success("SAM mapped data deduplicated successfully.")
        return deduped_df.sort_values(by="cluster id", ascending=True)
    except Exception as e:
        st.error(f"Error during SAM mapped data deduplication: {e}")
        return pd.DataFrame()

def main():
    st.title("CUSTOMER FILTER & DEDUPE")

    uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
    sam_names_file = st.file_uploader("Upload SAM Names File", type=["xlsx"])

    if uploaded_file is not None:
        df_filtered = load_data(uploaded_file)
        if not df_filtered.empty:
            st.dataframe(df_filtered, width=5000)

            start_time = datetime.datetime.now()

            deduped_df = process_file(df_filtered)
            if not deduped_df.empty:
                end_time = datetime.datetime.now()

                st.dataframe(deduped_df, width=5000)
                
                towrite = BytesIO()
                deduped_df.to_csv(towrite, index=False, header=True)
                towrite.seek(0)
                st.download_button("Download Deduplicated Data", towrite, "deduplicated_data.csv", "text/csv")
                
                st.write(f"Deduplication started at: {start_time}")
                st.write(f"Deduplication ended at: {end_time}")

                with st.spinner("Getting most frequent XOFPARTY_ID..."):
                    deduped_df = get_most_frequent_xof_party_number(deduped_df)

                st.success("Most frequent XOFPARTY_ID determined.")
                st.dataframe(deduped_df, width=5000)

                towrite = BytesIO()
                deduped_df.to_csv(towrite, index=False, header=True)
                towrite.seek(0)
                st.download_button("Download Processed Data", towrite, "processed_data.csv", "text/csv")

                if sam_names_file is not None:
                    try:
                        sam_names_df = pd.read_excel(sam_names_file, usecols=['CUSTOMER_NAME', 'Matched SAM Group'])

                        deduped_sam_mapped_data = deduped_sam_mapped_df(sam_names_df)
                        if not deduped_sam_mapped_data.empty:
                            st.success("Deduplication of SAM group mapped data successful.")
                            st.dataframe(deduped_sam_mapped_data, width=5000)

                            towrite_sam = BytesIO()
                            deduped_sam_mapped_data.to_csv(towrite_sam, index=False, header=True)
                            towrite_sam.seek(0)
                            st.download_button("Download Deduplicated SAM Mapped Data", towrite_sam, "deduplicated_sam_mapped_data.csv", "text/csv")
                    except Exception as e:
                        st.error(f"Error loading SAM names file: {e}")

if __name__ == "__main__":
    main()
