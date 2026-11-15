"""Database layer — file-based persistence.

Mirrors the Postgres schema but stores data in JSON files under data/.
No external database dependency needed for Render free tier.
"""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional, List

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


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


def _save(name: str, rows: list):
    p = _path(name)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)


@contextmanager
def tx():
    yield None


def init_schema():
    os.makedirs(DATA_DIR, exist_ok=True)
    for name in ["query_log.json", "student_profiles.json", "tickets.json", "sessions.json"]:
        if not os.path.exists(_path(name)):
            _save(name, [])


def log_query(timestamp_utc: str, category: str, language: str, outcome: str, summary: str):
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
    rows = _load("student_profiles.json")
    for r in rows:
        if r.get("user_id") == user_id:
            return r
    return None


def save_profile(user_id: str, degree: str, year, major: str, raw_text: str, updated_at_utc: str):
    rows = _load("student_profiles.json")
    rows = [r for r in rows if r.get("user_id") != user_id]
    rows.append({
        "user_id": user_id,
        "degree": degree,
        "year": year,
        "major": major,
        "raw_text": raw_text,
        "updated_at_utc": updated_at_utc,
    })
    _save("student_profiles.json", rows)


def create_ticket(ticket_id: str, user_id: str, sender: str, context: str, created_at: str, session_id: Optional[str]):
    rows = _load("tickets.json")
    rows.append({
        "ticket_id": ticket_id,
        "user_id": user_id,
        "sender": sender,
        "context": context,
        "created_at": created_at,
        "session_id": session_id,
        "status": "pending",
        "resolution_message": None,
    })
    _save("tickets.json", rows)


def list_open_tickets() -> List[dict]:
    rows = _load("tickets.json")
    return [r for r in rows if r.get("status") == "pending"]


def save_session(session_id: str, sender: str, channel: str):
    rows = _load("sessions.json")
    rows = [r for r in rows if r.get("session_id") != session_id]
    rows.append({
        "session_id": session_id,
        "sender": sender,
        "channel": channel,
        "last_active_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    })
    _save("sessions.json", rows)


def append_session_transcript(session_id: str, user_msg: str, bot_reply: str):
    transcript_path = _path(f"session_{session_id}.json")
    rows = _load(f"session_{session_id}.json")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows.append({
        "timestamp_utc": ts,
        "user": user_msg,
        "bot": bot_reply,
    })
    _save(f"session_{session_id}.json", rows)
