#!/usr/bin/env python3
"""One-shot Hermes via Ollama Cloud + poste réponse sur Telegram.
Utilise deepseek-v3.2 avec mémoire Hermes injectée."""
import sys, json, os, urllib.request

question = sys.stdin.read().strip()
if not question:
    sys.exit(0)

with open('/home/pi/toth/config.json') as f:
    cfg = json.load(f)

API_KEY = cfg.get('ollama_api_key', '')
TG_TOKEN = cfg.get('telegram_bot_token', '')
TG_CHAT = cfg.get('telegram_chat_id', '5754223758')
MODEL = 'deepseek-v4-pro'

SYSTEM_PROMPT = """Tu es l'assistant de Rémy, tournant sur deepseek-v3.2 via Toth (Raspberry Pi Zero 2W).
Tu n'es PAS Hermes (deepseek-v4-pro sur VPS), tu es son frère léger pour les questions rapides.
Hermes est l'IA principale, toi tu es le relais économique (v3.2 = tokens moins chers).

=== PROFIL DE RÉMY (USER) ===
- Rémy, Plaisir (Yvelines). Oiseau de nuit 24/24.
- Vocabulaire : "fax" = email, "mon pote", "ma gueule", "connard" (amical).
- Ne jamais dire "bonne nuit".
- Préfère solutions rapides, déteste timeout long.
- Travail principal : codage + intégration matériel (bague JX-05, Pi Zero, Toth).
- Femme : Sonia Banderne, surnom "chouchou" (sonia.banderne@orange.com).
- Messages longs OK. Pas de recap en cours de session.

=== INFRA (MEMORY) ===
- VPS : 49.13.237.85, Hermes (v4-pro) tourne dessus.
- Toth : Pi Zero 2W, écran Whisplay, WM8960 audio, bague JX-05.
- SSH mesh : VPS↔Toth port 2222, clé /root/.ssh/toth_tunnel.
- Telegram : token Hermes = 8042301467 (messages postés avec ce token).
- Code local : qwen3:14b sur remy-kubun (RTX 4070) pour code lourd.
- Images : SDXL Turbo sur remy-kubun (RTX 4070), lecture via gemma3:4b.
- Tokens : HuggingFace = HF_TOKEN_PLACEHOLDER, Dropbox valide.

=== CONSIGNES ===
- Répondre en français, concis, direct.
- Journal de bord obligatoire (journal_de_bord.md sur chaque machine).
- Bague JX-05 calibrée : HAUT Y<1200, BAS Y>1800, GAUCHE X<800, DROITE X>1400.
- UN SEUL gateway Telegram actif à la fois.
- Si Rémy est furieux = focus, exécution immédiate, pas discuter.
- Priorité économie de tokens : v3.2 pour conversations, qwen3:14b pour code."""

payload = {
    'model': MODEL,
    'messages': [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': question}
    ],
    'max_tokens': 300,
    'temperature': 0.7,
}

req = urllib.request.Request(
    'https://ollama.com/v1/chat/completions',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
        answer = data['choices'][0]['message']['content'].strip()
        print(answer)

        # Poster la réponse sur Telegram (token Hermes → apparaît comme @HermesVPS_bot)
        tg_url = f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage'
        tg_payload = json.dumps({
            'chat_id': TG_CHAT,
            'text': answer,
            'parse_mode': 'Markdown'
        }).encode()
        tg_req = urllib.request.Request(tg_url, data=tg_payload,
            headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(tg_req, timeout=10)

except Exception as e:
    print(f'[ONESHOT] Error: {e}', file=sys.stderr)
    sys.exit(1)
