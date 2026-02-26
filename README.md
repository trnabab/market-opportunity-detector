# Market Opportunity Detector

Finds trending products with low competition by combining Google Trends (demand) and eBay (supply) data.

## What it does

1. Browses eBay categories to discover products
2. Extracts keywords from product titles using NLP
3. Checks if demand is rising on Google Trends
4. Filters to keywords trending upward (Phase 1 complete)
5. Calculates an "opportunity score" based on demand vs competition (coming soon)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
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
```

## Current Status

- [x] eBay category browsing
- [x] NLP keyword extraction (spaCy)
- [x] Google Trends data fetching
- [x] Rising keyword detection
- [x] Discovery pipeline
- [ ] Data cleaning (Phase 2)
- [ ] Opportunity scoring (Phase 3)
- [ ] Database storage (Phase 4)
- [ ] Dashboard (Phase 6)
