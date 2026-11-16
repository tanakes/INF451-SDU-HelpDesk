"""Database layer - persistent storage.

Uses Postgres/Neon when DATABASE_URL is set; otherwise falls back to JSON files
under DATA_DIR (default: ./data). On Render, local files are ephemeral unless a
persistent disk is mounted and DATA_DIR points to it.
"""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATABASE_URL = (os.environ.get("DATABASE_URL") or "").strip()

_use_db = False
_psycopg = None
if DATABASE_URL:
    try:
        import psycopg as _psycopg_mod  # type: ignore

        _psycopg = _psycopg_mod
        _use_db = True
    except Exception:
        _psycopg = None
        _use_db = False


def _path(name: str) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, name)


def _load(name: str) -> list:
    p = _path(name)
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return []


def _save(name: str, rows: list) -> None:
    p = _path(name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)


@contextmanager
def tx():
    yield None


def _db_exec(query: str, params: tuple = (), fetch: str | None = None):
    if not _use_db or _psycopg is None:
        raise RuntimeError("database not configured")
    conn = _psycopg.connect(DATABASE_URL)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if fetch == "one":
                    return cur.fetchone()
                if fetch == "all":
                    return cur.fetchall()
                return None
    finally:
        conn.close()


def init_schema() -> None:
    if _use_db:
        try:
            _db_exec(
                """
                CREATE TABLE IF NOT EXISTS query_log (
                    id BIGSERIAL PRIMARY KEY,
                    timestamp_utc TEXT,
                    category TEXT,
                    language TEXT,
                    outcome TEXT,
                    summary TEXT
                )
                """
            )
            _db_exec(
                """
                CREATE TABLE IF NOT EXISTS student_profiles (
                    user_id TEXT PRIMARY KEY,
                    degree TEXT,
                    year INTEGER,
                    major TEXT,
                    raw_text TEXT,
                    updated_at_utc TEXT
                )
                """
            )
            _db_exec(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    sender TEXT,
                    context TEXT,
                    created_at TEXT,
                    session_id TEXT,
                    status TEXT,
                    resolution_message TEXT
                )
                """
            )
            _db_exec(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    sender TEXT,
                    channel TEXT,
                    last_active_utc TEXT
                )
                """
            )
            _db_exec(
                """
                CREATE TABLE IF NOT EXISTS session_transcripts (
                    id BIGSERIAL PRIMARY KEY,
                    session_id TEXT,
                    timestamp_utc TEXT,
                    user_msg TEXT,
                    bot_reply TEXT
                )
                """
            )
            _db_exec(
                """
                CREATE TABLE IF NOT EXISTS user_state (
                    user_id TEXT PRIMARY KEY,
                    state_json TEXT
                )
                """
            )
            return
        except Exception:
            pass

    os.makedirs(DATA_DIR, exist_ok=True)
    for name in ["query_log.json", "student_profiles.json", "tickets.json", "sessions.json", "user_state.json"]:
        if not os.path.exists(_path(name)):
            _save(name, [])


def log_query(timestamp_utc: str, category: str, language: str, outcome: str, summary: str):
    if _use_db:
        try:
            _db_exec(
                "INSERT INTO query_log (timestamp_utc, category, language, outcome, summary) VALUES (%s,%s,%s,%s,%s)",
                (timestamp_utc, category, language, outcome, summary),
            )
            return
        except Exception:
            pass
    rows = _load("query_log.json")
    rows.append({
        "timestamp_utc": timestamp_utc,
        "category": category,
        "language": language,
        "outcome": outcome,
        "summary": summary,
    })
    _save("query_log.json", rows)


def get_profile(user_id: str) -> Optional[dict]:
    if _use_db:
        try:
            row = _db_exec(
                "SELECT user_id, degree, year, major, raw_text, updated_at_utc FROM student_profiles WHERE user_id=%s",
                (str(user_id),),
                fetch="one",
            )
            if not row:
                return None
            return {
                "user_id": row[0], "degree": row[1], "year": row[2], "major": row[3],
                "raw_text": row[4], "updated_at_utc": row[5],
            }
        except Exception:
            pass
    rows = _load("student_profiles.json")
    for r in rows:
        if str(r.get("user_id")) == str(user_id):
            return r
    return None


def save_profile(user_id: str, degree: str, year, major: str, raw_text: str, updated_at_utc: str):
    if _use_db:
        try:
            _db_exec(
                """
                INSERT INTO student_profiles (user_id, degree, year, major, raw_text, updated_at_utc)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (user_id) DO UPDATE SET
                    degree=EXCLUDED.degree, year=EXCLUDED.year, major=EXCLUDED.major,
                    raw_text=EXCLUDED.raw_text, updated_at_utc=EXCLUDED.updated_at_utc
                """,
                (str(user_id), degree, year, major, raw_text, updated_at_utc),
            )
            return
        except Exception:
            pass
    rows = _load("student_profiles.json")
    rows = [r for r in rows if str(r.get("user_id")) != str(user_id)]
    rows.append({
        "user_id": str(user_id),
        "degree": degree,
        "year": year,
        "major": major,
        "raw_text": raw_text,
        "updated_at_utc": updated_at_utc,
    })
    _save("student_profiles.json", rows)


def create_ticket(ticket_id: str, user_id: str, sender: str, context: str, created_at: str, session_id: Optional[str]):
    if _use_db:
        try:
            _db_exec(
                """
                INSERT INTO tickets (ticket_id, user_id, sender, context, created_at, session_id, status, resolution_message)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (ticket_id, str(user_id), sender, context, created_at, session_id, "pending", None),
            )
            return
        except Exception:
            pass
    rows = _load("tickets.json")
    rows.append({
        "ticket_id": ticket_id,
        "user_id": str(user_id),
        "sender": sender,
        "context": context,
        "created_at": created_at,
        "session_id": session_id,
        "status": "pending",
        "resolution_message": None,
    })
    _save("tickets.json", rows)


def list_open_tickets() -> list[dict]:
    if _use_db:
        try:
            rows = _db_exec(
                "SELECT ticket_id, user_id, sender, context, created_at, session_id, status, resolution_message FROM tickets WHERE status=%s ORDER BY created_at DESC",
                ("pending",),
                fetch="all",
            ) or []
            return [{
                "ticket_id": r[0], "user_id": r[1], "sender": r[2], "context": r[3],
                "created_at": r[4], "session_id": r[5], "status": r[6], "resolution_message": r[7],
            } for r in rows]
        except Exception:
            pass
    rows = _load("tickets.json")
    return [r for r in rows if r.get("status") == "pending"]


def get_user_state(user_id: str) -> dict:
    if _use_db:
        try:
            row = _db_exec("SELECT state_json FROM user_state WHERE user_id=%s", (str(user_id),), fetch="one")
            if not row or not row[0]:
                return {}
            return json.loads(row[0])
        except Exception:
            pass
    rows = _load("user_state.json")
    for r in rows:
        if str(r.get("user_id")) == str(user_id):
            return r.get("state") or {}
    return {}


def set_user_state(user_id: str, state: dict):
    if _use_db:
        try:
            payload = json.dumps(state, ensure_ascii=False)
            _db_exec(
                """
                INSERT INTO user_state (user_id, state_json) VALUES (%s,%s)
                ON CONFLICT (user_id) DO UPDATE SET state_json=EXCLUDED.state_json
                """,
                (str(user_id), payload),
            )
            return
        except Exception:
            pass
    rows = _load("user_state.json")
    rows = [r for r in rows if str(r.get("user_id")) != str(user_id)]
    rows.append({"user_id": str(user_id), "state": state})
    _save("user_state.json", rows)


def clear_user_state(user_id: str):
    if _use_db:
        try:
            _db_exec("DELETE FROM user_state WHERE user_id=%s", (str(user_id),))
            return
        except Exception:
            pass
    rows = _load("user_state.json")
    rows = [r for r in rows if str(r.get("user_id")) != str(user_id)]
    _save("user_state.json", rows)


def save_session(session_id: str, sender: str, channel: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if _use_db:
        try:
            _db_exec(
                """
                INSERT INTO sessions (session_id, sender, channel, last_active_utc)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT (session_id) DO UPDATE SET
                    sender=EXCLUDED.sender, channel=EXCLUDED.channel, last_active_utc=EXCLUDED.last_active_utc
                """,
                (session_id, sender, channel, ts),
            )
            return
        except Exception:
            pass
    rows = _load("sessions.json")
    rows = [r for r in rows if r.get("session_id") != session_id]
    rows.append({
        "session_id": session_id,
        "sender": sender,
        "channel": channel,
        "last_active_utc": ts,
    })
    _save("sessions.json", rows)


def append_session_transcript(session_id: str, user_msg: str, bot_reply: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if _use_db:
        try:
            _db_exec(
                "INSERT INTO session_transcripts (session_id, timestamp_utc, user_msg, bot_reply) VALUES (%s,%s,%s,%s)",
                (session_id, ts, user_msg, bot_reply),
            )
            return
        except Exception:
            pass
    rows = _load(f"session_{session_id}.json")
    rows.append({
        "timestamp_utc": ts,
        "user": user_msg,
        "bot": bot_reply,
    })
    _save(f"session_{session_id}.json", rows)


def get_query_log_summary(limit_recent: int = 5) -> dict:
    summary = {
        "total": 0,
        "by_outcome": {},
        "by_category": {},
        "by_language": {},
        "recent": [],
    }
    rows = []
    if _use_db:
        try:
            all_rows = _db_exec(
                "SELECT timestamp_utc, category, language, outcome, summary FROM query_log ORDER BY id DESC",
                fetch="all",
            ) or []
            rows = [{
                "timestamp_utc": r[0], "category": r[1], "language": r[2], "outcome": r[3], "summary": r[4],
            } for r in all_rows]
        except Exception:
            rows = []
    if not rows:
        rows = list(reversed(_load("query_log.json")))
    summary["total"] = len(rows)
    for r in rows:
        outcome = r.get("outcome") or "unknown"
        category = r.get("category") or "Unknown"
        language = r.get("language") or "Unknown"
        summary["by_outcome"][outcome] = summary["by_outcome"].get(outcome, 0) + 1
        summary["by_category"][category] = summary["by_category"].get(category, 0) + 1
        summary["by_language"][language] = summary["by_language"].get(language, 0) + 1
    summary["recent"] = rows[: max(0, int(limit_recent))]
    return summary


def start_new_session(chat_id: str) -> str:
    state = get_user_state(chat_id)
    new_sid = f"tg-{chat_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    state["current_session_id"] = new_sid
    state.pop("awaiting_advisor_question", None)
    set_user_state(chat_id, state)
    return new_sid
