from __future__ import annotations

import re

from classification.taxonomy import CATEGORY_TAXONOMY, DEFAULT_CATEGORY_SLUG
from intelligence.types import ClassificationResult


class MarketClassifier:
    def __init__(self, taxonomy: dict[str, dict[str, object]] | None = None):
        self.taxonomy = taxonomy or CATEGORY_TAXONOMY

    def classify_text(self, text: str) -> ClassificationResult:
        normalized = _normalize(text)
        scores: dict[str, float] = {}
        evidence: dict[str, list[str]] = {}

        for slug, meta in self.taxonomy.items():
            score = 0.0
            terms: list[str] = []
            keywords = meta.get("keywords", {})
            for term, weight in keywords.items():
                occurrences = _count_occurrences(normalized, str(term))
                if occurrences:
                    score += occurrences * float(weight)
                    terms.append(str(term))
            scores[slug] = score
            evidence[slug] = terms

        top_slug = max(scores, key=scores.get)
        top_score = scores[top_slug]
        if top_score <= 0:
            return ClassificationResult(DEFAULT_CATEGORY_SLUG, 0.2, [])

        sorted_scores = sorted(scores.values(), reverse=True)
        second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0.0
        confidence = top_score / (top_score + second_score + 4.0)
        confidence = max(0.35, min(confidence, 0.98))

        return ClassificationResult(
            category_slug=top_slug,
            confidence=round(confidence, 3),
            evidence_terms=evidence[top_slug][:8],
        )


def classify_text(text: str) -> str:
    return MarketClassifier().classify_text(text).category_slug


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _count_occurrences(text: str, term: str) -> int:
    escaped = re.escape(term.lower())
    return len(re.findall(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text))
