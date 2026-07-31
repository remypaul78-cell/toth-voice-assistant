#!/bin/bash
# sd_card_sync.sh — Détecte une carte SD USB, monte la partition root,
# sync les fichiers critiques depuis le Pi, démonte, notifie Telegram.
# Déclenché par udev (insertion USB) ou manuellement.

set -e

LOG="/tmp/sd_card_sync.log"
TG_TOKEN=$(cat /home/pi/toth/config.json | python3 -c "import sys,json; print(json.load(sys.stdin).get(\"telegram_bot_token\",\"\"))" 2>/dev/null)
TG_CHAT=$(cat /home/pi/toth/config.json | python3 -c "import sys,json; print(json.load(sys.stdin).get(\"telegram_chat_id\",\"\"))" 2>/dev/null)

notify() {
    echo "[$(date '+%H:%M:%S')] $1" >> "$LOG"
    if [ -n "$TG_TOKEN" ] && [ -n "$TG_CHAT" ]; then
        curl -s -X POST "https://api.telegram.org/bot$TG_TOKEN/sendMessage" \
            -d "chat_id=$TG_CHAT" -d "text=$1" > /dev/null 2>&1
    fi
}

# Détecter la carte USB (le device le plus récent avec une partition Linux)
CARD=""
for dev in /dev/sda /dev/sdb /dev/sdc; do
    if [ -b "$dev" ] && lsblk "$dev" -o TYPE,FSTYPE -n 2>/dev/null | grep -q "vfat\|ext4"; then
        # Vérifier que ce n'est pas mmcblk0 (carte interne)
        if [[ "$dev" != "/dev/mmcblk0"* ]]; then
            CARD="$dev"
            break
        fi
    fi
done

if [ -z "$CARD" ]; then
    notify "sd_card_sync: aucune carte USB détectée"
    exit 1
fi

notify "🔄 Carte détectée: $CARD — sync en cours..."

# Trouver la partition root (ext4 ou la plus grosse)
ROOT_PART=""
for part in ${CARD}1 ${CARD}2 ${CARD}p1 ${CARD}p2; do
    FSTYPE=$(lsblk "$part" -o FSTYPE -n 2>/dev/null)
    if [ "$FSTYPE" = "ext4" ]; then
        ROOT_PART="$part"
        break
    fi
done

# Si pas ext4 trouvé, prendre la 2e partition (souvent root sur Raspberry Pi)
if [ -z "$ROOT_PART" ]; then
    if [ -b "${CARD}2" ]; then
        ROOT_PART="${CARD}2"
    elif [ -b "${CARD}p2" ]; then
        ROOT_PART="${CARD}p2"
    else
        notify "❌ Pas de partition root trouvée sur $CARD"
        exit 1
    fi
fi

MOUNT_POINT="/mnt/sd_sync"
mkdir -p "$MOUNT_POINT"

# Monter
if ! sudo mount -o rw "$ROOT_PART" "$MOUNT_POINT" 2>>"$LOG"; then
    notify "❌ Impossible de monter $ROOT_PART"
    exit 1
fi

notify "📂 Monté $ROOT_PART sur $MOUNT_POINT"

SYNCED=0
FAILED=0

# Synchroniser chaque chemin du manifeste
while IFS= read -r line; do
    # Ignorer commentaires et lignes vides
    [[ "$line" =~ ^# ]] && continue
    [ -z "$line" ] && continue
    
    SRC="$line"
    # Construire le chemin destination
    if [[ "$SRC" == /home/pi/* ]]; then
        DST="$MOUNT_POINT${SRC}"
    elif [[ "$SRC" == /etc/* ]]; then
        DST="$MOUNT_POINT${SRC}"
    elif [[ "$SRC" == /boot/* ]]; then
        DST="$MOUNT_POINT${SRC}"
    else
        DST="$MOUNT_POINT${SRC}"
    fi
    
    # Créer le dossier parent
    sudo mkdir -p "$(dirname "$DST")" 2>/dev/null
    
    # rsync
    if sudo rsync -a --delete "$SRC" "$DST" 2>>"$LOG"; then
        SYNCED=$((SYNCED+1))
    else
        FAILED=$((FAILED+1))
        notify "  ⚠️ Échec sync: $SRC"
    fi
done < /home/pi/toth/sd_card_sync_manifest.txt

# Démonter
sudo sync
sudo umount "$MOUNT_POINT" 2>/dev/null

if [ $FAILED -eq 0 ]; then
    notify "✅ Carte syncée: $SYNCED chemins copiés. Tu peux la retirer."
else
    notify "⚠️ Sync terminé: $SYNCED OK, $FAILED échecs. Voir log."
fi
