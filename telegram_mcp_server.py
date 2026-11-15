"""Telegram MCP Server — connects to personal Telegram account via MTProto API.

Provides read-only MCP tools for dialog/message/contact access plus a
send_message tool that requires explicit confirmation before sending.
"""
from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP
import qrcode
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import Message, User, Chat, Channel

# ---------------------------------------------------------------------------
# Configuration (credentials provided by user — never printed or logged)
# ---------------------------------------------------------------------------
API_ID = 31806014
API_HASH = "387fc06671b3edb8a54d7c12d7a25a94"
SESSION_FILE = "telegram_session.session"

# ---------------------------------------------------------------------------
# Global client state
# ---------------------------------------------------------------------------
_client: Optional[TelegramClient] = None
_client_lock = asyncio.Lock()
_is_authenticated = False


def _client_path() -> str:
    return SESSION_FILE


async def _get_client() -> TelegramClient:
    """Get or create the Telethon client, authenticating if needed."""
    global _client, _is_authenticated

    async with _client_lock:
        if _client is not None and _client.is_connected():
            return _client

        _client = TelegramClient(_client_path(), API_ID, API_HASH)
        await _client.connect()

        if not await _client.is_user_authorized():
            _is_authenticated = False
            raise RuntimeError(
                "Telegram client not authenticated. "
                "Call authenticate() first with your phone number."
            )

        _is_authenticated = True
        return _client


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------
mcp = FastMCP("telegram-mcp")


@mcp.tool()
async def authenticate() -> dict[str, Any]:
    """Step 1 of authentication: generate QR code for QR login.

    No SMS required. Scan the QR code with your Telegram app:
    - Mobile: Settings → Devices → Link Desktop Device
    - Desktop: Settings → Devices → Link Desktop Device

    Returns:
        QR code URL and instructions. Call authenticate_complete()
        after scanning to confirm authentication.
    """
    global _client, _is_authenticated

    async with _client_lock:
        if _client is not None and _client.is_connected():
            await _client.disconnect()

        _client = TelegramClient(_client_path(), API_ID, API_HASH)
        await _client.connect()

        if await _client.is_user_authorized():
            _is_authenticated = True
            return {
                "status": "already_authenticated",
                "message": "Session already exists and is authorized.",
            }

        try:
            qr_login = await _client.qr_login()
            return {
                "status": "qr_ready",
                "message": "QR code generated. Scan it with your Telegram app.",
                "qr_url": qr_login.url,
                "instructions": (
                    "1. Open Telegram on your phone\n"
                    "2. Go to Settings → Devices → Link Desktop Device\n"
                    "3. Scan the QR code below\n"
                    "4. Keep this window open while scanning\n"
                    "5. Call authenticate_complete() after scanning"
                ),
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "error",
                "message": f"Failed to generate QR code: {type(exc).__name__}",
            }


@mcp.tool()
async def authenticate_complete(password: Optional[str] = None) -> dict[str, Any]:
    """Step 2 of authentication: wait for QR login to complete.

    After scanning the QR code with your Telegram app, call this to confirm.
    If 2FA is enabled, provide your password.

    Args:
        password: Two-factor authentication password, if 2FA is enabled.

    Returns:
        Authentication result.
    """
    global _client, _is_authenticated

    if _client is None or not _client.is_connected():
        return {
            "status": "error",
            "message": "No active connection. Call authenticate() first.",
        }

    if await _client.is_user_authorized():
        _is_authenticated = True
        return {
            "status": "authenticated",
            "message": "Successfully authenticated via QR code.",
        }

    try:
        await _client.qr_login.wait()
        _is_authenticated = True
        return {
            "status": "authenticated",
            "message": "Successfully authenticated via QR code.",
        }
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "message": "QR code expired. Call authenticate() to generate a new one.",
        }
    except SessionPasswordNeededError:
        if password is None:
            return {
                "status": "2fa_required",
                "message": "Two-factor authentication is enabled. "
                "Call authenticate_complete() again with the password parameter.",
            }
        try:
            await _client.sign_in(password=password)
            _is_authenticated = True
            return {
                "status": "authenticated",
                "message": "Successfully authenticated with 2FA.",
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "error",
                "message": f"2FA sign-in failed: {type(exc).__name__}",
            }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "message": f"QR login failed: {type(exc).__name__}",
        }


@mcp.tool()
async def get_dialogs(limit: int = 20) -> dict[str, Any]:
    """List conversations (dialogs). Read-only.

    Args:
        limit: Maximum number of dialogs to return (default 20).

    Returns:
        List of dialogs with id, title, type, unread count, and date.
    """
    client = await _get_client()
    dialogs = await client.get_dialogs(limit=limit)

    result = []
    for d in dialogs:
        entity = d.entity
        dialog_type = "user"
        if isinstance(entity, Chat):
            dialog_type = "group"
        elif isinstance(entity, Channel):
            dialog_type = "channel" if entity.broadcast else "group"
        elif isinstance(entity, User):
            dialog_type = "user"

        result.append(
            {
                "id": entity.id,
                "title": getattr(entity, "title", None)
                or f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                or "Unknown",
                "type": dialog_type,
                "unread_count": d.unread_count,
                "date": str(d.date) if d.date else None,
            }
        )

    return {"status": "ok", "count": len(result), "dialogs": result}


@mcp.tool()
async def get_messages(chat_id: int, limit: int = 50) -> dict[str, Any]:
    """Retrieve messages from a specified chat. Read-only.

    Args:
        chat_id: Chat/channel/user ID.
        limit: Maximum number of messages (default 50).

    Returns:
        List of messages with id, sender, text, and date.
    """
    client = await _get_client()
    messages = await client.get_messages(chat_id, limit=limit)

    result = []
    for m in messages:
        if not isinstance(m, Message):
            continue
        sender = await m.get_sender() if m.sender_id else None
        sender_name = None
        if isinstance(sender, User):
            sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip() or sender.username
        elif isinstance(sender, (Chat, Channel)):
            sender_name = sender.title

        result.append(
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "sender_name": sender_name,
                "text": m.message or "",
                "date": str(m.date) if m.date else None,
                "out": bool(m.out),
            }
        )

    return {"status": "ok", "count": len(result), "messages": result}


@mcp.tool()
async def search_messages(query: str, limit: int = 20) -> dict[str, Any]:
    """Search messages across all chats. Read-only.

    Args:
        query: Search query string.
        limit: Maximum number of results (default 20).

    Returns:
        List of matching messages with chat info.
    """
    client = await _get_client()
    messages = await client.search_messages(query=query, limit=limit)

    result = []
    for m in messages:
        if not isinstance(m, Message):
            continue
        chat = await m.get_chat()
        chat_name = None
        if isinstance(chat, User):
            chat_name = f"{chat.first_name or ''} {chat.last_name or ''}".strip() or chat.username
        elif isinstance(chat, (Chat, Channel)):
            chat_name = chat.title

        result.append(
            {
                "id": m.id,
                "chat_id": m.peer_id.channel_id if hasattr(m.peer_id, "channel_id") else None,
                "chat_name": chat_name,
                "text": m.message or "",
                "date": str(m.date) if m.date else None,
            }
        )

    return {"status": "ok", "count": len(result), "messages": result}


@mcp.tool()
async def get_contacts() -> dict[str, Any]:
    """List contacts. Read-only.

    Returns:
        List of contacts with id, name, username, and phone.
    """
    client = await _get_client()
    contacts = await client.get_contacts()

    result = []
    for c in contacts:
        if not isinstance(c, User):
            continue
        result.append(
            {
                "id": c.id,
                "first_name": c.first_name or "",
                "last_name": c.last_name or "",
                "username": c.username or "",
                "phone": c.phone or "",
            }
        )

    return {"status": "ok", "count": len(result), "contacts": result}


@mcp.tool()
async def send_message(chat_id: int, text: str, confirm: bool = False) -> dict[str, Any]:
    """Send a message to a specified chat. Requires explicit confirmation.

    SECURITY: This tool requires confirm=true to actually send.
    Without confirmation, it returns a warning only.

    Args:
        chat_id: Target chat/user ID.
        text: Message text to send.
        confirm: Must be true to actually send the message.

    Returns:
        Send result or warning if not confirmed.
    """
    if not confirm:
        return {
            "status": "confirmation_required",
            "message": "Set confirm=true to send this message. "
            "This action modifies Telegram data.",
            "chat_id": chat_id,
            "text_preview": text[:50] + ("..." if len(text) > 50 else ""),
        }

    client = await _get_client()
    try:
        await client.send_message(chat_id, text)
        return {
            "status": "sent",
            "message": "Message sent successfully.",
            "chat_id": chat_id,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "message": f"Failed to send message: {type(exc).__name__}",
        }


@mcp.tool()
async def auth_status() -> dict[str, Any]:
    """Check current authentication status. Read-only.

    Returns:
        Whether the client is connected and authenticated.
    """
    connected = _client is not None and _client.is_connected()
    authorized = _is_authenticated and connected
    return {
        "connected": connected,
        "authenticated": authorized,
        "session_file": SESSION_FILE,
    }


@mcp.tool()
async def disconnect() -> dict[str, Any]:
    """Disconnect the Telegram client. Read-only state change."""
    global _client, _is_authenticated

    async with _client_lock:
        if _client is not None and _client.is_connected():
            await _client.disconnect()
        _is_authenticated = False
        return {"status": "disconnected"}


# ---------------------------------------------------------------------------
# Entry point for stdio transport
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
