import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date, datetime
from fpdf import FPDF
import base64
import io
import qrcode
from PIL import Image

# === CONFIG SUPABASE ===
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="ASYMAS BUSINESS", layout="wide", page_icon="💎")

# === CACHE TOUT STREAMLIT SAUF POUR LE PDG ===
st.markdown("""
    <style>
    #MainMenu {visibility: hidden!important;}
    header {visibility: hidden!important;}
 .stAppToolbar {display: none!important;}
    [data-testid="stToolbar"] {display: none!important;}
    [data-testid="stDecoration"] {display: none!important;}
    [data-testid="stHeader"] {display: none!important;}
    footer {visibility: hidden!important;}
 .stDeployButton {display:none!important;}
    [data-testid="stStatusWidget"] {display: none!important;}
    [data-testid="manage-app-button"] {display: none!important;}
    iframe[src*="streamlit.io"] {display: none!important;}
    button[kind="header"] {display: none!important;}
    div[data-testid="stBottomBlockContainer"] {display: none!important;}
 .st-emotion-cache-1wbqy5l {display: none!important;}
    button[title="Manage app"] {display: none!important;}
    a[href*="share.streamlit.io"] {display: none!important;}
    </style>
""", unsafe_allow_html=True)

# === SYSTÈME DE MOTS DE PASSE PERSISTANT DANS SUPABASE ===
@st.cache_data(ttl=10)
def load_passwords():
    try:
        data = supabase.table("utilisateurs").select("nom,role,password").execute()
        passwords = {}
        for user in data.data:
            passwords[user['role']] = user['password']
        return passwords
    except:
        return {
            "PDG": "tsang2024",
            "GERANTE": "asiya2024",
            "UTILISATEUR": "basam2024"
        }

passwords_db = load_passwords()

if 'user_role' not in st.session_state:
    st.session_state.user_role = None
    st.session_state.user_name = None

if st.session_state.user_role is None:
    st.markdown("# 🔐 ASYMAS BUSINESS - CONNEXION")

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("### Choisissez votre profil :")
        profil = st.selectbox("Utilisateur", ["-- Sélectionner --", "PDG TSANG", "Gérante ASIYA", "BASAM"])
        password = st.text_input("Mot de passe", type="password", key="pwd")

        if st.button("SE CONNECTER", width="stretch", type="primary"):
            if profil == "PDG TSANG" and password == passwords_db["PDG"]:
                st.session_state.user_role = "PDG"
                st.session_state.user_name = "TSANG"
                st.rerun()
            elif profil == "Gérante ASIYA" and password == passwords_db["GERANTE"]:
                st.session_state.user_role = "GERANTE"
                st.session_state.user_name = "ASIYA"
                st.rerun()
            elif profil == "BASAM" and password == passwords_db["UTILISATEUR"]:
                st.session_state.user_role = "UTILISATEUR"
                st.session_state.user_name = "BASAM"
                st.rerun()
            else:
                st.error("Profil ou mot de passe incorrect")
    st.stop()

# === CSS FOND BLANC SIMPLE SANS REFLETS ===
st.markdown("""
<style>
h1, h2, h3 {
    color: #00ff41!important;
    font-size: 2.2rem!important;
    font-weight: 900!important;
    padding: 10px 0!important;
    border-bottom: 3px solid #00ff41!important;
    margin-bottom: 20px!important;
}
div[data-testid="stMetricValue"] {color: #00ff41!important;}
.stButton>button {background-color: #00ff41!important; color: black!important; font-weight: bold; border: none;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_table(table_name):
    try:
        with st.spinner(f"Chargement {table_name}..."):
            data = supabase.table(table_name).select("*").order("id", desc=True).execute()
        return pd.DataFrame(data.data)
    except Exception as e:
        st.error(f"Erreur chargement {table_name}")
        st.code(repr(e))
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_table_columns(table_name):
    try:
        test = supabase.table(table_name).select("*").limit(1).execute()
        if test.data:
            return list(test.data[0].keys())
        return []
    except:
        return []

# === GÉNÉRER QR CODE OBLIGATOIRE ===
def generer_qrcode(data_text):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=1,
    )
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# === GÉNÉRATEUR PDF FACTURE - BENI RDC AVEC QR CODE ===
def generer_pdf_facture(numero, type_op, client, details_list, montant, devise, tel_client="+243...", periode=""):
    def clean_text(txt):
        return str(txt).encode('latin-1', 'replace').decode('latin-1')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_fill_color(20, 50, 40)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 20)
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, "ASYMAS BUSINESS", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(10, 16)
    pdf.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
    pdf.set_xy(10, 21)
    pdf.cell(0, 5, "Email: asamnesstsang636@gmail.com", ln=True)

    # === QR CODE OBLIGATOIRE EN HAUT DROITE ===
    qr_data = f"""ASYMAS BUSINESS
Facture: {numero}
Type: {type_op}
Client: {client}
Montant: {montant:,.0f} {devise}
Date: {date.today().strftime('%d/%m/%Y')}
Tel: +243 995 105 623"""
    qr_img_bytes = generer_qrcode(qr_data)
    pdf.image(io.BytesIO(qr_img_bytes), x=170, y=8, w=30)

    pdf.set_font("Arial", "B", 10)
    pdf.set_xy(150, 8)
    pdf.cell(50, 6, "FACTURE N°", ln=True, align="R")
    pdf.set_font("Arial", "", 10)
    pdf.set_xy(150, 14)
    pdf.cell(50, 6, clean_text(numero), ln=True, align="R")
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(150, 20)
    pdf.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")

    pdf.ln(15)

    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"FACTURE {clean_text(type_op.upper())}", ln=True, fill=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 10)
    pdf.set_draw_color(0, 0, 0)
    pdf.cell(90, 7, "FACTURE A:", 1, 0, 'L')
    pdf.cell(10, 7, "", 0, 0)
    pdf.cell(90, 7, "DETAILS PAIEMENT:", 1, 1, 'L')

    pdf.set_font("Arial", "", 9)
    pdf.cell(90, 6, f"Client: {clean_text(client)}", 'LR', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(90, 6, "M-Pesa: +243817264448", 'LR', 1, 'L')

    pdf.cell(90, 6, f"Tel: {clean_text(tel_client)}", 'LR', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(90, 6, "Echeance: Immediate", 'LR', 1, 'L')

    pdf.cell(90, 6, f"Date emission: {date.today().strftime('%d/%m/%Y')}", 'LRB', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(90, 6, "", 'LRB', 1, 'L')

    pdf.ln(8)

    pdf.set_fill_color(0, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(120, 8, "DESIGNATION", 1, 0, 'C', True)
    pdf.cell(30, 8, "QTE", 1, 0, 'C', True)
    pdf.cell(40, 8, f"MONTANT ({clean_text(devise)})", 1, 1, 'C', True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)

    if isinstance(details_list, list) and details_list:
        for item in details_list:
            nom = clean_text(item.get('nom', ''))
            qte = item.get('qte', 1)
            montant_item = item.get('prix', 0) * qte
            pdf.cell(120, 7, nom, 1, 0, 'L')
            pdf.cell(30, 7, str(qte), 1, 0, 'C')
            pdf.cell(40, 7, f"{montant_item:,.0f}", 1, 1, 'R')
    else:
        pdf.cell(120, 7, clean_text(details_list), 1, 0, 'L')
        pdf.cell(30, 7, "1", 1, 0, 'C')
        pdf.cell(40, 7, f"{montant:,.0f}", 1, 1, 'R')

    if periode:
        pdf.cell(120, 7, f"Periode: {clean_text(periode)}", 1, 0, 'L')
        pdf.cell(30, 7, "", 1, 0, 'C')
        pdf.cell(40, 7, "", 1, 1, 'R')

    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(150, 10, "MONTANT TOTAL A PAYER", 1, 0, 'R', True)
    pdf.cell(40, 10, f"{montant:,.0f} {clean_text(devise)}", 1, 1, 'R', True)

    return pdf.output(dest='S').encode('latin-1')

def creer_facture_auto(type_op, client, details, montant, devise="FC", details_list=None, tel="+243...", periode=""):
    numero_facture = f"AS-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    if details_list is None:
        details_list = [{"nom": details, "qte": 1, "prix": montant}]

    pdf_bytes = generer_pdf_facture(numero_facture, type_op, client, details_list, montant, devise, tel, periode)

    try:
        colonnes_compta = get_table_columns("compta")
        data_compta = {
            "type": "Revenu",
            "description": str(f"{type_op} - {client} - {details}"),
            "montant": float(montant),
            "date": str(date.today())
        }
        if "categorie" in colonnes_compta:
            data_compta["categorie"] = str(type_op)
        if "devise" in colonnes_compta:
            data_compta["devise"] = str(devise)

        supabase.table("compta").insert(data_compta).execute()
        st.toast(f"✅ Enregistré compta", icon="✅")
    except Exception as e:
        st.error("❌ ERREUR INSERTION COMPTA")
        st.code(repr(e))

    try:
        data_facture = {
            "numero_facture": str(numero_facture),
            "type_operation": str(type_op),
            "nom_client": str(client),
            "details": str(details),
            "montant": float(montant),
            "devise": str(devise),
            "date": str(date.today())
        }
        supabase.table("factures_proforma").insert(data_facture).execute()
        st.toast(f"✅ Enregistré factures", icon="✅")
    except Exception as e:
        st.warning("Table factures_proforma non trouvée - Crée-la dans Supabase")

    return numero_facture, pdf_bytes

df_biens = load_table("biens")
df_articles = load_table("articles")
df_voitures = load_table("voitures")
df_compta = load_table("compta")
df_factures = load_table("factures_proforma")
df_utilisateurs = load_table("utilisateurs")

st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
st.markdown("### Agriculture • Commerce • Immobilier • Automobile • Beni RDC")

with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.user_name}")
    st.markdown(f"**Rôle : {st.session_state.user_role}**")
    st.info("ASYMAS BUSINESS v1.0")

    if st.button("🔄 Actualiser", key="btn_save"):
        st.cache_data.clear()
        st.rerun()
    if st.button("🚪 DÉCONNEXION", key="logout", width="stretch"):
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.rerun()

if st.session_state.user_role == "UTILISATEUR":
    tab2, = st.tabs(["🛍️ Commerce"])
    tab1 = tab3 = tab4 = tab5 = tab6 = tab7 = tab8 = tab9 = None
elif st.session_state.user_role == "PDG":
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Dashboard", "🛍️ Commerce", "📦 Gestion Stock", "🏠 Immobilier", "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures", "👥 Utilisateurs"
    ])
else:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📊 Dashboard", "🛍️ Commerce", "📦 Gestion Stock", "🏠 Immobilier", "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures"
    ])
    tab9 = None

if tab1 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🏠 Biens", len(df_biens))
        col2.metric("📦 Articles", len(df_articles))
        col3.metric("🚗 Voitures", len(df_voitures))

        if not df_compta.empty and 'type' in df_compta.columns and 'montant' in df_compta.columns:
            revenus = df_compta[df_compta['type']=='Revenu']['montant'].sum()
            col4.metric("💰 Revenus", f"{revenus:,.0f} FC")
        elif not df_compta.empty:
            col4.metric("💰 Écritures", len(df_compta))
        else:
            col4.metric("💰 Revenus", "0 FC")

with tab2:
    st.markdown("## 🛍️ Commerce - Point de Vente")

    if 'panier_commerce' not in st.session_state:
        st.session_state.panier_commerce = []
    if 'vente_finie' not in st.session_state:
        st.session_state.vente_finie = False
    if 'pdf_data' not in st.session_state:
        st.session_state.pdf_data = None
    if 'num_fact' not in st.session_state:
        st.session_state.num_fact = None

    if df_articles.empty:
        st.error("Aucun article disponible - Ajoute des articles dans Gestion Stock")
    else:
        col_gauche, col_droite = st.columns([2,1])

        with col_gauche:
            st.subheader("👤 Client")
            nom_client = st.text_input("Nom Client", key="nom_client_c")
            tel_client = st.text_input("Téléphone Client", value="+243...", key="tel_client_c")

            st.subheader("📦 Rubrique Produit")
            recherche = st.text_input("🔍 Chercher un produit", placeholder="Tape le nom...", key="search_c")

            df_articles_filtre = df_articles.copy()
            if recherche:
                mask = df_articles['nom_article'].str.contains(recherche, case=False, na=False)
                df_articles_filtre = df_articles[mask]

            if not df_articles_filtre.empty:
                options = [f"{row['nom_article']} - {row.get('prix_vente',0):,.0f} FC - Stock:{row.get('stock','?')}" for _, row in df_articles_filtre.iterrows()]
                choix = st.selectbox("Choisir le produit", options, key="choix_prod_c")
                idx_choisi = options.index(choix)
                produit_choisi = df_articles_filtre.iloc[idx_choisi]

                c1, c2, c3 = st.columns([1,1,1])
                qte = c1.number_input("QTE", min_value=1, value=1, key="qte_c")
                c2.markdown(f"### Prix: **{produit_choisi.get('prix_vente',0):,.0f} FC**")

                if c3.button("➕ Ajouter au Panier", width="stretch", key="add_panier_c"):
                    stock_dispo = int(produit_choisi.get('stock', 0))
                    if stock_dispo < qte:
                        st.error(f"Stock insuffisant! Disponible: {stock_dispo}")
                        st.stop()
                    st.session_state.panier_commerce.append({
                        "id": int(produit_choisi['id']),
                        "nom": str(produit_choisi['nom_article']),
                        "prix": float(produit_choisi.get('prix_vente',0)),
                        "qte": int(qte),
                        "stock_dispo": stock_dispo
                    })
                    st.session_state.vente_finie = False
                    st.rerun()
            else:
                st.info("Aucun produit trouvé")

        with col_droite:
            st.subheader("🛒 Panier")
            total = 0

            if st.session_state.vente_finie and st.session_state.pdf_data:
                st.success(f"✅ Vente validée - {st.session_state.total_vente:,.0f} FC")
                st.info(f"📄 Facture: {st.session_state.num_fact}")
                st.download_button(
                    label="📥 Télécharger Facture PDF",
                    data=st.session_state.pdf_data,
                    file_name=f"{st.session_state.num_fact}.pdf",
                    mime="application/pdf",
                    width="stretch",
                    key="dl_facture_commerce"
                )
                # Bouton Imprimer
                pdf_b64 = base64.b64encode(st.session_state.pdf_data).decode()
                st.components.v1.html(f"""
                    <button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">
                        🖨️ IMPRIMER LA FACTURE
                    </button>
                    <script>
                    function printPDF() {{
                        const pdfData = 'data:application/pdf;base64,{pdf_b64}';
                        const win = window.open('', '_blank');
                        win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');
                        win.document.close();
                        setTimeout(() => {{ win.print(); }}, 1000);
                    }}
                    </script>
                """, height=60)
                if st.button("Nouvelle Vente", width="stretch", key="new_vente_c"):
                    st.session_state.panier_commerce = []
                    st.session_state.vente_finie = False
                    st.session_state.pdf_data = None
                    st.session_state.num_fact = None
                    st.rerun()
            elif not st.session_state.panier_commerce:
                st.info("Panier vide")
            else:
                for i, item in enumerate(st.session_state.panier_commerce):
                    with st.container(border=True):
                        st.markdown(f"**{item['nom']}**")
                        c1, c2 = st.columns([2,1])
                        new_qte = c1.number_input("QTE", min_value=1, value=item['qte'], key=f"qte_panier_c_{i}")
                        if new_qte > item.get('stock_dispo', 999):
                            st.error(f"Stock max: {item.get('stock_dispo', 999)}")
                            new_qte = item['qte']
                        st.session_state.panier_commerce[i]['qte'] = new_qte
                        sous_total = float(item['prix']) * int(st.session_state.panier_commerce[i]['qte'])
                        c2.markdown(f"**{sous_total:,.0f} FC**")
                        if st.button("❌ Supprimer", key=f"del_c_{i}"):
                            st.session_state.panier_commerce.pop(i)
                            st.rerun()
                        total += sous_total

                st.divider()
                st.markdown(f"### Total : **{total:,.0f} FC**")

                if st.button("💳 Finaliser Vente", type="primary", width="stretch", key="final_c"):
                    try:
                        if not nom_client or not st.session_state.panier_commerce:
                            st.warning("Nom client + panier requis")
                            st.stop()

                        with st.spinner("Enregistrement + Génération PDF..."):
                            id_utilisateur = 1
                            if st.session_state.user_name == "ASIYA":
                                id_utilisateur = 2
                            elif st.session_state.user_name == "BASAM":
                                id_utilisateur = 3

                            vente_result = supabase.table("ventes").insert({
                                "total": total,
                                "id_utilisateur": id_utilisateur,
                                "nom_client": nom_client,
                                "telephone_client": tel_client
                            }).execute()

                            id_vente = vente_result.data[0]['id']

                            for i in st.session_state.panier_commerce:
                                supabase.table("ventes_details").insert({
                                    "id_vente": id_vente,
                                    "id_article": i['id'],
                                    "quantite": i['qte'],
                                    "prix_unitaire": i['prix'],
                                    "sous_total": float(i['prix']) * int(i['qte'])
                                }).execute()
                                supabase.table("articles").update({"stock": i['stock_dispo'] - i['qte']}).eq("id", i['id']).execute()

                            details_list = [{"nom": i['nom'], "qte": i['qte'], "prix": i['prix']} for i in st.session_state.panier_commerce]
                            details_text = ", ".join([f"{i['nom']} x{i['qte']}" for i in st.session_state.panier_commerce])

                            num_fact, pdf_bytes = creer_facture_auto("Vente Commerce", nom_client, details_text, total, "FC", details_list, tel_client)

                            st.session_state.vente_finie = True
                            st.session_state.pdf_data = pdf_bytes
                            st.session_state.num_fact = num_fact
                            st.session_state.total_vente = total
                            st.session_state.panier_commerce = []
                            st.cache_data.clear()
                            st.rerun()

                    except Exception as e:
                        st.error(f"ERREUR SUPABASE : {e}")
                        st.code(str(e))

if tab3 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab3:
        st.markdown("## 📦 Gestion Stock - Articles")
        with st.expander("➕ Ajouter Nouvel Article"):
            with st.form("form_article", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nom = c1.text_input("Nom Article")
                cat = c2.text_input("Catégorie")
                prix_achat = c3.number_input("Prix Achat FC", min_value=0.0)
                prix_vente = c1.number_input("Prix Vente FC", min_value=0.0)
                stock = c2.number_input("Stock", min_value=0)

                if st.form_submit_button("💾 Ajouter Article"):
                    try:
                        supabase.table("articles").insert({
                            "nom_article": str(nom), "categorie": str(cat),
                            "prix_achat": float(prix_achat), "prix_vente": float(prix_vente), "stock": int(stock)
                        }).execute()
                        st.success("Article ajouté")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout")
                        st.code(repr(e))

        st.divider()
        st.subheader("📋 Liste des Articles - Modifier/Supprimer")
        if df_articles.empty:
            st.info("Aucun article")
        else:
            for _, row in df_articles.iterrows():
                with st.expander(f"{row['nom_article']} - {row.get('prix_vente',0):,.0f} FC - Stock:{row.get('stock',0)}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_nom = st.text_input("Nom", value=row['nom_article'], key=f"nom_{row['id']}")
                        new_cat = st.text_input("Catégorie", value=row.get('categorie',''), key=f"cat_{row['id']}")
                        new_prix_a = st.number_input("Prix Achat", value=float(row.get('prix_achat',0)), key=f"pa_{row['id']}")
                    with c2:
                        new_prix_v = st.number_input("Prix Vente", value=float(row.get('prix_vente',0)), key=f"pv_{row['id']}")
                        new_stock = st.number_input("Stock", value=int(row.get('stock',0)), key=f"stock_{row['id']}")

                    c1, c2 = st.columns(2)
                    if c1.button("✏️ Modifier", key=f"mod_art_{row['id']}", width="stretch"):
                        try:
                            supabase.table("articles").update({
                                "nom_article": str(new_nom), "categorie": str(new_cat),
                                "prix_achat": float(new_prix_a), "prix_vente": float(new_prix_v), "stock": int(new_stock)
                            }).eq("id", int(row['id'])).execute()
                            st.success("Modifié")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur modif")
                            st.code(repr(e))

                    if st.session_state.user_role == "PDG":
                        if c2.button("🗑️ Supprimer", key=f"del_art_{row['id']}", width="stretch"):
                            try:
                                supabase.table("articles").delete().eq("id", int(row['id'])).execute()
                                st.success("Supprimé")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur suppression")
                                st.code(repr(e))
                    else:
                        c2.info("🔒 Suppression réservée au PDG")

if tab4 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab4:
        st.markdown("## 🏠 Immobilier - Générer Facture")
        nom_client = st.text_input("👤 Nom du client", key="nom_client_bien")
        tel_client = st.text_input("Téléphone Client", value="+243...", key="tel_client_bien")
        col1, col2, col3 = st.columns(3)
        with col1:
            type_bien = st.selectbox("Type", ["Maison", "Appartement", "Bureau", "Terrain"], key="type_bien")
            adresse = st.text_input("Adresse", key="adresse_bien")
        with col2:
            prix = st.number_input("💰 Loyer USD", min_value=0.0, key="prix_bien")
            electricite = st.number_input("⚡ Électricité USD", min_value=0.0, key="elec_bien")
        with col3:
            eau = st.number_input("💧 Eau USD", min_value=0.0, key="eau_bien")
            duree_contrat = st.text_input("📅 Durée", placeholder="Ex: 6 mois", key="duree_bien")

        total_mensuel = float(prix) + float(electricite) + float(eau)
        st.info(f"💎 **TOTAL : {total_mensuel:,.2f} USD**")

        if st.button("📄 GÉNÉRER FACTURE PDF", type="primary", width="stretch", key="btn_facture_immo"):
            if nom_client and adresse:
                details_list = [
                    {"nom": f"Loyer {type_bien} | Adresse: {adresse} | Durée: {duree_contrat}", "qte": 1, "prix": prix},
                    {"nom": f"Electricite | {type_bien} - {adresse}", "qte": 1, "prix": electricite},
                    {"nom": f"Eau | {type_bien} - {adresse}", "qte": 1, "prix": eau}
                ]
                details_text = f"LOUER: {type_bien} | Adresse: {adresse} | Durée Contrat: {duree_contrat} | Loyer: {prix} $ | Electricité: {electricite} $ | Eau: {eau} $"
                periode = date.today().strftime("%B %Y")
                num_fact, pdf_bytes = creer_facture_auto("Loyer", nom_client, details_text, total_mensuel, "$", details_list, tel_client, periode)
                st.success(f"✅ Facture générée : {num_fact}")
                st.download_button(
                    label="📥 TÉLÉCHARGER LE PDF MAINTENANT",
                    data=pdf_bytes,
                    file_name=f"{num_fact}.pdf",
                    mime="application/pdf",
                    width="stretch",
                    key="dl_facture_immo"
                )
                # Bouton Imprimer
                pdf_b64 = base64.b64encode(pdf_bytes).decode()
                st.components.v1.html(f"""
                    <button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">
                        🖨️ IMPRIMER LA FACTURE
                    </button>
                    <script>
                    function printPDF() {{
                        const pdfData = 'data:application/pdf;base64,{pdf_b64}';
                        const win = window.open('', '_blank');
                        win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');
                        win.document.close();
                        setTimeout(() => {{ win.print(); }}, 1000);
                    }}
                    </script>
                """, height=60)
                st.cache_data.clear()
            else:
                st.error("Nom client + Adresse obligatoires")

if tab5 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab5:
        st.markdown("## 🚗 Automobile - Point de Vente")

        if 'panier_voiture' not in st.session_state:
            st.session_state.panier_voiture = []
        if 'vente_auto_finie' not in st.session_state:
            st.session_state.vente_auto_finie = False
        if 'pdf_auto' not in st.session_state:
            st.session_state.pdf_auto = None
        if 'num_fact_auto' not in st.session_state:
            st.session_state.num_fact_auto = None

        if df_voitures.empty:
            st.error("Aucune voiture disponible - Ajoute des voitures dans Gestion Parc")
        else:
            col_gauche, col_droite = st.columns([2,1])

            with col_gauche:
                st.subheader("👤 Client")
                nom_client = st.text_input("Nom Client", key="nom_client_v")
                tel_client = st.text_input("Téléphone Client", value="+243...", key="tel_client_v")

                st.subheader("🚗 Rubrique Véhicule")
                recherche_voiture = st.text_input("🔍 Chercher une voiture", placeholder="Marque, modèle, plaque...", key="search_v")

                df_voitures_filtre = df_voitures.copy()
                if recherche_voiture:
                    mask = df_voitures['marque'].str.contains(recherche_voiture, case=False, na=False) | \
                           df_voitures['modele'].str.contains(recherche_voiture, case=False, na=False) | \
                           df_voitures.get('plaque', pd.Series()).str.contains(recherche_voiture, case=False, na=False)
                    df_voitures_filtre = df_voitures[mask]

                if not df_voitures_filtre.empty:
                    options = []
                    for _, row in df_voitures_filtre.iterrows():
                        details = f"{row['marque']} {row['modele']} - {row.get('annee','')} - {row.get('plaque','')} - {row.get('prix',0):,.0f} $"
                        options.append(details)

                    choix = st.selectbox("Choisir le véhicule", options, key="choix_veh_v")
                    idx_choisi = options.index(choix)
                    voiture_choisie = df_voitures_filtre.iloc[idx_choisi]

                    with st.container(border=True):
                        st.markdown(f"### {voiture_choisie['marque']} {voiture_choisie['modele']}")
                        c1, c2, c3 = st.columns(3)
                        c1.markdown(f"**Année:** {voiture_choisie.get('annee','N/A')}")
                        c1.markdown(f"**Plaque:** {voiture_choisie.get('plaque','N/A')}")
                        c2.markdown(f"**Couleur:** {voiture_choisie.get('couleur','N/A')}")
                        km_val = voiture_choisie.get('kilometrage')
                        km_display = f"{int(km_val):,}" if km_val and str(km_val).isdigit() else 'N/A'
                        c2.markdown(f"**KM:** {km_display}")
                        c3.markdown(f"**Carburant:** {voiture_choisie.get('carburant','N/A')}")
                        c3.markdown(f"**Boîte:** {voiture_choisie.get('boite','N/A')}")
                        st.markdown(f"**Statut:** {voiture_choisie.get('statut','N/A')}")
                        st.markdown(f"### Prix: **{voiture_choisie.get('prix',0):,.0f} $**")
                    c1, c2 = st.columns([1,1])
                    qte = c1.number_input("QTE", min_value=1, value=1, key="qte_v")

                    if c2.button("➕ Ajouter au Panier", width="stretch", key="add_panier_v"):
                        if voiture_choisie.get('statut') == 'Vendue':
                            st.error("Cette voiture est déjà vendue!")
                            st.stop()
                        st.session_state.panier_voiture.append({
                            "id": int(voiture_choisie['id']),
                            "marque": str(voiture_choisie['marque']),
                            "modele": str(voiture_choisie['modele']),
                            "annee": str(voiture_choisie.get('annee','')),
                            "plaque": str(voiture_choisie.get('plaque','')),
                            "couleur": str(voiture_choisie.get('couleur','')),
                            "kilometrage": str(voiture_choisie.get('kilometrage','')),
                            "carburant": str(voiture_choisie.get('carburant','')),
                            "boite": str(voiture_choisie.get('boite','')),
                            "statut": str(voiture_choisie.get('statut','')),
                            "prix": float(voiture_choisie.get('prix',0)),
                            "qte": int(qte)
                        })
                        st.session_state.vente_auto_finie = False
                        st.rerun()
                else:
                    st.info("Aucune voiture trouvée")

            with col_droite:
                st.subheader("🛒 Panier")
                total = 0

                if st.session_state.vente_auto_finie and st.session_state.pdf_auto:
                    st.success(f"✅ Vente validée - {st.session_state.total_auto:,.0f} $")
                    st.info(f"📄 Facture PDF générée: {st.session_state.num_fact_auto}")
                    st.download_button(
                        label="📥 TÉLÉCHARGER LE PDF MAINTENANT",
                        data=st.session_state.pdf_auto,
                        file_name=f"{st.session_state.num_fact_auto}.pdf",
                        mime="application/pdf",
                        width="stretch",
                        key="dl_facture_auto"
                    )
                    # Bouton Imprimer
                    pdf_b64 = base64.b64encode(st.session_state.pdf_auto).decode()
                    st.components.v1.html(f"""
                        <button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">
                            🖨️ IMPRIMER LA FACTURE
                        </button>
                        <script>
                        function printPDF() {{
                            const pdfData = 'data:application/pdf;base64,{pdf_b64}';
                            const win = window.open('', '_blank');
                            win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');
                            win.document.close();
                            setTimeout(() => {{ win.print(); }}, 1000);
                        }}
                        </script>
                    """, height=60)
                    if st.button("Nouvelle Vente", width="stretch", key="new_vente_auto"):
                        st.session_state.panier_voiture = []
                        st.session_state.vente_auto_finie = False
                        st.session_state.pdf_auto = None
                        st.session_state.num_fact_auto = None
                        st.rerun()
                elif not st.session_state.panier_voiture:
                    st.info("Panier vide")
                else:
                    for i, item in enumerate(st.session_state.panier_voiture):
                        with st.container(border=True):
                            st.markdown(f"**{item['marque']} {item['modele']}**")
                            st.caption(f"Année: {item.get('annee','')} | Plaque: {item.get('plaque','')} | Couleur: {item.get('couleur','')}")
                            st.caption(f"KM: {item.get('kilometrage','')} | Carburant: {item.get('carburant','')} | Boîte: {item.get('boite','')}")
                            c1, c2 = st.columns([2,1])
                            st.session_state.panier_voiture[i]['qte'] = c1.number_input("QTE", min_value=1, value=item['qte'], key=f"qte_panier_v_{i}")
                            sous_total = float(item['prix']) * int(st.session_state.panier_voiture[i]['qte'])
                            c2.markdown(f"**{sous_total:,.0f} $**")
                            if st.button("❌ Supprimer", key=f"del_v_{i}"):
                                st.session_state.panier_voiture.pop(i)
                                st.rerun()
                            total += sous_total

                    st.divider()
                    st.markdown(f"### Total : **{total:,.0f} $**")

                if st.button("💳 Finaliser Vente", type="primary", width="stretch", key="btn_facture_auto"):
                    try:
                        if not nom_client or not st.session_state.panier_voiture:
                            st.warning("Nom client + panier requis")
                            st.stop()

                        with st.spinner("Enregistrement vente..."):
                            total = sum(float(i['prix']) * int(i['qte']) for i in st.session_state.panier_voiture)

                            id_utilisateur = 1
                            if st.session_state.user_name == "ASIYA":
                                id_utilisateur = 2
                            elif st.session_state.user_name == "BASAM":
                                id_utilisateur = 3

                            vente_result = supabase.table("ventes").insert({
                                "total": total,
                                "id_utilisateur": id_utilisateur,
                                "nom_client": nom_client,
                                "telephone_client": tel_client
                            }).execute()

                            id_vente = vente_result.data[0]['id']

                            for i in st.session_state.panier_voiture:
                                supabase.table("ventes_details").insert({
                                    "id_vente": id_vente,
                                    "id_voiture": i['id'],
                                    "quantite": i['qte'],
                                    "prix_unitaire": i['prix'],
                                    "sous_total": float(i['prix']) * int(i['qte'])
                                }).execute()
                                try:
                                    supabase.table("voitures").update({"statut": "Vendue"}).eq("id", i['id']).execute()
                                except:
                                    pass

                            details_list = []
                            for i in st.session_state.panier_voiture:
                                nom_complet = f"{i['marque']} {i['modele']} | Année: {i.get('annee','')} | Plaque: {i.get('plaque','')} | Couleur: {i.get('couleur','')}"
                                details_list.append({"nom": nom_complet, "qte": i['qte'], "prix": i['prix']})

                            # ON GÉNÈRE LE PDF MAIS ON L'INSÈRE JAMAIS DANS SUPABASE
                            num_fact, pdf_bytes = creer_facture_auto("Vente Auto", nom_client, f"Vente {len(st.session_state.panier_voiture)} véhicule(s)", total, "$", details_list, tel_client)

                            st.session_state.vente_auto_finie = True
                            st.session_state.pdf_auto = pdf_bytes
                            st.session_state.num_fact_auto = num_fact
                            st.session_state.total_auto = total
                            st.session_state.panier_voiture = []
                            st.cache_data.clear()
                            st.rerun()

                    except Exception as e:
                        st.error(f"ERREUR SUPABASE : {e}")
                        st.code(str(e))

if tab6 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab6:
        st.markdown("## 🚘 Gestion Parc - Voitures")

        colonnes_voitures = get_table_columns("voitures")

        with st.expander("➕ Ajouter Nouvelle Voiture"):
            with st.form("form_voiture", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                marque = c1.text_input("Marque")
                modele = c2.text_input("Modèle")
                annee = c3.number_input("Année", min_value=1990, max_value=2026, value=2020)
                plaque = c1.text_input("Plaque")

                data_insert = {
                    "marque": str(marque),
                    "modele": str(modele),
                    "annee": int(annee),
                    "plaque": str(plaque)
                }

                if "couleur" in colonnes_voitures:
                    couleur = c2.text_input("Couleur")
                    data_insert["couleur"] = str(couleur)
                if "kilometrage" in colonnes_voitures:
                    km = c3.number_input("Kilométrage", min_value=0, value=0)
                    data_insert["kilometrage"] = int(km)
                if "carburant" in colonnes_voitures:
                    carburant = c1.selectbox("Carburant", ["Essence", "Diesel", "Hybride", "Électrique"])
                    data_insert["carburant"] = str(carburant)
                if "boite" in colonnes_voitures:
                    boite = c2.selectbox("Boîte", ["Manuelle", "Automatique"])
                    data_insert["boite"] = str(boite)

                statut = c3.selectbox("Statut", ["Disponible", "Vendue", "Réservée"])
                prix = c1.number_input("Prix USD", min_value=0.0)

                data_insert["statut"] = str(statut)
                data_insert["prix"] = float(prix)

                if st.form_submit_button("💾 Ajouter Voiture"):
                    try:
                        supabase.table("voitures").insert(data_insert).execute()
                        st.success("Voiture ajoutée")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout")
                        st.code(repr(e))

        st.divider()
        st.subheader("📋 Liste des Voitures - Modifier/Supprimer")

        if df_voitures.empty:
            st.info("Aucune voiture")
        else:
            for _, row in df_voitures.iterrows():
                with st.expander(f"{row['marque']} {row['modele']} - {row.get('annee','')} - {row.get('prix',0):,.0f} $"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        new_marque = st.text_input("Marque", value=row['marque'], key=f"marque_{row['id']}")
                        new_modele = st.text_input("Modèle", value=row['modele'], key=f"modele_{row['id']}")
                        new_annee = st.number_input("Année", value=int(row.get('annee',2020)), key=f"annee_{row['id']}")
                        new_plaque = st.text_input("Plaque", value=row.get('plaque',''), key=f"plaque_{row['id']}")

                    data_update = {
                        "marque": str(new_marque),
                        "modele": str(new_modele),
                        "annee": int(new_annee),
                        "plaque": str(new_plaque)
                    }

                    with c2:
                        if "couleur" in colonnes_voitures:
                            new_couleur = st.text_input("Couleur", value=row.get('couleur',''), key=f"couleur_{row['id']}")
                            data_update["couleur"] = str(new_couleur)
                        if "kilometrage" in colonnes_voitures:
                            km_val = row.get('kilometrage')
                            new_km = st.number_input("KM", value=int(km_val) if km_val and str(km_val).isdigit() else 0, key=f"km_{row['id']}")
                            data_update["kilometrage"] = int(new_km)
                        if "carburant" in colonnes_voitures:
                            new_carburant = st.selectbox("Carburant", ["Essence", "Diesel", "Hybride", "Électrique"],
                                                        index=["Essence", "Diesel", "Hybride", "Électrique"].index(row.get('carburant','Essence')) if row.get('carburant') in ["Essence", "Diesel", "Hybride", "Électrique"] else 0,
                                                        key=f"carb_{row['id']}")
                            data_update["carburant"] = str(new_carburant)

                    with c3:
                        if "boite" in colonnes_voitures:
                            new_boite = st.selectbox("Boîte", ["Manuelle", "Automatique"],
                                                   index=["Manuelle", "Automatique"].index(row.get('boite','Manuelle')) if row.get('boite') in ["Manuelle", "Automatique"] else 0,
                                                   key=f"boite_{row['id']}")
                            data_update["boite"] = str(new_boite)
                        new_statut = st.selectbox("Statut", ["Disponible", "Vendue", "Réservée"],
                                                index=["Disponible", "Vendue", "Réservée"].index(row.get('statut','Disponible')) if row.get('statut') in ["Disponible", "Vendue", "Réservée"] else 0,
                                                key=f"statut_{row['id']}")
                        new_prix = st.number_input("Prix", value=float(row.get('prix',0)), key=f"prix_{row['id']}")
                        data_update["statut"] = str(new_statut)
                        data_update["prix"] = float(new_prix)

                    c1, c2 = st.columns(2)
                    if c1.button("✏️ Modifier", key=f"mod_voit_{row['id']}", width="stretch"):
                        try:
                            supabase.table("voitures").update(data_update).eq("id", int(row['id'])).execute()
                            st.success("Modifié")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur modif")
                            st.code(repr(e))

                    if st.session_state.user_role == "PDG":
                        if c2.button("🗑️ Supprimer", key=f"del_voit_{row['id']}", width="stretch"):
                            try:
                                supabase.table("voitures").delete().eq("id", int(row['id'])).execute()
                                st.success("Supprimé")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur suppression")
                                st.code(repr(e))
                    else:
                        c2.info("🔒 Suppression réservée au PDG")

if tab7 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab7:
        st.markdown("## 💰 Comptabilité - Générer Facture + Relevé")

        with st.expander("📄 Générer Facture Comptable", expanded=False):
            col1, col2, col3 = st.columns(3)
            type_op = col1.selectbox("Type", ["Revenu", "Dépense"], key="type_compta")
            montant = col2.number_input("Montant", min_value=0.0, key="montant_compta")
            devise = col3.selectbox("Devise", ["FC", "$", "€"], key="devise_compta")
            categorie = col1.selectbox("Catégorie", ["Vente Commerce", "Vente Auto", "Loyer", "Salaire", "Carburant", "Autre"], key="cat_compta")

            description = st.text_input("Description", key="desc_compta")
            nom_client = st.text_input("Nom Client/Bénéficiaire", key="nom_compta")
            tel_client = st.text_input("Téléphone", value="+243...", key="tel_compta")

            if st.button("📄 GÉNÉRER FACTURE PDF", type="primary", width="stretch", key="btn_facture_compta"):
                if description and nom_client:
                    details_list = [{"nom": f"{categorie} - {description}", "qte": 1, "prix": montant}]
                    num_fact, pdf_bytes = creer_facture_auto("Compta", nom_client, f"{categorie} - {description}", montant, devise, details_list, tel_client)

                    st.success(f"✅ Facture générée : {num_fact}")
                    st.download_button(
                        label="📥 TÉLÉCHARGER LE PDF MAINTENANT",
                        data=pdf_bytes,
                        file_name=f"{num_fact}.pdf",
                        mime="application/pdf",
                        width="stretch",
                        key="dl_facture_compta"
                    )
                    # Bouton Imprimer
                    pdf_b64 = base64.b64encode(pdf_bytes).decode()
                    st.components.v1.html(f"""
                        <button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">
                            🖨️ IMPRIMER LA FACTURE
                        </button>
                        <script>
                        function printPDF() {{
                            const pdfData = 'data:application/pdf;base64,{pdf_b64}';
                            const win = window.open('', '_blank');
                            win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');
                            win.document.close();
                            setTimeout(() => {{ win.print(); }}, 1000);
                        }}
                        </script>
                    """, height=60)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Description + Nom client obligatoires")

        st.divider()

        st.subheader("📊 Relevé Comptable - Classé par Catégorie")

        if df_compta.empty:
            st.warning("Aucune écriture comptable.")
        else:
            col_f1, col_f2 = st.columns(2)
            filtre_type = col_f1.selectbox("Filtrer Type", ["Tous", "Revenu", "Dépense"], key="filtre_type_compta")
            filtre_cat = col_f2.selectbox("Filtrer Catégorie", ["Toutes"] + list(df_compta.get('categorie', pd.Series()).dropna().unique()), key="filtre_cat_compta")

            df_filtre = df_compta.copy()
            if filtre_type!= "Tous":
                df_filtre = df_filtre[df_filtre['type'] == filtre_type]
            if filtre_cat!= "Toutes":
                df_filtre = df_filtre[df_filtre.get('categorie', '') == filtre_cat]

            df_filtre = df_filtre.sort_values('date', ascending=False)

            col_t1, col_t2, col_t3, col_t4 = st.columns(4)
            total_revenu = df_filtre[df_filtre['type']=='Revenu']['montant'].sum()
            total_depense = df_filtre[df_filtre['type']=='Dépense']['montant'].sum()
            solde = total_revenu - total_depense
            col_t1.metric("💰 Total Revenus", f"{total_revenu:,.0f}")
            col_t2.metric("💸 Total Dépenses", f"{total_depense:,.0f}")
            col_t3.metric("💎 Solde", f"{solde:,.0f}")
            col_t4.metric("📋 Écritures", len(df_filtre))

            st.divider()

            if 'categorie' in df_filtre.columns:
                categories = df_filtre['categorie'].dropna().unique()
                for cat in sorted(categories):
                    df_cat = df_filtre[df_filtre['categorie'] == cat]
                    total_cat = df_cat['montant'].sum()

                    with st.expander(f"📁 {cat} - {len(df_cat)} opérations - Total: {total_cat:,.0f}", expanded=True):
                        st.dataframe(
                            df_cat[['date', 'type', 'description', 'montant', 'devise']],
                            use_container_width=True,
                            hide_index=True
                        )
            else:
                st.dataframe(
                    df_filtre[['date', 'type', 'description', 'montant']],
                    use_container_width=True,
                    hide_index=True
                )

            st.divider()

            col_dl1, col_dl2 = st.columns(2)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtre.to_excel(writer, sheet_name='Releve_Comptable', index=False)
                if 'categorie' in df_filtre.columns:
                    for cat in df_filtre['categorie'].dropna().unique():
                        df_cat = df_filtre[df_filtre['categorie'] == cat]
                        df_cat.to_excel(writer, sheet_name=cat[:30], index=False)

            col_dl1.download_button(
                label="📥 TÉLÉCHARGER RELEVÉ EXCEL",
                data=output.getvalue(),
                file_name=f"Releve_Compta_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
                key="dl_releve_excel"
            )

            pdf_releve = FPDF()
            pdf_releve.add_page()
            pdf_releve.set_auto_page_break(auto=True, margin=15)

            pdf_releve.set_fill_color(20, 50, 40)
            pdf_releve.rect(0, 0, 210, 35, 'F')
            pdf_releve.set_text_color(255, 255, 255)
            pdf_releve.set_font("Arial", "B", 20)
            pdf_releve.set_xy(10, 8)
            pdf_releve.cell(0, 10, "ASYMAS BUSINESS", ln=True)
            pdf_releve.set_font("Arial", "", 9)
            pdf_releve.set_xy(10, 16)
            pdf_releve.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
            pdf_releve.set_xy(10, 21)
            pdf_releve.cell(0, 5, "Email: asamnesstsang636@gmail.com", ln=True)

            pdf_releve.set_font("Arial", "B", 10)
            pdf_releve.set_xy(150, 8)
            pdf_releve.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")

            pdf_releve.ln(15)

            pdf_releve.set_text_color(0, 0, 0)
            pdf_releve.set_fill_color(255, 204, 0)
            pdf_releve.set_font("Arial", "B", 14)
            pdf_releve.cell(0, 10, "RELEVE COMPTABLE", ln=True, fill=True)
            pdf_releve.ln(5)

            pdf_releve.set_font("Arial", "B", 11)
            pdf_releve.cell(0, 8, f"Total Revenus: {total_revenu:,.0f} | Total Depenses: {total_depense:,.0f} | Solde: {solde:,.0f}", ln=True)
            pdf_releve.ln(3)

            pdf_releve.set_font("Arial", "B", 9)
            pdf_releve.cell(25, 7, "Date", 1)
            pdf_releve.cell(25, 7, "Type", 1)
            pdf_releve.cell(90, 7, "Description", 1)
            pdf_releve.cell(30, 7, "Montant", 1)
            pdf_releve.cell(20, 7, "Devise", 1, ln=True)

            pdf_releve.set_font("Arial", "", 8)
            for _, row in df_filtre.iterrows():
                pdf_releve.cell(25, 6, str(row.get('date','')), 1)
                pdf_releve.cell(25, 6, str(row.get('type','')), 1)
                desc = str(row.get('description',''))[:45]
                pdf_releve.cell(90, 6, desc, 1)
                pdf_releve.cell(30, 6, f"{row.get('montant',0):,.0f}", 1)
                pdf_releve.cell(20, 6, str(row.get('devise','FC')), 1, ln=True)

            pdf_bytes_releve = pdf_releve.output(dest='S').encode('latin-1')

            col_dl2.download_button(
                label="📥 TÉLÉCHARGER RELEVÉ PDF",
                data=pdf_bytes_releve,
                file_name=f"Releve_Compta_{date.today().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                width="stretch",
                key="dl_releve_pdf"
            )

if tab8 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab8:
        st.markdown("## 📄 Factures - Relevé Général depuis Comptabilité")

        st.caption(f"Debug: {len(df_compta)} écritures comptables trouvées")

        if df_compta.empty:
            st.warning("Aucune écriture comptable.")
            st.info("👉 Fais une vente dans Commerce, Immobilier ou Automobile pour voir le relevé ici")
        else:
            df_compta_sorted = df_compta.sort_values('date', ascending=False)

            c1, c2, c3, c4 = st.columns(4)
            total_fc = df_compta_sorted[df_compta_sorted.get('devise','FC')=='FC']['montant'].sum()
            total_usd = df_compta_sorted[df_compta_sorted.get('devise','FC')=='$']['montant'].sum()
            total_eur = df_compta_sorted[df_compta_sorted.get('devise','FC')=='€']['montant'].sum()
            c1.metric("📄 Total Écritures", len(df_compta_sorted))
            c2.metric("💰 Total FC", f"{total_fc:,.0f} FC")
            c3.metric("💵 Total USD", f"{total_usd:,.0f} $")
            c4.metric("💶 Total EUR", f"{total_eur:,.0f} €")

            st.divider()

            categories_fact = ["Toutes"] + list(df_compta_sorted.get('categorie', pd.Series()).dropna().unique())
            filtre_cat_fact = st.selectbox("📂 Filtrer par Catégorie", categories_fact, key="filtre_cat_fact")

            df_filtre_fact = df_compta_sorted.copy()
            if filtre_cat_fact!= "Toutes":
                df_filtre_fact = df_filtre_fact[df_filtre_fact.get('categorie', '') == filtre_cat_fact]

            st.divider()

            categories = df_filtre_fact.get('categorie', pd.Series()).dropna().unique()

            for cat in sorted(categories):
                df_cat = df_filtre_fact[df_filtre_fact.get('categorie', '') == cat]
                total_cat_fc = df_cat[df_cat.get('devise','FC')=='FC']['montant'].sum()
                total_cat_usd = df_cat[df_cat.get('devise','FC')=='$']['montant'].sum()
                total_cat_eur = df_cat[df_cat.get('devise','FC')=='€']['montant'].sum()

                with st.expander(f"📁 {cat} - {len(df_cat)} opérations | FC: {total_cat_fc:,.0f} | $: {total_cat_usd:,.0f} | €: {total_cat_eur:,.0f}", expanded=True):

                    st.dataframe(
                        df_cat[['date', 'type', 'description', 'montant', 'devise']],
                        use_container_width=True,
                        hide_index=True
                    )

                    col_dl1, col_dl2 = st.columns(2)

                    output_cat = io.BytesIO()
                    with pd.ExcelWriter(output_cat, engine='openpyxl') as writer:
                        df_cat.to_excel(writer, sheet_name=cat[:30], index=False)

                    col_dl1.download_button(
                        label=f"📥 Télécharger {cat} - EXCEL",
                        data=output_cat.getvalue(),
                        file_name=f"Releve_{cat}_{date.today().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width="stretch",
                        key=f"dl_excel_cat_{cat}"
                    )

                    pdf_cat = FPDF()
                    pdf_cat.add_page()

                    pdf_cat.set_fill_color(20, 50, 40)
                    pdf_cat.rect(0, 0, 210, 35, 'F')
                    pdf_cat.set_text_color(255, 255, 255)
                    pdf_cat.set_font("Arial", "B", 20)
                    pdf_cat.set_xy(10, 8)
                    pdf_cat.cell(0, 10, "ASYMAS BUSINESS", ln=True)
                    pdf_cat.set_font("Arial", "", 9)
                    pdf_cat.set_xy(10, 16)
                    pdf_cat.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
                    pdf_cat.set_xy(10, 21)
                    pdf_cat.cell(0, 5, "Email: asamnesstsang636@gmail.com", ln=True)

                    pdf_cat.set_font("Arial", "B", 10)
                    pdf_cat.set_xy(150, 8)
                    pdf_cat.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")

                    pdf_cat.ln(15)

                    pdf_cat.set_text_color(0, 0, 0)
                    pdf_cat.set_fill_color(255, 204, 0)
                    pdf_cat.set_font("Arial", "B", 14)
                    pdf_cat.cell(0, 10, f"RELEVE - {cat.upper()}", ln=True, fill=True)
                    pdf_cat.ln(5)

                    pdf_cat.set_font("Arial", "B", 11)
                    pdf_cat.cell(0, 8, f"Total FC: {total_cat_fc:,.0f} | Total USD: {total_cat_usd:,.0f} | Total EUR: {total_cat_eur:,.0f}", ln=True)
                    pdf_cat.ln(3)

                    pdf_cat.set_font("Arial", "B", 9)
                    pdf_cat.cell(25, 7, "Date", 1)
                    pdf_cat.cell(25, 7, "Type", 1)
                    pdf_cat.cell(90, 7, "Description", 1)
                    pdf_cat.cell(30, 7, "Montant", 1)
                    pdf_cat.cell(20, 7, "Devise", 1, ln=True)

                    pdf_cat.set_font("Arial", "", 8)
                    for _, row in df_cat.iterrows():
                        pdf_cat.cell(25, 6, str(row.get('date','')), 1)
                        pdf_cat.cell(25, 6, str(row.get('type','')), 1)
                        desc = str(row.get('description',''))[:45]
                        pdf_cat.cell(90, 6, desc, 1)
                        pdf_cat.cell(30, 6, f"{row.get('montant',0):,.0f}", 1)
                        pdf_cat.cell(20, 6, str(row.get('devise','FC')), 1, ln=True)

                    pdf_bytes_cat = pdf_cat.output(dest='S').encode('latin-1')

                    col_dl2.download_button(
                        label=f"📥 Télécharger {cat} - PDF",
                        data=pdf_bytes_cat,
                        file_name=f"Releve_{cat}_{date.today().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        width="stretch",
                        key=f"dl_pdf_cat_{cat}"
                    )

            st.divider()

            st.subheader("📥 Télécharger Relevé Complet Toutes Catégories")
            col_dl_g1, col_dl_g2 = st.columns(2)

            output_global = io.BytesIO()
            with pd.ExcelWriter(output_global, engine='openpyxl') as writer:
                df_compta_sorted.to_excel(writer, sheet_name='Toutes_Operations', index=False)
                for cat in categories:
                    df_cat = df_compta_sorted[df_compta_sorted.get('categorie', '') == cat]
                    df_cat.to_excel(writer, sheet_name=cat[:30], index=False)

            col_dl_g1.download_button(
                label="📥 TÉLÉCHARGER TOUTES LES OPÉRATIONS - EXCEL",
                data=output_global.getvalue(),
                file_name=f"Releve_Complet_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
                key="dl_excel_global"
            )

            pdf_global = FPDF()
            pdf_global.add_page()

            pdf_global.set_fill_color(20, 50, 40)
            pdf_global.rect(0, 0, 210, 35, 'F')
            pdf_global.set_text_color(255, 255, 255)
            pdf_global.set_font("Arial", "B", 20)
            pdf_global.set_xy(10, 8)
            pdf_global.cell(0, 10, "ASYMAS BUSINESS", ln=True)
            pdf_global.set_font("Arial", "", 9)
            pdf_global.set_xy(10, 16)
            pdf_global.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
            pdf_global.set_xy(10, 21)
            pdf_global.cell(0, 5, "Email: asamnesstsang636@gmail.com", ln=True)

            pdf_global.set_font("Arial", "B", 10)
            pdf_global.set_xy(150, 8)
            pdf_global.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")

            pdf_global.ln(15)

            pdf_global.set_text_color(0, 0, 0)
            pdf_global.set_fill_color(255, 204, 0)
            pdf_global.set_font("Arial", "B", 14)
            pdf_global.cell(0, 10, "RELEVE GENERAL COMPLET", ln=True, fill=True)
            pdf_global.ln(5)

            pdf_global.set_font("Arial", "B", 11)
            pdf_global.cell(0, 8, f"Total FC: {total_fc:,.0f} | Total USD: {total_usd:,.0f} | Total EUR: {total_eur:,.0f}", ln=True)
            pdf_global.ln(3)

            for cat in sorted(categories):
                df_cat = df_compta_sorted[df_compta_sorted.get('categorie', '') == cat]
                total_cat_fc = df_cat[df_cat.get('devise','FC')=='FC']['montant'].sum()
                total_cat_usd = df_cat[df_cat.get('devise','FC')=='$']['montant'].sum()

                pdf_global.set_font("Arial", "B", 12)
                pdf_global.cell(0, 8, f"CATEGORIE: {cat} - {len(df_cat)} operations", ln=True)
                pdf_global.set_font("Arial", "B", 10)
                pdf_global.cell(0, 6, f"Total: FC {total_cat_fc:,.0f} | USD {total_cat_usd:,.0f}", ln=True)
                pdf_global.ln(2)

                pdf_global.set_font("Arial", "B", 9)
                pdf_global.cell(25, 7, "Date", 1)
                pdf_global.cell(25, 7, "Type", 1)
                pdf_global.cell(90, 7, "Description", 1)
                pdf_global.cell(30, 7, "Montant", 1)
                pdf_global.cell(20, 7, "Devise", 1, ln=True)

                pdf_global.set_font("Arial", "", 8)
                for _, row in df_cat.iterrows():
                    pdf_global.cell(25, 6, str(row.get('date','')), 1)
                    pdf_global.cell(25, 6, str(row.get('type','')), 1)
                    desc = str(row.get('description',''))[:45]
                   
