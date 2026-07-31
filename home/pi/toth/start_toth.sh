#!/bin/bash
# Wrapper pour lancer Toth avec reset GPIO préalable + retry
amixer -c 0 sset "Left Input Boost Mixer LINPUT1" 2
amixer -c 0 sset "Right Input Boost Mixer RINPUT1" 2
amixer -c 0 sset "Capture" 50
amixer -c 0 sset "Left Input Mixer Boost" on
amixer -c 0 sset "Right Input Mixer Boost" on
amixer -c 0 sset "Left Output Mixer PCM" on
amixer -c 0 sset "Right Output Mixer PCM" on
amixer -c 0 sset Headphone 127
LOGFILE=/home/pi/toth/toth_wrapper.log
echo "[$(date)] Demarrage Toth wrapper..." >> $LOGFILE

# 1. Tuer les process toth zombies AVANT tout
sudo pkill -9 -f "toth_chatbot.py" 2>/dev/null
sleep 1

# 2. liberer les GPIOs
sudo fuser -k /dev/gpiochip0 2>/dev/null
sudo fuser -k /dev/gpiochip4 2>/dev/null
for pin in 4 7 8 22 23 24 25 27; do
    timeout 1 sudo gpioset -c gpiochip0 $pin=0 2>/dev/null &
done
wait 2>/dev/null
sudo pkill -9 -f "gpioset.*gpiochip" 2>/dev/null
sleep 2
echo "[$(date)] GPIO reset done" >> $LOGFILE

# 3. Wipe pycache
rm -rf /home/pi/toth/__pycache__/* /home/pi/whisplay/runtime/__pycache__/* 2>/dev/null

# 4. Lancer Toth avec retry si GPIO busy
cd /home/pi/toth
MAX_RETRIES=3
for i in $(seq 1 $MAX_RETRIES); do
    nohup /usr/bin/python3 -u toth_chatbot.py >> $LOGFILE 2>&1 &
    PID=$!
    echo "[$(date)] Toth lance PID=$PID (essai $i/$MAX_RETRIES)" >> $LOGFILE
    sleep 5
    if ! kill -0 $PID 2>/dev/null; then
        echo "[$(date)] Crash detecte, retry..." >> $LOGFILE
        sudo fuser -k /dev/gpiochip0 2>/dev/null
        sleep 2
    else
        echo "[$(date)] Toth OK (PID=$PID)" >> $LOGFILE
        break
    fi
done
