"""Database layer for Neon Postgres.

Creates and manages: query_log, student_profiles, tickets, sessions.
All tables mirror the flat-file state from the buda.im backup so history is preserved.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Optional

import psycopg
from psycopg.rows import dict_row


def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return psycopg.connect(database_url, row_factory=dict_row)


@contextmanager
def tx():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema():
    with tx() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS query_log (
                    id SERIAL PRIMARY KEY,
                    timestamp_utc TEXT NOT NULL,
                    category TEXT NOT NULL,
                    language TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    summary TEXT NOT NULL
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS student_profiles (
                    user_id TEXT PRIMARY KEY,
                    degree TEXT DEFAULT 'Bachelor',
                    year INTEGER,
                    major TEXT DEFAULT 'General',
                    raw_text TEXT,
                    updated_at_utc TEXT
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    context TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    session_id TEXT,
                    status TEXT DEFAULT 'pending',
                    resolution_message TEXT
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    sender TEXT NOT NULL,
                    channel TEXT DEFAULT 'Telegram',
                    last_active_utc TEXT,
                    transcript_file TEXT
                );
                """
            )


def log_query(timestamp_utc: str, category: str, language: str, outcome: str, summary: str):
    with tx() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO query_log (timestamp_utc, category, language, outcome, summary) VALUES (%s,%s,%s,%s,%s)",
                (timestamp_utc, category, language, outcome, summary),
            )


def get_profile(user_id: str) -> Optional[dict]:
    with tx() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM student_profiles WHERE user_id = %s", (user_id,))
            return cur.fetchone()


def save_profile(user_id: str, degree: str, year, major: str, raw_text: str, updated_at_utc: str):
    with tx() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO student_profiles (user_id, degree, year, major, raw_text, updated_at_utc)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (user_id) DO UPDATE SET
                    degree = EXCLUDED.degree,
                    year = EXCLUDED.year,
                    major = EXCLUDED.major,
                    raw_text = EXCLUDED.raw_text,
                    updated_at_utc = EXCLUDED.updated_at_utc
                """,
                (user_id, degree, year, major, raw_text, updated_at_utc),
            )


def create_ticket(ticket_id: str, user_id: str, sender: str, context: str, created_at: str, session_id: Optional[str]):
    with tx() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tickets (ticket_id, user_id, sender, context, created_at, session_id, status)
                VALUES (%s,%s,%s,%s,%s,%s,'pending')
                """,
                (ticket_id, user_id, sender, context, created_at, session_id),
            )


def list_open_tickets():
    with tx() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tickets WHERE status = 'pending' ORDER BY created_at")
            return cur.fetchall()
