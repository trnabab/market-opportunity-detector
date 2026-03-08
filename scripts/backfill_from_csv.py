#!/usr/bin/env python3
"""
Backfill database from historical CSV files.

Reads data/history/scores, trends, and products CSVs and inserts
into the database so the dashboard shows full history.

Usage (from project root):
    python scripts/backfill_from_csv.py

Safe to run multiple times: skips (keyword, date) that already exist.
"""

import sys
import os
import csv
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from storage.history import HISTORY_DIR
from storage.crud import save_category
from storage.database import get_session
from storage.models import Keyword, DailySnapshot, OpportunityScore


IMPORTED_CATEGORY_EBAY_ID = "imported"
IMPORTED_CATEGORY_NAME = "Imported"
IMPORTED_CATEGORY_SEED = "import"


def _parse_bool(s):
    if s in (True, False):
        return bool(s)
    return str(s).strip().lower() in ("true", "1", "yes")


def _float(s, default=None):
    if s is None or s == "":
        return default
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def _int(s, default=None):
    if s is None or s == "":
        return default
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return default


def load_scores(date_str):
    """Load scores CSV for a date. Returns list of dicts."""
    path = os.path.join(HISTORY_DIR, "scores", f"{date_str}.csv")
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append({
                "keyword": row.get("keyword", "").strip(),
                "score": _float(row.get("score"), 0),
                "trend_momentum": _float(row.get("trend_momentum")),
                "trend_acceleration": _parse_bool(row.get("trend_acceleration", False)),
                "competition_density": _float(row.get("competition_density")),
                "price_spread": _float(row.get("price_spread"), 0),
                "avg_price": _float(row.get("avg_price")),
            })
    return rows


def load_trends(date_str):
    """Load trends CSV for a date. Returns dict keyword -> list of 12 week values (numbers or None)."""
    path = os.path.join(HISTORY_DIR, "trends", f"{date_str}.csv")
    if not os.path.isfile(path):
        return {}
    out = {}
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            keyword = row.get("keyword", "").strip()
            vals = []
            for i in range(12):
                v = row.get(f"week_{i+1}")
                vals.append(_int(v) if v not in (None, "") else None)
            out[keyword] = vals
    return out


def load_products(date_str):
    """Load products CSV for a date. Returns dict keyword -> {listing_count, unique_sellers, avg_price, min_price, max_price}."""
    path = os.path.join(HISTORY_DIR, "products", f"{date_str}.csv")
    if not os.path.isfile(path):
        return {}
    out = {}
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            keyword = row.get("keyword", "").strip()
            out[keyword] = {
                "listing_count": _int(row.get("listing_count"), 0),
                "unique_sellers": _int(row.get("unique_sellers"), 0),
                "avg_price": _float(row.get("avg_price")),
                "min_price": _float(row.get("min_price")),
                "max_price": _float(row.get("max_price")),
            }
    return out


def snapshot_exists(session, keyword_id, snapshot_date):
    return (
        session.query(DailySnapshot.id)
        .filter_by(keyword_id=keyword_id, snapshot_date=snapshot_date)
        .first()
        is not None
    )


def score_exists(session, keyword_id, score_date):
    return (
        session.query(OpportunityScore.id)
        .filter_by(keyword_id=keyword_id, score_date=score_date)
        .first()
        is not None
    )


def get_date_strings():
    """List all dates we have in scores (or trends) CSVs."""
    scores_dir = os.path.join(HISTORY_DIR, "scores")
    if not os.path.isdir(scores_dir):
        return []
    dates = []
    for name in os.listdir(scores_dir):
        if name.endswith(".csv"):
            date_str = name[:-4]
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                dates.append(date_str)
            except ValueError:
                pass
    return sorted(dates)


def get_or_create_keyword(session, keyword, category_id):
    """Return keyword_id, using a single session to avoid connection pool exhaustion."""
    now = datetime.now()
    kw = session.query(Keyword).filter_by(keyword=keyword, category_id=category_id).first()
    if kw:
        kw.last_seen = now
        return kw.id
    kw = Keyword(keyword=keyword, category_id=category_id, first_seen=now, last_seen=now)
    session.add(kw)
    session.flush()
    return kw.id


def run_backfill():
    category_id = save_category(
        ebay_id=IMPORTED_CATEGORY_EBAY_ID,
        name=IMPORTED_CATEGORY_NAME,
        seed=IMPORTED_CATEGORY_SEED,
    )
    session = get_session()
    try:
        date_strings = get_date_strings()
        if not date_strings:
            print("No CSV dates found in data/history/scores/")
            return

        print(f"Backfilling {len(date_strings)} dates: {date_strings[0]} .. {date_strings[-1]}")

        for date_str in date_strings:
            snapshot_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            scores = load_scores(date_str)
            trends = load_trends(date_str)
            products = load_products(date_str)

            if not scores:
                continue

            for row in scores:
                keyword = row.get("keyword")
                if not keyword:
                    continue

                keyword_id = get_or_create_keyword(session, keyword, category_id)

                if snapshot_exists(session, keyword_id, snapshot_date):
                    continue

                prod = products.get(keyword, {})
                trend_vals = trends.get(keyword)
                if trend_vals is not None:
                    trend_values = [v for v in trend_vals if v is not None]
                else:
                    trend_values = None

                session.add(DailySnapshot(
                    keyword_id=keyword_id,
                    snapshot_date=snapshot_date,
                    trend_momentum=row.get("trend_momentum"),
                    trend_acceleration=row.get("trend_acceleration", False),
                    competition_density=row.get("competition_density"),
                    avg_price=row.get("avg_price") or prod.get("avg_price"),
                    min_price=prod.get("min_price"),
                    max_price=prod.get("max_price"),
                    price_spread=row.get("price_spread", 0) or 0,
                    listing_count=prod.get("listing_count") or 0,
                    unique_sellers=prod.get("unique_sellers") or 0,
                    trend_values=trend_values,
                ))

                if not score_exists(session, keyword_id, snapshot_date):
                    session.add(OpportunityScore(
                        keyword_id=keyword_id,
                        score_date=snapshot_date,
                        score=row.get("score", 0),
                        weights=None,
                    ))

            session.commit()
            print(f"  {date_str}: {len(scores)} keywords")

        print("Backfill done. Dashboard will show full history.")
    finally:
        session.close()


if __name__ == "__main__":
    run_backfill()
