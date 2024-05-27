import nltk
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import word_tokenize
import pandas as pd

# Ensure the NLTK tokenization package is downloaded
nltk.download('punkt')

# Load spaCy's English model
nlp = spacy.load('en_core_web_sm')

# Read data from CSV
df = pd.read_csv("CustomerDeduplicationDataDataSet2.csv")

# Extract customer names, ensuring no NaNs
data_entries = df["CUSTOMER_NAME"].dropna().tolist()

# Preprocess data: convert to lowercase
preprocessed_entries = [entry.lower() for entry in data_entries]

# Step 1: Compute TF-IDF scores
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(preprocessed_entries)
feature_names = vectorizer.get_feature_names_out()
tfidf_scores = dict(zip(feature_names, tfidf_matrix.sum(axis=0).tolist()[0]))

# Define a threshold for low TF-IDF score
tfidf_threshold = min(tfidf_scores.values()) + (max(tfidf_scores.values()) - min(tfidf_scores.values())) / 3

# Identify terms with low TF-IDF scores
low_tfidf_terms = {term for term, score in tfidf_scores.items() if score < tfidf_threshold}

# Step 2: Function to extract named entities using spaCy
def extract_named_entities(text):
    doc = nlp(text)
    return {ent.text.lower() for ent in doc.ents}

# Step 3: Function to abbreviate company names
def abbreviate_company_name(name):
    # Tokenize the company name
    tokens = word_tokenize(name.lower())
    
    # Extract named entities
    named_entities = extract_named_entities(name)
    
    # Filter out tokens with low TF-IDF scores unless they are named entities
    filtered_tokens = [token for token in tokens if token not in low_tfidf_terms or token in named_entities]
    
    # Retain unique tokens while preserving the order
    unique_tokens = []
    seen_tokens = set()
    for token in filtered_tokens:
        if token not in seen_tokens:
            unique_tokens.append(token)
            seen_tokens.add(token)
    
    # Handle cases where all tokens are filtered out by ensuring at least named entities are retained
    if not unique_tokens:
        unique_tokens = list(named_entities)
    
    # Construct the abbreviated name
    abbreviated_name = ' '.join(unique_tokens)
    
    return abbreviated_name.title()  # Convert to title case for better readability

# Standardize the names in the data entries
standardized_entries = [abbreviate_company_name(entry) for entry in data_entries]

# Create a new DataFrame with original and standardized names
df_standardized = pd.DataFrame({
    'Original Name': data_entries,
    'Standardized Name': standardized_entries
})

# Output the DataFrame
print(df_standardized)

# Optionally, save the DataFrame to a new CSV file
df_standardized.to_csv("StandardizedCustomerNames.csv", index=False)
