#!/usr/bin/env python3
"""Test simple connexion Gmail"""
import imaplib
import json
import os

CONFIG_FILE = "/home/pi/toth/voice_mail_config.json"

with open(CONFIG_FILE) as f:
    cfg = json.load(f)

print("🔑 Connexion Gmail...")
try:
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    mail.login(cfg['gmail_email'], cfg['gmail_app_password'])
    mail.select('inbox')
    print("✅ Connexion OK !")
    
    _, data = mail.uid('search', None, 'UNSEEN')
    uids = data[0].split()
    print(f"📬 {len(uids)} mails non lus")
    
    if uids:
        for uid in uids[:3]:
            _, msg_data = mail.uid('fetch', uid, '(RFC822)')
            raw = msg_data[0][1]
            import email
            msg = email.message_from_bytes(raw)
            print(f"📧 De: {msg.get('From', 'Inconnu')[:50]}")
            print(f"📧 Sujet: {msg.get('Subject', 'Sans sujet')[:50]}")
            print("---")
    
    mail.logout()
    print("✅ Test terminé !")
except Exception as e:
    print(f"❌ Erreur: {e}")
