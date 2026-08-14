# IELTS Chapter 2 — Food Core Shadowing Passages API

A small FastAPI + SQLite service that serves IELTS core shadowing
passages (Chapter 2: Food) and their sectioned retelling content.

The passages are organised by theme (e.g. "Daily Meals, Fruit and
Vegetables"). Each passage is one of two types (`A`/`B`) and is split
into ordered, sentence-level sections used for shadowing practice.

## Quick start

```bash
# 1. Create the virtualenv and install dependencies
uv sync

# 2. Create the SQLite database (schema + seed data)
uv run python db/setup_db.py

# 3. Start the API
uv run uvicorn src.project.api:app --reload
```

The API is then available at <http://127.0.0.1:8000>, with interactive
docs at <http://127.0.0.1:8000/docs>.

## Configuration

| Env var    | Default              | Description                              |
| ---------- | -------------------- | ---------------------------------------- |
| `DB_PATH`  | `db/project.db`      | Path to the SQLite database file.        |

## Project layout

```
├── db/
│   ├── schema.sql          # SQLite schema (themes, passages, passage_sections)
│   ├── seed.sql            # Seed data (1 theme, passage A, 6 sections)
│   ├── setup_db.py         # Creates db/project.db from schema + seed
│   └── project.db          # Generated database (not committed)
├── src/project/
│   ├── api.py              # FastAPI application and endpoints
│   └── __init__.py
├── tests/
│   └── test_api.py         # Endpoint tests (pytest)
├── docs/
│   ├── schema.md           # Database schema documentation
│   └── api.md              # API reference
├── food.md                 # Source content used for seed data
├── pyproject.toml
└── README.md
```

## Database

SQLite database with three tables: `themes`, `passages` and
`passage_sections`. See [docs/schema.md](docs/schema.md) for the full
schema and [db/schema.sql](db/schema.sql) for the DDL.

## API overview

| Method | Path                          | Description                          |
| ------ | ----------------------------- | ------------------------------------ |
| GET    | `/health`                     | Liveness check                       |
| GET    | `/themes`                     | List all themes                      |
| GET    | `/themes/{theme_id}`          | Theme detail with its passages       |
| GET    | `/passages`                   | List passages (filter by theme/type) |
| GET    | `/passages/{passage_id}`      | Passage detail with sections         |
| GET    | `/passages/{passage_id}/sections` | Passage sections (ordered)       |

See [docs/api.md](docs/api.md) for the full reference.

## Tests

```bash
uv run pytest
```
