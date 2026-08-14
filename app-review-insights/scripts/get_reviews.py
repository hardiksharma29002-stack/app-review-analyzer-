"""
Offline Review Scraper for App Review Insights Analyzer.

Fetches recent reviews for the Groww app from the Google Play Store
and saves them to `data/reviews.csv`.

Usage:
    python scripts/get_reviews.py [--weeks N] [--limit N]
"""

import argparse
import sys
import pandas as pd
from datetime import datetime, timedelta
from google_play_scraper import Sort, reviews
from pathlib import Path

# Add project root to path so we can import config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
import config  # type: ignore

def fetch_reviews(app_id: str, max_weeks: int, max_count: int = 1000) -> pd.DataFrame:
    """Fetch reviews from Google Play Store."""
    print(f"Fetching reviews for {app_id}...")
    print(f"Targeting last {max_weeks} weeks (max {max_count} reviews).")
    
    cutoff_date = datetime.now() - timedelta(weeks=max_weeks)
    
    # We fetch in batches. google-play-scraper's `reviews` function
    # returns a tuple: (result, continuation_token)
    result, continuation_token = reviews(
        app_id,
        lang='en', 
        country='in', 
        sort=Sort.NEWEST, 
        count=max_count 
    )
    
    if not result:
        print("No reviews found.")
        return pd.DataFrame()
        
    df = pd.DataFrame(result)
    
    # Edge case #12: Date format inconsistencies (comes as datetime object)
    df['date'] = pd.to_datetime(df['at'])
    
    # Filter by date
    df = df[df['date'] >= cutoff_date]
    
    # Keep only required columns
    # 'score' -> 'rating', 'content' -> 'text'
    df = df.rename(columns={'score': 'rating', 'content': 'text'})
    
    # Edge case #18: Ensure we have required columns
    columns_to_keep = ['rating', 'title', 'text', 'date']
    
    # Not all reviews have titles, add if missing
    if 'title' not in df.columns:
        df['title'] = ""
        
    df = df[columns_to_keep]
    
    # Format date as YYYY-MM-DD string
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    
    # Edge Case #21: Ensure rating is in bounds
    df = df[(df['rating'] >= 1) & (df['rating'] <= 5)]
    
    # Edge case #24: Cap large datasets
    if len(df) > config.MAX_REVIEWS_CAP:
        print(f"Warning: Fetched {len(df)} reviews. Capping at {config.MAX_REVIEWS_CAP}.")
        df = df.head(config.MAX_REVIEWS_CAP)
        
    return df

def main():
    parser = argparse.ArgumentParser(description="Scrape Google Play reviews.")
    parser.add_argument("--weeks", type=int, default=config.DEFAULT_SCRAPE_WEEKS, 
                        help="Number of weeks to look back")
    parser.add_argument("--limit", type=int, default=1000, 
                        help="Maximum number of reviews to fetch initially")
    args = parser.parse_args()
    
    df = fetch_reviews(config.GROWW_APP_ID, max_weeks=args.weeks, max_count=args.limit)
    
    if df.empty:
        print("Error: DataFrame is empty. No reviews saved.")
        sys.exit(1)
        
    # Ensure data directory exists
    config.DATA_DIR.mkdir(exist_ok=True, parents=True)
    
    output_file = config.DATA_DIR / "reviews.csv"
    
    # Edge Case #15: CSV write permission denied (if file is open in Excel)
    try:
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"[OK] Successfully saved {len(df)} reviews to {output_file}")
    except PermissionError:
        print(f"[ERROR] Cannot write to {output_file}. Please close the file if it's open in another program.")
        sys.exit(1)

if __name__ == "__main__":
    main()
