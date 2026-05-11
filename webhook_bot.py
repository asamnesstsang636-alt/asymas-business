from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

STREAMLIT_URL = "https://ton-app.streamlit.app"  # METS TON URL STREAMLIT ICI
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

@app.route('/')
def home():
    return "FLOKI ASYMAS - ONLINE"

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
                        floki_reply = r.json().get("reply", "Erreur FLOKI")
                        
                        # Renvoie WhatsApp
                        url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
                        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
                        data_out = {
                            "messaging_product": "whatsapp",
                            "to": user_number,
                            "text": {"body": floki_reply}
                        }
                        requests.post(url, headers=headers, json=data_out)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"ERREUR: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()
