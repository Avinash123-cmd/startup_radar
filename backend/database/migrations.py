from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from database.models import Base

MIGRATION_VERSION = "20260608_production_refactor"
WATCHLIST_MIGRATION_VERSION = "20260609_watchlist_intelligence"


def run_migrations(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        _ensure_schema_migrations(conn)
        applied = {
            row[0]
            for row in conn.execute(text("SELECT version FROM schema_migrations")).fetchall()
        }
        # Run core migrations
        if MIGRATION_VERSION not in applied:
            inspector = inspect(conn)
            tables = set(inspector.get_table_names())

            if "market_data_points" in tables:
                _ensure_columns(
                    conn,
                    "market_data_points",
                    {
                        "normalized_text": "TEXT",
                        "classification_confidence": "FLOAT DEFAULT 0.0",
                        "classification_evidence": "TEXT",
                        "raw_payload": "TEXT",
                        "updated_at": "DATETIME",
                    },
                )

            if "trend_history" in tables:
                _ensure_columns(
                    conn,
                    "trend_history",
                    {
                        "source_breakdown": "TEXT",
                        "score_components": "TEXT",
                    },
                )

            if "opportunities" in tables:
                _ensure_columns(
                    conn,
                    "opportunities",
                    {
                        "evidence": "TEXT",
                        "gap_score": "FLOAT DEFAULT 0.0",
                        "score_components": "TEXT",
                    },
                )

            if "weekly_reports" in tables:
                _ensure_columns(conn, "weekly_reports", {"context_snapshot": "TEXT"})

            _migrate_product_hunt_products(conn, tables)
            conn.execute(
                text("INSERT INTO schema_migrations (version, applied_at) VALUES (:version, :applied_at)"),
                {"version": MIGRATION_VERSION, "applied_at": datetime.utcnow()},
            )

        # Run watchlist migrations
        if WATCHLIST_MIGRATION_VERSION not in applied:
            _ensure_watchlist_tables(conn)
            conn.execute(
                text("INSERT INTO schema_migrations (version, applied_at) VALUES (:version, :applied_at)"),
                {"version": WATCHLIST_MIGRATION_VERSION, "applied_at": datetime.utcnow()},
            )


def _ensure_schema_migrations(conn) -> None:
    is_pg = conn.dialect.name == "postgresql"
    datetime_type = "TIMESTAMP" if is_pg else "DATETIME"
    conn.execute(
        text(
            f"CREATE TABLE IF NOT EXISTS schema_migrations ("
            f"version VARCHAR(255) PRIMARY KEY, "
            f"applied_at {datetime_type} NOT NULL)"
        )
    )


def _ensure_columns(conn, table_name: str, columns: dict[str, str]) -> None:
    existing = {column["name"] for column in inspect(conn).get_columns(table_name)}
    for name, ddl_type in columns.items():
        if name not in existing:
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {name} {_dialect_type(conn, ddl_type)}"))


def _dialect_type(conn, ddl_type: str) -> str:
    if conn.dialect.name == "postgresql":
        return ddl_type.replace("DATETIME", "TIMESTAMP")
    return ddl_type


def _migrate_product_hunt_products(conn, tables: set[str]) -> None:
    if "product_hunt_products" not in tables or "market_data_points" not in tables:
        return

    rows = conn.execute(
        text(
            "SELECT ph_id, name, tagline, description, votes_count, comments_count, "
            "website_url, ph_url, topics, makers, launch_date, category_id "
            "FROM product_hunt_products"
        )
    ).mappings().all()

    for row in rows:
        exists = conn.execute(
            text(
                "SELECT 1 FROM market_data_points "
                "WHERE source = 'product_hunt' AND external_id = :external_id"
            ),
            {"external_id": row["ph_id"]},
        ).first()
        if exists:
            continue

        title = f"[Product Hunt] {row['name']}"
        description_parts = [
            row["tagline"] or "",
            row["description"] or "",
            f"Votes: {row['votes_count'] or 0}; Comments: {row['comments_count'] or 0}.",
        ]
        payload = {
            "topics": _loads(row["topics"]),
            "makers": _loads(row["makers"]),
            "website_url": row["website_url"],
            "ph_url": row["ph_url"],
        }
        conn.execute(
            text(
                "INSERT INTO market_data_points "
                "(source, external_id, title, description, url, engagement_score, published_at, "
                "category_id, normalized_text, classification_confidence, classification_evidence, raw_payload, created_at, updated_at) "
                "VALUES "
                "('product_hunt', :external_id, :title, :description, :url, :engagement_score, :published_at, "
                ":category_id, :normalized_text, 0.0, '[]', :raw_payload, :created_at, :updated_at)"
            ),
            {
                "external_id": row["ph_id"],
                "title": title,
                "description": " ".join(part for part in description_parts if part),
                "url": row["ph_url"] or row["website_url"] or "https://www.producthunt.com",
                "engagement_score": int(row["votes_count"] or 0),
                "published_at": row["launch_date"],
                "category_id": row["category_id"],
                "normalized_text": f"{title} {row['tagline'] or ''} {row['description'] or ''}".strip(),
                "raw_payload": json.dumps(payload),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
        )

    conn.execute(text("DROP TABLE product_hunt_products"))


def _loads(value: str | None):
    if not value:
        return []
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return []


def _ensure_watchlist_tables(conn) -> None:
    inspector = inspect(conn)
    existing_tables = set(inspector.get_table_names())

    is_pg = conn.dialect.name == "postgresql"
    id_type = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    datetime_type = "TIMESTAMP" if is_pg else "DATETIME"

    if "watchlists" not in existing_tables:
        conn.execute(text(
            f"CREATE TABLE watchlists ("
            f"id {id_type}, "
            f"name VARCHAR(100) NOT NULL, "
            f"description TEXT, "
            f"is_active INTEGER DEFAULT 1, "
            f"created_at {datetime_type} NOT NULL)"
        ))

    if "watchlist_categories" not in existing_tables:
        conn.execute(text(
            f"CREATE TABLE watchlist_categories ("
            f"id {id_type}, "
            f"watchlist_id INTEGER NOT NULL, "
            f"category_id INTEGER NOT NULL, "
            f"created_at {datetime_type} NOT NULL, "
            f"FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE, "
            f"FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE)"
        ))

    if "watchlist_repositories" not in existing_tables:
        conn.execute(text(
            f"CREATE TABLE watchlist_repositories ("
            f"id {id_type}, "
            f"watchlist_id INTEGER NOT NULL, "
            f"repository_id INTEGER NOT NULL, "
            f"created_at {datetime_type} NOT NULL, "
            f"FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE, "
            f"FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE)"
        ))

    if "alerts" not in existing_tables:
        conn.execute(text(
            f"CREATE TABLE alerts ("
            f"id {id_type}, "
            f"watchlist_id INTEGER NOT NULL, "
            f"severity VARCHAR(20) NOT NULL, "
            f"alert_type VARCHAR(50) NOT NULL, "
            f"category_id INTEGER, "
            f"repository_id INTEGER, "
            f"title VARCHAR(255) NOT NULL, "
            f"message TEXT NOT NULL, "
            f"previous_value FLOAT, "
            f"current_value FLOAT, "
            f"change_percent FLOAT, "
            f"is_read INTEGER DEFAULT 0, "
            f"created_at {datetime_type} NOT NULL, "
            f"FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE, "
            f"FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL, "
            f"FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE SET NULL)"
        ))
