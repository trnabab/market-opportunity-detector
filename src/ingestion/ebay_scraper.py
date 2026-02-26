"""
eBay scraper - fetches product listings from eBay Browse API.

Requires EBAY_APP_ID and EBAY_CERT_ID in your .env file.
"""

import base64
import os
from datetime import datetime
from dotenv import load_dotenv
import requests

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
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
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
        "limit": min(limit, 200)  # eBay max is 200
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


def search_multiple(keywords):
    """Search eBay for multiple keywords, return list of results."""
    results = []
    for keyword in keywords:
        print(f"Searching: {keyword}...")
        result = search_ebay(keyword)
        results.append(result)
        
        if result["success"]:
            print(f"  Found {result['total_results']} results, avg ${result['avg_price']}")
        else:
            print(f"  Error: {result.get('error')}")
    
    return results


# Quick test
if __name__ == "__main__":
    # Test with a few keywords
    test_keywords = ["dumbbells", "yoga mat", "resistance bands"]
    
    print("=" * 50)
    print("eBay Search Test")
    print("=" * 50)
    
    results = search_multiple(test_keywords)
    
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    for r in results:
        if r["success"]:
            print(f"{r['keyword']}: {r['total_results']} results, ${r['avg_price']} avg, {r['unique_sellers']} sellers")
