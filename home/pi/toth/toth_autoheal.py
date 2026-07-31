#!/usr/bin/env python3
"""Toth Auto-Heal Daemon — watchdog des services critiques.
Surveille et redémarre automatiquement toth.service, watcher_v2, flag vocal, connectivité SSH.
Reboot automatique après 3 échecs consécutifs du service toth.
Cible : Pi Zero 2W — /home/pi/toth/toth_autoheal.py"""

import subprocess
import time
import os
from datetime import datetime

LOG = "/var/log/toth_autoheal.log"
MAX_LOG_LINES = 3000
TRUNCATE_TO = 2000
CHECK_INTERVAL = 30
SSH_TIMEOUT = 10
MAX_CONSECUTIVE_FAILS = 3

VPS_IP = "49.13.237.85"
SSH_KEY = "/home/pi/.ssh/id_ed25519"
WATCHER_SCRIPT = "/home/pi/toth/watcher_v2.py"


def log(msg: str):
    """Écrire un message horodaté dans le fichier de log."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        with open(LOG, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass  # si on peut pas logger, on abandonne silencieusement


def rotate_log():
    """Tronquer le log s'il dépasse MAX_LOG_LINES."""
    try:
        if not os.path.exists(LOG):
            return
        with open(LOG, "r") as f:
            lines = f.readlines()
        if len(lines) > MAX_LOG_LINES:
            with open(LOG, "w") as f:
                f.writelines(lines[-TRUNCATE_TO:])
    except Exception:
        pass


def run(cmd: list[str], timeout: int = SSH_TIMEOUT) -> tuple[bool, str]:
    """Exécuter une commande, retourner (succès, stdout)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


# --- Checks individuels ---

def check_toth_service() -> bool:
    """Vérifier que toth.service est actif. Retourne True si OK."""
    ok, out = run(["systemctl", "is-active", "toth"], timeout=5)
    if ok and out == "active":
        return True
    log(f"TOTH SERVICE DOWN (status={out}) — tentative restart...")
    ok2, out2 = run(["sudo", "systemctl", "restart", "toth"], timeout=15)
    if ok2:
        log("TOTH SERVICE RESTARTED")
        return True
    else:
        log(f"TOTH SERVICE RESTART FAILED: {out2}")
        return False


def check_watcher() -> bool:
    """Vérifier que watcher_v2.py tourne. Retourne True si OK (ou relancé)."""
    ok, out = run(["pgrep", "-f", "watcher_v2.py"], timeout=5)
    if ok and out.strip():
        return True
    log("WATCHER v2 DOWN — relance...")
    # Lancer en background depuis le dossier de pi
    ok2, out2 = run([
        "nohup", "python3", WATCHER_SCRIPT,
    ], timeout=5)
    # nohup rend toujours 0, on vérifie après un court délai
    time.sleep(2)
    ok3, _ = run(["pgrep", "-f", "watcher_v2.py"], timeout=5)
    if ok3:
        log("WATCHER v2 RESTARTED")
        return True
    else:
        log(f"WATCHER v2 RESTART FAILED")
        return False


def check_ssh() -> bool:
    """Vérifier la connectivité SSH vers le VPS. Log uniquement."""
    ok, out = run([
        "ssh", "-o", "ConnectTimeout=5",
        "-o", "StrictHostKeyChecking=no",
        "-i", SSH_KEY,
        f"pi@{VPS_IP}", "hostname"
    ], timeout=SSH_TIMEOUT)
    if ok:
        return True
    else:
        log(f"SSH VPS DOWN ({out[:80]})")
        return False


def check_vocal_flag():
    """Recréer /tmp/toth_vocal_enabled si absent."""
    flag = "/tmp/toth_vocal_enabled"
    if not os.path.exists(flag):
        try:
            open(flag, "w").close()
            log("VOCAL FLAG RECREATED")
        except Exception as e:
            log(f"VOCAL FLAG FAILED: {e}")


def reboot_system():
    """Rebooter le Pi Zero après log."""
    log("REBOOT: 3 échecs consécutifs toth.service → sudo reboot")
    run(["sudo", "reboot"], timeout=5)


# --- Boucle principale ---

def main():
    rotate_log()
    log("=" * 40)
    log("TOTH AUTO-HEAL DAEMON STARTED")
    log(f"Check interval={CHECK_INTERVAL}s, max fails={MAX_CONSECUTIVE_FAILS}, VPS={VPS_IP}")

    toth_fails = 0  # compteur persistant, hors try/except

    while True:
        try:
            # 1. Service toth
            if check_toth_service():
                toth_fails = 0
            else:
                toth_fails += 1
                log(f"TOTH FAIL COUNT: {toth_fails}/{MAX_CONSECUTIVE_FAILS}")
                if toth_fails >= MAX_CONSECUTIVE_FAILS:
                    reboot_system()
                    # Si le reboot ne part pas immédiatement, on sort
                    time.sleep(60)
                    continue

            # 2. Watcher v2
            check_watcher()

            # 3. Connectivité SSH VPS
            check_ssh()

            # 4. Flag vocal
            check_vocal_flag()

        except Exception as e:
            log(f"GLOBAL ERROR: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
