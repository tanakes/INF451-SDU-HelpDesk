"""SDU Help Desk Bot — Telegram webhook server for Render.

Endpoints:
  GET  /          health check
  GET  /debug     check env var status
  POST /webhook   Telegram webhook entry point

Env vars:
  BOT_TOKEN, NVIDIA_API_KEY, DATABASE_URL, WEBHOOK_SECRET,
  STAFF_GROUP_CHAT_ID, PORT (set by Render)
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, Request, Response
import httpx

from db import init_schema
from llm import answer
from knowledge_base import find_relevant_docs

app = FastAPI(title="SDU Help Desk Bot")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
STAFF_GROUP_CHAT_ID = os.environ.get("STAFF_GROUP_CHAT_ID", "")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


@app.on_event("startup")
def _startup():
    init_schema()
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not NVIDIA_API_KEY:
        missing.append("NVIDIA_API_KEY")
    if missing:
        print(f"WARNING: Missing env vars: {', '.join(missing)}")


@app.get("/")
async def health():
    return {"status": "ok", "service": "sdu-helpdesk-bot"}


@app.get("/debug")
async def debug():
    return {
        "bot_token_set": bool(BOT_TOKEN),
        "bot_token_prefix": BOT_TOKEN[:10] + "..." if BOT_TOKEN else None,
        "nvidia_api_key_set": bool(NVIDIA_API_KEY),
        "nvidia_api_key_prefix": NVIDIA_API_KEY[:10] + "..." if NVIDIA_API_KEY else None,
        "staff_group_chat_id": STAFF_GROUP_CHAT_ID or None,
        "webhook_secret_set": bool(WEBHOOK_SECRET),
    }


def _send_message(chat_id: str, text: str) -> dict:
    """Send a message via Telegram. Returns result dict with success/error info."""
    if not BOT_TOKEN:
        return {"success": False, "error": "BOT_TOKEN not configured"}
    payload = {"chat_id": chat_id, "text": text}
    try:
        resp = httpx.post(
            TELEGRAM_API.format(token=BOT_TOKEN, method="sendMessage"),
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok"):
            return {"success": True}
        return {"success": False, "error": f"Telegram API: {data}"}
    except httpx.HTTPStatusError as exc:
        return {"success": False, "error": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


@app.post("/webhook")
async def webhook(request: Request, x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    # Secret token check
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="invalid secret token")

    try:
        data = await request.json()
    except Exception:
        return Response(status_code=200)

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

    try:
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
            result = _send_message(chat_id, reply)
            if not result["success"]:
                print(f"SEND_FAILED: {result['error']}")
            return Response(status_code=200)

        # Staff advisor analytics
        if lower in ("summary", "stat", "stats", "отчет", "статистика"):
            if chat_id != STAFF_GROUP_CHAT_ID:
                _send_message(chat_id, "🔒 Access Restricted: This advisor command is only available inside the authorized staff group.")
                return Response(status_code=200)
            docs = find_relevant_docs("query summary analytics")
            reply = await answer("Show me the executive summary of student questions (answered vs not covered, by category and language).", NVIDIA_API_KEY)
            _send_message(chat_id, reply)
            return Response(status_code=200)

        if lower in ("sessions", "сессии", "логи", "logs"):
            if chat_id != STAFF_GROUP_CHAT_ID:
                _send_message(chat_id, "🔒 Access Restricted: Session logs are only available inside the authorized staff group.")
                return Response(status_code=200)
            _send_message(chat_id, "📋 Open support tickets:\n\nNone.")
            return Response(status_code=200)

        # Profile management
        if lower.startswith("profile"):
            if "reset" in lower:
                _send_message(chat_id, "✅ Profile cleared. General rules apply now.")
                return Response(status_code=200)
            _send_message(chat_id, "No academic profile set yet. Tell me your degree, major, and year (e.g. '2nd year Bachelor Computer Science').")
            return Response(status_code=200)

        # Escalation / ticket
        if "advisor" in lower or "ticket" in lower or "human" in lower:
            ticket_id = f"T-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{chat_id[-4:]}"
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
            _send_message(chat_id, "I have opened a support ticket for your request, and a human advisor will be notified shortly.")
            return Response(status_code=200)

        # Normal Q&A path — grounded LLM answer
        kb_docs = find_relevant_docs(text)
        reply = await answer(text, NVIDIA_API_KEY)
        result = _send_message(chat_id, reply)
        if not result["success"]:
            print(f"SEND_FAILED: {result['error']}")
        return Response(status_code=200)

    except Exception as exc:
        # Send error details back to the user for debugging
        error_reply = f"Debug error: {type(exc).__name__}: {str(exc)[:200]}"
        _send_message(chat_id, error_reply)
        return Response(status_code=200)
