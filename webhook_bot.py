from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# CONFIG RENDER - Variables d'environnement
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "FLOKI2026") # Même que dans Meta
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_floki_reply(message_text, user_number):
    """Appelle Groq API pour avoir la réponse de FLOKI"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": "Tu es FLOKI, assistant WhatsApp du boss à Goma. Style congolais, direct, 1 phrase max. Pas de blabla. Tu réponds aux clients."
            },
            {"role": "user", "content": message_text}
        ],
        "max_tokens": 80,
        "temperature": 0.7
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        r.raise_for_status()
        reply = r.json()['choices'][0]['message']['content'].strip()
        logging.info(f"GROQ REPLY: {reply}")
        return reply
    except Exception as e:
        logging.error(f"GROQ ERROR: {e}")
        return "FLOKI bug chef, réessaye dans 1 min"

def send_whatsapp_message(to, text):
    """Envoie le message sur WhatsApp"""
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    r = requests.post(url, headers=headers, json=data)
    logging.info(f"WA SEND: {r.status_code} {r.text}")
    return r.status_code == 200

@app.route('/', methods=['GET'])
def home():
    return "FLOKI ASYMAS - ONLINE 🔥", 200

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Meta appelle ça pour vérifier ton webhook"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logging.info("WEBHOOK_VERIFIED")
        return challenge, 200
    else:
        logging.error("VERIFICATION_FAILED")
        return "Forbidden", 403

@app.route('/webhook', methods=['POST'])
def handle_message():
    """Meta envoie les messages WhatsApp ici"""
    try:
        data = request.get_json()
        logging.info(f"Received: {data}")

        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])

                    for msg in messages:
                        user_number = msg["from"]
                        user_text = msg["text"]["body"]

                        logging.info(f"MSG FROM {user_number}: {user_text}")

                        # 1. Appelle Groq pour réponse FLOKI
                        floki_reply = get_floki_reply(user_text, user_number)

                        # 2. Renvoie sur WhatsApp
                        send_whatsapp_message(user_number, floki_reply)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logging.error(f"GLOBAL ERROR: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
