"""
Discovery pipeline - finds trending products with low competition.

Ties together eBay browsing, keyword extraction, and Google Trends.
"""

from ebay_scraper import browse_category, extract_keywords
from google_trends import fetch_trends, filter_rising_keywords


# eBay category IDs (for reference)
CATEGORIES = {
    "strength_training": {
        "id": "28088",
        "seed": "weights",
        "stop_words": ["weights", "training", "strength", "gym", "fitness", "exercise"],
        "anchors": [
            "dumbbell",
            "barbell",
            "kettlebell",
            "weight plate",
            "bench press",
            "squat rack",
            "resistance band",
            "battle ropes",
            "pull up bar",
        ],
        "blacklist": [
            "fishing",
            "motorcycle",
            "wheel",
            "curtain",
            "sinker",
            "balance",
            "blind",
            "drape",
        ],
    },
    "yoga": {
        "id": "28063",
        "seed": "yoga",
        "stop_words": ["yoga", "pilates", "mat", "exercise", "fitness", "stretching"],
        "anchors": [
            "yoga mat",
            "yoga block",
            "yoga strap",
            "yoga belt",
            "yoga wheel",
            "yoga ball",
            "yoga ring",
        ],
        "blacklist": [
            "car",
            "motorcycle",
            "fishing",
            "curtain",
        ],
    },
    "cardio": {
        "id": "28060",
        "seed": "treadmill",
        "stop_words": ["cardio", "running", "exercise", "fitness", "machine"],
        "anchors": [
            "treadmill",
            "elliptical",
            "rowing machine",
            "stationary bike",
            "jump rope",
            "stepper",
            "exercise bike",
        ],
        "blacklist": [
            "car",
            "motorcycle",
            "fishing",
            "curtain",
            "sewing",
        ],
    },
}


def discover_opportunities(category, limit=100):
    """
    Discover trending product opportunities in an eBay category.

    Steps:
    1. Browse eBay category for products
    2. Extract keywords from product titles
    3. Check Google Trends for rising interest
    4. Return keywords that are trending up
    """
    # Get products from eBay
    products = browse_category(category["id"], category["seed"], limit)
    # Get keywords from titles
    keyword_map = extract_keywords(
        products, category["stop_words"], category["anchors"], category.get("blacklist")
    )
    keywords = list(keyword_map.keys())
    # Check trends in batches of 5
    all_rising_keywords = {}
    for i in range(0, len(keywords), 5):
        batch = keywords[i : i + 5]
        trends = fetch_trends(batch)
        if not trends.empty:
            rising_data = filter_rising_keywords(trends)
            all_rising_keywords.update(rising_data)
    # Filter keyword_map to only rising keywords
    rising_map = {
        kw: {"products": keyword_map[kw], "trends": all_rising_keywords[kw]}
        for kw in all_rising_keywords.keys()
        if kw in keyword_map
    }
    return rising_map


if __name__ == "__main__":
    print("=" * 50)
    print("Discovery Pipeline Test")
    print("=" * 50)

    # Test with Strength Training category
    results = discover_opportunities(CATEGORIES["strength_training"])

    print("\nRising keywords found:")
    for keyword in results:
        print(f"  - {keyword}")
