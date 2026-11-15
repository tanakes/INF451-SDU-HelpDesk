"""Standalone Telegram QR authentication script.

Authenticates your personal Telegram account using Telethon's QR code login —
no SMS required. Scan the QR code with your already-authorized Telegram app:

1. Telegram mobile app: Settings → Devices → Link Desktop Device
2. Telegram Desktop: Settings → Devices → Link Desktop Device

SECURITY: API credentials are embedded (provided by you). Session file is saved
locally as telegram_session.session and is gitignored.
"""
from __future__ import annotations

import asyncio
import sys

import qrcode
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

API_ID = 31806014
API_HASH = "387fc06671b3edb8a54d7c12d7a25a94"
SESSION_FILE = "telegram_session.session"


def print_qr_terminal(qr_code: str) -> None:
    """Print QR code to terminal using ANSI blocks."""
    lines = qr_code.split("\n")
    for line in lines:
        row = ""
        for ch in line:
            row += "\u2588\u2588" if ch == "1" else "  "
        print(row)


async def main() -> None:
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    await client.connect()

    # Already authenticated?
    if await client.is_user_authorized():
        print("✅ Already authenticated! Session is valid.")
        me = await client.get_me()
        print(f"Logged in as: {me.first_name} ({me.phone})")
        await client.disconnect()
        return

    print("\n🔐 QR Code Authentication")
    print("=" * 40)
    print("1. Open Telegram on your phone")
    print("2. Go to Settings → Devices → Link Desktop Device")
    print("3. Scan the QR code below")
    print("4. Keep this window open while scanning")
    print("=" * 40 + "\n")

    qr_login = await client.qr_login()

    # Print QR code to terminal
    print("Scan this QR code with your Telegram app:\n")
    print_qr_terminal(qr_code=qr_login.url)

    # Also save QR code as image file
    img = qrcode.make(qr_login.url)
    img.save("telegram_qr.png")
    print("\n💾 QR code also saved as: telegram_qr.png")
    print("(You can open this image and scan it from your phone)\n")

    print("⏳ Waiting for you to scan the QR code...")
    print("   (This will time out after 5 minutes if not scanned)")

    try:
        await qr_login.wait()
        print("\n✅ Successfully authenticated via QR code!")
    except asyncio.TimeoutError:
        print("\n❌ QR code expired. Please run the script again to generate a new one.")
        await client.disconnect()
        return
    except Exception as exc:  # noqa: BLE001
        print(f"\n❌ QR login failed: {type(exc).__name__}: {exc}")
        await client.disconnect()
        return

    # Handle 2FA if needed
    if await client.is_user_authorized():
        print("\n🎉 Authentication complete!")
        me = await client.get_me()
        print(f"Logged in as: {me.first_name or ''} {me.last_name or ''}".strip())
        print(f"Phone: {me.phone}")
        print(f"User ID: {me.id}")
        print(f"\n💾 Session saved locally as: {SESSION_FILE}")
        print("   This file is gitignored and will not be committed.")
    else:
        # Might need 2FA password
        print("\n🔐 Two-factor authentication is required.")
        password = input("Enter your 2FA password: ").strip()
        try:
            await client.sign_in(password=password)
            print("\n✅ Successfully authenticated with 2FA!")
            me = await client.get_me()
            print(f"Logged in as: {me.first_name or ''} {me.last_name or ''}".strip())
            print(f"Phone: {me.phone}")
            print(f"User ID: {me.id}")
            print(f"\n💾 Session saved locally as: {SESSION_FILE}")
        except Exception as exc:  # noqa: BLE001
            print(f"\n❌ 2FA sign-in failed: {type(exc).__name__}: {exc}")
            await client.disconnect()
            return

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
