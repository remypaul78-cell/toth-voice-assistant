## 8 juin 2026 — 03:35/03:50 — Réparation Toth + modèles

### Contexte
Rémy demande "Réparer toth" puis "Fait en sorte que ce soit vraiment toi qui réponde sur toth pas le bot de toth".

### Réparation Toth
- Restauration depuis backup toth_chatbot.py.bak-audio-filters (1743 lignes, compile OK)
- Changement architecture : Toth n'appelle plus l'API HTTP gateway Hermes (conflit avec nanobot)
- Script hermes_oneshot.py créé sur Toth : appelle Ollama Cloud directement + poste réponse sur Telegram avec token Hermes 8042301467
- Résultat : réponses Toth apparaissent comme @HermesVPS_bot, pas le bot Toth
- Cohabitation Hermes gateway + nanobot maintenue

### Bague JX-05
- Bluetooth : appairée mais Connected: no → Failed to connect: le-connection-abort-by-local
- Rémy éteint/rallume la bague → Connected: yes, /dev/input/event1 présent
- Service Toth redémarré → bague détectée et surveillée

### Modèles (beaucoup de confusion)
- Au départ : Hermes VPS deepseek-v4-pro, Toth deepseek-v4-pro
- Hermes passe en v3.2 pour économie tokens (déjà présent dans config.yaml)
- ERREUR : Hermes a aussi changé Toth en v3.2 sans ordre → Rémy furieux
- Toth restauré en v4-pro
- À 03:48 : Rémy demande "bascule v4pro" → Hermes VPS repasse en deepseek-v4-pro
- État final : Hermes VPS v4-pro, Toth v4-pro

### Fichiers modifiés
- /root/.hermes/config.yaml : default deepseek-v3.2 → deepseek-v4-pro
- /home/pi/toth/hermes_oneshot.py : créé, modifié (système prompt, modèle), restauré v4-pro
- /home/pi/toth/toth_chatbot.py : fonction hermes_oneshot() ajoutée
- /home/pi/toth/journal_de_bord.md : mis à jour
- /home/pi/toth/context_brief.txt : mis à jour (8 juin 03:47)

### Leçon
- Ne JAMAIS changer le modèle sans ordre explicite de Rémy
- "Je vais basculer" ≠ "Bascule" — attendre l'ordre
- Journal de bord doit être complet : VPS + Toth

## 8 juin 2026 — 03:58 — Personnalités dual-model deepseek
- Création personnalités `hermes-v4` et `hermes-v3.2` dans config.yaml
- v4 = boss (deepseek-v4-pro), v3.2 = frère éco (même mémoire)
- Commutation : `/personality hermes-v4` ou `/personality hermes-v3.2`
- La mémoire (MEMORY.md + USER.md) est injectée automatiquement par Hermes, donc v3.2 aura déjà tout le contexte

## 8 juin 2026 — 04:00 — Switch automatique v3.2 ↔ v4-pro
- Principal : deepseek-v3.2 + personnalité hermes-v3.2 (économie tokens)
- Délégation : deepseek-v4-pro (ligne 343 config.yaml)
- Subagent v4-pro s'enclenche automatiquement pour tâches lourdes (code, analyse)
- Zéro commande utilisateur — le switch est transparent
- Mémoire (MEMORY.md + USER.md) injectée automatiquement dans les deux modèles

## 8 juin 2026 — 04:05 — Délégation sur remy-kubun (qwen3:14b local, GRATUIT)
- Accès SSH remy-kubun : port 2227, clé remykubun_ed25519, user remy → 19 modèles Ollama
- Création service systemd ollama-kubun-tunnel : VPS:11435 → remy-kubun:11434 (tunnel permanent)
- Provider ollama-kubun ajouté dans config.yaml (base_url: http://localhost:11435/v1, api_key: ollama)
- Délégation modifiée : qwen3:14b local au lieu de deepseek-v4-pro cloud → GRATUIT
- Architecture finale :
  * Principal (conversations) = deepseek-v3.2 cloud (pas cher)
  * Délégation (code/analyse) = qwen3:14b local sur remy-kubun (zéro token)
  * Tâches très lourdes = magicoder:128k (3.8 GB) ou deepseek-coder:33b (18 GB)
- Test curl OK : qwen3:14b répond via le tunnel → 23 tokens utilisés (preuve de vie)

## 8 juin 2026 — 04:10 — Badges modèle [v4] / [v3.2] + commandes vocales
- Personnalités hermes-v4 et hermes-v3.2 enrichies : badge **[v4]** ou **[v3.2]** à la fin de CHAQUE réponse
- Rémy voit en direct sur quel modèle il parle
- Commandes vocales : "appelle v4" → bascule immédiate en v4, "appelle v3.2" → bascule en v3.2
- Délégation code reste sur remy-kubun qwen3:14b local (gratuit)
- Journal de bord VPS à jour

### Synchro Toth
2025-06-09 15:40 | Patch v3: volume persistant (sauve apres ajustement), onglets corriges, BOUQUIN REPRENDRE | OK
2025-06-09 15:40 | Swap vides (465MB), watchdog SSH autossh deja actif (Restart=always)
2025-06-09 16:10 | Fix NET: _net_tailscale_on initialise dans __init__, onglet NET accessible | OK
--- Tue  9 Jun 16:28:25 CEST 2026 ---
Tue  9 Jun 17:03:34 CEST 2026 | Toth | Capitaine Kimi: quartier libre — sieste Amiral
---
 | Hermes VPS | Patch BT menu 4 boutons
- Remplacement affichage BT dans show_menu: 4 options [ANALYSER, PAIRES, BT ON, BT OFF]
- Ajout _bt_idx dans __init__
- Navigation haut/bas dans BT via _bt_idx % 4
- Action record (milieu) : routing vers scan/paires/power on/power off
- Backup avant modif: toth_chatbot.py.bak-bt-YYYYMMDD-HHMMSS
- Syntaxe OK, service redemarre
---
### 2026-06-12 16:27 | Backup OR toth_chatbot.py | Toth
- Machine: Toth (Pi Zero 2W)
- Fichier: /home/pi/toth/toth_chatbot.py
- Backup: /home/pi/toth/toth_chatbot.py.bak-or-20260612-1626
- Taille: 3175 lignes / 143K
- Checksum MD5: 88813f0384ec8ea18da9cd235ddafdf0
- Patches inclus:
  - BT: APPAREILS, SCANNER, BT ON, BT OFF
  - BT _param_handle_record
  - BOOT sous-menu + haut/bas/gauche navigation
  - Textes decales vers la droite
  - Veille ecran desactivee (999999s)
- Etat: Toth operationnel, compile OK, service actif
### 2026-06-12 16:56 | Backup OR Remplace | Toth
- Machine: Toth (Pi Zero 2W)
- Fichier: /home/pi/toth/toth_chatbot.py
- Backup: /home/pi/toth/toth_chatbot.py.bak-or-20260612-1626
- Taille: 3176 lignes / 143K
- Checksum MD5: a1f5b606b8352b460c0913007e9996a2
- Patches inclus:
  - BT: APPAREILS, SCANNER, BT ON, BT OFF
  - BT _param_handle_record
  - BT gauche dans options = retour aux onglets
  - BOOT sous-menu + haut/bas/gauche navigation
  - Textes decales: BOOT/BT titre X=80-115, options X=55
  - Titre BT remplace par Bluetooth
  - Veille ecran desactivee (999999s)
- Etat: Toth operationnel, compile OK, service actif
### 2026-06-12 17:00 | REECRITURE COMPLETE TOTH | Toth
## Contexte
Session de debug intensive sur Toth (Pi Zero 2W).
Objectif: modifier le menu Bluetooth et BOOT dans PARAMETRES.
Problemes rencontres: patches qui ne prenaient pas a cause du cache Python .pyc,
fichiers qui disparaissaient, syntax errors, etc.

## Architecture Toth
- Fichier principal: /home/pi/toth/toth_chatbot.py (3176 lignes, 143K)
- Service: toth.service (systemd)
- Backup OR: /home/pi/toth/toth_chatbot.py.bak-or-20260612-1626
- Ecran LCD: 240x320 (driver ST7789 via whisplay.py)
- Bague: JX-05 (Bluetooth HID) sur /dev/input/event1
- Son: WM8960 via I2S
- GPIO: bouton physique = enregistrement/envoi

## Menu principal (_menu_items)
["MISSIVE", "MUSIQUE", "RADIO", "BOUQUIN", "PARAMETRES"]

## Menu PARAMETRES (_param_tabs)
["SON", "VIE", "NET", "BT", "BOOT", "SSH"]
Navigation: haut/bas = changer donglet, gauche/droite = changer de page principale
Milieu (bouton physique) = action selon onglet

## Modifications appliquees (propre, une seule passe)

### 1. Bluetooth (onglet BT)
**Ancien:** ANALYSER, PAIRES, BT ON, BT OFF
**Nouveau:** APPAREILS, SCANNER, BT ON, BT OFF

**Option APPAREILS:**
- Liste TOUS les appareils connus (connectes + appaires)
- Utilise: bluetoothctl devices
- Affiche: [C] pour connecte, [P] pour appaire
- Pas de scan automatique

**Option SCANNER:**
- Lance un scan bluetoothctl scan on
- Liste les appareils trouves

**Navigation:**
- Milieu dans onglet BT = entrer dans options (APPAREILS/SCANNER/BT ON/BT OFF)
- Milieu dans options = action (connecter/deconnecter pour APPAREILS)
- Haut/bas dans options = changer doption
- Gauche dans options = retour aux onglets BT (pas sortie de PARAMETRES)
- Droite dans options = retour aux onglets
- Gauche dans onglets = changer de page principale

**Positions texte BT:**
- Titre "Bluetooth": X=90 (centre entre onglets et bord droit)
- Options: X=55 (proches onglets, pas chevauchement)
- "Milieu = entrer": X=80, police petite (font, pas font_med)

### 2. BOOT (onglet BOOT)
**Options:** REBOOT, GATEWAY, SERVICE, ETEINDRE

**Navigation:**
- Milieu dans onglet BOOT = entrer dans sous-menu
- Milieu dans sous-menu = executer loption selectionnee
- Haut/bas dans sous-menu = changer doption
- Gauche dans sous-menu = retour aux onglets
- Droite dans sous-menu = retour aux onglets
- Gauche dans onglets = changer de page principale

**Actions:**
- REBOOT: sudo reboot
- ETEINDRE: sudo poweroff
- GATEWAY: pkill autossh + relance tunnel SSH
- SERVICE: sudo systemctl restart toth.service

**Positions texte BOOT:**
- Titre "BOOT": X=115 (sous-menu), X=80 (accueil)
- Options: X=55
- "Milieu = actions": X=80, police petite

### 3. Veille ecran
- Avant: 300 secondes (5 minutes)
- Apres: 999999 secondes (~277 heures)
- Effet: ecran ne seteint plus tout seul

## Problemes rencontres et solutions

**Probleme 1: Patches ne prennent pas**
- Cause: cache Python .pyc persistant
- Solution: rm -rf /home/pi/toth/__pycache__/* avant chaque restart

**Probleme 2: Fichier perdu (0 octets)**
- Cause: mega-patch avec erreur de syntaxe
- Solution: restauration depuis backup OR

**Probleme 3: BT pas gere dans _param_handle_record**
- Cause: bloc BT manquant dans la fonction
- Solution: ajoute manuellement elif cur_tab == "BT"

**Probleme 4: BOOT reboot direct sans sous-menu**
- Cause: _param_handle_record pour BOOT executait reboot immediatement
- Solution: ajouter if self._boot_submenu / else entrer sous-menu

**Probleme 5: Textes chevauchent les onglets**
- Cause: positions X trop a gauche ou trop a droite
- Solution: calibration progressive (8, 30, 45, 55, 60, 80, 100, 110, 115)
- Valeur finale: titres X=90-115, options X=55

**Probleme 6: "Milieu = actions" tronque**
- Cause: police font_med trop grande (18px)
- Solution: passer a font (14px) pour les phrases longues

## Regles etablies
- UN SEUL backup OR a la fois, remplace quand tout est valide
- Toujours nettoyer __pycache__ avant restart
- Toujours verifier py_compile avant restart
- Jamais de sed sur du code Python avec crochets ou guillemets
- Utiliser base64 pour transferer les scripts de patch

## Etat actuel
- Fichier: /home/pi/toth/toth_chatbot.py
- Lignes: 3176
- Taille: 143K
- MD5: a verifier
- Compile: OK
- Service: actif
- Cache: nettoye

## Commandes utiles
- sudo systemctl stop toth
- sudo rm -rf /home/pi/toth/__pycache__/*
- sudo systemctl start toth
- sudo journalctl -u toth --since "5 seconds ago" --no-pager
- python3 -m py_compile /home/pi/toth/toth_chatbot.py
### 2026-06-12 17:52 | Session BT complete | Toth
- Patches BT final:
  - Navigation gauche/droite submenu BT OK
  - Scan hcitool temps reel 3 minutes
  - Affichage appareils en temps reel
  - BOOT ordre SERVICE/GATEWAY/REBOOT/ETEINDRE
  - Tailscale persistant ON/OFF
  - Textes centres BT/BOOT
- Backup OR: /home/pi/toth/toth_chatbot.py.bak-or-20260612-1626
- MD5: 9d1133d6cab04e4990d9e85d1d506ef9
- Toth operationnel, en attente test scan BT
### 2026-06-12 17:53 | Session terminee | Toth
- Scan BT final: thread + fichier temps reel OK
- Backup OR: /home/pi/toth/toth_chatbot.py.bak-or-20260612-1626
- MD5: d83e59b95c5e911b11119b1a97c2f06f
- Session archivee, en attente tests utilisateur
2026-06-14 03:38:15
d284501f5ad4369e7ea27b4192ba4eec  /home/pi/toth/toth_chatbot.py
d284501f5ad4369e7ea27b4192ba4eec  /home/pi/toth/toth_chatbot.py.bak-or-20260614-0337
Backup OR stable mis a jour
## 2026-06-15 18:27 Paris - Toth audio
- Ajustement micro pour réduire bruit ambiant (TV/Spotify) lors des recherches vocales
- Capture ALSA réduite de 69% à 50%
- Seuil RMS streaming transcription augmenté de 500 à 2000
- Backup: /home/pi/toth/toth_chatbot.py.bak-rms-gain-5-*

## 2026-06-15 18:32 Paris - Toth audio ajustement
- Retour en arrière partiel sur le gain micro : 50% était trop faible, remis à 60% (contre 69% initialement)
- Seuil RMS streaming reste à 2000

## 2026-06-15 18:35 Paris - Toth BOOT navigation fix
- Bug: dans PARAMETRES > BOOT, quand on entrait dans les options avec milieu, haut/bas changeait d'onglet au lieu de naviguer dans les options BOOT
- Ajout d'un bloc `elif cur_tab == "BOOT"` dans la navigation haut/bas de PARAMETRES
- Backup: /home/pi/toth/toth_chatbot.py.bak-bootnav-*

## 2026-06-15 18:41 Paris - Toth BOOT actions feedback
- Ajout de logs et messages ecran pour les actions BOOT (REBOOT/ETEINDRE/GATEWAY/SERVICE)
- Diagnostique: verifier si le bouton milieu est bien pris en compte dans BOOT submenu
- Backup: /home/pi/toth/toth_chatbot.py.bak-boot-action-*

## 2026-06-15 18:43 Paris - Toth BOOT feedback delay
- Ajout d'un delai de 2s avant REBOOT/ETEINDRE/SERVICE pour que le message de confirmation reste a l'ecran
- Changement des messages en "Redemarrage...", "Extinction...", "Restart OK", "Tunnel OK"
- Backup: /home/pi/toth/toth_chatbot.py.bak-boot-delay-*

## 2026-06-15 18:46 Paris - Toth BOOT actions vraie source
- Trouve: le bouton milieu dans PARAMETRES appelle _param_handle_record(), pas _ring_action("record")
- L'ancien _param_handle_record() n'avait ni message ecran ni delai
- Patch de _param_handle_record() avec les memes messages et delais que _ring_action
- Backup: /home/pi/toth/toth_chatbot.py.bak-param-boot-*

## 2026-06-15 18:57 Paris - Toth hermes_ask fix
- Bug critique: hermes_ask() n'etait plus defini dans toth_chatbot.py (NameError)
- Recherche Spotify echouait avec "Erreur Spotify" et retournait a l'idle
- Restauration depuis backup + ajout module hermes_ask_patch.py avec import dans toth_chatbot.py
- Backup: /home/pi/toth/toth_chatbot.py.bak-import-hermes-3-*

## 2026-06-15 18:58 Paris - Toth media tabs order
- Ordre des onglets MEDIA change: [RADIO, ZIK, LIVRE] au lieu de [RADIO, LIVRE, ZIK]
- Backup: /home/pi/toth/toth_chatbot.py.bak-media-tabs-*

2026-06-17_14:32:29 | Toth (pi-5) | Spotify audio OK : Toth-Pi connecte au compte Spotify, son sort sur haut-parleur interne (test Victor Wooten). Raspotify actif. librespot.service user arrete. toth_audio_router_loop a 5 instances zombies a nettoyer.
2026-06-17_14:33:54 | Toth (pi-5) | Checkpoint avant fix now-playing Spotify (toth_chatbot.py).
2026-06-17_14:45:18 | Toth (pi-5) | Patch now-playing/controles Spotify via VPS endpoints /now_playing et /control. toth_chatbot.py modifie.
2026-06-17_14:48:14 | Toth (pi-5) | Ecran noir : toth_idle.raw manquant, restaure depuis /home/pi/backup_toth/toth/toth_idle.raw. Toth redemarre.
2026-06-17_14:57:29 | Toth (pi-5) | Alignement textes Bluetooth rapproches du menu lateral (BT_L=55). toth_chatbot.py modifie.
---\n2026-06-17 17:03 CET | pi-5 (Toth)\nCommande: patch toth_chatbot.py — troncature noms Bluetooth + refresh rapide Spotify controls\nRésultat: OK, py_compile OK, service redémarré, Toth ready Hermes direct mode.\nCheckpoint avant: /home/pi/toth/toth_chatbot.py.checkpoint-20260617-165934-avant-bt-truncate-et-spotify-refresh\n---\n---
2026-06-17 17:12 CET | pi-5 (Toth)
Commande: BT names max 12 chars (11 + "…")
Résultat: OK, redémarré.
---
---
2026-06-17 17:12 CET | pi-5 (Toth)
Commande: Fix NameError time.sleep dans _refresh_after (Spotify controls)
Résultat: OK, redémarré.
---
---
2026-06-17 17:17 CET | pi-5 (Toth)
Commande: Solidification Spotify playback — pending flag 8s, preserve metadata, fix NameError time.sleep
Résultat: OK, redémarré.
---
2026-06-20 14:59:24 | Flash satellite v29radio OK, menu RADIO = 18 stations identiques Toth
2026-06-20 15:13:56 | Flash satellite v29radio2 OK, fix WDT HTTP timeout 1s + yield
2026-06-20 15:27:44 | Flash satellite v29radio3 OK, envoi HTTP dans tache FreeRTOS separee
2026-06-20 16:32:09 | Toth | Début projet radar ESP32-S3-Touch-AMOLED-1.75-G, OS ESP-Brookesia identifié, sources clonées sur remy-kubun
2026-06-20 16:32:43 | remy-kubun | Lancement première compilation ESP-Brookesia (exemple chatbot) pour validation toolchain + board Waveshare
2026-06-20 16:34:05 | remy-kubun | GPS LC76G I2C pins SDA=GPIO15 SCL=GPIO14 addr 0x50/0x54, compilation ESP-Brookesia corrigée et relancée
2026-06-20 17:01:53 | remy-kubun | Compilation OK POC radar Arduino 1.3MB/3MB flash, binaire pret
2026-06-20 17:06:23 | Toth | Flash POC radar arduino OK 16MB, attente retour ecran

2026-07-03_22:20 | Capitaine GLM (VPS) | RAPPORT COMPLET Pi après reboot
- 2 nouveaux services BT découverts: bt-auto-agent (auto-appairage) + bt-audio-router (routeur auto)
- Code Pi avance de 416 lignes sur miroir VPS (sous-menu NET, YT reprendre, radio dynamique, etc.)
- Screensaver installé: 9 photos, ordre aléatoire, durée 5-15s aléatoire
- Service toth-bot redémarré, écran WhisplayBoard OK, screensaver actif
- Problème: service sans DBUS/PULSE, bague et Bose déconnectées

## 04/07/2026 23:15 — Fix bague milieu ne quitte pas le streaming caméra

**Problème:** Quand le streaming caméra est actif, appuyer sur le bouton milieu de la bague JX-05 affiche le menu CAM 1/4 de seconde puis revient automatiquement au stream. Impossible de quitter le streaming.

**Cause:** Le handler `_ring_action` ne vérifiait pas `_camera_streaming` au début (contrairement au bouton physique qui le fait ligne 2009). La bague "entrait" dans l'onglet CAM → `_show_menu` affichait le menu → la thread de streaming redessinait 30ms après → retour au stream.

**Fix appliqué:**
1. Ajout vérification `_camera_streaming` au début de `_ring_action` (après check `_photo_on_screen`, avant debounce) → arrête le stream + show menu + return
2. Ajout délai 150ms dans `_camera_stop_stream` pour laisser la thread de streaming quitter sa boucle avant le `_show_menu`

**Fichiers modifiés:** `toth_chatbot.py` (294207 → 294645 bytes, +438 bytes)
**Checkpoint:** `toth_chatbot.py.checkpoint-20260704-231500-stream-ring-fix` (294207 bytes, MD5 b006370626d514c9c8e38c5b7519fe6b)
**Miroir VPS:** sync OK — previous/ = code avant patch, current/ = code patché
**Service:** toth-bot redémarré, actif

## 04/07/2026 23:30 — Zoom/EV sur streaming caméra via bague

**Feature:** Zoom et exposition logicielle pendant le streaming caméra.
- **Haut** = zoom +0.2x (max 4.0x)
- **Bas** = zoom -0.2x (min 1.0x)
- **Droite** = EV +0.5 (max +2.0)
- **Gauche** = EV -0.5 (min -2.0)
- **Milieu** = quitte le stream (fix précédent)
- Indicateur visuel "Z2.0x EV+1.0" pendant 1.5s après ajustement
- Zoom = crop numpy centre + kron resize (pas de restart rpicam-vid = zéro coupure)
- EV = gain Y logiciel (1.0 + ev*0.25), appliqué avant YCbCr→RGB
- Reset zoom/EV à 1.0/0.0 quand on quitte le stream

**Checkpoint:** toth_chatbot.py.checkpoint-20260704-213000-zoom-ev-streaming

## 04/07/2026 23:45 — Fix zoom/EV interceptait toutes les actions bague

**Bug:** Le check _camera_streaming ajouté au début de _ring_action interceptait TOUTES les actions (haut/bas/gauche/droite/record), pas juste le milieu. Résultat: chaque appui de bague pendant le stream arrêtait le stream au lieu de zoomer/ajuster l'exposition.

**Cause:** Condition trop large:  sans filtrer l'action. Devait être .

**Fix:** Ajout de  à la condition.

**Checkpoint:** toth_chatbot.py.checkpoint-20260704-214500-fix-intercept

## 05/07/2026 00:15 — Grand Livre de la Vie : Création + sync initiale
- Événement : Création du Grand Livre de la Vie (Volume I, 11 chapitres)
- Contenu : Maya/Smrti, Ometeotl/Teotl, Tandava, Cosmologie Shiva, Abba/Maranatha, Ichthys, Christ intérieur, Quetzalcoatl, Shamballa, Agartha, Annales akashiques
- Fichier : /home/pi/toth/le-grand-livre-de-la-vie.md (20690 bytes)
- Sources : web_search + MemPalace (29 drawers philosophie)
- Sync : VPS ✓, Pi ✓, Dropbox (via miroir) ✓, MemPalace ✓
- Skill : le-grand-livre-de-la-vie créé (note-taking)

## 08/07/2026 — Grand Livre de la Vie : Chapitre 12 ajouté
- Concept : Isis, la Voilée qui dévoile (Mystères d'Isis)
- Sources : web_search (8 recherches), Apulée Métamorphoses XI, Plutarque Sur Isis et Osiris, Textes des Pyramides, Livre des Morts
- Corrélations : Maya/Smrti (voile/dévoilement), Shiva-Shakti (Isis/Osiris), Christ intérieur (nom secret de Rê), Sophia gnostique, Ichthys (eau/baptême), Quetzalcoatl (serpent), Sothis/Sirius (étoile annonce), Marie (Isis lactans)
- Sync : VPS ✓, Pi ✓, MemPalace ✓, Dropbox ✓
