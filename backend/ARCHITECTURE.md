# AI Startup Radar Architecture

## Current Compatibility Surface

The frontend calls these FastAPI contracts and they must remain stable:

- `GET /trends`
- `GET /trends/{slug}/history`
- `GET /predictions`
- `GET /opportunities`
- `GET /insights`
- `GET /repositories`
- `GET /repositories/{repo_id}/history`
- `GET /repositories/languages`
- `GET /reports`
- `GET /reports/{slug}`
- `GET /settings`, `POST /settings`, `POST /settings/sync`, `POST /settings/reset`

## Target Pipeline

Collectors -> normalization -> classification -> intelligence/trend scoring -> forecasting -> market-gap detection -> opportunities -> reports -> API compatibility layer.

`backend.pipeline.run_pipeline` is the single orchestration entrypoint used by app startup, the scheduler, and manual sync.

## Dependency Graph Before Refactor

- `main.py` registered the active routers and called `collector_manager`, `trend_analyzer`, `opportunity_generator`, and `insights_generator`.
- `scheduler.py` duplicated the same pipeline sequence.
- `api.predictions` computed fixed prediction probabilities directly in the route.
- `api.insights` used hardcoded fallback insight text.
- `processor.trend_analyzer`, `processor.opportunity_generator`, and `processor.insights_generator` each owned separate formulas or templates.
- `collectors.reddit_collector`, `collectors.arxiv_collector`, and `collectors.hn_collector` each embedded classification heuristics.

## Findings

- Mock/fake data paths existed in all collectors, including Product Hunt always generating synthetic records.
- Hardcoded opportunity copy and report markdown were stored in processor modules.
- Momentum, demand, competition, confidence, and forecast probability were calculated in multiple places.
- Legacy JSON telemetry scripts read and wrote `database/history.json` and `database/category_history.json`.
- `growth.py`, `rankings.py`, `smart_opportunities.py`, `founder_ideas.py`, and `investor_report.py` were not used by the frontend or registered app.
- SQLite contained an orphan `product_hunt_products` table without an active SQLAlchemy model.
- `settings.json` contained API credentials; production settings now use environment variables for secrets.

## Migration Strategy

The migration is additive first: existing API tables and response models remain readable while pipeline status, classification evidence, and normalized signal fields are introduced. Legacy JSON telemetry and mock paths are removed after the database-backed engines are active.
