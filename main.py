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

def generer_pdf_devis_consulting(numero, type_devis, client, titre_projet, parcelle, localisation, details_sections, devise="USD", tel_client="+243...", main_oeuvre=0):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_fill_color(20, 50, 40)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255)
    pdf.set_font("Arial", "B", 20)
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, "ASYMAS CONSULTING", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(10, 16)
    pdf.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
    pdf.set_xy(10, 21)
    pdf.cell(0, 5, "Email: asamnesstsang636@gmail.com", ln=True)
    pdf.set_font("Arial", "B", 10)
    pdf.set_xy(150, 8)
    pdf.cell(50, 6, "DEVIS N", ln=True, align="R")
    pdf.set_font("Arial", "", 10)
    pdf.set_xy(150, 14)
    pdf.cell(50, 6, safe_pdf_txt(numero), ln=True, align="R")
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(150, 20)
    pdf.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")
    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.multi_cell(0, 6, safe_pdf_txt(titre_projet.upper()), align="C")
    pdf.ln(3)
    pdf.set_font("Arial", "B", 10)
    if parcelle:
        pdf.cell(0, 6, f"PARCELLE N° {safe_pdf_txt(parcelle)}", ln=True)
    if localisation:
        pdf.cell(0, 6, f"LOCALISATION: {safe_pdf_txt(localisation)}", ln=True)
    pdf.cell(0, 6, f"CLIENT: {safe_pdf_txt(client)}", ln=True)
    if tel_client:
        pdf.cell(0, 6, f"TEL: {safe_pdf_txt(tel_client)}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(220, 220)
    pdf.cell(10, 7, "N°", 1, 0, 'C', True)
    pdf.cell(90, 7, "DESIGNATION DES OUVRAGES", 1, 0, 'C', True)
    pdf.cell(15, 7, "Unité", 1, 0, 'C', True)
    pdf.cell(20, 7, "Qté", 1, 0, 'C', True)
    pdf.cell(25, 7, "Prix U", 1, 0, 'C', True)
    pdf.cell(30, 7, "Prix total", 1, 1, 'C', True)
    pdf.set_font("Arial", "", 8)
    grand_total = 0
    for section in details_sections:
        pdf.set_font("Arial", "B", 9)
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(10, 6, section['numero'], 1, 0, 'L', True)
        pdf.cell(180, 6, safe_pdf_txt(section['titre']), 1, 1, 'L', True)
        pdf.set_font("Arial", "", 8)
        sous_total = 0
        for item in section['items']:
            qte = item.get('qte', 0)
            pu = item.get('pu', 0)
            total_item = qte * pu
            sous_total += total_item
            pdf.cell(10, 5, item.get('num', ''), 1, 0, 'C')
            pdf.cell(90, 5, safe_pdf_txt(item.get('designation', '')), 1, 0, 'L')
            pdf.cell(15, 5, item.get('unite', ''), 1, 0, 'C')
            pdf.cell(20, 5, f"{qte:,.2f}" if qte else "", 1, 0, 'R')
            pdf.cell(25, 5, f"{pu:,.0f}" if pu else "", 1, 0, 'R')
            pdf.cell(30, 5, f"{total_item:,.0f}" if total_item else "", 1, 1, 'R')
        pdf.set_font("Arial", "B", 8)
        pdf.cell(160, 6, "Sous Total", 1, 0, 'R', True)
        pdf.cell(30, 6, f"{sous_total:,.0f}", 1, 1, 'R', True)
        grand_total += sous_total
    if main_oeuvre > 0:
        pdf.cell(160, 6, "MAIN D'OEUVRE", 1, 0, 'R')
        pdf.cell(30, 6, f"{main_oeuvre:,.0f}", 1, 1, 'R')
        grand_total += main_oeuvre
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(160, 8, f"TOTAL GENERAL ({devise})", 1, 0, 'R', True)
    pdf.cell(30, 8, f"{grand_total:,.0f}", 1, 1, 'R', True)
    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    if type_devis == "Industriel":
        ingenieur = "SAMY TSANGYA"
        tel_ing = "+243 995 105 623"
        adresse_ing = "Beni, Nord-Kivu, RDC"
    else:
        ingenieur = "ESDRAS TSANGYA"
        tel_ing = "+243 972 888 690"
        adresse_ing = "Beni, Nord-Kivu, RDC | Av. du 30 Juin, Q. Malepe | esdrastsangya@gmail.com"
    pdf.cell(0, 8, "SIGNATURE INGENIEUR RESPONSABLE:", ln=True)
    pdf.ln(3)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, pdf.get_y(), 100, pdf.get_y())
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(10, pdf.get_y() + 1)
    pdf.cell(90, 5, f"Ing. {ingenieur}", ln=True)
    pdf.set_xy(10, pdf.get_y())
    pdf.cell(90, 5, f"Tel: {tel_ing}", ln=True)
    pdf.set_xy(10, pdf.get_y())
    pdf.cell(90, 5, f"Adresse: {safe_pdf_txt(adresse_ing)}", ln=True)
    pdf.ln(8)
    pdf.set_font("Arial", "I", 9)
    pdf.set_text_color(0, 102, 0)
    pdf.cell(0, 6, "Devis estimatif - Valable 30 jours", ln=True, align="C")
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
  \"name\": \"ASYMAS BUSINESS\",
  \"short_name\": \"ASYMAS\",
  \"start_url\": \".\",
  \"display\": \"standalone\",
  \"background_color\": \"#000000\",
  \"theme_color\": \"#00ff41\",
  \"description\": \"Agriculture Commerce Immobilier Automobile\",
  \"icons\": [{
    \"src\": \"https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f48e.png\",
    \"sizes\": \"192x192\",
    \"type\": \"image/png\"
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
df_devis = load_table("devis")
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
    st.info("ASYMAS BUSINESS v2.5")
    if st.button("🔄 Actualiser", key="btn_save"):
        st.cache_data.clear()
        st.rerun()

perms = st.session_state.user_perms
if isinstance(perms, str):
    try: perms = json.loads(perms)
    except: perms = {}

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
if st.session_state.user_role == "PDG" or perms.get('devis_industriel', False) or perms.get('devis_batiment', False):
    tabs_dispo.append("📋 Devis")
if st.session_state.user_role == "PDG" or perms.get('users', False):
    tabs_dispo.append("👥 Utilisateurs")

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
        if 'last_qr' not in st.session_state:
            st.session_state.last_qr = ""

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

                if qr_code and qr_code!= st.session_state.last_qr:
                    st.session_state.last_qr = qr_code
                    st.rerun()

                df_articles_filtre = df_articles[df_articles['stock'] > 0].copy()

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
            st.subheader("Scanner QR pour remplir le code")
            qr_scan_ajout = qrcode_scanner(key='qr_add_article')
            if qr_scan_ajout:
                st.success(f"QR scanné : {qr_scan_ajout}")
                st.session_state.qr_code_temp = qr_scan_ajout

            with st.form("form_article", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nom = c1.text_input("Nom Article")
                cat = c2.text_input("Catégorie")
                code_qr = c3.text_input("Code QR", value=st.session_state.get('qr_code_temp', ''), placeholder="Scanne ou tape le code")

                c1, c2, c3 = st.columns(3)
                prix_achat_fc = c1.number_input("Prix Achat FC", min_value=0.0)
                prix_vente_fc = c2.number_input("Prix Vente FC", min_value=0.0)
                prix_vente_usd = c3.number_input("Prix Vente $", min_value=0.0)

                stock = c1.number_input("Stock", min_value=0)

                if st.form_submit_button("💾 Ajouter Article"):
                    try:
                        data_insert = {
                            "nom_article": str(nom),
                            "categorie": str(cat),
                            "prix_achat": float(prix_achat_fc),
                            "prix_vente": float(prix_vente_fc),
                            "stock": int(stock),
                            "code_qr": str(code_qr) if code_qr else None
                        }
                        colonnes_articles = get_table_columns("articles")
                        if "prix_vente_usd" in colonnes_articles:
                            data_insert["prix_vente_usd"] = float(prix_vente_usd)

                        supabase.table("articles").insert(data_insert).execute()
                        st.success(f"Article {nom} ajouté avec QR: {code_qr}")
                        if 'qr_code_temp' in st.session_state:
                            del st.session_state.qr_code_temp
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
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        new_nom = st.text_input("Nom", value=row['nom_article'], key=f"nom_{row['id']}")
                        new_cat = st.text_input("Catégorie", value=row.get('categorie',''), key=f"cat_{row['id']}")
                        new_code_qr = st.text_input("Code QR", value=row.get('code_qr',''), key=f"qr_art_{row['id']}")
                    with c2:
                        new_prix_a = st.number_input("Prix Achat FC", value=float(row.get('prix_achat',0)), key=f"pa_{row['id']}")
                        new_prix_v = st.number_input("Prix Vente FC", value=float(row.get('prix_vente',0)), key=f"pv_{row['id']}")
                        new_prix_usd = st.number_input("Prix Vente $", value=float(row.get('prix_vente_usd',0)), key=f"pusd_{row['id']}")
                    with c3:
                        new_stock = st.number_input("Stock", value=int(row.get('stock',0)), key=f"stock_{row['id']}")

                    c1, c2 = st.columns(2)
                    if c1.button("✏️ Modifier", key=f"mod_art_{row['id']}", width="stretch"):
                        try:
                            data_update = {
                                "nom_article": str(new_nom),
                                "categorie": str(new_cat),
                                "prix_achat": float(new_prix_a),
                                "prix_vente": float(new_prix_v),
                                "stock": int(new_stock),
                                "code_qr": str(new_code_qr) if new_code_qr else None
                            }
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

# === TAB COMPTABILITÉ AVEC FACTURES TELECHARGEABLES ===
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
            total_rev = df_filtre_compta[df_filtre_compta['type']=='Revenu']['montant'].sum()
            total_dep = df_filtre_compta[df_filtre_compta['type']=='Dépense']['montant'].sum()
            solde = total_rev - total_dep
            col_t1.metric("💚 Revenus", f"{total_rev:,.0f} FC")
            col_t2.metric("💸 Dépenses", f"{total_dep:,.0f} FC")
            col_t3.metric("💰 Solde", f"{solde:,.0f} FC", delta=f"{solde:,.0f}")

            if not df_filtre_compta.empty:
                excel_data = generer_excel_pro(df_filtre_compta, "Releve Comptable", total_rev, total_dep, solde)
                st.download_button(label="📥 Télécharger Relevé Excel", data=excel_data, file_name=f"releve_compta_{date_debut}_{date_fin}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")

            st.divider()
            st.subheader("📊 Relevé par Catégorie")

            categories_autorisees = []
            if st.session_state.user_role == "PDG":
                categories_autorisees = df_filtre_compta['categorie'].dropna().unique().tolist()
            else:
                if perms.get('commerce', False): categories_autorisees.append("Vente Commerce")
                if perms.get('immobilier', False): categories_autorisees.append("Loyer")
                if perms.get('automobile', False): categories_autorisees.append("Vente Voiture")

            if 'categorie' in df_filtre_compta.columns:
                categories = [c for c in df_filtre_compta['categorie'].dropna().unique() if c in categories_autorisees or st.session_state.user_role == "PDG"]
                for cat in categories:
                    df_cat = df_filtre_compta[df_filtre_compta['categorie'] == cat]
                    total_cat = df_cat['montant'].sum()
                    with st.expander(f"📁 {cat} - Total: {total_cat:,.0f} FC ({len(df_cat)} opérations)"):
                        for idx, row in df_cat.iterrows():
                            c1, c2, c3, c4 = st.columns([3,2,2,2])
                            c1.write(f"**{row['date']}** | {row.get('description','')}")
                            c2.write(f"{row['montant']:,.0f} {row.get('devise','FC')}")
                            c3.write(f"Par: {row.get('utilisateur','')}")

                            if 'numero_facture' in row and pd.notna(row['numero_facture']):
                                if c4.button("📄 PDF", key=f"pdf_fact_{row['id']}"):
                                    try:
                                        details_list = json.loads(row.get('details', '[]')) if row.get('details') else [{"nom": row.get('description',''), "qte": 1, "pu": row['montant']}]
                                        client_nom = row.get('description','').split(' - ')[1] if ' - ' in row.get('description','') else 'Client'
                                        pdf_bytes = generer_pdf_facture(row['numero_facture'], row.get('categorie','Vente'), client_nom, details_list, row['montant'], row.get('devise','FC'))
                                        st.download_button(label="📥 Télécharger", data=bytes(pdf_bytes), file_name=f"{row['numero_facture']}.pdf", mime="application/pdf", key=f"dl_compta_{row['id']}")
                                        pdf_b64 = base64.b64encode(pdf_bytes).decode()
                                        st.components.v1.html(f"""<button onclick="printPDF()" style="width:100%; padding:5px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:3px; cursor:pointer;">🖨️ Imprimer</button><script>function printPDF() {{const pdfData = 'data:application/pdf;base64,{pdf_b64}'; const win = window.open('', '_blank'); win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>'); win.document.close(); setTimeout(() => {{ win.print(); }}, 1000);}}</script>""", height=35)
                                    except Exception as e:
                                        st.error("Erreur génération PDF")
                            else:
                                c4.write("")
            else:
                st.dataframe(df_filtre_compta, width="stretch", hide_index=True)

# === TAB FACTURES ===
if "📄 Factures" in tab_map:
    with tab_map["📄 Factures"]:
        st.markdown("## 📄 Toutes les Factures")

        df_proforma = load_table("factures_proforma")
        df_compta_factures = df_compta[df_compta['numero_facture'].notna()] if 'numero_facture' in df_compta.columns else pd.DataFrame()

        peut_industriel = st.session_state.user_role == "PDG" or perms.get('devis_industriel', False)
        peut_batiment = st.session_state.user_role == "PDG" or perms.get('devis_batiment', False)

        with st.expander("➕ Créer Facture Proforma Technique"):
            if not peut_industriel and not peut_batiment:
                st.error("🔒 Accès non autorisé - Contacte le PDG")
                st.stop()

            if 'lignes_proforma' not in st.session_state:
                st.session_state.lignes_proforma = [{"nom": "", "qte": 1, "pu": 0.0}]

            types_dispo = []
            if peut_industriel: types_dispo.append("Industriel")
            if peut_batiment: types_dispo.append("Bâtiment & Génie Civil")

            c1, c2, c3 = st.columns(3)
            if len(types_dispo) == 1:
                type_proforma = types_dispo[0]
                c1.info(f"Type autorisé : {type_proforma}")
            else:
                type_proforma = c1.selectbox("Type Proforma", types_dispo, key="type_proforma")

            client_proforma = c2.text_input("Client", key="client_proforma")
            tel_proforma = c3.text_input("Téléphone", value="+243...", key="tel_proforma")

            c1, c2 = st.columns(2)
            devise_proforma = c1.selectbox("Devise", ["$", "€", "FC"], key="devise_proforma")
            date_validite = c2.date_input("Valable jusqu'au", value=date.today() + timedelta(days=30), key="date_validite_proforma")

            titre_projet = st.text_input("Titre du projet", value="FOURNITURE MATÉRIELS", key="titre_projet_proforma")
            localisation = st.text_input("Localisation", value="Beni, Nord-Kivu", key="localisation_proforma")

            st.markdown("### Détails Matériaux / Prestations")

            col_btn1, col_btn2 = st.columns([3,1])
            if col_btn1.button("➕ Ajouter Ligne", key="add_ligne_proforma"):
                st.session_state.lignes_proforma.append({"nom": "", "qte": 1, "pu": 0.0})
                st.rerun()

            total_proforma = 0
            for i, ligne in enumerate(st.session_state.lignes_proforma):
                c1, c2, c3, c4 = st.columns([4,1,2,1])
                ligne['nom'] = c1.text_input(f"Designation {i+1}", value=ligne['nom'], key=f"nom_prof_{i}")
                ligne['qte'] = c2.number_input(f"Qté {i+1}", min_value=1, value=ligne['qte'], key=f"qte_prof_{i}")
                ligne['pu'] = c3.number_input(f"PU {i+1}", min_value=0.0, value=ligne['pu'], key=f"pu_prof_{i}")
                if c4.button("❌", key=f"del_prof_{i}") and len(st.session_state.lignes_proforma) > 1:
                    st.session_state.lignes_proforma.pop(i)
                    st.rerun()
                total_proforma += ligne['qte'] * ligne['pu']

            main_oeuvre_prof = st.number_input("💪 Main d'Oeuvre", min_value=0.0, value=0.0, key="mo_proforma")
            montant_global_prof = total_proforma + main_oeuvre_prof

            st.metric("💰 COUT GLOBAL PROFORMA", f"{montant_global_prof:,.2f} {devise_proforma}")
            st.info(f"Total matériaux: {total_proforma:,.2f} + Main d'oeuvre: {main_oeuvre_prof:,.2f}")

            if st.button("💾 GÉNÉRER PROFORMA TECHNIQUE", type="primary", width="stretch"):
                if not client_proforma:
                    st.error("⚠️ Nom du client obligatoire")
                    st.stop()
                try:
                    numero_proforma = f"PRO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    ingenieur = "SAMY TSANGYA" if type_proforma == "Industriel" else "ESDRAS TSANGYA"
                    tel_ing = "+243 995 105 623" if type_proforma == "Industriel" else "+243 972 888 690"

                    details_sections = [{
                        "numero": "I",
                        "titre": "MATERIAUX / PRESTATIONS",
                        "items": [{"num": f"{i+1}", "designation": l['nom'], "unite": "U", "qte": l['qte'], "pu": l['pu']} for i, l in enumerate(st.session_state.lignes_proforma) if l['nom']]
                    }]

                    supabase.table("factures_proforma").insert({
                        "numero": numero_proforma,
                        "client": client_proforma,
                        "telephone": tel_proforma,
                        "categorie": f"Proforma {type_proforma}",
                        "type_proforma": type_proforma,
                        "titre_projet": titre_projet,
                        "localisation": localisation,
                        "montant": float(montant_global_prof),
                        "main_oeuvre": float(main_oeuvre_prof),
                        "devise": devise_proforma,
                        "date": str(date.today()),
                        "date_validite": str(date_validite),
                        "details": json.dumps(st.session_state.lignes_proforma),
                        "ingenieur": ingenieur,
                        "telephone_ingenieur": tel_ing,
                        "statut": "En attente",
                        "utilisateur": st.session_state.user_name
                    }).execute()

                    pdf_bytes = generer_pdf_devis_consulting(numero_proforma, type_proforma, client_proforma, titre_projet, "", localisation, details_sections, devise_proforma, tel_proforma, main_oeuvre_prof)

                    st.success(f"✅ Proforma {numero_proforma} créée - {type_proforma}")
                    st.download_button(label="📥 TÉLÉCHARGER PROFORMA PDF", data=bytes(pdf_bytes), file_name=f"{numero_proforma}.pdf", mime="application/pdf", width="stretch", type="primary")

                    pdf_b64 = base64.b64encode(pdf_bytes).decode()
                    st.components.v1.html(f"""<button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">🖨️ IMPRIMER PROFORMA</button><script>function printPDF() {{const pdfData = 'data:application/pdf;base64,{pdf_b64}'; const win = window.open('', '_blank'); win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>'); win.document.close(); setTimeout(() => {{ win.print(); }}, 1000);}}</script>""", height=60)

                    st.session_state.lignes_proforma = [{"nom": "", "qte": 1, "pu": 0.0}]
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error("Erreur création proforma")
                    st.code(repr(e))

        st.divider()

        col_f1, col_f2, col_f3 = st.columns(3)
        date_debut_fact = col_f1.date_input("📅 Date début", value=date.today() - timedelta(days=30), key="date_debut_fact")
        date_fin_fact = col_f2.date_input("📅 Date fin", value=date.today(), key="date_fin_fact")
        filtre_nom_fact = col_f3.text_input("👤 Nom Client", placeholder="Tape un nom...", key="filtre_nom_fact")

        st.subheader("📋 Factures Proforma Techniques")

        df_proforma_filtre = df_proforma.copy()
        if 'date' in df_proforma_filtre.columns:
            df_proforma_filtre = df_proforma_filtre[(df_proforma_filtre['date'] >= str(date_debut_fact)) & (df_proforma_filtre['date'] <= str(date_fin_fact))]
        if filtre_nom_fact:
            df_proforma_filtre = df_proforma_filtre[df_proforma_filtre['client'].str.contains(filtre_nom_fact, case=False, na=False)]

        if st.session_state.user_role!= "PDG":
            types_autorises = []
            if peut_industriel: types_autorises.append("Industriel")
            if peut_batiment: types_autorises.append("Bâtiment & Génie Civil")
            if 'type_proforma' in df_proforma_filtre.columns:
                df_proforma_filtre = df_proforma_filtre[df_proforma_filtre['type_proforma'].isin(types_autorises)]

        if df_proforma_filtre.empty:
            st.info("Aucune proforma pour cette période")
        else:
            types_prof = df_proforma_filtre['type_proforma'].dropna().unique() if 'type_proforma' in df_proforma_filtre.columns else ['Proforma']
            for type_p in types_prof:
                df_type = df_proforma_filtre[df_proforma_filtre['type_proforma'] == type_p] if 'type_proforma' in df_proforma_filtre.columns else df_proforma_filtre
                total_type = df_type['montant'].sum()

                with st.expander(f"📁 Proforma {type_p} - Total: {total_type:,.2f} ({len(df_type)} proforma)"):
                    for idx, row in df_type.iterrows():
                        col_info, col_btn1, col_btn2, col_btn3 = st.columns([3,1,1,1])
                        col_info.markdown(f"**{row['numero']}** | {row.get('date','')} | {row['client']} | **{row.get('montant',0):,.0f} {row.get('devise','$')}** | Ing: {row.get('ingenieur','')}")

                        if col_btn1.button("👁️ Voir", key=f"voir_prof_{row['id']}", width="stretch"):
                            st.json(json.loads(row.get('details','[]')))

                        if col_btn2.button("📥 PDF", key=f"dl_prof_{row['id']}", width="stretch"):
                            details = json.loads(row.get('details', '[]'))
                            details_sections = [{
                                "numero": "I",
                                "titre": "MATERIAUX / PRESTATIONS",
                                "items": [{"num": f"{i+1}", "designation": d['nom'], "unite": "U", "qte": d['qte'], "pu": d['pu']} for i, d in enumerate(details)]
                            }]
                            pdf_bytes = generer_pdf_devis_consulting(
                                row['numero'], row.get('type_proforma','Industriel'), row['client'],
                                row.get('titre_projet','PROJET'), "", row.get('localisation',''), details_sections,
                                row.get('devise','$'), row.get('telephone',''), row.get('main_oeuvre',0)
                            )
                            st.download_button(label="💾 Télécharger", data=bytes(pdf_bytes), file_name=f"{row['numero']}.pdf", mime="application/pdf", key=f"dl_btn_prof_{row['id']}")

                        if st.session_state.user_role == "PDG":
                            if col_btn3.button("🗑️", key=f"del_prof_{row['id']}", width="stretch"):
                                supabase.table("factures_proforma").delete().eq("id", int(row['id'])).execute()
                                st.success("Proforma supprimée")
                                st.cache_data.clear()
                                st.rerun()

        st.divider()

        st.subheader("📋 Factures Automatiques - Triées par Catégorie")

        if st.session_state.user_role!= "PDG":
            categories_autorisees = []
            if perms.get('commerce', False): categories_autorisees.append("Vente Commerce")
            if perms.get('immobilier', False): categories_autorisees.append("Loyer")
            if perms.get('automobile', False): categories_autorisees.append("Vente Voiture")
            df_compta_factures = df_compta_factures[df_compta_factures['categorie'].isin(categories_autorisees)]

        df_compta_factures = df_compta_factures[(df_compta_factures['date'] >= str(date_debut_fact)) & (df_compta_factures['date'] <= str(date_fin_fact))]
        if filtre_nom_fact:
            df_compta_factures = df_compta_factures[df_compta_factures['description'].str.contains(filtre_nom_fact, case=False, na=False)]

        if df_compta_factures.empty:
            st.info("Aucune facture auto pour cette période")
        else:
            categories = df_compta_factures['categorie'].dropna().unique()
            for cat in categories:
                df_cat = df_compta_factures[df_compta_factures['categorie'] == cat]
                total_cat = df_cat['montant'].sum()

                with st.expander(f"📁 {cat} - Total: {total_cat:,.0f} FC ({len(df_cat)} factures)"):
                    for idx, row in df_cat.iterrows():
                        col_info, col_btn1, col_btn2 = st.columns([4,1,1])
                        client_nom = row.get('description','').split(' - ')[1] if ' - ' in row.get('description','') else 'Client'
                        col_info.markdown(f"**{row['numero_facture']}** | {row['date']} | {client_nom} | **{row['montant']:,.0f} {row.get('devise','FC')}**")

                        if col_btn1.button("📥 PDF", key=f"dl_fact_auto_{row['id']}", width="stretch"):
                            try:
                                details_list = json.loads(row.get('details', '[]')) if row.get('details') else [{"nom": row.get('description',''), "qte": 1, "pu": row['montant']}]
                                pdf_bytes = generer_pdf_facture(row['numero_facture'], row.get('categorie','Vente'), client_nom, details_list, row['montant'], row.get('devise','FC'))
                                st.download_button(label="💾 Télécharger", data=bytes(pdf_bytes), file_name=f"{row['numero_facture']}.pdf", mime="application/pdf", key=f"dl_btn_fact_auto_{row['id']}")
                            except:
                                st.error("Erreur PDF")

                        if col_btn2.button("🖨️ Imprimer", key=f"print_fact_auto_{row['id']}", width="stretch"):
                            try:
                                details_list = json.loads(row.get('details', '[]')) if row.get('details') else [{"nom": row.get('description',''), "qte": 1, "pu": row['montant']}]
                                pdf_bytes = generer_pdf_facture(row['numero_facture'], row.get('categorie','Vente'), client_nom, details_list, row['montant'], row.get('devise','FC'))
                                pdf_b64 = base64.b64encode(pdf_bytes).decode()
                                st.components.v1.html(f"""<script>const pdfData = 'data:application/pdf;base64,{pdf_b64}'; const win = window.open('', '_blank'); win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>'); win.document.close(); setTimeout(() => {{ win.print(); }}, 1000);</script>""", height=0)
                                st.success("Impression lancée")
                            except:
                                st.error("Erreur impression")

# === TAB DEVIS ===
if "📋 Devis" in tab_map:
    with tab_map["📋 Devis"]:
        st.markdown("## 📋 Devis International - ASYMAS CONSULTING")

        peut_industriel = st.session_state.user_role == "PDG" or perms.get('devis_industriel', False)
        peut_batiment = st.session_state.user_role == "PDG" or perms.get('devis_batiment', False)

        if not peut_industriel and not peut_batiment:
            st.error("🔒 Accès non autorisé - Contacte le PDG")
            st.stop()

        # FORCE L'AFFICHAGE DES 2 TABS SI TU ES PDG
        if st.session_state.user_role == "PDG":
            tab1, tab2 = st.tabs(["🧱 Modèle Clôture 23.5m - Bâtiment", "📝 Devis Vide - Industriel/Bâtiment"])
        else:
            tab_names = []
            if peut_batiment:
                tab_names.append("🧱 Modèle Clôture 23.5m")
            if peut_industriel:
                tab_names.append("📝 Devis Vide")
            if not tab_names:
                st.error("Aucune permission devis")
                st.stop()
            tabs_devis = st.tabs(tab_names)
            tab1 = tabs_devis[0] if peut_batiment else None
            tab2 = tabs_devis[-1]

        # Tab Clôture Bâtiment
        if peut_batiment or st.session_state.user_role == "PDG":
            with tab1:
                st.markdown("### DEVIS DE MATERIAUX POUR LA CONSTRUCTION DE CLOTURE")

                if 'titre_cloture' not in st.session_state:
                    st.session_state.titre_cloture = "DEVIS DE MATERIAUX POUR LA CONSTRUCTION DE CLOTURE DE 23.5m"

                st.session_state.titre_cloture = st.text_input(
                    "Titre du devis éditable",
                    value=st.session_state.titre_cloture,
                    key="titre_cloture_input"
                )

                if 'lignes_cloture' not in st.session_state:
                    st.session_state.lignes_cloture = [
                        {"section": "I", "no": "", "designation": "Installation chantier", "unite": "ff", "qte": 1, "pu": 200},
                        {"section": "I", "no": "", "designation": "Demolitions", "unite": "ff", "qte": 1, "pu": 70},
                        {"section": "II", "no": "1", "designation": "moellon", "unite": "Canters", "qte": 9, "pu": 50},
                        {"section": "II", "no": "2", "designation": "sable", "unite": "Canters", "qte": 4, "pu": 40},
                        {"section": "II", "no": "3", "designation": "ciment", "unite": "sac", "qte": 23, "pu": 13.5},
                        {"section": "II", "no": "4", "designation": "gravier", "unite": "Canters", "qte": 3, "pu": 80},
                        {"section": "II", "no": "5", "designation": "armature de 10", "unite": "pièce", "qte": 9, "pu": 9},
                        {"section": "II", "no": "6", "designation": "armature de 8", "unite": "pièce", "qte": 4, "pu": 8},
                        {"section": "II", "no": "7", "designation": "armature de 6", "unite": "pièce", "qte": 12, "pu": 3.5},
                        {"section": "II", "no": "8", "designation": "Fil à ligature", "unite": "kg", "qte": 16, "pu": 2.5},
                        {"section": "III", "no": "1", "designation": "bloc ciment", "unite": "pièce", "qte": 987, "pu": 1},
                        {"section": "III", "no": "2", "designation": "sable", "unite": "Canters", "qte": 5, "pu": 40},
                        {"section": "III", "no": "3", "designation": "ciment", "unite": "sac", "qte": 15, "pu": 13.5},
                        {"section": "III", "no": "4", "designation": "gravier", "unite": "Canters", "qte": 0.5, "pu": 70},
                        {"section": "III", "no": "5", "designation": "Barre Corniche de6", "unite": "pièce", "qte": 8, "pu": 3},
                        {"section": "III", "no": "6", "designation": "Fil à ligature", "unite": "kg", "qte": 6, "pu": 2},
                        {"section": "IV", "no": "1", "designation": "socle et longrine", "unite": "pièce", "qte": 8, "pu": 7},
                        {"section": "IV", "no": "2", "designation": "Colonne", "unite": "pièce", "qte": 18, "pu": 7},
                        {"section": "IV", "no": "3", "designation": "Corniche", "unite": "pièce", "qte": 6, "pu": 7},
                        {"section": "IV", "no": "4", "designation": "clous de8", "unite": "kg", "qte": 15, "pu": 2},
                        {"section": "IV", "no": "5", "designation": "clous de10", "unite": "kg", "qte": 10, "pu": 2},
                        {"section": "V", "no": "1", "designation": "ciment", "unite": "sac", "qte": 20, "pu": 13.5},
                        {"section": "V", "no": "2", "designation": "sable", "unite": "Canters", "qte": 7, "pu": 40},
                    ]

                c1, c2 = st.columns(2)
                client_cloture = c1.text_input("Client", key="client_cloture")
                tel_cloture = c2.text_input("Téléphone", value="+243...", key="tel_cloture")
                localisation_cloture = st.text_input("Localisation", value="Beni, Nord-Kivu", key="loc_cloture")
                parcelle_cloture = st.text_input("N° Parcelle", key="parc_cloture")

                st.markdown("#### Sections : I.Installation | II.Fondation | III.Élévation | IV.Coffrage | V.Finissage")

                if st.button("➕ Ajouter Ligne Matériau", key="add_ligne_cloture"):
                    st.session_state.lignes_cloture.append({"section": "V", "no": "", "designation": "", "unite": "pièce", "qte": 1, "pu": 0})
                    st.rerun()

                total_mat = 0
                sections = {"I": "Installation chantier", "II": "Fondation", "III": "Élévation de mur et corniche", "IV": "Coffrage Colonne, Corniche et Socle", "V": "Finissage"}

                for section_code, section_nom in sections.items():
                    st.markdown(f"**{section_code}. {section_nom}**")
                    lignes_section = [l for l in st.session_state.lignes_cloture if l['section'] == section_code]
                    sous_total = 0

                    for i, ligne in enumerate(lignes_section):
                        idx_global = st.session_state.lignes_cloture.index(ligne)
                        c1, c2, c3, c4, c5, c6 = st.columns([1, 6, 2, 2, 2, 1])
                        ligne['no'] = c1.text_input("No", value=ligne['no'], key=f"no_clot_{idx_global}", label_visibility="collapsed")
                        ligne['designation'] = c2.text_input("Désignation", value=ligne['designation'], key=f"des_clot_{idx_global}", label_visibility="collapsed")
                        ligne['unite'] = c3.text_input("Unité", value=ligne['unite'], key=f"unit_clot_{idx_global}", label_visibility="collapsed")
                        ligne['qte'] = c4.number_input("Qté", value=float(ligne['qte']), key=f"qte_clot_{idx_global}", label_visibility="collapsed")
                        ligne['pu'] = c5.number_input("PU", value=float(ligne['pu']), key=f"pu_clot_{idx_global}", label_visibility="collapsed")
                        if c6.button("❌", key=f"del_clot_{idx_global}"):
                            st.session_state.lignes_cloture.pop(idx_global)
                            st.rerun()

                        pt = ligne['qte'] * ligne['pu']
                        sous_total += pt
                        total_mat += pt

                    st.caption(f"Sous-total {section_nom}: {sous_total:,.2f} USD")
                    st.divider()

                main_oeuvre_cloture = st.number_input("💪 Main d'œuvre USD", min_value=0.0, value=1173.0, key="mo_cloture")
                cout_total = total_mat + main_oeuvre_cloture

                col_t1, col_t2, col_t3 = st.columns(3)
                col_t1.metric("TOTAL MATERIAUX", f"{total_mat:,.2f} $")
                col_t2.metric("MAIN D'OEUVRE", f"{main_oeuvre_cloture:,.2f} $")
                col_t3.metric("COUT TOTAL PROJET", f"{cout_total:,.2f} $")

                if st.button("💾 GÉNÉRER DEVIS CLÔTURE PDF", type="primary", width="stretch"):
                    if not client_cloture:
                        st.error("⚠️ Nom du client obligatoire")
                        st.stop()
                    try:
                        numero = f"DEV-CLOT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                        details_sections = []
                        for section_code, section_nom in sections.items():
                            items = []
                            for l in st.session_state.lignes_cloture:
                                if l['section'] == section_code and l['designation']:
                                    items.append({"num": l['no'], "designation": l['designation'], "unite": l['unite'], "qte": l['qte'], "pu": l['pu']})
                            if items:
                                details_sections.append({"numero": section_code, "titre": section_nom, "items": items})

                        supabase.table("devis").insert({
                            "numero": numero,
                            "client": client_cloture,
                            "telephone": tel_cloture,
                            "type_devis": "Bâtiment & Génie Civil",
                            "description_longue": st.session_state.titre_cloture + f"\nLocalisation: {localisation_cloture}\nParcelle: {parcelle_cloture}",
                            "montant_global": float(cout_total),
                            "main_oeuvre": float(main_oeuvre_cloture),
                            "devise": "$",
                            "ingenieur": "ESDRAS TSANGYA",
                            "telephone_ingenieur": "+243 972 888 690",
                            "details": json.dumps(st.session_state.lignes_cloture),
                            "utilisateur": st.session_state.user_name,
                            "statut": "Validé",
                            "date": str(date.today())
                        }).execute()

                        pdf_bytes = generer_pdf_devis_consulting(
                            numero, "Bâtiment & Génie Civil", client_cloture,
                            st.session_state.titre_cloture, parcelle_cloture, localisation_cloture,
                            details_sections, "$", tel_cloture, main_oeuvre_cloture
                        )

                        st.success(f"✅ Devis {numero} généré - Ing. ESDRAS TSANGYA")
                        st.download_button(
                            label="📥 TÉLÉCHARGER LE PDF",
                            data=bytes(pdf_bytes),
                            file_name=f"{numero}.pdf",
                            mime="application/pdf",
                            width="stretch",
                            type="primary"
                        )

                        pdf_b64 = base64.b64encode(pdf_bytes).decode()
                        st.components.v1.html(f"""
                            <button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">
                                🖨️ IMPRIMER LE DEVIS
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
                    except Exception as e:
                        st.error("Erreur génération devis")
                        st.code(repr(e))

        # Tab Devis Vide - Industriel/Bâtiment
        with tab2:
            st.markdown("### 📝 Devis Vide - Choisis le type")
            #... ton code Devis Vide existant ici...
if "👥 Utilisateurs" in tab_map:
    with tab_map["👥 Utilisateurs"]:
        st.markdown("## 👥 Gestion des Utilisateurs")
        with st.expander("➕ Ajouter Utilisateur"):
            with st.form("form_user", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nom_user = c1.text_input("Nom")
                role_user = c2.selectbox("Rôle", ["PDG", "GERANTE", "UTILISATEUR", "COMMERCANT"])
                pwd_user = c3.text_input("Mot de passe", type="password")

                st.markdown("**Permissions :**")
                col1, col2, col3, col4 = st.columns(4)
                perms_dict = {}
                perms_dict['dashboard'] = col1.checkbox("Dashboard", value=True)
                perms_dict['commerce'] = col2.checkbox("Commerce", value=True)
                perms_dict['stock'] = col3.checkbox("Stock")
                perms_dict['immobilier'] = col4.checkbox("Immobilier")
                perms_dict['automobile'] = col1.checkbox("Automobile")
                perms_dict['parc'] = col2.checkbox("Parc Auto")
                perms_dict['comptabilite'] = col3.checkbox("Comptabilité")
                perms_dict['factures'] = col4.checkbox("Factures")
                perms_dict['devis_industriel'] = col1.checkbox("Devis Industriel")
                perms_dict['devis_batiment'] = col2.checkbox("Devis Bâtiment")
                perms_dict['users'] = col3.checkbox("Gestion Users")
                perms_dict['supprimer'] = col4.checkbox("Supprimer données")

                if st.form_submit_button("💾 Ajouter Utilisateur"):
                    try:
                        supabase.table("utilisateurs").insert({
                            "nom": nom_user,
                            "role": role_user,
                            "password": pwd_user,
                            "permissions": perms_dict,
                            "categories_autorisees": []
                        }).execute()
                        st.success(f"Utilisateur {nom_user} ajouté")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout utilisateur")
                        st.code(repr(e))

        st.divider()
        st.subheader("📋 Liste des Utilisateurs")
        if df_utilisateurs.empty:
            st.info("Aucun utilisateur")
        else:
            for _, row in df_utilisateurs.iterrows():
                with st.expander(f"{row['nom']} - {row['role']}"):
                    st.json(row.get('permissions', {}))
                    if st.session_state.user_role == "PDG" and row['nom']!= st.session_state.user_name:
                        if st.button("🗑️ Supprimer", key=f"del_user_{row['id']}"):
                            supabase.table("utilisateurs").delete().eq("id", int(row['id'])).execute()
                            st.success("Utilisateur supprimé")
                            st.cache_data.clear()
                            st.rerun()
                            
