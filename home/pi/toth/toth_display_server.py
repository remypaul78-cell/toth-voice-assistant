#!/usr/bin/env python3
"""
toth_display_server.py
Mini serveur HTTP pour l'ecran tactile ESP32-S3 de Toth.
Reçoit tap / swipe via HTTP POST et route vers toth_chatbot.py.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "0.0.0.0"
PORT = 5000

# Reference a l'instance Toth injectee par toth_chatbot.py
_toth_instance = None


def set_toth_instance(inst):
    global _toth_instance
    _toth_instance = inst


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/action":
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = self.rfile.read(length).decode("utf-8")
            data = json.loads(payload)
        except Exception as e:
            self._json(400, {"error": f"bad json: {e}"})
            return

        action = data.get("action")
        item = data.get("item")
        direction = data.get("dir")
        source = data.get("source", "display")

        if _toth_instance is None:
            self._json(503, {"error": "toth not ready"})
            return

        try:
            text = _toth_instance.handle_display_action(action, item, direction, source=source)
            self._json(200, {"ok": True, "text": text})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_GET(self):
        if self.path == "/ping":
            self._json(200, {"ok": True, "toth_ready": _toth_instance is not None})
        elif self.path.startswith("/show_photo"):
            import urllib.parse
            params = urllib.parse.parse_qs(self.path.split("?", 1)[-1] if "?" in self.path else "")
            photo_path = params.get("path", [None])[0]
            if not photo_path or _toth_instance is None:
                self._json(400, {"error": "missing path or toth not ready"})
                return
            try:
                _toth_instance.show_photo(photo_path)
                self._json(200, {"ok": True, "path": photo_path})
            except Exception as e:
                self._json(500, {"error": str(e)})
        else:
            self._json(404, {"error": "not found"})


def start_server():
    server = HTTPServer((HOST, PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"[TOTH_DISPLAY] HTTP server on {HOST}:{PORT}")
    return server


if __name__ == "__main__":
    print("Run this module from toth_chatbot.py, not standalone.")