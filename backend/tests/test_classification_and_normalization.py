from datetime import datetime

from classification.classifier import MarketClassifier
from intelligence.normalization import normalize_signal
from intelligence.types import RawSignal


def test_classifier_returns_category_confidence_and_evidence():
    result = MarketClassifier().classify_text("Visual browser automation agent for web navigation and Playwright tasks")

    assert result.category_slug == "browser-agents"
    assert result.confidence > 0
    assert "browser automation" in result.evidence_terms


def test_normalize_signal_preserves_contract_fields():
    signal = normalize_signal(
        RawSignal(
            source="hacker_news",
            external_id="123",
            title="Show HN: SWE agent for debugging code",
            description="A developer agent that writes tests and refactors code.",
            url="https://example.com",
            engagement_score=42,
            published_at=datetime(2026, 6, 1),
        )
    )

    assert signal.source == "hacker_news"
    assert signal.external_id == "123"
    assert signal.category_slug == "coding-agents"
    assert signal.classification_confidence > 0
    assert signal.normalized_text
