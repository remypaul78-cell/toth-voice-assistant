#!/usr/bin/env python3
"""Initialise la session Telethon pour Toth (interactif)."""
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
    
    if await client.is_user_authorized():
        print("[TELETHON] Session déjà autorisée")
        me = await client.get_me()
        print(f"[TELETHON] Connecté en tant que {me.first_name} @{me.username}")
        await client.disconnect()
        return
    
    print("[TELETHON] Lancement authentification...")
    await client.start()
    
    print("[TELETHON] Session créée avec succès")
    me = await client.get_me()
    print(f"[TELETHON] Connecté en tant que {me.first_name} @{me.username}")
    await client.disconnect()

import asyncio
asyncio.run(main())
