#!/usr/bin/env python3
"""Test envoi Telethon vers DM avec le bot principal (conversation en cours)."""
import os, sys
sys.path.insert(0, '/home/pi/toth/venv_telethon/lib/python3.13/site-packages')
sys.path.insert(0, '/home/pi/toth/venv_telethon/lib/python3.12/site-packages')

from telethon import TelegramClient
from telethon.tl.types import InputUser

API_ID = 37846858
API_HASH = "0d43866e4c4fb496560e7fa9d900cf09"
SESSION_FILE = "/home/pi/toth/toth_telethon.session"

async def main():
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print("[TEST] Non autorise")
        await client.disconnect()
        return
    
    # Envoyer un message a soi-meme (Saved Messages)
    try:
        await client.send_message("me", "🤖 Test Telethon vers conversation principale")
        print("[TEST] Message envoye avec succes")
    except Exception as e:
        print(f"[TEST] Erreur envoi: {e}")
    
    await client.disconnect()

import asyncio
asyncio.run(main())
