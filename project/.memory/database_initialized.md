---
name: database_initialized
description: SQLite database has been created with schema and seed data.
type: project
---

The project database is initialized at project/db/project.db. It has 3 tables (themes, passages, passage_sections) and 4 custom indexes (idx_passages_theme, idx_passages_theme_type, idx_passages_type, idx_sections_passage_order). Seed data was created from food.md and contains 1 theme, 1 passage, and 6 passage sections. Files created: project/db/seed.sql (3474 bytes) and project/db/setup_db.py (2027 bytes).
