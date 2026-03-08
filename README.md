# Market Opportunity Detector

Automated product opportunity discovery system that combines **Google Trends** (demand signals) with **eBay** (supply/competition data) to find trending products with low competition.

## Features

- **Automated Discovery** — Browses eBay categories and extracts product keywords using NLP (spaCy)
- **Semantic Filtering** — Uses word embeddings to filter relevant keywords and reject outliers
- **Trend Analysis** — Fetches Google Trends data to identify rising search interest
- **Opportunity Scoring** — Calculates a 0–100 score using weighted features (momentum, competition density, price spread)
- **Database Storage** — Persists data to PostgreSQL with time-series snapshots
- **REST API** — FastAPI endpoints for querying opportunities and keyword history
- **Dashboard** — Streamlit app with KPIs, charts, and filters
- **Scheduled Pipeline** — GitHub Actions workflow runs weekly data collection automatically

## Tech Stack

| Layer | Technology |
|-------|------------|
| Data Ingestion | eBay Browse API, pytrends (Google Trends) |
| NLP | spaCy (noun chunks, word embeddings) |
| Processing | Pandas, custom feature engineering |
| Database | PostgreSQL (Neon), SQLAlchemy, Alembic |
| API | FastAPI, Uvicorn |
| Dashboard | Streamlit |
| Automation | GitHub Actions (cron) |

## Architecture

```
eBay Category Browse
        ↓
Extract Keywords (spaCy NLP)
        ↓
Semantic Filtering (word embeddings)
        ↓
Google Trends (rising demand?)
        ↓
Feature Engineering (momentum, competition, prices)
        ↓
Opportunity Scoring (Niche Hunter weights)
        ↓
PostgreSQL Storage
        ↓
FastAPI + Streamlit Dashboard
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL (local Docker or cloud like Neon)
- eBay Developer Account ([get credentials](https://developer.ebay.com/))

### Installation

1. Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/market-opportunity-detector.git
cd market-opportunity-detector
pip install -r requirements.txt
python -m spacy download en_core_web_md
```

2. Set up the database (Docker example):

```bash
docker run -d --name market-db \
  -e POSTGRES_PASSWORD=dev \
  -e POSTGRES_DB=market_opportunities \
  -p 5432:5432 postgres
```

3. Create a `.env` file:

```
EBAY_APP_ID=your_app_id_here
EBAY_CERT_ID=your_cert_id_here
DATABASE_URL=postgresql://postgres:dev@localhost:5432/market_opportunities
```

4. Run database migrations:

```bash
alembic upgrade head
```

### Usage

**Run the weekly data collection** (discovers opportunities and saves to database):

```bash
python scripts/collect_weekly.py
```

**Start the API server**:

```bash
cd src
uvicorn api.main:app --reload
```

**Start the dashboard**:

```bash
cd src
streamlit run dashboard/app.py
```

**Backfill historical CSV data** (if you have existing CSVs in `data/history/`):

```bash
python scripts/backfill_from_csv.py
```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /categories` | List tracked categories |
| `GET /opportunities?limit=20` | Top opportunities ranked by score |
| `GET /keywords/{keyword}/history` | Time-series data for a keyword |

## Project Structure

```
src/
  ingestion/
    ebay_scraper.py      # eBay API client + keyword extraction
    google_trends.py     # Google Trends data fetching
    discovery.py         # Discovery pipeline orchestration
  processing/
    features.py          # Feature engineering
  scoring/
    opportunity.py       # Opportunity scoring and ranking
  storage/
    database.py          # SQLAlchemy engine and session
    models.py            # Database models
    crud.py              # CRUD operations
    history.py           # CSV backup storage
  pipeline/
    orchestrator.py      # Pipeline orchestration
  api/
    main.py              # FastAPI endpoints
    queries.py           # Database queries
  dashboard/
    app.py               # Streamlit dashboard
scripts/
  collect_weekly.py      # Weekly data collection entry point
  backfill_from_csv.py   # Load CSV history into database
.github/workflows/
  collect_weekly.yml     # GitHub Actions scheduled automation
```

## Opportunity Scoring

The scoring algorithm uses a "Niche Hunter" strategy that prioritizes low competition:

| Feature | Weight | Rationale |
|---------|--------|-----------|
| Trend Momentum | +0.3 | Reward rising search interest |
| Trend Acceleration | +0.2 | Reward growth that's speeding up |
| Competition Density | -0.5 | Heavily penalize crowded markets |
| Price Spread | -0.2 | Prefer stable pricing |

## License

MIT
