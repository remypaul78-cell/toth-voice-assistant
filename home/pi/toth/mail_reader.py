#!/usr/bin/env python3
import imaplib
import email
from email.header import decode_header
import subprocess
import time
import os

IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993
EMAIL = 'remypaul78@gmail.com'
PASSWORD = 'ejrfclujkyehtuy'
LAST_MAIL_FILE = '/home/pi/toth/.last_mail'

def speak(text):
    """Prononce sur WM8960 via espeak. Bloquant pour éviter superposition."""
    try:
        clean = text.replace('*', '').replace('_', '').replace('`', '')[:500]
        cmd = "espeak -v fr -s 150 '" + clean.replace("'", "\\'") + "' --stdout | ffmpeg -i - -ac 2 -ar 48000 -f alsa hw:0,0 -y 2>/dev/null"
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        print(f'🔊 {clean[:80]}...')
    except subprocess.TimeoutExpired:
        print(f'🔊 TTS timeout')
    except Exception as e:
        print(f'❌ TTS: {e}')

def get_last_uid():
    if os.path.exists(LAST_MAIL_FILE):
        with open(LAST_MAIL_FILE, 'r') as f:
            return int(f.read().strip())
    return 0

def save_last_uid(uid):
    with open(LAST_MAIL_FILE, 'w') as f:
        f.write(str(uid))

def read_mails():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL, PASSWORD)
        mail.select('inbox')
        last_uid = get_last_uid()
        _, data = mail.uid('search', None, f'UID {last_uid+1}:*')
        if not data[0]:
            print('📭 Pas de nouveaux mails')
            mail.logout()
            return
        uids = data[0].split()
        if not uids or (len(uids) == 1 and int(uids[0]) <= last_uid):
            print('📭 Pas de nouveaux mails')
            mail.logout()
            return
        print(f'📬 {len(uids)} nouveau(s) mail(s) !')
        speak(f'Vous avez {len(uids)} nouveaux mails')
        for uid in uids:
            uid = int(uid)
            if uid <= last_uid:
                continue
            _, msg_data = mail.uid('fetch', str(uid), '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            from_header = decode_header(msg.get('From'))[0]
            if isinstance(from_header[0], bytes):
                from_str = from_header[0].decode(from_header[1] or 'utf-8')
            else:
                from_str = from_header[0]
            subject_header = decode_header(msg.get('Subject'))[0]
            if isinstance(subject_header[0], bytes):
                subject_str = subject_header[0].decode(subject_header[1] or 'utf-8')
            else:
                subject_str = subject_header[0]
            print(f'📧 De: {from_str}')
            print(f'📧 Sujet: {subject_str}')
            speak(f'Mail de {from_str}')
            time.sleep(1)
            speak(f'Sujet: {subject_str}')
            time.sleep(1)
            save_last_uid(uid)
            time.sleep(2)
        mail.logout()
        print('✅ Mails lus !')
    except Exception as e:
        print(f'❌ Erreur: {e}')

if __name__ == '__main__':
    print('📧 Mail Reader Toth démarré...')
    read_mails()
