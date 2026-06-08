from __future__ import annotations

from scoring.scale import clamp, log_scale


def calculate_momentum(
    star_growth_30d: int,
    growth_rate: float,
    signal_strength: float,
    source_count: int,
    news_volume: int,
) -> float:
    repo_velocity = log_scale(star_growth_30d, divisor=50000, maximum=34)
    relative_growth = clamp(growth_rate, 0, 80) / 80 * 18
    external_validation = clamp(signal_strength, 0, 80) / 80 * 32
    source_diversity = min(source_count, 5) / 5 * 10
    volume_bonus = log_scale(news_volume, divisor=120, maximum=6)
    return round(clamp(repo_velocity + relative_growth + external_validation + source_diversity + volume_bonus, 0, 99), 1)


def calculate_competition(repo_count: int, avg_stars: float, mature_repo_count: int) -> int:
    density = log_scale(repo_count, divisor=200, maximum=38)
    maturity = log_scale(avg_stars, divisor=100000, maximum=34)
    incumbency = log_scale(mature_repo_count, divisor=60, maximum=28)
    return int(round(clamp(density + maturity + incumbency, 0, 100)))


def calculate_demand(momentum_score: float, forecast_probability: int, signal_confidence: float) -> int:
    value = momentum_score * 0.55 + forecast_probability * 0.3 + signal_confidence * 0.15
    return int(round(clamp(value, 0, 100)))


def calculate_opportunity(demand_score: int, competition_score: int, confidence: float) -> int:
    opportunity = demand_score * 0.68 + (100 - competition_score) * 0.24 + confidence * 0.08
    return int(round(clamp(opportunity, 0, 100)))


def calculate_growth_probability(slope: float, current_momentum: float, confidence: float) -> int:
    trend_component = clamp((slope + 4.0) / 8.0, 0, 1) * 34
    momentum_component = clamp(current_momentum, 0, 99) / 99 * 44
    confidence_component = clamp(confidence, 0, 100) / 100 * 22
    return int(round(clamp(trend_component + momentum_component + confidence_component, 5, 95)))
