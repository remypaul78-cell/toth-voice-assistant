#!/usr/bin/env python3
"""Module Telethon minimal pour Toth : envoyer question au bot Hermes, ecouter reponses."""
import os, sys, asyncio, threading, time

VENV = "/home/pi/toth/venv_telethon"
sys.path.insert(0, f"{VENV}/lib/python3.13/site-packages")
sys.path.insert(0, f"{VENV}/lib/python3.12/site-packages")

from telethon import TelegramClient, events

API_ID = 37846858
API_HASH = "0d43866e4c4fb496560e7fa9d900cf09"
SESSION_FILE = "/home/pi/toth/toth_telethon.session"
# Bot Hermes — Toth envoie ici et ecoute les reponses
BOT_ID = 8042301467  # @tothhermestrismegistebot

class TothTelegramBridge:
    def __init__(self, on_reply):
        self.on_reply = on_reply
        self.client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
        self.loop = None
        self.thread = None
        self.last_msg_id = 0
        self.sent_msg_ids = set()  # Track messages we sent to avoid echo
        self.ready = False
        self.expecting_reply = False
        self.reply_session_id = None
        self._question_ts = 0  # timestamp derniere question
        self._min_reply_delay = 2.0  # delai min avant d accepter une reponse (s)
        self._reply_timeout = 120  # apres ce delai, on n attend plus
        self._question_counter = 0  # ID unique par question
        self._tts_playing = False  # True pendant le TTS -- ignorer les messages
        self._vocal_all = False  # Mode vocal total: lire TOUTES les reponses sur Toth
        self._vocal_callback = None  # Callback pour mode vocal total
        self._vocal_queue = []  # Queue pour mode vocal total (messages pendant TTS)
        self._vocal_playing = False  # True pendant le TTS vocal total

    def set_tts_playing(self, val):
        """Pendant le TTS, ignorer les messages Telegram entrants."""
        self._tts_playing = val

    def set_vocal_all(self, enabled, callback=None):
        """Mode vocal total: lire TOUTES les reponses du bot sur les haut-parleurs de Toth."""
        self._vocal_all = enabled
        self._vocal_callback = callback
        if enabled:
            self.expecting_reply = True
        print(f"[TELETHON] Mode vocal total: {'ON' if enabled else 'OFF'}")

    def set_vocal_playing(self, val):
        """Marquer le TTS vocal total comme en cours. Quand il finit, drainer la queue."""
        self._vocal_playing = val
        if not val and self._vocal_queue:
            import threading
            queued = self._vocal_queue.pop(0)
            print(f"[TELETHON] VOCAL TOTAL (drain queue): {queued[:60]}")
            if self._vocal_callback:
                threading.Thread(target=self._vocal_callback, args=(queued,), daemon=True).start()

    def is_vocal_playing(self):
        return self._vocal_playing

    def is_vocal_all(self):
        return self._vocal_all

    def set_expecting(self, session_id=None):
        """Tell bridge we just sent a question and expect a reply."""
        self.expecting_reply = True
        self.reply_session_id = session_id
        self._question_ts = time.time()
        self._question_counter += 1

    def clear_expecting(self):
        self.expecting_reply = False
        self.reply_session_id = None
        self._question_ts = 0

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._async_run())
        except Exception as e:
            print(f"[TELETHON] Run error: {e}")

    async def _async_run(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            print("[TELETHON] Session non autorisee !")
            return
        me = await self.client.get_me()
        print(f"[TELETHON] Connecte: {me.first_name}")
        
        # Handler: ecoute TOUS les messages entrants (pas de filtre chat)
        # On filtre manuellement: ignore nos propres messages, garde ceux du bot
        @self.client.on(events.NewMessage(incoming=True))
        async def handler(event):
            msg = event.message
            sender = await event.get_sender()
            sender_id = msg.sender_id
            
            # Ignorer nos propres messages (Toth envoye via Telethon = compte Remy)
            if sender and getattr(sender, 'is_self', False):
                return
            # Ignorer si c'est un message qu'on a envoye (tracked)
            if msg.id in self.sent_msg_ids:
                return
            if msg.id <= self.last_msg_id:
                return
            self.last_msg_id = msg.id
            
            text = msg.text or ""
            # Filtrer: ne garder que les messages venant du bot Hermes
            if sender_id != BOT_ID:
                return
            
            # Mode vocal total: forwarder TOUS les messages du bot (AVANT tts_playing)
            if self._vocal_all:
                # Filtrer les messages techniques DIRECTEMENT dans le bridge
                _tech = ("💻", "📖", "📚", "⚙️", "🔧", "⚡", "💾", "⚠️", "🔍", "🌐", "📝", "📋", "🔗", "🎬", "🎨", "🔊", "[[audio", "MEDIA:", "⏳", "👁️", "📸", "🎯", "🚀", "🤖", "📊", "✅", "❌", "🎵", "🎸", "🎙️", "🛠️", "📡", "🔔", "💬", "📨", "📜", "🏷️", "📌", "📍", "🧠", "💭", "🧩", "⏰", "🗓️", "⏸️", "▶️", "🔄", "⬆️", "⬇️", "🟢", "🔴", "🟡", "📦", "🧹", "# write_file", "# ", "```", "import ", "from PIL", "from toth", "✏️")
                _err = ("Operation interrupted", "waiting for model", "timed out", "rate limit",
                        "connection refused", "api error", "model response", "elapsed)",
                        "Interrupting current task", "Self-improvement review", "Memory updated",
                        "Still working", "iteration", "vision_analyze", "I'll respond",
                        "sudo journalctl", "ssh -o", "sleep 5")
                if text.strip().startswith(_tech) or any(p.lower() in text.lower() for p in _err):
                    print(f"[TELETHON] VOCAL TOTAL (filtre bridge): {text[:60]}")
                    return
                if self._vocal_playing:
                    print(f"[TELETHON] VOCAL TOTAL (queue + pre-synth): {text[:60]}")
                    self._vocal_queue.append(text)
                    # Pre-synthesize immediately for instant playback when dequeued
                    try:
                        import threading as _th
                        def _do_presynth():
                            try:
                                import re as _re
                                sys.path.insert(0, "/home/pi/toth")
                                from toth_chatbot import _pre_synth_first_batch
                                _pre_synth_first_batch(text)
                            except Exception as e:
                                print(f"[BRIDGE] Pre-synth error: {e}")
                        _th.Thread(target=_do_presynth, daemon=True).start()
                    except Exception:
                        pass
                    return
                print(f"[TELETHON] VOCAL TOTAL: {text[:80]}")
                if self._vocal_callback:
                    self._vocal_callback(text)
                if self.on_reply:
                    self.on_reply(text)
                return
            # Pendant le TTS, ignorer tous les messages (evite dannuler la reponse en cours)
            if self._tts_playing:
                print(f"[TELETHON] Message ignore (TTS en cours): {text[:60]}")
                return
            # Only forward if we are expecting a reply
            if not self.expecting_reply:
                print(f"[TELETHON] Message non attendu (pas en attente): {text[:60]}")
                return
            # Filtrer par timestamp: ne pas accepter de reponse trop rapide (messages intermediaires)
            elapsed = time.time() - self._question_ts
            if elapsed < self._min_reply_delay:
                print(f"[TELETHON] Message trop rapide ({elapsed:.1f}s < {self._min_reply_delay}s): {text[:60]}")
                return
            # Timeout: on n attend plus
            if elapsed > self._reply_timeout:
                print(f"[TELETHON] Timeout ({elapsed:.0f}s > {self._reply_timeout}s): {text[:60]}")
                self.expecting_reply = False
                return
            # Filter technical messages
            tech_prefixes = ("💻", "📖", "🔧", "⚡", "💾", "⚠️", "🔍", "🌐", "📝", "📋", "🔗", "🎬", "🎨", "🔊", "[[audio", "MEDIA:", "⏳")
            if text.strip().startswith(tech_prefixes):
                print(f"[TELETHON] Message technique ignoré: {text[:60]}")
                return
            # Filtrer les messages d erreur Hermes + monitoring de l agent
            error_patterns = ("Operation interrupted", "waiting for model", "timed out",
                              "rate limit", "connection refused", "api error",
                              "model response", "elapsed)", "Interrupting current task",
                              "Self-improvement review", "Memory updated",
                              "Je surveille", "Je verifie", "Je regarde",
                              "Le bridge", "Pas de réponse encore", "Le filtre",
                              "La question est partie", "Le TTS", "Le patch",
                              "sudo journalctl", "ssh -o", "sleep 5",
                              "La réponse n'est pas encore", "bridge attend", "CONTEXT COMPACTION", "Preflight compression", "compaction",
                              "write_file:", "patch_toth", "tesseract", "import ", "from PIL", "import re", "numpy")
            if any(p.lower() in text.lower() for p in error_patterns):
                print(f"[TELETHON] Message erreur/intermediaire ignoré: {text[:60]}")
                return
            print(f"[TELETHON] Reponse bot recue ({elapsed:.1f}s): {text[:80]}")
            # NE PAS remettre expecting_reply = False — continuer a capturer tous les messages
            # jusqu'a la prochaine question (set_expecting reset le flag)
            if self.on_reply:
                self.on_reply(text)
        
        self.ready = True
        print("[TELETHON] Polling reponses actif (listening for bot replies)")
        await self.client.run_until_disconnected()

    def send_question(self, text):
        if not self.ready:
            print("[TELETHON] Pas encore pret, envoi synchrone")
            return self._send_sync(text)
        try:
            # Envoyer au BOT, pas a Remy lui-meme
            future = asyncio.run_coroutine_threadsafe(
                self.client.send_message(BOT_ID, f"🏴‍☠️ Rémy 🏴‍☠️ {text}"),
                self.loop
            )
            # Recuperer le message_id envoye pour l'eviter dans le handler
            sent_msg = future.result(timeout=10)
            if sent_msg:
                self.sent_msg_ids.add(sent_msg.id)
            print(f"[TELETHON] Question envoyee au bot: {text[:60]}")
        except Exception as e:
            print(f"[TELETHON] Erreur envoi: {e}")

    def _send_sync(self, text):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
            client.connect()
            if client.is_user_authorized():
                client.send_message(BOT_ID, f"🏴‍☠️ Rémy 🏴‍☠️ {text}")
                print(f"[TELETHON-SYNC] Question envoyee au bot: {text[:60]}")
            client.disconnect()
        except Exception as e:
            print(f"[TELETHON-SYNC] Erreur: {e}")

if __name__ == "__main__":
    def cb(text):
        print(f"[CB] {text[:80]}")
    b = TothTelegramBridge(cb)
    b.start()
    time.sleep(5)
    b.send_question("Test module Telethon — tu me reçois ?")
    time.sleep(30)