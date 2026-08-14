"""
Data Cleaning and PII Scrubbing Module (Phase 3).

Reads raw reviews, handles edge cases (empty DF, bad columns),
deduplicates, redacts PII using regex patterns, and samples data.
"""

import pandas as pd
import re
import sys
from pathlib import Path
import html
from typing import Union

# Add project root to path so we can import config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
import config

def redact_pii(text: str) -> str:
    """Apply all PII regex patterns to a given text."""
    if not isinstance(text, str):
        return str(text)
    
    redacted = text
    for pii_type, rules in config.PII_PATTERNS.items():
        # Edge Case #28-32: PII regex replacement
        redacted = re.sub(rules["pattern"], rules["replacement"], redacted)
    return redacted

def clean_reviews(data: Union[Path, pd.DataFrame] = config.DATA_DIR / "reviews.csv") -> pd.DataFrame:
    """
    Load, clean, scrub, and sample reviews.
    Returns a cleaned DataFrame.
    """
    if hasattr(data, "columns"):
        df = data.copy()
    else:
        csv_path = data
        print(f"Cleaning data from {csv_path}...")
        
        # Edge case #17: Empty/missing DataFrame
        if not csv_path.exists():
            print(f"[ERROR] CSV not found at {csv_path}")
            return pd.DataFrame()
            
        try:
            # Edge case #23: CSV encoding fallback
            try:
                df = pd.read_csv(csv_path, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(csv_path, encoding='latin-1')
        except Exception as e:
            print(f"[ERROR] Failed to read CSV: {e}")
            return pd.DataFrame()

    if len(df) == 0:
        print("[WARNING] CSV is empty.")
        return pd.DataFrame()
        
    # Edge case #18: Missing required columns
    missing_cols = config.REQUIRED_CSV_COLUMNS - set(df.columns)
    if missing_cols:
        print(f"[ERROR] Missing required columns: {missing_cols}")
        return pd.DataFrame()

    # Drop pure duplicates (Edge case #22 partially handled)
    initial_len = len(df)
    df = df.drop_duplicates(subset=['text'])
    if initial_len != len(df):
        print(f"Dropped {initial_len - len(df)} duplicate reviews.")

    # Edge case #20 & #21: Ensure rating is numeric and bounded
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    df = df.dropna(subset=['rating', 'text'])
    df = df[(df['rating'] >= 1) & (df['rating'] <= 5)]
    
    # Edge case #11: Special characters / HTML entities in text
    df['text'] = df['text'].apply(lambda x: html.unescape(str(x)).replace('\n', ' ').strip())
    
    # Apply PII scrubbing
    print("Scrubbing PII (emails, phone numbers, Aadhaar, PAN, URLs)...")
    df['text'] = df['text'].apply(redact_pii)
    
    # Sort by date (newest first)
    df = df.sort_values(by='date', ascending=False)
    
    # Fast Processing Cap (User Request)
    if len(df) > config.MAX_REVIEWS_TO_ANALYZE:
        print(f"Sampling down to top {config.MAX_REVIEWS_TO_ANALYZE} recent reviews for blazing fast LLM speed.")
        df = df.head(config.MAX_REVIEWS_TO_ANALYZE)
        
    print(f"[OK] Cleaned and retained {len(df)} reviews for analysis.")
    return df

if __name__ == "__main__":
    df_cleaned = clean_reviews()
    if not df_cleaned.empty:
        print(df_cleaned[['rating', 'text', 'date']].head())
