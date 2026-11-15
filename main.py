"""SDU Help Desk Bot — Telegram webhook server for Render.

Implements User Stories US-01 through US-10 (Sprints 1-5).

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

import json
import os
import re
from collections import OrderedDict
from datetime import datetime, timezone
from threading import Lock

from fastapi import FastAPI, Header, HTTPException, Request, Response
import httpx

from llm import answer
from knowledge_base import find_relevant_docs, DOCS
from db import (
    init_schema,
    log_query,
    create_ticket,
    get_profile,
    save_profile,
    list_open_tickets,
    save_session,
    append_session_transcript,
)

app = FastAPI(title="SDU Help Desk Bot")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
STAFF_GROUP_CHAT_ID = os.environ.get("STAFF_GROUP_CHAT_ID", "")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
PORT = int(os.environ.get("PORT", "8000"))
PUBLIC_BASE_URL = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/") or "https://sdu-helpdesk-bot-fresh.onrender.com"

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

_SEEN_UPDATE_IDS: "OrderedDict[int, bool]" = OrderedDict()
_SEEN_MESSAGE_KEYS: "OrderedDict[str, bool]" = OrderedDict()
_SEEN_LOCK = Lock()
_MAX_SEEN = 5000


def _mark_seen(store: "OrderedDict", key, max_size: int = _MAX_SEEN) -> bool:
    with _SEEN_LOCK:
        if key in store:
            return True
        store[key] = True
        while len(store) > max_size:
            store.popitem(last=False)
    return False


# ---------------------------------------------------------------------------
# US-04 Document dispatch manifest
# ---------------------------------------------------------------------------
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "documents", "manifest.json"), "r", encoding="utf-8") as _f:
    _DISPATCH_MANIFEST = json.load(_f)["resources"]

_DISPATCH_BY_ID = {r["id"]: r for r in _DISPATCH_MANIFEST}
_DISPATCH_BY_CATEGORY: dict[str, list[dict]] = {}
for _r in _DISPATCH_MANIFEST:
    _DISPATCH_BY_CATEGORY.setdefault(_r["category"], []).append(_r)


def get_dispatch_resources(category: str | None = None) -> list[dict]:
    if category:
        return _DISPATCH_BY_CATEGORY.get(category, [])
    return list(_DISPATCH_MANIFEST)


def get_dispatch_resource(resource_id: str) -> dict | None:
    return _DISPATCH_BY_ID.get(resource_id)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
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
                {"command": "tickets", "description": "Show open tickets (staff only)"},
                {"command": "summary", "description": "Show query analytics (staff only)"},
                {"command": "help", "description": "Show help information"},
            ]
            httpx.post(
                TELEGRAM_API.format(token=BOT_TOKEN, method="setMyCommands"),
                json={"commands": cmds},
                timeout=15,
            )
        except Exception:
            pass

        # Ensure webhook is configured with secret token when available
        try:
            webhook_url = f"{PUBLIC_BASE_URL}/webhook"
            payload = {
                "url": webhook_url,
                "allowed_updates": ["message"],
                "drop_pending_updates": False,
            }
            if WEBHOOK_SECRET:
                payload["secret_token"] = WEBHOOK_SECRET
            httpx.post(
                TELEGRAM_API.format(token=BOT_TOKEN, method="setWebhook"),
                json=payload,
                timeout=20,
            )
        except Exception as exc:
            print(f"STARTUP WARNING: Failed to set webhook: {exc}")


# ---------------------------------------------------------------------------
# Health / debug
# ---------------------------------------------------------------------------
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
        "port": PORT,
        "kb_docs_count": len(DOCS),
        "dispatch_resources": len(_DISPATCH_MANIFEST),
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


# ---------------------------------------------------------------------------
# Message sending helpers
# ---------------------------------------------------------------------------
def _send_message(chat_id: str | int, text: str) -> dict:
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


def _send_document(chat_id: str | int, file_path: str) -> dict:
    if not BOT_TOKEN:
        return {"success": False, "error": "BOT_TOKEN not configured"}
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}
    try:
        with open(file_path, "rb") as _f:
            files = {"document": (_f.name, _f, "application/octet-stream")}
            data = {"chat_id": chat_id}
            resp = httpx.post(
                TELEGRAM_API.format(token=BOT_TOKEN, method="sendDocument"),
                data=data,
                files=files,
                timeout=60,
            )
        resp.raise_for_status()
        result = resp.json()
        if result.get("ok"):
            return {"success": True}
        return {"success": False, "error": f"Telegram API: {result}"}
    except httpx.HTTPStatusError as exc:
        return {"success": False, "error": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _send_photo(chat_id: str | int, file_path: str) -> dict:
    if not BOT_TOKEN:
        return {"success": False, "error": "BOT_TOKEN not configured"}
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}
    try:
        with open(file_path, "rb") as _f:
            files = {"photo": (_f.name, _f, "image/jpeg")}
            data = {"chat_id": chat_id}
            resp = httpx.post(
                TELEGRAM_API.format(token=BOT_TOKEN, method="sendPhoto"),
                data=data,
                files=files,
                timeout=60,
            )
        resp.raise_for_status()
        result = resp.json()
        if result.get("ok"):
            return {"success": True}
        return {"success": False, "error": f"Telegram API: {result}"}
    except httpx.HTTPStatusError as exc:
        return {"success": False, "error": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Session persistence
# ---------------------------------------------------------------------------
def _save_session_transcript(session_id: str, sender: str, user_msg: str, bot_reply: str):
    try:
        save_session(session_id, sender, "Telegram")
        append_session_transcript(session_id, user_msg, bot_reply)
    except Exception:
        pass  # never break the webhook on session save failure


# ---------------------------------------------------------------------------
# US-01 / US-02: Commands and menu
# ---------------------------------------------------------------------------
WELCOME_MESSAGE = (
    "🎓 Welcome to the SDU University Help Desk!\n\n"
    "Choose a topic:\n\n"
    "1. Tuition Fees\n"
    "2. Course Add/Drop\n"
    "3. Dormitory\n"
    "4. Transcripts\n\n"
    "Or just ask your question in Kazakh, Russian, or English."
)

MENU_MESSAGE = (
    "📋 SDU Help Desk Menu:\n\n"
    "1. Tuition Fees\n"
    "2. Course Add/Drop\n"
    "3. Dormitory\n"
    "4. Transcripts\n\n"
    "Ask your question in Kazakh, Russian, or English."
)

HELP_MESSAGE = (
    "🆘 SDU Help Desk Bot Commands:\n\n"
    "/start - Start the bot and show welcome menu\n"
    "/menu - Show topic menu\n"
    "/profile - View or set your academic profile\n"
    "/advisor - Escalate to a human advisor\n"
    "/tickets - Show open tickets (staff only)\n"
    "/summary - Show query analytics (staff only)\n"
    "/help - Show this help\n\n"
    "Or just ask your question in Kazakh, Russian, or English."
)


def _format_dispatch_resource(r: dict) -> str:
    mode = r.get("dispatch_mode", "link")
    title = r.get("title", "Untitled")
    if mode == "file":
        return f"📄 {title} — official PDF available (file dispatch)"
    if mode == "link":
        return f"🔗 {title} — {r.get('url', 'URL not available')}"
    if mode == "unavailable":
        return f"❌ {title} — Not available for download. Please contact the SSC in Block B."
    return f"ℹ️ {title} — {mode}"


def _is_staff_chat(chat_id: str | int) -> bool:
    return bool(STAFF_GROUP_CHAT_ID) and str(chat_id) == str(STAFF_GROUP_CHAT_ID)


def _parse_profile_text(text: str) -> dict:
    lower = text.lower()
    degree = "Bachelor"
    if "phd" in lower or "doctoral" in lower or "doctorate" in lower:
        degree = "PhD"
    elif "master" in lower:
        degree = "Master"
    elif "bachelor" in lower:
        degree = "Bachelor"

    year = None
    year_match = re.search(r"\b([1-6])\s*(?:st|nd|rd|th)?\s*[- ]?\s*year\b", lower)
    if not year_match:
        year_match = re.search(r"\byear\s*([1-6])\b", lower)
    if not year_match:
        ord_map = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6}
        for name, num in ord_map.items():
            if re.search(rf"\b{name}\s+year\b", lower):
                year = num
                break
    if year_match and year is None:
        try:
            year = int(year_match.group(1))
        except Exception:
            year = None

    major = "General"
    major_patterns = [
        r"\b(?:bachelor|master|phd|doctoral)\s+(?:of\s+)?(.+?)\s+student\b",
        r"\b(?:major(?:ing)?\s+in)\s+(.+?)(?:[,.]|$)",
        r"\bstudent(?:\s+of|\s+in)\s+(.+?)(?:[,.]|$)",
    ]
    for pat in major_patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            candidate = re.sub(r"\s+", " ", m.group(1)).strip(" .,-")
            candidate = re.sub(r"\b\d+(?:st|nd|rd|th)?\s*year\b", "", candidate, flags=re.IGNORECASE).strip(" .,-")
            if candidate and 2 <= len(candidate) <= 60:
                major = candidate.title()
                break

    return {"degree": degree, "year": year, "major": major}


# ---------------------------------------------------------------------------
# Webhook
# ---------------------------------------------------------------------------
@app.post("/webhook")
async def webhook(request: Request, x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="invalid secret token")

    try:
        data = await request.json()
    except Exception:
        return Response(status_code=200)

    update_id = data.get("update_id")
    if isinstance(update_id, int) and _mark_seen(_SEEN_UPDATE_IDS, update_id):
        return Response(status_code=200)

    message = data.get("message")
    if not message:
        return Response(status_code=200)

    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    message_id = message.get("message_id")
    if chat_id and message_id is not None:
        if _mark_seen(_SEEN_MESSAGE_KEYS, f"{chat_id}:{message_id}"):
            return Response(status_code=200)
    sender = " ".join(filter(None, [chat.get("first_name", ""), chat.get("last_name", "")])).strip() or "Unknown"
    text = message.get("text", "")
    if not text:
        return Response(status_code=200)

    session_id = f"tg-{chat_id}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lower = text.strip().lower()

    try:
        # ── US-01: /start command ──
        if lower == "/start":
            result = _send_message(chat_id, WELCOME_MESSAGE)
            if not result["success"]:
                print(f"SEND_FAILED: {result['error']}")
            _save_session_transcript(session_id, sender, "/start", WELCOME_MESSAGE)
            log_query(now, "System", "English", "answered", "User started bot with /start")
            return Response(status_code=200)

        # ── US-02: /menu command ──
        if lower == "/menu":
            result = _send_message(chat_id, MENU_MESSAGE)
            if not result["success"]:
                print(f"SEND_FAILED: {result['error']}")
            _save_session_transcript(session_id, sender, "/menu", MENU_MESSAGE)
            return Response(status_code=200)

        # ── US-01: /help command ──
        if lower == "/help":
            result = _send_message(chat_id, HELP_MESSAGE)
            if not result["success"]:
                print(f"SEND_FAILED: {result['error']}")
            _save_session_transcript(session_id, sender, "/help", HELP_MESSAGE)
            return Response(status_code=200)

        # ── US-08: /profile command ──
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
            result = _send_message(chat_id, reply)
            if not result["success"]:
                print(f"SEND_FAILED: {result['error']}")
            _save_session_transcript(session_id, sender, "/profile", reply)
            return Response(status_code=200)

        # ── US-09: /advisor command ──
        if lower == "/advisor" or lower in ("advisor", "ticket", "human", "escalate"):
            ticket_id = f"T-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{chat_id[-4:]}"
            escalation_context = text.strip()
            if lower == "/advisor":
                escalation_context = "Student requested to speak with a human advisor."
            create_ticket(ticket_id, chat_id, sender, escalation_context, now, session_id)
            notify = (
                "🚨 New Escalation Ticket:\n\n"
                f"Student: {sender} (ID: {chat_id})\n"
                f"Request: {escalation_context}\n\n"
                f"Staff Actions:\n"
                f"1. Use /tickets to view open tickets\n"
                f"2. Resolve ticket for {ticket_id}\n"
            )
            if STAFF_GROUP_CHAT_ID:
                _send_message(STAFF_GROUP_CHAT_ID, notify)
            reply = "I have opened a support ticket for your request, and a human advisor will be notified shortly."
            result = _send_message(chat_id, reply)
            if not result["success"]:
                print(f"SEND_FAILED: {result['error']}")
            _save_session_transcript(session_id, sender, text, reply)
            log_query(now, "Other / Not covered", "English", "answered", "Student requested human advisor escalation")
            return Response(status_code=200)

        # ── US-10: /tickets command (staff only) ──
        if lower == "/tickets":
            if not _is_staff_chat(chat_id):
                reply = "🔒 Access Restricted: This command is only available inside the authorized staff group."
                _send_message(chat_id, reply)
                _save_session_transcript(session_id, sender, "/tickets", reply)
                return Response(status_code=200)
            tickets = list_open_tickets()
            lines = ["📋 Open support tickets:"]
            if not tickets:
                lines.append("None.")
            else:
                for t in tickets:
                    lines.append(f"• {t['ticket_id']}: {t.get('sender','Unknown')} — {t.get('context','')[:80]}")
            reply = "\n".join(lines)
            result = _send_message(chat_id, reply)
            if not result["success"]:
                print(f"SEND_FAILED: {result['error']}")
            _save_session_transcript(session_id, sender, "/tickets", reply)
            return Response(status_code=200)

        # ── US-06: /summary command (staff only) ──
        if lower == "/summary":
            if not _is_staff_chat(chat_id):
                reply = "🔒 Access Restricted: This command is only available inside the authorized staff group."
                _send_message(chat_id, reply)
                _save_session_transcript(session_id, sender, "/summary", reply)
                return Response(status_code=200)
            reply = await answer("Show me the executive summary of student questions (answered vs not covered, by category and language).", NVIDIA_API_KEY)
            result = _send_message(chat_id, reply)
            if not result["success"]:
                print(f"SEND_FAILED: {result['error']}")
            _save_session_transcript(session_id, sender, "/summary", reply)
            log_query(now, "Campus Services", "English", "answered", "Staff requested executive summary")
            return Response(status_code=200)

        # ── US-04: Document dispatch commands ──
        # Handle requests for specific documents like "send me the campus map"
        doc_keywords = {
            "campus map": "campus_map_image",
            "tuition regulation": "tuition_fees_regulation_pdf",
            "tuition fees regulation": "tuition_fees_regulation_pdf",
            "academic calendar": "academic_calendar",
            "dormitory boys": "dormitory_boys_house",
            "dormitory girls": "dormitory_girls_house",
            "student service center": "student_service_center_services",
            "petition forms": "petition_forms",
            "campus wifi": "campus_wifi_info",
            "academic regulations": "academic_regulations_all",
        }

        doc_requested = None
        for keyword, resource_id in doc_keywords.items():
            if keyword in lower:
                doc_requested = resource_id
                break

        if doc_requested:
            resource = get_dispatch_resource(doc_requested)
            if not resource:
                reply = "❌ I couldn't find that document. Please contact the SSC in Block B."
                result = _send_message(chat_id, reply)
                if not result["success"]:
                    print(f"SEND_FAILED: {result['error']}")
                _save_session_transcript(session_id, sender, text, reply)
                return Response(status_code=200)

            mode = resource.get("dispatch_mode", "link")

            if mode == "unavailable":
                reply = (
                    f"❌ {resource.get('title', 'Document')} is not available for download.\n\n"
                    f"Reason: {resource.get('reason', 'No reason provided.')}\n\n"
                    f"Please contact the SSC in Block B for assistance."
                )
                result = _send_message(chat_id, reply)
                if not result["success"]:
                    print(f"SEND_FAILED: {result['error']}")
                _save_session_transcript(session_id, sender, text, reply)
                return Response(status_code=200)

            if mode == "link":
                url = resource.get("url", "")
                reply = (
                    f"🔗 {resource.get('title', 'Document')}\n\n"
                    f"Link: {url}\n\n"
                    f"This is the official source. Please visit the link for the full document."
                )
                result = _send_message(chat_id, reply)
                if not result["success"]:
                    print(f"SEND_FAILED: {result['error']}")
                _save_session_transcript(session_id, sender, text, reply)
                return Response(status_code=200)

            if mode == "file":
                file_path = resource.get("file", "")
                if not file_path:
                    reply = f"❌ File path not configured for {resource.get('title', 'Document')}."
                    result = _send_message(chat_id, reply)
                    if not result["success"]:
                        print(f"SEND_FAILED: {result['error']}")
                    _save_session_transcript(session_id, sender, text, reply)
                    return Response(status_code=200)

                # Resolve relative path
                base_dir = os.path.dirname(os.path.abspath(__file__))
                abs_path = os.path.join(base_dir, file_path)

                if file_path.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                    result = _send_photo(chat_id, abs_path)
                else:
                    result = _send_document(chat_id, abs_path)

                if not result["success"]:
                    reply = f"❌ Failed to send {resource.get('title', 'Document')}. Error: {result['error']}"
                    _send_message(chat_id, reply)
                else:
                    reply = f"📎 Here is your document: {resource.get('title', 'Document')}"
                    _send_message(chat_id, reply)

                _save_session_transcript(session_id, sender, text, reply if result["success"] else f"Document dispatch failed: {result.get('error', 'unknown')}")
                return Response(status_code=200)

        # US-08: Profile setting from natural language
        if any(kw in lower for kw in ["i am a", "i'm a", "my degree", "student year", "my major"]) and any(
            kw in lower for kw in ["bachelor", "master", "phd", "doctoral", "year", "student"]
        ):
            prof = _parse_profile_text(text)
            save_profile(chat_id, prof["degree"], prof["year"], prof["major"], text[:200], now)
            reply = (
                "✅ Profile updated!\n\n"
                f"Degree: {prof['degree']}\n"
                f"Major: {prof['major']}\n"
                f"Year: {prof['year'] if prof['year'] is not None else 'N/A'}\n\n"
                "Use /profile to view it anytime."
            )
            result = _send_message(chat_id, reply)
            if not result["success"]:
                print(f"SEND_FAILED: {result['error']}")
            _save_session_transcript(session_id, sender, text, reply)
            return Response(status_code=200)

        # ── US-03 / US-05: Normal Q&A path — grounded LLM answer ──
        kb_docs = find_relevant_docs(text)
        reply = await answer(text, NVIDIA_API_KEY)
        result = _send_message(chat_id, reply)
        if not result["success"]:
            print(f"SEND_FAILED: {result['error']}")
        _save_session_transcript(session_id, sender, text, reply)
        category = kb_docs[0].category if kb_docs else "Other / Not covered"
        log_query(now, category, "English", "answered" if kb_docs else "not covered", text[:160])
        return Response(status_code=200)

    except Exception as exc:
        error_reply = f"Debug error: {type(exc).__name__}: {str(exc)[:200]}"
        _send_message(chat_id, error_reply)
        return Response(status_code=200)
