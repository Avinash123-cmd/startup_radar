"""
Repository Comparison Engine
GET /compare?repos=owner/repo,owner/repo,...

Fetches the requested repositories from the database, computes a momentum score
for each using the mandated formula, ranks them, and returns a structured
comparison payload with a declared winner.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.crud import get_repository_by_fullname
from database.db import get_db
from database.models import Repository, RepositorySnapshot

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_REPOS: int = 10          # Guard against excessively large comparisons
MIN_REPOS: int = 2           # Comparison requires at least two subjects
MOMENTUM_CAP: float = 100.0  # Hard ceiling on momentum score
SNAPSHOT_LOOKBACK_DAYS: int = 30


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------

class SnapshotPoint(BaseModel):
    """Lightweight representation of a historical star snapshot."""
    stars: int
    recorded_at: datetime

    class Config:
        from_attributes = True


class ComparedRepository(BaseModel):
    """Single repository entry inside the comparison payload."""

    rank: int = Field(..., description="1-based rank by momentum (1 = highest)")
    full_name: str
    name: str
    url: str
    description: Optional[str] = None
    language: Optional[str] = None
    category: str = Field(..., description="Category name the repo belongs to")
    stars: int
    forks: int
    star_growth_30d: int = Field(
        ..., description="Stars gained over the last 30 days (snapshot-derived)"
    )
    momentum_score: float = Field(
        ...,
        description=(
            "Composite score: (star_growth_30d × 0.5) + (log(stars+1) × 10) "
            "+ (forks × 0.01), capped at 100"
        ),
    )
    snapshot_history: List[SnapshotPoint] = Field(
        default_factory=list,
        description="Up to 30 historical star snapshots used for growth calculation",
    )


class CompareResponse(BaseModel):
    """Top-level response envelope for the comparison endpoint."""

    winner: str = Field(..., description="full_name of the highest-momentum repository")
    total_compared: int
    repositories: List[ComparedRepository]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fetch_snapshots_30d(db: Session, repo_id: int) -> List[RepositorySnapshot]:
    """Return all snapshots recorded within the last 30 days, oldest-first."""
    cutoff = datetime.utcnow() - timedelta(days=SNAPSHOT_LOOKBACK_DAYS)
    return (
        db.query(RepositorySnapshot)
        .filter(
            RepositorySnapshot.repository_id == repo_id,
            RepositorySnapshot.recorded_at >= cutoff,
        )
        .order_by(RepositorySnapshot.recorded_at.asc())
        .all()
    )


def _star_growth_from_snapshots(
    snapshots: List[RepositorySnapshot], current_stars: int
) -> int:
    """
    Derive 30-day star growth from snapshot history.

    Strategy:
    - If ≥ 2 snapshots exist: newest_stars − oldest_stars.
    - If exactly 1 snapshot: current_stars − that snapshot's stars.
    - If no snapshots: 0 (not enough history).
    """
    if len(snapshots) >= 2:
        return max(0, snapshots[-1].stars - snapshots[0].stars)
    if len(snapshots) == 1:
        return max(0, current_stars - snapshots[0].stars)
    return 0


def _compute_momentum(star_growth: int, stars: int, forks: int) -> float:
    """
    Momentum formula (spec-mandated):
        momentum = (star_growth × 0.5) + (log(stars + 1) × 10) + (forks × 0.01)

    Result is floored at 0 and capped at MOMENTUM_CAP (100).
    """
    raw = (star_growth * 0.5) + (math.log(stars + 1) * 10) + (forks * 0.01)
    return round(min(max(raw, 0.0), MOMENTUM_CAP), 4)


def _parse_repo_names(raw: str) -> List[str]:
    """
    Split and normalise the comma-separated `repos` query parameter.
    Strips whitespace; removes empty tokens; lower-cases for consistent lookup.
    Returns the original-case tokens (GitHub is case-insensitive but we store
    exact case in DB, so we preserve case and let the DB query handle it).
    """
    return [r.strip() for r in raw.split(",") if r.strip()]


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(tags=["Compare"])


@router.get(
    "/compare",
    response_model=CompareResponse,
    summary="Compare multiple repositories by momentum",
    description=(
        "Accepts a comma-separated list of GitHub `owner/repo` full names via the "
        "`repos` query parameter (min 2, max 10). Looks each repository up in the "
        "local database, derives 30-day star growth from `RepositorySnapshot` history, "
        "computes a momentum score, ranks by momentum descending, and returns a "
        "structured comparison with a declared winner."
    ),
)
def compare_repositories(
    repos: str = Query(
        ...,
        description=(
            "Comma-separated list of repository full names (owner/repo). "
            "Example: crewAIInc/crewAI,microsoft/autogen,browser-use/browser-use"
        ),
        min_length=3,
    ),
    db: Session = Depends(get_db),
) -> CompareResponse:

    # ── 1. Parse & validate the input ────────────────────────────────────────
    repo_names: List[str] = _parse_repo_names(repos)

    if len(repo_names) < MIN_REPOS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"At least {MIN_REPOS} repositories are required for a comparison. "
                f"Received: {len(repo_names)}."
            ),
        )

    if len(repo_names) > MAX_REPOS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Maximum {MAX_REPOS} repositories may be compared in a single request. "
                f"Received: {len(repo_names)}."
            ),
        )

    # Detect exact duplicates up-front so callers get a clear error.
    seen: set[str] = set()
    duplicates: List[str] = []
    for rn in repo_names:
        key = rn.lower()
        if key in seen:
            duplicates.append(rn)
        seen.add(key)

    if duplicates:
        raise HTTPException(
            status_code=422,
            detail=f"Duplicate repository names detected: {', '.join(duplicates)}",
        )

    # ── 2. Fetch each repository from the database ───────────────────────────
    found: List[Repository] = []
    not_found: List[str] = []

    for full_name in repo_names:
        repo = get_repository_by_fullname(db, full_name)
        if repo is None:
            not_found.append(full_name)
        else:
            found.append(repo)

    if not_found:
        raise HTTPException(
            status_code=404,
            detail=(
                f"The following repositories were not found in the database: "
                f"{', '.join(not_found)}. "
                "Ensure the pipeline has been run and the repository names are exact "
                "(case-sensitive, owner/repo format)."
            ),
        )

    # ── 3. Compute metrics for each repository ───────────────────────────────
    computed: List[ComparedRepository] = []

    for repo in found:
        snapshots = _fetch_snapshots_30d(db, repo.id)
        star_growth = _star_growth_from_snapshots(snapshots, repo.stars)
        momentum = _compute_momentum(star_growth, repo.stars, repo.forks)
        category_name = repo.category.name if repo.category else "Unknown"

        snapshot_points = [
            SnapshotPoint(stars=s.stars, recorded_at=s.recorded_at)
            for s in snapshots
        ]

        computed.append(
            ComparedRepository(
                rank=0,                   # Assigned after sorting
                full_name=repo.full_name,
                name=repo.name,
                url=repo.url,
                description=repo.description,
                language=repo.language,
                category=category_name,
                stars=repo.stars,
                forks=repo.forks,
                star_growth_30d=star_growth,
                momentum_score=momentum,
                snapshot_history=snapshot_points,
            )
        )

    # ── 4. Rank by momentum descending ───────────────────────────────────────
    computed.sort(key=lambda r: r.momentum_score, reverse=True)

    for position, entry in enumerate(computed, start=1):
        entry.rank = position

    # ── 5. Build and return response ─────────────────────────────────────────
    winner = computed[0].full_name  # Highest momentum after sort

    return CompareResponse(
        winner=winner,
        total_compared=len(computed),
        repositories=computed,
    )
