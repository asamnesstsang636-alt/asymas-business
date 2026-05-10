from flask import Flask, request, jsonify
import requests, os, json
from supabase import create_client, Client
from groq import Groq
from datetime import datetime, date

app = Flask(__name__)

# === CONFIG - TES VRAIES CLÉS ===
META_TOKEN = os.getenv("META_TOKEN", "EAA8PVIKSui0BRUZC7kFoO99B2TTDrEwwTZB3sL66lEMNBeLdiqsiHD9c3l") # Mets dans Render
PHONE_ID = os.getenv("PHONE_ID", "1049697111568187") # Mets dans Render
VERIFY_TOKEN = "asymas2024" # Garde celui-là pour Meta

# SUPABASE - Même base que ton Streamlit
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# GROQ - Cerveau IA
GROQ_CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY"))

# === FONCTION ENVOI WHATSAPP ===
def send_whatsapp(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {META_TOKEN}", "Content-Type": "application/json"}
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text[:4096]} # Limite WhatsApp
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        return r.json()
    except:
        return None

# === CERVEAU ASYMAS - IL LIT TA BASE SUPABASE ===
def cerveau_asymas(message_client, numero_client):
    # 1. Récupère contexte live depuis Supabase
    contexte_db = ""
    try:
        # Compta du jour
        today = str(date.today())
        compta_jour = supabase.table("compta").select("type,montant,description").eq("date", today).execute()
        revenus = sum(float(x['montant']) for x in compta_jour.data if x['type']=='Revenu')
        depenses = sum(float(x['montant']) for x in compta_jour.data if x['type']=='Depense')

        # Stock top 5
        articles = supabase.table("articles").select("nom_article,prix_vente,stock").gt("stock",0).limit(5).execute()
        stock_txt = "\n".join([f"- {a['nom_article']}: {a['prix_vente']:,.0f}FC Stock:{a['stock']}" for a in articles.data])

        # Voitures dispo
        voitures = supabase.table("voitures").select("marque,modele,prix").eq("statut","Disponible").limit(3).execute()
        voitures_txt = "\n".join([f"- {v['marque']} {v['modele']}: {v['prix']:,.0f}$" for v in voitures.data])

        contexte_db = f"""
        COMPTA AUJOURD'HUI: Revenu {revenus:,.0f}FC | Dépense {depenses:,.0f}FC | Bénéfice {revenus-depenses:,.0f}FC
        STOCK DISPO:
        {stock_txt if stock_txt else 'Aucun'}
        VOITURES DISPO:
        {voitures_txt if voitures_txt else 'Aucune'}
        """
    except Exception as e:
        contexte_db = "Base temporairement inaccessible"

    prompt_systeme = f"""
    Tu es SAMY TSANGYA, PDG ASYMAS BUSINESS Beni RDC. Tel: +243 995 105 623.
    Tu gères TOUT: compta, stock, voitures, immobilier, conseils.
    Tu parles direct, congolais, 2 lignes max. Pas de "Bonjour".

    DONNÉES LIVE ASYMAS:
    {contexte_db}

    RÈGLES STRICTES:
    1. Si "situation", "bilan", "chiffre" → Donne bénéfice du jour + 1 conseil action
    2. Si "prix" + nom produit → Donne prix exact du stock + "Tape 1 pour commander"
    3. Si "facture" + nom + produit + montant → Réponds "OK je prépare. Confirme nom client"
    4. Si "voiture" → Liste 1-2 voitures dispo avec prix
    5. Si tu connais pas → "Pas en stock chef. Tu veux que je commande?"
    6. Finis TOUJOURS par une action: "Tape 1", "Dis OUI", "Envoie photo"
    """

    try:
        chat = GROQ_CLIENT.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_systeme},
                {"role": "user", "content": message_client}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=200
        )
        return chat.choices[0].message.content.strip()
    except Exception as e:
        return "Cerveau ASYMAS en maintenance. Réessaie dans 1min chef."

# === WEBHOOK META ===
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # Vérification Meta
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Token invalide", 403

    # Réception message WhatsApp
    if request.method == "POST":
        data = request.json
        try:
            entry = data['entry'][0]['changes'][0]['value']
            if 'messages' not in entry:
                return jsonify({"status": "no_message"}), 200

            msg = entry['messages'][0]
            numero = msg['from'] # 243995105623
            texte = msg['text']['body']
            nom_whatsapp = entry['contacts'][0]['profile']['name']

            # 1. Log dans Supabase
            supabase.table("conversations").insert({
                "numero": numero,
                "nom_client": nom_whatsapp,
                "message": texte,
                "date": datetime.now().isoformat(),
                "sens": "recu"
            }).execute()

            # 2. Cerveau ASYMAS réfléchit
            reponse = cerveau_asymas(texte, numero)

            # 3. Envoie réponse WhatsApp
            send_whatsapp(numero, reponse)

            # 4. Log réponse
            supabase.table("conversations").insert({
                "numero": numero,
                "nom_client": "ASYMAS BOT",
                "message": reponse,
                "date": datetime.now().isoformat(),
                "sens": "envoye"
            }).execute()

        except Exception as e:
            print(f"Erreur webhook: {e}")

        return jsonify({"status": "ok"}), 200

# === TEST SANTE ===
@app.route("/", methods=["GET"])
def home():
    return "ASYMAS BOT WEBHOOK ACTIF ✅", 200

if __name__ == "__main__":
    app.run(port=5000, debug=False)
