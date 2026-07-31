#!/bin/bash
# =============================================================================
# RECONSTRUCTION COMPLÈTE DU SYSTÈME TOTH
# Prend un backup généré par backup_toth_full.sh et reconstruit TOUT.
# Usage: sudo ./rebuild_toth.sh <backup.tar.gz>
#
# CE QUE ÇA FAIT :
#   1. Installe les paquets APT nécessaires
#   2. Restaure les fichiers (toth, whisplay, hermes, ssh)
#   3. Recrée l'environnement Python (venv + dépendances)
#   4. Configure le son (WM8960), le boot, les GPIO
#   5. Installe et active les services systemd
#   6. Restaure le crontab
# =============================================================================
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: sudo $0 <backup.tar.gz>"
    echo "  Le backup.tar.gz est généré par backup_toth_full.sh"
    exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERREUR : $BACKUP_FILE introuvable"
    exit 1
fi

# Vérification : on tourne bien sur un Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  ATTENTION : Ce script est conçu pour un Raspberry Pi."
    echo "   /proc/device-tree/model ne contient pas 'Raspberry Pi'."
    echo "   Continuer quand même ? (Ctrl-C pour annuler, Entrée pour continuer)"
    read
fi

REBUILD_DIR=$(mktemp -d)
trap "rm -rf $REBUILD_DIR" EXIT

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     RECONSTRUCTION DU SYSTÈME TOTH                          ║"
echo "║     Backup : $BACKUP_FILE"
echo "║     $(date)                                                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Extraction
echo "📦 Extraction du backup..."
tar -xzf "$BACKUP_FILE" -C "$REBUILD_DIR"

# ============================================================================
# PHASE 1 : PAQUETS APT
# ============================================================================
echo ""
echo "── Étape 1/8 : Installation des paquets système ──"

# Paquets indispensables (même sans le fichier de backup)
ESSENTIAL_PACKAGES=(
    python3 python3-pip python3-venv python3-dev
    git curl wget rsync
    pulseaudio pulseaudio-utils pulseaudio-module-bluetooth
    bluetooth bluez bluez-tools
    alsa-utils libportaudio2
    gpiod libgpiod-dev
    i2c-tools
    ffmpeg mpg123
    autossh
    cron
)

echo "   Installation des paquets essentiels..."
apt-get update -qq
apt-get install -y "${ESSENTIAL_PACKAGES[@]}" 2>&1 | tail -3

# Installer aussi les paquets listés dans le backup
if [ -f "$REBUILD_DIR/packages/apt-manual.txt" ]; then
    echo "   Installation des paquets supplémentaires (depuis le backup)..."
    xargs -a "$REBUILD_DIR/packages/apt-manual.txt" apt-get install -y 2>&1 | tail -5 || true
fi

# ============================================================================
# PHASE 2 : CONFIGURATION BOOT
# ============================================================================
echo ""
echo "── Étape 2/8 : Configuration boot ──"

BOOT_CONFIG=""
if [ -f "$REBUILD_DIR/configs/boot_config.txt" ]; then
    BOOT_CONFIG="$REBUILD_DIR/configs/boot_config.txt"
elif [ -f /boot/firmware/config.txt ]; then
    echo "   (conservation du config.txt existant)"
fi

if [ -n "$BOOT_CONFIG" ]; then
    if [ -f /boot/firmware/config.txt ]; then
        cp "$BOOT_CONFIG" /boot/firmware/config.txt
        echo "   /boot/firmware/config.txt ✓"
    elif [ -f /boot/config.txt ]; then
        cp "$BOOT_CONFIG" /boot/config.txt
        echo "   /boot/config.txt ✓"
    fi
fi

# Activer SPI, I2C, I2S (si pas déjà fait)
raspi-config nonint do_spi 0 2>/dev/null || true
raspi-config nonint do_i2c 0 2>/dev/null || true

# ============================================================================
# PHASE 3 : RESTAURATION FICHIERS
# ============================================================================
echo ""
echo "── Étape 3/8 : Restauration des fichiers ──"

# Toth
if [ -d "$REBUILD_DIR/toth" ]; then
    echo "   Restauration /home/pi/toth/..."
    mkdir -p /home/pi/toth
    rsync -a "$REBUILD_DIR/toth/" /home/pi/toth/
    chown -R pi:pi /home/pi/toth
fi

# Whisplay
if [ -d "$REBUILD_DIR/whisplay" ]; then
    echo "   Restauration /home/pi/whisplay/..."
    mkdir -p /home/pi/whisplay
    rsync -a "$REBUILD_DIR/whisplay/" /home/pi/whisplay/
    chown -R pi:pi /home/pi/whisplay
fi

# Hermes configs
if [ -d "$REBUILD_DIR/hermes" ]; then
    echo "   Restauration config Hermes..."
    mkdir -p /home/pi/.hermes/memories
    mkdir -p /home/pi/.hermes/scripts
    mkdir -p /home/pi/.hermes/skills
    mkdir -p /home/pi/.hermes/pairing
    mkdir -p /home/pi/.hermes/cron

    # Fichiers individuels
    for f in config.yaml .env SOUL.md auth.json channel_directory.json gateway_state.json; do
        if [ -f "$REBUILD_DIR/hermes/$f" ]; then
            cp "$REBUILD_DIR/hermes/$f" /home/pi/.hermes/
            echo "     $f ✓"
        fi
    done

    # Mémoires
    for f in MEMORY.md USER.md; do
        if [ -f "$REBUILD_DIR/hermes/$f" ]; then
            cp "$REBUILD_DIR/hermes/$f" /home/pi/.hermes/memories/
        fi
    done

    # Cron jobs
    if [ -f "$REBUILD_DIR/hermes/jobs.json" ]; then
        cp "$REBUILD_DIR/hermes/jobs.json" /home/pi/.hermes/cron/
    fi

    # Scripts custom
    if [ -d "$REBUILD_DIR/hermes/scripts" ]; then
        rsync -a "$REBUILD_DIR/hermes/scripts/" /home/pi/.hermes/scripts/
    fi

    # Skills custom
    if [ -d "$REBUILD_DIR/hermes/skills" ]; then
        for d in "$REBUILD_DIR/hermes/skills/"*/; do
            skill_name=$(basename "$d")
            if [ -f "$d/SKILL.md" ]; then
                rsync -a "$d" "/home/pi/.hermes/skills/$skill_name/"
            fi
        done
    fi

    # Pairing
    if [ -d "$REBUILD_DIR/hermes/pairing" ]; then
        rsync -a "$REBUILD_DIR/hermes/pairing/" /home/pi/.hermes/pairing/
    fi

    chown -R pi:pi /home/pi/.hermes
fi

# SSH keys
if [ -d "$REBUILD_DIR/ssh" ]; then
    echo "   Restauration clés SSH..."
    mkdir -p /home/pi/.ssh
    rsync -a "$REBUILD_DIR/ssh/" /home/pi/.ssh/
    chown -R pi:pi /home/pi/.ssh
    chmod 700 /home/pi/.ssh
    chmod 600 /home/pi/.ssh/id_* /home/pi/.ssh/authorized_keys 2>/dev/null || true
    chmod 644 /home/pi/.ssh/*.pub 2>/dev/null || true
fi

# Audio config
if [ -f "$REBUILD_DIR/configs/asound.conf" ]; then
    cp "$REBUILD_DIR/configs/asound.conf" /etc/asound.conf
    echo "   /etc/asound.conf ✓"
fi
if [ -f "$REBUILD_DIR/configs/asoundrc" ]; then
    cp "$REBUILD_DIR/configs/asoundrc" /home/pi/.asoundrc
    chown pi:pi /home/pi/.asoundrc
    echo "   ~/.asoundrc ✓"
fi

# Himalaya config
if [ -f "$REBUILD_DIR/configs/config.toml" ]; then
    mkdir -p /home/pi/.config/himalaya
    cp "$REBUILD_DIR/configs/config.toml" /home/pi/.config/himalaya/
    chown -R pi:pi /home/pi/.config/himalaya
    echo "   himalaya config ✓"
fi

# ============================================================================
# PHASE 4 : ENVIRONNEMENT PYTHON
# ============================================================================
echo ""
echo "── Étape 4/8 : Environnement Python ──"

REQUIREMENTS_FILE="$REBUILD_DIR/toth/requirements.txt"

# Créer requirements.txt s'il n'existe pas (détection auto)
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "   Génération de requirements.txt (détection automatique)..."
    cd /home/pi/toth
    grep -rh "^import \|^from " --include="*.py" . 2>/dev/null | \
        sed 's/import //;s/from //;s/ .*//' | sort -u | \
        grep -v "^toth_\|^pisugar_\|^battery_\|^radio\|^vocal_\|^mail_\|^launcher\|^__" \
        > "$REQUIREMENTS_FILE" 2>/dev/null || true

    # Ajouts manuels essentiels
    cat >> "$REQUIREMENTS_FILE" << 'EOF'
# Dépendances Toth - ajouts manuels
edge-tts
gpiozero
lgpio
pyaudio
pygame
tinytuya
requests
EOF
fi

echo "   Création du venv..."
cd /home/pi/toth
python3 -m venv .venv
source .venv/bin/activate
echo "   Installation des dépendances Python..."
pip install --upgrade pip setuptools wheel 2>&1 | tail -1
pip install -r "$REQUIREMENTS_FILE" 2>&1 | tail -5 || true
deactivate
chown -R pi:pi /home/pi/toth/.venv

# ============================================================================
# PHASE 5 : SERVICES SYSTEMD
# ============================================================================
echo ""
echo "── Étape 5/8 : Installation des services systemd ──"

# Services système
if [ -d "$REBUILD_DIR/systemd" ]; then
    for svc in "$REBUILD_DIR/systemd/"*.service; do
        if [ -f "$svc" ]; then
            svc_name=$(basename "$svc")
            cp "$svc" "/etc/systemd/system/$svc_name"
            chmod 644 "/etc/systemd/system/$svc_name"
            echo "   $svc_name ✓"
        fi
    done
    systemctl daemon-reload
fi

# Services utilisateur
if [ -d "$REBUILD_DIR/systemd_user" ]; then
    mkdir -p /home/pi/.config/systemd/user
    for svc in "$REBUILD_DIR/systemd_user/"*.service; do
        if [ -f "$svc" ]; then
            svc_name=$(basename "$svc")
            cp "$svc" "/home/pi/.config/systemd/user/$svc_name"
            chown pi:pi "/home/pi/.config/systemd/user/$svc_name"
            echo "   user/$svc_name ✓"
        fi
    done
    # Rechargement user (à faire en tant que pi)
    su - pi -c "XDG_RUNTIME_DIR=/run/user/1000 systemctl --user daemon-reload" 2>/dev/null || true
fi

# ============================================================================
# PHASE 6 : ACTIVATION SERVICES
# ============================================================================
echo ""
echo "── Étape 6/8 : Activation des services ──"

# Activer les services système pertinents
for svc in toth toth-watchdog autossh-tonton; do
    if [ -f "/etc/systemd/system/$svc.service" ]; then
        systemctl enable "$svc" 2>/dev/null && echo "   $svc activé" || echo "   $svc (déjà activé ou ignoré)"
    fi
done

# Services utilisateur (activer avec linger pour qu'ils démarrent au boot)
loginctl enable-linger pi 2>/dev/null || true
for svc in toth-chatbot hermes-gateway; do
    if [ -f "/home/pi/.config/systemd/user/$svc.service" ]; then
        su - pi -c "XDG_RUNTIME_DIR=/run/user/1000 systemctl --user enable $svc" 2>/dev/null && \
            echo "   user/$svc activé" || echo "   user/$svc (déjà activé ou ignoré)"
    fi
done

# ============================================================================
# PHASE 7 : CRONTAB
# ============================================================================
echo ""
echo "── Étape 7/8 : Restauration du crontab ──"

if [ -f "$REBUILD_DIR/configs/crontab.txt" ]; then
    crontab -u pi "$REBUILD_DIR/configs/crontab.txt" 2>/dev/null && \
        echo "   crontab restauré ✓" || echo "   ⚠️  Échec crontab (pas critique)"
fi

# ============================================================================
# PHASE 8 : AUDIO ET FINALISATION
# ============================================================================
echo ""
echo "── Étape 8/8 : Configuration audio et finalisation ──"

# S'assurer que le module WM8960 est chargé
modprobe wm8960 2>/dev/null || echo "   (wm8960 déjà chargé ou pas encore dispo, OK après reboot)"
modprobe snd-soc-wm8960 2>/dev/null || true

# Groupes utilisateur pour GPIO, audio, bluetooth
usermod -a -G gpio,i2c,spi,audio,pulse,pulse-access,bluetooth pi 2>/dev/null || true

# Permissions Bluetooth (PolicyKit pour ne pas demander de mot de passe)
cat > /etc/polkit-1/localauthority/50-local.d/50-bluetooth.pkla << 'POLKIT'
[Bluetooth]
Identity=unix-user:pi
Action=org.bluez.*
ResultAny=yes
ResultInactive=yes
ResultActive=yes
POLKIT

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     ✅ RECONSTRUCTION TERMINÉE                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Prochaines étapes :"
echo "  1. Redémarrer le Pi : sudo reboot"
echo "  2. Vérifier que les services démarrent :"
echo "     sudo systemctl status toth toth-watchdog autossh-tonton"
echo "     su - pi -c 'systemctl --user status toth-chatbot hermes-gateway'"
echo "  3. Vérifier le son : speaker-test -t sine -f 440 -l 1"
echo "  4. Vérifier le Bluetooth : bluetoothctl"
echo "  5. Lancer un backup post-reconstruction :"
echo "     /home/pi/toth/backup_toth_full.sh"
echo ""
echo "⚠️  Notes importantes :"
echo "  - Le .env contient peut-être des tokens expirés, vérifie"
echo "  - Les clés SSH sont restaurées mais vérifie l'accès au VPS Tonton"
echo "  - Si le module WM8960 ne charge pas : active 'dtoverlay=wm8960-soundcard'"
echo "    dans /boot/firmware/config.txt et reboot"
echo "  - Le tunnel autossh nécessite que le VPS Tonton accepte la clé"
echo ""
read -p "Redémarrer maintenant ? (o/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]]; then
    reboot
fi
