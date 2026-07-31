#!/bin/bash
# Libère les pins GPIO avant le démarrage de Toth
sudo fuser -k /dev/gpiochip0 2>/dev/null
sudo fuser -k /dev/gpiochip4 2>/dev/null
# Reset toutes les pins à 0 puis relâche
for pin in 4 7 8 22 23 24 25 27; do
    timeout 1 sudo gpioset -c gpiochip0 $pin=0 2>/dev/null &
done
wait 2>/dev/null
sleep 0.5
# Tue tout gpioset résiduel
sudo pkill -9 -f "gpioset.*gpiochip0" 2>/dev/null
exit 0
