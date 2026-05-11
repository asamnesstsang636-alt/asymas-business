from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# CONFIG
STREAMLIT_URL = "https://ypglhjpmflkj8lxvqsetao.streamlit.app/"  # ← REMPLACE AVEC TA VRAIE URL
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = "FLOKI2026"  # ← MÊME TOKEN QUE DANS META

@app.route('/', methods=['GET'])
def home():
    return "FLOKI ASYMAS - ONLINE", 200

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
                    for msg in value.get("messages", []):
                        user_number = msg["from"]
                        user_text = msg["text"]["body"]
                        
                        logging.info(f"MSG FROM {user_number}: {user_text}")

                        # 1. Appelle Streamlit FLOKI
                        try:
                            r = requests.post(
                                f"{STREAMLIT_URL}/api/floki",
                                json={"message": user_text, "user": user_number},
                                timeout=15
                            )
                            r.raise_for_status()
                            floki_reply = r.json().get("reply", "FLOKI ne répond pas.")
                        except Exception as e:
                            logging.error(f"STREAMLIT ERROR: {e}")
                            floki_reply = "FLOKI KO. Erreur serveur."

                        # 2. Renvoie sur WhatsApp
                        url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
                        headers = {
                            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                            "Content-Type": "application/json"
                        }
                        data_out = {
                            "messaging_product": "whatsapp",
                            "to": user_number,
                            "text": {"body": floki_reply}
                        }
                        wa_response = requests.post(url, headers=headers, json=data_out)
                        logging.info(f"WA SEND: {wa_response.status_code}")

        return jsonify({"status": "ok"}), 200
    
    except Exception as e:
        logging.error(f"GLOBAL ERROR: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
