"""SDU Help Desk Bot — Telegram webhook server for Render.

Endpoints:
  GET  /          health check
  GET  /debug     check env var status
  GET  /test-send test _send_message to chat 987654321
  POST /webhook   Telegram webhook entry point (echoes back for debugging)
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, Request, Response
import httpx

app = FastAPI(title="SDU Help Desk Bot")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
STAFF_GROUP_CHAT_ID = os.environ.get("STAFF_GROUP_CHAT_ID", "")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


@app.on_event("startup")
def _startup():
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not NVIDIA_API_KEY:
        missing.append("NVIDIA_API_KEY")
    if missing:
        print(f"STARTUP WARNING: Missing env vars: {', '.join(missing)}")
    else:
        print("STARTUP: All required env vars are set")


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
    """Test _send_message to chat 987654321."""
    if not BOT_TOKEN:
        return {"error": "BOT_TOKEN not set"}
    payload = {"chat_id": 987654321, "text": "Test message from SDU Help Desk Bot - debugging"}
    try:
        resp = httpx.post(
            TELEGRAM_API.format(token=BOT_TOKEN, method="sendMessage"),
            json=payload,
            timeout=15,
        )
        data = resp.json()
        return {"status": resp.status_code, "telegram_response": data}
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
    text = message.get("text", "")
    if not text:
        return Response(status_code=200)

    # Echo back the message for debugging
    reply = f"Echo: {text}\n\n(Debug mode - bot is receiving your messages)"
    result = _send_message(chat_id, reply)
    print(f"WEBHOOK: chat_id={chat_id}, text={text[:50]}, send_result={result}")
    return Response(status_code=200)
