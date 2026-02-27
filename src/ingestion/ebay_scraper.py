"""
eBay scraper - fetches product listings from eBay Browse API.

Requires EBAY_APP_ID and EBAY_CERT_ID in your .env file.
"""

import base64
import os
from datetime import datetime
from dotenv import load_dotenv
import requests
import spacy

# Load the spacy model
nlp = spacy.load("en_core_web_md")

# Load environment variables
load_dotenv()

# Your eBay credentials (from .env file)
EBAY_APP_ID = os.getenv("EBAY_APP_ID")
EBAY_CERT_ID = os.getenv("EBAY_CERT_ID")

# eBay API URLs
OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

# Settings
MARKETPLACE = "EBAY_AU"  # Change to EBAY_US, EBAY_UK, etc. if needed


def get_access_token():
    """
    Get an access token from eBay.

    eBay uses OAuth2 - we exchange our app credentials for a temporary token.
    The token lasts 2 hours, but we get a fresh one each time for simplicity.
    """
    if not EBAY_APP_ID or not EBAY_CERT_ID:
        print("ERROR: Set EBAY_APP_ID and EBAY_CERT_ID in your .env file")
        return None

    # eBay wants credentials as base64-encoded "app_id:cert_id"
    credentials = f"{EBAY_APP_ID}:{EBAY_CERT_ID}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}",
    }

    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }

    response = requests.post(OAUTH_URL, headers=headers, data=data, timeout=30)

    if response.status_code != 200:
        print(f"ERROR: Failed to get token - {response.status_code}")
        print(response.text)
        return None

    token = response.json()["access_token"]
    return token


def search_ebay(keyword, limit=50):
    """
    Search eBay for products matching a keyword.

    Returns a dict with:
    - keyword: what you searched for
    - total_results: how many listings exist
    - avg_price: average price of items found
    - unique_sellers: how many different sellers
    - items: list of individual product data
    """
    token = get_access_token()
    if not token:
        return {"keyword": keyword, "success": False, "error": "No token"}

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE,
    }

    params = {
        "q": keyword,
        "limit": min(limit, 200),  # eBay max is 200
    }

    response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=30)

    if response.status_code != 200:
        return {"keyword": keyword, "success": False, "error": response.text[:200]}

    data = response.json()
    items = data.get("itemSummaries", [])

    # Extract prices and sellers
    prices = []
    sellers = set()

    for item in items:
        # Get price
        price_value = item.get("price", {}).get("value")
        if price_value:
            try:
                prices.append(float(price_value))
            except ValueError:
                pass

        # Get seller
        seller = item.get("seller", {}).get("username")
        if seller:
            sellers.add(seller)

    # Calculate stats
    avg_price = sum(prices) / len(prices) if prices else 0

    return {
        "keyword": keyword,
        "success": True,
        "total_results": data.get("total", len(items)),
        "items_fetched": len(items),
        "avg_price": round(avg_price, 2),
        "min_price": round(min(prices), 2) if prices else 0,
        "max_price": round(max(prices), 2) if prices else 0,
        "unique_sellers": len(sellers),
        "timestamp": datetime.now().isoformat(),
    }


def browse_category(category_id, seed_keyword, limit=50):
    """
    Browse an eBay category and return product listings.

    Returns a list of dicts, each with:
    - title: product title
    - price: listing price
    - seller: seller username
    """
    token = get_access_token()
    if not token:
        return {"list": [], "success": False, "error": "No token"}

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE,
    }

    params = {
        "q": seed_keyword,
        "category_ids": category_id,
        "limit": min(limit, 200),  # eBay max is 200
    }

    response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=30)

    if response.status_code != 200:
        return {"list": [], "success": False, "error": response.text[:200]}

    data = response.json()
    items = data.get("itemSummaries", [])

    # Extract prices and sellers
    all_items = []

    for item in items:
        # Get title
        title = item.get("title")

        # Get price
        price_value = item.get("price", {}).get("value")

        # Get seller
        seller = item.get("seller", {}).get("username")

        all_items.append(
            {
                "title": title,
                "price": price_value,
                "seller": seller,
            }
        )

    # Calculate stats
    return all_items


def is_relevant(phrase, anchors, blacklist=None, threshold=0.35):
    """
    Check if phrase is relevant to category.

    1. Reject if similar to any blacklist word
    2. Accept if average of top 2 anchor scores >= threshold
    """
    phrase_doc = nlp(phrase)

    if not phrase_doc.has_vector:
        return False

    # Step 1: Check blacklist
    if blacklist:
        for bad_word in blacklist:
            bad_doc = nlp(bad_word)
            if phrase_doc.similarity(bad_doc) >= 0.5:
                return False

    # Step 2: Check positive anchors (top 2 average)
    scores = []
    for anchor in anchors:
        anchor_doc = nlp(anchor)
        scores.append(phrase_doc.similarity(anchor_doc))

    scores.sort(reverse=True)
    top_2_avg = sum(scores[:2]) / min(2, len(scores))

    return top_2_avg >= threshold


def extract_keywords(products, stop_words, anchors, blacklist=None):
    """
    Extract product keywords from titles using NLP.
    """
    keyword_map = {}
    stop_words_set = set(word.lower() for word in stop_words)

    for product in products:
        title = product.get("title", "")
        if not title:
            continue

        doc = nlp(title.lower())

        for chunk in doc.noun_chunks:
            phrase = chunk.text.strip()

            # Skip if phrase is too long or too short
            if len(phrase.split()) > 3 or len(phrase) < 3:
                continue

            # Skip if phrase contains numbers or measurements
            if any(
                token.like_num or token.text in ["kg", "cm", "mm", "lb", "lbs"]
                for token in chunk
            ):
                continue

            # Skip if phrase is in stop words
            if phrase.lower() in stop_words_set:
                continue

            # Skip if not relevant (semantic filter - expensive, do last)
            if not is_relevant(phrase, anchors, blacklist):
                continue

            if phrase not in keyword_map:
                keyword_map[phrase] = []
            keyword_map[phrase].append(product)

    return keyword_map
