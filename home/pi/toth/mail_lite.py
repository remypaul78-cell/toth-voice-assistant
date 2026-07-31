#!/usr/bin/env python3
import imaplib, email, json, os, subprocess, sys

CONFIG = '/home/pi/toth/voice_mail_config.json'
with open(CONFIG) as f: cfg = json.load(f)

def speak(text):
    """Prononce sur WM8960 via espeak. Bloquant pour éviter superposition."""
    try:
        clean = text.replace("'", "\\'")[:200]
        cmd = f"espeak -v fr -s 150 '{clean}' --stdout | ffmpeg -i - -ac 2 -ar 48000 -f alsa hw:0,0 -y 2>/dev/null"
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        print(f'🔊 {clean[:80]}...')
    except subprocess.TimeoutExpired:
        print(f'🔊 TTS timeout')
    except Exception:
        pass

try:
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    mail.login(cfg['gmail_email'], cfg['gmail_app_password'])
    mail.select('inbox')
    _, data = mail.uid('search', None, 'UNSEEN')
    uids = data[0].split()[-3:]
    if not uids:
        speak('Pas de nouveaux mails.')
        print('📭 Pas de nouveaux mails.')
        sys.exit(0)
    speak(f'{len(uids)} nouveaux mails.')
    print(f'📬 {len(uids)} nouveaux mails.')
    for uid in uids:
        _, msg_data = mail.uid('fetch', uid, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])')
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        from_str = msg.get('From', 'Inconnu')[:50]
        subj_str = msg.get('Subject', 'Sans sujet')[:50]
        speak(f'De {from_str}. Sujet: {subj_str}')
        print(f'📧 De: {from_str} | Sujet: {subj_str}')
    mail.logout()
    print('✅ Fait !')
except Exception as e:
    print(f'❌ Erreur: {e}')
