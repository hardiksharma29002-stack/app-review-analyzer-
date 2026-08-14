"""
LLM Theme Classification Module (Phase 3).

Uses Groq API to classify reviews into predefined themes.
Uses ThreadPoolExecutor for concurrent batch processing (blazing fast).
Handles API rate limits, invalid JSON, and hallucinated themes.
"""

import json
import time
import sys
from pathlib import Path
from typing import List, Dict
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from groq import Groq

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
import config

def get_groq_client():
    is_valid, msg = config.validate_groq_config()
    if not is_valid:
        print(f"[ERROR] {msg}")
        sys.exit(1)
    return Groq(api_key=config.GROQ_API_KEY)

def extract_dynamic_themes(df: pd.DataFrame, client: Groq, retry_count=0) -> List[str]:
    """
    Extracts 5 distinct business themes dynamically from a sample of the dataset.
    """
    system_prompt = (
        "You are an expert Data Analyst. I will provide a sample of user reviews. "
        "Identify exactly 5 primary business themes (categories) that best summarize the topics discussed in this specific dataset. "
        "Keep the theme names short (2-4 words) and professional (e.g. 'Checkout Experience', 'App Crashes'). "
        "Return ONLY a valid JSON object with a single key 'themes' containing a list of exactly 5 strings."
    )
    
    # Sample up to 50 random reviews to get a sense of the dataset
    sample_df = df.sample(n=min(50, len(df)), random_state=42)
    user_prompt = "Reviews sample:\n"
    for _, r in sample_df.iterrows():
        user_prompt += f"Rating: {r['rating']} | Text: {r['text'][:150]}\n"

    try:
        completion = client.chat.completions.create(
            model=config.GROQ_MODEL_PRIMARY,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2, # slightly higher temp for initial clustering
            response_format={"type": "json_object"}
        )
        result = json.loads(completion.choices[0].message.content)
        themes = result.get("themes", [])
        if len(themes) != 5:
            raise ValueError(f"Expected 5 themes, got {len(themes)}")
        return themes
        
    except Exception as e:
        if "rate limit" in str(e).lower() or "429" in str(e):
            if retry_count < config.CLASSIFICATION_MAX_RETRIES:
                wait_time = (retry_count + 1) * 2
                print(f"[WARNING] Rate limit hit during extraction. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return extract_dynamic_themes(df, client, retry_count + 1)
        
        print(f"[ERROR] Dynamic theme extraction failed: {e}. Falling back to default generic themes.")
        return ["App Performance & Stability", "Customer Support", "Pricing & Value", "Usability & Design", "Feature Requests"]

def classify_batch(batch: List[Dict], client: Groq, themes_list: List[str], retry_count=0) -> Dict[str, str]:
    """
    Sends a batch of reviews to Groq. Returns {id: theme}.
    Uses JSON mode to enforce structured output.
    """
    system_prompt = (
        "You are a specialized App Review Classifier. "
        "Classify each review into exactly ONE of these themes:\n"
        + "\n".join([f"- {t}" for t in themes_list]) + "\n\n"
        "Return ONLY a valid JSON object where keys are the review IDs and values are the exact theme name."
    )
    
    # Format user prompt
    user_prompt = "Reviews to classify:\n"
    for r in batch:
        user_prompt += f"ID: {r['id']} | Rating: {r['rating']} | Text: {r['text']}\n"

    try:
        completion = client.chat.completions.create(
            model=config.GROQ_MODEL_PRIMARY,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=config.CLASSIFICATION_TEMPERATURE,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON
        result = json.loads(completion.choices[0].message.content)
        return result
        
    except Exception as e:
        # Edge Case #42: Rate Limits & Retries
        if "rate limit" in str(e).lower() or "429" in str(e):
            if retry_count < config.CLASSIFICATION_MAX_RETRIES:
                wait_time = (retry_count + 1) * 2
                print(f"[WARNING] Rate limit hit. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return classify_batch(batch, client, themes_list, retry_count + 1)
        
        print(f"[ERROR] Batch classification failed: {e}")
        return {}

def classify_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classifies all reviews in the DataFrame concurrently.
    """
    if df.empty:
        return df
        
    print(f"Classifying {len(df)} reviews using {config.GROQ_MODEL_PRIMARY}...")
    
    # Assign temporary IDs for LLM tracking
    df = df.copy()
    df['id'] = range(1, len(df) + 1)
    
    # Prepare batches
    records = df.to_dict('records')
    batches = [records[i:i + config.CLASSIFICATION_BATCH_SIZE] 
               for i in range(0, len(records), config.CLASSIFICATION_BATCH_SIZE)]
               
    client = get_groq_client()
    
    print("Dynamically extracting dataset themes...")
    dynamic_themes = extract_dynamic_themes(df, client)
    print(f"Extracted Themes: {dynamic_themes}")
    
    theme_mapping = {}
    
    print(f"Sending {len(batches)} batches concurrently (blazing fast!)...")
    
    # Concurrent execution for massive speedup
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(classify_batch, batch, client, dynamic_themes): i for i, batch in enumerate(batches)}
        
        for future in as_completed(futures):
            batch_result = future.result()
            theme_mapping.update(batch_result)
            
    # Map results back to dataframe
    # Edge case #47: 6th theme invention (validate against allow-list)
    def clean_theme(review_id):
        raw_theme = theme_mapping.get(str(review_id), "Unknown")
        # Direct match
        if raw_theme in dynamic_themes:
            return raw_theme
        # Fuzzy match
        for valid_theme in dynamic_themes:
            if raw_theme.lower() in valid_theme.lower():
                return valid_theme
        # Fallback
        return "Unknown"
        
    df['theme'] = df['id'].apply(clean_theme)
    
    # Drop temp ID
    df = df.drop(columns=['id'])
    
    # Filter out unknowns (Edge Case handling)
    classified_count = len(df[df['theme'] != "Unknown"])
    print(f"[OK] Successfully classified {classified_count}/{len(df)} reviews.")
    
    return df

if __name__ == "__main__":
    from pipeline.clean import clean_reviews
    df = clean_reviews()
    df_classified = classify_reviews(df)
    if not df_classified.empty:
        print("\nTheme Distribution:")
        print(df_classified['theme'].value_counts())
