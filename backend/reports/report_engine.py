from __future__ import annotations

import json
import os
from datetime import datetime

import requests
from sqlalchemy.orm import Session

from database.crud import add_weekly_report
from database.models import MarketDataPoint, Opportunity, Repository, TrendHistory, WeeklyReport
from forecasting.forecast_engine import generate_forecasts
from intelligence.trend_engine import latest_trends_as_dicts
from intelligence.types import ReportContext


def generate_weekly_report(db: Session) -> WeeklyReport:
    context = build_report_context(db)
    content = _deterministic_markdown(context)
    llm_content = _try_llm_summary(context, content)
    if llm_content:
        content = llm_content
    summary = _summary(context)
    now = datetime.utcnow()
    slug = f"report-{now.strftime('%Y-%W')}"
    db.query(WeeklyReport).filter(WeeklyReport.slug == slug).delete()
    db.commit()
    return add_weekly_report(
        db=db,
        title=f"AI Startup Radar Briefing - Week {now.strftime('%U, %Y')}",
        slug=slug,
        summary=summary,
        content=content,
        context_snapshot=_context_to_dict(context),
    )


def build_report_context(db: Session) -> ReportContext:
    trends = sorted(latest_trends_as_dicts(db), key=lambda item: item["momentum_score"], reverse=True)
    forecasts = generate_forecasts(db)
    opportunities = [
        {
            "title": opportunity.title,
            "niche": opportunity.niche,
            "score": opportunity.opportunity_score,
            "demand": opportunity.demand_score,
            "competition": opportunity.competition_score,
        }
        for opportunity in db.query(Opportunity).order_by(Opportunity.opportunity_score.desc()).limit(8).all()
    ]
    top_repositories = [
        {
            "name": repo.full_name,
            "stars": repo.stars,
            "forks": repo.forks,
            "language": repo.language,
        }
        for repo in db.query(Repository).order_by(Repository.stars.desc()).limit(8).all()
    ]
    top_signals = [
        {
            "source": signal.source,
            "title": signal.title,
            "score": signal.engagement_score,
            "published_at": signal.published_at.isoformat(),
        }
        for signal in db.query(MarketDataPoint).order_by(MarketDataPoint.engagement_score.desc()).limit(8).all()
    ]
    return ReportContext(trends, forecasts, opportunities, top_repositories, top_signals)


def _deterministic_markdown(context: ReportContext) -> str:
    lines: list[str] = ["# Weekly Market Briefing", ""]
    if not context.trends:
        return "# Weekly Market Briefing\n\nNo market signals are available yet. Run the ingestion pipeline after configuring source credentials."

    leader = context.trends[0]
    lines += [
        "## Executive Summary",
        f"{leader['name']} leads current market momentum with a score of {leader['momentum_score']}, "
        f"{leader['star_growth_30d']} tracked 30-day stars, and {leader['news_volume']} recent external signals.",
        "",
        "## Category Momentum",
    ]
    for trend in context.trends[:6]:
        lines.append(
            f"- **{trend['name']}**: momentum {trend['momentum_score']}, "
            f"growth {trend['growth_rate']}%, mentions {trend['news_volume']}."
        )

    if context.forecasts:
        lines += ["", "## Forecasts"]
        for forecast in context.forecasts[:5]:
            lines.append(
                f"- **{forecast.category}**: {forecast.growth_probability}% 30-day growth probability "
                f"with {forecast.confidence}% confidence."
            )

    if context.opportunities:
        lines += ["", "## Market Gaps"]
        for opportunity in context.opportunities[:5]:
            lines.append(
                f"- **{opportunity['title']}** ({opportunity['niche']}): opportunity {opportunity['score']}, "
                f"demand {opportunity['demand']}, competition {opportunity['competition']}."
            )

    if context.top_repositories:
        lines += ["", "## Repositories To Watch"]
        for repo in context.top_repositories[:5]:
            lines.append(f"- **{repo['name']}**: {repo['stars']} stars, {repo['forks']} forks, {repo['language'] or 'Other'}.")

    if context.top_signals:
        lines += ["", "## Evidence Signals"]
        for signal in context.top_signals[:5]:
            lines.append(f"- **{signal['source']}**: {signal['title']} ({signal['score']} engagement).")

    return "\n".join(lines)


def _summary(context: ReportContext) -> str:
    if not context.trends:
        return "No market signals are available yet."
    leader = context.trends[0]
    return (
        f"{leader['name']} currently leads AI market momentum with a score of {leader['momentum_score']} "
        f"based on repository growth and cross-source signal validation."
    )


def _try_llm_summary(context: ReportContext, deterministic_content: str) -> str | None:
    api_key = os.getenv("OPENAI_KEY", os.getenv("OPENAI_API_KEY", ""))
    if not api_key:
        return None
    try:
        payload = {
            "model": os.getenv("OPENAI_REPORT_MODEL", "gpt-4o-mini"),
            "messages": [
                {
                    "role": "system",
                    "content": "Write concise market intelligence markdown grounded only in the provided JSON and draft.",
                },
                {
                    "role": "user",
                    "content": json.dumps({"context": _context_to_dict(context), "draft": deterministic_content}, default=str),
                },
            ],
            "temperature": 0.2,
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception:
        return None


def _context_to_dict(context: ReportContext) -> dict:
    return {
        "trends": context.trends,
        "forecasts": [forecast.__dict__ for forecast in context.forecasts],
        "opportunities": context.opportunities,
        "top_repositories": context.top_repositories,
        "top_signals": context.top_signals,
    }
