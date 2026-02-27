"""
Historical data storage for trend forecasting.

Saves weekly snapshots of trends, scores, and product data to CSV files.
"""

import os
from datetime import datetime
import csv

# Base directory for historical data
HISTORY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "history")


def get_date_str():
    """Get current date as string for filenames."""
    return datetime.now().strftime("%Y-%m-%d")


def save_trends(opportunities, date_str=None):
    """
    Save trend data for all keywords.
    
    Each row: date, keyword, week_1, week_2, ..., week_12
    """
    if date_str is None:
        date_str = get_date_str()
    
    filepath = os.path.join(HISTORY_DIR, "trends", f"{date_str}.csv")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        
        # Header
        header = ["date", "keyword"] + [f"week_{i+1}" for i in range(12)]
        writer.writerow(header)
        
        # Data
        for keyword, data in opportunities.items():
            trends = data.get("trends", [])
            # Pad to 12 weeks if shorter
            trends = trends + [None] * (12 - len(trends))
            row = [date_str, keyword] + trends[:12]
            writer.writerow(row)
    
    print(f"Saved trends to {filepath}")
    return filepath


def save_scores(features, scores, date_str=None):
    """
    Save feature and score data for all keywords.
    
    Each row: date, keyword, score, trend_momentum, trend_acceleration, 
              competition_density, price_spread, avg_price
    """
    if date_str is None:
        date_str = get_date_str()
    
    filepath = os.path.join(HISTORY_DIR, "scores", f"{date_str}.csv")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        
        # Header
        header = [
            "date", "keyword", "score", "trend_momentum", "trend_acceleration",
            "competition_density", "price_spread", "avg_price"
        ]
        writer.writerow(header)
        
        # Data
        for keyword, feat in features.items():
            score = scores.get(keyword, 0)
            row = [
                date_str,
                keyword,
                score,
                feat.get("trend_momentum", 0),
                feat.get("trend_acceleration", False),
                feat.get("competition_density", 0),
                feat.get("price_stats", {}).get("price_spread", 0),
                feat.get("price_stats", {}).get("avg_price", 0),
            ]
            writer.writerow(row)
    
    print(f"Saved scores to {filepath}")
    return filepath


def save_products(opportunities, date_str=None):
    """
    Save product summary data for all keywords.
    
    Each row: date, keyword, listing_count, unique_sellers, avg_price, min_price, max_price
    """
    if date_str is None:
        date_str = get_date_str()
    
    filepath = os.path.join(HISTORY_DIR, "products", f"{date_str}.csv")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        
        # Header
        header = ["date", "keyword", "listing_count", "unique_sellers", 
                  "avg_price", "min_price", "max_price"]
        writer.writerow(header)
        
        # Data
        for keyword, data in opportunities.items():
            products = data.get("products", [])
            
            prices = [float(p["price"]) for p in products if p.get("price")]
            sellers = set(p["seller"] for p in products if p.get("seller"))
            
            row = [
                date_str,
                keyword,
                len(products),
                len(sellers),
                round(sum(prices) / len(prices), 2) if prices else 0,
                round(min(prices), 2) if prices else 0,
                round(max(prices), 2) if prices else 0,
            ]
            writer.writerow(row)
    
    print(f"Saved products to {filepath}")
    return filepath


def save_all(opportunities, features, scores):
    """Save all historical data for current date."""
    date_str = get_date_str()
    save_trends(opportunities, date_str)
    save_scores(features, scores, date_str)
    save_products(opportunities, date_str)
    print(f"\nAll data saved for {date_str}")
