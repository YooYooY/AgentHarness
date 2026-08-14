"""REST API endpoints for the project.

Provides read-only REST endpoints over the SQLite database described in
db/schema.sql. The database file is taken from the ``DB_PATH`` environment
variable, defaulting to ``db/project.db`` relative to the project root.

Endpoints:
    GET /health                      -> service health check
    GET /themes                      -> list all themes
    GET /themes/{theme_id}           -> theme detail incl. its passages
    GET /passages                    -> list passages (?theme_id=, ?passage_type=)
    GET /passages/{passage_id}       -> passage detail incl. sections
    GET /passages/{passage_id}/sections -> shadowing sections of a passage
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "db" / "project.db"

app = FastAPI(
    title="Project API",
    description="REST API over the project database (food/IELTS core passages).",
    version="0.1.0",
)


def get_db_path() -> Path:
    return Path(os.environ.get("DB_PATH", str(DEFAULT_DB_PATH))).resolve()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _loads_json(value: Any) -> Any:
    """Parse a JSON column value, returning [] for NULL/empty values."""
    if value is None:
        return []
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []


def _theme_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "slug": row["slug"],
        "name": row["name"],
        "sort_order": row["sort_order"],
    }


def _passage_row(row: sqlite3.Row, include_sections: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": row["id"],
        "theme_id": row["theme_id"],
        "passage_type": row["passage_type"],
        "title": row["title"],
        "content": row["content"],
        "core_chunks": _loads_json(row["core_chunks"]),
        "retelling_map": _loads_json(row["retelling_map"]),
        "output_ladder": _loads_json(row["output_ladder"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    if include_sections:
        data["sections"] = [
            {
                "id": s["id"],
                "section_order": s["section_order"],
                "text": s["text"],
            }
            for s in row["sections"]
        ]
    return data


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}


@app.get("/themes", tags=["themes"])
def list_themes() -> list[dict[str, Any]]:
    """List all themes, ordered by sort_order."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, slug, name, sort_order FROM themes ORDER BY sort_order, id"
        ).fetchall()
    return [_theme_row(r) for r in rows]


@app.get("/themes/{theme_id}", tags=["themes"])
def get_theme(theme_id: int) -> dict[str, Any]:
    """Return a theme together with its passages."""
    with get_connection() as conn:
        theme = conn.execute(
            "SELECT id, slug, name, sort_order FROM themes WHERE id = ?",
            (theme_id,),
        ).fetchone()
        if theme is None:
            raise HTTPException(status_code=404, detail="Theme not found")
        passage_rows = conn.execute(
            "SELECT * FROM passages WHERE theme_id = ? ORDER BY passage_type, id",
            (theme_id,),
        ).fetchall()
    result = _theme_row(theme)
    result["passages"] = [_passage_row(r) for r in passage_rows]
    return result


@app.get("/passages", tags=["passages"])
def list_passages(
    theme_id: int | None = Query(default=None),
    passage_type: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    """List passages, optionally filtered by theme_id and/or passage_type."""
    sql = "SELECT * FROM passages WHERE 1 = 1"
    params: list[Any] = []
    if theme_id is not None:
        sql += " AND theme_id = ?"
        params.append(theme_id)
    if passage_type is not None:
        if passage_type not in ("A", "B"):
            raise HTTPException(
                status_code=422, detail="passage_type must be 'A' or 'B'"
            )
        sql += " AND passage_type = ?"
        params.append(passage_type)
    sql += " ORDER BY theme_id, passage_type, id"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_passage_row(r) for r in rows]


@app.get("/passages/{passage_id}", tags=["passages"])
def get_passage(passage_id: int) -> dict[str, Any]:
    """Return a passage including its shadowing sections."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM passages WHERE id = ?", (passage_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Passage not found")
        sections = conn.execute(
            "SELECT id, section_order, text FROM passage_sections "
            "WHERE passage_id = ? ORDER BY section_order",
            (passage_id,),
        ).fetchall()
    return _passage_row({**row, "sections": sections}, include_sections=True)


@app.get("/passages/{passage_id}/sections", tags=["passages"])
def get_passage_sections(passage_id: int) -> list[dict[str, Any]]:
    """Return the ordered shadowing sections of a passage."""
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM passages WHERE id = ?", (passage_id,)
        ).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail="Passage not found")
        rows = conn.execute(
            "SELECT id, section_order, text FROM passage_sections "
            "WHERE passage_id = ? ORDER BY section_order",
            (passage_id,),
        ).fetchall()
    return [
        {"id": r["id"], "section_order": r["section_order"], "text": r["text"]}
        for r in rows
    ]
