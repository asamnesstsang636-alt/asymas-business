from flask import Flask, request, jsonify
import requests, os, json
from supabase import create_client, Client
from groq import Groq
from datetime import datetime, date

app = Flask(__name__)
from flask_cors import CORS
CORS(app)

# === CONFIG ===
META_TOKEN = os.getenv("META_TOKEN")
PHONE_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "asymas_webhook_verify")

# SUPABASE
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# GROQ
GROQ_CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY"))

def send_whatsapp(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {META_TOKEN}", "Content-Type": "application/json"}
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text[:4096]}
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"WhatsApp sent: {r.status_code}")
        return r.json()
    except Exception as e:
        print(f"Erreur envoi WhatsApp: {e}")
        return None

def get_snapshot():
    try:
        today = str(date.today())
        compta_jour = supabase.table("compta").select("type,montant").eq("date", today).execute()
        revenus = sum(float(x['montant']) for x in compta_jour.data if x['type']=='Revenu')
        depenses = sum(float(x['montant']) for x in compta_jour.data if x['type']=='Depense')
        ruptures = supabase.table("articles").select("nom_article").lt("stock", 5).execute()
        return f"CA J: {revenus-depenses:,.0f}FC | Alertes: {len(ruptures.data)} ruptures"
    except Exception as e:
        print(f"Erreur Snapshot: {e}")
        return "CA J: 0FC | Alertes: 0 ruptures"

def cerveau_asymas(message_client, numero_client):
    snapshot = get_snapshot()
    prompt_systeme = f"""
    Tu es FLOKI, agent de terrain d'ASYMAS BUSINESS Beni RDC.
    Style: Militaire. Sec. Exécutant. Tu attends les ordres. Zéro blabla.
    SNAPSHOT LIVE: {snapshot}
    MESSAGE DU BOSS: {message_client}
    RÈGLES STRICTES:
    1. Si le boss dit "Slt", "Yo", "Floki", "Situation": Réponds UNIQUEMENT: "FLOKI. {snapshot}. Ordres?"
    2. Si ordre clair: "Ventes", "Stock", "Bilan", "1", "Dettes", "Voiture": Exécute. 3 lignes max. Chiffres + 1 action. Termine par "Autre?"
    3. Si "Prix" + produit: Donne prix + stock Supabase. "Autre?"
    4. Si message flou: Réponds: "Ordre flou. 1.Ventes 2.Stock 3.Caisse 4.Voitures. Choix?"
    5. INTERDIT: Bonjour, émojis, conseils non demandés, phrases longues.
    6. Max 160 caractères. Tu es un agent, pas un bavard.
    """
    try:
        chat = GROQ_CLIENT.chat.completions.create(
            messages=[{"role": "system", "content": prompt_systeme}, {"role": "user", "content": message_client}],
            model="llama-3.3-70b-versatile", temperature=0.1, max_tokens=120
        )
        return chat.choices[0].message.content.strip()
    except Exception as e:
        print(f"Erreur Groq: {e}")
        return "Système down. Réessaie."

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Forbidden", 403
    if request.method == "POST":
        data = request.json
        try:
            entry = data['entry'][0]['changes'][0]['value']
            if 'messages' not in entry:
                return jsonify({"status": "no_message"}), 200
            msg = entry['messages'][0]
            numero = msg['from']
            nom_whatsapp = entry['contacts'][0]['profile']['name']
            if msg['type'] == 'text':
                texte = msg['text']['body']
            elif msg['type'] == 'audio':
                audio_id = msg['audio']['id']
                audio_url_req = requests.get(f"https://graph.facebook.com/v20.0/{audio_id}", headers={"Authorization": f"Bearer {META_TOKEN}"})
                audio_url = audio_url_req.json()['url']
                audio_file = requests.get(audio_url, headers={"Authorization": f"Bearer {META_TOKEN}"})
                transcription = GROQ_CLIENT.audio.transcriptions.create(file=("audio.ogg", audio_file.content), model="whisper-large-v3", language="fr")
                texte = transcription.text
            else:
                return jsonify({"status": "unsupported_type"}), 200
            supabase.table("conversations").insert({"numero": numero, "nom_client": nom_whatsapp, "message": texte, "date": datetime.now().isoformat(), "sens": "recu"}).execute()
            reponse = cerveau_asymas(texte, numero)
            send_whatsapp(numero, reponse)
            supabase.table("conversations").insert({"numero": numero, "nom_client": "FLOKI ASYMAS", "message": reponse, "date": datetime.now().isoformat(), "sens": "envoye"}).execute()
        except Exception as e:
            print(f"Erreur webhook: {e}")
        return jsonify({"status": "ok"}), 200

@app.route("/chat", methods=["POST"])
def chat_web():
    try:
        data = request.json
        message = data.get("message", "")
        numero = data.get("numero", "WEB_TSANG")
        reponse = cerveau_asymas(message, numero)
        return jsonify({"reponse": reponse})
    except Exception as e:
        print(f"Erreur /chat: {e}")
        return jsonify({"reponse": "Erreur serveur FLOKI"}), 500

@app.route("/chat/transcribe", methods=["POST"])
def transcribe_web():
    try:
        audio_file = request.files['audio']
        transcription = GROQ_CLIENT.audio.transcriptions.create(file=("audio.webm", audio_file.read()), model="whisper-large-v3", language="fr")
        return jsonify({"text": transcription.text})
    except Exception as e:
        print(f"Erreur /chat/transcribe: {e}")
        return jsonify({"text": ""}), 500

@app.route("/", methods=["GET"])
def home():
    return "FLOKI ASYMAS ACTIF ✅", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
