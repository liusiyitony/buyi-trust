"""
Buyi Trust Protocol — Database layer
SQLite for now, PostgreSQL-ready schema.
"""

import sqlite3
import os
from flask import g

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cert.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS certificates (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    cert_id    TEXT UNIQUE NOT NULL,
    cert_json  TEXT NOT NULL,
    provider_type TEXT NOT NULL,
    provider_id   TEXT NOT NULL,
    provider_name TEXT NOT NULL,
    category      TEXT NOT NULL,
    service_type  TEXT NOT NULL DEFAULT 'predictive',
    confidence    INTEGER DEFAULT 0,
    status        TEXT DEFAULT 'pending',
    value_score   REAL DEFAULT 0,
    created_at    TEXT NOT NULL,
    updated_at    TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_cert_provider ON certificates(provider_id);
CREATE INDEX IF NOT EXISTS idx_cert_status ON certificates(status);
CREATE INDEX IF NOT EXISTS idx_cert_category ON certificates(category);
CREATE INDEX IF NOT EXISTS idx_cert_created ON certificates(created_at);

CREATE TABLE IF NOT EXISTS verifications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cert_id         TEXT NOT NULL,
    accuracy        TEXT DEFAULT 'pending',
    value_score     INTEGER NOT NULL,
    emotional_tags  TEXT DEFAULT '[]',
    client_feedback TEXT DEFAULT '',
    verified_at     TEXT NOT NULL,
    eas_uid         TEXT DEFAULT '',
    FOREIGN KEY (cert_id) REFERENCES certificates(cert_id)
);

CREATE INDEX IF NOT EXISTS idx_verify_cert ON verifications(cert_id);
CREATE INDEX IF NOT EXISTS idx_verify_date ON verifications(verified_at);

CREATE TABLE IF NOT EXISTS daily_roots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT UNIQUE NOT NULL,
    merkle_root TEXT NOT NULL,
    cert_count  INTEGER NOT NULL,
    tx_hash     TEXT DEFAULT '',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_registry (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_name TEXT UNIQUE NOT NULL,
    schema_uid  TEXT DEFAULT '',
    chain       TEXT DEFAULT 'base',
    tx_hash     TEXT DEFAULT '',
    registered_at TEXT DEFAULT ''
);
"""


def get_db() -> sqlite3.Connection:
    """Get or create database connection."""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


def init_db():
    """Initialize database schema."""
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {DB_PATH}")


def close_db(e=None):
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ── Query helpers ───────────────────────────────────────────────────
def get_pending_verifications(days_ago: int = 30) -> list[dict]:
    """Get certificates that need verification reminders."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute("""
        SELECT cert_id, cert_json, created_at
        FROM certificates
        WHERE status = 'pending'
          AND created_at <= datetime('now', ?)
        ORDER BY created_at DESC
    """, (f'-{days_ago} days',)).fetchall()
    
    conn.close()
    return [dict(r) for r in rows]


def get_today_certificates() -> list[dict]:
    """Get all certificates created today for batch timestamping."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute("""
        SELECT cert_json FROM certificates
        WHERE date(created_at) = date('now')
    """).fetchall()
    
    conn.close()
    return [dict(r) for r in rows]


def save_daily_root(date: str, merkle_root: str, cert_count: int, tx_hash: str = ""):
    """Save daily Merkle root record."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT OR REPLACE INTO daily_roots (date, merkle_root, cert_count, tx_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (date, merkle_root, cert_count, tx_hash, now))
    conn.commit()
    conn.close()
