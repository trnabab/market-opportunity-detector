# Market Opportunity Detector

Finds trending products with low competition by combining Google Trends (demand) and eBay (supply) data.

## What it does

1. Discovers product keywords from eBay categories
2. Checks if demand is rising on Google Trends
3. Calculates an "opportunity score" based on demand vs competition

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your eBay API credentials:
```
EBAY_APP_ID=your_app_id_here
EBAY_CERT_ID=your_cert_id_here
```

Get eBay credentials at: https://developer.ebay.com/

## Project Structure

```
src/
  ingestion/           # Data fetching
    ebay_scraper.py    # eBay product search
    google_trends.py   # Google Trends data
data/
  raw/                 # Raw data files
```

## Current Status

- [x] eBay search by keyword
- [x] Google Trends data fetching
- [ ] Keyword discovery from categories
- [ ] Opportunity scoring
- [ ] Database storage
- [ ] Dashboard
