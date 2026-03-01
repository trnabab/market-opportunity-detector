from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Date,
    Float,
)
from sqlalchemy.sql import func
from storage.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    ebay_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    seed = Column(String, nullable=False)
    stop_words = Column(JSON)
    anchors = Column(JSON)
    blacklist = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    keyword = Column(String, nullable=False)
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)


class DailySnapshot(Base):
    __tablename__ = "daily_snapshots"

    id = Column(Integer, primary_key=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    snapshot_date = Column(Date)
    trend_momentum = Column(Float)
    trend_acceleration = Column(Boolean)
    competition_density = Column(Float)
    avg_price = Column(Float)
    min_price = Column(Float)
    max_price = Column(Float)
    price_spread = Column(Float)
    listing_count = Column(Integer)
    unique_sellers = Column(Integer)
    trend_values = Column(JSON)


class OpportunityScore(Base):
    __tablename__ = "opportunity_scores"

    id = Column(Integer, primary_key=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    score_date = Column(Date)
    score = Column(Float)
    weights = Column(JSON)
