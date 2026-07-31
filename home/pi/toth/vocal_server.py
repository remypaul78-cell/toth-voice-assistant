#!/usr/bin/env python3
"""Serveur vocal HTTP minimal pour Toth. Recoit du texte et le prononce."""
import sys, os, time, subprocess, json, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

HOST = "0.0.0.0"
PORT = 8070
TMP = "/tmp/toth_http_speech.mp3"

def speak_http(text):
    """Prononce un texte via edge-tts, sans bloquer le main thread."""
    if not text:
        return
    print(f"[VOCAL] Speaking: {text[:80]}...")
    try:
        import asyncio
        from edge_tts import Communicate
        async def s():
            c = Communicate(text, "fr-FR-RemyMultilingualNeural")
            with open(TMP, "wb") as f:
                async for ch in c.stream():
                    if ch["type"] == "audio":
                        f.write(ch["data"])
        asyncio.run(s())
        for dev in ["hw:0,0", "default"]:
            rr = subprocess.run(["mpg123", "-q", "-a", dev, TMP],
                                timeout=60, capture_output=True)
            if rr.returncode == 0:
                print(f"[VOCAL] OK on {dev}")
                return
        print("[VOCAL] Playback failed")
    except Exception as e:
        print(f"[VOCAL] Error: {e}")


class VocalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        text = qs.get("t", [""])[0]
        if text:
            text = urllib.parse.unquote(text)
            threading.Thread(target=speak_http, args=(text,), daemon=True).start()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"vocal server: ?t=hello+world")

    def log_message(self, fmt, *args):
        pass  # silent


def main():
    server = HTTPServer((HOST, PORT), VocalHandler)
    print(f"[VOCAL] Server on {HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
