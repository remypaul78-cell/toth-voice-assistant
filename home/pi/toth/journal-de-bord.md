
## 07/07/2026 23:00 — Session 10: Fix LED RGB + Audio Volume + Reboot

### LED RGB
- **Problème**: SoftPWM (threads) crashait silencieusement sur PermissionError → LED ne changeait pas
- **Fix**: _rgb() remplacé par GPIO direct (board._gpio_output, pas de threads PWM)
- **Couleurs**: supprimé vert (0,255,0) et bleu (0,0,255). Spec: rouge=record, éteint=reste
- **Résultat**: LED rouge visible pendant enregistrement ✅ (confirmé Rémy)

### Audio
- **Problème**: Pas de son TTS ni radio. Headphone volume à 0% + .asoundrc modifié + PulseAudio tué
- **Fix**: .asoundrc remis original (type hw), PulseAudio relancé, Headphone+Speaker à 127
- **Reboot requis** pour restauration complète du son
- **Résultat**: Son restauré après reboot ✅ (confirmé Rémy)

### Backup
- Pi checkpoint: /home/pi/toth/checkpoints/pre-led-fix-20260707-204500.py
- VPS backup: /root/toth-backup/{toth_chatbot.py, telethon_bridge.py, .asoundrc}
- Miroir VPS sync: current/ à jour
- MemPalace: drawer créé wing=toth room=fixes
- Skill toth-chatbot: patch appliqué (LED SoftPWM + Audio Headphone pitfalls)
