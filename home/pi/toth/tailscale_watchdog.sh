#!/bin/bash
# Tailscale watchdog for Toth - checks connection every 60s, restarts if down
VPS_IP="100.99.52.89"
LOG="/home/pi/toth/logs/tailscale_watchdog.log"
mkdir -p "$(dirname "$LOG")"

while true; do
    if ! ping -c 1 -W 5 "$VPS_IP" >/dev/null 2>&1; then
        echo "$(date): Tailscale down, restarting..." >> "$LOG"
        sudo tailscale down 2>/dev/null
        sleep 2
        sudo tailscale up --accept-routes --accept-dns 2>/dev/null
        sleep 10
        if ping -c 1 -W 5 "$VPS_IP" >/dev/null 2>&1; then
            echo "$(date): Tailscale recovered" >> "$LOG"
        else
            echo "$(date): Tailscale still down after restart" >> "$LOG"
        fi
    fi
    sleep 60
done