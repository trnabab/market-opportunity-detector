# Market Opportunity Detector

Finds trending products with low competition by combining Google Trends (demand) and eBay (supply) data.

## What it does

1. Browses eBay categories to discover products
2. Extracts keywords from product titles using NLP
3. Filters keywords using semantic similarity (word embeddings)
4. Checks if demand is rising on Google Trends
5. Calculates features: trend momentum, acceleration, competition density, price spread
6. Calculates an "opportunity score" (0-100) using weighted features

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_md
```

2. Create a `.env` file with your eBay API credentials:
```
EBAY_APP_ID=your_app_id_here
EBAY_CERT_ID=your_cert_id_here
```

Get eBay credentials at: https://developer.ebay.com/

## Usage

Run the discovery pipeline:
```bash
cd src/ingestion
python discovery.py
```

## Project Structure

```
src/
  ingestion/
    ebay_scraper.py    # eBay API client + keyword extraction
    google_trends.py   # Google Trends data + rising filter
    discovery.py       # Discovery pipeline orchestration
  processing/
    features.py        # Feature engineering (momentum, competition, etc.)
  scoring/
    opportunity.py     # Opportunity scoring and ranking
```

## Current Status

- [x] eBay category browsing
- [x] NLP keyword extraction (spaCy)
- [x] Semantic filtering with word embeddings
- [x] Google Trends data fetching
- [x] Rising keyword detection
- [x] Discovery pipeline
- [x] Feature engineering (Phase 2)
- [x] Opportunity scoring (Phase 3)
- [ ] Database storage (Phase 4)
- [ ] Dashboard (Phase 6)
