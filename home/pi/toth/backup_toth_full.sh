#!/bin/bash
# =============================================================================
# BACKUP COMPLET DU SYSTÈME TOTH
# Sauvegarde TOUT ce qu'il faut pour reconstruire le Pi à l'identique.
# À lancer régulièrement (cron ou manuel).
# Génère un tar.gz horodaté.
# =============================================================================
set -euo pipefail

BACKUP_DIR="${1:-/home/pi/toth_backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/toth_full_backup_$TIMESTAMP.tar.gz"
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "=== Sauvegarde complète Toth ==="
echo "Timestamp: $TIMESTAMP"
echo "Backup dir: $BACKUP_DIR"
echo "Temp: $TEMP_DIR"

mkdir -p "$BACKUP_DIR" "$TEMP_DIR/systemd" "$TEMP_DIR/systemd_user" \
         "$TEMP_DIR/configs" "$TEMP_DIR/ssh" "$TEMP_DIR/hermes" \
         "$TEMP_DIR/packages"

# ── 1. Toth (sans venv ni pycache) ──────────────────────────────────────
echo "[1/10] Sauvegarde Toth..."
rsync -a --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
      /home/pi/toth/ "$TEMP_DIR/toth/"

# ── 2. Whisplay ─────────────────────────────────────────────────────────
echo "[2/10] Sauvegarde Whisplay..."
if [ -d /home/pi/whisplay ]; then
    rsync -a --exclude='__pycache__' --exclude='*.pyc' \
          /home/pi/whisplay/ "$TEMP_DIR/whisplay/"
fi

# ── 3. Hermes configs ───────────────────────────────────────────────────
echo "[3/10] Sauvegarde config Hermes..."
cp /home/pi/.hermes/config.yaml "$TEMP_DIR/hermes/"
cp /home/pi/.hermes/.env "$TEMP_DIR/hermes/" 2>/dev/null || true
cp /home/pi/.hermes/SOUL.md "$TEMP_DIR/hermes/" 2>/dev/null || true
cp /home/pi/.hermes/auth.json "$TEMP_DIR/hermes/" 2>/dev/null || true
cp /home/pi/.hermes/channel_directory.json "$TEMP_DIR/hermes/" 2>/dev/null || true

# Mémoires
if [ -f /home/pi/.hermes/memories/MEMORY.md ]; then
    cp /home/pi/.hermes/memories/MEMORY.md "$TEMP_DIR/hermes/"
fi
if [ -f /home/pi/.hermes/memories/USER.md ]; then
    cp /home/pi/.hermes/memories/USER.md "$TEMP_DIR/hermes/"
fi

# Cron jobs
cp /home/pi/.hermes/cron/jobs.json "$TEMP_DIR/hermes/" 2>/dev/null || true

# Custom scripts
if [ -d /home/pi/.hermes/scripts ]; then
    rsync -a /home/pi/.hermes/scripts/ "$TEMP_DIR/hermes/scripts/"
fi

# Custom skills (only user-created, not bundled)
if [ -d /home/pi/.hermes/skills ]; then
    mkdir -p "$TEMP_DIR/hermes/skills"
    # Sauvegarde que les skills customs (ceux avec SKILL.md, pas juste DESCRIPTION.md)
    for d in /home/pi/.hermes/skills/*/; do
        skill_name=$(basename "$d")
        if [ -f "$d/SKILL.md" ]; then
            rsync -a "$d" "$TEMP_DIR/hermes/skills/$skill_name/"
        fi
    done
fi

# Pairing info
if [ -d /home/pi/.hermes/pairing ]; then
    rsync -a /home/pi/.hermes/pairing/ "$TEMP_DIR/hermes/pairing/"
fi

# Gateway config
cp /home/pi/.hermes/gateway_state.json "$TEMP_DIR/hermes/" 2>/dev/null || true

# ── 4. Clés SSH ─────────────────────────────────────────────────────────
echo "[4/10] Sauvegarde clés SSH..."
rsync -a /home/pi/.ssh/ "$TEMP_DIR/ssh/"

# ── 5. Services systemd ─────────────────────────────────────────────────
echo "[5/10] Sauvegarde services systemd..."
for svc in toth toth-watchdog autossh-tonton whatsapp-bot; do
    if [ -f "/etc/systemd/system/$svc.service" ]; then
        cp "/etc/systemd/system/$svc.service" "$TEMP_DIR/systemd/"
    fi
done

for svc in toth-chatbot hermes-gateway; do
    if [ -f "/home/pi/.config/systemd/user/$svc.service" ]; then
        cp "/home/pi/.config/systemd/user/$svc.service" "$TEMP_DIR/systemd_user/"
    fi
done

# ── 6. Crontab ──────────────────────────────────────────────────────────
echo "[6/10] Sauvegarde crontab..."
crontab -l > "$TEMP_DIR/configs/crontab.txt" 2>/dev/null || echo "# no crontab" > "$TEMP_DIR/configs/crontab.txt"

# ── 7. Boot config ──────────────────────────────────────────────────────
echo "[7/10] Sauvegarde /boot/config..."
if [ -f /boot/firmware/config.txt ]; then
    cp /boot/firmware/config.txt "$TEMP_DIR/configs/boot_config.txt"
elif [ -f /boot/config.txt ]; then
    cp /boot/config.txt "$TEMP_DIR/configs/boot_config.txt"
fi

# ── 8. Audio config ─────────────────────────────────────────────────────
echo "[8/10] Sauvegarde config audio..."
cp /etc/asound.conf "$TEMP_DIR/configs/asound.conf" 2>/dev/null || true
cp /home/pi/.asoundrc "$TEMP_DIR/configs/asoundrc" 2>/dev/null || true

# ── 9. Liste des paquets APT ────────────────────────────────────────────
echo "[9/10] Sauvegarde liste paquets APT..."
dpkg --get-selections | grep -v deinstall > "$TEMP_DIR/packages/apt-packages.txt"
apt-mark showmanual > "$TEMP_DIR/packages/apt-manual.txt" 2>/dev/null || true

# ── 10. Config Himlaya ──────────────────────────────────────────────────
echo "[10/10] Sauvegarde config himalaya..."
cp /home/pi/.config/himalaya/config.toml "$TEMP_DIR/configs/" 2>/dev/null || true

# ── Compression ─────────────────────────────────────────────────────────
echo "Compression vers $BACKUP_FILE..."
tar -czf "$BACKUP_FILE" -C "$TEMP_DIR" .

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo ""
echo "✅ Backup créé : $BACKUP_FILE ($SIZE)"
echo ""
echo "Contenu :"
tar -tzf "$BACKUP_FILE" | head -30
echo "... ($(tar -tzf "$BACKUP_FILE" | wc -l) fichiers au total)"

# Nettoyage : garde les 10 derniers backups
cd "$BACKUP_DIR"
ls -t toth_full_backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true

echo ""
echo "=== Terminé ==="
echo "Pour reconstruire : ./rebuild_toth.sh $BACKUP_FILE"
