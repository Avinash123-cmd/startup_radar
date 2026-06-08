from __future__ import annotations

import re
from datetime import datetime

from classification.classifier import MarketClassifier
from intelligence.types import NormalizedSignal, RawSignal


def normalize_signal(raw: RawSignal, classifier: MarketClassifier | None = None) -> NormalizedSignal:
    classifier = classifier or MarketClassifier()
    title = _clean(raw.title)
    description = _clean(raw.description)
    normalized_text = _clean(f"{title} {description}")
    classification = classifier.classify_text(normalized_text)

    return NormalizedSignal(
        source=raw.source,
        external_id=str(raw.external_id),
        title=title[:500],
        description=description,
        url=raw.url or "",
        engagement_score=max(int(raw.engagement_score or 0), 0),
        published_at=raw.published_at or datetime.utcnow(),
        normalized_text=normalized_text,
        category_slug=classification.category_slug,
        classification_confidence=classification.confidence,
        classification_evidence=classification.evidence_terms,
        raw_payload=raw.raw_payload or {},
    )


def _clean(value: str) -> str:
    value = value or ""
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()
