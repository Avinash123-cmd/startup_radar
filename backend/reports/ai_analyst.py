"""
AI Market Analyst — Ollama-powered analysis engine
====================================================
Assembles a structured context from all live engines (trend, market gap,
founder ideas, analysis) and submits a grounded prompt to a local Ollama
instance.  Returns a structured dict; falls back gracefully when Ollama is
unavailable.

Public entry point:
    run_ai_analysis(slug: str, db: Session) -> AIAnalysisResult
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

import requests
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from config import get_settings
from database.crud import get_category_by_slug
from database.models import (
    Category,
    MarketDataPoint,
    Repository,
    TrendHistory,
)
from opportunities.founder_engine import FounderIdea, generate_founder_ideas
from opportunities.market_gap_engine import detect_market_gaps

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PRIMARY_MODEL = "qwen3:8b"
FALLBACK_MODEL = None
OLLAMA_TIMEOUT = 300          # seconds per request
MAX_RETRIES = 2               # attempts before giving up on a model
RETRY_BACKOFF = 2.0           # seconds between retries
CACHE_TTL_SECONDS = 3600      # 1 hour in-process cache


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class AIAnalysisResult:
    category: str
    slug: str
    executive_summary: str
    market_overview: str
    key_drivers: list[str]
    risks: list[str]
    startup_opportunities: list[str]
    recommended_startup: str
    confidence: float           # 0.0–1.0
    model_used: str             # which Ollama model responded
    generated_at: datetime = field(default_factory=datetime.utcnow)
    fallback_mode: bool = False  # True when Ollama was unavailable


# ---------------------------------------------------------------------------
# In-process cache  { slug -> (result, expires_at) }
# ---------------------------------------------------------------------------

_cache: dict[str, tuple[AIAnalysisResult, float]] = {}


def _cache_get(slug: str) -> Optional[AIAnalysisResult]:
    entry = _cache.get(slug)
    if entry and time.monotonic() < entry[1]:
        return entry[0]
    _cache.pop(slug, None)
    return None


def _cache_set(slug: str, result: AIAnalysisResult) -> None:
    _cache[slug] = (result, time.monotonic() + CACHE_TTL_SECONDS)


# ---------------------------------------------------------------------------
# Data collection helpers
# ---------------------------------------------------------------------------

def _fetch_trend(db: Session, category_id: int) -> Optional[TrendHistory]:
    return (
        db.query(TrendHistory)
        .filter(TrendHistory.category_id == category_id)
        .order_by(desc(TrendHistory.recorded_at))
        .first()
    )


def _fetch_signals(db: Session, category_id: int, limit: int = 3) -> list[MarketDataPoint]:
    since = datetime.utcnow() - timedelta(days=30)
    return (
        db.query(MarketDataPoint)
        .filter(
            MarketDataPoint.category_id == category_id,
            MarketDataPoint.published_at >= since,
        )
        .order_by(desc(MarketDataPoint.engagement_score))
        .limit(limit)
        .all()
    )


def _fetch_top_repos(db: Session, category_id: int, limit: int = 3) -> list[Repository]:
    return (
        db.query(Repository)
        .filter(Repository.category_id == category_id)
        .order_by(desc(Repository.stars))
        .limit(limit)
        .all()
    )


def _fetch_founder_ideas_for_category(
    db: Session, category_name: str, limit: int = 2
) -> list[FounderIdea]:
    """Run the founder engine and filter to this category only."""
    try:
        all_ideas = generate_founder_ideas(db)
        return [
            i for i in all_ideas
            if i.category.lower() == category_name.lower()
        ][:limit]
    except Exception as exc:
        logger.warning("Founder engine failed: %s", exc)
        return []


def _count_repos(db: Session, category_id: int) -> int:
    return (
        db.query(func.count(Repository.id))
        .filter(Repository.category_id == category_id)
        .scalar()
        or 0
    )


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(
    category: Category,
    trend: TrendHistory,
    signals: list[MarketDataPoint],
    repos: list[Repository],
    ideas: list[FounderIdea],
    repo_count: int,
) -> str:
    """Assemble a grounded, structured analyst prompt."""

    repo_lines = "\n".join(
        f"  - {r.full_name}: {r.stars:,} stars, {r.forks:,} forks, lang={r.language or 'N/A'}"
        for r in repos
    ) or "  No repositories recorded yet."

    signal_lines = "\n".join(
        f"  - [{s.source}] {s.title} (engagement: {s.engagement_score})"
        for s in signals
    ) or "  No recent signals."

    idea_lines = "\n".join(
        f"  - {i.startup_idea}: {i.problem_statement[:120]}... "
        f"(opportunity score: {i.opportunity_score}, confidence: {i.confidence:.2f})"
        for i in ideas
    ) or "  No founder ideas generated for this category."

    # Parse market gaps for this category
    gap_risks: list[str] = []
    gap_opps: list[str] = []
    if trend.growth_rate < 5:
        gap_risks.append("Growth rate below 5% — category may be plateauing.")
    if trend.momentum_score < 30:
        gap_risks.append("Low momentum score — not yet at critical adoption mass.")
    if trend.news_volume == 0:
        gap_risks.append("Zero news coverage detected this period.")
    if trend.star_growth_30d > 500:
        gap_opps.append(f"Strong 30-day star growth ({trend.star_growth_30d:,}) signals rising developer interest.")
    if trend.momentum_score >= 60:
        gap_opps.append("High momentum — infrastructure and SaaS layer products may find fast PMF.")
    if repo_count < 20:
        gap_opps.append(f"Only {repo_count} repositories tracked — ecosystem not yet saturated.")

    risks_text = "\n".join(f"  - {r}" for r in gap_risks) or "  No major risks identified."
    opps_text = "\n".join(f"  - {o}" for o in gap_opps) or "  Monitor for emerging opportunities."

    prompt = f"""You are a senior AI market analyst producing a structured investment brief.
Analyse the following live market intelligence data for the category "{category.name}" and respond with a valid JSON object.

=== MARKET DATA ===

Category: {category.name}
Description: {category.description or "No description available."}

Trend Metrics (latest snapshot):
  Momentum Score: {trend.momentum_score:.1f} / 100
  Growth Rate: {trend.growth_rate:.1f}%
  Star Growth (30d): {trend.star_growth_30d:,}
  News Volume: {trend.news_volume}
  Total Repositories Tracked: {repo_count}

Top Repositories:
{repo_lines}

Recent Market Signals (last 30 days):
{signal_lines}

Identified Risks:
{risks_text}

Identified Opportunities:
{opps_text}

Founder Startup Ideas:
{idea_lines}

=== INSTRUCTIONS ===

Based ONLY on the data above, produce a JSON object with this exact structure:

{{
  "executive_summary": "<2-3 sentence summary of the current state of this category>",
  "market_overview": "<1 paragraph explaining the market dynamics, growth trajectory, and ecosystem maturity>",
  "key_drivers": ["<driver 1>", "<driver 2>", "<driver 3>"],
  "risks": ["<risk 1>", "<risk 2>", "<risk 3>"],
  "startup_opportunities": ["<opportunity 1>", "<opportunity 2>", "<opportunity 3>"],
  "recommended_startup": "<single most actionable startup idea with a one-sentence rationale>",
  "confidence": <float between 0.0 and 1.0 reflecting your confidence given the data quality>
}}

Rules:
- Output ONLY the JSON object. No markdown, no explanation, no preamble.
- Every field must be populated. Do not leave any field empty or null.
- Base all claims strictly on the data provided above. Do not hallucinate trends.
- Confidence should reflect data quality: high signals + high momentum = higher confidence.
- key_drivers, risks, and startup_opportunities must each have at least 2 and at most 5 items.
"""
    prompt = prompt.strip()
    if len(prompt) > 12000:
        prompt = prompt[:12000]
    return prompt



# ---------------------------------------------------------------------------
# Ollama client
# ---------------------------------------------------------------------------

def _ollama_url() -> str:
    settings = get_settings()
    base = settings.get("ollama_endpoint", "http://localhost:11434").rstrip("/")
    return f"{base}/api/generate"


def _call_ollama(model: str, prompt: str) -> dict[str, Any]:
    logger.info("=" * 60)
    logger.info("OLLAMA REQUEST")
    logger.info("Model: %s", model)
    logger.info("Prompt Length: %s chars", len(prompt))
    logger.info("URL: %s", _ollama_url())

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 300,
        },
    }

    start = time.time()

    response = requests.post(
        _ollama_url(),
        json=payload,
        timeout=OLLAMA_TIMEOUT,
    )

    elapsed = round(time.time() - start, 2)

    logger.info("Response Status: %s", response.status_code)
    logger.info("Response Time: %s sec", elapsed)

    response.raise_for_status()

    return response.json()

def _extract_json_from_response(raw_text: str) -> dict[str, Any]:
    """
    Parse the structured JSON block from the LLM response.
    Ollama may wrap the JSON in thinking tags or markdown fences — strip them.
    """
    text = raw_text.strip()

    # Strip <think>...</think> blocks (qwen3 thinking models)
    while "<think>" in text and "</think>" in text:
        start = text.find("<think>")
        end = text.find("</think>") + len("</think>")
        text = text[:start] + text[end:]
        text = text.strip()

    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first and last fence lines
        inner = []
        in_block = False
        for line in lines:
            if line.startswith("```") and not in_block:
                in_block = True
                continue
            if line.startswith("```") and in_block:
                break
            inner.append(line)
        text = "\n".join(inner).strip()

    # Find the first { ... } block
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    return json.loads(text)


def _attempt_ollama(model: str, prompt: str) -> Optional[dict[str, Any]]:
    """Try calling Ollama with retries. Returns parsed dict or None."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Ollama attempt %d/%d with model=%s", attempt, MAX_RETRIES, model)
            raw = _call_ollama(model, prompt)
            response_text = raw.get("response", "")
            if not response_text:
                raise ValueError("Empty response from Ollama")
            logger.info("Ollama response length: %s chars", len(response_text))
            return _extract_json_from_response(response_text)
        except (requests.ConnectionError, requests.Timeout) as exc:
            logger.warning("Ollama unreachable (attempt %d): %s", attempt, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF)
            else:
                return None
        except requests.HTTPError as exc:
            logger.warning("Ollama HTTP error (attempt %d): %s", attempt, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF)
            else:
                return None
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("Ollama response parse error (attempt %d): %s", attempt, exc)
            # Don't retry parse errors — the model responded but output was malformed
            return None
    return None


def clear_analysis_cache() -> None:
    _cache.clear()
    logger.info("AI analysis cache cleared")


# ---------------------------------------------------------------------------
# Deterministic fallback
# ---------------------------------------------------------------------------

def _deterministic_result(
    category: Category,
    trend: TrendHistory,
    signals: list[MarketDataPoint],
    repos: list[Repository],
    ideas: list[FounderIdea],
    repo_count: int,
) -> AIAnalysisResult:
    """
    Produce a rule-based analysis when Ollama is unavailable.
    Matches the same output shape as the LLM path.
    """
    momentum = trend.momentum_score
    growth = trend.growth_rate
    star_growth = trend.star_growth_30d
    signal_count = len(signals)

    strength = (
        "strong upward momentum" if momentum >= 70
        else "moderate growth" if momentum >= 40
        else "early-stage activity"
    )

    exec_summary = (
        f"{category.name} is exhibiting {strength} with a momentum score of "
        f"{momentum:.1f}/100 and {star_growth:,} stars gained in the last 30 days. "
        f"{'Market signal coverage is healthy.' if signal_count >= 10 else 'Signal coverage is limited — run the pipeline for richer data.'}"
    )

    market_overview = (
        f"The {category.name} ecosystem currently tracks {repo_count} repositories with a "
        f"{growth:.1f}% growth rate. {signal_count} recent signals across community and media "
        f"sources have been recorded. {'Ecosystem maturity is accelerating.' if momentum >= 60 else 'The category is in early formative stages.'}"
    )

    key_drivers: list[str] = []
    if star_growth > 200:
        key_drivers.append(f"Developer adoption is accelerating ({star_growth:,} stars in 30d).")
    if momentum >= 50:
        key_drivers.append("Momentum score indicates sustained community interest.")
    if repos:
        key_drivers.append(f"Leading repositories ({repos[0].full_name}) anchoring ecosystem.")
    if not key_drivers:
        key_drivers.append("Early signals present but require sustained collection for validation.")

    risks: list[str] = []
    if growth < 5:
        risks.append("Growth rate below 5% — watch for plateau signals.")
    if signal_count < 5:
        risks.append("Thin signal coverage reduces forecast reliability.")
    if momentum < 30:
        risks.append("Low momentum — category has not yet reached critical developer mass.")
    if not risks:
        risks.append("No significant risk factors identified based on current data.")

    opps: list[str] = []
    if star_growth > 500:
        opps.append("High star velocity creates early mover advantage for tooling products.")
    if momentum >= 60:
        opps.append("SaaS wrappers and managed services can ride accelerating adoption.")
    if repo_count < 20:
        opps.append("Low repository saturation — founding team can still define the category.")
    if not opps:
        opps.append("Monitor this category — early signals may crystallise into material gaps.")

    recommended = (
        ideas[0].startup_idea
        if ideas
        else f"Vertical workflow automation platform for the {category.name} ecosystem."
    )

    # Confidence mirrors the analysis engine formula
    max_signals = 50
    max_repos = 30
    confidence = round(
        (min(signal_count / max_signals, 1.0) * 0.40)
        + (min(repo_count / max_repos, 1.0) * 0.30)
        + 0.30,
        3,
    )

    return AIAnalysisResult(
        category=category.name,
        slug=category.slug,
        executive_summary=exec_summary,
        market_overview=market_overview,
        key_drivers=key_drivers,
        risks=risks,
        startup_opportunities=opps,
        recommended_startup=recommended,
        confidence=confidence,
        model_used="deterministic-fallback",
        fallback_mode=True,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_ai_analysis(slug: str, db: Session) -> AIAnalysisResult:
    """
    Full pipeline:
      1. Check in-process cache (1h TTL).
      2. Resolve category + pull all engine data.
      3. Build structured prompt.
      4. Try PRIMARY_MODEL → FALLBACK_MODEL → deterministic fallback.
      5. Cache and return.

    Raises ValueError if the category slug is not found.
    Raises RuntimeError if trend data is absent (pipeline not yet run).
    """

    # ── Cache hit ────────────────────────────────────────────────────────────
    cached = _cache_get(slug)
    if cached:
        logger.info("Cache hit for slug=%s", slug)
        return cached

    # ── Resolve category ─────────────────────────────────────────────────────
    category: Optional[Category] = get_category_by_slug(db, slug)
    if not category:
        raise ValueError(f"Category with slug '{slug}' not found.")

    # ── Gather data ──────────────────────────────────────────────────────────
    trend = _fetch_trend(db, category.id)
    if not trend:
        raise RuntimeError(
            f"No trend data for '{category.name}'. Run the pipeline first."
        )

    signals = _fetch_signals(db, category.id)
    repos = _fetch_top_repos(db, category.id)
    ideas = _fetch_founder_ideas_for_category(db, category.name)
    repo_count = _count_repos(db, category.id)

    # ── Build prompt ─────────────────────────────────────────────────────────
    prompt = _build_prompt(category, trend, signals, repos, ideas, repo_count)

    # ── Try Ollama (primary then fallback model) ──────────────────────────────
    model_used: Optional[str] = None
    parsed: Optional[dict[str, Any]] = None

    models = [PRIMARY_MODEL]

    if FALLBACK_MODEL:
        models.append(FALLBACK_MODEL)

    for model in models:
        parsed = _attempt_ollama(model, prompt)
        if parsed:
            model_used = model
            logger.info("Ollama responded successfully with model=%s", model)
            break

    # ── Build result ─────────────────────────────────────────────────────────
    if parsed and model_used:
        def _list(key: str, fallback: list[str]) -> list[str]:
            val = parsed.get(key, fallback)
            return val if isinstance(val, list) and val else fallback

        def _str(key: str, fallback: str) -> str:
            val = parsed.get(key, "")
            return val.strip() if isinstance(val, str) and val.strip() else fallback

        def _float(key: str, fallback: float) -> float:
            val = parsed.get(key, fallback)
            try:
                return round(min(max(float(val), 0.0), 1.0), 3)
            except (TypeError, ValueError):
                return fallback

        result = AIAnalysisResult(
            category=category.name,
            slug=category.slug,
            executive_summary=_str("executive_summary", "No summary generated."),
            market_overview=_str("market_overview", "No overview generated."),
            key_drivers=_list("key_drivers", ["Insufficient data for driver analysis."]),
            risks=_list("risks", ["Risk analysis unavailable."]),
            startup_opportunities=_list("startup_opportunities", ["No opportunities identified."]),
            recommended_startup=_str("recommended_startup", "No recommendation generated."),
            confidence=_float("confidence", 0.5),
            model_used=model_used,
            fallback_mode=False,
        )
    else:
        logger.warning(
            "Ollama unavailable for slug=%s — using deterministic fallback.", slug
        )
        result = _deterministic_result(
            category, trend, signals, repos, ideas, repo_count
        )

    _cache_set(slug, result)
    return result
