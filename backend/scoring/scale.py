from __future__ import annotations

import math
from datetime import datetime


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def log_scale(value: float, divisor: float, maximum: float) -> float:
    if value <= 0:
        return 0.0
    return clamp(math.log1p(value) / math.log1p(divisor) * maximum, 0.0, maximum)


def age_in_days(dt: datetime, now: datetime | None = None) -> float:
    now = now or datetime.utcnow()
    return max((now - dt).total_seconds() / 86400.0, 0.0)


def recency_decay(dt: datetime, half_life_days: float = 14.0, now: datetime | None = None) -> float:
    days = age_in_days(dt, now)
    if half_life_days <= 0:
        return 1.0
    return 0.5 ** (days / half_life_days)
