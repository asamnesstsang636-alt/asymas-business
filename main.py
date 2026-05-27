import streamlit as st
import pandas as pd
st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide", initial_sidebar_state="auto")
st.markdown("""<meta name="mobile-web-app-capable" content="yes">""", unsafe_allow_html=True)

from supabase import create_client, Client
from datetime import date, datetime, timedelta
from fpdf import FPDF
import base64, io, qrcode, tempfile, os, json
from PIL import Image
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from streamlit_qrcode_scanner import qrcode_scanner

# === HOLOGRAMME LOGIN AVEC 6 MODULES ===
st.markdown("""
<style>
.block-container{padding:0!important;max-width:100%!important;}
.main{background:#0a0a0a;margin:0;padding:0;}
div[data-testid="stTextInput"]{position:absolute!important; bottom:8%!important; left:50%!important; transform:translateX(-50%)!important; width:180px!important; z-index:100!important;}
div[data-testid="stTextInput"] input{background:rgba(0,0,0,0.9)!important; border:2px solid #FFD700!important; border-radius:10px!important; color:#FFD700!important; text-align:center!important; padding:10px!important;}
div[data-testid="stTextInput"] label{display:none!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="position:relative;width:100vw;height:100vh;background:radial-gradient(ellipse at center 55%, rgba(255,215,0,0.7) 0%, rgba(15,15,15,1) 85%);overflow:hidden;">
    <div style="position:absolute;bottom:10%;left:50%;transform:translateX(-50%);width:340px;height:170px;background:linear-gradient(145deg,#2d2d2d,#1a1a1a);border-radius:45px;box-shadow:0 35px 70px rgba(0,0,0,0.9);border:3px solid #444;"></div>
    <div style="position:absolute;top:45%;left:50%;transform:translate(-50%,-50%);width:450px;height:450px;">
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:380px;height:380px;border:2px solid rgba(255,215,0,0.5);border-radius:50%;box-shadow:0 0 80px rgba(255,215,0,0.8);animation:pulseRing 3s ease-in-out infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:300px;height:300px;border:2px dotted rgba(255,215,0,0.9);border-radius:50%;animation:rotate 15s linear infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:220px;height:220px;border:3px solid #FFD700;border-radius:50%;box-shadow:0 0 90px #FFD700;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:170px;height:170px;background:radial-gradient(circle,#FFD700 0%,#FFA500 100%);border-radius:50%;box-shadow:0 0 100px #FFD700;display:flex;flex-direction:column;align-items:center;justify-content:center;animation:pulseCart 2s ease-in-out infinite;">
            <div style="font-size:50px;">🛒</div>
            <div style="font-size:16px;font-weight:bold;color:#000;margin-top:5px;">ASYMAS</div>
        </div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:380px;height:380px;">
            <div style="position:absolute;top:0px;left:50%;transform:translateX(-50%);background:#fff;border:3px solid #FFD700;border-radius:50%;width:60px;height:60px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:24px;box-shadow:0 0 20px #FFD700;"><div>🏪</div><div style="font-size:8px;color:#000;font-weight:bold;">Commerce</div></div>
            <div style="position:absolute;top:45px;right:35px;background:#fff;border:3px solid #FFD700;border-radius:50%;width:60px;height:60px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:24px;box-shadow:0 0 20px #FFD700;"><div>🚚</div><div style="font-size:8px;color:#000;font-weight:bold;">Auto</div></div>
            <div style="position:absolute;bottom:45px;right:35px;background:#fff;border:3px solid #FFD700;border-radius:50%;width:60px;height:60px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:24px;box-shadow:0 0 20px #FFD700;"><div>🧾</div><div style="font-size:8px;color:#000;font-weight:bold;">Factures</div></div>
            <div style="position:absolute;bottom:0px;left:50%;transform:translateX(-50%);background:#fff;border:3px solid #FFD700;border-radius:50%;width:60px;height:60px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:24px;box-shadow:0 0 20px #FFD700;"><div>🏠</div><div style="font-size:8px;color:#000;font-weight:bold;">Immo</div></div>
            <div style="position:absolute;bottom:45px;left:35px;background:#fff;border:3px solid #FFD700;border-radius:50%;width:60px;height:60px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:24px;box-shadow:0 0 20px #FFD700;"><div>📦</div><div style="font-size:8px;color:#000;font-weight:bold;">Stock</div></div>
            <div style="position:absolute;top:45px;left:35px;background:#fff;border:3px solid #FFD700;border-radius:50%;width:60px;height:60px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:24px;box-shadow:0 0 20px #FFD700;"><div>📊</div><div style="font-size:8px;color:#000;font-weight:bold;">Compta</div></div>
        </div>
    </div>
</div>
<style>@keyframes pulseRing{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}50%{transform:translate(-50%,-50%) scale(1.12);opacity:1;}}
@keyframes pulseCart{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.18);}}
@keyframes rotate{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}</style>
""", unsafe_allow_html=True)

pwd = st.text_input("", type="password", placeholder="Mot de passe ASYMAS")
if pwd!= "asymas2025":
    st.stop()

st.success("Accès autorisé ✅")
st.session_state.user_role = "PDG"
st.session_state.user_name = "PDG"

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === TOUTES TES FONCTIONS DE L'ANCIEN CODE ===
@st.cache_data(ttl=60)
def load_table(table_name):
    try:
        data = supabase.table(table_name).select("*").order("id", desc=True).execute()
        return pd.DataFrame(data.data)
    except Exception as e:
        st.error(f"Erreur {table_name}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_table_columns(table_name):
    try:
        test = supabase.table(table_name).select("*").limit(1).execute()
        if test.data: return list(test.data[0].keys())
        return []
    except: return []

def generer_qrcode(data_text):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=3, border=1)
    qr.add_data(data_text); qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name); return temp_file.name

def safe_pdf_txt(txt):
    if txt is None or pd.isna(txt): return ""
    txt = str(txt).replace('—','-').replace('’',"'").replace('“','"').replace('”','"')
    return ''.join(c if ord(c) < 128 else '?' for c in txt)

def generer_pdf_facture(numero, type_op, client, details_list, montant, devise, tel_client="+243...", periode="", type_facture="Simple"):
    pdf = FPDF(); pdf.add_page(); pdf.set_auto_page_break(auto=False, margin=10)
    pdf.set_fill_color(20, 50, 40); pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 20); pdf.set_xy(10, 8); pdf.cell(0, 10, "ASYMAS BUSINESS", ln=True)
    pdf.set_font("Arial", "", 9); pdf.set_xy(10, 16); pdf.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
    pdf.set_xy(10, 21); pdf.cell(0, 5, "Email: asamnesstsang636@gmail.com", ln=True)
    pdf.set_font("Arial", "B", 10); pdf.set_xy(150, 8)
    titre_fact = "FACTURE N" if type_facture == "Simple" else "PROFORMA N"
    pdf.cell(50, 6, titre_fact, ln=True, align="R")
    pdf.set_font("Arial", "", 10); pdf.set_xy(150, 14); pdf.cell(50, 6, safe_pdf_txt(numero), ln=True, align="R")
    pdf.set_font("Arial", "", 9); pdf.set_xy(150, 20); pdf.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")
    y_pos = 45; pdf.set_text_color(0, 0, 0); pdf.set_fill_color(255, 204, 0); pdf.set_font("Arial", "B", 14); pdf.set_xy(10, y_pos)
    pdf.cell(0, 10, f"{type_facture.upper()} {safe_pdf_txt(type_op.upper())}", ln=True, fill=True); y_pos += 15
    pdf.set_font("Arial", "B", 10); pdf.set_draw_color(0, 0, 0); pdf.set_xy(10, y_pos)
    pdf.cell(85, 7, "FACTURE A:", 1, 0, 'L'); pdf.cell(10, 7, "", 0, 0); pdf.cell(85, 7, "DETAILS PAIEMENT:", 1, 1, 'L'); y_pos += 7
    pdf.set_font("Arial", "", 9); pdf.set_xy(10, y_pos)
    pdf.cell(85, 6, f"Client: {safe_pdf_txt(client)}", 'LR', 0, 'L'); pdf.cell(10, 6, "", 0, 0); pdf.cell(85, 6, "M-Pesa: +243817264448", 'LR', 1, 'L'); y_pos += 6
    pdf.set_xy(10, y_pos); pdf.cell(85, 6, f"Tel: {safe_pdf_txt(tel_client)}", 'LR', 0, 'L'); pdf.cell(10, 6, "", 0, 0); pdf.cell(85, 6, "Echeance: Immediate", 'LR', 1, 'L'); y_pos += 6
    pdf.set_xy(10, y_pos); pdf.cell(85, 6, f"Date emission: {date.today().strftime('%d/%m/%Y')}", 'LRB', 0, 'L'); pdf.cell(10, 6, "", 0, 0); pdf.cell(85, 6, "", 'LRB', 1, 'L'); y_pos += 14
    pdf.set_fill_color(0, 102, 0); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 10); pdf.set_xy(10, y_pos)
    pdf.cell(115, 8, "DESIGNATION", 1, 0, 'C', True); pdf.cell(25, 8, "QTE", 1, 0, 'C', True); pdf.cell(40, 8, f"MONTANT ({safe_pdf_txt(devise)})", 1, 1, 'C', True); y_pos += 8
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 9)
    if isinstance(details_list, list) and details_list:
        for item in details_list:
            if y_pos > 240: pdf.add_page(); y_pos = 30
            nom = safe_pdf_txt(item.get('nom', '')); qte = item.get('qte', 1); pu = item.get('pu', item.get('prix', 0)); montant_item = pu * qte
            pdf.set_xy(10, y_pos); pdf.cell(115, 7, nom, 1, 0, 'L'); pdf.cell(25, 7, str(qte), 1, 0, 'C'); pdf.cell(40, 7, f"{montant_item:,.0f}", 1, 1, 'R'); y_pos += 7
    else:
        pdf.set_xy(10, y_pos); pdf.cell(115, 7, safe_pdf_txt(details_list), 1, 0, 'L'); pdf.cell(25, 7, "1", 1, 0, 'C'); pdf.cell(40, 7, f"{montant:,.0f}", 1, 1, 'R'); y_pos += 7
    if periode:
        if y_pos > 240: pdf.add_page(); y_pos = 30
        pdf.set_xy(10, y_pos); pdf.cell(115, 7, f"Periode: {safe_pdf_txt(periode)}", 1, 0, 'L'); pdf.cell(25, 7, "", 1, 0, 'C'); pdf.cell(40, 7, "", 1, 1, 'R'); y_pos += 7
    pdf.set_fill_color(255, 204, 0); pdf.set_font("Arial", "B", 11); pdf.set_xy(10, y_pos)
    pdf.cell(140, 10, "MONTANT TOTAL A PAYER", 1, 0, 'R', True); pdf.cell(40, 10, f"{montant:,.0f} {safe_pdf_txt(devise)}", 1, 1, 'R', True); y_pos += 15
    if y_pos > 220: pdf.add_page(); y_pos = 30
    pdf.set_xy(10, y_pos); pdf.set_font("Arial", "B", 10); pdf.cell(0, 8, "SIGNATURE RESPONSABLE:", ln=True); y_pos += 11
    pdf.set_draw_color(0, 0, 0); pdf.line(10, y_pos, 100, y_pos); y_pos += 1; pdf.set_font("Arial", "", 9); pdf.set_xy(10, y_pos)
    pdf.cell(90, 5, "Ing. SAMY TSANGYA", ln=True); y_pos += 5; pdf.set_xy(10, y_pos); pdf.cell(90, 5, "Tel: +243 995 105 623", ln=True)
    y_pos += 5; pdf.set_xy(10, y_pos); pdf.cell(90, 5, "Beni, Nord-Kivu, RDC", ln=True); y_pos += 10
    pdf.set_font("Arial", "I", 10); pdf.set_text_color(0, 102, 0); pdf.set_xy(10, y_pos)
    pdf.cell(0, 6, "Merci pour votre confiance! ASYMAS BUSINESS - Votre partenaire de croissance", ln=True, align="C")
    qr_data = f"""ASYMAS BUSINESS\nFacture: {numero}\nType: {type_op}\nClient: {client}\nMontant: {montant:,.0f} {devise}\nDate: {date.today().strftime('%d/%m/%Y')}\nTel: +243 995 105 623"""
    qr_path = generer_qrcode(qr_data); pdf.image(qr_path, x=155, y=y_pos-25, w=25); os.unlink(qr_path)
    return bytes(pdf.output(dest='S'))

def creer_facture_auto(type_op, client, details, montant, devise="FC", details_list=None, tel="+243...", periode="", type_facture="Simple"):
    numero_facture = f"AS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if details_list is None: details_list = [{"nom": details, "qte": 1, "pu": montant}]
    pdf_bytes = generer_pdf_facture(numero_facture, type_op, client, details_list, montant, devise, tel, periode, type_facture)
    try:
        colonnes_compta = get_table_columns("compta")
        data_compta = {"type": "Revenu", "description": str(f"{type_op} - {client} - {details}"), "montant": float(montant), "date": str(date.today()), "utilisateur": st.session_state.user_name}
        if "categorie" in colonnes_compta: data_compta["categorie"] = str(type_op)
        if "devise" in colonnes_compta: data_compta["devise"] = str(devise)
        if "numero_facture" in colonnes_compta: data_compta["numero_facture"] = str(numero_facture)
        if "details" in colonnes_compta: data_compta["details"] = json.dumps(details_list)
        supabase.table("compta").insert(data_compta).execute(); st.toast(f"✅ Enregistré par {st.session_state.user_name}", icon="✅")
    except Exception as e: st.error("❌ ERREUR INSERTION COMPTA"); st.code(repr(e))
    return numero_facture, pdf_bytes

# === CHARGEMENT DONNEES ===
df_biens = load_table("biens")
df_articles = load_table("articles")
df_voitures = load_table("voitures")
df_compta = load_table("compta")
df_factures = load_table("factures_proforma")
df_devis = load_table("devis")
df_utilisateurs = load_table("utilisateurs")

if 'montant' not in df_compta.columns: df_compta['montant'] = 0
if 'type' not in df_compta.columns: df_compta['type'] = 'Inconnu'
if 'date' in df_compta.columns:
    df_compta['date'] = pd.to_datetime(df_compta['date'], errors='coerce')
    df_compta = df_compta.sort_values('date', ascending=False)

st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
st.markdown("### Agriculture • Commerce • Immobilier • Automobile • Beni RDC")

with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.user_name}")
    st.markdown(f"**Rôle : {st.session_state.user_role}**")
    st.info("ASYMAS BUSINESS v3.0 Hologram")
    if 'theme_choisi' not in st.session_state: st.session_state.theme_choisi = "Sombre ASYMAS"
    theme = st.selectbox("🎨", ["Sombre ASYMAS","Bleu Pro","Vert Agri","Noir Luxe"], key="theme_choisi", label_visibility="collapsed")
    if st.button("🚪 Déconnexion", use_container_width=True): st.session_state.clear(); st.rerun()
    if st.button("🔄 Actualiser", key="btn_save"): st.cache_data.clear(); st.rerun()

if theme=="Sombre ASYMAS": st.markdown("""<style>.stApp{background:#0E1117;color:#E0E0E0}h1,h2,h3{color:#14B814!important}</style>""",unsafe_allow_html=True)
elif theme=="Bleu Pro": st.markdown("""<style>.stApp{background:#0A1929;color:#E3F2FD}h1,h2,h3{color:#2196F3!important}</style>""",unsafe_allow_html=True)
elif theme=="Vert Agri": st.markdown("""<style>.stApp{background:#1B2A1B;color:#E8F5E9}h1,h2,h3{color:#4CAF50!important}</style>""",unsafe_allow_html=True)
elif theme=="Noir Luxe": st.markdown("""<style>.stApp{background:#000;color:#FFF}h1,h2,h3{color:#FFD700!important}</style>""",unsafe_allow_html=True)

tabs_dispo = ["📊 Dashboard", "🛍️ Commerce", "📦 Gestion Stock", "🏠 Immobilier", "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures", "📋 Devis", "👥 Utilisateurs"]
tabs = st.tabs(tabs_dispo)
tab_map = {name: tab for name, tab in zip(tabs_dispo, tabs)}
# === DASHBOARD ===
with tab_map["📊 Dashboard"]:
    st.markdown("## 📊 Dashboard ASYMAS")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏠 Biens", len(df_biens))
    col2.metric("📦 Articles", len(df_articles))
    col3.metric("🚗 Voitures", len(df_voitures))
    if not df_compta.empty and 'type' in df_compta.columns and 'montant' in df_compta.columns:
        revenus = df_compta[df_compta['type']=='Revenu']['montant'].sum()
        col4.metric("💰 Revenus", f"{revenus:,.0f} FC")
    else:
        col4.metric("💰 Revenus", "0 FC")
    st.divider()
    if not df_compta.empty:
        st.subheader("📈 Dernières transactions")
        st.dataframe(df_compta.head(10), use_container_width=True)

# === COMMERCE ===
with tab_map["🛍️ Commerce"]:
    st.markdown("## 🛍️ Commerce - Point de Vente")
    if 'panier_commerce' not in st.session_state: st.session_state.panier_commerce = []
    if 'vente_finie' not in st.session_state: st.session_state.vente_finie = False
    if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None
    if 'num_fact' not in st.session_state: st.session_state.num_fact = None
    if 'client_com_nom' not in st.session_state: st.session_state.client_com_nom = ""
    if 'client_com_tel' not in st.session_state: st.session_state.client_com_tel = "+243..."
    if 'last_qr' not in st.session_state: st.session_state.last_qr = ""

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
                st.info(f"*{p['nom_article']}* | Catégorie: {p.get('categorie','N/A')} | QR: {p.get('code_qr','N/A')}")
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
                col1.write(f"*{item['nom']}*")
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
                            supabase.table("ventes").insert({"numero_facture": num_fact,"client_nom": st.session_state.client_com_nom,"article_id": item['id'],"quantite": item['qte'],"prix_unitaire": item['pu'],"total": item['qte'] * item['pu']}).execute()
                            stock_actuel = df_articles[df_articles['id'] == item['id']]['stock'].iloc[0]
                            supabase.table("articles").update({"stock": int(stock_actuel - item['qte'])}).eq("id", item['id']).execute()
                            details_list.append({"nom": item['nom'],"qte": item['qte'],"pu": item['pu'],"total": item['qte'] * item['pu']})
                        details_json = json.dumps(details_list)
                        supabase.table("compta").insert({"date": str(date.today()),"type": "Revenu","categorie": "Vente Commerce","description": f"Vente - {st.session_state.client_com_nom}","montant": float(total_panier),"devise": "FC","numero_facture": num_fact,"details": details_json,"utilisateur": st.session_state.user_name}).execute()
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
with tab_map["📦 Gestion Stock"]:
    st.markdown("## 📦 Gestion Stock")
    st.dataframe(df_articles, use_container_width=True)
    with st.expander("➕ Ajouter Article"):
        with st.form("form_article"):
            nom = st.text_input("Nom Article")
            stock = st.number_input("Stock", min_value=0)
            prix = st.number_input("Prix Vente FC", min_value=0.0)
            if st.form_submit_button("Ajouter"):
                supabase.table("articles").insert({"nom_article": nom, "stock": stock, "prix_vente": prix}).execute()
                st.cache_data.clear(); st.rerun()

# === IMMOBILIER ===
with tab_map["🏠 Immobilier"]:
    st.markdown("## 🏠 Immobilier")
    st.dataframe(df_biens, use_container_width=True)

# === AUTOMOBILE ===
with tab_map["🚗 Automobile"]:
    st.markdown("## 🚗 Automobile")
    st.dataframe(df_voitures, use_container_width=True)

# === GESTION PARC ===
with tab_map["🚘 Gestion Parc"]:
    st.markdown("## 🚘 Gestion Parc")
    st.write("Module en cours...")

# === COMPTABILITÉ ===
with tab_map["💰 Comptabilité"]:
    st.markdown("## 💰 Comptabilité")
    st.dataframe(df_compta, use_container_width=True)

# === FACTURES ===
with tab_map["📄 Factures"]:
    st.markdown("## 📄 Factures & Proformas")
    st.dataframe(df_factures, use_container_width=True)

# === DEVIS ===
with tab_map["📋 Devis"]:
    st.markdown("## 📋 Devis Consulting")
    st.dataframe(df_devis, use_container_width=True)

# === UTILISATEURS ===
with tab_map["👥 Utilisateurs"]:
    st.markdown("## 👥 Gestion Utilisateurs")
    st.dataframe(df_utilisateurs, use_container_width=True)

# === FLOKI SIDEBAR ===
with st.sidebar:
    st.divider()
    st.markdown("### 🤖 FLOKI")
    st.caption("Conseiller du PDG")
    q = st.text_input("Ordre pour FLOKI", key="floki_input", placeholder="Ex: CA du mois")
    if st.button("Exécuter", type="primary", use_container_width=True):
        if q:
            st.info(f"FLOKI: {q}")
