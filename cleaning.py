import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer, util

def analyze_duplicates(df, threshold=0.75):
    if df.empty:
        return df

    model = SentenceTransformer('all-MiniLM-L6-v2')
    df["combined_text"] = df["title"].fillna("") + " " + df["description"].fillna("")
    
    embeddings = model.encode(
        df["combined_text"].tolist(), 
        convert_to_tensor=True, 
        show_progress_bar=False
    )
    
    cosine_scores = util.cos_sim(embeddings, embeddings)
    is_duplicate = np.zeros(len(df), dtype=bool)
    parent_titles = [None] * len(df)
    
    for i in range(len(df)):
        if is_duplicate[i]: 
            continue 
        for j in range(i + 1, len(df)):
            if not is_duplicate[j]:
                score = float(cosine_scores[i][j])
                if score > threshold:
                    is_duplicate[j] = True
                    parent_titles[j] = df.loc[i, "title"]
                    
    df["is_duplicate"] = is_duplicate
    df["duplicate_of_title"] = parent_titles
    df.drop(columns=["combined_text"], inplace=True, errors="ignore")
    return df