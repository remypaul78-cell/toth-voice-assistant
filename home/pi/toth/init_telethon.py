#!/usr/bin/env python3
"""Initialise la session Telethon pour Toth."""
import os, sys, time

sys.path.insert(0, '/home/pi/toth/venv_telethon/lib/python3.13/site-packages')
sys.path.insert(0, '/home/pi/toth/venv_telethon/lib/python3.12/site-packages')

from telethon import TelegramClient

API_ID = 37846858
API_HASH = "0d43866e4c4fb496560e7fa9d900cf09"
PHONE = "+33631986089"
SESSION_FILE = "/home/pi/toth/toth_telethon.session"
CODE_FILE = "/tmp/tg_code.txt"

def code_callback():
    print(f"[TELETHON] En attente du code dans {CODE_FILE}...")
    for _ in range(150):  # 5 minutes max
        if os.path.exists(CODE_FILE):
            with open(CODE_FILE, "r") as f:
                code = f.read().strip()
            if code:
                try:
                    os.remove(CODE_FILE)
                except Exception:
                    pass
                print(f"[TELETHON] Code recu: {code}")
                return code
        time.sleep(2)
    raise Exception("Timeout en attente du code")

client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

async def main():
    await client.connect()
    if await client.is_user_authorized():
        print("[TELETHON] Session deja autorisee")
        me = await client.get_me()
        print(f"[TELETHON] Connecte en tant que {me.first_name} @{me.username}")
        return
    print(f"[TELETHON] Envoi du code a {PHONE}")
    await client.send_code_request(PHONE)
    code = code_callback()
    try:
        await client.sign_in(PHONE, code)
    except Exception as e:
        print(f"[TELETHON] Erreur sign_in: {e}")
        raise
    print("[TELETHON] Session creee avec succes")
    me = await client.get_me()
    print(f"[TELETHON] Connecte en tant que {me.first_name} @{me.username}")

with client:
    client.loop.run_until_complete(main())
