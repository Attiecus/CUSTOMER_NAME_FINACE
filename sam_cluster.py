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
from fuzzywuzzy import process, fuzz
import openpyxl
from io import BytesIO

def assign_party_numbers(df):
    df_copy = df.copy()

    no_sam_match_df = df_copy[df_copy['Matched SAM Group']== 'No SAM Match']
    df_filtered = df_copy[df_copy['Matched SAM Group'].str.lower() != 'no sam match']

    unique_sam_map_groups = df_filtered['Matched SAM Group'].unique()
    
    party_numbers = {}
    
    for sam_group in unique_sam_map_groups:
        if sam_group not in party_numbers:
            similar_groups = process.extract(sam_group, unique_sam_map_groups, scorer=fuzz.token_sort_ratio)
            
            for group, _ in similar_groups:
                if group not in party_numbers:
                    party_numbers[group] = len(party_numbers) + 1

    df_filtered['NEW ID'] = df_filtered['Matched SAM Group'].map(party_numbers)

    most_frequent_values_no_sam = no_sam_match_df.groupby('cluster id').agg({
        'XOFPARTY_ID': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
        'CUSTOMER_NAME': lambda x: x.mode().iloc[0] if not x.mode().empty else None
    }).reset_index()
    most_frequent_values_no_sam.rename(columns={'XOFPARTY_ID': 'Most_Frequent_XOFPARTY_ID', 'CUSTOMER_NAME': 'Most_Frequent_CUSTOMER_NAME'}, inplace=True)

    no_sam_match_df = no_sam_match_df.merge(most_frequent_values_no_sam, on='cluster id', how='left')

    no_sam_match_df['CUSTOMER_NAME'] = no_sam_match_df['Most_Frequent_CUSTOMER_NAME']
    no_sam_match_df['XOFPARTY_ID'] = no_sam_match_df['Most_Frequent_XOFPARTY_ID']

    most_frequent_values_filtered = df_filtered.groupby('NEW ID').agg({
        'XOFPARTY_ID': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
        'CUSTOMER_NAME': lambda x: x.mode().iloc[0] if not x.mode().empty else None
    }).reset_index()
    most_frequent_values_filtered.rename(columns={'XOFPARTY_ID': 'Most_Frequent_XOFPARTY_ID', 'CUSTOMER_NAME': 'Most_Frequent_CUSTOMER_NAME'}, inplace=True)

    df_filtered = df_filtered.merge(most_frequent_values_filtered, on='NEW ID', how='left')

    df_combined = pd.concat([df_filtered.reset_index(drop=True), no_sam_match_df.reset_index(drop=True)], ignore_index=True)

    df_combined.sort_values(by='NEW ID', ascending=True)

    return df_combined

def main():
    st.title("Excel File Processor")
    
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
    
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        
        df_processed = assign_party_numbers(df)
        
        st.write("Processed DataFrame:")
        st.write(df_processed)
        
        towrite = BytesIO()
        df_processed.to_csv(towrite, index=False, header=True)
        towrite.seek(0)
        st.download_button("Download Mapped Data", towrite, "mapped_data.csv", "text/csv")

if __name__ == "__main__":
    main()
