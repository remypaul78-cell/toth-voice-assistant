#!/usr/bin/env python3
"""Client Telegram utilisateur pour Toth via Telethon.
Envoie les questions vers 'Messages enregistres' (routes vers le DM principal par Hermes)
et poll les reponses.
"""
import asyncio, threading, json, os, time
import sys
sys.path.insert(0, '/home/pi/toth/venv_telethon/lib/python3.13/site-packages')
sys.path.insert(0, '/home/pi/toth/venv_telethon/lib/python3.12/site-packages')

from telethon import TelegramClient, events

API_ID = 37846858
API_HASH = "0d43866e4c4fb496560e7fa9d900cf09"
SESSION_FILE = "/home/pi/toth/toth_telethon.session"

class TothTelegramUser:
    def __init__(self, on_reply=None):
        self.on_reply = on_reply
        self.client = None
        self.loop = None
        self.thread = None
        self._ready = False

    def _run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
        
        @self.client.on(events.NewMessage)
        async def handler(event):
            sender = await event.get_sender()
            me = await self.client.get_me()
            # On ne garde que les messages recus dans 'Messages enregistres' (chat avec soi-meme)
            if sender and sender.id == me.id and event.is_private:
                text = event.raw_text or ""
                # Ignorer les messages envoyes par Toth lui-meme
                if text.startswith("🏴‍☠️ Rémy 🏴‍☠️"):
                    return
                print(f"[TG-USER] Reponse recue: {text[:60]}")
                if self.on_reply:
                    self.on_reply(text)
        
        async def start():
            await self.client.connect()
            if not await self.client.is_user_authorized():
                print("[TG-USER] Non autorise")
                return
            self._ready = True
            me = await self.client.get_me()
            print(f"[TG-USER] Pret: {me.first_name}")
            await self.client.run_until_disconnected()
        
        self.loop.run_until_complete(start())

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def send_question(self, text):
        def _send():
            async def async_send():
                try:
                    await self.client.send_message("me", f"🏴‍☠️ Rémy 🏴‍☠️ {text}")
                    print(f"[TG-USER] Question envoyee: {text[:60]}")
                except Exception as e:
                    print(f"[TG-USER] Erreur envoi: {e}")
            if self.loop and self._ready:
                asyncio.run_coroutine_threadsafe(async_send(), self.loop)
            else:
                print("[TG-USER] Client pas pret")
        threading.Thread(target=_send, daemon=True).start()

    def stop(self):
        if self.loop and self.client:
            async def _disc():
                await self.client.disconnect()
            try:
                asyncio.run_coroutine_threadsafe(_disc(), self.loop)
            except Exception:
                pass

if __name__ == "__main__":
    def cb(text):
        print(f"[MAIN] Reply: {text[:60]}")
    t = TothTelegramUser(on_reply=cb)
    t.start()
    time.sleep(5)
    t.send_question("test depuis module telethon")
    time.sleep(30)
    t.stop()
