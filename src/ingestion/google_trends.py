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
        print("Warning: Can only fetch 5 keywords at a time. Using first 5.")
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


def filter_rising_keywords(trends_df):
    """
    Filter keywords to only those with rising interest.

    Returns list of keyword names that are trending upward.
    """
    rising = []

    for keyword in trends_df.columns:
        # Skip the 'isPartial' column that pytrends adds
        if keyword == "isPartial":
            continue
        # Get the data for this keyword
        data = trends_df[keyword].dropna()
        # Get last 4 weeks average
        last_4_weeks = data.tail(4).mean()
        # Get last 8 weeks average
        previous_4_weeks = data.tail(8).head(4).mean()
        # If last 4 weeks is greater than previous 4 weeks, add to rising list
        if last_4_weeks > previous_4_weeks:
            rising.append(keyword)

    return rising


