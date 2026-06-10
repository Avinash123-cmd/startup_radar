"""
Founder Intelligence Engine
===========================
Transforms detected market gaps into actionable startup opportunity briefs for
founders. Each brief includes a category-specific startup idea, target customer,
problem statement, MVP features, pricing model, revenue model, GTM strategy,
competition assessment, build difficulty, time-to-MVP estimate, and a composite
confidence score.

Entry point: ``generate_founder_ideas(db)``
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from intelligence.types import MarketGap
from opportunities.market_gap_engine import detect_market_gaps

# ---------------------------------------------------------------------------
# Output dataclass
# ---------------------------------------------------------------------------

@dataclass
class FounderIdea:
    title: str
    category: str
    opportunity_score: int
    startup_idea: str
    target_customer: str
    problem_statement: str
    mvp_features: list[str]
    pricing_model: str
    revenue_model: str
    go_to_market: str
    competition_level: str          # "Low" | "Medium" | "High"
    build_difficulty: str           # "Low" | "Medium" | "High"
    estimated_time_to_mvp: str      # e.g. "6–10 weeks"
    confidence: float               # 0.0–1.0


# ---------------------------------------------------------------------------
# Category-specific idea profiles
# ---------------------------------------------------------------------------
# Each entry maps a category slug to a list of idea blueprints.  A blueprint
# carries all static fields that differ by category; dynamic fields (scores,
# confidence, etc.) are computed from live gap data at runtime.

@dataclass(frozen=True)
class _IdeaBlueprint:
    startup_idea: str
    target_customer: str
    problem_statement: str
    mvp_features: list[str]
    pricing_model: str
    revenue_model: str
    go_to_market: str
    build_difficulty: str           # baseline; may be adjusted by gap size
    estimated_time_to_mvp: str


_CATEGORY_PROFILES: dict[str, list[_IdeaBlueprint]] = {
    # ── AI Agents ────────────────────────────────────────────────────────────
    "ai-agents": [
        _IdeaBlueprint(
            startup_idea="Agent Monitoring & Observability Platform",
            target_customer="ML/platform engineers deploying multi-agent pipelines in production",
            problem_statement=(
                "Teams running autonomous agent workflows have no reliable way to trace "
                "decisions, detect loops, measure latency per step, or audit tool calls — "
                "leading to silent failures and uncontrolled API spend."
            ),
            mvp_features=[
                "Real-time agent execution traces with step-level latency",
                "Token usage and cost dashboard per agent/workflow",
                "Alert rules on error rate, stall detection, and infinite loops",
                "SDK-based instrumentation for LangChain, CrewAI, AutoGen",
                "Exportable audit logs (JSON / CSV)",
            ],
            pricing_model="Seat-based SaaS — Free tier (1 agent), $49/mo Starter, $299/mo Team",
            revenue_model="Recurring subscription + usage-based overages on event volume",
            go_to_market=(
                "Open-source the SDK; monetise the hosted dashboard. "
                "Target AI engineer communities (Hugging Face, LangChain Discord). "
                "Publish cost-reduction case studies on dev.to / Substack."
            ),
            build_difficulty="Medium",
            estimated_time_to_mvp="8–12 weeks",
        ),
        _IdeaBlueprint(
            startup_idea="Agent Security & Prompt Injection Scanner",
            target_customer="Security-conscious enterprises adopting AI agents in customer-facing products",
            problem_statement=(
                "Prompt injection, tool misuse, and data exfiltration are poorly understood "
                "attack vectors in agent deployments; no purpose-built scanner exists for "
                "agent pipelines the way SAST tools exist for code."
            ),
            mvp_features=[
                "Automated prompt injection test suite against agent endpoints",
                "Tool-call policy enforcement (allowlist / denylist)",
                "PII leakage detection in agent outputs",
                "CI/CD integration (GitHub Actions, GitLab)",
                "Compliance report generator (SOC-2 friendly)",
            ],
            pricing_model="Per-scan pricing + enterprise annual contracts",
            revenue_model="Usage-based + enterprise licensing",
            go_to_market=(
                "Partner with AI security researchers for credibility. "
                "Offer free scans for open-source agent repos. "
                "Conference presence at DEF CON AI Village and RSA."
            ),
            build_difficulty="High",
            estimated_time_to_mvp="12–16 weeks",
        ),
        _IdeaBlueprint(
            startup_idea="Agent Memory Infrastructure",
            target_customer="Developers building long-running or personalised AI agents",
            problem_statement=(
                "Stateless LLM calls force developers to implement their own memory, "
                "context compression, and retrieval — every team reinvents the same "
                "unreliable infrastructure."
            ),
            mvp_features=[
                "Managed vector + episodic memory store per agent identity",
                "Context compression with configurable summarisation strategies",
                "Memory search API (semantic + recency-weighted)",
                "Multi-session persistence and branching",
                "Drop-in middleware for LangChain and AutoGen",
            ],
            pricing_model="Storage + query throughput tiers; Free / $29 / $149 / Enterprise",
            revenue_model="Consumption SaaS",
            go_to_market=(
                "Publish benchmark showing memory-augmented agents outperform stateless ones. "
                "Integrate with top frameworks and appear in their docs. "
                "Developer-led PLG with free tier."
            ),
            build_difficulty="Medium",
            estimated_time_to_mvp="6–10 weeks",
        ),
    ],

    # ── LLM Frameworks ───────────────────────────────────────────────────────
    "llm-frameworks": [
        _IdeaBlueprint(
            startup_idea="RAG Pipeline Quality & Evaluation Platform",
            target_customer="ML engineers and LLM application developers building RAG systems",
            problem_statement=(
                "Teams deploying Retrieval-Augmented Generation have no standard way to "
                "measure retrieval precision, answer faithfulness, or regression between "
                "prompt / chunk-size / model changes."
            ),
            mvp_features=[
                "Automated faithfulness and relevance scoring (RAGAS-compatible)",
                "A/B test runner for retrieval strategies",
                "Dataset management for golden QA pairs",
                "Regression alerts on metric degradation",
                "Integration with LangChain, LlamaIndex, and custom pipelines",
            ],
            pricing_model="Freemium — Free (100 evals/mo), $79/mo Growth, custom Enterprise",
            revenue_model="Subscription + per-evaluation overages",
            go_to_market=(
                "Contribute evaluation metrics to LangChain / LlamaIndex communities. "
                "Publish public leaderboard of open RAG benchmarks. "
                "Reach ML Engineers via Weights & Biases and Hugging Face."
            ),
            build_difficulty="Medium",
            estimated_time_to_mvp="8–10 weeks",
        ),
        _IdeaBlueprint(
            startup_idea="LLM Cost Governance & FinOps Dashboard",
            target_customer="Engineering leaders and platform teams running multi-model LLM fleets",
            problem_statement=(
                "As LLM API spend scales, organisations lack per-feature, per-model, and "
                "per-team cost attribution, making budget control and model selection "
                "decisions opaque."
            ),
            mvp_features=[
                "Token spend attribution by project, team, and feature flag",
                "Multi-provider normalised cost view (OpenAI, Anthropic, Gemini, OSS)",
                "Anomaly alerts on spend spikes",
                "Model swap recommendation engine (cost vs. quality trade-off)",
                "Export to Datadog / Grafana",
            ],
            pricing_model="Percentage of monitored spend (0.5%) or flat $199/mo",
            revenue_model="SaaS + optional advisory tier",
            go_to_market=(
                "Target CTOs via LinkedIn thought leadership on LLM FinOps. "
                "Partner with cloud cost tools (Infracost, Vantage). "
                "Open-source the SDK; charge for the dashboard."
            ),
            build_difficulty="Medium",
            estimated_time_to_mvp="6–8 weeks",
        ),
    ],

    # ── Browser & Desktop Automation Agents ──────────────────────────────────
    "browser-agents": [
        _IdeaBlueprint(
            startup_idea="No-Code Browser Automation SaaS",
            target_customer="Operations teams and non-technical business users automating web workflows",
            problem_statement=(
                "Existing RPA tools (UiPath, Automation Anywhere) are expensive and "
                "brittle; AI browser agents are powerful but require engineering effort "
                "to configure and maintain."
            ),
            mvp_features=[
                "Point-and-click workflow recorder with AI intent understanding",
                "Natural language instruction interface ('go to X, find Y, fill Z')",
                "Schedule and trigger management",
                "Error recovery with human-in-the-loop fallback",
                "Audit trail and run history",
            ],
            pricing_model="Per-workflow execution credits; $0 / $49 / $199 monthly tiers",
            revenue_model="Consumption + seat-based subscription",
            go_to_market=(
                "Target ops and RevOps personas on Product Hunt and LinkedIn. "
                "Template marketplace for common workflows (lead scraping, form filling). "
                "Affiliate partnerships with no-code tool communities."
            ),
            build_difficulty="High",
            estimated_time_to_mvp="12–18 weeks",
        ),
        _IdeaBlueprint(
            startup_idea="Browser Agent Testing & Reliability Layer",
            target_customer="QA engineers and developers building AI-driven browser agents",
            problem_statement=(
                "Browser agent pipelines are inherently flaky; there are no purpose-built "
                "tools to replay, assert, and regression-test AI-driven browser sessions "
                "the way Playwright/Cypress test traditional UIs."
            ),
            mvp_features=[
                "Session recording and deterministic replay",
                "DOM-change resilience layer (AI-based selector healing)",
                "Parallel execution with result diffing",
                "CI pipeline integration",
                "Flakiness score per step",
            ],
            pricing_model="Per-test-run pricing; $0 / $99 / $499 monthly",
            revenue_model="Subscription + usage-based",
            go_to_market=(
                "Open-source the replay engine; monetise the managed platform. "
                "Integrate with browser-use, Skyvern, and LaVague. "
                "Reach QA engineers via TestingConf, MoT."
            ),
            build_difficulty="High",
            estimated_time_to_mvp="10–14 weeks",
        ),
    ],

    # ── Voice & Audio AI ─────────────────────────────────────────────────────
    "voice-ai": [
        _IdeaBlueprint(
            startup_idea="AI Call Centre SaaS",
            target_customer="SMB customer support teams and BPO providers",
            problem_statement=(
                "Hiring and retaining call centre agents is expensive; off-the-shelf IVR "
                "systems are rigid and frustrating; GPT-quality voice assistants require "
                "months of custom integration work."
            ),
            mvp_features=[
                "Pre-built voice agent with FAQ ingestion (knowledge base upload)",
                "Live call transcription and sentiment tracking",
                "Escalation routing to human agents with full context hand-off",
                "PSTN and SIP integration (Twilio / Vonage)",
                "Analytics dashboard (resolution rate, AHT, CSAT proxy)",
            ],
            pricing_model="Per-minute call pricing + $199/mo base; Enterprise custom",
            revenue_model="Consumption + platform subscription",
            go_to_market=(
                "Target support-heavy verticals: e-commerce, healthcare scheduling, logistics. "
                "Partner with Shopify app marketplace and Zendesk ecosystem. "
                "Launch with a 'replace your IVR in 48h' positioning."
            ),
            build_difficulty="High",
            estimated_time_to_mvp="14–20 weeks",
        ),
        _IdeaBlueprint(
            startup_idea="Voice Quality Analytics & Coaching Platform",
            target_customer="Sales and customer success teams running high-volume calls",
            problem_statement=(
                "Managers cannot listen to every sales or support call; existing speech "
                "analytics tools are expensive and non-actionable — they score but don't "
                "coach."
            ),
            mvp_features=[
                "Auto-transcription and call scoring (talk ratio, filler words, objection handling)",
                "AI coaching nudges per rep per call",
                "Competitor mention and topic extraction",
                "CRM sync (Salesforce, HubSpot)",
                "Weekly coaching digest email",
            ],
            pricing_model="Per-seat SaaS — $35/user/mo; Enterprise volume discounts",
            revenue_model="Recurring subscription",
            go_to_market=(
                "Target RevOps and Sales Enablement personas. "
                "Partner with Gong/Chorus resellers as a cheaper alternative. "
                "Free 30-day trial with instant Zoom/Meet integration."
            ),
            build_difficulty="Medium",
            estimated_time_to_mvp="8–12 weeks",
        ),
    ],

    # ── AI Coding Assistants ──────────────────────────────────────────────────
    "coding-agents": [
        _IdeaBlueprint(
            startup_idea="AI Code Review & PR Intelligence Platform",
            target_customer="Engineering teams at Series A–C startups with growing codebases",
            problem_statement=(
                "Human code review is a bottleneck; AI-generated code from Copilot/Cursor "
                "ships bugs at scale; teams lack automated, contextual PR feedback beyond "
                "linters and static analysis."
            ),
            mvp_features=[
                "LLM-powered PR summary and risk classification",
                "Security and logic bug detection with explanation",
                "Test coverage gap identification per PR",
                "Review time SLA tracking per engineer",
                "GitHub / GitLab bot integration",
            ],
            pricing_model="Per-seat — $19/dev/mo; Team $99/mo (up to 10 devs)",
            revenue_model="Subscription",
            go_to_market=(
                "GitHub Marketplace listing as primary acquisition channel. "
                "Freemium for open-source repos. "
                "Target CTOs via developer-tool newsletters (TLDR, Changelog)."
            ),
            build_difficulty="Medium",
            estimated_time_to_mvp="6–8 weeks",
        ),
        _IdeaBlueprint(
            startup_idea="Autonomous Test Generation Agent",
            target_customer="Backend and full-stack engineers with low test coverage",
            problem_statement=(
                "Writing unit and integration tests is tedious and routinely skipped under "
                "deadline pressure; no existing tool generates semantically correct, "
                "maintainable tests automatically from existing code."
            ),
            mvp_features=[
                "AST-aware test generation for Python, TypeScript, Go",
                "Edge case and boundary condition inference",
                "Existing test-style matching (pytest / Jest / Go testing conventions)",
                "CI PR comment with generated test diff",
                "Coverage delta reporting",
            ],
            pricing_model="Usage-based — $0.005 per generated test; Team $79/mo unlimited",
            revenue_model="Consumption + subscription",
            go_to_market=(
                "VSCode extension for instant adoption. "
                "Viral: tweet 'before/after coverage' screenshots. "
                "Target platform/DX teams at fast-scaling startups."
            ),
            build_difficulty="High",
            estimated_time_to_mvp="10–14 weeks",
        ),
    ],

    # ── AI Image & Video Generation ───────────────────────────────────────────
    "multimodal-generation": [
        _IdeaBlueprint(
            startup_idea="Brand-Consistent AI Image Generation Platform",
            target_customer="Marketing teams and creative agencies producing content at scale",
            problem_statement=(
                "Generic AI image tools produce off-brand results; adapting outputs to "
                "brand guidelines (colours, style, typography) requires manual post-processing "
                "that defeats the automation value proposition."
            ),
            mvp_features=[
                "Brand kit ingestion (logo, colour palette, typography, example imagery)",
                "Style-locked generation with brand consistency scoring",
                "Batch generation with campaign templating",
                "One-click export to Figma, Canva, Adobe Express",
                "Usage rights audit trail",
            ],
            pricing_model="Credits-based — $0 (50 credits), $49/mo (500), $199/mo (2500)",
            revenue_model="Consumption + subscription",
            go_to_market=(
                "Freemium launch on Product Hunt. "
                "Agency partner programme with white-label option. "
                "Integrations with Notion and Webflow for content teams."
            ),
            build_difficulty="Medium",
            estimated_time_to_mvp="8–12 weeks",
        ),
        _IdeaBlueprint(
            startup_idea="AI Video Ad Generator for E-Commerce",
            target_customer="D2C brands and performance marketing teams running paid social",
            problem_statement=(
                "Creating video ads is expensive ($2k–$20k per production); AI video "
                "tools are generic and produce uncanny outputs; brands need product-aware, "
                "platform-optimised short-form video at volume."
            ),
            mvp_features=[
                "Product image → 15/30s video ad generation",
                "Platform-specific templates (TikTok, Meta Reels, YouTube Shorts)",
                "AI voiceover with tone controls (urgent, aspirational, etc.)",
                "A/B variant generation from a single brief",
                "Direct publish to Meta Ads Manager",
            ],
            pricing_model="Per-video or $149/mo unlimited (SMB), Enterprise custom",
            revenue_model="Subscription + usage overages",
            go_to_market=(
                "DTC Slack communities and Shopify partners. "
                "Performance marketing agencies as channel partners. "
                "'Replace your UGC agency in one click' positioning."
            ),
            build_difficulty="High",
            estimated_time_to_mvp="12–16 weeks",
        ),
    ],
}

# Fallback blueprint for categories not explicitly mapped
_DEFAULT_BLUEPRINTS: list[_IdeaBlueprint] = [
    _IdeaBlueprint(
        startup_idea="Vertical SaaS Workflow Automation Platform",
        target_customer="Operations and product teams in the target vertical",
        problem_statement=(
            "Teams in this emerging category lack purpose-built tooling and are forced "
            "to stitch together generic tools, creating brittle, undifferentiated stacks."
        ),
        mvp_features=[
            "Workflow builder with category-specific step templates",
            "Integration hub for the top 5 tools in the vertical",
            "Analytics and reporting dashboard",
            "Team collaboration and permissions",
            "API for custom integrations",
        ],
        pricing_model="Seat-based SaaS — Free / $49 / $199 / Enterprise",
        revenue_model="Recurring subscription",
        go_to_market=(
            "Community-led growth in vertical-specific Slack/Discord groups. "
            "Content marketing targeting early adopters. "
            "Direct outreach to 50 design partners."
        ),
        build_difficulty="Medium",
        estimated_time_to_mvp="8–12 weeks",
    )
]


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------

def _compute_confidence(gap: MarketGap) -> float:
    """
    Weighted confidence (0.0–1.0):
      35% — raw gap confidence from signal engine
      25% — demand score (normalised to 0–100)
      25% — inverse competition (low competition → higher confidence)
      15% — opportunity score (normalised to 0–100)
    """
    demand_norm = min(gap.demand_score / 100.0, 1.0)
    competition_inv = 1.0 - min(gap.competition_score / 100.0, 1.0)
    opp_norm = min(gap.opportunity_score / 100.0, 1.0)
    gap_conf = min(max(gap.confidence / 100.0, 0.0), 1.0)

    raw = (
        gap_conf       * 0.35
        + demand_norm  * 0.25
        + competition_inv * 0.25
        + opp_norm     * 0.15
    )
    return round(min(max(raw, 0.0), 1.0), 3)


# ---------------------------------------------------------------------------
# Competition & difficulty derivation
# ---------------------------------------------------------------------------

def _competition_label(score: int) -> str:
    if score >= 65:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"


def _build_difficulty_adjustment(base: str, gap: MarketGap) -> str:
    """Nudge difficulty up if evidence_terms are sparse (less research to stand on)."""
    if base == "Low":
        return "Low"
    if base == "High":
        return "High"
    # Medium → possibly High if data is thin
    if len(gap.evidence_terms) < 3 and gap.confidence < 40.0:
        return "High"
    return "Medium"


# ---------------------------------------------------------------------------
# Idea selection — pick the blueprint whose index correlates with opportunity rank
# ---------------------------------------------------------------------------

def _select_blueprint(slug: str, rank_index: int) -> _IdeaBlueprint:
    blueprints = _CATEGORY_PROFILES.get(slug, _DEFAULT_BLUEPRINTS)
    return blueprints[rank_index % len(blueprints)]


# ---------------------------------------------------------------------------
# Title generation
# ---------------------------------------------------------------------------

def _build_title(blueprint: _IdeaBlueprint, gap: MarketGap) -> str:
    """
    Use the blueprint startup idea as the title base; append a primary pain
    term when available for specificity.
    """
    if gap.pain_terms:
        pain = gap.pain_terms[0].replace("-", " ").title()
        # Only append if it adds signal and doesn't make it redundant
        base = blueprint.startup_idea
        if pain.lower() not in base.lower():
            return f"{base} — {pain} Focus"
    return blueprint.startup_idea


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_founder_ideas(db: Session) -> list[FounderIdea]:
    """
    Detect market gaps, then transform each into a ``FounderIdea`` brief.
    Results are sorted by ``opportunity_score`` descending.
    """
    gaps: list[MarketGap] = detect_market_gaps(db)
    ideas: list[FounderIdea] = []

    for rank_index, gap in enumerate(gaps):
        blueprint = _select_blueprint(gap.slug, rank_index)
        confidence = _compute_confidence(gap)
        build_diff = _build_difficulty_adjustment(blueprint.build_difficulty, gap)
        title = _build_title(blueprint, gap)

        ideas.append(
            FounderIdea(
                title=title,
                category=gap.category,
                opportunity_score=gap.opportunity_score,
                startup_idea=blueprint.startup_idea,
                target_customer=blueprint.target_customer,
                problem_statement=blueprint.problem_statement,
                mvp_features=list(blueprint.mvp_features),
                pricing_model=blueprint.pricing_model,
                revenue_model=blueprint.revenue_model,
                go_to_market=blueprint.go_to_market,
                competition_level=_competition_label(gap.competition_score),
                build_difficulty=build_diff,
                estimated_time_to_mvp=blueprint.estimated_time_to_mvp,
                confidence=confidence,
            )
        )

    # Already sorted by detect_market_gaps but re-sort defensively
    ideas.sort(key=lambda i: i.opportunity_score, reverse=True)
    return ideas
