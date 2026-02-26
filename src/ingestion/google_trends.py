"""
Google Trends scraper - fetches search interest data.

Uses pytrends library (unofficial Google Trends API).
"""

import time
import pandas as pd
from pytrends.request import TrendReq

# Settings
GEO = "AU"  # Country code (AU = Australia, US = United States, etc.)
TIMEFRAME = "today 12-m"  # Last 12 months


def fetch_trends(keywords, geo=GEO, timeframe=TIMEFRAME):
    """
    Fetch Google Trends data for a list of keywords.
    
    Returns a DataFrame with weekly search interest (0-100 scale).
    
    Note: Google Trends only allows 5 keywords at a time.
    """
    # pytrends limit
    if len(keywords) > 5:
        print(f"Warning: Can only fetch 5 keywords at a time. Using first 5.")
        keywords = keywords[:5]
    
    print(f"Fetching trends for: {keywords}")
    print(f"Region: {geo}, Timeframe: {timeframe}")
    
    try:
        pytrends = TrendReq(hl="en-US", timeout=(10, 25))
        pytrends.build_payload(keywords, timeframe=timeframe, geo=geo)
        
        df = pytrends.interest_over_time()
        
        if df.empty:
            print("No data returned from Google Trends")
            return pd.DataFrame()
        
        print(f"Got {len(df)} weeks of data")
        return df
        
    except Exception as e:
        # Check if rate limited
        if "429" in str(e):
            print("Rate limited by Google. Wait a minute and try again.")
        else:
            print(f"Error: {e}")
        return pd.DataFrame()


def fetch_trends_with_retry(keywords, max_retries=3):
    """
    Same as fetch_trends but retries on failure.
    
    Useful because Google Trends sometimes rate-limits requests.
    """
    for attempt in range(max_retries):
        df = fetch_trends(keywords)
        
        if not df.empty:
            return df
        
        if attempt < max_retries - 1:
            wait_time = 30 * (attempt + 1)  # 30s, 60s, 90s
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    print("All retries failed")
    return pd.DataFrame()


def get_rising_queries(keyword, geo=GEO):
    """
    Find related queries that are rising in popularity.
    
    This is useful for discovering new keywords to track.
    Returns a DataFrame of rising queries, or empty if none found.
    """
    print(f"Finding rising queries for: {keyword}")
    
    try:
        pytrends = TrendReq(hl="en-US", timeout=(10, 25))
        pytrends.build_payload([keyword], timeframe=TIMEFRAME, geo=geo)
        
        related = pytrends.related_queries()
        
        if keyword in related and related[keyword]["rising"] is not None:
            return related[keyword]["rising"]
        else:
            print("No rising queries found")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()


def save_to_csv(df, filename="google_trends.csv"):
    """Save trends data to a CSV file."""
    df.to_csv(filename)
    print(f"Saved to {filename}")


# Quick test
if __name__ == "__main__":
    test_keywords = ["dumbbells", "yoga mat", "resistance bands"]
    
    print("=" * 50)
    print("Google Trends Test")
    print("=" * 50)
    
    df = fetch_trends(test_keywords)
    
    if not df.empty:
        print("\nLast 5 weeks:")
        print(df.tail())
        
        print("\nAverage interest:")
        for kw in test_keywords:
            if kw in df.columns:
                print(f"  {kw}: {df[kw].mean():.1f}")
