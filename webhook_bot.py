from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

STREAMLIT_URL = "https://asymas-floki.streamlit.app" # ← METS TA VRAIE URL
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

@app.route('/')
def home():
    return "FLOKI ASYMAS - ONLINE"

@app.route('/webhook', methods=['GET'])
def verify():
    # Meta vérifie le webhook ici
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    VERIFY_TOKEN = "FLOKI2026" # ← METS LE MÊME DANS META

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    for msg in value.get("messages", []):
                        user_number = msg["from"]
                        user_text = msg["text"]["body"]

                        # Appelle Streamlit
                        r = requests.post(f"{STREAMLIT_URL}/api/floki",
                                        json={"message": user_text, "user": user_number},
                                        timeout=10)
                        r.raise_for_status()
                        floki_reply = r.json().get("reply", "FLOKI dort. Reviens dans 1min.")

                        # Renvoie WhatsApp
                        url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
                        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
                        data_out = {
                            "messaging_product": "whatsapp",
                            "to": user_number,
                            "text": {"body": floki_reply}
                        }
                        requests.post(url, headers=headers, json=data_out)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"ERREUR /chat: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()
