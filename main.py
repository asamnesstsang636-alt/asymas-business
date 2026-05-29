import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json
import base64
import difflib
import re
import urllib.parse
import requests
from fpdf import FPDF
from supabase import create_client, Client

# === CONFIG SUPABASE ===
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="ASYMAS BUSINESS", layout="wide", page_icon="📊")

# === SESSION STATE ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'show_circle_menu' not in st.session_state:
    st.session_state.show_circle_menu = False
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "📊 Dashboard"
if 'user_role' not in st.session_state:
    st.session_state.user_role = ""
    st.session_state.user_name = ""
    st.session_state.perms = {}
    st.session_state.user_cats = []

# === FONCTION LOGIN ===
def login():
    st.markdown("""
    <style>
  .circle-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 75vh;
        background: radial-gradient(circle at center, #FFD700 0%, #1a1a2e 70%);
        border-radius: 20px;
        margin: 20px 0;
        position: relative;
    }
  .center-btn {
        position: absolute;
        top: 45%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 160px;
        height: 160px;
        background: linear-gradient(135deg, #FFD700, #FFA500);
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        font-weight: bold;
        font-size: 20px;
        color: #000;
        box-shadow: 0 0 40px #FFD700;
        z-index: 10;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="circle-container"><div class="center-btn">🛒<br>ASYMAS</div></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2,2,2])
    with col2:
        pwd = st.text_input("Mot de passe", type="password", key="login_pwd")
        if st.button("🔓 Accéder", width="stretch"):
            try:
                result = supabase.table("utilisateurs").select("*").eq("password", pwd).execute()
                if result.data:
                    user = result.data[0]
                    st.session_state.logged_in = True
                    st.session_state.show_circle_menu = True
                    st.session_state.user_name = user['nom']
                    st.session_state.user_role = user['role']
                    st.session_state.perms = user.get('permissions', {})
                    st.session_state.user_cats = user.get('categories_autorisees', [])
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")
            except Exception as e:
                st.error(f"Erreur connexion: {e}")

# === PAGE D'ACCUEIL LOGIN ===
if not st.session_state.logged_in:
    login()
    st.stop()

# === CHARGEMENT DONNEES ===
@st.cache_data
def load_data():
    return {
        "articles": pd.DataFrame(supabase.table("articles").select("*").execute().data or []),
        "compta": pd.DataFrame(supabase.table("compta").select("*").execute().data or []),
        "biens": pd.DataFrame(supabase.table("biens").select("*").execute().data or []),
        "voitures": pd.DataFrame(supabase.table("voitures").select("*").execute().data or []),
        "utilisateurs": pd.DataFrame(supabase.table("utilisateurs").select("*").execute().data or [])
    }

data = load_data()
df_articles = data["articles"]
df_compta = data["compta"]
df_biens = data["biens"]
df_voitures = data["voitures"]
df_utilisateurs = data["utilisateurs"]
perms = st.session_state.perms

# === MENU CIRCULAIRE ===
if st.session_state.show_circle_menu:
    st.markdown("""
    <style>
  .circle-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 75vh;
        background: radial-gradient(circle at center, #FFD700 0%, #1a1a2e 70%);
        border-radius: 20px;
        margin: 20px 0;
        position: relative;
    }
  .circle-menu {
        position: relative;
        width: 450px;
        height: 450px;
        border: 3px solid #FFD700;
        border-radius: 50%;
        animation: rotate 30s linear infinite;
    }
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
  .center-btn {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 160px;
        height: 160px;
        background: linear-gradient(135deg, #FFD700, #FFA500);
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        font-weight: bold;
        font-size: 20px;
        color: #000;
        box-shadow: 0 0 40px #FFD700;
        z-index: 10;
    }
    div[data-testid="stButton"] > button {
        background: white;
        color: black;
        font-weight: bold;
        border-radius: 50%;
        width: 90px;
        height: 90px;
        font-size: 12px;
        box-shadow: 0 0 15px #FFD700;
        animation: counter-rotate 30s linear infinite;
    }
    @keyframes counter-rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(-360deg); }
    }
    div[data-testid="stButton"] > button:hover {
        transform: scale(1.15);
        box-shadow: 0 0 25px #FFD700;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="circle-container"><div class="circle-menu">', unsafe_allow_html=True)
    st.markdown('<div class="center-btn">🛒<br>ASYMAS</div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    # Tous les boutons visibles, ouverture conditionnée
    col1, col2, col3 = st.columns([1,1,1])
    if col2.button("🏪\nCommerce", key="circle_Commerce", use_container_width=True):
        if perms.get('commerce', False) or st.session_state.user_role == "PDG":
            st.session_state.show_circle_menu = False
            st.session_state.active_tab = "🛍️ Commerce"
            st.rerun()
        else:
            st.error("⛔ Vous n'avez pas l'autorisation Commerce")

    col4, col5, col6 = st.columns([1,3,1])
    if col4.button("📊\nCompta", key="circle_Compta", use_container_width=True):
        if perms.get('comptabilite', False) or st.session_state.user_role == "PDG":
            st.session_state.show_circle_menu = False
            st.session_state.active_tab = "💰 Comptabilité"
            st.rerun()
        else:
            st.error("⛔ Vous n'avez pas l'autorisation Comptabilité")

    if col6.button("🚗\nAuto", key="circle_Auto", use_container_width=True):
        if perms.get('automobile', False) or st.session_state.user_role == "PDG":
            st.session_state.show_circle_menu = False
            st.session_state.active_tab = "🚗 Automobile"
            st.rerun()
        else:
            st.error("⛔ Vous n'avez pas l'autorisation Automobile")

    col7, col8, col9 = st.columns([1,1,1])
    if col7.button("📦\nStock", key="circle_Stock", use_container_width=True):
        if perms.get('stock', False) or st.session_state.user_role == "PDG":
            st.session_state.show_circle_menu = False
            st.session_state.active_tab = "📦 Gestion Stock"
            st.rerun()
        else:
            st.error("⛔ Vous n'avez pas l'autorisation Stock")

    if col8.button("🏠\nImmo", key="circle_Immo", use_container_width=True):
        if perms.get('immobilier', False) or st.session_state.user_role == "PDG":
            st.session_state.show_circle_menu = False
            st.session_state.active_tab = "🏠 Immobilier"
            st.rerun()
        else:
            st.error("⛔ Vous n'avez pas l'autorisation Immobilier")

    if col9.button("📄\nFactures", key="circle_Factures", use_container_width=True):
        if perms.get('factures', False) or st.session_state.user_role == "PDG":
            st.session_state.show_circle_menu = False
            st.session_state.active_tab = "📄 Factures"
            st.rerun()
        else:
            st.error("⛔ Vous n'avez pas l'autorisation Factures")

    st.divider()
    col_a, col_b = st.columns(2)
    if col_a.button("📋 Voir tous les onglets", width="stretch"):
        st.session_state.show_circle_menu = False
        st.rerun()
    if col_b.button("🔒 Déconnexion", width="stretch"):
        st.session_state.logged_in = False
        st.session_state.show_circle_menu = False
        st.rerun()
    st.stop()

# === SIDEBAR ===
with st.sidebar:
    st.markdown(f"**👤 {st.session_state.user_name}**")
    st.markdown(f"**Rôle: {st.session_state.user_role}**")
    if st.button("🏠 Retour Accueil"):
        st.session_state.show_circle_menu = True
        st.rerun()
    if st.button("🔒 Déconnexion"):
        st.session_state.logged_in = False
        st.session_state.show_circle_menu = False
        st.rerun()

# === TABS PRINCIPAUX ===
tab_names = [
    "📊 Dashboard", "🛍️ Commerce", "📦 Gestion Stock", "🏠 Immobilier",
    "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures",
    "📋 Devis", "👥 Utilisateurs"
]

# Filtrer les onglets selon permissions
allowed_tabs = ["📊 Dashboard"]
if perms.get('commerce') or st.session_state.user_role == "PDG": allowed_tabs.append("🛍️ Commerce")
if perms.get('stock') or st.session_state.user_role == "PDG": allowed_tabs.append("📦 Gestion Stock")
if perms.get('immobilier') or st.session_state.user_role == "PDG": allowed_tabs.append("🏠 Immobilier")
if perms.get('automobile') or st.session_state.user_role == "PDG": allowed_tabs.append("🚗 Automobile")
if perms.get('parc') or st.session_state.user_role == "PDG": allowed_tabs.append("🚘 Gestion Parc")
if perms.get('comptabilite') or st.session_state.user_role == "PDG": allowed_tabs.append("💰 Comptabilité")
if perms.get('factures') or st.session_state.user_role == "PDG": allowed_tabs.append("📄 Factures")
if perms.get('devis_industriel') or perms.get('devis_batiment') or st.session_state.user_role == "PDG": allowed_tabs.append("📋 Devis")
if perms.get('users') or st.session_state.user_role == "PDG": allowed_tabs.append("👥 Utilisateurs")

tab_map_list = st.tabs(allowed_tabs)
tab_map = {name: tab for name, tab in zip(allowed_tabs, tab_map_list)}

# === FONCTIONS UTILES ===
def get_table_columns(table_name):
    try:
        result = supabase.table(table_name).select("*").limit(1).execute()
        return list(result.data[0].keys()) if result.data else []
    except:
        return []

def safe_pdf_txt(text):
    if pd.isna(text) or text is None:
        return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def generer_pdf_facture(numero, categorie, client, details, total, devise, tel, periode=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(20, 50, 40)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 20)
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, "ASYMAS BUSINESS", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(10, 16)
    pdf.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
    pdf.set_font("Arial", "B", 10)
    pdf.set_xy(150, 8)
    pdf.cell(50, 6, f"Facture: {numero}", ln=True, align="R")
    pdf.set_xy(150, 14)
    pdf.cell(50, 6, f"Date: {date.today()}", ln=True, align="R")
    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"FACTURE - {safe_pdf_txt(categorie).upper()}", ln=True, fill=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"Client: {safe_pdf_txt(client)}", ln=True)
    pdf.cell(0, 8, f"Tel: {safe_pdf_txt(tel)}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(80, 7, "Designation", 1)
    pdf.cell(20, 7, "Qte", 1)
    pdf.cell(30, 7, "PU", 1)
    pdf.cell(30, 7, "Total", 1, ln=True)
    pdf.set_font("Arial", "", 9)
    for item in details:
        pdf.cell(80, 6, safe_pdf_txt(item['nom'])[:40], 1)
        pdf.cell(20, 6, str(item['qte']), 1)
        pdf.cell(30, 6, f"{item['pu']:,.0f}", 1)
        pdf.cell(30, 6, f"{item['qte']*item['pu']:,.0f}", 1, ln=True)
    pdf.ln(3)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(130, 8, "TOTAL:", 0)
    pdf.cell(30, 8, f"{total:,.0f} {devise}", 1, ln=True)
    return bytes(pdf.output(dest='S'))

def creer_facture_auto(categorie, client, details_text, total, devise, details_list, tel, periode="", statut="Proforma"):
    num_fact = f"FACT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    pdf_bytes = generer_pdf_facture(num_fact, categorie, client, details_list, total, devise, tel, periode)
    supabase.table("compta").insert({
        "date": str(date.today()),
        "type": "Revenu",
        "categorie": categorie,
        "description": f"{categorie} - {client}",
        "montant": float(total),
        "devise": devise,
        "numero_facture": num_fact,
        "details": json.dumps(details_list),
        "utilisateur": st.session_state.user_name
    }).execute()
    return num_fact, pdf_bytes

def generer_excel_pro(df, titre, total_rev, total_dep, solde):
    return b"Excel placeholder"

def generer_pdf_devis_consulting(numero, type_devis, client, titre, parcelle, loc, sections, devise, tel, mo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"DEVIS {type_devis} - {numero}", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Client: {client}", ln=True)
    pdf.cell(0, 8, f"Titre: {titre}", ln=True)
    return bytes(pdf.output(dest='S'))

def qrcode_scanner(key="qr"):
    return st.text_input("Scanner QR", key=key)

# === DASHBOARD ===
if "📊 Dashboard" in tab_map:
    with tab_map["📊 Dashboard"]:
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

# === COMMERCE ===
if "🛍️ Commerce" in tab_map:
    with tab_map["🛍️ Commerce"]:
        st.markdown("## 🛍️ Commerce - Point de Vente")
        if 'panier_commerce' not in st.session_state:
            st.session_state.panier_commerce = []
        if 'vente_finie' not in st.session_state:
            st.session_state.vente_finie = False
        if 'pdf_data' not in st.session_state:
            st.session_state.pdf_data = None
        if 'num_fact' not in st.session_state:
            st.session_state.num_fact = None
        if 'client_com_nom' not in st.session_state:
            st.session_state.client_com_nom = ""
        if 'client_com_tel' not in st.session_state:
            st.session_state.client_com_tel = "+243..."
        if 'last_qr' not in st.session_state:
            st.session_state.last_qr = ""

        col_gauche, col_droite = st.columns([2,1])
        with col_gauche:
            st.subheader("👤 Client")
            st.session_state.client_com_nom = st.text_input("Nom Client", value=st.session_state.client_com_nom, key="nom_client_c")
            st.session_state.client_com_tel = st.text_input("Téléphone Client", value=st.session_state.client_com_tel, key="tel_client_c")
            st.subheader("🔍 Scanner QR Code")
            col_scan1, col_scan2 = st.columns([2,1])
            with col_scan1:
                qr_code = qrcode_scanner(key='qr_commerce_unique')
            with col_scan2:
                recherche_manuelle = st.text_input("🔎 Recherche manuelle", placeholder="Tape le nom...", key="search_man_c")
            if qr_code and qr_code!= st.session_state.last_qr:
                st.session_state.last_qr = qr_code
                st.rerun()

            df_articles_filtre = df_articles[df_articles['stock'] > 0].copy() if not df_articles.empty else pd.DataFrame()
            if qr_code:
                qr_clean = str(qr_code).strip().upper()
                df_articles_filtre = df_articles_filtre[df_articles_filtre['code_qr'].astype(str).str.strip().str.upper() == qr_clean]
                if not df_articles_filtre.empty:
                    st.success(f"✅ QR Trouvé : {df_articles_filtre.iloc[0]['nom_article']}")
                else:
                    st.error(f"❌ QR {qr_code} : Produit introuvable")
            elif recherche_manuelle:
                mask = df_articles_filtre['nom_article'].str.contains(recherche_manuelle, case=False, na=False)
                df_articles_filtre = df_articles_filtre[mask]

            if df_articles_filtre.empty:
                st.warning("⚠️ Aucun produit disponible")
            else:
                st.success(f"✅ {len(df_articles_filtre)} produit(s) disponible(s)")
                options_articles = []
                for _, p in df_articles_filtre.iterrows():
                    qr_txt = f" | QR:{p['code_qr']}" if 'code_qr' in p and p['code_qr'] else ""
                    prix_usd = f" | {p['prix_vente_usd']:,.2f}$" if 'prix_vente_usd' in p else ""
                    options_articles.append(f"{p['nom_article']} | Stock:{int(p['stock'])} | {p['prix_vente']:,.0f} FC{prix_usd}{qr_txt} | ID:{p['id']}")
                article_choisi = st.selectbox("Sélectionne le produit", options_articles, key="select_article_unique")
                if article_choisi:
                    id_choisi = int(article_choisi.split("ID:")[1])
                    p = df_articles_filtre[df_articles_filtre['id'] == id_choisi].iloc[0]
                    c1, c2, c3 = st.columns(3)
                    qte_max = int(p['stock'])
                    qte = c1.number_input("Quantité", min_value=1, max_value=qte_max, value=1, key="qte_c_unique")
                    c2.metric("Stock dispo", qte_max)
                    c3.metric("Prix unitaire", f"{p['prix_vente']:,.0f} FC")
                    st.info(f"**{p['nom_article']}** | Catégorie: {p.get('categorie','N/A')} | QR: {p.get('code_qr','N/A')}")
                    if st.button("🛒 AJOUTER AU PANIER", type="primary", width="stretch", key="add_article_unique"):
                        existant = next((item for item in st.session_state.panier_commerce if item['id'] == int(p['id'])), None)
                        if existant:
                            if existant['qte'] + qte <= qte_max:
                                existant['qte'] += qte
                                st.success(f"Panier mis à jour: {existant['qte']}x")
                            else:
                                st.error(f"Stock insuffisant! Max dispo: {qte_max}")
                        else:
                            st.session_state.panier_commerce.append({
                                "id": int(p['id']),
                                "nom": str(p['nom_article']),
                                "pu": float(p['prix_vente']),
                                "qte": int(qte),
                                "code_qr": p.get('code_qr',''),
                                "stock_max": qte_max
                            })
                            st.success("Ajouté au panier")
                        st.rerun()
        with col_droite:
            st.subheader("🛒 Panier")
            if st.session_state.vente_finie and st.session_state.pdf_data:
                st.success("✅ Vente enregistrée!")
                st.download_button("📥 Télécharger Facture PDF", data=st.session_state.pdf_data, file_name=f"{st.session_state.num_fact}.pdf", mime="application/pdf", width="stretch")
                pdf_b64 = base64.b64encode(st.session_state.pdf_data).decode()
                st.components.v1.html(f"""<button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">🖨️ IMPRIMER LA FACTURE</button><script>function printPDF() {{const pdfData = 'data:application/pdf;base64,{pdf_b64}';const win = window.open('', '_blank');win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');win.document.close();setTimeout(() => {{ win.print(); }}, 1000);}}</script>""", height=60)
                if st.button("NOUVELLE VENTE", width="stretch"):
                    st.session_state.vente_finie = False
                    st.session_state.pdf_data = None
                    st.session_state.num_fact = None
                    st.session_state.client_com_nom = ""
                    st.session_state.last_qr = ""
                    st.rerun()
            elif not st.session_state.panier_commerce:
                st.info("Panier vide")
            else:
                total_panier = 0
                for i, item in enumerate(st.session_state.panier_commerce):
                    col1, col2, col3 = st.columns([4,2,1])
                    col1.write(f"**{item['nom']}**")
                    col2.write(f"Qté: {item['qte']} | {item['pu']:,.0f} FC")
                    if col3.button("❌", key=f"d_{i}"):
                        st.session_state.panier_commerce.pop(i)
                        st.rerun()
                    total_panier += item['qte'] * item['pu']
                st.markdown(f"### Total: {total_panier:,.0f} FC")
                st.divider()
                if st.button("💾 FINALISER VENTE & FACTURE", width="stretch", type="primary"):
                    if not st.session_state.client_com_nom:
                        st.error("Nom du client obligatoire!")
                    else:
                        try:
                            num_fact = f"VTE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            details_list = []
                            for item in st.session_state.panier_commerce:
                                supabase.table("ventes").insert({"numero_facture": num_fact, "client_nom": st.session_state.client_com_nom, "article_id": item['id'], "quantite": item['qte'], "prix_unitaire": item['pu'], "total": item['qte'] * item['pu']}).execute()
                                stock_actuel = df_articles[df_articles['id'] == item['id']]['stock'].iloc[0]
                                supabase.table("articles").update({"stock": int(stock_actuel - item['qte'])}).eq("id", item['id']).execute()
                                details_list.append({"nom": item['nom'], "qte": item['qte'], "pu": item['pu'], "total": item['qte'] * item['pu']})
                            details_json = json.dumps(details_list)
                            supabase.table("compta").insert({"date": str(date.today()), "type": "Revenu", "categorie": "Vente Commerce", "description": f"Vente - {st.session_state.client_com_nom}", "montant": float(total_panier), "devise": "FC", "numero_facture": num_fact, "details": details_json, "utilisateur": st.session_state.user_name}).execute()
                            pdf_bytes = generer_pdf_facture(num_fact, "Vente Commerce", st.session_state.client_com_nom, details_list, total_panier, "FC", st.session_state.client_com_tel)
                            st.session_state.pdf_data = pdf_bytes
                            st.session_state.num_fact = num_fact
                            st.session_state.vente_finie = True
                            st.session_state.panier_commerce = []
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur finalisation vente")
                            st.code(repr(e))

# === GESTION STOCK ===
if "📦 Gestion Stock" in tab_map:
    with tab_map["📦 Gestion Stock"]:
        st.markdown("## 📦 Gestion Stock Commerce - Articles & Pertes")
        tab_stock, tab_ajout, tab_mvt, tab_pertes = st.tabs(["📊 Stock Actuel", "➕ Ajouter Article", "📈 Mouvements", "⚠️ Pertes & Casses"])
        with tab_stock:
            st.subheader("📊 Stock Actuel Commerce")
            if df_articles.empty:
                st.info("Aucun article en stock")
            else:
                for _, row in df_articles.iterrows():
                    col1, col2, col3, col4 = st.columns([3,1,1,1])
                    with col1:
                        st.write(f"**{row['nom_article']}** - {row.get('categorie','')} - QR:{row.get('code_qr','N/A')}")
                    with col2:
                        stock_val = int(row.get('stock',0))
                        if stock_val < 5:
                            st.error(f"⚠️ Stock: {stock_val}")
                        else:
                            st.success(f"✅ Stock: {stock_val}")
                    with col3:
                        st.write(f"PA: {row.get('prix_achat',0):,.0f}")
                    with col4:
                        st.write(f"PV: {row.get('prix_vente',0):,.0f} FC")
                    with st.expander(f"Modifier/Supprimer {row['nom_article']}"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            new_nom = st.text_input("Nom", value=row['nom_article'], key=f"nom_art_{row['id']}")
                            new_cat = st.text_input("Catégorie", value=row.get('categorie',''), key=f"cat_art_{row['id']}")
                            new_code_qr = st.text_input("Code QR", value=row.get('code_qr',''), key=f"qr_art_{row['id']}")
                        with c2:
                            new_prix_a = st.number_input("Prix Achat FC", value=float(row.get('prix_achat',0)), key=f"pa_art_{row['id']}")
                            new_prix_v = st.number_input("Prix Vente FC", value=float(row.get('prix_vente',0)), key=f"pv_art_{row['id']}")
                            new_prix_usd = st.number_input("Prix Vente $", value=float(row.get('prix_vente_usd',0)), key=f"pusd_art_{row['id']}")
                        with c3:
                            new_stock = st.number_input("Stock", value=int(row.get('stock',0)), key=f"stock_art_{row['id']}")
                        c1, c2 = st.columns(2)
                        if c1.button("✏️ Modifier", key=f"mod_art_{row['id']}", width="stretch"):
                            try:
                                data_update = {"nom_article": str(new_nom), "categorie": str(new_cat), "prix_achat": float(new_prix_a), "prix_vente": float(new_prix_v), "stock": int(new_stock), "code_qr": str(new_code_qr) if new_code_qr else None}
                                colonnes_articles = get_table_columns("articles")
                                if "prix_vente_usd" in colonnes_articles:
                                    data_update["prix_vente_usd"] = float(new_prix_usd)
                                supabase.table("articles").update(data_update).eq("id", int(row['id'])).execute()
                                st.success("Modifié")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur modif")
                                st.code(repr(e))
                        if st.session_state.user_role == "PDG" or perms.get('supprimer', False):
                            if c2.button("🗑️ Supprimer", key=f"del_art_{row['id']}", width="stretch"):
                                try:
                                    supabase.table("articles").delete().eq("id", int(row['id'])).execute()
                                    st.success("Supprimé")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erreur suppression")
                                    st.code(repr(e))
        with tab_ajout:
            st.subheader("➕ Ajouter Nouvel Article Commerce")
            qr_scan_ajout = qrcode_scanner(key='qr_add_article_com')
            if qr_scan_ajout:
                st.success(f"QR scanné : {qr_scan_ajout}")
                st.session_state.qr_code_temp = qr_scan_ajout
            with st.form("form_article_com", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nom = c1.text_input("Nom Article")
                cat = c2.text_input("Catégorie")
                code_qr = c3.text_input("Code QR", value=st.session_state.get('qr_code_temp', ''))
                c1, c2, c3 = st.columns(3)
                prix_achat_fc = c1.number_input("Prix Achat FC", min_value=0.0)
                prix_vente_fc = c2.number_input("Prix Vente FC", min_value=0.0)
                prix_vente_usd = c3.number_input("Prix Vente $", min_value=0.0)
                stock = c1.number_input("Stock Initial", min_value=0)
                if st.form_submit_button("💾 Ajouter Article"):
                    try:
                        data_insert = {"nom_article": str(nom), "categorie": str(cat), "prix_achat": float(prix_achat_fc), "prix_vente": float(prix_vente_fc), "stock": int(stock), "code_qr": str(code_qr) if code_qr else None}
                        colonnes_articles = get_table_columns("articles")
                        if "prix_vente_usd" in colonnes_articles:
                            data_insert["prix_vente_usd"] = float(prix_vente_usd)
                        supabase.table("articles").insert(data_insert).execute()
                        st.success(f"Article {nom} ajouté")
                        if 'qr_code_temp' in st.session_state:
                            del st.session_state.qr_code_temp
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout")
                        st.code(repr(e))
        with tab_mvt:
            st.subheader("📈 Mouvements de Stock Commerce")
            try:
                mvts = supabase.table('mouvements_stock').select("*").order("created_at", desc=True).limit(50).execute().data
            except:
                mvts = []
            if not mvts:
                st.info("Aucun mouvement enregistré")
            else:
                df_mvt = pd.DataFrame(mvts)
                st.dataframe(df_mvt[['article_nom', 'type', 'quantite', 'motif', 'created_by', 'created_at']], use_container_width=True, hide_index=True)
        with tab_pertes:
            st.subheader("⚠️ Déclarer Perte/Casse Article Commerce")
            articles_dispo = df_articles[df_articles['stock'] > 0].copy() if not df_articles.empty else pd.DataFrame()
            if articles_dispo.empty:
                st.warning("Aucun article en stock pour déclarer une perte")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    article_dict = {f"{a['nom_article']} - Stock:{int(a['stock'])}": a for _, a in articles_dispo.iterrows()}
                    article_choisi = st.selectbox("Article abîmé/perdu", list(article_dict.keys()))
                    qte_perte = st.number_input("Quantité abîmée", min_value=1, max_value=int(article_dict[article_choisi]['stock']) if article_choisi else 1)
                with col2:
                    motif_perte = st.selectbox("Motif", ["Casse", "Vol", "Péremption", "Autre"])
                with st.form("form_perte_com"):
                    commentaire = st.text_area("Commentaire")
                    if st.form_submit_button("⚠️ Enregistrer la Perte"):
                        try:
                            article_data = article_dict[article_choisi]
                            supabase.table("mouvements_stock").insert({
                                "article_id": int(article_data['id']),
                                "article_nom": str(article_data['nom_article']),
                                "type": "perte",
                                "categorie": "commerce",
                                "quantite": int(qte_perte),
                                "motif": str(motif_perte),
                                "commentaire": str(commentaire),
                                "montant": float(article_data['prix_achat']) * int(qte_perte),
                                "created_by": st.session_state.user_name
                            }).execute()
                            new_stock = int(article_data['stock']) - int(qte_perte)
                            supabase.table("articles").update({"stock": new_stock}).eq("id", int(article_data['id'])).execute()
                            st.success(f"Perte enregistrée: {qte_perte} x {article_data['nom_article']}")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur enregistrement perte")
                            st.code(repr(e))

# === IMMOBILIER ===
if "🏠 Immobilier" in tab_map:
    with tab_map["🏠 Immobilier"]:
        st.markdown("## 🏠 Immobilier - Location & Vente")
        tab_louer, tab_vendre, tab_liste = st.tabs(["📝 Louer", "💰 Vendre", "📋 Liste Biens"])
        with tab_louer:
            st.subheader("📝 Nouveau Contrat de Location")
            with st.form("form_location"):
                c1, c2 = st.columns(2)
                type_bien = c1.selectbox("Type de bien", ["Appartement", "Maison", "Bureau", "Magasin", "Terrain"])
                adresse = c2.text_input("Adresse complète")
                c1, c2, c3 = st.columns(3)
                prix = c1.number_input("Loyer mensuel $", min_value=0.0)
                duree_contrat = c2.selectbox("Durée contrat", ["6 mois", "1 an", "2 ans", "3 ans"])
                electricite = c3.number_input("Électricité $/mois", min_value=0.0)
                eau = c1.number_input("Eau $/mois", min_value=0.0)
                client_nom = c2.text_input("Nom Locataire")
                client_tel = c3.text_input("Tél Locataire")
                if st.form_submit_button("💾 Créer Facture Location"):
                    if client_nom and adresse:
                        total = prix + electricite + eau
                        details_list = [
                            {"nom": f"Loyer {type_bien} | Adresse: {adresse} | Duree: {duree_contrat}", "qte": 1, "pu": prix},
                            {"nom": f"Electricite | {type_bien} - {adresse}", "qte": 1, "pu": electricite},
                            {"nom": f"Eau | {type_bien} - {adresse}", "qte": 1, "pu": eau}
                        ]
                        details_text = f"LOUER: {type_bien} | Adresse: {adresse} | Duree Contrat: {duree_contrat} | Loyer: {prix} $ | Electricite: {electricite} $ | Eau: {eau} $"
                        try:
                            num_fact, pdf_bytes = creer_facture_auto("Immobilier", client_nom, details_text, total, "USD", details_list, client_tel)
                            st.success(f"Facture {num_fact} créée")
                            st.download_button("📥 Télécharger Facture", data=pdf_bytes, file_name=f"{num_fact}.pdf", mime="application/pdf")
                        except Exception as e:
                            st.error("Erreur création facture")
                            st.code(repr(e))
                    else:
                        st.error("Nom locataire et adresse obligatoires")
        with tab_vendre:
            st.subheader("💰 Vente de Bien Immobilier")
            with st.form("form_vente_immo"):
                c1, c2 = st.columns(2)
                type_bien_v = c1.selectbox("Type de bien", ["Appartement", "Maison", "Bureau", "Magasin", "Terrain", "Parcelle"], key="type_vente")
                adresse_v = c2.text_input("Adresse complète", key="addr_vente")
                prix_vente = c1.number_input("Prix de vente $", min_value=0.0)
                client_acheteur = c2.text_input("Nom Acheteur")
                tel_acheteur = c1.text_input("Tél Acheteur")
                if st.form_submit_button("💾 Créer Facture Vente"):
                    if client_acheteur and adresse_v:
                        details_list = [{"nom": f"Vente {type_bien_v} | Adresse: {adresse_v}", "qte": 1, "pu": prix_vente}]
                        details_text = f"VENTE: {type_bien_v} | Adresse: {adresse_v} | Prix: {prix_vente} $"
                        try:
                            num_fact, pdf_bytes = creer_facture_auto("Immobilier", client_acheteur, details_text, prix_vente, "USD", details_list, tel_acheteur)
                            st.success(f"Facture {num_fact} créée")
                            st.download_button("📥 Télécharger Facture", data=pdf_bytes, file_name=f"{num_fact}.pdf", mime="application/pdf")
                        except Exception as e:
                            st.error("Erreur création facture")
                            st.code(repr(e))
                    else:
                        st.error("Nom acheteur et adresse obligatoires")
        with tab_liste:
            st.subheader("📋 Biens Immobiliers Enregistrés")
            if df_biens.empty:
                st.info("Aucun bien enregistré")
            else:
                st.dataframe(df_biens, use_container_width=True, hide_index=True)

# === AUTOMOBILE ===
if "🚗 Automobile" in tab_map:
    with tab_map["🚗 Automobile"]:
        st.markdown("## 🚗 Automobile - Vente Véhicules")
        tab_vente_auto, tab_liste_auto = st.tabs(["💰 Nouvelle Vente", "📋 Stock Voitures"])
        with tab_vente_auto:
            st.subheader("💰 Vente de Véhicule")
            if df_voitures.empty:
                st.warning("Aucune voiture en stock")
            else:
                voitures_dispo = df_voitures[df_voitures['quantite'] > 0].copy()
                if voitures_dispo.empty:
                    st.warning("Aucune voiture disponible à la vente")
                else:
                    voiture_dict = {f"{v['modele']} - {int(v['quantite'])} unités - {float(v['prix']):,.0f} FC": v for _, v in voitures_dispo.iterrows()}
                    with st.form("form_vente_auto"):
                        voiture_choisie = st.selectbox("Véhicule à vendre", list(voiture_dict.keys()))
                        qte_vente = st.number_input("Quantité", min_value=1, max_value=int(voiture_dict[voiture_choisie]['quantite']))
                        client_auto = st.text_input("Nom Acheteur")
                        tel_auto = st.text_input("Tél Acheteur")
                        if st.form_submit_button("💾 Créer Facture Vente Auto"):
                            if client_auto:
                                v = voiture_dict[voiture_choisie]
                                total_auto = float(v['prix']) * int(qte_vente)
                                details_list = [{"nom": f"{v['modele']} | Chassis: {v.get('chassis','N/A')}", "qte": int(qte_vente), "pu": float(v['prix'])}]
                                details_text = f"VENTE AUTO: {v['modele']} | Qte: {qte_vente} | Prix unit: {v['prix']} FC"
                                try:
                                    num_fact, pdf_bytes = creer_facture_auto("Automobile", client_auto, details_text, total_auto, "FC", details_list, tel_auto)
                                    new_qte = int(v['quantite']) - int(qte_vente)
                                    supabase.table("voitures").update({"quantite": new_qte}).eq("id", int(v['id'])).execute()
                                    st.success(f"Facture {num_fact} créée")
                                    st.download_button("📥 Télécharger Facture", data=pdf_bytes, file_name=f"{num_fact}.pdf", mime="application/pdf")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erreur vente auto")
                                    st.code(repr(e))
                            else:
                                st.error("Nom acheteur obligatoire")
        with tab_liste_auto:
            st.subheader("📋 Stock Voitures")
            if df_voitures.empty:
                st.info("Aucune voiture enregistrée")
            else:
                st.dataframe(df_voitures, use_container_width=True, hide_index=True)

# === GESTION PARC ===
if "🚘 Gestion Parc" in tab_map:
    with tab_map["🚘 Gestion Parc"]:
        st.markdown("## 🚘 Gestion Parc Auto - Véhicules de Service")
        st.info("Module pour gérer les véhicules du parc de l'entreprise. À développer selon tes besoins.")

# === COMPTABILITE ===
if "💰 Comptabilité" in tab_map:
    with tab_map["💰 Comptabilité"]:
        st.markdown("## 💰 Comptabilité Générale")
        tab_saisie, tab_rapport = st.tabs(["📝 Saisie Écriture", "📊 Rapport"])
        with tab_saisie:
            with st.form("form_compta"):
                c1, c2, c3 = st.columns(3)
                date_ecr = c1.date_input("Date", value=date.today())
                type_ecr = c2.selectbox("Type", ["Revenu", "Dépense"])
                cat_ecr = c3.text_input("Catégorie")
                desc = st.text_area("Description")
                c1, c2 = st.columns(2)
                montant = c1.number_input("Montant", min_value=0.0)
                devise = c2.selectbox("Devise", ["FC", "USD"])
                if st.form_submit_button("💾 Enregistrer"):
                    try:
                        supabase.table("compta").insert({
                            "date": str(date_ecr),
                            "type": type_ecr,
                            "categorie": str(cat_ecr),
                            "description": str(desc),
                            "montant": float(montant),
                            "devise": devise,
                            "utilisateur": st.session_state.user_name
                        }).execute()
                        st.success("Écriture enregistrée")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur enregistrement")
                        st.code(repr(e))
        with tab_rapport:
            if df_compta.empty:
                st.info("Aucune écriture comptable")
            else:
                revenus = df_compta[df_compta['type'] == 'Revenu']['montant'].sum()
                depenses = df_compta[df_compta['type'] == 'Dépense']['montant'].sum()
                solde = revenus - depenses
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Revenus", f"{revenus:,.0f} FC")
                col2.metric("Total Dépenses", f"{depenses:,.0f} FC")
                col3.metric("Solde", f"{solde:,.0f} FC", delta=f"{solde:,.0f}")
                st.dataframe(df_compta.sort_values('date', ascending=False), use_container_width=True, hide_index=True)

# === FACTURES ===
if "📄 Factures" in tab_map:
    with tab_map["📄 Factures"]:
        st.markdown("## 📄 Toutes les Factures")
        try:
            factures = supabase.table('compta').select("*").not_.is_("numero_facture", "null").order("date", desc=True).limit(100).execute().data
        except:
            factures = []
        if not factures:
            st.info("Aucune facture enregistrée")
        else:
            df_fact = pd.DataFrame(factures)
            if st.session_state.user_cats and "Toutes" not in st.session_state.user_cats:
                df_fact = df_fact[df_fact['categorie'].isin(st.session_state.user_cats)]
            st.dataframe(df_fact[['numero_facture', 'date', 'categorie', 'description', 'montant', 'devise']], use_container_width=True, hide_index=True)

# === DEVIS ===
if "📋 Devis" in tab_map:
    with tab_map["📋 Devis"]:
        st.markdown("## 📋 Gestion des Devis")
        tab_industriel, tab_batiment, tab_historique = st.tabs(["🏭 Devis Industriel", "🏗️ Devis Bâtiment", "📚 Historique"])
        
        perms_devis_ind = perms.get('devis_industriel', False) or st.session_state.user_role == "PDG"
        perms_devis_bat = perms.get('devis_batiment', False) or st.session_state.user_role == "PDG"
        perms_hist = perms.get('devis_historique', False) or st.session_state.user_role == "PDG"

        with tab_industriel:
            if perms_devis_ind:
                st.subheader("🏭 Créer Devis Industriel")
                # Code devis industriel à compléter selon ton besoin
                st.info("Module devis industriel - à configurer")
            else:
                st.error("⛔ Vous n'avez pas l'autorisation Devis Industriel")

        with tab_batiment:
            if perms_devis_bat:
                st.subheader("🏗️ Créer Devis Bâtiment")
                # Code devis bâtiment à compléter selon ton besoin
                st.info("Module devis bâtiment - à configurer")
            else:
                st.error("⛔ Vous n'avez pas l'autorisation Devis Bâtiment")

        with tab_historique:
            if perms_hist:
                st.subheader("📚 Historique des Devis")
                try:
                    devis_list = supabase.table('devis').select("*").order("created_at", desc=True).limit(50).execute().data
                    if devis_list:
                        st.dataframe(pd.DataFrame(devis_list), use_container_width=True, hide_index=True)
                    else:
                        st.info("Aucun devis enregistré")
                except:
                    st.info("Table devis non configurée")
            else:
                st.error("⛔ Vous n'avez pas l'autorisation Historique Devis")

# === UTILISATEURS ===
if "👥 Utilisateurs" in tab_map:
    with tab_map["👥 Utilisateurs"]:
        st.markdown("## 👥 Gestion Utilisateurs - Droits d'Accès")
        with st.expander("➕ Ajouter Nouvel Utilisateur", expanded=True):
            with st.form("form_user", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nom_user = c1.text_input("Nom *", placeholder="Ex: Jean KABAMBA")
                role_user = c2.selectbox("Rôle *", ["PDG", "GERANTE", "UTILISATEUR", "CAISSIER", "COMMERCIAL"])
                pwd_user = c3.text_input("Mot de passe *", type="password")
                st.markdown("**🔐 Autorisations d'onglets :**")
                col1, col2, col3, col4 = st.columns(4)
                perm_dashboard = col1.checkbox("Dashboard", value=True)
                perm_commerce = col2.checkbox("Commerce", value=True)
                perm_stock = col3.checkbox("Gestion Stock")
                perm_immobilier = col4.checkbox("Immobilier")
                perm_automobile = col1.checkbox("Automobile")
                perm_parc = col2.checkbox("Gestion Parc")
                perm_comptabilite = col3.checkbox("Comptabilité")
                perm_factures = col4.checkbox("Factures")
                perm_supprimer = col1.checkbox("🗑️ Peut Supprimer")
                perm_users = col2.checkbox("👥 Gérer Utilisateurs")
                st.markdown("**📋 Autorisations Devis :**")
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    st.markdown("*Devis Industriel*")
                    perm_devis_ind = st.checkbox("Créer", key="perm_ind_creer")
                    perm_devis_ind_dl = st.checkbox("Télécharger", key="perm_ind_dl")
                    perm_devis_ind_pr = st.checkbox("Imprimer", key="perm_ind_pr")
                with col_d2:
                    st.markdown("*Devis Bâtiment*")
                    perm_devis_bat = st.checkbox("Créer", key="perm_bat_creer")
                    perm_devis_bat_dl = st.checkbox("Télécharger", key="perm_bat_dl")
                    perm_devis_bat_pr = st.checkbox("Imprimer", key="perm_bat_pr")
                with col_d3:
                    st.markdown("*Historique*")
                    perm_devis_hist = st.checkbox("Voir Historique", key="perm_hist")
                st.markdown("**📂 Catégories de Factures Visibles :**")
                cats_dispo = sorted(df_compta['categorie'].dropna().unique().tolist()) if 'categorie' in df_compta.columns else []
                cats_autorisees = st.multiselect("Sélectionne les catégories que cet utilisateur peut voir dans Factures", ["Toutes"] + cats_dispo, default=["Toutes"], key="cats_factures")
                if st.form_submit_button("💾 Ajouter Utilisateur", type="primary"):
                    if nom_user and pwd_user:
                        try:
                            perms_dict = {
                                "dashboard": perm_dashboard, "commerce": perm_commerce, "stock": perm_stock,
                                "immobilier": perm_immobilier, "automobile": perm_automobile, "parc": perm_parc,
                                "comptabilite": perm_comptabilite, "factures": perm_factures, "supprimer": perm_supprimer,
                                "users": perm_users, "devis_industriel": perm_devis_ind,
                                "devis_industriel_download": perm_devis_ind_dl, "devis_industriel_print": perm_devis_ind_pr,
                                "devis_batiment": perm_devis_bat, "devis_batiment_download": perm_devis_bat_dl,
                                "devis_batiment_print": perm_devis_bat_pr, "devis_historique": perm_devis_hist
                            }
                            supabase.table("utilisateurs").insert({
                                "nom": nom_user, "role": role_user, "password": pwd_user,
                                "permissions": perms_dict,
                                "categories_autorisees": cats_autorisees if "Toutes" not in cats_autorisees else []
                            }).execute()
                            st.success(f"Utilisateur {nom_user} ajouté")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur ajout")
                            st.code(repr(e))
                    else:
                        st.error("Nom et mot de passe obligatoires")
        st.divider()
        st.subheader("📋 Liste des Utilisateurs")
        if df_utilisateurs.empty:
            st.info("Aucun utilisateur")
        else:
            for _, user in df_utilisateurs.iterrows():
                current_perms = user.get('permissions', {})
                if isinstance(current_perms, str):
                    try:
                        current_perms = json.loads(current_perms)
                    except:
                        current_perms = {}
                with st.expander(f"{user['nom']} - {user['role']}"):
                    st.write(f"**Permissions:** {json.dumps(current_perms, indent=2)}")
                    if st.session_state.user_role == "PDG" and user['nom'] != st.session_state.user_name:
                        if st.button("🗑️ Supprimer", key=f"del_user_{user['id']}"):
                            try:
                                supabase.table("utilisateurs").delete().eq("id", int(user['id'])).execute()
                                st.success(f"Utilisateur {user['nom']} supprimé")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur suppression")
                                st.code(repr(e))
