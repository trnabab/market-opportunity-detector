WEIGHTS = {
    "trend_momentum": 0.3,
    "trend_acceleration": 0.2,
    "competition_density": -0.5,
    "price_spread": -0.2,
}


def normalize_features(features_dict):
    """
    Normalize features across all keywords using min-max scaling.

    Input: {keyword: {trend_momentum: 0.05, competition_density: 0.01, ...}}
    Output: {keyword: {trend_momentum: 0.7, competition_density: 0.2, ...}}

    All output values will be between 0 and 1.
    """
    all_values = {
        "trend_momentum": [],
        "competition_density": [],
        "price_spread": [],
        "trend_acceleration": [],
    }

    for kw, features in features_dict.items():
        all_values["trend_momentum"].append(features["trend_momentum"])
        all_values["competition_density"].append(features["competition_density"])
        all_values["price_spread"].append(features["price_stats"]["price_spread"])
        all_values["trend_acceleration"].append(
            1.0 if features["trend_acceleration"] else 0.0
        )

    # Step 2: Calculate ranges
    ranges = {}
    for feature, values in all_values.items():
        ranges[feature] = (min(values), max(values))

    # Step 3: Normalize each keyword
    normalized_map = {}
    keywords = list(features_dict.keys())

    for i, kw in enumerate(keywords):
        normalized_map[kw] = {}
        for feature in all_values.keys():
            value = all_values[feature][i]
            min_val, max_val = ranges[feature]
            if max_val == min_val:
                normalized_map[kw][feature] = 0.5
            else:
                normalized_map[kw][feature] = (value - min_val) / (max_val - min_val)

    return normalized_map


def calculate_scores(normalized_features, weights=WEIGHTS):
    """
    Calculate opportunity scores for all keywords.

    Returns: dict of {keyword: score} where score is 0-100
    """
    min_possible = sum(w for w in weights.values() if w < 0)
    max_possible = sum(w for w in weights.values() if w > 0)
    score_range = max_possible - min_possible

    scores = {}
    for kw, features in normalized_features.items():
        raw_score = sum(features[feature] * weights[feature] for feature in features)
        scaled = (raw_score - min_possible) / score_range * 100
        scores[kw] = round(scaled, 1)

    return scores


def rank_opportunities(features_dict, weights=WEIGHTS):
    """
    Rank keywords by opportunity score.

    Input: raw features from calculate_features()
    Output: list of (keyword, score) tuples, sorted highest to lowest
    """
    normalized_features = normalize_features(features_dict)
    scores = calculate_scores(normalized_features, weights)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
