#!/usr/bin/env python3
"""Test envoi de message via Telethon depuis Toth vers DM principal."""
import os, sys
sys.path.insert(0, '/home/pi/toth/venv_telethon/lib/python3.13/site-packages')
sys.path.insert(0, '/home/pi/toth/venv_telethon/lib/python3.12/site-packages')

from telethon import TelegramClient

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
    me = await client.get_me()
    print(f"[TEST] Connecte: {me.first_name} @{me.username}")
    
    # Envoyer un message a soi-meme (DM saved messages / chat_id 5754223758)
    try:
        await client.send_message(5754223758, "🤖 Test envoi Telethon depuis Toth")
        print("[TEST] Message envoye avec succes")
    except Exception as e:
        print(f"[TEST] Erreur envoi: {e}")
    
    await client.disconnect()

import asyncio
asyncio.run(main())
