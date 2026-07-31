#!/usr/bin/env python3
"""Watcher Toth v2 — vocalise /tmp/toth_announce.txt via mpg123
Mode vocal : contrôlé par /tmp/toth_vocal_enabled
  - Flag présent → vocalise TOUTES les annonces (mode permanent)
  - Flag absent  → NE vocalise PAS (mode silence, Toth gère ses propres réponses)
"""
import os
import time
import subprocess

ANNOUNCE_FILE = "/tmp/toth_announce.txt"
AUDIO_FILE = "/tmp/toth_voice.mp3"
VOCAL_FLAG = "/tmp/toth_vocal_enabled"

print("[WATCHER v2] Démarrage", flush=True)

while True:
    try:
        if os.path.exists(ANNOUNCE_FILE):
            with open(ANNOUNCE_FILE, 'r') as f:
                text = f.read().strip()
            os.remove(ANNOUNCE_FILE)
            
            if not text:
                time.sleep(2)
                continue
            
            vocal_on = os.path.exists(VOCAL_FLAG)
            recording = os.path.exists("/tmp/toth_recording")
            if recording:
                print(f"[WATCHER v2] ⏸️  Enregistrement en cours — attente...", flush=True)
                for _ in range(60):  # attendre max 2 min
                    if not os.path.exists("/tmp/toth_recording"):
                        print(f"[WATCHER v2] ✅ Enregistrement fini, on vocalise", flush=True)
                        time.sleep(1)
                        break
                    time.sleep(2)
                else:
                    print(f"[WATCHER v2] ⚠️  Timeout attente enregistrement, on force", flush=True)
                vocal_on = os.path.exists(VOCAL_FLAG)  # re-check au cas où
            
            if not vocal_on:
                print(f"[WATCHER v2] 🔇 Vocal OFF — annonce ignorée: {text[:60]}...", flush=True)
                time.sleep(2)
                continue
            
            print(f"[WATCHER v2] 🔊 Annonce: {text[:80]}...", flush=True)
            
            # Générer audio edge-tts → MP3
            r1 = subprocess.run([
                "/home/pi/.local/bin/edge-tts",
                "--voice", "fr-FR-HenriNeural",
                "--text", text,
                "--write-media", AUDIO_FILE
            ], capture_output=True, text=True, timeout=30)
            
            if r1.returncode != 0:
                print(f"[WATCHER v2] ❌ edge-tts: {r1.stderr[:200]}", flush=True)
                continue
            
            # Jouer via mpg123
            r2 = subprocess.run(["mpg123", "-q", AUDIO_FILE], timeout=15)
            
            if r2.returncode == 0:
                print("[WATCHER v2] ✅ OK", flush=True)
            else:
                print(f"[WATCHER v2] ❌ mpg123: exit={r2.returncode}", flush=True)
            
            if os.path.exists(AUDIO_FILE):
                os.remove(AUDIO_FILE)
        
        time.sleep(2)
    
    except Exception as e:
        print(f"[WATCHER v2] Erreur: {e}", flush=True)
        time.sleep(5)
