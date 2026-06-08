from __future__ import annotations

from dataclasses import dataclass

from classification.classifier import MarketClassifier
from collectors.collector_manager import collect_all_sources
from config import get_runtime_settings
from database.crud import (
    add_collector_run,
    add_market_data_point,
    create_or_update_repository,
    create_pipeline_run,
    finish_pipeline_run,
    get_category_by_slug,
    seed_categories,
)
from database.db import SessionLocal, engine
from database.migrations import run_migrations
from intelligence.normalization import normalize_signal
from intelligence.trend_engine import compute_trends
from intelligence.types import CollectorBatch, NormalizedSignal
from opportunities.opportunity_engine import generate_opportunities
from reports.report_engine import generate_weekly_report


@dataclass(frozen=True)
class PipelineResult:
    status: str
    records_collected: int
    records_saved: int
    messages: list[str]


def run_pipeline(settings: dict | None = None, include_reports: bool = True) -> PipelineResult:
    run_migrations(engine)
    db = SessionLocal()
    pipeline_run = None
    records_collected = 0
    records_saved = 0
    messages: list[str] = []

    try:
        seed_categories(db)
        pipeline_run = create_pipeline_run(db)
        batches = collect_all_sources(settings or get_runtime_settings())
        classifier = MarketClassifier()

        for batch in batches:
            saved = _persist_batch(db, batch, classifier)
            records_collected += len(batch.records)
            records_saved += saved
            add_collector_run(
                db=db,
                pipeline_run_id=pipeline_run.id,
                source=batch.source,
                status=batch.status,
                started_at=batch.started_at,
                finished_at=batch.finished_at,
                records_collected=len(batch.records),
                records_saved=saved,
                message=batch.message,
            )
            if batch.status != "success":
                messages.append(f"{batch.source}: {batch.status} - {batch.message}")

        compute_trends(db)
        generate_opportunities(db)
        if include_reports:
            generate_weekly_report(db)

        status = "success" if not any(message for message in messages if "failed" in message) else "partial"
        finish_pipeline_run(
            db,
            pipeline_run,
            status=status,
            records_collected=records_collected,
            records_saved=records_saved,
            message="Pipeline completed." if not messages else "Pipeline completed with source issues.",
            errors=messages,
        )
        return PipelineResult(status, records_collected, records_saved, messages)
    except Exception as exc:
        messages.append(str(exc))
        if pipeline_run:
            finish_pipeline_run(
                db,
                pipeline_run,
                status="failed",
                records_collected=records_collected,
                records_saved=records_saved,
                message="Pipeline failed.",
                errors=messages,
            )
        raise
    finally:
        db.close()


def collect_and_persist_signals(settings: dict | None = None) -> PipelineResult:
    run_migrations(engine)
    db = SessionLocal()
    try:
        seed_categories(db)
        classifier = MarketClassifier()
        records_collected = 0
        records_saved = 0
        messages: list[str] = []
        for batch in collect_all_sources(settings or get_runtime_settings()):
            saved = _persist_batch(db, batch, classifier)
            records_collected += len(batch.records)
            records_saved += saved
            add_collector_run(
                db=db,
                source=batch.source,
                status=batch.status,
                records_collected=len(batch.records),
                records_saved=saved,
                message=batch.message,
                started_at=batch.started_at,
                finished_at=batch.finished_at,
            )
            if batch.status != "success":
                messages.append(f"{batch.source}: {batch.status} - {batch.message}")
        return PipelineResult("success", records_collected, records_saved, messages)
    finally:
        db.close()


def _persist_batch(db, batch: CollectorBatch, classifier: MarketClassifier) -> int:
    saved = 0
    for raw in batch.records:
        signal = normalize_signal(raw, classifier)
        if _persist_signal(db, signal):
            saved += 1
    return saved


def _persist_signal(db, signal: NormalizedSignal) -> bool:
    category = get_category_by_slug(db, signal.category_slug)
    category_id = category.id if category else None
    add_market_data_point(
        db=db,
        source=signal.source,
        external_id=signal.external_id,
        title=signal.title,
        description=signal.description,
        url=signal.url,
        engagement_score=signal.engagement_score,
        published_at=signal.published_at,
        category_id=category_id,
        normalized_text=signal.normalized_text,
        classification_confidence=signal.classification_confidence,
        classification_evidence=signal.classification_evidence,
        raw_payload=signal.raw_payload,
    )
    if signal.source == "github" and category_id:
        _persist_repository(db, signal, category_id)
    return True


def _persist_repository(db, signal: NormalizedSignal, category_id: int) -> None:
    payload = signal.raw_payload
    create_or_update_repository(
        db=db,
        name=str(payload.get("name") or signal.title.split("/")[-1]),
        full_name=str(payload.get("full_name") or signal.external_id),
        url=signal.url,
        description=signal.description,
        stars=signal.engagement_score,
        forks=int(payload.get("forks") or 0),
        language=str(payload.get("language") or "Other"),
        category_id=category_id,
    )


if __name__ == "__main__":
    result = run_pipeline()
    print(result)
