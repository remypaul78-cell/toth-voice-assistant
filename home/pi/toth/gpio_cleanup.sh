#!/bin/bash
# gpio_cleanup.sh — Libère les GPIO occupés par des processus zombies
# Lancé par systemd ExecStartPre avant toth.service

LOG_TAG='gpio-cleanup'

# Liste des gpiochip utilisés par Toth (Pi Zero = gpiochip0, Pi 5 = gpiochip4)
CHIPS='/dev/gpiochip0 /dev/gpiochip4'

for chip in $CHIPS; do
    if [ -e "$chip" ]; then
        PIDS=$(fuser "$chip" 2>/dev/null)
        if [ -n "$PIDS" ]; then
            logger -t $LOG_TAG "Releasing $chip held by PIDs: $PIDS"
            fuser -k "$chip" 2>/dev/null
            sleep 0.5
        fi
    fi
done

# Tuer aussi les processus python zombies sur toth_chatbot
ZOMBIES=$(pgrep -f 'toth_chatbot.py' 2>/dev/null)
if [ -n "$ZOMBIES" ]; then
    logger -t $LOG_TAG "Killing zombie toth processes: $ZOMBIES"
    kill -9 $ZOMBIES 2>/dev/null
    sleep 0.5
fi

logger -t $LOG_TAG 'GPIO cleanup done'
exit 0
