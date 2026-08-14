"""
Theme Grouping and Quote Selection Module (Phase 4).

Extracts the top 3 themes from classified data.
Selects 1 representative quote per theme (preferring concise, lower-rating reviews).
Applies a second pass of PII redaction (belt-and-suspenders).
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
import config
from pipeline.clean import redact_pii

def select_top_quotes(df: pd.DataFrame) -> dict:
    """
    Groups reviews by theme, identifies top themes, and selects quotes.
    Returns:
        {
            "theme_counts": {"Theme Name": count, ...},
            "quotes": [
                {"theme": "...", "quote": "...", "rating": 3}, ...
            ]
        }
    """
    print("Selecting representative quotes from top themes...")
    
    if df.empty:
        return {"theme_counts": {}, "quotes": []}
        
    # Get top 3 themes (ignoring "Unknown")
    valid_df = df[df['theme'] != "Unknown"]
    theme_counts = valid_df['theme'].value_counts()
    
    top_themes = theme_counts.head(config.REPORT_TOP_THEMES).index.tolist()
    
    # Edge case #55: Fewer than 3 themes found
    if len(top_themes) < config.REPORT_TOP_THEMES:
        print(f"[WARNING] Only found {len(top_themes)} valid themes. Expected {config.REPORT_TOP_THEMES}.")
        
    selected_quotes = []
    
    for theme in top_themes:
        theme_df = valid_df[valid_df['theme'] == theme]
        
        # Strategy: Prefer ratings 1-3 (they show pain points), and length between 30 and 150 characters
        # If none match, just take the first available.
        candidates = theme_df[(theme_df['rating'] <= 3) & 
                              (theme_df['text'].str.len() > 30) & 
                              (theme_df['text'].str.len() < 200)]
                              
        if not candidates.empty:
            chosen_row = candidates.iloc[0]
        else:
            chosen_row = theme_df.iloc[0]
            
        quote_text = chosen_row['text']
        
        # Second Pass PII Redaction (Safety Net)
        quote_text = redact_pii(quote_text)
        
        # Truncate if too long (max 50 words)
        words = quote_text.split()
        if len(words) > config.QUOTE_MAX_WORDS:
            quote_text = " ".join(words[:config.QUOTE_MAX_WORDS]) + "..."
            
        selected_quotes.append({
            "theme": theme,
            "quote": quote_text,
            "rating": int(chosen_row['rating'])
        })
        
    print(f"[OK] Selected {len(selected_quotes)} quotes.")
    return {
        "theme_counts": theme_counts.to_dict(),
        "quotes": selected_quotes
    }

if __name__ == "__main__":
    # Test script locally
    import os
    from pipeline.clean import clean_reviews
    from pipeline.classify import classify_reviews
    
    # Quick end-to-end test
    df_clean = clean_reviews()
    df_class = classify_reviews(df_clean)
    res = select_top_quotes(df_class)
    print("\n--- Quotes ---")
    for q in res['quotes']:
        print(f"[{q['theme']}] {q['rating']}⭐: {q['quote']}")
