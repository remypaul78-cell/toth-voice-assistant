#!/bin/bash
# Auto-connect AirPods at boot
# Waits for Bluetooth to be ready, then connects

AIRPODS_MAC="E4:90:FD:E3:4A:D3"
MAX_ATTEMPTS=10
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    
    # Check if already connected
    if bluetoothctl info "$AIRPODS_MAC" 2>/dev/null | grep -q "Connected: yes"; then
        echo "AirPods déjà connectés"
        exit 0
    fi
    
    # Try to connect
    echo "Tentative $ATTEMPT/$MAX_ATTEMPTS de connexion AirPods..."
    echo -e "connect $AIRPODS_MAC" | bluetoothctl 2>/dev/null
    
    sleep 3
    
    if bluetoothctl info "$AIRPODS_MAC" 2>/dev/null | grep -q "Connected: yes"; then
        echo "AirPods connectés !"
        paplay /usr/share/sounds/alsa/Front_Center.wav 2>/dev/null
        exit 0
    fi
    
    echo "Pas encore connectés, attente..."
done

echo "AirPods non trouvés après $MAX_ATTEMPTS tentatives"
exit 1
