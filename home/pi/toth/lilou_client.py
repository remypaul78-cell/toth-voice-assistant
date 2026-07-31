#!/usr/bin/env python3
"""Client Lilou pour Toth — Pi Zero 2W.

Pousse/récupère les souvenirs du Palais de Lilou (MemPalace) via l'API
HTTP du VPS. Aucun modèle local, aucune DB locale — juste des
requêtes HTTP légères.
"""

import json, os, urllib.request, urllib.error

LILOU_HOST = os.getenv("LILOU_HOST", "49.13.237.85")
LILOU_PORT = int(os.getenv("LILOU_PORT", "8082"))
LILOU_KEY  = os.getenv("LILOU_KEY", "toth-lilou-key-2026")
LILOU_URL  = f"http://{LILOU_HOST}:{LILOU_PORT}"

# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------

def _req(path, payload=None, method="POST"):
    url = f"{LILOU_URL}{path}"
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method,
                                  headers={"Content-Type": "application/json",
                                           "X-Lilou-Key": LILOU_KEY})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode(), "status": e.code}
    except Exception as e:
        return {"error": str(e)}

# ------------------------------------------------------------------
# public API — à appeler depuis toth_chatbot.py
# ------------------------------------------------------------------

def remember(text: str, room: str = "toth-memoire", wing: str = "toth") -> str:
    """Stocke un souvenir dans Lilou. Retourne le drawer_id ou 'KO'."""
    r = _req("/add", {"wing": wing, "room": room, "content": text})
    return r.get("drawer_id", "KO") if "drawer_id" in r else str(r.get("error", "KO"))


def recall(query: str, limit: int = 3, room: str = None, wing: str = "toth") -> list:
    """Recherche sémantique dans Lilou. Retourne liste de dicts {content, score, room}."""
    payload = {"query": query, "limit": limit, "wing": wing}
    if room:
        payload["room"] = room
    r = _req("/search", payload)
    if "results" in r:
        return r["results"]
    return []


def recent(limit: int = 5, wing: str = "toth", room: str = None) -> list:
    """Derniers souvenirs stockés (chronologique)."""
    payload = {"limit": limit, "wing": wing}
    if room:
        payload["room"] = room
    r = _req("/recent", payload)
    return r.get("results", [])


def diary_write(entry: str, topic: str = "toth") -> str:
    """Écrit dans le journal de Lilou."""
    r = _req("/diary", {"entry": entry, "topic": topic, "agent_name": "toth"})
    return r.get("status", "KO")


if __name__ == "__main__":
    # test rapide
    print("[LILOU] Test remember…")
    print(remember("Test connexion depuis Toth à " + LILOU_URL))
    print("[LILOU] Test recall…")
    print(recall("test connexion"))
