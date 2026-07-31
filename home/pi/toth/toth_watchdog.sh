#!/bin/bash
# Watchdog Toth : verifie service actif + heartbeat recent.
# Au redemarrage, capture l'etat systeme pour diagnostic.
LOG=/var/log/toth_watchdog.log
CAPTURE_DIR=/var/log/toth_crash
mkdir -p "$CAPTURE_DIR"

restart_toth() {
    REASON="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') $REASON — capturing state and restarting" >> "$LOG"
    TS=$(date +%Y%m%d-%H%M%S)
    journalctl -u toth.service -n 200 --no-pager > "$CAPTURE_DIR/toth-$TS.log" 2>&1 || true
    dmesg | tail -100 > "$CAPTURE_DIR/dmesg-$TS.log" 2>&1 || true
    systemctl stop toth.service || true
    rm -rf /home/pi/toth/__pycache__
    systemctl start toth.service
    echo "$(date '+%Y-%m-%d %H:%M:%S') restart done ($REASON)" >> "$LOG"
}

while true; do
    if ! systemctl is-active --quiet toth.service; then
        restart_toth "toth.service inactive"
    elif [ -f /tmp/toth_heartbeat ]; then
        LAST=$(stat -c %Y /tmp/toth_heartbeat 2>&1 || echo 0)
        NOW=$(date +%s)
        AGE=$((NOW - LAST))
        if [ "$AGE" -gt 60 ]; then
            restart_toth "heartbeat stale (${AGE}s)"
        fi
    fi
    sleep 30
done
