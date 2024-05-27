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
from io import BytesIO
from rapidfuzz import process, fuzz

def trim_name(name):
    if pd.isna(name):
        return name  # Handle NaN values and return as is.
    
    if isinstance(name, str):
        # Remove 'c/o' notation
        if 'c/o' in name.lower():
            name = name.split(' c/o', 1)[0]
        
        # Remove variations of 'LLC'
        name = name.replace('L L C','').replace(' LLC', '').replace(' llc', '').replace(' L.L.C', '').replace(' l.l.c', '')

    return name.strip()  # Strip to clean any leading/trailing whitespace



def load_data(file_buffer, sheet_name=0):
    # Load data and trim C/O from INSURED_RI
    data = pd.read_excel(file_buffer, usecols=['INSURED_RI', 'SAM_GROUP_NAME'], sheet_name=sheet_name)
    data['INSURED_RI'] = data['INSURED_RI'].apply(lambda x: trim_name(x))
    return data


def match_sam_groups(file_buffer, sam_names_df):
    chunk_size = 1000
    chunks = pd.read_csv(file_buffer, chunksize=chunk_size, usecols=['CUSTOMER_NAME', 'XOFPARTY_ID', 'cluster id'])
    processed_chunks = []
    cluster_sam_group_mapping = {}

    # Process each chunk
    for chunk in chunks:
        for cluster_id, group in chunk.groupby('cluster id'):
            # Check if SAM group already matched for this cluster ID
            if cluster_id in cluster_sam_group_mapping:
                sam_group = cluster_sam_group_mapping[cluster_id]
            else:
                # Match the first entry in this cluster
                first_entry = group.iloc[0]
                sam_group = find_matching_sam_group(first_entry, sam_names_df)
                cluster_sam_group_mapping[cluster_id] = sam_group

            # Assign SAM group to all entries in this cluster
            chunk.loc[group.index, 'Matched SAM Group'] = sam_group

        processed_chunks.append(chunk)

    return pd.concat(processed_chunks)


def find_matching_sam_group(entry, sam_names_df):
    insured_value = trim_name(str(entry['CUSTOMER_NAME'])).lower()
    sam_names_dict = {trim_name(str(row['INSURED_RI']).lower()): row['SAM_GROUP_NAME'] for _, row in sam_names_df.iterrows() if pd.notna(row['INSURED_RI'])}
    matches = process.extractOne(insured_value, sam_names_dict.keys(), scorer=fuzz.token_sort_ratio)
    
    if matches is None or matches[1] < 85:
        return 'No SAM Match'

    return sam_names_dict[matches[0]]




def main():
    st.title("SAM Group Mapping")

    deduped_data_file = st.file_uploader("Upload Deduplicated Data", type=["csv"])
    sam_names_file = st.file_uploader("Upload SAM Names File", type=["xlsx"])

    if deduped_data_file and sam_names_file:
        # Load SAM names data
        sam_names_df = load_data(sam_names_file)

        # Display a spinner while matching data
        with st.spinner("Matching data..."):
            processed_df = match_sam_groups(deduped_data_file, sam_names_df)
            

        st.success("Data matching completed.")
        st.dataframe(processed_df)

        # Allow users to download the mapped data
        towrite = BytesIO()
        processed_df.to_csv(towrite, index=False, header=True)
        towrite.seek(0)
        st.download_button("Download Mapped Data", towrite, "mapped_data.csv", "text/csv")

if __name__ == "__main__":
    main()
