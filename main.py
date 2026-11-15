"""SDU Help Desk Bot — Telegram webhook server for Render.

Endpoints:
  GET  /          health check
  GET  /debug     check env var status
  GET  /test-send test _send_message
  POST /webhook   Telegram webhook entry point

Env vars:
  BOT_TOKEN, NVIDIA_API_KEY, STAFF_GROUP_CHAT_ID, WEBHOOK_SECRET,
  PORT (set by Render)
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, Request, Response
import httpx

from llm import answer
from knowledge_base import find_relevant_docs
from db import init_schema, log_query, create_ticket, get_profile, save_profile

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
        print(f"STARTUP WARNING: Missing env vars: {', '.join(missing)}")
    else:
        print("STARTUP: All required env vars are set")

    # Set Telegram bot commands
    if BOT_TOKEN:
        try:
            cmds = [
                {"command": "start", "description": "Start the bot and show welcome menu"},
                {"command": "menu", "description": "Show topic menu"},
                {"command": "profile", "description": "View or set your academic profile"},
                {"command": "advisor", "description": "Escalate to a human advisor"},
                {"command": "help", "description": "Show help information"},
            ]
            httpx.post(
                TELEGRAM_API.format(token=BOT_TOKEN, method="setMyCommands"),
                json={"commands": cmds},
                timeout=15,
            )
        except Exception:
            pass


@app.get("/")
async def health():
    return {"status": "ok", "service": "sdu-helpdesk-bot"}


@app.get("/debug")
async def debug():
    return {
        "bot_token_set": bool(BOT_TOKEN),
        "bot_token_prefix": BOT_TOKEN[:10] + "..." if BOT_TOKEN else None,
        "nvidia_api_key_set": bool(NVIDIA_API_KEY),
        "staff_group_chat_id": STAFF_GROUP_CHAT_ID or None,
        "webhook_secret_set": bool(WEBHOOK_SECRET),
    }


@app.get("/test-send")
async def test_send():
    if not BOT_TOKEN:
        return {"error": "BOT_TOKEN not set"}
    payload = {"chat_id": 987654321, "text": "Test from SDU Help Desk Bot"}
    try:
        resp = httpx.post(
            TELEGRAM_API.format(token=BOT_TOKEN, method="sendMessage"),
            json=payload,
            timeout=15,
        )
        return {"status": resp.status_code, "telegram_response": resp.json()}
    except Exception as exc:
        return {"error": str(exc)}


def _send_message(chat_id: str, text: str) -> dict:
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


def _save_session(session_id: str, sender: str, channel: str, text: str, reply: str):
    """Save session transcript to file-based database."""
    from db import save_session, append_session_transcript
    try:
        save_session(session_id, sender, channel)
        append_session_transcript(session_id, text, reply)
    except Exception:
        pass  # don't break the webhook on session save failure


@app.post("/webhook")
async def webhook(request: Request, x_telegram_bot_api_secret_token: str | None = Header(default=None)):
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
        # /start command - new session
        if lower == "/start":
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
            _save_session(session_id, sender, "Telegram", "/start", reply)
            log_query(now, "System", "English", "answered", "User started bot with /start")
            return Response(status_code=200)

        # /menu command
        if lower == "/menu":
            reply = (
                "📋 SDU Help Desk Menu:\n\n"
                "1. Tuition Fees\n"
                "2. Course Add/Drop\n"
                "3. Dormitory\n"
                "4. Transcripts\n\n"
                "Ask your question in Kazakh, Russian, or English."
            )
            _send_message(chat_id, reply)
            _save_session(session_id, sender, "Telegram", "/menu", reply)
            return Response(status_code=200)

        # /help command
        if lower == "/help":
            reply = (
                "🆘 SDU Help Desk Bot Commands:\n\n"
                "/start - Start the bot and show welcome menu\n"
                "/menu - Show topic menu\n"
                "/profile - View or set your academic profile\n"
                "/advisor - Escalate to a human advisor\n"
                "/help - Show this help\n\n"
                "Or just ask your question in Kazakh, Russian, or English."
            )
            _send_message(chat_id, reply)
            _save_session(session_id, sender, "Telegram", "/help", reply)
            return Response(status_code=200)

        # /profile command
        if lower == "/profile":
            prof = get_profile(chat_id)
            if prof:
                reply = (
                    f"🎓 Your academic profile:\n\n"
                    f"Degree: {prof.get('degree', 'N/A')}\n"
                    f"Major: {prof.get('major', 'N/A')}\n"
                    f"Year: {prof.get('year', 'N/A')}\n"
                    f"Updated: {prof.get('updated_at_utc', 'N/A')}\n\n"
                    f"To update, send: 'I am a [degree] [major] student, year [number]'"
                )
            else:
                reply = (
                    "No academic profile set yet.\n\n"
                    "Tell me your degree, major, and year (e.g. 'I am a 2nd year Bachelor Computer Science student')."
                )
            _send_message(chat_id, reply)
            _save_session(session_id, sender, "Telegram", "/profile", reply)
            return Response(status_code=200)

        # Profile setting (natural language)
        if any(kw in lower for kw in ["i am a", "i'm a", "my degree", "student year"]) and any(
            kw in lower for kw in ["bachelor", "master", "phd", "year", "student"]
        ):
            save_profile(chat_id, "Bachelor", None, "General", text[:100], now)
            reply = (
                "✅ Profile updated!\n\n"
                "I've saved your academic information. Use /profile to view it anytime."
            )
            _send_message(chat_id, reply)
            _save_session(session_id, sender, "Telegram", text, reply)
            return Response(status_code=200)

        # Staff advisor analytics
        if lower in ("summary", "stat", "stats", "отчет", "статистика"):
            if chat_id != STAFF_GROUP_CHAT_ID:
                _send_message(chat_id, "🔒 Access Restricted: This advisor command is only available inside the authorized staff group.")
                return Response(status_code=200)
            docs = find_relevant_docs("query summary analytics")
            reply = await answer("Show me the executive summary of student questions.", NVIDIA_API_KEY)
            _send_message(chat_id, reply)
            return Response(status_code=200)

        if lower in ("sessions", "сессии", "логи", "logs"):
            if chat_id != STAFF_GROUP_CHAT_ID:
                _send_message(chat_id, "🔒 Access Restricted: Session logs are only available inside the authorized staff group.")
                return Response(status_code=200)
            _send_message(chat_id, "📋 Open support tickets:\n\nNone.")
            return Response(status_code=200)

        # Escalation / ticket
        if "advisor" in lower or "ticket" in lower or "human" in lower or lower == "/advisor":
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
            reply = "I have opened a support ticket for your request, and a human advisor will be notified shortly."
            _send_message(chat_id, reply)
            _save_session(session_id, sender, "Telegram", text, reply)
            log_query(now, "Other / Not covered", "English", "answered", "Student requested human advisor escalation")
            return Response(status_code=200)

        # Normal Q&A path — grounded LLM answer
        kb_docs = find_relevant_docs(text)
        reply = await answer(text, NVIDIA_API_KEY)
        result = _send_message(chat_id, reply)
        if not result["success"]:
            print(f"SEND_FAILED: {result['error']}")
        _save_session(session_id, sender, "Telegram", text, reply)
        category = kb_docs[0].category if kb_docs else "Other / Not covered"
        log_query(now, category, "English", "answered" if kb_docs else "not covered", text[:160])
        return Response(status_code=200)

    except Exception as exc:
        error_reply = f"Debug error: {type(exc).__name__}: {str(exc)[:200]}"
        _send_message(chat_id, error_reply)
        return Response(status_code=200)
