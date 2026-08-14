"""Set up the SQLite database for the project.

Reads db/schema.sql and db/seed.sql and applies them to a SQLite database
file. The database file path defaults to db/project.db and can be overridden
with the DB_PATH environment variable or the --db-path CLI argument.

Usage:
    python db/setup_db.py [--db-path path/to.db] [--reset]
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent
SCHEMA_FILE = DB_DIR / "schema.sql"
SEED_FILE = DB_DIR / "seed.sql"
DEFAULT_DB_PATH = DB_DIR / "project.db"


def read_sql(path: Path) -> str:
    """Read a SQL file, stripping SQL comments for sqlite3.executescript."""
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        lines.append(line)
    return "\n".join(lines)


def setup_database(db_path: Path, reset: bool = False) -> None:
    """Create (and optionally reset) the database from schema + seed files."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if reset and db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(read_sql(SCHEMA_FILE))
        conn.executescript(read_sql(SEED_FILE))
        conn.commit()
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-path",
        default=os.environ.get("DB_PATH", str(DEFAULT_DB_PATH)),
        help="Path to the SQLite database file.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing database file before recreating it.",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path).expanduser().resolve()
    setup_database(db_path, reset=args.reset)
    print(f"Database ready: {db_path}")


if __name__ == "__main__":
    main()
