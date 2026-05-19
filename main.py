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

def generer_pdf_facture(numero, type_op, client, details_list, montant, devise, tel_client="+243...", periode="", type_facture="Simple"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False, margin=10)
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
    titre_fact = "FACTURE N" if type_facture == "Simple" else "PROFORMA N"
    pdf.cell(50, 6, titre_fact, ln=True, align="R")
    pdf.set_font("Arial", "", 10)
    pdf.set_xy(150, 14)
    pdf.cell(50, 6, safe_pdf_txt(numero), ln=True, align="R")
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(150, 20)
    pdf.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")
    y_pos = 45
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.set_xy(10, y_pos)
    pdf.cell(0, 10, f"{type_facture.upper()} {safe_pdf_txt(type_op.upper())}", ln=True, fill=True)
    y_pos += 15
    pdf.set_font("Arial", "B", 10)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_xy(10, y_pos)
    pdf.cell(85, 7, "FACTURE A:", 1, 0, 'L')
    pdf.cell(10, 7, "", 0, 0)
    pdf.cell(85, 7, "DETAILS PAIEMENT:", 1, 1, 'L')
    y_pos += 7
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(10, y_pos)
    pdf.cell(85, 6, f"Client: {safe_pdf_txt(client)}", 'LR', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(85, 6, "M-Pesa: +243817264448", 'LR', 1, 'L')
    y_pos += 6
    pdf.set_xy(10, y_pos)
    pdf.cell(85, 6, f"Tel: {safe_pdf_txt(tel_client)}", 'LR', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(85, 6, "Echeance: Immediate", 'LR', 1, 'L')
    y_pos += 6
    pdf.set_xy(10, y_pos)
    pdf.cell(85, 6, f"Date emission: {date.today().strftime('%d/%m/%Y')}", 'LRB', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(85, 6, "", 'LRB', 1, 'L')
    y_pos += 14
    pdf.set_fill_color(0, 102, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.set_xy(10, y_pos)
    pdf.cell(115, 8, "DESIGNATION", 1, 0, 'C', True)
    pdf.cell(25, 8, "QTE", 1, 0, 'C', True)
    pdf.cell(40, 8, f"MONTANT ({safe_pdf_txt(devise)})", 1, 1, 'C', True)
    y_pos += 8
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)
    if isinstance(details_list, list) and details_list:
        for item in details_list:
            if y_pos > 240:
                pdf.add_page()
                y_pos = 30
            nom = safe_pdf_txt(item.get('nom', ''))
            qte = item.get('qte', 1)
            pu = item.get('pu', item.get('prix', 0))
            montant_item = pu * qte
            pdf.set_xy(10, y_pos)
            pdf.cell(115, 7, nom, 1, 0, 'L')
            pdf.cell(25, 7, str(qte), 1, 0, 'C')
            pdf.cell(40, 7, f"{montant_item:,.0f}", 1, 1, 'R')
            y_pos += 7
    else:
        pdf.set_xy(10, y_pos)
        pdf.cell(115, 7, safe_pdf_txt(details_list), 1, 0, 'L')
        pdf.cell(25, 7, "1", 1, 0, 'C')
        pdf.cell(40, 7, f"{montant:,.0f}", 1, 1, 'R')
        y_pos += 7
    if periode:
        if y_pos > 240:
            pdf.add_page()
            y_pos = 30
        pdf.set_xy(10, y_pos)
        pdf.cell(115, 7, f"Periode: {safe_pdf_txt(periode)}", 1, 0, 'L')
        pdf.cell(25, 7, "", 1, 0, 'C')
        pdf.cell(40, 7, "", 1, 1, 'R')
        y_pos += 7
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 11)
    pdf.set_xy(10, y_pos)
    pdf.cell(140, 10, "MONTANT TOTAL A PAYER", 1, 0, 'R', True)
    pdf.cell(40, 10, f"{montant:,.0f} {safe_pdf_txt(devise)}", 1, 1, 'R', True)
    y_pos += 15
    if y_pos > 220:
        pdf.add_page()
        y_pos = 30
    pdf.set_xy(10, y_pos)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, "SIGNATURE RESPONSABLE:", ln=True)
    y_pos += 11
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, y_pos, 100, y_pos)
    y_pos += 1
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(10, y_pos)
    pdf.cell(90, 5, "Ing. SAMY TSANGYA", ln=True)
    y_pos += 5
    pdf.set_xy(10, y_pos)
    pdf.cell(90, 5, "Tel: +243 995 105 623", ln=True)
    y_pos += 5
    pdf.set_xy(10, y_pos)
    pdf.cell(90, 5, "Beni, Nord-Kivu, RDC", ln=True)
    y_pos += 10
    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(0, 102, 0)
    pdf.set_xy(10, y_pos)
    pdf.cell(0, 6, "Merci pour votre confiance! ASYMAS BUSINESS - Votre partenaire de croissance", ln=True, align="C")
    qr_data = f"""ASYMAS BUSINESS
Facture: {numero}
Type: {type_op}
Client: {client}
Montant: {montant:,.0f} {devise}
Date: {date.today().strftime('%d/%m/%Y')}
Tel: +243 995 105 623"""
    qr_path = generer_qrcode(qr_data)
    pdf.image(qr_path, x=155, y=y_pos-25, w=25)
    os.unlink(qr_path)
    return bytes(pdf.output(dest='S'))

def generer_pdf_devis_consulting(numero, type_devis, client, titre_projet, parcelle, localisation, details_sections, devise="USD", tel_client="+243...", main_oeuvre=0):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False, margin=10)
    pdf.set_fill_color(20, 50, 40)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255)
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
    y_pos = 45
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.set_xy(10, y_pos)
    pdf.multi_cell(0, 6, safe_pdf_txt(titre_projet.upper()), align="C")
    y_pos = pdf.get_y() + 3
    pdf.set_font("Arial", "B", 10)
    pdf.set_xy(10, y_pos)
    if parcelle:
        pdf.cell(0, 6, f"PARCELLE N {safe_pdf_txt(parcelle)}", ln=True)
        y_pos += 6
    pdf.set_xy(10, y_pos)
    if localisation:
        pdf.cell(0, 6, f"LOCALISATION: {safe_pdf_txt(localisation)}", ln=True)
        y_pos += 6
    pdf.set_xy(10, y_pos)
    pdf.cell(0, 6, f"CLIENT: {safe_pdf_txt(client)}", ln=True)
    y_pos += 6
    if tel_client:
        pdf.set_xy(10, y_pos)
        pdf.cell(0, 6, f"TEL: {safe_pdf_txt(tel_client)}", ln=True)
        y_pos += 6
    y_pos += 5
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(220, 220, 220)
    pdf.set_xy(10, y_pos)
    pdf.cell(10, 7, "N", 1, 0, 'C', True)
    pdf.cell(90, 7, "DESIGNATION DES OUVRAGES", 1, 0, 'C', True)
    pdf.cell(15, 7, "Unité", 1, 0, 'C', True)
    pdf.cell(20, 7, "Qté", 1, 0, 'C', True)
    pdf.cell(25, 7, "Prix U", 1, 0, 'C', True)
    pdf.cell(30, 7, "Prix total", 1, 1, 'C', True)
    y_pos += 7
    pdf.set_font("Arial", "", 8)
    grand_total = 0
    for section in details_sections:
        if y_pos > 240:
            pdf.add_page()
            y_pos = 30
        pdf.set_font("Arial", "B", 9)
        pdf.set_fill_color(200, 200, 200)
        pdf.set_xy(10, y_pos)
        pdf.cell(10, 6, section['numero'], 1, 0, 'L', True)
        pdf.cell(180, 6, safe_pdf_txt(section['titre']), 1, 1, 'L', True)
        y_pos += 6
        pdf.set_font("Arial", "", 8)
        sous_total = 0
        for item in section['items']:
            if y_pos > 250:
                pdf.add_page()
                y_pos = 30
            qte = item.get('qte', 0)
            pu = item.get('pu', 0)
            total_item = qte * pu
            sous_total += total_item
            pdf.set_xy(10, y_pos)
            pdf.cell(10, 5, item.get('num', ''), 1, 0, 'C')
            pdf.cell(90, 5, safe_pdf_txt(item.get('designation', '')), 1, 0, 'L')
            pdf.cell(15, 5, item.get('unite', ''), 1, 0, 'C')
            pdf.cell(20, 5, f"{qte:,.2f}" if qte else "", 1, 0, 'R')
            pdf.cell(25, 5, f"{pu:,.0f}" if pu else "", 1, 0, 'R')
            pdf.cell(30, 5, f"{total_item:,.0f}" if total_item else "", 1, 1, 'R')
            y_pos += 5
        pdf.set_font("Arial", "B", 8)
        pdf.set_xy(10, y_pos)
        pdf.cell(160, 6, "Sous Total", 1, 0, 'R', True)
        pdf.cell(30, 6, f"{sous_total:,.0f}", 1, 1, 'R', True)
        y_pos += 6
        grand_total += sous_total
    if main_oeuvre > 0:
        if y_pos > 250:
            pdf.add_page()
            y_pos = 30
        pdf.set_xy(10, y_pos)
        pdf.cell(160, 6, "MAIN D'OEUVRE", 1, 0, 'R')
        pdf.cell(30, 6, f"{main_oeuvre:,.0f}", 1, 1, 'R')
        y_pos += 6
        grand_total += main_oeuvre
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 10)
    pdf.set_xy(10, y_pos)
    pdf.cell(160, 8, f"TOTAL GENERAL ({devise})", 1, 0, 'R', True)
    pdf.cell(30, 8, f"{grand_total:,.0f}", 1, 1, 'R', True)
    y_pos += 15
    if y_pos > 220:
        pdf.add_page()
        y_pos = 30
    pdf.set_xy(10, y_pos)
    pdf.set_font("Arial", "B", 10)
    if type_devis == "Industriel":
        ingenieur = "SAMY TSANGYA"
        tel_ing = "+243 995 105 623"
        adresse_ing = "Beni, Nord-Kivu, RDC"
    else:
        ingenieur = "ESDRAS TSANGYA"
        tel_ing = "+243 972 888 690"
        adresse_ing = "Beni, Nord-Kivu, RDC | esdrastsangya@gmail.com"
    pdf.cell(0, 8, "SIGNATURE INGENIEUR RESPONSABLE:", ln=True)
    y_pos += 11
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, y_pos, 100, y_pos)
    y_pos += 1
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(10, y_pos)
    pdf.cell(90, 5, f"Ing. {ingenieur}", ln=True)
    y_pos += 5
    pdf.set_xy(10, y_pos)
    pdf.cell(90, 5, f"Tel: {tel_ing}", ln=True)
    y_pos += 5
    pdf.set_xy(10, y_pos)
    pdf.cell(90, 5, f"Adresse: {safe_pdf_txt(adresse_ing)}", ln=True)
    y_pos += 8
    pdf.set_font("Arial", "I", 9)
    pdf.set_text_color(0, 102, 0)
    pdf.set_xy(10, y_pos)
    pdf.cell(0, 6, "Devis estimatif - Valable 30 jours", ln=True, align="C")
    return bytes(pdf.output(dest='S'))

def creer_facture_auto(type_op, client, details, montant, devise="FC", details_list=None, tel="+243...", periode="", type_facture="Simple"):
    numero_facture = f"AS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if details_list is None:
        details_list = [{"nom": details, "qte": 1, "pu": montant}]
    pdf_bytes = generer_pdf_facture(numero_facture, type_op, client, details_list, montant, devise, tel, periode, type_facture)
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
                df_users_login = supabase.table("utilisateurs").select("id, nom, role, password").execute().data
                df_users_login = pd.DataFrame(df_users_login)
                st.write(df_users_login) # supprime ça après
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
if 'date' in df_compta.columns:
    df_compta['date'] = pd.to_datetime(df_compta['date'], errors='coerce')
    df_compta = df_compta.sort_values('date', ascending=False)

st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
st.markdown("### Agriculture • Commerce • Immobilier • Automobile • Beni RDC")

with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.user_name}")
    st.markdown(f"**Rôle : {st.session_state.user_role}**")
    st.info("ASYMAS BUSINESS v2.6")
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
                                num_fact, "Vente Commerce", st.session_state.client_com_nom,
                                details_list, total_panier, "FC", st.session_state.client_com_tel
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
                    motif_perte = st.selectbox("Motif", ["Casse", "Vol", "Péremption", "Défaut fabrication", "Accident", "Autre"])
                    detail_perte = st.text_area("Détails", placeholder="Ex: Carton mouillé lors livraison")
                    responsable = st.text_input("Déclaré par", value=st.session_state.user_name)
                
                if article_choisi:
                    article_data = article_dict[article_choisi]
                    valeur_perte = qte_perte * float(article_data.get('prix_achat', 0))
                    st.error(f"💸 Valeur de la perte : {valeur_perte:,.0f} FC")
                
                if st.button("🚨 ENREGISTRER LA PERTE", type="primary", width="stretch"):
                    if article_choisi and qte_perte > 0:
                        article_data = article_dict[article_choisi]
                        try:
                            # 1. Déduire du stock
                            nouveau_stock = int(article_data['stock']) - qte_perte
                            supabase.table('articles').update({"stock": nouveau_stock}).eq("id", int(article_data['id'])).execute()
                            
                            # 2. Enregistrer mouvement
                            supabase.table('mouvements_stock').insert({
                                "article_id": int(article_data['id']),
                                "article_nom": str(article_data['nom_article']),
                                "type": "PERTE",
                                "quantite": -int(qte_perte),
                                "motif": f"{motif_perte} - {detail_perte}",
                                "valeur": float(valeur_perte),
                                "created_by": responsable,
                                "created_at": datetime.now().isoformat()
                            }).execute()
                            
                            st.success(f"✅ Perte enregistrée. Nouveau stock {article_data['nom_article']}: {nouveau_stock}")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur enregistrement perte")
                            st.code(repr(e))
            
            st.divider()
            st.subheader("📋 Historique Pertes Commerce")
            try:
                pertes = supabase.table('mouvements_stock').select("*").eq("type", "PERTE").order("created_at", desc=True).limit(20).execute().data
            except:
                pertes = []
            
            if not pertes:
                st.info("Aucune perte enregistrée")
            else:
                total_pertes = sum(p.get('valeur', 0) for p in pertes)
                st.metric("💸 TOTAL PERTES COMMERCE", f"{total_pertes:,.0f} FC")
                
                for p in pertes:
                    with st.expander(f"🔴 {p.get('article_nom')} - {abs(p.get('quantite',0))} - {p.get('created_at','')[:10]}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Qté perdue:** {abs(p.get('quantite', 0))}")
                            st.write(f"**Valeur:** {p.get('valeur', 0):,.0f} FC")
                        with col2:
                            st.write(f"**Motif:** {p.get('motif', 'N/A')}")
                            st.write(f"**Par:** {p.get('created_by', 'N/A')}")
                        with col3:
                            if st.session_state.user_role == "PDG":
                                if st.button("🗑️ Supprimer", key=f"del_perte_com_{p.get('id')}"):
                                    supabase.table('mouvements_stock').delete().eq("id", p.get('id')).execute()
                                    st.rerun()
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
                num_fact, pdf_bytes = creer_facture_auto("Loyer", nom_client, details_text, total_mensuel, "$", details_list, tel_client, periode, "Proforma")
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
                                num_fact, pdf_bytes = creer_facture_auto("Vente Voiture", st.session_state.client_auto_nom, details_text, total_voiture, "$", details_list, st.session_state.client_auto_tel, "", "Proforma")
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
        st.markdown("## 🚘 Gestion Parc Automobile & Pertes")
        
        tab_ajout_v, tab_liste_v, tab_pertes_v = st.tabs(["➕ Ajouter Voiture", "📋 Liste Voitures", "⚠️ Pertes/Dégâts Voitures"])
        
        colonnes_voitures = get_table_columns("voitures")
        
        with tab_ajout_v:
            st.subheader("➕ Ajouter Nouvelle Voiture au Parc")
            with st.form("form_voiture_parc", clear_on_submit=True):
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
                    prix = c3.number_input("Prix Achat $", min_value=0.0, value=0.0)
                    data_insert["prix"] = float(prix)
                if "statut" in colonnes_voitures:
                    statut = c1.selectbox("Statut", ["Disponible", "En réparation", "Réservée", "Vendue"])
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
                        st.success(f"Voiture {marque} {modele} ajoutée")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout")
                        st.code(repr(e))

        with tab_liste_v:
            st.subheader("📋 Liste des Voitures - Modifier/Supprimer")
            if df_voitures.empty:
                st.info("Aucune voiture")
            else:
                for _, row in df_voitures.iterrows():
                    with st.expander(f"{row['marque']} {row['modele']} - {row.get('plaque','')} - Stock:{row.get('quantite',0)} - {row.get('statut','')}"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            new_marque = st.text_input("Marque", value=row['marque'], key=f"marque_v_{row['id']}")
                            new_modele = st.text_input("Modèle", value=row['modele'], key=f"modele_v_{row['id']}")
                            new_annee = st.text_input("Année", value=row.get('annee',''), key=f"annee_v_{row['id']}")
                        data_update = {"marque": str(new_marque), "modele": str(new_modele), "annee": str(new_annee)}
                        with c2:
                            if "plaque" in colonnes_voitures:
                                new_plaque = st.text_input("Plaque", value=row.get('plaque',''), key=f"plaque_v_{row['id']}")
                                data_update["plaque"] = str(new_plaque)
                            if "couleur" in colonnes_voitures:
                                new_couleur = st.text_input("Couleur", value=row.get('couleur',''), key=f"couleur_v_{row['id']}")
                                data_update["couleur"] = str(new_couleur)
                            if "kilometrage" in colonnes_voitures:
                                km_val = row.get('kilometrage', 0)
                                try:
                                    km_val = int(float(km_val)) if km_val else 0
                                except:
                                    km_val = 0
                                new_km = st.number_input("KM", value=km_val, key=f"km_v_{row['id']}")
                                data_update["kilometrage"] = int(new_km)
                        with c3:
                            if "carburant" in colonnes_voitures:
                                carburant_options = ["Essence", "Diesel", "Hybride", "Électrique"]
                                carb_val = row.get('carburant','Essence')
                                new_carb = st.selectbox("Carburant", carburant_options, index=carburant_options.index(carb_val) if carb_val in carburant_options else 0, key=f"carb_v_{row['id']}")
                                data_update["carburant"] = str(new_carb)
                            if "boite" in colonnes_voitures:
                                boite_options = ["Manuelle", "Automatique"]
                                boite_val = row.get('boite','Manuelle')
                                new_boite = st.selectbox("Boîte", boite_options, index=boite_options.index(boite_val) if boite_val in boite_options else 0, key=f"boite_v_{row['id']}")
                                data_update["boite"] = str(new_boite)
                            if "prix" in colonnes_voitures:
                                new_prix = st.number_input("Prix $", value=float(row.get('prix',0)), key=f"prix_v_{row['id']}")
                                data_update["prix"] = float(new_prix)
                            if "statut" in colonnes_voitures:
                                statut_options = ["Disponible", "En réparation", "Réservée", "Vendue"]
                                statut_val = row.get('statut','Disponible')
                                new_statut = st.selectbox("Statut", statut_options, index=statut_options.index(statut_val) if statut_val in statut_options else 0, key=f"statut_v_{row['id']}")
                                data_update["statut"] = str(new_statut)
                        if "quantite" in colonnes_voitures:
                            new_qte = st.number_input("Stock", value=int(row.get('quantite',1)), min_value=0, key=f"qte_v_{row['id']}")
                            data_update["quantite"] = int(new_qte)
                        if "qualite" in colonnes_voitures:
                            qualite_options = ["Neuf", "Occasion", "Reconditionné"]
                            qualite_val = row.get('qualite','Neuf')
                            new_qualite = st.selectbox("Qualité", qualite_options, index=qualite_options.index(qualite_val) if qualite_val in qualite_options else 0, key=f"qual_v_{row['id']}")
                            data_update["qualite"] = str(new_qualite)
                        if "code_qr" in colonnes_voitures:
                            new_code_qr = st.text_input("Code QR", value=row.get('code_qr',''), key=f"qr_v_{row['id']}")
                            data_update["code_qr"] = str(new_code_qr)
                        c1, c2 = st.columns(2)
                        if c1.button("✏️ Modifier", key=f"mod_v_parc_{row['id']}", width="stretch"):
                            try:
                                supabase.table("voitures").update(data_update).eq("id", int(row['id'])).execute()
                                st.success("Modifié")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur modif")
                                st.code(repr(e))
                        if st.session_state.user_role == "PDG" or perms.get('supprimer', False):
                            if c2.button("🗑️ Supprimer", key=f"del_v_parc_{row['id']}", width="stretch"):
                                try:
                                    supabase.table("voitures").delete().eq("id", int(row['id'])).execute()
                                    st.success("Supprimé")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erreur suppression")
                                    st.code(repr(e))

        with tab_pertes_v:
            st.subheader("⚠️ Déclarer Dégât/Perte Voiture")
            
            voitures_dispo = df_voitures[df_voitures.get('quantite', 1) > 0].copy() if not df_voitures.empty else pd.DataFrame()
            
            if voitures_dispo.empty:
                st.warning("Aucune voiture en stock pour déclarer un dégât")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    voiture_dict = {f"{v['marque']} {v['modele']} - {v.get('plaque','')} - Stock:{int(v.get('quantite',1))}": v for _, v in voitures_dispo.iterrows()}
                    voiture_choisie = st.selectbox("Voiture endommagée/perdue", list(voiture_dict.keys()))
                    qte_perte_v = st.number_input("Quantité endommagée", min_value=1, max_value=int(voiture_dict[voiture_choisie].get('quantite',1)) if voiture_choisie else 1)
                with col2:
                    motif_perte_v = st.selectbox("Type de dégât", ["Accident", "Vol", "Incendie", "Panne moteur", "Dégât carrosserie", "Pneus crevés", "Autre"])
                    detail_perte_v = st.text_area("Détails du dégât", placeholder="Ex: Pare-choc avant enfoncé + phare cassé")
                    responsable_v = st.text_input("Déclaré par", value=st.session_state.user_name, key="resp_v")
                
                if voiture_choisie:
                    voiture_data = voiture_dict[voiture_choisie]
                    valeur_perte_v = qte_perte_v * float(voiture_data.get('prix', 0))
                    st.error(f"💸 Valeur de la perte : {valeur_perte_v:,.2f} $")
                
                if st.button("🚨 ENREGISTRER DÉGÂT VOITURE", type="primary", width="stretch"):
                    if voiture_choisie and qte_perte_v > 0:
                        voiture_data = voiture_dict[voiture_choisie]
                        try:
                            # 1. Déduire du stock
                            nouveau_stock_v = int(voiture_data.get('quantite',1)) - qte_perte_v
                            nouveau_statut = "En réparation" if nouveau_stock_v > 0 else "Endommagée"
                            supabase.table('voitures').update({
                                "quantite": nouveau_stock_v,
                                "statut": nouveau_statut
                            }).eq("id", int(voiture_data['id'])).execute()
                            
                            # 2. Enregistrer mouvement perte
                            supabase.table('mouvements_stock').insert({
                                "article_id": int(voiture_data['id']),
                                "article_nom": f"{voiture_data['marque']} {voiture_data['modele']} - {voiture_data.get('plaque','')}",
                                "type": "PERTE_VOITURE",
                                "quantite": -int(qte_perte_v),
                                "motif": f"{motif_perte_v} - {detail_perte_v}",
                                "valeur": float(valeur_perte_v),
                                "created_by": responsable_v,
                                "created_at": datetime.now().isoformat()
                            }).execute()
                            
                            st.success(f"✅ Dégât enregistré. Stock {voiture_data['marque']} {voiture_data['modele']}: {nouveau_stock_v}")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur enregistrement dégât")
                            st.code(repr(e))
            
            st.divider()
            st.subheader("📋 Historique Dégâts/Pertes Voitures")
            try:
                pertes_v = supabase.table('mouvements_stock').select("*").eq("type", "PERTE_VOITURE").order("created_at", desc=True).limit(20).execute().data
            except:
                pertes_v = []
            
            if not pertes_v:
                st.info("Aucun dégât de voiture enregistré")
            else:
                total_pertes_v = sum(p.get('valeur', 0) for p in pertes_v)
                st.metric("💸 TOTAL PERTES VOITURES", f"{total_pertes_v:,.2f} $")
                
                for p in pertes_v:
                    with st.expander(f"🔴 {p.get('article_nom')} - {abs(p.get('quantite',0))} - {p.get('created_at','')[:10]}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Qté endommagée:** {abs(p.get('quantite', 0))}")
                            st.write(f"**Valeur:** {p.get('valeur', 0):,.2f} $")
                        with col2:
                            st.write(f"**Motif:** {p.get('motif', 'N/A')}")
                            st.write(f"**Par:** {p.get('created_by', 'N/A')}")
                        with col3:
                            if st.session_state.user_role == "PDG":
                                if st.button("🗑️ Supprimer", key=f"del_perte_v_{p.get('id')}"):
                                    supabase.table('mouvements_stock').delete().eq("id", p.get('id')).execute()
                                    st.rerun()
if "💰 Comptabilité" in tab_map:
    with tab_map["💰 Comptabilité"]:
        st.markdown("## 💰 Comptabilité - Relevé par Catégorie")
        colonnes_compta = get_table_columns("comptes")
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
            if st.session_state.user_role!= "PDG":
                cats_user = st.session_state.get('user_cats', [])
                if cats_user and "Toutes" not in cats_user:
                    df_compta_sorted = df_compta_sorted[df_compta_sorted['categorie'].isin(cats_user)]
                else:
                    # Si pas de catégorie définie et pas PDG = voit rien
                    if not cats_user:
                        st.error("⛔ Aucune catégorie autorisée. Contacte le PDG.")
                        st.stop()

            categories_fact = ["Toutes"] + list(df_compta_sorted.get('categorie', pd.Series(dtype=str)).dropna().unique())
            filtre_cat_fact = col_f4.selectbox("📂 Filtrer par Catégorie", categories_fact, key="filtre_cat_fact")
            filtre_client_fact = col_f5.text_input("👤 Nom Client contient", placeholder="Tape un nom...", key="filtre_client_fact")
            df_filtre_fact = df_compta_sorted[(df_compta_sorted['date'] >= str(date_debut)) & (df_compta_sorted['date'] <= str(date_fin))]

            if filtre_cat_fact!= "Toutes":
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
                            # 7 COLONNES = 7 VARIABLES
                            col_a, col_b, col_c, col_d, col_e, col_f, col_g = st.columns([1.2,0.8,2.5,1,0.8,0.5,0.5])
                            col_a.write(f"**{row.get('date','')}**")
                            col_b.write(f"{row.get('type','')}")
                            col_c.write(f"{row.get('description','')}")
                            col_d.write(f"**{row.get('montant',0):,.0f} {row.get('devise','FC')}**")
                            col_e.write(f"👤 {row.get('utilisateur','N/A')}")
                            if st.session_state.user_role == "PDG":
                                 if col_g.button("🗑️", key=f"del_compta_{row['id']}", help="Supprimer"):
                                      supabase.table("compta").delete().eq("id", int(row['id'])).execute()
                                      st.success("Facture supprimée")
                                      st.cache_data.clear()
                                      st.rerun()
                                 else:
                                    col_g.write("")
                            # === BOUTON TÉLÉCHARGER PDF ===
                            try:
                                details_list = []
                                if row.get('details') and str(row.get('details'))!= 'nan':
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
                            except Exception as e:
                                col_f.write("❌")
                                col_g.write("❌")
if "📋 Devis" in tab_map:
    with tab_map["📋 Devis"]:
        st.markdown("## 📋 Devis Consulting - Industriel & Bâtiment")

        if 'devis_sections' not in st.session_state:
            st.session_state.devis_sections = []
        if 'devis_bat_sections' not in st.session_state:
            st.session_state.devis_bat_sections = []
        if 'devis_bat_titre' not in st.session_state:
            st.session_state.devis_bat_titre = "DEVIS DE MATERIAUX POUR LA CONSTRUCTION DE CLOTURE DE 23.5m"
        if 'devis_bat_main_oeuvre' not in st.session_state:
            st.session_state.devis_bat_main_oeuvre = 1173.0

        tab_industriel, tab_batiment = st.tabs(["🏭 Devis Industriel", "🏗️ Devis Bâtiment"])

        with tab_industriel:
            peut_creer_ind = st.session_state.user_role == "PDG" or perms.get('devis_industriel', False)

            if peut_creer_ind:
                st.session_state.devis_type = "Industriel"
                st.subheader("🏭 Nouveau Devis Industriel")
                col1, col2, col3 = st.columns(3)
                with col1:
                    client_devis = st.text_input("👤 Client", key="client_devis_ind")
                    tel_client_devis = st.text_input("📞 Téléphone", value="+243...", key="tel_devis_ind")
                with col2:
                    titre_devis = st.text_input("📋 Titre Projet", key="titre_devis_ind")
                    parcelle_devis = st.text_input("🗺️ Parcelle N°", key="parcelle_devis_ind")
                with col3:
                    localisation_devis = st.text_input("📍 Localisation", key="loc_devis_ind")
                    devise_devis = st.selectbox("💵 Devise", ["USD", "FC", "€"], key="devise_devis_ind")

                st.divider()
                st.markdown("### 📊 Tableau Complet Éditable")

                if not st.session_state.devis_sections:
                    st.session_state.devis_sections = [
                        {
                            "numero": "A",
                            "titre": "ELECTRICITE",
                            "items": [
                                {"type": "cable", "designation": "Câble 2.5mm²", "marque": "Nexans", "section": "2.5mm²", "longueur": 100, "unite": "m", "qte": 1, "pu": 1.2},
                                {"type": "interrupteur", "designation": "Interrupteur", "marque": "Legrand", "couleur": "Blanc", "qualite": "Standard", "unite": "pc", "qte": 5, "pu": 3.5},
                                {"type": "autre", "designation": "Goulotte 25x16", "unite": "m", "qte": 10, "pu": 2.5, "spec": ""}
                            ]
                        }
                    ]

                total_general_ind = 0

                col_h1, col_h2, col_h3, col_h4, col_h5, col_h6, col_h7, col_h8 = st.columns([0.5, 3, 1.5, 1.5, 1, 1, 1, 0.5])
                col_h1.markdown("**N°**")
                col_h2.markdown("**Désignation**")
                col_h3.markdown("**Type/Marque**")
                col_h4.markdown("**Spécifications**")
                col_h5.markdown("**Qté**")
                col_h6.markdown("**PU**")
                col_h7.markdown("**Total**")
                col_h8.markdown("")
                st.divider()

                for idx, section in enumerate(st.session_state.devis_sections):
                    col_titre, col_del_sec = st.columns([5, 1])
                    with col_titre:
                        st.markdown(f"**{section['numero']}. {section['titre']}**")
                    with col_del_sec:
                        if st.button("🗑️ Supprimer Section", key=f"del_sec_ind_{idx}"):
                            st.session_state.devis_sections.pop(idx)
                            st.rerun()

                    sous_total_sec = 0

                    for i, item in enumerate(section['items']):
                        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.5, 3, 1.5, 1.5, 1, 1, 1, 0.5])

                        with col1:
                            new_num = st.text_input("N°", value=str(item.get('num', '')), key=f"num_ind_{idx}_{i}", label_visibility="collapsed")
                            section['items'][i]['num'] = new_num

                        with col2:
                            new_des = st.text_input("Désignation", value=item.get('designation', ''), key=f"des_ind_{idx}_{i}", label_visibility="collapsed")
                            section['items'][i]['designation'] = new_des

                        with col3:
                            type_item = st.selectbox("Type", ["cable", "interrupteur", "prise", "disjoncteur", "autre"],
                                                    index=["cable", "interrupteur", "prise", "disjoncteur", "autre"].index(item.get('type', 'autre')),
                                                    key=f"type_ind_{idx}_{i}", label_visibility="collapsed")
                            section['items'][i]['type'] = type_item

                        with col4:
                            if type_item == "cable":
                                marque = st.text_input("Marque", value=item.get('marque', ''), key=f"marque_ind_{idx}_{i}", label_visibility="collapsed", placeholder="Marque")
                                section_cable = st.text_input("Section", value=item.get('section', ''), key=f"sec_ind_{idx}_{i}", label_visibility="collapsed", placeholder="2.5mm²")
                                longueur = st.number_input("Long", value=float(item.get('longueur', 0)), key=f"long_ind_{idx}_{i}", label_visibility="collapsed", format="%.1f")
                                section['items'][i]['marque'] = marque
                                section['items'][i]['section'] = section_cable
                                section['items'][i]['longueur'] = longueur
                                section['items'][i]['spec'] = f"{marque} - {section_cable} - {longueur}m"
                            elif type_item == "interrupteur":
                                marque = st.text_input("Marque", value=item.get('marque', ''), key=f"marque_int_{idx}_{i}", label_visibility="collapsed", placeholder="Marque")
                                couleur = st.selectbox("Couleur", ["Blanc", "Noir", "Gris", "Beige"],
                                                      index=["Blanc", "Noir", "Gris", "Beige"].index(item.get('couleur', 'Blanc')) if item.get('couleur') in ["Blanc", "Noir", "Gris", "Beige"] else 0,
                                                      key=f"coul_int_{idx}_{i}", label_visibility="collapsed")
                                qualite = st.selectbox("Qualité", ["Standard", "Premium", "Pro"],
                                                      index=["Standard", "Premium", "Pro"].index(item.get('qualite', 'Standard')) if item.get('qualite') in ["Standard", "Premium", "Pro"] else 0,
                                                      key=f"qual_int_{idx}_{i}", label_visibility="collapsed")
                                section['items'][i]['marque'] = marque
                                section['items'][i]['couleur'] = couleur
                                section['items'][i]['qualite'] = qualite
                                section['items'][i]['spec'] = f"{marque} - {couleur} - {qualite}"
                            else:
                                spec = st.text_input("Détails", value=item.get('spec', ''), key=f"spec_ind_{idx}_{i}", label_visibility="collapsed", placeholder="Détails")
                                section['items'][i]['spec'] = spec

                        with col5:
                            unite = st.selectbox("Unité", ["m", "pc", "kg", "lot", "m²", "m³"],
                                               index=["m", "pc", "kg", "lot", "m²", "m³"].index(item.get('unite', 'pc')) if item.get('unite') in ["m", "pc", "kg", "lot", "m²", "m³"] else 1,
                                               key=f"unit_ind_{idx}_{i}", label_visibility="collapsed")
                            new_qte = st.number_input("Qté", value=float(item.get('qte', 0)), min_value=0.0, key=f"qte_ind_{idx}_{i}", label_visibility="collapsed", format="%.2f")
                            section['items'][i]['unite'] = unite
                            section['items'][i]['qte'] = new_qte

                        with col6:
                            new_pu = st.number_input("PU", value=float(item.get('pu', 0)), min_value=0.0, key=f"pu_ind_{idx}_{i}", label_visibility="collapsed", format="%.2f")
                            section['items'][i]['pu'] = new_pu

                        with col7:
                            pt = new_qte * new_pu
                            st.markdown(f"**{pt:,.2f}**")
                            sous_total_sec += pt

                        with col8:
                            if st.button("❌", key=f"del_item_ind_{idx}_{i}", help="Supprimer"):
                                section['items'].pop(i)
                                st.rerun()

                    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.5, 3, 1.5, 1.5, 1, 1, 1, 0.5])
                    with col1:
                        num_item = st.text_input("N°", key=f"num_ind_{idx}_new", label_visibility="collapsed", placeholder="N°")
                    with col2:
                        design = st.text_input("Désignation", key=f"des_ind_{idx}_new", label_visibility="collapsed", placeholder="Ajouter article...")
                    with col3:
                        type_new = st.selectbox("Type", ["cable", "interrupteur", "prise", "disjoncteur", "autre"], key=f"type_ind_{idx}_new", label_visibility="collapsed")
                    with col4:
                        if type_new == "cable":
                            marque_new = st.text_input("Marque", key=f"marque_ind_{idx}_new", label_visibility="collapsed", placeholder="Marque")
                            section_new = st.text_input("Section", key=f"sec_ind_{idx}_new", label_visibility="collapsed", placeholder="2.5mm²")
                            longueur_new = st.number_input("Long", min_value=0.0, key=f"long_ind_{idx}_new", label_visibility="collapsed", format="%.1f")
                        elif type_new == "interrupteur":
                            marque_new = st.text_input("Marque", key=f"marque_int_{idx}_new", label_visibility="collapsed", placeholder="Marque")
                            couleur_new = st.selectbox("Couleur", ["Blanc", "Noir", "Gris", "Beige"], key=f"coul_int_{idx}_new", label_visibility="collapsed")
                            qualite_new = st.selectbox("Qualité", ["Standard", "Premium", "Pro"], key=f"qual_int_{idx}_new", label_visibility="collapsed")
                        else:
                            spec_new = st.text_input("Détails", key=f"spec_ind_{idx}_new", label_visibility="collapsed", placeholder="Détails")
                    with col5:
                        unite = st.selectbox("Unité", ["m", "pc", "kg", "lot"], key=f"unit_ind_{idx}_new", label_visibility="collapsed")
                        qte = st.number_input("Qté", min_value=0.0, key=f"qte_ind_{idx}_new", label_visibility="collapsed", format="%.2f")
                    with col6:
                        pu = st.number_input("PU", min_value=0.0, key=f"pu_ind_{idx}_new", label_visibility="collapsed", format="%.2f")
                    with col7:
                        st.markdown(f"**{qte*pu:,.2f}**")
                    with col8:
                        if st.button("➕", key=f"add_item_ind_{idx}", help="Ajouter"):
                            if design:
                                new_item = {"num": num_item, "designation": design, "type": type_new, "unite": unite, "qte": qte, "pu": pu}
                                if type_new == "cable":
                                    new_item.update({"marque": marque_new, "section": section_new, "longueur": longueur_new})
                                elif type_new == "interrupteur":
                                    new_item.update({"marque": marque_new, "couleur": couleur_new, "qualite": qualite_new})
                                else:
                                    new_item.update({"spec": spec_new})
                                section['items'].append(new_item)
                                st.rerun()

                    col_st1, col_st2, col_st3 = st.columns([7.5, 1, 0.5])
                    col_st1.markdown(f"**Sous-total {section['titre']}**")
                    col_st2.markdown(f"**{sous_total_sec:,.2f}**")
                    total_general_ind += sous_total_sec
                    st.divider()

                col_add1, col_add2, col_add3 = st.columns([1,4,1])
                with col_add1:
                    new_section_num = st.text_input("N° Section", placeholder="B", key="new_sec_num_ind", label_visibility="collapsed")
                with col_add2:
                    new_section_titre = st.text_input("Titre Section", placeholder="Nouvelle section...", key="new_sec_titre_ind", label_visibility="collapsed")
                with col_add3:
                    if st.button("➕ Section", key="add_section_ind", width="stretch"):
                        if new_section_titre:
                            st.session_state.devis_sections.append({"numero": new_section_num, "titre": new_section_titre, "items": []})
                            st.rerun()

                st.divider()
                main_oeuvre = st.number_input("👷 Main d'oeuvre", min_value=0.0, key="mo_devis_ind")
                cout_total_ind = total_general_ind + main_oeuvre
                st.metric("COUT TOTAL DU PROJET", f"{cout_total_ind:,.2f} {devise_devis}")

                if st.button("📄 GÉNÉRER DEVIS PDF", type="primary", width="stretch", key="gen_devis_ind"):
                    if client_devis and titre_devis and st.session_state.devis_sections:
                        numero_devis = f"DEV-IND-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        try:
                            data_devis = {
                                "numero": numero_devis,
                                "type": "Industriel",
                                "client": client_devis,
                                "telephone": tel_client_devis,
                                "titre": titre_devis,
                                "parcelle": parcelle_devis,
                                "localisation": localisation_devis,
                                "sections": st.session_state.devis_sections,
                                "main_oeuvre": main_oeuvre,
                                "total": cout_total_ind,
                                "devise": devise_devis,
                                "created_by": st.session_state.user_name,
                                "created_at": datetime.now().isoformat()
                            }
                            supabase.table('devis').insert(data_devis).execute()
                            st.success(f"✅ Devis enregistré : {numero_devis}")
                            st.session_state.devis_sections = []
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur enregistrement")
                            st.code(repr(e))
                    else:
                        st.error("Client, Titre et au moins 1 section requis")
            else:
                st.info("🔒 Vous n'avez pas l'autorisation de créer des devis industriels")

            peut_telecharger_ind = st.session_state.user_role == "PDG" or perms.get('devis_industriel_download', False)
            peut_imprimer_ind = st.session_state.user_role == "PDG" or perms.get('devis_industriel_print', False)

            if peut_telecharger_ind or peut_imprimer_ind:
                st.divider()
                st.subheader("📚 Devis Industriel Enregistrés")
                try:
                    devis_ind_list = supabase.table('devis').select("*").eq("type", "Industriel").order("created_at", desc=True).limit(10).execute().data
                except:
                    devis_ind_list = []

                if not devis_ind_list:
                    st.info("Aucun devis industriel enregistré")
                else:
                    for d in devis_ind_list:
                        numero = d.get('numero', 'N/A')
                        client = d.get('client', 'N/A')
                        total = d.get('total', 0)
                        devise = d.get('devise', 'USD')
                        date_crea = d.get('created_at', '')[:10] if d.get('created_at') else 'N/A'

                        with st.expander(f"{numero} - {client} - {total:,.0f} {devise} - {date_crea}"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**Projet:** {d.get('titre','N/A')}")
                                st.write(f"**Parcelle:** {d.get('parcelle','N/A')}")
                                st.write(f"**Localisation:** {d.get('localisation','N/A')}")
                            with col2:
                                st.write(f"**Main d'oeuvre:** {d.get('main_oeuvre',0):,.0f} {devise}")
                                st.write(f"**TOTAL:** {total:,.0f} {devise}")
                                st.write(f"**Par:** {d.get('created_by','N/A')}")
                            with col3:
                                if peut_telecharger_ind:
                                    pdf_bytes = generer_pdf_devis_consulting(
                                        numero, "Industriel", client, d.get('titre',''),
                                        d.get('parcelle',''), d.get('localisation',''), d.get('sections',[]),
                                        devise, d.get('telephone',''), d.get('main_oeuvre',0)
                                    )
                                    st.download_button(
                                        label="📥 Télécharger",
                                        data=pdf_bytes,
                                        file_name=f"{numero}.pdf",
                                        mime="application/pdf",
                                        key=f"dl_ind_hist_{numero}",
                                        width="stretch"
                                    )
                                if peut_imprimer_ind:
                                    pdf_bytes = generer_pdf_devis_consulting(
                                        numero, "Industriel", client, d.get('titre',''),
                                        d.get('parcelle',''), d.get('localisation',''), d.get('sections',[]),
                                        devise, d.get('telephone',''), d.get('main_oeuvre',0)
                                    )
                                    pdf_b64 = base64.b64encode(pdf_bytes).decode()
                                    safe_id = numero.replace('-', '_')
                                    st.components.v1.html(f"""
                                        <button onclick="printPDF_{safe_id}()" style="width:100%; padding:8px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:5px;">
                                            🖨️ Imprimer
                                        </button>
                                        <script>
                                        function printPDF_{safe_id}() {{
                                            const pdfData = 'data:application/pdf;base64,{pdf_b64}';
                                            const win = window.open('', '_blank');
                                            win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');
                                            win.document.close();
                                            setTimeout(() => {{ win.print(); }}, 1000);
                                        }}
                                        </script>
                                    """, height=45)
                                if st.session_state.user_role == "PDG":
                                    if st.button("🗑️ Supprimer", key=f"del_ind_{numero}", width="stretch"):
                                        supabase.table('devis').delete().eq("numero", numero).execute()
                                        st.success("Supprimé")
                                        st.rerun()

        with tab_batiment:
            peut_creer_bat = st.session_state.user_role == "PDG" or perms.get('devis_batiment', False)

            if peut_creer_bat:
                st.session_state.devis_type = "Bâtiment"
                st.subheader("🏗️ Nouveau Devis Bâtiment - ASYMAS CONSULTING")

                if not st.session_state.devis_bat_sections:
                    st.session_state.devis_bat_sections = [
                        {
                            "numero": "I",
                            "titre": "Installation chantier / Demolitions",
                            "items": [
                                {"num": "", "designation": "Installationchantier", "unite": "ff", "qte": 1, "pu": 200},
                                {"num": "", "designation": "Demolitions", "unite": "ff", "qte": 1, "pu": 70}
                            ]
                        },
                        {
                            "numero": "II",
                            "titre": "fondation",
                            "items": [
                                {"num": "1", "designation": "moellon", "unite": "Canters", "qte": 9, "pu": 50},
                                {"num": "2", "designation": "sable", "unite": "Canters", "qte": 4, "pu": 40},
                                {"num": "3", "designation": "ciment", "unite": "sac", "qte": 23, "pu": 13.5},
                                {"num": "4", "designation": "gravier", "unite": "Canters", "qte": 3, "pu": 80},
                                {"num": "5", "designation": "armature de 10", "unite": "pièce", "qte": 9, "pu": 9},
                                {"num": "", "designation": "armature de 8", "unite": "pièce", "qte": 4, "pu": 8},
                                {"num": "6", "designation": "armature de 6", "unite": "pièce", "qte": 12, "pu": 3.5},
                                {"num": "7", "designation": "Fil à ligature", "unite": "kg", "qte": 16, "pu": 2.5}
                            ]
                        },
                        {
                            "numero": "III",
                            "titre": "Élévation de mur et corniche",
                            "items": [
                                {"num": "1", "designation": "bloc ciment", "unite": "pièce", "qte": 987, "pu": 1},
                                {"num": "2", "designation": "sable", "unite": "Canters", "qte": 5, "pu": 40},
                                {"num": "3", "designation": "ciment", "unite": "sac", "qte": 15, "pu": 13.5},
                                {"num": "4", "designation": "gravier", "unite": "Canters", "qte": 0.5, "pu": 70},
                                {"num": "5", "designation": "Barre Corniche de6", "unite": "pièce", "qte": 8, "pu": 3},
                                {"num": "6", "designation": "Fil à ligature", "unite": "kg", "qte": 6, "pu": 2}
                            ]
                        },
                        {
                            "numero": "IV",
                            "titre": "Coffrage Colonne, Cornice et Socle",
                            "items": [
                                {"num": "1", "designation": "socle et longrine", "unite": "pièce", "qte": 8, "pu": 7},
                                {"num": "2", "designation": "Colonne", "unite": "pièce", "qte": 18, "pu": 7},
                                {"num": "3", "designation": "Corniche", "unite": "pièce", "qte": 6, "pu": 7},
                                {"num": "4", "designation": "clous de8", "unite": "kg", "qte": 15, "pu": 2},
                                {"num": "5", "designation": "clous de10", "unite": "kg", "qte": 10, "pu": 2}
                            ]
                        },
                        {
                            "numero": "V",
                            "titre": "Finissage",
                            "items": [
                                {"num": "", "designation": "ciment", "unite": "sac", "qte": 20, "pu": 13.5},
                                {"num": "", "designation": "sable", "unite": "Canters", "qte": 7, "pu": 40}
                            ]
                        }
                    ]

                col1, col2, col3 = st.columns(3)
                with col1:
                    client_devis_bat = st.text_input("👤 Client", key="client_devis_bat")
                    tel_client_devis_bat = st.text_input("📞 Téléphone", value="+243...", key="tel_devis_bat")
                with col2:
                    st.session_state.devis_bat_titre = st.text_input("📋 Titre du Devis", value=st.session_state.devis_bat_titre, key="titre_devis_bat")
                    parcelle_devis_bat = st.text_input("🗺️ Parcelle N°", key="parcelle_devis_bat")
                with col3:
                    localisation_devis_bat = st.text_input("📍 Localisation", key="loc_devis_bat")
                    devise_devis_bat = st.selectbox("💵 Devise", ["USD", "FC", "€"], key="devise_devis_bat")

                st.divider()
                st.markdown("### 📊 Tableau Complet Éditable")

                total_general = 0

                col_h1, col_h2, col_h3, col_h4, col_h5, col_h6, col_h7 = st.columns([0.5, 4, 1.5, 1.5, 1.5, 1.5, 0.5])
                col_h1.markdown("**no**")
                col_h2.markdown("**désignation**")
                col_h3.markdown("**unité**")
                col_h4.markdown("**quantité**")
                col_h5.markdown("**pu USD**")
                col_h6.markdown("**PT USD**")
                col_h7.markdown("")
                st.divider()

                for idx, section in enumerate(st.session_state.devis_bat_sections):
                    st.markdown(f"**{section['numero']}. {section['titre']}**")

                    sous_total_sec = 0
                    for i, item in enumerate(section['items']):
                        col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 4, 1.5, 1.5, 1.5, 1.5, 0.5])
                        with col1:
                            new_num = st.text_input("N°", value=str(item['num']), key=f"num_bat_{idx}_{i}", label_visibility="collapsed")
                            section['items'][i]['num'] = new_num
                        with col2:
                            new_des = st.text_input("Désignation", value=item['designation'], key=f"des_bat_{idx}_{i}", label_visibility="collapsed")
                            section['items'][i]['designation'] = new_des
                        with col3:
                            options_unit = ["Canters", "sac", "pièce", "kg", "ff", "m3", "m2", "ml", "t", "barre"]
                            new_unit = st.selectbox("Unité", options_unit,
                                                   index=options_unit.index(item['unite']) if item['unite'] in options_unit else 0,
                                                   key=f"unit_bat_{idx}_{i}", label_visibility="collapsed")
                            section['items'][i]['unite'] = new_unit
                        with col4:
                            new_qte = st.number_input("Qté", value=float(item['qte']), min_value=0.0, key=f"qte_bat_{idx}_{i}", label_visibility="collapsed", format="%.2f")
                            section['items'][i]['qte'] = new_qte
                        with col5:
                            new_pu = st.number_input("PU", value=float(item['pu']), min_value=0.0, key=f"pu_bat_{idx}_{i}", label_visibility="collapsed", format="%.2f")
                            section['items'][i]['pu'] = new_pu
                        with col6:
                            pt = new_qte * new_pu
                            st.markdown(f"**{pt:,.2f}**")
                            sous_total_sec += pt
                        with col7:
                            if st.button("❌", key=f"del_item_bat_{idx}_{i}", help="Supprimer"):
                                section['items'].pop(i)
                                st.rerun()

                    col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 4, 1.5, 1.5, 1.5, 1.5, 0.5])
                    with col1:
                        num_item = st.text_input("N°", key=f"num_bat_{idx}_new", label_visibility="collapsed", placeholder="N°")
                    with col2:
                        design = st.text_input("Désignation", key=f"des_bat_{idx}_new", label_visibility="collapsed", placeholder="Ajouter article...")
                    with col3:
                        unite = st.selectbox("Unité", ["Canters", "sac", "pièce", "kg", "ff", "m3", "m2", "ml", "t", "barre"], key=f"unit_bat_{idx}_new", label_visibility="collapsed")
                    with col4:
                        qte = st.number_input("Qté", min_value=0.0, key=f"qte_bat_{idx}_new", label_visibility="collapsed", format="%.2f")
                    with col5:
                        pu = st.number_input("PU", min_value=0.0, key=f"pu_bat_{idx}_new", label_visibility="collapsed", format="%.2f")
                    with col6:
                        st.markdown(f"**{qte*pu:,.2f}**")
                    with col7:
                        if st.button("➕", key=f"add_item_bat_{idx}", help="Ajouter"):
                            if design:
                                section['items'].append({"num": num_item, "designation": design, "unite": unite, "qte": qte, "pu": pu})
                                st.rerun()

                    col_st1, col_st2, col_st3 = st.columns([6.5, 1.5, 0.5])
                    col_st1.markdown(f"**sous-total**")
                    col_st2.markdown(f"**{sous_total_sec:,.2f}**")
                    total_general += sous_total_sec
                    st.divider()

                col_add1, col_add2, col_add3 = st.columns([1,4,1])
                with col_add1:
                    new_section_num_bat = st.text_input("N° Section", placeholder="VI", key="new_sec_num_bat", label_visibility="collapsed")
                with col_add2:
                    new_section_titre_bat = st.text_input("Titre Section", placeholder="Nouvelle section...", key="new_sec_titre_bat", label_visibility="collapsed")
                with col_add3:
                    if st.button("➕ Section", key="add_section_bat", width="stretch"):
                        if new_section_titre_bat:
                            st.session_state.devis_bat_sections.append({"numero": new_section_num_bat, "titre": new_section_titre_bat, "items": []})
                            st.rerun()

                st.divider()
                col_mo1, col_mo2, col_mo3 = st.columns(3)
                with col_mo1:
                    st.metric("TOTAL MATERIAUX", f"{total_general:,.2f} {devise_devis_bat}")
                with col_mo2:
                    st.session_state.devis_bat_main_oeuvre = st.number_input("Main d'oeuvre", value=st.session_state.devis_bat_main_oeuvre, min_value=0.0, key="mo_devis_bat", format="%.2f")
                with col_mo3:
                    cout_total = total_general + st.session_state.devis_bat_main_oeuvre
                    st.metric("COUT TOTAL DU PROJET", f"{cout_total:,.2f} {devise_devis_bat}")

                st.markdown("**Architecte VINCENT KALAVI**")

                st.divider()
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if st.button("📄 GÉNÉRER DEVIS PDF", type="primary", width="stretch", key="gen_devis_bat"):
                        if client_devis_bat and st.session_state.devis_bat_titre:
                            numero_devis = f"DEV-BAT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                            try:
                                data_devis = {
                                    "numero": numero_devis,
                                    "type": "Bâtiment",
                                    "client": client_devis_bat,
                                    "telephone": tel_client_devis_bat,
                                    "titre": st.session_state.devis_bat_titre,
                                    "parcelle": parcelle_devis_bat,
                                    "localisation": localisation_devis_bat,
                                    "sections": st.session_state.devis_bat_sections,
                                    "main_oeuvre": st.session_state.devis_bat_main_oeuvre,
                                    "total": cout_total,
                                    "devise": devise_devis_bat,
                                    "created_by": st.session_state.user_name,
                                    "created_at": datetime.now().isoformat()
                                }
                                supabase.table('devis').insert(data_devis).execute()
                                st.success(f"✅ Devis enregistré : {numero_devis}")
                                st.cache_data.clear()
                            except Exception as e:
                                st.error("Erreur enregistrement")
                                st.code(repr(e))
                                st.stop()

                            pdf_bytes = generer_pdf_devis_consulting(
                                numero_devis, "Bâtiment", client_devis_bat, st.session_state.devis_bat_titre,
                                parcelle_devis_bat, localisation_devis_bat, st.session_state.devis_bat_sections,
                                devise_devis_bat, tel_client_devis_bat, st.session_state.devis_bat_main_oeuvre
                            )
                            st.session_state.pdf_devis_bat = pdf_bytes
                            st.session_state.num_devis_bat = numero_devis
                            st.rerun()
                        else:
                            st.error("Client et Titre requis")

                with col_btn2:
                    if 'pdf_devis_bat' in st.session_state and st.session_state.pdf_devis_bat:
                        st.download_button(
                            label="📥 Télécharger PDF",
                            data=st.session_state.pdf_devis_bat,
                            file_name=f"{st.session_state.num_devis_bat}.pdf",
                            mime="application/pdf",
                            width="stretch",
                            key="dl_devis_bat"
                        )

                with col_btn3:
                    if st.button("🔄 Réinitialiser", key="reset_devis_bat", width="stretch"):
                        st.session_state.devis_bat_sections = []
                        if 'pdf_devis_bat' in st.session_state:
                            del st.session_state.pdf_devis_bat
                        st.rerun()

                if 'pdf_devis_bat' in st.session_state and st.session_state.pdf_devis_bat:
                    pdf_b64 = base64.b64encode(st.session_state.pdf_devis_bat).decode()
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
            else:
                st.info("🔒 Vous n'avez pas l'autorisation de créer des devis bâtiment")

            peut_telecharger_bat = st.session_state.user_role == "PDG" or perms.get('devis_batiment_download', False)
            peut_imprimer_bat = st.session_state.user_role == "PDG" or perms.get('devis_batiment_print', False)

            if peut_telecharger_bat or peut_imprimer_bat:
                st.divider()
                st.subheader("📚 Devis Bâtiment Enregistrés")

                try:
                    devis_bat_list = supabase.table('devis').select("*").eq("type", "Bâtiment").order("created_at", desc=True).limit(5).execute().data
                except:
                    devis_bat_list = []

                if not devis_bat_list:
                    st.info("Aucun devis bâtiment enregistré")
                else:
                    for d in devis_bat_list:
                        numero = d.get('numero', 'N/A')
                        client = d.get('client', 'N/A')
                        total = d.get('total', 0)
                        devise = d.get('devise', 'USD')

                        col1, col2, col3, col4 = st.columns([3,2,1,1])
                        with col1:
                            st.write(f"**{numero}** - {client}")
                        with col2:
                            st.write(f"{total:,.0f} {devise}")
                        with col3:
                            if peut_telecharger_bat:
                                pdf_bytes = generer_pdf_devis_consulting(
                                    numero, "Bâtiment", client, d.get('titre',''),
                                    d.get('parcelle',''), d.get('localisation',''), d.get('sections',[]),
                                    devise, d.get('telephone',''), d.get('main_oeuvre',0)
                                )
                                st.download_button(
                                    label="📥",
                                    data=pdf_bytes,
                                    file_name=f"{numero}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_bat_bas_{numero}"
                                )
                            else:
                                st.write("🔒")
                        with col4:
                            if peut_imprimer_bat:
                                pdf_bytes = generer_pdf_devis_consulting(
                                    numero, "Bâtiment", client, d.get('titre',''),
                                    d.get('parcelle',''), d.get('localisation',''), d.get('sections',[]),
                                    devise, d.get('telephone',''), d.get('main_oeuvre',0)
                                )
                                pdf_b64 = base64.b64encode(pdf_bytes).decode()
                                safe_id = numero.replace('-', '_')
                                st.components.v1.html(f"""
                                    <button onclick="printPDF_{safe_id}()" style="width:100%; padding:6px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer;">
                                        🖨️
                                    </button>
                                    <script>
                                    function printPDF_{safe_id}() {{
                                        const pdfData = 'data:application/pdf;base64,{pdf_b64}';
                                        const win = window.open('', '_blank');
                                        win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');
                                        win.document.close();
                                        setTimeout(() => {{ win.print(); }}, 1000);
                                    }}
                                    </script>
                                """, height=40)
                            else:
                                st.write("🔒")
                    
                        
                        
                        

                        
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
                cats_autorisees = st.multiselect("Sélectionne les catégories que cet utilisateur peut voir dans Factures", 
                                                 ["Toutes"] + cats_dispo, default=["Toutes"], key="cats_factures")

                if st.form_submit_button("💾 Ajouter Utilisateur", type="primary"):
                    if nom_user and pwd_user:
                        try:
                            perms_dict = {
                                "dashboard": perm_dashboard,
                                "commerce": perm_commerce,
                                "stock": perm_stock,
                                "immobilier": perm_immobilier,
                                "automobile": perm_automobile,
                                "parc": perm_parc,
                                "comptabilite": perm_comptabilite,
                                "factures": perm_factures,
                                "supprimer": perm_supprimer,
                                "users": perm_users,
                                "devis_industriel": perm_devis_ind,
                                "devis_industriel_download": perm_devis_ind_dl,
                                "devis_industriel_print": perm_devis_ind_pr,
                                "devis_batiment": perm_devis_bat,
                                "devis_batiment_download": perm_devis_bat_dl,
                                "devis_batiment_print": perm_devis_bat_pr,
                                "devis_historique": perm_devis_hist
                            }
                            supabase.table("utilisateurs").insert({
                                "nom": nom_user,
                                "role": role_user,
                                "password": pwd_user,
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
                    # AFFICHAGE ACTUEL
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.write("**Onglets :**")
                        if current_perms.get('dashboard'): st.write("✅ Dashboard")
                        if current_perms.get('commerce'): st.write("✅ Commerce")
                        if current_perms.get('stock'): st.write("✅ Stock")
                        if current_perms.get('immobilier'): st.write("✅ Immobilier")
                        if current_perms.get('automobile'): st.write("✅ Automobile")
                        if current_perms.get('parc'): st.write("✅ Parc")
                        if current_perms.get('comptabilite'): st.write("✅ Comptabilité")
                        if current_perms.get('factures'): st.write("✅ Factures")
                        if current_perms.get('users'): st.write("✅ Utilisateurs")
                        if current_perms.get('supprimer'): st.write("✅ Supprimer")
                    with c2:
                        st.write("**Devis Industriel :**")
                        if current_perms.get('devis_industriel'): st.write("✅ Créer")
                        if current_perms.get('devis_industriel_download'): st.write("✅ Télécharger")
                        if current_perms.get('devis_industriel_print'): st.write("✅ Imprimer")
                    with c3:
                        st.write("**Devis Bâtiment :**")
                        if current_perms.get('devis_batiment'): st.write("✅ Créer")
                        if current_perms.get('devis_batiment_download'): st.write("✅ Télécharger")
                        if current_perms.get('devis_batiment_print'): st.write("✅ Imprimer")
                        if current_perms.get('devis_historique'): st.write("✅ Historique")

                    st.divider()
                    
                    # SEUL LE PDG PEUT MODIFIER
                    if st.session_state.user_role == "PDG":
                        st.markdown("**✏️ Modifier les autorisations :**")
                        with st.form(f"edit_user_{user['id']}"):
                            col1, col2, col3, col4 = st.columns(4)
                            perm_dashboard = col1.checkbox("Dashboard", value=current_perms.get('dashboard', False), key=f"edit_dash_{user['id']}")
                            perm_commerce = col2.checkbox("Commerce", value=current_perms.get('commerce', False), key=f"edit_com_{user['id']}")
                            perm_stock = col3.checkbox("Gestion Stock", value=current_perms.get('stock', False), key=f"edit_stock_{user['id']}")
                            perm_immobilier = col4.checkbox("Immobilier", value=current_perms.get('immobilier', False), key=f"edit_immo_{user['id']}")
                            perm_automobile = col1.checkbox("Automobile", value=current_perms.get('automobile', False), key=f"edit_auto_{user['id']}")
                            perm_parc = col2.checkbox("Gestion Parc", value=current_perms.get('parc', False), key=f"edit_parc_{user['id']}")
                            perm_comptabilite = col3.checkbox("Comptabilité", value=current_perms.get('comptabilite', False), key=f"edit_comp_{user['id']}")
                            perm_factures = col4.checkbox("Factures", value=current_perms.get('factures', False), key=f"edit_fact_{user['id']}")
                            perm_supprimer = col1.checkbox("🗑️ Peut Supprimer", value=current_perms.get('supprimer', False), key=f"edit_sup_{user['id']}")
                            perm_users = col2.checkbox("👥 Gérer Utilisateurs", value=current_perms.get('users', False), key=f"edit_users_{user['id']}")

                            st.markdown("**📋 Devis Industriel :**")
                            col_i1, col_i2, col_i3 = st.columns(3)
                            perm_devis_ind = col_i1.checkbox("Créer", value=current_perms.get('devis_industriel', False), key=f"edit_ind_{user['id']}")
                            perm_devis_ind_dl = col_i2.checkbox("Télécharger", value=current_perms.get('devis_industriel_download', False), key=f"edit_ind_dl_{user['id']}")
                            perm_devis_ind_pr = col_i3.checkbox("Imprimer", value=current_perms.get('devis_industriel_print', False), key=f"edit_ind_pr_{user['id']}")

                            st.markdown("**📋 Devis Bâtiment :**")
                            col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                            perm_devis_bat = col_b1.checkbox("Créer", value=current_perms.get('devis_batiment', False), key=f"edit_bat_{user['id']}")
                            perm_devis_bat_dl = col_b2.checkbox("Télécharger", value=current_perms.get('devis_batiment_download', False), key=f"edit_bat_dl_{user['id']}")
                            perm_devis_bat_pr = col_b3.checkbox("Imprimer", value=current_perms.get('devis_batiment_print', False), key=f"edit_bat_pr_{user['id']}")
                            perm_devis_hist = col_b4.checkbox("Historique", value=current_perms.get('devis_historique', False), key=f"edit_hist_{user['id']}")

                            col_btn1, col_btn2 = st.columns(2)
                            if col_btn1.form_submit_button("💾 Enregistrer Modifications", type="primary", width="stretch"):
                                new_perms = {
                                    "dashboard": perm_dashboard, "commerce": perm_commerce, "stock": perm_stock,
                                    "immobilier": perm_immobilier, "automobile": perm_automobile, "parc": perm_parc,
                                    "comptabilite": perm_comptabilite, "factures": perm_factures, "supprimer": perm_supprimer,
                                    "users": perm_users, "devis_industriel": perm_devis_ind,
                                    "devis_industriel_download": perm_devis_ind_dl, "devis_industriel_print": perm_devis_ind_pr,
                                    "devis_batiment": perm_devis_bat, "devis_batiment_download": perm_devis_bat_dl,
                                    "devis_batiment_print": perm_devis_bat_pr, "devis_historique": perm_devis_hist
                                }
                                try:
                                    supabase.table("utilisateurs").update({"permissions": new_perms}).eq("id", int(user['id'])).execute()
                                    st.success(f"Permissions de {user['nom']} mises à jour")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erreur modification")
                                    st.code(repr(e))

                        # SUPPRIMER UTILISATEUR - SAUF SOI-MEME
                        if user['nom']!= st.session_state.user_name:
                            if st.button("🗑️ Supprimer cet utilisateur", key=f"del_user_{user['id']}", type="secondary", width="stretch"):
                                try:
                                    supabase.table("utilisateurs").delete().eq("id", int(user['id'])).execute()
                                    st.success(f"Utilisateur {user['nom']} supprimé")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erreur suppression")
                                    st.code(repr(e))
                        else:
                            st.info("🔒 Vous ne pouvez pas supprimer votre propre compte")
                    else:
                        st.info("🔒 Seul le PDG peut modifier les autorisations")
                         # === FLOKI SOLDAT V15.2 - CODE COMPLET CORRIGÉ ===
import difflib, re, urllib.parse, streamlit as st, pandas as pd, tempfile, speech_recognition as sr, base64
from datetime import datetime, date, timedelta
from fpdf import FPDF

class PDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.set_auto_page_break(auto=True, margin=20)
        self.set_left_margin(20)
        self.set_right_margin(20)
        self.set_top_margin(25)
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'ASYMAS COMPANY', 0, 1, 'C')
        self.ln(2)
    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 8, f'Page {self.page_no()}', 0, 0, 'C')

class FLOKI:
    def __init__(self, supabase_client, dataframes):
        self.supabase = supabase_client
        self.df = dataframes

    def _clean_question(self, q):
        q = q.lower()
        q = q.replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a").replace("ç", "c")
        q = re.sub(r'[^\w\s]', ' ', q)
        return re.sub(r'\s+', ' ', q).strip()

    def ask(self, question):
        q_raw, q = question, self._clean_question(question)
        if any(g in q for g in ["slt", "salut", "bonjour", "hello", "yo"]):
            return "Présent chef. Floki à l’écoute. Donnez-moi l’ordre."
        if any(m in q for m in ["genere", "redige", "ecris", "fais", "prepare", "lettre", "contrat", "conge"]):
            return self._generate_document_illimite(q_raw)
        if "envoi" in q and "message" in q:
            return self._action_send_message(q_raw)
        if "commande" in q or "commander" in q:
            return self._action_commander(q)
        rep = self._search_asymas(q)
        return rep + "\n\nSource: ASYMAS" if rep else "Chef, je n’ai pas cette donnée dans ASYMAS."

    def _generate_document_illimite(self, q):
        q_clean = self._clean_question(q)
        doc_type_map = {
            "mise en garde": "mise_en_garde", "conge de maternite": "conge_maternite",
            "conge": "conge", "rupture": "rupture", "contrat": "contrat",
            "pret": "pret", "attestation": "attestation", "licenciement": "licenciement",
            "avertissement": "avertissement"
        }
        doc_type = "lettre"
        for key, val in doc_type_map.items():
            if key in q_clean:
                doc_type = val
                break

        required_fields = {
            "contrat": ["nom", "poste", "salaire", "date_debut", "date_fin"],
            "conge": ["nom", "poste", "date_debut", "date_fin", "motif"],
            "conge_maternite": ["nom", "poste", "date_debut", "date_fin"],
            "mise_en_garde": ["nom", "poste", "motif", "date_debut"],
            "licenciement": ["nom", "poste", "motif", "date_debut"],
            "avertissement": ["nom", "poste", "motif", "date_debut"],
            "pret": ["nom", "poste", "montant", "motif"],
            "attestation": ["nom", "poste", "date_debut"],
            "rupture": ["nom", "poste", "motif", "date_debut"],
            "lettre": ["nom", "poste", "objet", "corps"]
        }

        data = self._extract_all_fields(q)
        template_func = getattr(self, f"_template_{doc_type}", self._template_lettre)
        text = template_func(data)

        st.session_state['floki_doc_data'] = data
        st.session_state['floki_doc_text'] = text
        st.session_state['floki_doc_type'] = doc_type
        st.session_state['floki_required_fields'] = required_fields.get(doc_type, ["nom"])

        missing = [k for k in required_fields.get(doc_type, ["nom"]) if data.get(k) in ["______", "______ FC"]]
        if missing:
            st.session_state['floki_missing_fields'] = missing
            # FIX SYNTAXERROR : on utilise une variable séparateur
            sep = ", "
            doc_nom = doc_type.replace("_"," ")
            return f"Document {doc_type.replace("_"," ")} généré pour {data["nom"]}, mais il manque : {sep.join(missing)}. Corrige ci-dessous."
        else:
            pdf_bytes = self._create_pdf_bytes(f"{doc_type}_{data['nom']}", text, doc_type)
            filename = f"{doc_type}_{data['nom']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.session_state['pdf_ready'] = pdf_bytes
            st.session_state['pdf_name'] = filename
            return f"{doc_type.replace('_', ' ').capitalize()} complet généré pour {data['nom']}. Choisis comment le transférer ci-dessous."

    def _extract_all_fields(self, q):
        return {
            "nom": self._extract_value(q, ["pour", "a", "de", "nomme", "appele"]) or "______",
            "poste": self._extract_value(q, ["poste", "fonction"]) or "______",
            "salaire": self._extract_value(q, ["salaire", "remuneration"]) or "______ FC",
            "montant": self._extract_value(q, ["montant", "somme"]) or "______ FC",
            "date_debut": self._extract_value(q, ["du", "debut"]) or "______",
            "date_fin": self._extract_value(q, ["au", "fin"]) or "______",
            "motif": self._extract_value(q, ["motif", "raison"]) or "______",
            "objet": self._extract_after(q, "objet") or "______",
            "corps": self._extract_after(q, "texte") or "______",
            "date": date.today().strftime('%d/%m/%Y')
        }

    def _extract_value(self, q, keywords):
        for kw in keywords:
            match = re.search(rf'{kw}\s+([a-z0-9\s\-]+)', q, re.IGNORECASE)
            if match:
                return match.group(1).strip().capitalize()
        return None

    def _extract_after(self, q, keyword):
        match = re.search(rf'{keyword}\s*:\s*(.+)', q, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _signature_block(self):
    return (
        "\n\nFait a Kinshasa, le " + date.today().strftime('%d/%m/%Y') + 
        "\n\nSignature de l employe : __________________" + 
        "    Signature Direction ASYMAS : __________________"
    )
        
               
               

    def _template_contrat(self, d):
        header = "AFRICA INNOVATION INDUSTRIAL\nCONTRAT DE TRAVAIL\n"
        body = f"Entre AFRICA INNOVATION INDUSTRIAL et {d['nom']}\nPoste : {d['poste']}\nDurée : {d['date_debut']} au {d['date_fin']}\nSalaire : {d['salaire']}\n"
        return header + body + self._signature_block()
    def _template_conge(self, d):
        header = "ASYMAS COMPANY\nDEMANDE DE CONGE\n"
        body = f"Je soussigné(e) {d['nom']}, {d['poste']}, demande congé du {d['date_debut']} au {d['date_fin']}.\nMotif : {d['motif']}\n"
        return header + body + self._signature_block()
    def _template_conge_maternite(self, d):
        header = "ASYMAS COMPANY\nDEMANDE DE CONGE DE MATERNITE\n"
        body = f"Je soussignée {d['nom']}, {d['poste']}, sollicite un congé de maternité du {d['date_debut']} au {d['date_fin']}, conformément au code du travail.\n"
        return header + body + self._signature_block()
    def _template_mise_en_garde(self, d):
        header = "ASYMAS COMPANY\nMISE EN GARDE\n"
        body = f"Monsieur/Madame {d['nom']}\nPoste : {d['poste']}\nObjet : Manquement - {d['motif']}\n\nFaits constatés le {d['date_debut']}.\n"
        return header + body + "\n\nSignature Direction ASYMAS : __________________"
    def _template_licenciement(self, d):
        header = "ASYMAS COMPANY\nLICENCIEMENT\n"
        body = f"Monsieur/Madame {d['nom']}\nPoste : {d['poste']}\nMotif : {d['motif']}\nPréavis à partir du {d['date_debut']}.\n"
        return header + body + self._signature_block()
    def _template_avertissement(self, d):
        header = "ASYMAS COMPANY\nAVERTISSEMENT\n"
        body = f"Monsieur/Madame {d['nom']}\nPoste : {d['poste']}\nMotif : {d['motif']}\nDate : {d['date_debut']}\n"
        return header + body + "\n\nSignature Direction ASYMAS : __________________"
    def _template_pret(self, d):
        header = "ASYMAS COMPANY\nDEMANDE DE PRET\n"
        body = f"Je soussigné(e) {d['nom']}, {d['poste']}, sollicite {d['montant']}.\nMotif : {d['motif']}\n"
        return header + body + self._signature_block()
    def _template_attestation(self, d):
        header = "ASYMAS COMPANY\nATTESTATION DE TRAVAIL\n"
        body = f"Nous certifions que {d['nom']}, {d['poste']}, travaille chez ASYMAS depuis {d['date_debut']}.\n"
        return header + body + "\n\nSignature Direction ASYMAS : __________________"
    def _template_rupture(self, d):
        header = "ASYMAS COMPANY\nRUPTURE DE CONTRAT\n"
        body = f"Monsieur/Madame {d['nom']}\nPoste : {d['poste']}\nMotif : {d['motif']}\nPréavis à partir du {d['date_debut']}.\n"
        return header + body + self._signature_block()
    def _template_lettre(self, d):
        header = "ASYMAS COMPANY\nLETTRE ADMINISTRATIVE\n"
        body = f"Monsieur/Madame {d['nom']}\nPoste : {d['poste']}\nObjet : {d['objet']}\n\n{d['corps']}\n"
        return header + body + self._signature_block()

    def _create_pdf_bytes(self, filename, text, doc_type):
        pdf = PDF()
        if doc_type == "contrat":
            pdf.header = lambda: (pdf.set_font('Arial', 'B', 12), pdf.cell(0, 8, 'AFRICA INNOVATION INDUSTRIAL', 0, 1, 'C'), pdf.ln(2))
        pdf.add_page()
        pdf.set_font("Arial", size=11)
        page_width = pdf.w - pdf.l_margin - pdf.r_margin
        for line in text.strip().split('\n'):
            line = line.strip()
            if not line:
                pdf.ln(5)
                continue
            safe_line = line.encode('latin-1', errors='replace').decode('latin-1')
            w = page_width if page_width > 0 else 170
            pdf.multi_cell(w, 8, safe_line)
        return pdf.output(dest='S').encode('latin-1', errors='replace')

    def _upload_to_supabase(self, pdf_bytes, filename):
        try:
            path = f"documents/{filename}"
            self.supabase.storage.from_("floki-docs").upload(path, pdf_bytes, {"upsert": "true"})
            url = self.supabase.storage.from_("floki-docs").get_public_url(path)
            return url
        except Exception as e:
            return None

    def _action_send_message(self, question):
        nums = re.findall(r'\+?\d{9,15}', question)
        if nums:
            numero = nums[0].replace("+", "")
            message = re.sub(r'envoi.*?message.*?\+?\d{9,15}\s*:?', '', question, flags=re.IGNORECASE).strip()
            url = f"https://wa.me/{numero}?text={urllib.parse.quote(message)}"
            return f"Ordre exécuté chef. Lien WhatsApp: {url}"
        return "Chef, donne-moi un numéro."

    def _action_commander(self, q):
        produit_match = re.search(r'commande\s+([a-z0-9\s]+?)\s+quantite\s+(\d+)', q)
        if not produit_match:
            produit_match = re.search(r'commander\s+([a-z0-9\s]+?)\s+(\d+)', q)
        if not produit_match:
            return "Chef, dis-moi: 'commande [produit] quantité [nombre]'"
        produit, quantite = produit_match.group(1).strip(), int(produit_match.group(2))
        try:
            self.supabase.table("commandes").insert({
                "produit": produit, "quantite": quantite, "date": datetime.now().isoformat(),
                "statut": "en_attente", "commande_par": st.session_state.get('user_name', 'PDG')
            }).execute()
            return f"Commande enregistrée chef: {quantite} x {produit}."
        except Exception as e:
            return f"Erreur: {e}."

    def _search_asymas(self, q):
        if "commerce" in q and "exterieur" in q:
            return self._get_commerce_exterieur(q)
        if "importation" in q or "importer" in q:
            return self._get_importations(q)
        if "exportation" in q or "exporter" in q:
            return self._get_exportations(q)
        if "stock" in q and "de" in q:
            produit = q.split("de")[-1].strip()
            return self._search_product(produit)
        if "commande" in q and ("attente" in q or "en cours" in q or "liste" in q):
            return self._get_commandes_attente()
        if "voiture" in q and ("moins cher" in q or "prix" in q):
            return self._get_voiture_moins_cher()
        if "chiffre" in q or "ca" in q or "revenu" in q:
            return self._chiffre_affaires()
        return None

    def _get_commerce_exterieur(self, q):
        imp = self._get_importations(q)
        exp = self._get_exportations(q)
        return f"RAPPORT COMMERCE EXTERIEUR:\n\n{imp}\n\n{exp}"

    def _get_importations(self, q=""):
        try:
            result = self.supabase.table("importations").select("*").order("date", desc=True).limit(20).execute()
            if not result.data: return "Aucune importation enregistrée chef."
            data = result.data
            pays_mots = ["dubaï", "dubai", "chine", "kampala", "europe", "usa", "etats unis"]
            for mot in pays_mots:
                if mot in q:
                    data = [r for r in data if mot in str(r.get('pays', r.get('destination', ''))).lower()]
                    break
            if not data: return f"Aucune importation trouvée pour {mot} chef."
            total = sum(float(r.get('montant', 0)) for r in data[:5])
            txt = "\n".join([f"- {r.get('produit', 'N/A')} de {r.get('pays', 'N/A')}: {float(r.get('montant', 0)):,.0f} FC" for r in data[:5]])
            return f"Dernières importations - Total: {total:,.0f} FC\n{txt}"
        except: return "Chef, table 'importations' vide."

    def _get_exportations(self, q=""):
        try:
            result = self.supabase.table("exportations").select("*").order("date", desc=True).limit(20).execute()
            if not result.data: return "Aucune exportation enregistrée chef."
            data = result.data
            pays_mots = ["dubaï", "dubai", "chine", "kampala", "europe", "usa", "etats unis"]
            for mot in pays_mots:
                if mot in q:
                    data = [r for r in data if mot in str(r.get('pays', r.get('destination', ''))).lower()]
                    break
            if not data: return f"Aucune exportation trouvée pour {mot} chef."
            total = sum(float(r.get('montant', 0)) for r in data[:5])
            txt = "\n".join([f"- {r.get('produit', 'N/A')} vers {r.get('pays', 'N/A')}: {float(r.get('montant', 0)):,.0f} FC" for r in data[:5]])
            return f"Dernières exportations - Total: {total:,.0f} FC\n{txt}"
        except: return "Chef, table 'exportations' vide."

    def _search_product(self, q):
        if self.df['articles'].empty: return None
        articles = self.df['articles'].copy()
        articles['nom_clean'] = articles['nom_article'].astype(str).str.lower().str.replace(r'[^a-z0-9\s]', '', regex=True).str.replace(r'\s+', ' ', regex=True).str.strip()
        q_clean = re.sub(r'[^a-z0-9\s]', '', q).strip()
        for _, r in articles.iterrows():
            if q_clean in r['nom_clean']:
                return f"{r['nom_article']}: Stock {int(r['stock'])} unités, Prix {float(r['prix_vente']):,.0f} FC"
        return None

    def _get_commandes_attente(self):
        try:
            result = self.supabase.table("commandes").select("*").eq("statut", "en_attente").order("date", desc=True).limit(10).execute()
            if not result.data: return "Aucune commande en attente chef."
            txt = "\n".join([f"- {r['quantite']} x {r['produit']}" for r in result.data])
            return f"Commandes en attente:\n{txt}"
        except: return "Chef, table 'commandes' manquante."

    def _get_voiture_moins_cher(self):
        if self.df['voitures'].empty: return "Pas de données voitures chef."
        prix_col = next((col for col in ['prix', 'prix_vente', 'prix_achat', 'montant'] if col in self.df['voitures'].columns), None)
        if not prix_col: return "Chef, pas de colonne prix."
        dispo = self.df['voitures'][self.df['voitures'].get('quantite', 1) > 0]
        if dispo.empty: return "Aucune voiture en stock chef."
        moins_chere = dispo.loc[dispo[prix_col].idxmin()]
        return f"Voiture la moins chère: {moins_chere.get('modele', 'N/A')} à {float(moins_chere[prix_col]):,.0f} FC"

    def _chiffre_affaires(self):
        if self.df['compta'].empty: return "Pas de données compta chef."
        rev = self.df['compta'][self.df['compta']['type'] == 'Revenu']['montant'].sum()
        dep = self.df['compta'][self.df['compta']['type'] == 'Dépense']['montant'].sum()
        return f"Rapport compta:\nRevenus: {rev:,.0f} FC\nDépenses: {dep:,.0f} FC\nSolde: {rev-dep:,.0f} FC"

# === UI ===
if 'floki' not in st.session_state:
    dataframes = {"articles": df_articles, "compta": df_compta, "biens": df_biens, "voitures": df_voitures}
    st.session_state.floki = FLOKI(supabase, dataframes)

user_role = str(st.session_state.get('user_role', '')).upper()

with st.sidebar:
    if user_role == 'PDG':
        st.divider()
        st.markdown("### 🤖 FLOKI")
        q = st.text_input("Ton ordre", key="floki_input", placeholder="Ex: fais un contrat pour Paul")
        if st.button("Exécuter", type="primary", use_container_width=True):
            if q:
                with st.spinner("Floki réfléchit..."):
                    st.session_state.floki_rep = st.session_state.floki.ask(q)
        if 'floki_rep' in st.session_state:
            st.success(st.session_state.floki_rep)
            if 'floki_missing_fields' in st.session_state:
                st.warning("Chef, remplis les champs vides :")
                with st.form("correction_form"):
                    data = st.session_state['floki_doc_data']
                    new_data = data.copy()
                    for field in st.session_state['floki_missing_fields']:
                        new_data[field] = st.text_input(field, value="", placeholder=f"Renseigne {field}")
                    submitted = st.form_submit_button("Valider et générer PDF")
                    if submitted:
                        st.session_state['floki_doc_data'].update(new_data)
                        doc_type = st.session_state['floki_doc_type']
                        template_func = getattr(st.session_state.floki, f"_template_{doc_type}", st.session_state.floki._template_lettre)
                        new_text = template_func(st.session_state['floki_doc_data'])
                        pdf_bytes = st.session_state.floki._create_pdf_bytes(f"{doc_type}_{new_data['nom']}", new_text, doc_type)
                        st.session_state['pdf_ready'] = pdf_bytes
                        st.session_state['pdf_name'] = f"{doc_type}_{new_data['nom']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                        del st.session_state['floki_missing_fields']
                        st.rerun()
            if 'pdf_ready' in st.session_state:
                st.markdown("#### Transfert du document")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button("Télécharger", data=st.session_state['pdf_ready'],
                                       file_name=st.session_state['pdf_name'], mime="application/pdf",
                                       use_container_width=True)
                with col2:
                    numero = st.text_input("N° WhatsApp", placeholder="+243...", key="whatsapp_num")
                    if st.button("Envoyer WhatsApp", use_container_width=True):
                        if numero:
                            msg = f"Document ASYMAS: {st.session_state['pdf_name']}"
                            wa_url = f"https://wa.me/{numero.replace('+','')}?text={urllib.parse.quote(msg)}"
                            st.markdown(f"[Clique ici pour envoyer]({wa_url})")
                            st.caption("Ouvre sur ton téléphone, puis joins le PDF téléchargé.")
                        else:
                            st.error("Renseigne un numéro chef.")
                with col3:
                    if st.button("Générer lien de partage", use_container_width=True):
                        with st.spinner("Upload en cours..."):
                            url = st.session_state.floki._upload_to_supabase(st.session_state['pdf_ready'], st.session_state['pdf_name'])
                            if url:
                                st.code(url, language=None)
                                st.success("Lien copié. Partage-le chef.")
                            else:
                                st.error("Upload échoué. Vérifie bucket 'floki-docs' public sur Supabase.")
