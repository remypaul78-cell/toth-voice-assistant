#!/bin/bash
# Surveille les changements de sinks PulseAudio et re-route automatiquement.
LOG=/home/pi/toth/toth_audio_router.log
SINK_INTERNAL="alsa_output.platform-soc_sound.stereo-fallback"

set_default() {
    local sink="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') Audio router: default sink = $sink" >> "$LOG"
    pactl set-default-sink "$sink" && pactl set-sink-volume "$sink" 70%
}

bt_sink() {
    pactl list short sinks | awk '/bluez_sink/ {print $2}' | head -1
}

# Initial route
bt=$(bt_sink)
[ -n "$bt" ] && set_default "$bt" || set_default "$SINK_INTERNAL"

# Listen to PulseAudio events
pactl subscribe 2>&1 | while read -r line; do
    if echo "$line" | grep -qE "sink|card|server"; then
        bt=$(bt_sink)
        current=$(pactl info | grep "Default Sink" | awk '{print $3}')
        if [ -n "$bt" ] && [ "$current" != "$bt" ]; then
            set_default "$bt"
        elif [ -z "$bt" ] && [ "$current" != "$SINK_INTERNAL" ]; then
            set_default "$SINK_INTERNAL"
        fi
    fi
done
