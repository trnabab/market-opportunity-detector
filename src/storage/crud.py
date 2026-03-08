"""
CRUD operations for database persistence.

Handles create, read, update for categories, keywords, snapshots, and scores.
"""

from datetime import datetime
from storage.database import get_session
from storage.models import Category, Keyword, DailySnapshot, OpportunityScore


def save_category(ebay_id, name, seed, stop_words=None, anchors=None, blacklist=None):
    """
    Save a new category to the database.
    Returns the created category's id.
    """
    session = get_session()
    existing = session.query(Category).filter_by(ebay_id=ebay_id).first()

    if existing:
        return existing.id
    else:
        category = Category(
            ebay_id=ebay_id,
            name=name,
            seed=seed,
            stop_words=stop_words,
            anchors=anchors,
            blacklist=blacklist,
        )
        session.add(category)
        session.commit()
        return category.id


def save_keyword(keyword, category_id):
    """
    Save a keyword to the database.
    If it already exists, update last_seen.
    Returns the keyword's id.
    """
    session = get_session()
    now = datetime.now()

    existing = (
        session.query(Keyword)
        .filter_by(keyword=keyword, category_id=category_id)
        .first()
    )

    if existing:
        existing.last_seen = now
        session.commit()
        return existing.id
    else:
        new_keyword = Keyword(
            keyword=keyword,
            category_id=category_id,
            first_seen=now,
            last_seen=now,
        )
        session.add(new_keyword)
        session.commit()
        return new_keyword.id


def save_daily_snapshot(
    keyword_id,
    snapshot_date,
    trend_momentum,
    trend_acceleration,
    competition_density,
    avg_price,
    min_price,
    max_price,
    price_spread,
    listing_count,
    unique_sellers,
    trend_values,
):
    """
    Save a daily snapshot to the database.
    Returns the created snapshot's id.
    """
    session = get_session()
    snapshot = DailySnapshot(
        keyword_id=keyword_id,
        snapshot_date=snapshot_date,
        trend_momentum=trend_momentum,
        trend_acceleration=trend_acceleration,
        competition_density=competition_density,
        avg_price=avg_price,
        min_price=min_price,
        max_price=max_price,
        price_spread=price_spread,
        listing_count=listing_count,
        unique_sellers=unique_sellers,
        trend_values=trend_values,
    )
    session.add(snapshot)
    session.commit()
    return snapshot.id


def save_opportunity_score(keyword_id, score_date, score, weights):
    """
    Save an opportunity score to the database.
    Returns the created score's id.
    """
    session = get_session()
    opp_score = OpportunityScore(
        keyword_id=keyword_id, score_date=score_date, score=score, weights=weights
    )
    session.add(opp_score)
    session.commit()
    return opp_score.id
