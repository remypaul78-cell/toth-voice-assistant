#!/bin/bash
set -e

TOTH_FILE="/home/pi/toth/toth_chatbot.py"
BACKUP_FILE="/home/pi/toth/toth_chatbot.py.bak-auto-send-mod"

echo "Creating backup: $BACKUP_FILE"
cp "$TOTH_FILE" "$BACKUP_FILE"

echo "Applying modifications..."

# Supprimer les lignes du timeout dans _record()
# Lignes 1263-1264
sed -i '1263,1264d' "$TOTH_FILE"

# Dans la section d'erreur, garder seulement os.remove sans _cancel_record_timeout
# Lignes 1265-1268 avant: 
#  if not self.rec.start(self._on_live_text):
#      self._cancel_record_timeout()
#      try: os.remove("/tmp/toth_recording")
#      except OSError: pass
# Après: 
#  if not self.rec.start(self._on_live_text):
#      try: os.remove("/tmp/toth_recording")
#      except OSError: pass
# On remplace les 4 lignes (1265-1268) par 3 lignes sans _cancel_record_timeout
sed -i '1265,1268c\        if not self.rec.start(self._on_live_text):\n            try: os.remove(\"/tmp/toth_recording\")\n            except OSError: pass' "$TOTH_FILE"

# Supprimer self._cancel_record_timeout() dans _process() à la ligne ~1306
# Trouvons la ligne exacte
if grep -n "self._cancel_record_timeout()  # annule le timeout si arrêt manuel" "$TOTH_FILE"; then
    LINE=$(grep -n "self._cancel_record_timeout()  # annule le timeout si arrêt manuel" "$TOTH_FILE" | cut -d: -f1)
    echo "Found self._cancel_record_timeout() at line $LINE"
    sed -i "${LINE}d" "$TOTH_FILE"
else
    echo "WARNING: Could not find self._cancel_record_timeout() in _process()"
fi

# Trouver et supprimer la méthode _cancel_record_timeout() 
if grep -n "def _cancel_record_timeout" "$TOTH_FILE"; then
    START_LINE=$(grep -n "def _cancel_record_timeout" "$TOTH_FILE" | cut -d: -f1)
    echo "Found _cancel_record_timeout at line $START_LINE"
    # Trouver où elle finit (première ligne vide après les 6 lignes suivantes)
    END_LINE=$((START_LINE + 6))
    while [ $END_LINE -lt $(wc -l < "$TOTH_FILE") ] && [[ ! $(sed -n "${END_LINE}p" "$TOTH_FILE") =~ ^[[:space:]]*$ ]]; do
        END_LINE=$((END_LINE + 1))
    done
    echo "Deleting lines $START_LINE to $END_LINE"
    sed -i "${START_LINE},${END_LINE}d" "$TOTH_FILE"
else
    echo "WARNING: Could not find _cancel_record_timeout method"
fi

# Trouver et supprimer la méthode _record_timeout_cb()
if grep -n "def _record_timeout_cb" "$TOTH_FILE"; then
    START_LINE=$(grep -n "def _record_timeout_cb" "$TOTH_FILE" | cut -d: -f1)
    echo "Found _record_timeout_cb at line $START_LINE"
    # Trouver où elle finit (première ligne vide après les 4 lignes suivantes)
    END_LINE=$((START_LINE + 4))
    while [ $END_LINE -lt $(wc -l < "$TOTH_FILE") ] && [[ ! $(sed -n "${END_LINE}p" "$TOTH_FILE") =~ ^[[:space:]]*$ ]]; do
        END_LINE=$((END_LINE + 1))
    done
    echo "Deleting lines $START_LINE to $END_LINE"
    sed -i "${START_LINE},${END_LINE}d" "$TOTH_FILE"
else
    echo "WARNING: Could not find _record_timeout_cb method"
fi

# Vérifier que MAX_RECORD_SEC peut être gardé ou commenté
echo "Checking if MAX_RECORD_SEC is still referenced..."
if grep -n "MAX_RECORD_SEC" "$TOTH_FILE" | grep -v "^24:" | grep -v "^1262:"; then
    echo "WARNING: MAX_RECORD_SEC still referenced elsewhere!"
else
    echo "MAX_RECORD_SEC only referenced in comments and definition, keeping it."
fi

echo "Patch applied successfully!"
echo "Checking for leftover references to _record_timeout..."
grep -n "_record_timeout" "$TOTH_FILE" || echo "No leftover references found."

echo "Checking for leftover references to _cancel_record_timeout..."
grep -n "_cancel_record_timeout" "$TOTH_FILE" || echo "No leftover references found."

echo "Checking for leftover references to _record_timeout_cb..."
grep -n "_record_timeout_cb" "$TOTH_FILE" || echo "No leftover references found."