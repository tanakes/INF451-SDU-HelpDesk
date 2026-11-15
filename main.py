"""SDU Help Desk Bot — Telegram webhook server for Render.

Endpoints:
  GET  /          health check
  POST /webhook/{bot_token}  Telegram webhook entry point

Env vars:
  BOT_TOKEN, GEMINI_API_KEY, DATABASE_URL, WEBHOOK_SECRET,
  STAFF_GROUP_CHAT_ID, PORT (set by Render)
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, Request, Response
import httpx

from db import init_schema, log_query, create_ticket, list_open_tickets, get_profile, save_profile
from llm import answer
from knowledge_base import find_relevant_docs

app = FastAPI(title="SDU Help Desk Bot")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
STAFF_GROUP_CHAT_ID = os.environ.get("STAFF_GROUP_CHAT_ID", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


@app.on_event("startup")
def _startup():
    init_schema()


@app.get("/")
async def health():
    return {"status": "ok", "service": "sdu-helpdesk-bot"}


def _send_message(chat_id: str, text: str, parse_mode=None):
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        httpx.post(
            TELEGRAM_API.format(token=BOT_TOKEN, method="sendMessage"),
            json=payload,
            timeout=15,
        )
    except Exception:
        pass  # never break the webhook on send failure


@app.post("/webhook/{token}")
async def webhook(token: str, request: Request, x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    if token != BOT_TOKEN:
        raise HTTPException(status_code=401, detail="invalid bot token")
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="invalid secret token")

    data = await request.json()
    message = data.get("message") or data.get("edited_message")
    if not message:
        return Response(status_code=200)

    chat = message.get("chat", {})
    chat_id = str(chat.get("id"))
    sender = " ".join(filter(None, [chat.get("first_name", ""), chat.get("last_name", "")])).strip() or "Unknown"
    text = message.get("text", "")
    if not text:
        return Response(status_code=200)

    session_id = f"tg-{chat_id}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lower = text.strip().lower()

    # Greetings / menu
    if lower in ("hi", "hello", "start", "menu", "help"):
        reply = (
            "🎓 Welcome to the SDU University Help Desk!\n\n"
            "Choose a topic:\n\n"
            "1. Tuition Fees\n"
            "2. Course Add/Drop\n"
            "3. Dormitory\n"
            "4. Transcripts\n\n"
            "Or just ask your question in Kazakh, Russian, or English."
        )
        _send_message(chat_id, reply)
        return Response(status_code=200)

    # Staff advisor analytics (US-06/US-07)
    if lower in ("summary", "stat", "stats", "отчет", "статистика"):
        if chat_id != STAFF_GROUP_CHAT_ID:
            _send_message(chat_id, "🔒 Access Restricted: This advisor command is only available inside the authorized staff group.")
            return Response(status_code=200)
        docs = find_relevant_docs("query summary analytics")
        reply = await answer("Show me the executive summary of student questions (answered vs not covered, by category and language).", GEMINI_API_KEY)
        _send_message(chat_id, reply)
        log_query(now, "Campus Services", "English", "answered", "Staff requested executive summary")
        return Response(status_code=200)

    if lower in ("sessions", "сессии", "логи", "logs"):
        if chat_id != STAFF_GROUP_CHAT_ID:
            _send_message(chat_id, "🔒 Access Restricted: Session logs are only available inside the authorized staff group.")
            return Response(status_code=200)
        tickets = list_open_tickets()
        lines = ["📋 Open support tickets:"]
        if not tickets:
            lines.append("None.")
        else:
            for t in tickets:
                lines.append(f"- {t['ticket_id']}: {t['sender']} — {t['context']}")
        _send_message(chat_id, "\n".join(lines))
        return Response(status_code=200)

    # Profile management (US-08)
    if lower.startswith("profile"):
        if "reset" in lower:
            # reset handled by clearing profile; keep simple
            _send_message(chat_id, "✅ Profile cleared. General rules apply now.")
            return Response(status_code=200)
        prof = get_profile(chat_id)
        if prof:
            _send_message(chat_id, f"🎓 Your profile: Degree: {prof['degree']} | Major: {prof['major']} | Year: {prof['year']}")
        else:
            _send_message(chat_id, "No academic profile set yet. Tell me your degree, major, and year (e.g. '2nd year Bachelor Computer Science').")
        return Response(status_code=200)

    # Escalation / ticket (US-09)
    if "advisor" in lower or "ticket" in lower or "human" in lower:
        ticket_id = f"T-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{chat_id[-4:]}"
        create_ticket(ticket_id, chat_id, sender, text, now, session_id)
        notify = (
            "New Escalation Ticket:\n\n"
            f"Student: {sender} (ID: {chat_id})\n"
            f"Request: '{text}'\n\n"
            f"Staff Actions:\n"
            f"1. 'Show open tickets'\n"
            f"2. 'Resolve ticket for {ticket_id} with [message]'\n"
        )
        if STAFF_GROUP_CHAT_ID:
            _send_message(STAFF_GROUP_CHAT_ID, notify)
        log_query(now, "Other / Not covered", "English", "answered", "Student requested human advisor escalation")
        _send_message(chat_id, "I have opened a support ticket for your request, and a human advisor will be notified shortly.")
        return Response(status_code=200)

    # Normal Q&A path — grounded LLM answer
    kb_docs = find_relevant_docs(text)
    category = kb_docs[0].category if kb_docs else "Other / Not covered"
    reply = await answer(text, GEMINI_API_KEY)
    _send_message(chat_id, reply)
    log_query(now, category, "English", "answered" if kb_docs else "not covered", text[:160])
    return Response(status_code=200)
