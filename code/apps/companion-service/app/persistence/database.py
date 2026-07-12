"""SQLite connection and schema management."""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS settings (
    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id=1),
    initial_nudge_minutes INTEGER NOT NULL,
    repeat_nudge_minutes INTEGER NOT NULL,
    after_dismiss_cooldown_minutes INTEGER NOT NULL,
    after_accept_cooldown_minutes INTEGER NOT NULL,
    after_irritation_cooldown_minutes INTEGER NOT NULL,
    quiet_default_minutes INTEGER NOT NULL,
    interaction_intensity TEXT NOT NULL,
    visual_lead_in_seconds INTEGER NOT NULL,
    maximum_nudge_words INTEGER NOT NULL,
    wellness_nudges_enabled INTEGER NOT NULL,
    muted INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS focus_sessions (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL,
    initial_nudge_at TEXT,
    last_nudge_at TEXT,
    next_eligible_nudge_at TEXT,
    wellness_nudges_enabled INTEGER NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_focus_session
    ON focus_sessions(status) WHERE status='active';
CREATE TABLE IF NOT EXISTS nudge_events (
    id TEXT PRIMARY KEY,
    focus_session_id TEXT NOT NULL REFERENCES focus_sessions(id),
    created_at TEXT NOT NULL,
    policy_reason TEXT NOT NULL,
    threshold_minutes INTEGER NOT NULL,
    elapsed_minutes INTEGER NOT NULL,
    interaction_intensity TEXT NOT NULL,
    expression_name TEXT NOT NULL,
    gesture_name TEXT NOT NULL,
    outcome TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS deferrals (
    id TEXT PRIMARY KEY,
    nudge_event_id TEXT NOT NULL REFERENCES nudge_events(id),
    created_at TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS quiet_intervals (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)

    def connect(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA journal_mode=WAL")
        return c

    def initialize(self) -> None:
        with self.connect() as c:
            c.executescript(_SCHEMA)
