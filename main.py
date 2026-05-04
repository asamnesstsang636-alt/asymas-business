import streamlit as st
import pandas as pd
st.set_page_config(
    page_title="ASYMAS BUSINESS",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="auto"
)
st.markdown("""
<meta name="mobile-web-app-capable" content="yes">
""", unsafe_allow_html=True)
from supabase import create_client, Client
from datetime import date, datetime, timedelta
from fpdf import FPDF
import base64
import io
import qrcode
from PIL import Image
import tempfile
import os
import json
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from streamlit_qrcode_scanner import qrcode_scanner

# === CONFIG SUPABASE ===
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === FONCTIONS ===
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

@st.cache_data(ttl=10)
def load_passwords():
    try:
        data = supabase.table("utilisateurs").select("nom,role,password,permissions,categories_autorisees").execute()
        passwords = {}
        perms = {}
        for user in data.data:
            passwords[user['role']] = user['password']
            perms[user['role']] = {
                'permissions': user.get('permissions', {}),
                'categories_autorisees': user.get('categories_autorisees', [])
            }
        st.session_state.permissions_db = perms
        return passwords
    except:
        st.session_state.permissions_db = {}
        return {
            "PDG": "tsang2024",
            "GERANTE": "asiya2024",
            "UTILISATEUR": "basam2024"
        }

def generer_qrcode(data_text):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=3, border=1)
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name)
    return temp_file.name

def safe_pdf_txt(txt):
    if txt is None or pd.isna(txt):
        return ""
    txt = str(txt)
    txt = txt.replace('—', '-').replace('–', '-').replace('’', "'").replace('“', '"').replace('”', '"')
    txt = txt.replace('•', '-').replace('…', '...')
    txt = ''.join(c if ord(c) < 128 else '?' for c in txt)
    return txt.replace('\n', ' ').replace('\r', '').strip()

def generer_pdf_facture(numero, type_op, client, details_list, montant, devise, tel_client="+243...", periode=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
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
    pdf.set_font("Arial", "B", 10)
    pdf.set_xy(150, 8)
    pdf.cell(50, 6, "FACTURE N", ln=True, align="R")
    pdf.set_font("Arial", "", 10)
    pdf.set_xy(150, 14)
    pdf.cell(50, 6, safe_pdf_txt(numero), ln=True, align="R")
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(150, 20)
    pdf.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")
    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"FACTURE {safe_pdf_txt(type_op.upper())}", ln=True, fill=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.set_draw_color(0, 0, 0)
    pdf.cell(85, 7, "FACTURE A:", 1, 0, 'L')
    pdf.cell(10, 7, "", 0, 0)
    pdf.cell(85, 7, "DETAILS PAIEMENT:", 1, 1, 'L')
    pdf.set_font("Arial", "", 9)
    pdf.cell(85, 6, f"Client: {safe_pdf_txt(client)}", 'LR', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(85, 6, "M-Pesa: +243817264448", 'LR', 1, 'L')
    pdf.cell(85, 6, f"Tel: {safe_pdf_txt(tel_client)}", 'LR', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(85, 6, "Echeance: Immediate", 'LR', 1, 'L')
    pdf.cell(85, 6, f"Date emission: {date.today().strftime('%d/%m/%Y')}", 'LRB', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(85, 6, "", 'LRB', 1, 'L')
    pdf.ln(8)
    pdf.set_fill_color(0, 102, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(115, 8, "DESIGNATION", 1, 0, 'C', True)
    pdf.cell(25, 8, "QTE", 1, 0, 'C', True)
    pdf.cell(40, 8, f"MONTANT ({safe_pdf_txt(devise)})", 1, 1, 'C', True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)
    if isinstance(details_list, list) and details_list:
        for item in details_list:
            nom = safe_pdf_txt(item.get('nom', ''))
            qte = item.get('qte', 1)
            pu = item.get('pu', item.get('prix', 0))
            montant_item = pu * qte
            pdf.cell(115, 7, nom, 1, 0, 'L')
            pdf.cell(25, 7, str(qte), 1, 0, 'C')
            pdf.cell(40, 7, f"{montant_item:,.0f}", 1, 1, 'R')
    else:
        pdf.cell(115, 7, safe_pdf_txt(details_list), 1, 0, 'L')
        pdf.cell(25, 7, "1", 1, 0, 'C')
        pdf.cell(40, 7, f"{montant:,.0f}", 1, 1, 'R')
    if periode:
        pdf.cell(115, 7, f"Periode: {safe_pdf_txt(periode)}", 1, 0, 'L')
        pdf.cell(25, 7, "", 1, 0, 'C')
        pdf.cell(40, 7, "", 1, 1, 'R')
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(140, 10, "MONTANT TOTAL A PAYER", 1, 0, 'R', True)
    pdf.cell(40, 10, f"{montant:,.0f} {safe_pdf_txt(devise)}", 1, 1, 'R', True)
    pdf.ln(10)
    if type_op in ["Loyer", "Vente Voiture"]:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, "SIGNATURE CLIENT:", ln=True)
        pdf.ln(3)
        pdf.set_draw_color(0, 0, 0)
        pdf.line(10, pdf.get_y(), 100, pdf.get_y())
        pdf.set_font("Arial", "", 8)
        pdf.set_xy(10, pdf.get_y() + 1)
        pdf.cell(90, 5, f"Nom: {safe_pdf_txt(client)}", ln=True)
        pdf.set_xy(10, pdf.get_y())
        pdf.cell(90, 5, "Date: ___________________", ln=True)
        pdf.ln(5)
    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(0, 102, 0)
    pdf.cell(0, 6, "Merci pour votre confiance! ASYMAS BUSINESS - Votre partenaire de croissance", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    qr_data = f"""ASYMAS BUSINESS
Facture: {numero}
Type: {type_op}
Client: {client}
Montant: {montant:,.0f} {devise}
Date: {date.today().strftime('%d/%m/%Y')}
Tel: +243 995 105 623"""
    qr_path = generer_qrcode(qr_data)
    y_position = pdf.get_y()
    if y_position > 250:
        pdf.add_page()
        y_position = 30
    pdf.image(qr_path, x=155, y=y_position, w=25)
    os.unlink(qr_path)
    pdf.set_xy(10, y_position + 5)
    pdf.set_font("Arial", "", 8)
    pdf.cell(140, 5, "Scannez ce QR Code pour verifier l'authenticite de la facture", ln=False)
    pdf.set_xy(10, y_position + 10)
    pdf.cell(140, 5, "ASYMAS BUSINESS - Beni, Nord-Kivu, RDC", ln=False)
    return bytes(pdf.output(dest='S'))
def creer_facture_auto(type_op, client, details, montant, devise="FC", details_list=None, tel="+243...", periode=""):
    numero_facture = f"AS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if details_list is None:
        details_list = [{"nom": details, "qte": 1, "pu": montant}]
    pdf_bytes = generer_pdf_facture(numero_facture, type_op, client, details_list, montant, devise, tel, periode)
    try:
        colonnes_compta = get_table_columns("compta")
        data_compta = {
            "type": "Revenu",
            "description": str(f"{type_op} - {client} - {details}"),
            "montant": float(montant),
            "date": str(date.today()),
            "utilisateur": st.session_state.user_name
        }
        if "categorie" in colonnes_compta:
            data_compta["categorie"] = str(type_op)
        if "devise" in colonnes_compta:
            data_compta["devise"] = str(devise)
        if "numero_facture" in colonnes_compta:
            data_compta["numero_facture"] = str(numero_facture)
        if "details" in colonnes_compta:
            data_compta["details"] = json.dumps(details_list)
        supabase.table("compta").insert(data_compta).execute()
        st.toast(f"✅ Enregistré par {st.session_state.user_name}", icon="✅")
    except Exception as e:
        st.error("❌ ERREUR INSERTION COMPTA")
        st.code(repr(e))
    return numero_facture, pdf_bytes

def generer_excel_pro(df_data, titre="Relevé Comptable", total_revenu=0, total_depense=0, solde=0):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_data.to_excel(writer, sheet_name='Releve', index=False, startrow=6)
        workbook = writer.book
        worksheet = writer.sheets['Releve']
        worksheet.merge_cells('A1:F1')
        worksheet['A1'] = 'ASYMAS BUSINESS'
        worksheet['A1'].font = Font(size=20, bold=True, color='006600')
        worksheet['A1'].alignment = Alignment(horizontal='center')
        worksheet.merge_cells('A2:F2')
        worksheet['A2'] = 'Beni, Nord-Kivu, RDC | Tel: +243 995 105 623 | asamnesstsang636@gmail.com'
        worksheet['A2'].font = Font(size=10, italic=True)
        worksheet['A2'].alignment = Alignment(horizontal='center')
        worksheet.merge_cells('A3:F3')
        worksheet['A3'] = f'{titre.upper()} - Edité le {date.today().strftime("%d/%m/%Y")}'
        worksheet['A3'].font = Font(size=14, bold=True, color='FF6600')
        worksheet['A3'].alignment = Alignment(horizontal='center')
        worksheet.merge_cells('A4:F4')
        worksheet['A4'] = f'Total Revenus: {total_revenu:,.0f} FC | Total Dépenses: {total_depense:,.0f} FC | Solde: {solde:,.0f} FC'
        worksheet['A4'].font = Font(size=11, bold=True)
        worksheet['A4'].alignment = Alignment(horizontal='center')
        worksheet['A4'].fill = PatternFill(start_color='FFCC00', end_color='FFCC00', fill_type='solid')
        header_fill = PatternFill(start_color='006600', end_color='006600', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')
        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        for col in range(1, len(df_data.columns) + 1):
            cell = worksheet.cell(row=7, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        for row in range(7, len(df_data) + 8):
            for col in range(1, len(df_data.columns) + 1):
                worksheet.cell(row=row, column=col).border = thin_border
                worksheet.cell(row=row, column=col).alignment = Alignment(horizontal='left')
        for col in range(1, len(df_data.columns) + 1):
            worksheet.column_dimensions[get_column_letter(col)].width = 18
    return output.getvalue()

st.markdown("""
<link rel="manifest" href="data:application/manifest+json,{
  \\"name\\": \\"ASYMAS BUSINESS\\",
  \\"short_name\\": \\"ASYMAS\\",
  \\"start_url\\": \\".\\",
  \\"display\\": \\"standalone\\",
  \\"background_color\\": \\"#000000\\",
  \\"theme_color\\": \\"#00ff41\\",
  \\"description\\": \\"Agriculture Commerce Immobilier Automobile\\",
  \\"icons\\": [{
    \\"src\\": \\"https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f48e.png\\",
    \\"sizes\\": \\"192x192\\",
    \\"type\\": \\"image/png\\"
  }]
}">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
""", unsafe_allow_html=True)

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

passwords_db = load_passwords()

if 'user_role' not in st.session_state:
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.session_state.user_perms = {}
    st.session_state.user_cats = []

if st.session_state.user_role is None:
    st.markdown("# 🔐 ASYMAS BUSINESS - CONNEXION")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("### Choisissez votre profil :")
        df_users_login = load_table("utilisateurs")
        if not df_users_login.empty:
            options_login = ["-- Sélectionner --"] + [f"{row['nom']} - {row['role']}" for _, row in df_users_login.iterrows()]
        else:
            options_login = ["-- Sélectionner --", "PDG TSANG", "Gérante ASIYA", "BASAM"]
        profil = st.selectbox("Utilisateur", options_login)
        password = st.text_input("Mot de passe", type="password", key="pwd")
        if st.button("SE CONNECTER", width="stretch", type="primary"):
            if profil!= "-- Sélectionner --":
                nom_connect = profil.split(" - ")[0]
                role_connect = profil.split(" - ")[1] if " - " in profil else profil
                user_data = df_users_login[df_users_login['nom'] == nom_connect]
                if not user_data.empty and password == user_data.iloc[0]['password']:
                    st.session_state.user_role = user_data.iloc[0]['role']
                    st.session_state.user_name = user_data.iloc[0]['nom']
                    st.session_state.user_perms = user_data.iloc[0].get('permissions', {})
                    st.session_state.user_cats = user_data.iloc[0].get('categories_autorisees', [])
                    st.rerun()
                else:
                    st.error("Profil ou mot de passe incorrect")
    st.stop()

if 'user_role' in st.session_state and st.session_state.user_role is not None:
    with st.sidebar:
        if 'theme_choisi' not in st.session_state: st.session_state.theme_choisi = "Sombre ASYMAS"
        theme = st.selectbox("🎨", ["Sombre ASYMAS","Bleu Pro","Vert Agri","Noir Luxe"], key="theme_choisi", label_visibility="collapsed")
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state.user_role=None
            st.session_state.user_name=None
            st.session_state.user_perms={}
            st.session_state.user_cats=[]
            st.rerun()

    if theme=="Sombre ASYMAS": st.markdown("""<style>.stApp{background:#0E1117;color:#E0E0E0}h1,h2,h3{color:#14B814!important}</style>""",unsafe_allow_html=True)
    elif theme=="Bleu Pro": st.markdown("""<style>.stApp{background:#0A1929;color:#E3F2FD}h1,h2,h3{color:#2196F3!important}</style>""",unsafe_allow_html=True)
    elif theme=="Vert Agri": st.markdown("""<style>.stApp{background:#1B2A1B;color:#E8F5E9}h1,h2,h3{color:#4CAF50!important}</style>""",unsafe_allow_html=True)
    elif theme=="Noir Luxe": st.markdown("""<style>.stApp{background:#000;color:#FFF}h1,h2,h3{color:#FFD700!important}</style>""",unsafe_allow_html=True)

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

df_biens = load_table("biens")
df_articles = load_table("articles")
df_voitures = load_table("voitures")
df_compta = load_table("compta")
df_factures = load_table("factures_proforma")
df_utilisateurs = load_table("utilisateurs")

if 'montant' not in df_compta.columns:
    df_compta['montant'] = 0
if 'type' not in df_compta.columns:
    df_compta['type'] = 'Inconnu'

st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
st.markdown("### Agriculture • Commerce • Immobilier • Automobile • Beni RDC")

with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.user_name}")
    st.markdown(f"**Rôle : {st.session_state.user_role}**")
    st.info("ASYMAS BUSINESS v2.0")
    if st.button("🔄 Actualiser", key="btn_save"):
        st.cache_data.clear()
        st.rerun()

perms = st.session_state.user_perms
if isinstance(perms, str):
    try: perms = json.loads(perms)
    except: perms = {}

# === GESTION DES TABS AVEC PERMISSIONS - TOUT LE MONDE VOIT LES TABS DE BASE ===
tabs_dispo = []
if st.session_state.user_role == "PDG" or perms.get('dashboard', True):
    tabs_dispo.append("📊 Dashboard")
if st.session_state.user_role == "PDG" or perms.get('commerce', True):
    tabs_dispo.append("🛍️ Commerce")
if st.session_state.user_role == "PDG" or perms.get('stock', False):
    tabs_dispo.append("📦 Gestion Stock")
if st.session_state.user_role == "PDG" or perms.get('immobilier', False):
    tabs_dispo.append("🏠 Immobilier")
if st.session_state.user_role == "PDG" or perms.get('automobile', False):
    tabs_dispo.append("🚗 Automobile")
if st.session_state.user_role == "PDG" or perms.get('parc', False):
    tabs_dispo.append("🚘 Gestion Parc")
if st.session_state.user_role == "PDG" or perms.get('comptabilite', False):
    tabs_dispo.append("💰 Comptabilité")
if st.session_state.user_role == "PDG" or perms.get('factures', False):
    tabs_dispo.append("📄 Factures")
if st.session_state.user_role == "PDG" or perms.get('users', False):
    tabs_dispo.append("👥 Utilisateurs")

# Si aucun tab, afficher au moins Dashboard et Commerce
if not tabs_dispo:
    tabs_dispo = ["📊 Dashboard", "🛍️ Commerce"]

tabs = st.tabs(tabs_dispo)
tab_map = {name: tab for name, tab in zip(tabs_dispo, tabs)}

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

        if df_articles.empty:
            st.error("Aucun article disponible - Ajoute des articles dans Gestion Stock")
        else:
            col_gauche, col_droite = st.columns([2,1])
            with col_gauche:
                st.subheader("👤 Client")
                st.session_state.client_com_nom = st.text_input("Nom Client", value=st.session_state.client_com_nom, key="nom_client_c")
                st.session_state.client_com_tel = st.text_input("Téléphone Client", value=st.session_state.client_com_tel, key="tel_client_c")
                st.subheader("📦 Rubrique Produit")
                col_scan1, col_scan2 = st.columns([1,3])
                with col_scan1:
                    qr_code = qrcode_scanner(key='qr_scanner_c')
                with col_scan2:
                    recherche_manuelle = st.text_input("🔍 QR Code ou Nom", placeholder="Scanne ou tape le nom...", key="search_c").strip()
                recherche = qr_code if qr_code else recherche_manuelle
                if qr_code:
                    st.success(f"QR Scanné: {qr_code}")
                df_articles_filtre = df_articles[df_articles['stock'] > 0].copy()
                if recherche:
                    search_clean = str(recherche).upper().strip()
                    mask = df_articles_filtre['nom_article'].str.contains(recherche, case=False, na=False)
                    if 'code_qr' in df_articles_filtre.columns:
                        mask = mask | df_articles_filtre['code_qr'].astype(str).str.upper().str.contains(search_clean, case=False, na=False)
                    df_articles_filtre = df_articles_filtre
                if df_articles_filtre.empty:
                    st.warning("⚠️ Aucun produit disponible")
                else:
                    st.success(f"✅ {len(df_articles_filtre)} produit(s) disponible(s)")
                    options_articles = []
                    for _, p in df_articles_filtre.iterrows():
                        qr_txt = f" | QR:{p['code_qr']}" if 'code_qr' in p and p['code_qr'] else ""
                        options_articles.append(f"{p['nom_article']} | Stock:{int(p['stock'])} | {p['prix_vente']:,.0f} FC{qr_txt} | ID:{p['id']}")
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
                    st.download_button(
                        "📥 Télécharger Facture PDF",
                        data=st.session_state.pdf_data,
                        file_name=f"{st.session_state.num_fact}.pdf",
                        mime="application/pdf",
                        width="stretch"
                    )
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
                    if st.button("NOUVELLE VENTE", width="stretch"):
                        st.session_state.vente_finie = False
                        st.session_state.pdf_data = None
                        st.session_state.num_fact = None
                        st.session_state.client_com_nom = ""
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
                                    supabase.table("ventes").insert({
                                        "numero_facture": num_fact,
                                        "client_nom": st.session_state.client_com_nom,
                                        "article_id": item['id'],
                                        "quantite": item['qte'],
                                        "prix_unitaire": item['pu'],
                                        "total": item['qte'] * item['pu']
                                    }).execute()
                                    stock_actuel = df_articles[df_articles['id'] == item['id']]['stock'].iloc[0]
                                    supabase.table("articles").update({"stock": int(stock_actuel - item['qte'])}).eq("id", item['id']).execute()
                                    details_list.append({
                                        "nom": item['nom'],
                                        "qte": item['qte'],
                                        "pu": item['pu'],
                                        "total": item['qte'] * item['pu']
                                    })
                                details_json = json.dumps(details_list)
                                supabase.table("compta").insert({
                                    "date": str(date.today()),
                                    "type": "Revenu",
                                    "categorie": "Vente Commerce",
                                    "description": f"Vente - {st.session_state.client_com_nom}",
                                    "montant": float(total_panier),
                                    "devise": "FC",
                                    "numero_facture": num_fact,
                                    "details": details_json,
                                    "utilisateur": st.session_state.user_name
                                }).execute()
                                pdf_bytes = generer_pdf_facture(
                                    num_fact,
                                    "Vente Commerce",
                                    st.session_state.client_com_nom,
                                    details_list,
                                    total_panier,
                                    "FC",
                                    st.session_state.client_com_tel
                                )
                                st.session_state.pdf_data = pdf_bytes
                                st.session_state.num_fact = num_fact
                                st.session_state.vente_finie = True
                                st.session_state.panier_commerce = []
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur finalisation vente")
                                st.code(repr(e))

if "📦 Gestion Stock" in tab_map:
    with tab_map["📦 Gestion Stock"]:
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
                        supabase.table("articles").insert({"nom_article": str(nom), "categorie": str(cat), "prix_achat": float(prix_achat), "prix_vente": float(prix_vente), "stock": int(stock)}).execute()
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
                            supabase.table("articles").update({"nom_article": str(new_nom), "categorie": str(new_cat), "prix_achat": float(new_prix_a), "prix_vente": float(new_prix_v), "stock": int(new_stock)}).eq("id", int(row['id'])).execute()
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
                    else:
                        c2.info("🔒 Suppression non autorisée")

if "🏠 Immobilier" in tab_map:
    with tab_map["🏠 Immobilier"]:
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
                    {"nom": f"Loyer {type_bien} | Adresse: {adresse} | Duree: {duree_contrat}", "qte": 1, "pu": prix},
                    {"nom": f"Electricite | {type_bien} - {adresse}", "qte": 1, "pu": electricite},
                    {"nom": f"Eau | {type_bien} - {adresse}", "qte": 1, "pu": eau}
                ]
                details_text = f"LOUER: {type_bien} | Adresse: {adresse} | Duree Contrat: {duree_contrat} | Loyer: {prix} $ | Electricite: {electricite} $ | Eau: {eau} $"
                periode = date.today().strftime("%B %Y")
                num_fact, pdf_bytes = creer_facture_auto("Loyer", nom_client, details_text, total_mensuel, "$", details_list, tel_client, periode)
                st.success(f"✅ Facture générée : {num_fact}")
                st.download_button(
                    label="📥 Télécharger Facture PDF",
                    data=bytes(pdf_bytes),
                    file_name=f"{num_fact}.pdf",
                    mime="application/pdf",
                    width="stretch",
                    key="dl_facture_immo"
                )
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

if "🚗 Automobile" in tab_map:
    with tab_map["🚗 Automobile"]:
        st.markdown("## 🚗 Automobile - Point de Vente")
        if 'panier_voiture' not in st.session_state:
            st.session_state.panier_voiture = []
        if 'vente_auto_finie' not in st.session_state:
            st.session_state.vente_auto_finie = False
        if 'pdf_auto' not in st.session_state:
            st.session_state.pdf_auto = None
        if 'num_fact_auto' not in st.session_state:
            st.session_state.num_fact_auto = None
        if 'client_auto_nom' not in st.session_state:
            st.session_state.client_auto_nom = ""
        if 'client_auto_tel' not in st.session_state:
            st.session_state.client_auto_tel = "+243..."

        if df_voitures.empty:
            st.error("Aucune voiture disponible - Ajoute des voitures dans Gestion Parc")
        else:
            col_gauche, col_droite = st.columns([2,1])
            with col_gauche:
                st.subheader("👤 Client")
                st.session_state.client_auto_nom = st.text_input("Nom Client", value=st.session_state.client_auto_nom, key="nom_client_v")
                st.session_state.client_auto_tel = st.text_input("Téléphone Client", value=st.session_state.client_auto_tel, key="tel_client_v")
                st.subheader("🔍 Choisir Voiture")
                search_qr = st.text_input("QR Code, Plaque, Marque ou Modèle", placeholder="Filtre la liste...", key="search_voiture_qr").strip()
                df_voitures_dispo = df_voitures[(df_voitures['statut'] == 'Disponible') & (df_voitures['quantite'] > 0)]
                if search_qr:
                    search_clean = search_qr.upper()
                    df_voitures_dispo = df_voitures_dispo[
                        df_voitures_dispo['code_qr'].str.contains(search_clean, case=False, na=False) |
                        df_voitures_dispo['plaque'].str.contains(search_clean, case=False, na=False) |
                        df_voitures_dispo['marque'].str.contains(search_clean, case=False, na=False) |
                        df_voitures_dispo['modele'].str.contains(search_clean, case=False, na=False)
                    ]
                if df_voitures_dispo.empty:
                    st.warning("⚠️ Aucune voiture disponible")
                else:
                    st.success(f"✅ {len(df_voitures_dispo)} véhicule(s) disponible(s)")
                    options_voitures = []
                    for _, v in df_voitures_dispo.iterrows():
                        options_voitures.append(f"{v['marque']} {v['modele']} {v.get('annee','')} | {v.get('couleur','')} | {v['plaque']} | Stock:{int(v.get('quantite',1))} | {v['prix']:,.0f}$ | ID:{v['id']}")
                    voiture_choisie = st.selectbox("Sélectionne le véhicule", options_voitures, key="select_voiture_unique")
                    if voiture_choisie:
                        id_choisi = int(voiture_choisie.split("ID:")[1])
                        v = df_voitures_dispo[df_voitures_dispo['id'] == id_choisi].iloc[0]
                        c1, c2, c3 = st.columns(3)
                        qte_max = int(v.get('quantite', 1))
                        qte = c1.number_input("Quantité", min_value=1, max_value=qte_max, value=1, key=f"qte_v_unique")
                        c2.metric("Stock dispo", qte_max)
                        c3.metric("Prix unitaire", f"{v['prix']:,.0f}$")
                        st.info(f"**{v['marque']} {v['modele']}** | Couleur: {v.get('couleur','N/A')} | Qualité: {v.get('qualite','N/A')} | QR: {v.get('code_qr','N/A')}")
                        if st.button("🛒 AJOUTER AU PANIER", type="primary", width="stretch", key="add_voiture_unique"):
                            existant = next((item for item in st.session_state.panier_voiture if item['id'] == int(v['id'])), None)
                            if existant:
                                if existant['qte'] + qte <= qte_max:
                                    existant['qte'] += qte
                                    st.success(f"Panier mis à jour: {existant['qte']}x")
                                else:
                                    st.error(f"Stock insuffisant! Max dispo: {qte_max}")
                            else:
                                st.session_state.panier_voiture.append({
                                    "id": int(v['id']),
                                    "nom": f"{v['marque']} {v['modele']} {v.get('annee','')}",
                                    "pu": float(v['prix']),
                                    "qte": int(qte),
                                    "plaque": v.get('plaque',''),
                                    "qualite": v.get('qualite',''),
                                    "code_qr": v.get('code_qr',''),
                                    "stock_max": qte_max
                                })
                                st.success("Ajouté au panier")
                            st.rerun()
            with col_droite:
                st.subheader("🛒 Panier Voiture")
                total_voiture = 0
                if st.session_state.vente_auto_finie and st.session_state.pdf_auto:
                    st.success(f"✅ Vente validée - {st.session_state.total_auto:,.0f} $")
                    st.info(f"📄 Facture: {st.session_state.num_fact_auto}")
                    if st.session_state.pdf_auto:
                        st.download_button(
                            label="📥 TÉLÉCHARGER LE PDF",
                            data=bytes(st.session_state.pdf_auto),
                            file_name=f"{st.session_state.num_fact_auto}.pdf",
                            mime="application/pdf",
                            width="stretch",
                            key="dl_facture_auto"
                        )
                    pdf_b64 = base64.b64encode(st.session_state.pdf_auto).decode()
                    st.components.v1.html(f"""
                        <button onclick="printPDFAuto()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">
                            🖨️ IMPRIMER LA FACTURE
                        </button>
                        <script>
                        function printPDFAuto() {{
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
                        st.session_state.client_auto_nom = ""
                        st.session_state.client_auto_tel = "+243..."
                        st.rerun()
                elif not st.session_state.panier_voiture:
                    st.info("Panier vide")
                else:
                    for idx, item in enumerate(st.session_state.panier_voiture):
                        col1, col2, col3, col4 = st.columns([3,1,1,1])
                        col1.write(f"**{item['nom']}** | {item.get('qualite','')} | {item['plaque']}")
                        col2.write(f"Qté: {item['qte']}")
                        col3.write(f"{item['pu'] * item['qte']:,.2f} $")
                        if col4.button("❌", key=f"del_v_{idx}"):
                            st.session_state.panier_voiture.pop(idx)
                            st.rerun()
                        total_voiture += item['pu'] * item['qte']
                    st.metric("💰 TOTAL VOITURE", f"{total_voiture:,.2f} $")
                    st.markdown(f"**Client:** {st.session_state.client_auto_nom}")
                    st.markdown(f"**Tel:** {st.session_state.client_auto_tel}")
                    if st.button("✅ FINALISER VENTE VOITURE", type="primary", width="stretch"):
                        if st.session_state.client_auto_nom and st.session_state.panier_voiture:
                            try:
                                details_list = [{"nom": f"{item['nom']} | {item.get('qualite','')} | {item['plaque']}",
                                                "qte": item['qte'], "pu": item['pu']} for item in st.session_state.panier_voiture]
                                details_text = " | ".join([f"{item['qte']}x {item['nom']} ({item.get('qualite','')})" for item in st.session_state.panier_voiture])
                                num_fact, pdf_bytes = creer_facture_auto("Vente Voiture", st.session_state.client_auto_nom, details_text, total_voiture, "$", details_list, st.session_state.client_auto_tel, "")
                                for item in st.session_state.panier_voiture:
                                    supabase.table("voitures").update({
                                        "quantite": item['stock_max'] - item['qte'],
                                        "statut": "Vendue" if item['stock_max'] - item['qte'] == 0 else "Disponible"
                                    }).eq("id", item['id']).execute()
                                st.session_state.vente_auto_finie = True
                                st.session_state.pdf_auto = pdf_bytes
                                st.session_state.num_fact_auto = num_fact
                                st.session_state.total_auto = total_voiture
                                st.session_state.panier_voiture = []
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur finalisation: {e}")
                        else:
                            st.error("Nom client obligatoire - Remplis à gauche")

if "🚘 Gestion Parc" in tab_map:
    with tab_map["🚘 Gestion Parc"]:
        st.markdown("## 🚘 Gestion Parc Automobile")
        colonnes_voitures = get_table_columns("voitures")
        with st.expander("➕ Ajouter Nouvelle Voiture"):
            with st.form("form_voiture", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                marque = c1.text_input("Marque")
                modele = c2.text_input("Modèle")
                annee = c3.text_input("Année")
                data_insert = {"marque": str(marque), "modele": str(modele), "annee": str(annee)}
                if "plaque" in colonnes_voitures:
                    plaque = c1.text_input("Plaque")
                    data_insert["plaque"] = str(plaque)
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
                if "prix" in colonnes_voitures:
                    prix = c3.number_input("Prix $", min_value=0.0, value=0.0)
                    data_insert["prix"] = float(prix)
                if "statut" in colonnes_voitures:
                    statut = c1.selectbox("Statut", ["Disponible", "Réservée", "Vendue"])
                    data_insert["statut"] = str(statut)
                if "quantite" in colonnes_voitures:
                    quantite = c2.number_input("Quantité en Stock", min_value=1, value=1)
                    data_insert["quantite"] = int(quantite)
                if "qualite" in colonnes_voitures:
                    qualite = c3.selectbox("Qualité", ["Neuf", "Occasion", "Reconditionné"])
                    data_insert["qualite"] = str(qualite)
                if "code_qr" in colonnes_voitures:
                    code_qr = c1.text_input("Code QR", placeholder="Scanner ou générer")
                    data_insert["code_qr"] = str(code_qr)
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
        st.subheader("📋 Liste des Voitures")
        if df_voitures.empty:
            st.info("Aucune voiture")
        else:
            for _, row in df_voitures.iterrows():
                with st.expander(f"{row['marque']} {row['modele']} - {row.get('plaque','')} - Stock:{row.get('quantite',0)} - {row.get('statut','')}"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        new_marque = st.text_input("Marque", value=row['marque'], key=f"marque_{row['id']}")
                        new_modele = st.text_input("Modèle", value=row['modele'], key=f"modele_{row['id']}")
                        new_annee = st.text_input("Année", value=row.get('annee',''), key=f"annee_{row['id']}")
                    data_update = {"marque": str(new_marque), "modele": str(new_modele), "annee": str(new_annee)}
                    with c2:
                        if "plaque" in colonnes_voitures:
                            new_plaque = st.text_input("Plaque", value=row.get('plaque',''), key=f"plaque_{row['id']}")
                            data_update["plaque"] = str(new_plaque)
                        if "couleur" in colonnes_voitures:
                            new_couleur = st.text_input("Couleur", value=row.get('couleur',''), key=f"couleur_{row['id']}")
                            data_update["couleur"] = str(new_couleur)
                        if "kilometrage" in colonnes_voitures:
                            km_val = row.get('kilometrage', 0)
                            try:
                                km_val = int(float(km_val)) if km_val else 0
                            except:
                                km_val = 0
                            new_km = st.number_input("KM", value=km_val, key=f"km_{row['id']}")
                            data_update["kilometrage"] = int(new_km)
                    with c3:
                        if "carburant" in colonnes_voitures:
                            carburant_options = ["Essence", "Diesel", "Hybride", "Électrique"]
                            carb_val = row.get('carburant','Essence')
                            new_carb = st.selectbox("Carburant", carburant_options, index=carburant_options.index(carb_val) if carb_val in carburant_options else 0, key=f"carb_{row['id']}")
                            data_update["carburant"] = str(new_carb)
                        if "boite" in colonnes_voitures:
                            boite_options = ["Manuelle", "Automatique"]
                            boite_val = row.get('boite','Manuelle')
                            new_boite = st.selectbox("Boîte", boite_options, index=boite_options.index(boite_val) if boite_val in boite_options else 0, key=f"boite_{row['id']}")
                            data_update["boite"] = str(new_boite)
                        if "prix" in colonnes_voitures:
                            new_prix = st.number_input("Prix $", value=float(row.get('prix',0)), key=f"prix_{row['id']}")
                            data_update["prix"] = float(new_prix)
                        if "statut" in colonnes_voitures:
                            statut_options = ["Disponible", "Réservée", "Vendue"]
                            statut_val = row.get('statut','Disponible')
                            new_statut = st.selectbox("Statut", statut_options, index=statut_options.index(statut_val) if statut_val in statut_options else 0, key=f"statut_{row['id']}")
                            data_update["statut"] = str(new_statut)
                        if "quantite" in colonnes_voitures:
                            new_qte = st.number_input("Stock", value=int(row.get('quantite',1)), min_value=0, key=f"qte_{row['id']}")
                            data_update["quantite"] = int(new_qte)
                        if "qualite" in colonnes_voitures:
                            qualite_options = ["Neuf", "Occasion", "Reconditionné"]
                            qualite_val = row.get('qualite','Neuf')
                            new_qualite = st.selectbox("Qualité", qualite_options, index=qualite_options.index(qualite_val) if qualite_val in qualite_options else 0, key=f"qual_{row['id']}")
                            data_update["qualite"] = str(new_qualite)
                        if "code_qr" in colonnes_voitures:
                            new_code_qr = st.text_input("Code QR", value=row.get('code_qr',''), key=f"qr_{row['id']}")
                            data_update["code_qr"] = str(new_code_qr)
                    c1, c2 = st.columns(2)
                    if c1.button("✏️ Modifier", key=f"mod_v_{row['id']}", width="stretch"):
                        try:
                            supabase.table("voitures").update(data_update).eq("id", int(row['id'])).execute()
                            st.success("Modifié")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur modif")
                            st.code(repr(e))
                    if st.session_state.user_role == "PDG" or perms.get('supprimer', False):
                        if c2.button("🗑️ Supprimer", key=f"del_v_{row['id']}", width="stretch"):
                            try:
                                supabase.table("voitures").delete().eq("id", int(row['id'])).execute()
                                st.success("Supprimé")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur suppression")
                                st.code(repr(e))
                    else:
                        c2.info("🔒 Suppression non autorisée")

if "💰 Comptabilité" in tab_map:
    with tab_map["💰 Comptabilité"]:
        st.markdown("## 💰 Comptabilité - Relevé par Catégorie")
        colonnes_compta = get_table_columns("compta")
        with st.expander("➕ Ajouter Opération"):
            with st.form("form_compta", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                type_op = c1.selectbox("Type", ["Revenu", "Dépense"])
                cat = c2.text_input("Catégorie", placeholder="Ex: Loyer, Vente Auto, Carburant")
                montant = c3.number_input("Montant", min_value=0.0)
                data_insert = {"type": str(type_op), "categorie": str(cat), "montant": float(montant), "utilisateur": st.session_state.user_name}
                if "description" in colonnes_compta:
                    desc = c1.text_input("Description", placeholder="Ex: Loyer - Client Jean")
                    data_insert["description"] = str(desc)
                if "devise" in colonnes_compta:
                    devise = c2.selectbox("Devise", ["FC", "$", "€"])
                    data_insert["devise"] = str(devise)
                if "date" in colonnes_compta:
                    date_op = c3.date_input("Date", value=date.today())
                    data_insert["date"] = str(date_op)
                if st.form_submit_button("💾 Ajouter Opération"):
                    try:
                        supabase.table("compta").insert(data_insert).execute()
                        st.success("Opération ajoutée")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout")
                        st.code(repr(e))
        st.divider()
        if df_compta.empty:
            st.info("Aucune opération")
        else:
            df_compta_sorted = df_compta.sort_values('date', ascending=False)
            col_f1, col_f2, col_f3 = st.columns(3)
            date_debut = col_f1.date_input("📅 Date début", value=date.today() - timedelta(days=30), key="date_debut_compta")
            date_fin = col_f2.date_input("📅 Date fin", value=date.today(), key="date_fin_compta")
            filtre_nom = col_f3.text_input("👤 Nom Client", placeholder="Tape un nom...", key="filtre_nom_compta")

            df_filtre_compta = df_compta_sorted[(df_compta_sorted['date'] >= str(date_debut)) & (df_compta_sorted['date'] <= str(date_fin))]
            if filtre_nom:
                df_filtre_compta = df_filtre_compta[df_filtre_compta['description'].str.contains(filtre_nom, case=False, na=False)]

            col_t1, col_t2, col_t3 = st.columns(3)
            total_fc = df_filtre_compta[df_filtre_compta.get('devise','FC')=='FC']['montant'].sum()
            total_usd = df_filtre_compta[df_filtre_compta.get('devise','FC')=='$']['montant'].sum()
            total_eur = df_filtre_compta[df_filtre_compta.get('devise','FC')=='€']['montant'].sum()
            col_t1.metric("💵 Total FC", f"{total_fc:,.0f}")
            col_t2.metric("💵 Total USD", f"{total_usd:,.0f}")
            col_t3.metric("💵 Total EUR", f"{total_eur:,.0f}")
            st.divider()

            categories = df_filtre_compta.get('categorie', pd.Series(dtype=str)).dropna().unique()
            if len(categories) == 0:
                st.info("Aucune opération trouvée avec ces filtres")
            else:
                for cat in sorted(categories):
                    df_cat = df_filtre_compta[df_filtre_compta.get('categorie', '') == cat]
                    total_cat_fc = df_cat[df_cat.get('devise','FC')=='FC']['montant'].sum()
                    total_cat_usd = df_cat[df_cat.get('devise','FC')=='$']['montant'].sum()
                    total_cat_eur = df_cat[df_cat.get('devise','FC')=='€']['montant'].sum()
                    total_cat = total_cat_fc + total_cat_usd + total_cat_eur

                    with st.expander(f"📁 {cat} - {len(df_cat)} opérations - Total: {total_cat:,.0f}", expanded=False):
                        colonnes_affiche = ['date', 'type', 'description', 'montant', 'devise']
                        if 'utilisateur' in df_cat.columns:
                            colonnes_affiche.append('utilisateur')
                        st.dataframe(df_cat[colonnes_affiche], use_container_width=True, hide_index=True)

                        col_dl1, col_dl2 = st.columns(2)
                        excel_bytes_cat = generer_excel_pro(
                            df_cat,
                            f"Releve {cat} {date_debut}-{date_fin}",
                            df_cat[df_cat['type']=='Revenu']['montant'].sum(),
                            df_cat[df_cat['type']=='Dépense']['montant'].sum(),
                            df_cat[df_cat['type']=='Revenu']['montant'].sum() - df_cat[df_cat['type']=='Dépense']['montant'].sum()
                        )
                        safe_cat = str(cat).replace(" ", "_").replace("/", "_")
                        col_dl1.download_button(
                            label=f"📥 {cat} - EXCEL",
                            data=excel_bytes_cat,
                            file_name=f"Compta_{safe_cat}_{date_debut}_{date_fin}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            width="stretch",
                            key=f"dl_excel_compta_{safe_cat}_{date_debut}_{filtre_nom}"
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
                        pdf_cat.set_font("Arial", "B", 10)
                        pdf_cat.set_xy(150, 8)
                        filtre_txt = f"Filtre: {filtre_nom}" if filtre_nom else "Tous"
                        pdf_cat.cell(50, 6, f"Periode: {date_debut} au {date_fin}", ln=True, align="R")
                        pdf_cat.set_xy(150, 14)
                        pdf_cat.cell(50, 6, filtre_txt, ln=True, align="R")
                        pdf_cat.ln(15)
                        pdf_cat.set_text_color(0, 0, 0)
                        pdf_cat.set_fill_color(255, 204, 0)
                        pdf_cat.set_font("Arial", "B", 14)
                        pdf_cat.cell(0, 10, f"RELEVE COMPTABLE - {safe_pdf_txt(cat).upper()}", ln=True, fill=True)
                        pdf_cat.ln(5)
                        pdf_cat.set_font("Arial", "B", 11)
                        pdf_cat.cell(0, 8, f"Total FC: {total_cat_fc:,.0f} | USD: {total_cat_usd:,.0f} | EUR: {total_cat_eur:,.0f}", ln=True)
                        pdf_cat.ln(3)
                        pdf_cat.set_font("Arial", "B", 9)
                        pdf_cat.cell(20, 7, "Date", 1)
                        pdf_cat.cell(20, 7, "Type", 1)
                        pdf_cat.cell(70, 7, "Description", 1)
                        pdf_cat.cell(25, 7, "Montant", 1)
                        pdf_cat.cell(15, 7, "Dev", 1)
                        pdf_cat.cell(30, 7, "Utilisateur", 1, ln=True)
                        pdf_cat.set_font("Arial", "", 8)
                        for _, row in df_cat.iterrows():
                            try:
                                pdf_cat.cell(20, 6, safe_pdf_txt(row.get('date','')), 1)
                                pdf_cat.cell(20, 6, safe_pdf_txt(row.get('type','')), 1)
                                desc = safe_pdf_txt(row.get('description',''))[:35]
                                pdf_cat.cell(70, 6, desc, 1)
                                pdf_cat.cell(25, 6, f"{row.get('montant',0):,.0f}", 1)
                                pdf_cat.cell(15, 6, safe_pdf_txt(row.get('devise','FC')), 1)
                                pdf_cat.cell(30, 6, safe_pdf_txt(row.get('utilisateur','N/A')), 1, ln=True)
                            except:
                                continue
                        pdf_bytes_cat = bytes(pdf_cat.output(dest='S'))
                        col_dl2.download_button(
                            label=f"📥 {cat} - PDF",
                            data=pdf_bytes_cat,
                            file_name=f"Compta_{safe_cat}_{date_debut}_{date_fin}.pdf",
                            mime="application/pdf",
                            width="stretch",
                            key=f"dl_pdf_compta_{safe_cat}_{date_debut}_{filtre_nom}"
                        )
                        pdf_b64 = base64.b64encode(pdf_bytes_cat).decode()
                        st.components.v1.html(f"""
                            <button onclick="printPDF_{safe_cat}()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">
                                🖨️ IMPRIMER LE RELEVÉ {cat}
                            </button>
                            <script>
                            function printPDF_{safe_cat}() {{
                                const pdfData = 'data:application/pdf;base64,{pdf_b64}';
                                const win = window.open('', '_blank');
                                win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');
                                win.document.close();
                                setTimeout(() => {{ win.print(); }}, 1000);
                            }}
                            </script>
                        """, height=60)

if "📄 Factures" in tab_map:
    with tab_map["📄 Factures"]:
        st.markdown("## 📄 Factures - Relevé par Catégorie")
        if df_compta.empty:
            st.info("Aucune opération")
        else:
            df_compta_sorted = df_compta.sort_values('date', ascending=False)
            col_f1, col_f2, col_f3 = st.columns(3)
            date_debut = col_f1.date_input("📅 Date début", value=date.today() - timedelta(days=30), key="date_debut_fact")
            date_fin = col_f2.date_input("📅 Date fin", value=date.today(), key="date_fin_fact")
            col_f4, col_f5 = st.columns(2)

            # === FILTRE OBLIGATOIRE PAR CATÉGORIE AUTORISÉE ===
            if st.session_state.user_role != "PDG":
                cats_user = st.session_state.get('user_cats', [])
                if cats_user and "Toutes" not in cats_user:
                    df_compta_sorted = df_compta_sorted[df_compta_sorted['categorie'].isin(cats_user)]
                else:
                    if not cats_user:
                        st.error("⛔ Aucune catégorie autorisée. Contacte le PDG.")
                        st.stop()

            categories_fact = ["Toutes"] + list(df_compta_sorted.get('categorie', pd.Series(dtype=str)).dropna().unique())
            filtre_cat_fact = col_f4.selectbox("📂 Filtrer par Catégorie", categories_fact, key="filtre_cat_fact")
            filtre_client_fact = col_f5.text_input("👤 Nom Client contient", placeholder="Tape un nom...", key="filtre_client_fact")
            df_filtre_fact = df_compta_sorted[(df_compta_sorted['date'] >= str(date_debut)) & (df_compta_sorted['date'] <= str(date_fin))]

            if filtre_cat_fact != "Toutes":
                df_filtre_fact = df_filtre_fact[df_filtre_fact.get('categorie', '') == filtre_cat_fact]
            if filtre_client_fact:
                df_filtre_fact = df_filtre_fact[df_filtre_fact['description'].str.contains(filtre_client_fact, case=False, na=False)]

            col_t1, col_t2, col_t3 = st.columns(3)
            total_fc = df_filtre_fact[df_filtre_fact.get('devise','FC')=='FC']['montant'].sum()
            total_usd = df_filtre_fact[df_filtre_fact.get('devise','FC')=='$']['montant'].sum()
            total_eur = df_filtre_fact[df_filtre_fact.get('devise','FC')=='€']['montant'].sum()
            col_t1.metric("💵 Total FC", f"{total_fc:,.0f}")
            col_t2.metric("💵 Total USD", f"{total_usd:,.0f}")
            col_t3.metric("💵 Total EUR", f"{total_eur:,.0f}")
            st.divider()

            categories = df_filtre_fact.get('categorie', pd.Series(dtype=str)).dropna().unique()
            if len(categories) == 0:
                st.info("Aucune catégorie trouvée dans la période sélectionnée")
            else:
                for cat in sorted(categories):
                    df_cat = df_filtre_fact[df_filtre_fact.get('categorie', '') == cat]
                    total_cat_fc = df_cat[df_cat.get('devise','FC')=='FC']['montant'].sum()
                    total_cat_usd = df_cat[df_cat.get('devise','FC')=='$']['montant'].sum()
                    total_cat_eur = df_cat[df_cat.get('devise','FC')=='€']['montant'].sum()
                    with st.expander(f"📁 {cat} - {len(df_cat)} opérations | FC: {total_cat_fc:,.0f} | $: {total_cat_usd:,.0f} | €: {total_cat_eur:,.0f}", expanded=True):
                        for idx, row in df_cat.iterrows():
                            # === 8 COLONNES : Date, Type, Desc, Montant, User, PDF, Imprimer, Supprimer ===
                            col_a, col_b, col_c, col_d, col_e, col_f, col_g, col_h = st.columns([1.2,0.8,2.5,1,0.8,0.5,0.5])
                            col_a.write(f"**{row.get('date','')}**")
                            col_b.write(f"{row.get('type','')}")
                            col_c.write(f"{row.get('description','')}")
                            col_d.write(f"**{row.get('montant',0):,.0f} {row.get('devise','FC')}**")
                            col_e.write(f"👤 {row.get('utilisateur','N/A')}")

                            # === BOUTON TÉLÉCHARGER PDF ===
                            try:
                                details_list = []
                                if row.get('details') and str(row.get('details')) != 'nan':
                                    details_list = json.loads(row['details'])
                                else:
                                    details_list = [{"nom": row.get('description',''), "qte": 1, "pu": row.get('montant',0)}]

                                client_nom = row.get('description', '').split(' - ')[1] if ' - ' in row.get('description','') else 'Client'
                                pdf_bytes = generer_pdf_facture(
                                    row.get('numero_facture', f"FACT-{row['id']}"),
                                    row.get('categorie', 'Facture'),
                                    client_nom,
                                    details_list,
                                    row.get('montant',0),
                                    row.get('devise','FC'),
                                    "+243...",
                                    ""
                                )
                                col_f.download_button(
                                    "📥",
                                    data=pdf_bytes,
                                    file_name=f"{row.get('numero_facture', f'FACT-{row['id']}')}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_fact_{row['id']}",
                                    help="Télécharger PDF"
                                )

                                # === BOUTON IMPRIMER ===
                                pdf_b64 = base64.b64encode(pdf_bytes).decode()
                                col_g.markdown(f"""
                                    <button onclick="printPDF_{row['id']}()" style="width:100%; padding:2px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; font-size:16px;">
                                        🖨️
                                    </button>
                                    <script>
                                    function printPDF_{row['id']}() {{
                                        const pdfData = 'data:application/pdf;base64,{pdf_b64}';
                                        const win = window.open('', '_blank');
                                        win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');
                                        win.document.close();
                                        setTimeout(() => {{ win.print(); }}, 1000);
                                    }}
                                    </script>
                                """, unsafe_allow_html=True)

                                # === BOUTON SUPPRIMER - PDG UNIQUEMENT ===
                                if st.session_state.user_role == "PDG" or perms.get('supprimer', False):
                                   if col_g.button("🗑️", key=f"del_fact_{row['id']}", help="Supprimer cette facture"):
                                        try:
                                            supabase.table("compta").delete().eq("id", int(row['id'])).execute()
                                            st.success(f"Facture {row.get('numero_facture', row['id'])} supprimée")
                                            st.cache_data.clear()
                                            st.rerun()
                                        except Exception as e:
                                            st.error("Erreur suppression")
                                            st.code(repr(e))
                                else:
                                    col_h.write("")
                                    
                            except Exception as e:
                                col_f.write("❌")
                                col_g.write("❌")
                                col_h.write("❌")
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
                perm_stock = col3.checkbox("Gestion Stock", value=(role_user in ["PDG","GERANTE"]))
                perm_immo = col4.checkbox("Immobilier", value=(role_user in ["PDG","GERANTE"]))
                col1, col2, col3, col4 = st.columns(4)
                perm_auto = col1.checkbox("Automobile", value=(role_user in ["PDG","GERANTE"]))
                perm_parc = col2.checkbox("Gestion Parc", value=(role_user in ["PDG","GERANTE"]))
                perm_compta = col3.checkbox("Comptabilité", value=(role_user in ["PDG","GERANTE"]))
                perm_factures = col4.checkbox("Factures", value=(role_user in ["PDG","GERANTE"]))
                col1, col2 = st.columns(2)
                perm_supprimer = col1.checkbox("🗑️ Peut Supprimer", value=(role_user=="PDG"))
                perm_users = col2.checkbox("👥 Gérer Utilisateurs", value=(role_user=="PDG"))

                st.markdown("**📂 Catégories de Factures Visibles :**")
                categories_dispo = ["Toutes", "Loyer", "Vente Commerce", "Vente Voiture", "Carburant", "Dépense", "Revenu"]
                cats_autorisees = st.multiselect(
                    "Sélectionne les catégories que cet utilisateur peut voir dans Factures",
                    categories_dispo,
                    default=["Toutes"],
                    key="cats_user_new"
                )

                if st.form_submit_button("💾 Ajouter Utilisateur", type="primary"):
                    if not nom_user or not pwd_user:
                        st.error("Nom et mot de passe obligatoires")
                    else:
                        try:
                            permissions = {
                                "dashboard": perm_dashboard, "commerce": perm_commerce, "stock": perm_stock,
                                "immobilier": perm_immo, "automobile": perm_auto, "parc": perm_parc,
                                "comptabilite": perm_compta, "factures": perm_factures,
                                "supprimer": perm_supprimer, "users": perm_users
                            }
                            supabase.table("utilisateurs").insert({
                                "nom": str(nom_user),
                                "role": str(role_user),
                                "password": str(pwd_user),
                                "permissions": permissions,
                                "categories_autorisees": cats_autorisees if "Toutes" not in cats_autorisees else []
                            }).execute()
                            st.success(f"✅ Utilisateur {nom_user} ajouté avec rôle {role_user}")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("❌ ERREUR AJOUT UTILISATEUR")
                            st.code(f"ERREUR COMPLÈTE : {repr(e)}")

        st.divider()
        st.subheader("📋 Liste des Utilisateurs")
        if df_utilisateurs.empty:
            st.info("Aucun utilisateur")
        else:
            for _, row in df_utilisateurs.iterrows():
                perms_user = row.get('permissions', {})
                if isinstance(perms_user, str):
                    try:
                        perms_user = json.loads(perms_user)
                    except:
                        perms_user = {}
                cats_user = row.get('categories_autorisees', [])
                if cats_user is None:
                    cats_user = []
                with st.expander(f"{row['nom']} - {row['role']}", expanded=False):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_nom = st.text_input("Nom", value=row['nom'], key=f"nom_u_{row['id']}")
                        new_role = st.selectbox("Rôle", ["PDG", "GERANTE", "UTILISATEUR", "CAISSIER", "COMMERCIAL"],
                                               index=["PDG", "GERANTE", "UTILISATEUR", "CAISSIER", "COMMERCIAL"].index(row['role']) if row['role'] in ["PDG", "GERANTE", "UTILISATEUR", "CAISSIER", "COMMERCIAL"] else 2,
                                               key=f"role_u_{row['id']}")
                    with c2:
                        new_pwd = st.text_input("Nouveau mot de passe", type="password", placeholder="Laisser vide pour garder l'ancien", key=f"pwd_u_{row['id']}")
                    st.markdown("**🔐 Autorisations d'onglets :**")
                    col1, col2, col3, col4 = st.columns(4)
                    p_dashboard = col1.checkbox("Dashboard", value=perms_user.get('dashboard',True), key=f"p1_{row['id']}")
                    p_commerce = col2.checkbox("Commerce", value=perms_user.get('commerce',True), key=f"p2_{row['id']}")
                    p_stock = col3.checkbox("Stock", value=perms_user.get('stock',False), key=f"p3_{row['id']}")
                    p_immo = col4.checkbox("Immobilier", value=perms_user.get('immobilier',False), key=f"p4_{row['id']}")
                    col1, col2, col3, col4 = st.columns(4)
                    p_auto = col1.checkbox("Auto", value=perms_user.get('automobile',False), key=f"p5_{row['id']}")
                    p_parc = col2.checkbox("Parc", value=perms_user.get('parc',False), key=f"p6_{row['id']}")
                    p_compta = col3.checkbox("Compta", value=perms_user.get('comptabilite',False), key=f"p7_{row['id']}")
                    p_fact = col4.checkbox("Factures", value=perms_user.get('factures',False), key=f"p8_{row['id']}")
                    col1, col2 = st.columns(2)
                    p_del = col1.checkbox("🗑️ Peut Supprimer", value=perms_user.get('supprimer',False), key=f"p9_{row['id']}")
                    p_users = col2.checkbox("👥 Gérer Users", value=perms_user.get('users',False), key=f"p10_{row['id']}")

                    st.markdown("**📂 Catégories de Factures Visibles :**")
                    categories_dispo = ["Toutes", "Loyer", "Vente Commerce", "Vente Voiture", "Carburant", "Dépense", "Revenu"]
                    cats_modif = st.multiselect(
                        "Catégories autorisées",
                        categories_dispo,
                        default=cats_user if cats_user else ["Toutes"],
                        key=f"cats_u_{row['id']}"
                    )

                    c1, c2 = st.columns(2)
                    if c1.button("✏️ Modifier", key=f"mod_u_{row['id']}", width="stretch"):
                        try:
                            update_data = {
                                "nom": str(new_nom),
                                "role": str(new_role),
                                "permissions": {
                                    "dashboard": p_dashboard, "commerce": p_commerce, "stock": p_stock,
                                    "immobilier": p_immo, "automobile": p_auto, "parc": p_parc,
                                    "comptabilite": p_compta, "factures": p_fact,
                                    "supprimer": p_del, "users": p_users
                                },
                                "categories_autorisees": cats_modif if "Toutes" not in cats_modif else []
                            }
                            if new_pwd:
                                update_data["password"] = str(new_pwd)
                            supabase.table("utilisateurs").update(update_data).eq("id", int(row['id'])).execute()
                            st.success("Modifié")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur modif")
                            st.code(repr(e))
                    if c2.button("🗑️ Supprimer", key=f"del_u_{row['id']}", width="stretch"):
                        try:
                            supabase.table("utilisateurs").delete().eq("id", int(row['id'])).execute()
                            st.success("Supprimé")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur suppression")
                            st.code(repr(e))
