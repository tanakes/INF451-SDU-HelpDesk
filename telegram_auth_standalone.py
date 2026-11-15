"""Standalone Telegram authentication script.

Run this locally on your machine to authenticate your personal Telegram account
with Telethon. It will:
1. Send a verification code to your phone number via SMS
2. Ask you to enter the code you received
3. Support 2FA password if enabled
4. Save the authenticated session locally as telegram_session.session

SECURITY: API credentials are embedded (provided by you). Session file is saved
locally and gitignored. Never share this script's output or session file.
"""
from __future__ import annotations

import asyncio
import os
import sys

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

API_ID = 31806014
API_HASH = "387fc06671b3edb8a54d7c12d7a25a94"
SESSION_FILE = "telegram_session.session"
PHONE = "+77053236136"


async def main() -> None:
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    await client.connect()

    if await client.is_user_authorized():
        print("✅ Already authenticated! Session is valid.")
        me = await client.get_me()
        print(f"Logged in as: {me.first_name} ({me.phone})")
        await client.disconnect()
        return

    print(f"📱 Sending verification code to {PHONE} via SMS...")
    try:
        await client.send_code_request(PHONE)
        print("✅ Code sent via SMS.")
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Failed to send code: {type(exc).__name__}: {exc}")
        await client.disconnect()
        return

    code = input("\nEnter the verification code you received: ").strip()

    try:
        await client.sign_in(code=code)
        print("✅ Successfully authenticated!")
    except SessionPasswordNeededError:
        print("🔐 Two-factor authentication is enabled.")
        password = input("Enter your 2FA password: ").strip()
        try:
            await client.sign_in(password=password)
            print("✅ Successfully authenticated with 2FA!")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ 2FA sign-in failed: {type(exc).__name__}: {exc}")
            await client.disconnect()
            return
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Sign-in failed: {type(exc).__name__}: {exc}")
        await client.disconnect()
        return

    me = await client.get_me()
    print(f"\n🎉 Logged in as: {me.first_name or ''} {me.last_name or ''}".strip())
    print(f"Phone: {me.phone}")
    print(f"User ID: {me.id}")
    print(f"\n💾 Session saved locally as: {SESSION_FILE}")
    print("This file is gitignored and will not be committed.")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
