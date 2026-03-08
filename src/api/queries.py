"""
Database queries for the API.

Read-only functions to fetch opportunities, keywords, and history.
"""

from storage.database import get_session
from storage.models import Category, OpportunityScore, Keyword, DailySnapshot


def get_categories():
    """Get all tracked categories."""
    session = get_session()
    results = session.query(Category).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "ebay_id": r.ebay_id,
            "seed": r.seed,
        }
        for r in results
    ]


def get_opportunities(limit=20):
    """
    Get top opportunities from the most recent score date.
    One row per keyword (highest score wins if keyword appears in multiple categories).
    Returns list of dicts: [{keyword, score, score_date}, ...]
    """
    session = get_session()

    # Fetch extra rows so we can dedupe by keyword and still return `limit` unique keywords
    results = (
        session.query(
            Keyword.keyword, OpportunityScore.score, OpportunityScore.score_date
        )
        .join(OpportunityScore, Keyword.id == OpportunityScore.keyword_id)
        .order_by(OpportunityScore.score.desc())
        .limit(limit * 10)
        .all()
    )

    seen = set()
    out = []
    for result in results:
        if result.keyword in seen:
            continue
        seen.add(result.keyword)
        out.append({
            "keyword": result.keyword,
            "score": result.score,
            "score_date": result.score_date,
        })
        if len(out) >= limit:
            break
    return out


def get_keyword_history(keyword):
    """
    Get history of scores for a keyword.
    Returns list of dicts: [{date, score, trend_momentum, trend_acceleration, competition_density, avg_price, min_price, max_price, price_spread, listing_count, unique_sellers, trend_values}, ...]
    """
    session = get_session()

    results = (
        session.query(
            Keyword.keyword,
            DailySnapshot.snapshot_date,
            DailySnapshot.trend_momentum,
            DailySnapshot.trend_acceleration,
            DailySnapshot.competition_density,
            DailySnapshot.avg_price,
            DailySnapshot.min_price,
            DailySnapshot.max_price,
            DailySnapshot.price_spread,
            DailySnapshot.listing_count,
            DailySnapshot.unique_sellers,
            DailySnapshot.trend_values,
        )
        .join(DailySnapshot, Keyword.id == DailySnapshot.keyword_id)
        .filter(Keyword.keyword == keyword)
        .order_by(DailySnapshot.snapshot_date.desc())
        .all()
    )

    return [
        {
            "keyword": result.keyword,
            "date": result.snapshot_date,
            "trend_momentum": result.trend_momentum,
            "trend_acceleration": result.trend_acceleration,
            "competition_density": result.competition_density,
            "avg_price": result.avg_price,
            "min_price": result.min_price,
            "max_price": result.max_price,
            "price_spread": result.price_spread,
            "listing_count": result.listing_count,
            "unique_sellers": result.unique_sellers,
            "trend_values": result.trend_values,
        }
        for result in results
    ]
