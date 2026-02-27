"""
Feature engineering for market opportunity detection.

Calculates metrics from raw eBay and Google Trends data.
"""


def calculate_trend_momentum(trends):
    """
    Calculate trend momentum as % change between last 4 weeks and previous 4 weeks.

    Returns: float (e.g., 0.15 = 15% growth, -0.10 = 10% decline)
    """
    if len(trends) < 8:
        return 0.0

    last_4 = trends[-4:]
    last_4_avg = sum(last_4) / len(last_4)

    prev_4 = trends[-8:-4]
    prev_4_avg = sum(prev_4) / len(prev_4)

    if prev_4_avg == 0:
        return 0.0

    momentum = (last_4_avg - prev_4_avg) / prev_4_avg
    return round(momentum, 4)


def calculate_trend_acceleration(trends):
    """
    Check if trend momentum is increasing (growth is speeding up).

    Returns: bool
    """
    if len(trends) < 12:
        return False

    # Older momentum: weeks 9-12 vs 5-8
    older_prev = trends[-12:-8]
    older_last = trends[-8:-4]
    older_momentum = (
        (sum(older_last) / 4 - sum(older_prev) / 4) / (sum(older_prev) / 4)
        if sum(older_prev) > 0
        else 0
    )

    # Recent momentum: weeks 5-8 vs 1-4
    recent_prev = trends[-8:-4]
    recent_last = trends[-4:]
    recent_momentum = (
        (sum(recent_last) / 4 - sum(recent_prev) / 4) / (sum(recent_prev) / 4)
        if sum(recent_prev) > 0
        else 0
    )

    return recent_momentum > older_momentum


def calculate_price_stats(products):
    """
    Calculate price statistics for a list of products.

    Returns: dict with:
    - avg_price: average price
    - min_price: minimum price
    - max_price: maximum price
    - price_spread: price spread as % of average price
    """
    prices = [float(p["price"]) for p in products if p.get("price")]

    if not prices:
        return {
            "avg_price": 0,
            "min_price": 0,
            "max_price": 0,
            "price_spread": 0,
        }

    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)

    price_spread = ((max_price - min_price) / avg_price) if avg_price > 0 else 0

    return {
        "avg_price": round(avg_price, 2),
        "min_price": round(min_price, 2),
        "max_price": round(max_price, 2),
        "price_spread": round(price_spread, 2),
    }


def calculate_competition_density(products, trends):
    """
    Calculate competition density as the number of unique sellers divided by the number of products.

    Returns: float (e.g., 0.5 = 50% competition density)
    """
    unique_sellers = len(set([p["seller"] for p in products if p.get("seller")]))
    avg_trend = sum(trends) / len(trends)
    return (unique_sellers / avg_trend) if avg_trend > 0 else 0


def calculate_features(opportunities):
    """
    Calculate features for a list of opportunities.

    Returns: dict with:
    - keyword: keyword
    - price_stats: price statistics
    - competition_density: competition density
    - trend_momentum: trend momentum
    - trend_acceleration: trend acceleration
    """
    feature_map = {}
    for kw, data in opportunities.items():
        products = data["products"]
        trends = data["trends"]
        price_stats = calculate_price_stats(products)
        competition_density = calculate_competition_density(products, trends)
        trend_momentum = calculate_trend_momentum(trends)
        trend_acceleration = calculate_trend_acceleration(trends)
        feature_map[kw] = {
            "price_stats": price_stats,
            "competition_density": competition_density,
            "trend_momentum": trend_momentum,
            "trend_acceleration": trend_acceleration,
        }
    return feature_map
