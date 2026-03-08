#!/usr/bin/env python3
"""
Weekly data collection script.

Run this weekly (via cron or manually) to collect historical data
for future ML training.

Usage:
    python scripts/collect_weekly.py

Cron example (every Sunday at 9am):
    0 9 * * 0 cd /path/to/project && python scripts/collect_weekly.py
"""

import sys
import os
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ingestion"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "processing"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "scoring"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "storage"))

from discovery import discover_opportunities, CATEGORIES
from features import calculate_features
from opportunity import rank_opportunities, WEIGHTS
from history import save_all
from crud import (
    save_category,
    save_keyword,
    save_daily_snapshot,
    save_opportunity_score,
)


def get_or_create_category(category_name, category):
    """Save category to database and return its id."""
    category_id = save_category(
        ebay_id=category["id"],
        name=category_name,
        seed=category["seed"],
        stop_words=category.get("stop_words"),
        anchors=category.get("anchors"),
        blacklist=category.get("blacklist"),
    )
    return category_id


def collect_and_save_category(category_name, category):
    """
    Collect data for a single category and save to database.
    Returns opportunities, features, scores for CSV backup.
    """
    print(f"\n{'=' * 50}")
    print(f"Processing: {category_name}")
    print("=" * 50)

    # Step 0: Save category to database
    category_id = get_or_create_category(category_name, category)
    print(f"Category saved with id: {category_id}")

    # Step 1: Run discovery
    opportunities = discover_opportunities(category)

    if not opportunities:
        print(f"No rising keywords found for {category_name}")
        return {}, {}, {}

    # Step 2: Save keywords to database, track their IDs
    keyword_ids = {}
    for keyword in opportunities.keys():
        keyword_id = save_keyword(keyword, category_id)
        keyword_ids[keyword] = keyword_id
    print(f"Saved {len(keyword_ids)} keywords")

    # Step 3: Calculate features
    features = calculate_features(opportunities)

    # Step 4: Save daily snapshots
    today = date.today()
    for keyword, feat in features.items():
        keyword_id = keyword_ids[keyword]
        products = opportunities[keyword]["products"]
        trends = opportunities[keyword]["trends"]

        # Count unique sellers
        unique_sellers = len(set(p["seller"] for p in products if p.get("seller")))

        save_daily_snapshot(
            keyword_id=keyword_id,
            snapshot_date=today,
            trend_momentum=feat["trend_momentum"],
            trend_acceleration=feat["trend_acceleration"],
            competition_density=feat["competition_density"],
            avg_price=feat["price_stats"]["avg_price"],
            min_price=feat["price_stats"]["min_price"],
            max_price=feat["price_stats"]["max_price"],
            price_spread=feat["price_stats"]["price_spread"],
            listing_count=len(products),
            unique_sellers=unique_sellers,
            trend_values=trends,
        )
    print(f"Saved {len(features)} daily snapshots")

    # Step 5: Calculate and save scores
    ranked = rank_opportunities(features)
    scores = dict(ranked)

    for keyword, score in scores.items():
        keyword_id = keyword_ids[keyword]
        save_opportunity_score(
            keyword_id=keyword_id,
            score_date=today,
            score=score,
            weights=WEIGHTS,
        )
    print(f"Saved {len(scores)} opportunity scores")

    # Print results
    print(f"\nFound {len(opportunities)} rising keywords:")
    for kw, score in ranked:
        print(f"  {score:5.1f}  {kw}")

    return opportunities, features, scores


def main():
    print("=" * 50)
    print("WEEKLY DATA COLLECTION")
    print("=" * 50)

    all_opportunities = {}
    all_features = {}
    all_scores = {}

    # Process each category
    for category_name, category in CATEGORIES.items():
        opportunities, features, scores = collect_and_save_category(
            category_name, category
        )
        all_opportunities.update(opportunities)
        all_features.update(features)
        all_scores.update(scores)

    if not all_opportunities:
        print("\nNo data to save.")
        return

    # Save to CSV history (backup)
    print("\n" + "=" * 50)
    print("SAVING CSV BACKUP")
    print("=" * 50)
    save_all(all_opportunities, all_features, all_scores)

    print("\nDone!")


if __name__ == "__main__":
    main()
