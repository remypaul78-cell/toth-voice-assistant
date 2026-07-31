# Carnet de bord de Toth

Journal des modifications, bugs et décisions importantes du projet Toth.

---

## 2 juin 2026 (soir) — Fix conflit SPI : _display_lock sur TOUS les draw_image

**Problème** : Le `_display_lock` (threading.Lock) existait mais n'était utilisé que dans `_disp()`. Les 4 autres appels à `draw_image()` le contournaient — notamment le thread visage (FACE) et le thread scroll. Résultat : conflits SPI constants → `[FACE] Error: [Errno 1] Operation not permitted` et `[SCROLL] Frame error: [Errno 1] Operation not permitted`.

**Fix** : Ajout de `with self._display_lock:` autour des 4 appels restants :
- `_disp_scroll()` → affichage sans scroll (ligne ~992)
- `_disp_scroll()` → frame d'animation (ligne ~1027)
- `_disp_scroll()` → frame finale (ligne ~1045)
- Thread visage FACE (ligne ~1079) — le coupable principal
- `_show_face_override()` (ligne ~1282)

Après restart : 35+ secondes sans erreur. Threads stables (4).

## 2 juin 2026 (soir) — Diagnostic bouton : test des trois bips ✅

**Contexte** : Le bouton de Toth ne répond plus depuis plusieurs jours. Pour déterminer si le problème est matériel (carte son/GPIO HS) ou logiciel (crash silencieux du thread bouton), Hermes a envoyé un test audio simple : trois bips distincts.

**Résultat** : Rémy a entendu les trois bips → **l'audio fonctionne normalement**. Le problème est donc logiciel : le thread bouton crash silencieusement (probablement emporté par le crash du thread visage « Operation not permitted »), alors que le hardware GPIO/audio est intact.

**Prochaine étape** : Trouver pourquoi le thread visage crash et comment l'empêcher d'emporter le thread bouton avec lui.

---

## 2 juin 2026 — Changement couleurs écran : violet + jaune

Rémy a demandé un fond violet et texte jaune. Choix final : **fond #2D004B (violet sombre) + texte #FFFF00 (jaune vif)**. Modifié dans `_disp()` et `_disp_scroll()`. Le visage/clock reste sur fond noir.

---

## 2 juin 2026 — Optimisation : appel API HTTP direct + contexte limité

**Problème** : Toth passait par le CLI Hermes (`hermes ask`) pour chaque question, ce qui prenait ~50s par appel (spawn du process + chargement complet du prompt).

**Solution** :
- Appel direct à l'API HTTP du gateway Hermes (localhost:8765) au lieu du CLI
- Contexte limité aux 5 derniers messages de la conversation
- Résultat : **7-8 secondes** par réponse au lieu de 50s

**Fichier modifié** : `/home/pi/toth/toth_chatbot.py` — fonction `hermes_ask()`

---

## 2 juin 2026 — Timeout DeepSeek : 60s + 3 tentatives

**Problème** : Pattern observé dans les logs — le 1er message passe en 8.4s, le 2e timeout à 45s (systématiquement). DeepSeek décroche parfois et met plus de 45s à répondre.

**Solution appliquée** :
- `hermes_ask()` timeout passé de 45s → 60s
- `MAX_ATTEMPTS` passé à 3 (max 3 minutes d'attente au total)
- 0.5s de délai entre chaque tentative

**Fichier modifié** : `/home/pi/toth/toth_chatbot.py` (lignes ~746, 1014-1015)

**Prochaine étape si ça timeout encore** : essayer un modèle plus rapide que DeepSeek.

---

## 2 juin 2026 — CALL_TIMEOUT 20s → 90s

Problème initial : Hermes via Nous Portal prend environ 30s pour répondre (prompt de ~18K tokens). Avec CALL_TIMEOUT à 20s, Toth timeoutait 1 fois sur 2.

Solution : CALL_TIMEOUT passé à 90s, retry ×6 (max 9 min).

**Note** : Ce réglage a ensuite été ajusté à 60s + 3 tentatives (3 min max) pour éviter d'attendre trop longtemps sans feedback.

---

## 2 juin 2026 — Migration vers Nous Portal (provider:nous, deepseek-v4-pro)

- **GMKtec** (192.168.1.54, RTX 4070) : réinstallé sur Nous Portal, plus d'Ollama. Fichier Soul.md pour l'identité. Gateway Telegram via systemd user.
- **Pi Zero 2 W / Toth** (192.168.1.56) : Hermes sur Nous Portal, plus de Tailscale. Ollama annulé.

---

## 2 juin 2026 — Bug TTS : variable `_TTS_PROC` locale vs globale

**Problème** : Quand Rémy appuyait sur le bouton pendant que Toth parlait, le TTS ne s'arrêtait pas. La fonction `speak()` utilisait une variable locale `_TTS_PROC` au lieu de la globale `_TTS_PROC`. Résultat : `_btn()` essayait de tuer un processus fantôme (la variable globale vide), le vrai processus TTS continuait.

**Correction** : Ajout de `global _TTS_PROC` en haut de la fonction `speak()` pour que tout le monde parle à la même variable.

**Fichier modifié** : `/home/pi/toth/toth_chatbot.py` — fonction `speak()`

---

## 2 juin 2026 — Bug bouton STOP : variable TTS locale vs globale + vérification par phrase

**Problème** : Quand Rémy appuyait sur le bouton pendant que Toth parlait, le TTS ne s'arrêtait pas. La fonction `speak()` utilisait une variable locale `_TTS_PROC` au lieu de la globale. Résultat : `_btn()` essayait de tuer un processus fantôme (variable globale vide), le vrai TTS continuait.

**Correction** :
- Ajout de `global _TTS_PROC` en haut de `speak()`
- Cancel vérifié **à chaque phrase** au lieu de tous les groupes de 4 → le TTS s'arrête en moins d'une phrase après l'appui

**Fichier modifié** : `/home/pi/toth/toth_chatbot.py` — fonctions `speak()` et `_btn()`

---

## 2 juin 2026 — Bug enregistrement infini + timeout max 60s

**Problème** : Toth restait bloqué en mode enregistrement indéfiniment, captant du bruit de fond sans jamais s'arrêter — pas de détection de silence (VAD). Écran LCD figé, nécessitait un appui bouton ou redémarrage pour débloquer.

**Solution appliquée** : timeout max d'enregistrement de **60 secondes**. Si l'utilisateur ne dit rien ou que le silence n'est pas détecté, l'enregistrement s'arrête automatiquement.

**Note** : Solution « pansement », pas de vraie détection de silence (VAD). À améliorer plus tard.

**Fichier modifié** : `/home/pi/toth/toth_chatbot.py` — boucle d'enregistrement

---

## 2 juin 2026 — Conflit double service Toth (système vs utilisateur)

**Problème** : Deux instances de Toth tournaient en même temps — le service système `toth.service` et le service utilisateur `toth-chatbot.service`. Les deux se battaient pour le GPIO du bouton, rendant le bouton STOP inopérant. Le service utilisateur avait été relancé par erreur.

**Solution** :
- Kill des deux processus
- Relance uniquement du service système `toth.service`
- **Masquage définitif** du service utilisateur (`systemctl --user mask toth-chatbot`) pour éviter tout conflit futur

**Fichiers** : `/etc/systemd/system/toth.service` (conservé), `~/.config/systemd/user/toth-chatbot.service` (masqué)

---

## 2 juin 2026 — Écran LCD : fond blanc, police Montserrat Black 23, scroll 8fps

**Contexte** : Rémy trouvait le clignotement désagréable et voulait un style « graffiti » pour la police.

**Changements** :
- Fond passé de noir à **blanc** (#FFFFFF), texte **noir**
- Police passée de DejaVuSans-Bold 22 à **Montserrat Black 23** (graisse la plus épaisse)
- Scroll réduit de 15 à **8 images/seconde** — supprime le flicker tout en restant fluide
- BATCH_SIZE = 3 (3 phrases par groupe TTS)
- Défilement continu pixel par pixel, proportionnel à l'avancement de la voix

**Fichier modifié** : `/home/pi/toth/toth_chatbot.py` — méthodes `_disp()`, `_disp_scroll()`, `speak()`

---

## 2 juin 2026 — Hiérarchie de reset bouton (3s / 10s)

**Nouveau comportement** :
- Appui **court** (< 3s) : normal (enregistrer / envoyer / cancel)
- Appui **long** (3-9,9s) : **soft reset** (`sys.exit(0)`) — systemd relance Toth 10s après
- Appui **très long** (≥ 10s) : **hard reset** (`systemctl restart toth`) — systemd tue le process de force et le relance

**Debounce** : 1,5s pour éviter les rebonds sur appuis courts. Les appuis longs contournent le debounce.

**Fichier modifié** : `/home/pi/toth/toth_chatbot.py` — `_btn_press()`, `_btn_release()`

---

## 2 juin 2026 — Nouveau système de scroll + timeout/retry intelligent

**Session** : `20260602_140232_85b662` (14h02-14h49)

### 🔄 Scroll rapide
- Retour du vrai scroll (plus d'affichage statique)
- Vitesse triplée : ~50 px/sec (contre 16 px/sec avant)
- 12 fps, fluide sans scintiller
- Si le texte tient sur l'écran → centré, pas de scroll inutile
- Pas de soulignement (Rémy trouvait ça moche)
- `_disp_scroll()` et `speak()` avec callback `display_cb`

### 🧠 Timeout/retry intelligent (refonte complète)
**Avant** : 5 tentatives automatiques × 90s (7,5 min max), Toth bloqué à attendre
**Après** : 1 tentative × 120s, si timeout → Toth s'excuse et sauvegarde la question

**Modifications dans `toth_chatbot.py` :**
- Ligne 860 : ajout de `self._pending_question = None` et `self._pending_since = 0` dans `__init__`
- Lignes ~1237-1310 : remplacement de la boucle `MAX_ATTEMPTS=5` par une tentative unique `CALL_TIMEOUT=120`
- En cas d'échec : `self._pending_question = question` + TTS "Désolé, je peux pas répondre pour le moment. Réessaie."
- En cas de succès : `self._pending_question = None` (efface la question en attente)
- Lignes ~1134-1150 : modification de `_btn_short_press()` — si question en attente + moins de 10 min → retry automatique au lieu d'enregistrer
- Appui 3s → reset (efface la question), appui 10s → reboot service

**Fichier modifié** : `/home/pi/toth/toth_chatbot.py` (PID 15334 après redémarrage)

---

## 2 juin 2026 — Fix reset (soft + hard) : nettoyage complet

**Problème** : Le reset (appui 3s ou 10s) faisait juste `sys.exit(0)` sans nettoyer. Toth reprenait l'ancienne session Telegram (`/tmp/toth_shared_session`) → DeepSeek continuait la conversation précédente → le reset ne servait à rien.

**Fix** : Avant le `sys.exit(0)`, le reset nettoie maintenant `_cancel_flag=True`, `_pending_question=None`, et supprime `/tmp/toth_shared_session` + `/tmp/toth_waiting_since`. Soft et hard reset ont le même nettoyage.

---

## 2 juin 2026 — Synchro Hermes ↔ Toth : brief actif (anti « deux bottes »)

**Problème** : Hermes (Telegram) et Toth (vocal/écran) se désynchronisaient — Toth ne voyait que les 5 derniers messages Telegram, manquait toutes les décisions/actions faites hors discussion (changements de code, reset, config…). Résultat : Rémy parlait à « deux bottes » qui donnaient des infos différentes.

**Solution** : Fichier `/tmp/toth_context_brief` — un résumé concis que j'écris après chaque décision importante. Dans `hermes_ask()`, ce fichier est lu et injecté dans le prompt avec la mention « ⚠️ Contexte ACTUEL (donné par Hermes, prioritaire sur l'historique) ». Le reset (soft/hard) supprime aussi ce fichier pour repartir à zéro.

**Fichier modifié** : `/home/pi/toth/toth_chatbot.py` — `hermes_ask()` (lignes ~808-820), soft reset (~1141-1149), hard reset (~1120-1126)

**Leçon apprise** : `session_search` permet de retrouver n'importe quelle conversation passée avec Hermes, même sur d'anciennes sessions. Quand Hermes « perd la mémoire » en début de session, il peut chercher dans l'historique au lieu de demander à Rémy de tout répéter.

**La procédure maintenant :**
1. En arrivant sur une session vide → lire le `CARNET_DE_BORD_DE_TOTH.md`
2. Si le carnet n'est pas à jour → `session_search` avec des mots-clés du sujet
3. Puis seulement demander à Rémy ce qu'il reste à faire

---

**Problème** : Après les changements de scroll, l'écran LCD est devenu noir. Dans les logs : `OSError: [Errno 16] Device or resource busy` sur le GPIO du WhisplayBoard. Le processus crashait en boucle car les pins GPIO n'étaient pas libérées entre les redémarrages.

**Correction** : Redémarrage via `systemctl restart toth.service` — le `ExecStartPre` nettoie les GPIO avant le lancement (`fuser -k /dev/gpiochip0` + gpioset). L'écran s'est rallumé.

**Note** : Le service système `toth.service` est le SEUL service actif. Le service utilisateur `toth-chatbot.service` est masqué définitivement.

---

## Chronique des améliorations précédentes

- **Sync session Toth** : cron toutes les minutes → `/tmp/toth_shared_session`, permet à Toth de reprendre le contexte Telegram (`sync_toth_session.py`).
- **Auto-repair watchdog** : gpioset GPIO 4,7,8,22-25,27 en ExecStartPre. Heartbeat 2s, watchdog 30s, timeout de démarrage 60s.
- **TTS** : edge-tts, voix fr-FR-RemyMultilingualNeural, volume 30%.
- **Batterie** : PiSugar3 avec RTC.
- **Notifications Telegram** : chat ID 5754223758.
