#!/usr/bin/env python3
"""Watcher Toth — surveille /tmp/toth_announce.txt et vocalise via mpg123"""
import os
import time
import subprocess

ANNOUNCE_FILE = "/tmp/toth_announce.txt"
AUDIO_FILE = "/tmp/toth_voice.mp3"

print("[WATCHER] Démarrage", flush=True)

while True:
    try:
        if os.path.exists(ANNOUNCE_FILE):
            with open(ANNOUNCE_FILE, 'r') as f:
                text = f.read().strip()
            os.remove(ANNOUNCE_FILE)
            
            if not text:
                time.sleep(2)
                continue
            
            print(f"[WATCHER] Annonce: {text[:80]}...", flush=True)
            
            # edge-tts → MP3
            r1 = subprocess.run([
                "/home/pi/.local/bin/edge-tts",
                "--voice", "fr-FR-RemyMultilingualNeural",
                "--text", text,
                "--write-media", AUDIO_FILE
            ], capture_output=True, text=True, timeout=30)
            
            if r1.returncode != 0:
                print(f"[WATCHER] ❌ edge-tts: {r1.stderr[:200]}", flush=True)
                continue
            
            # mpg123 direct
            r2 = subprocess.run(
                ["mpg123", "-q", AUDIO_FILE],
                timeout=15
            )
            
            if r2.returncode == 0:
                print("[WATCHER] ✅ OK", flush=True)
            else:
                print(f"[WATCHER] ❌ mpg123: exit={r2.returncode}", flush=True)
            
            if os.path.exists(AUDIO_FILE):
                os.remove(AUDIO_FILE)
        
        time.sleep(2)
    
    except Exception as e:
        print(f"[WATCHER] Erreur: {e}", flush=True)
        time.sleep(5)
