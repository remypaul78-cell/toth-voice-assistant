#!/usr/bin/env python3
"""
Toth Voice Mail - Système vocal pour gérer les mails
Commandes vocales :
- "mes mails" → Lit les nouveaux mails
- "suivant" → Mail suivant
- "efface" → Efface le mail courant
- "réponds" → Prépare une réponse (dictée)
- "stop" → Arrête la lecture
"""

import os
import time
import subprocess
import requests
import json
import imaplib
import email
from email.header import decode_header

# ============ CONFIG ============
CONFIG_FILE = "/home/pi/toth/voice_mail_config.json"

def load_config():
    """Charge la config (clés API, mots de passe)"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        "groq_api_key": "",
        "gmail_app_password": "",
        "gmail_email": "remypaul78@gmail.com",
        "button_pin": 17,
        "record_duration": 5,
        "last_uid_file": "/home/pi/toth/.last_mail_uid"
    }

def save_config(cfg):
    """Sauvegarde la config"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)

# ============ AUDIO ============
def speak(text):
    """Prononce sur WM8960 via espeak. Bloquant pour éviter superposition."""
    try:
        clean = text.replace("'", "\\'")[:300]
        cmd = f"espeak -v fr -s 150 '{clean}' --stdout | ffmpeg -i - -ac 2 -ar 48000 -f alsa hw:0,0 -y 2>/dev/null"
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        print(f"🔊 {clean[:80]}...")
    except subprocess.TimeoutExpired:
        print(f"🔊 TTS timeout")
    except Exception as e:
        print(f"❌ TTS: {e}")

def record_audio(duration=5):
    """Enregistre l'audio du micro WM8960"""
    try:
        cmd = f"arecord -D hw:0,0 -d {duration} -f cd -t wav /tmp/voice_cmd.wav 2>/dev/null"
        subprocess.run(cmd, shell=True, timeout=duration+2)
        return "/tmp/voice_cmd.wav"
    except Exception as e:
        print(f"❌ Enregistrement: {e}")
        return None

def transcribe_audio(audio_file, cfg):
    """Transcrit l'audio avec Groq Whisper"""
    try:
        with open(audio_file, "rb") as f:
            response = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {cfg['groq_api_key']}"},
                files={"file": f},
                data={"model": "whisper-large-v3", "language": "fr", "response_format": "json"},
                timeout=30
            )
        text = response.json().get("text", "").lower().strip()
        print(f"🎤 Transcription: {text}")
        return text
    except Exception as e:
        print(f"❌ Transcription: {e}")
        return ""

# ============ MAILS ============
def get_last_uid(cfg):
    """Récupère le dernier UID lu"""
    if os.path.exists(cfg['last_uid_file']):
        with open(cfg['last_uid_file'], 'r') as f:
            return int(f.read().strip())
    return 0

def save_last_uid(uid, cfg):
    """Sauvegarde le dernier UID lu"""
    with open(cfg['last_uid_file'], 'w') as f:
        f.write(str(uid))

def read_new_mails(cfg):
    """Lit les nouveaux mails Gmail"""
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        mail.login(cfg['gmail_email'], cfg['gmail_app_password'])
        mail.select('inbox')
        
        last_uid = get_last_uid(cfg)
        _, data = mail.uid('search', None, f'UID {last_uid+1}:*')
        
        if not data[0]:
            speak("Vous n'avez pas de nouveaux mails.")
            mail.logout()
            return []
        
        uids = [int(u) for u in data[0].split() if int(u) > last_uid]
        if not uids:
            speak("Vous n'avez pas de nouveaux mails.")
            mail.logout()
            return []
        
        speak(f"Vous avez {len(uids)} nouveaux mails.")
        
        mails = []
        for uid in sorted(uids):
            _, msg_data = mail.uid('fetch', str(uid), '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Décoder l'expéditeur
            from_hdr = decode_header(msg.get('From', 'Inconnu'))[0]
            from_str = from_hdr[0].decode(from_hdr[1] or 'utf-8') if isinstance(from_hdr[0], bytes) else from_hdr[0]
            
            # Décoder le sujet
            subj_hdr = decode_header(msg.get('Subject', 'Sans sujet'))[0]
            subj_str = subj_hdr[0].decode(subj_hdr[1] or 'utf-8') if isinstance(subj_hdr[0], bytes) else subj_hdr[0]
            
            mails.append({
                'uid': uid,
                'from': from_str,
                'subject': subj_str,
                'date': msg.get('Date', 'Date inconnue')
            })
        
        mail.logout()
        return mails
        
    except Exception as e:
        speak(f"Erreur lors de la lecture des mails: {str(e)[:50]}")
        return []

def delete_mail(uid, cfg):
    """Efface un mail par UID"""
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        mail.login(cfg['gmail_email'], cfg['gmail_app_password'])
        mail.select('inbox')
        mail.uid('STORE', str(uid), '+FLAGS', '\\Deleted')
        mail.expunge()
        mail.logout()
        speak("Mail effacé.")
        return True
    except Exception as e:
        speak(f"Erreur lors de la suppression: {str(e)[:50]}")
        return False

# ============ MAIN ============
def main():
    cfg = load_config()
    
    # Vérifier que les clés sont configurées
    if not cfg.get('groq_api_key'):
        speak("Configuration incomplète. Veuillez configurer la clé Groq.")
        print(f"⚠️  Éditez {CONFIG_FILE} pour ajouter vos clés API")
        return
    
    if not cfg.get('gmail_app_password'):
        speak("Configuration incomplète. Veuillez configurer le mot de passe Gmail.")
        print(f"⚠️  Éditez {CONFIG_FILE} pour ajouter le mot de passe Gmail")
        return
    
    speak("Système vocal mail activé. Appuyez sur le bouton et parlez.")
    print("=" * 50)
    print("Toth Voice Mail - Commandes:")
    print("  'mes mails' → Lit les nouveaux mails")
    print("  'suivant'   → Passe au mail suivant")
    print("  'efface'    → Efface le mail courant")
    print("  'réponds'   → Prépare une réponse")
    print("  'stop'      → Arrête la lecture")
    print("=" * 50)
    
    # Mode interactif (pour test)
    mails = []
    current_index = 0
    
    while True:
        try:
            print("\n🎤 Appuyez sur Entrée pour enregistrer une commande (ou tapez le texte)")
            print("   (Ctrl+C pour quitter)")
            user_input = input("> ").strip().lower()
            
            if not user_input:
                # Enregistrement vocal
                speak("J'écoute.")
                audio_file = record_audio(cfg['record_duration'])
                if audio_file:
                    user_input = transcribe_audio(audio_file, cfg)
                else:
                    speak("Je n'ai pas compris.")
                    continue
            
            # Traitement des commandes
            if "mail" in user_input or "mails" in user_input or "message" in user_input:
                speak("Je vérifie vos mails.")
                mails = read_new_mails(cfg)
                current_index = 0
                
                if mails:
                    mail = mails[current_index]
                    speak(f"Premier mail. De {mail['from']}. Sujet: {mail['subject']}")
                    save_last_uid(mail['uid'], cfg)
                    
            elif "suivant" in user_input or "next" in user_input:
                if mails and current_index < len(mails) - 1:
                    current_index += 1
                    mail = mails[current_index]
                    speak(f"Mail suivant. De {mail['from']}. Sujet: {mail['subject']}")
                    save_last_uid(mail['uid'], cfg)
                else:
                    speak("Il n'y a pas d'autre mail.")
                    
            elif "efface" in user_input or "supprime" in user_input or "delete" in user_input:
                if mails and current_index < len(mails):
                    mail = mails[current_index]
                    if delete_mail(mail['uid'], cfg):
                        mails.pop(current_index)
                        if current_index >= len(mails):
                            current_index = max(0, len(mails) - 1)
                else:
                    speak("Aucun mail à effacer.")
                    
            elif "répond" in user_input or "réponds" in user_input or "reply" in user_input:
                if mails and current_index < len(mails):
                    mail = mails[current_index]
                    speak(f"Préparation de la réponse à {mail['from']}. Dites votre message.")
                    # TODO: Enregistrer la réponse et l'envoyer
                else:
                    speak("Aucun mail pour répondre.")
                    
            elif "stop" in user_input or "arrête" in user_input:
                speak("Arrêt de la lecture.")
                
            elif "quitte" in user_input or "exit" in user_input or "bye" in user_input:
                speak("Au revoir.")
                break
                
            else:
                speak("Je n'ai pas compris. Dites: mes mails, suivant, efface, réponds, ou stop.")
                
        except KeyboardInterrupt:
            speak("Au revoir.")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
            time.sleep(1)

if __name__ == '__main__':
    main()
