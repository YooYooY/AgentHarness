-- ============================================================================
-- Project: food / IELTS Chapter 2 — Food Core Shadowing Passages
-- Database: SQLite
-- File: db/schema.sql
-- Description: Database schema for the project, including tables and indexes.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- Table: themes
-- A top-level topic group that passages belong to (e.g. "Daily Meals").
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS themes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT    NOT NULL UNIQUE,          -- machine-readable identifier
    name        TEXT    NOT NULL,                 -- human-readable name
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ----------------------------------------------------------------------------
-- Table: passages
-- A single core passage, either "A" (everyday English) or "B" (IELTS English).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS passages (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    theme_id       INTEGER NOT NULL REFERENCES themes(id) ON DELETE CASCADE,
    passage_type   TEXT    NOT NULL CHECK (passage_type IN ('A', 'B')),
    title          TEXT    NOT NULL,
    content        TEXT    NOT NULL,              -- full core passage text
    core_chunks    TEXT    NOT NULL DEFAULT '[]', -- JSON array of chunks
    retelling_map  TEXT    NOT NULL DEFAULT '[]', -- JSON array (retelling order)
    output_ladder  TEXT    NOT NULL DEFAULT '[]', -- JSON array (output ladder)
    created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ----------------------------------------------------------------------------
-- Table: passage_sections
-- Marked shadowing sections within a passage, ordered for practice.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS passage_sections (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    passage_id   INTEGER NOT NULL REFERENCES passages(id) ON DELETE CASCADE,
    section_order INTEGER NOT NULL,               -- 1-based position in passage
    text         TEXT    NOT NULL,                -- section text to shadow
    UNIQUE (passage_id, section_order)
);

-- ----------------------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_passages_theme
    ON passages (theme_id);

CREATE INDEX IF NOT EXISTS idx_passages_type
    ON passages (passage_type);

CREATE INDEX IF NOT EXISTS idx_passages_theme_type
    ON passages (theme_id, passage_type);

CREATE INDEX IF NOT EXISTS idx_sections_passage_order
    ON passage_sections (passage_id, section_order);
