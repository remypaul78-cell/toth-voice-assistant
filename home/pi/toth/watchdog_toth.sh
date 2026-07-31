#!/bin/bash
# Vérifie que Toth tourne, le relance si besoin
if ! pgrep -f "toth_chatbot.py" > /dev/null; then
    echo "[$(date)] Toth down — restarting" >> /home/pi/toth/toth_watchdog.log
    /home/pi/toth/start_toth.sh &
fi
