#!/bin/bash
# Wrapper pour Toth - charge le .env et lance le script Python
set -e
set -a  # exporte toutes les variables
source /home/pi/.hermes/.env
set +a
exec /usr/bin/python3 /home/pi/toth/toth_chatbot.py
