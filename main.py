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
  \"background_color\": \"#000\",
  \"theme_color\": \"#ffcc00\",
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

# === STYLE HOLOGRAPHIQUE JAUNE COMME L'IMAGE ===
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
[data-testid="stBottomBlockContainer"] {display: none!important;}

.stApp {
    background: radial-gradient(circle at center, #1a1200 0%, #000 100%);
    overflow-x: hidden;
}

h1, h2, h3 {
    color: #ffcc00!important;
    font-size: 2.2rem!important;
    font-weight: 900!important;
    padding: 10px 0!important;
    border-bottom: 3px solid #ffcc00!important;
    text-shadow: 0 0 20px #ffcc00, 0 0 40px #ffaa00!important;
    margin-bottom: 20px!important;
}

div[data-testid="stMetricValue"] {
    color: #ffcc00!important;
    text-shadow: 0 0 15px #ffcc00;
    font-size: 2.8rem!important;
}

.stButton>button {
    background: linear-gradient(135deg, #ffcc00 0%, #ff9900 100%)!important;
    color: black!important;
    font-weight: bold;
    border: none;
    border-radius: 10px;
    box-shadow: 0 0 20px rgba(255,204,0,0.6);
    transition: all 0.3s;
}
.stButton>button:hover {
    box-shadow: 0 0 40px rgba(255,204,0,1);
    transform: translateY(-2px);
}

.login-circle {
    width: 380px; height: 380px; border-radius: 50%;
    border: 3px solid #ffcc00;
    box-shadow: 0 0 40px #ffcc00, inset 0 0 30px rgba(255,204,0,0.2);
    margin: 50px auto; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    background: radial-gradient(circle, rgba(255,204,0,0.15) 0%, rgba(0,0,0,0.9) 70%);
    animation: rotateGlow 4s linear infinite; padding: 25px;
}
@keyframes rotateGlow {
    0% {box-shadow: 0 0 40px #ffcc00, inset 0 0 30px rgba(255,204,0,0.2);}
    50% {box-shadow: 0 0 60px #ffaa00, inset 0 0 40px rgba(255,170,0,0.3);}
    100% {box-shadow: 0 0 40px #ffcc00, inset 0 0 30px rgba(255,204,0,0.2);}
}

.holo-dash {
    background: radial-gradient(circle at center, #2a1f0a 0%, #000 100%);
    padding: 50px; border-radius: 30px; position: relative;
    height: 450px; margin-bottom: 30px; overflow: hidden;
}
.holo-cart {
    font-size: 100px; position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%); color: #ffcc00;
    filter: drop-shadow(0 0 25px #ffcc00);
    animation: float 3s ease-in-out infinite;
}
.holo-icon {
    position: absolute; top: 50%; left: 50%; font-size: 35px;
    color: #ffcc00; filter: drop-shadow(0 0 15px #ffcc00);
    animation: orbit 12s linear infinite;
}
@keyframes float {
    0%, 100% { transform: translate(-50%, -50%) translateY(0px); }
    50% { transform: translate(-50%, -50%) translateY(-20px); }
}
@keyframes orbit {
    from { transform: rotate(0deg) translateX(170px) rotate(0deg); }
    to { transform: rotate(360deg) translateX(170px) rotate(-360deg); }
}
</style>
""", unsafe_allow_html=True)

passwords_db = load_passwords()

if 'user_role' not in st.session_state:
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.session_state.user_perms = {}
    st.session_state.user_cats = []

if st.session_state.user_role is None:
    st.markdown('<div class="login-circle">', unsafe_allow_html=True)
    st.markdown("<h2 style='color:#ffcc00; text-shadow:0 0 15px #ffcc00'>🔐 CONNEXION</h2>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:80px; color:#ffcc00; filter:drop-shadow(0 0 20px #ffcc00)'>🛒</div>", unsafe_allow_html=True)

    df_users_login = load_table("utilisateurs")
    if not df_users_login.empty:
        options_login = ["-- Sélectionner --"] + [f"{row['nom']} - {row['role']}" for _, row in df_users_login.iterrows()]
    else:
        options_login = ["-- Sélectionner --", "PDG TSANG", "Gérante ASIYA", "BASAM"]

    profil = st.selectbox("Utilisateur", options_login, label_visibility="collapsed")
    password = st.text_input("Mot de passe", type="password", key="pwd", label_visibility="collapsed", placeholder="Mot de passe")

    if st.button("SE CONNECTER", width="stretch", type="primary"):
        if profil!= "-- Sélectionner --":
            nom_connect = profil.split(" - ")[0]
            df_users_login = supabase.table("utilisateurs").select("id, nom, role, password").execute().data
            df_users_login = pd.DataFrame(df_users_login)
            user_data = df_users_login[df_users_login['nom'] == nom_connect]
            if not user_data.empty and password == user_data.iloc[0]['password']:
                st.session_state.user_role = user_data.iloc[0]['role']
                st.session_state.user_name = user_data.iloc[0]['nom']
                st.session_state.user_perms = user_data.iloc[0].get('permissions', {})
                st.session_state.user_cats = user_data.iloc[0].get('categories_autorisees', [])
                st.rerun()
            else:
                st.error("Profil ou mot de passe incorrect")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

if 'user_role' in st.session_state and st.session_state.user_role is not None:
    with st.sidebar:
        st.markdown(f"## 👤 {st.session_state.user_name}")
        st.markdown(f"**Rôle : {st.session_state.user_role}**")
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state.user_role=None
            st.session_state.user_name=None
            st.session_state.user_perms={}
            st.session_state.user_cats=[]
            st.rerun()

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

    if st.session_state.user_role == "PDG" or st.session_state.user_perms.get('dashboard', True):
        st.markdown("""
        <div class="holo-dash">
            <div class="holo-cart">🛒</div>
            <div class="holo-icon" style="animation-delay: 0s">🏪</div>
            <div class="holo-icon" style="animation-delay: -2s">🚚</div>
            <div class="holo-icon" style="animation-delay: -4s">📢</div>
            <div class="holo-icon" style="animation-delay: -6s">@</div>
            <div class="holo-icon" style="animation-delay: -8s">@</div>
            <div class="holo-icon" style="animation-delay: -10s">📶</div>
        </div>
        """, unsafe_allow_html=True)

    perms = st.session_state.user_perms
    if isinstance(perms, str):
        try:
            perms = json.loads(perms)
        except:
            perms = {}

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

    # === PARTIE 1 : CODE COMMERCE ===
    if "🛍️ Commerce" in tab_map:
        with tab_map["🛍️ Commerce"]:
            # Colle ici tout ton code Commerce de la partie 1

    # === PARTIE 2 : CODE GESTION STOCK, IMMOBILIER, AUTOMOBILE, GESTION PARC ===
    if "📦 Gestion Stock" in tab_map:
        with tab_map["📦 Gestion Stock"]:
            # Colle ici tout ton code Gestion Stock de la partie 2

    if "🏠 Immobilier" in tab_map:
        with tab_map["🏠 Immobilier"]:
            # Colle ici ton code Immobilier

    if "🚗 Automobile" in tab_map:
        with tab_map["🚗 Automobile"]:
            # Colle ici ton code Automobile

    if "🚘 Gestion Parc" in tab_map:
        with tab_map["🚘 Gestion Parc"]:
            # Colle ici ton code Gestion Parc

    # === PARTIE 3 : CODE COMPTABILITÉ, FACTURES, DEVIS, UTILISATEURS ===
    if "💰 Comptabilité" in tab_map:
        with tab_map["💰 Comptabilité"]:
            # Colle ici ton code Comptabilité

    if "📄 Factures" in tab_map:
        with tab_map["📄 Factures"]:
            # Colle ici ton code Factures

    if "📋 Devis" in tab_map:
        with tab_map["📋 Devis"]:
            # Colle ici ton code Devis complet

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

            # === FLOKI SOLDAT COMPLET - VERSION PDG ===
            import difflib
            import re
            import urllib.parse
            import json
            import requests
            import streamlit as st
            import pandas as pd
            from datetime import datetime

            class FLOKI:
                def __init__(self, supabase_client, dataframes):
                    self.supabase = supabase_client
                    self.df = dataframes
                    self.system_knowledge = self._get_supabase_schema()

                def _get_supabase_schema(self):
                    schema = {}
                    tables = ["articles", "compta", "biens", "voitures", "mouvements_stock", "devis", "notifications", "floki_logs"]
                    for t in tables:
                        try:
                            result = self.supabase.table(t).select("*").limit(1).execute()
                            schema[t] = list(result.data[0].keys()) if result.data else []
                        except:
                            schema[t] = []
                    return schema

                def ask(self, question):
                    q = question.lower().strip()
                    log_entry = {"demande": question, "date": datetime.now().isoformat(), "source": "ASYMAS"}

                    if any(g in q for g in ["slt", "salut", "bonjour", "hello", "yo"]):
                        return "Présent chef. FLOKI opérationnel. Donnez l'ordre."

                    if "envoie" in q and "message" in q and "numero" in q:
                        result = self._action_send_whatsapp(question)
                        log_entry.update({"action": "whatsapp_send", "reponse": result})
                        self._log_action(log_entry)
                        return result

                    if any(k in q for k in ["redige", "rédige", "lettre", "relance", "convocation"]):
                        result = self._action_rediger(question)
                        log_entry.update({"action": "redaction", "reponse": result})
                        self._log_action(log_entry)
                        return result

                    if any(k in q for k in ["conseil", "avis", "opportunite", "risque", "que faire"]):
                        result = self._action_conseil(q)
                        log_entry.update({"action": "conseil", "reponse": result})
                        self._log_action(log_entry)
                        return result

                    q_clean = re.sub(r'(trouve moi|donne moi|donne|trouve|cherche|le prix de|prix du|du|de|le|la|un|une|pour moi|combien)', '', q).strip()
                    rep = self._search_asymas(q_clean)
                    if rep:
                        log_entry.update({"source": "ASYMAS", "reponse": rep})
                        self._log_action(log_entry)
                        return rep + "\n\nSource: ASYMAS"

                    web_rep = self._search_web(question)
                    log_entry.update({"source": "WEB", "reponse": web_rep})
                    self._log_action(log_entry)
                    return web_rep + "\n\nSource: WEB"

                def _search_asymas(self, q):
                    if "voiture" in q and ("moins cher" in q or "prix" in q):
                        return self._get_voiture_moins_cher()
                    if "voiture" in q and ("liste" in q or "donne" in q):
                        return self._get_voitures_stock()
                    rep = self._search_product(q)
                    if rep: return rep
                    if "perte" in q and "commerce" in q:
                        return self._get_pertes_commerce()
                    if any(k in q for k in ["stock bas", "rupture", "manque"]):
                        return self._stock_bas()
                    if any(k in q for k in ["ca", "chiffre", "revenu", "vente", "argent", "benefice", "solde"]):
                        return self._chiffre_affaires()
                    return None

                def _get_voiture_moins_cher(self):
                    if self.df['voitures'].empty:
                        return "Pas de données voitures chef."
                    prix_col = next((col for col in ['prix', 'prix_vente', 'prix_achat', 'montant'] if col in self.df['voitures'].columns), None)
                    if not prix_col:
                        return "Chef, je ne trouve pas la colonne prix dans voitures."
                    dispo = self.df['voitures'][self.df['voitures'].get('quantite', 1) > 0]
                    if dispo.empty:
                        return "Aucune voiture en stock chef."
                    moins_chere = dispo.loc[dispo[prix_col].idxmin()]
                    modele = moins_chere.get('modele', moins_chere.get('nom', 'N/A'))
                    prix = float(moins_chere[prix_col])
                    return f"Voiture la moins chère: {modele} à {prix:,.0f} FC"

                def _get_voitures_stock(self):
                    if self.df['voitures'].empty:
                        return "Pas de données voitures chef."
                    dispo = self.df['voitures'][self.df['voitures'].get('quantite', 0) > 0]
                    if dispo.empty:
                        return "Aucune voiture en stock chef."
                    txt = "\n".join([f"- {r.get('modele', r.get('nom', 'N/A'))}: {int(r.get('quantite', 0))} unités - {float(r.get('prix', r.get('prix_vente', 0))):,.0f} FC" for _, r in dispo.iterrows()])
                    return f"Voitures en stock:\n{txt}"

                def _get_pertes_commerce(self):
                    try:
                        result = self.supabase.table("mouvements_stock").select("*").eq("type", "perte").eq("categorie", "commerce").order("date", desc=True).limit(10).execute()
                        if not result.data:
                            return "Aucune perte commerce enregistrée chef."
                        txt = "\n".join([f"- {r.get('article', 'N/A')}: {r.get('montant', 0):,.0f} FC le {r.get('date', '')[:10]}" for r in result.data])
                        return f"Dernières pertes commerce:\n{txt}"
                    except Exception as e:
                        return f"Erreur lecture pertes: {e}. Vérifiez RLS sur mouvements_stock."

                def _search_product(self, q):
                    if self.df['articles'].empty:
                        return None
                    articles = self.df['articles'].copy()
                    articles['nom_clean'] = articles['nom_article'].astype(str).str.lower().str.replace(r'[^a-z0-9\s]', '', regex=True).str.replace(r'\s+', ' ', regex=True).str.strip()
                    q_clean = re.sub(r'[^a-z0-9\s]', '', q).strip()
                    mots_q = [w for w in q_clean.split() if len(w) > 2]
                    if mots_q:
                        for _, r in articles.iterrows():
                            if all(word in r['nom_clean'] for word in mots_q):
                                return f"{r['nom_article']}: Stock {int(r['stock'])} unités, Prix {float(r['prix_vente']):,.0f} FC"
                    noms = articles['nom_clean'].tolist()
                    closest = difflib.get_close_matches(q_clean, noms, n=1, cutoff=0.45)
                    if closest:
                        r = articles[articles['nom_clean'] == closest[0]].iloc[0]
                        return f"{r['nom_article']}: Stock {int(r['stock'])} unités, Prix {float(r['prix_vente']):,.0f} FC"
                    return None

                def _stock_bas(self):
                    if self.df['articles'].empty:
                        return "Pas d'articles chef."
                    low = self.df['articles'][self.df['articles']['stock'] < 5]
                    if low.empty:
                        return "Stock OK chef. Rien en dessous de 5 unités."
                    txt = "\n".join([f"- {r['nom_article']}: {r['stock']} unités" for _, r in low.iterrows()])
                    return f"Attention chef, stock bas:\n{txt}"

                def _chiffre_affaires(self):
                    if self.df['compta'].empty:
                        return "Pas de données compta chef."
                    rev = self.df['compta'][self.df['compta']['type'] == 'Revenu']['montant'].sum()
                    dep = self.df['compta'][self.df['compta']['type'] == 'Dépense']['montant'].sum()
                    return f"Rapport compta:\nRevenus: {rev:,.0f} FC\nDépenses: {dep:,.0f} FC\nSolde: {rev-dep:,.0f} FC"

                def _search_web(self, q):
                    try:
                        url = f"https://api.duckgo.com/?q={urllib.parse.quote(q)}&format=json&no_html=1"
                        r = requests.get(url, timeout=4)
                        data = r.json()
                        if data.get('AbstractText'):
                            return f"Info vérifiée: {data['AbstractText']}"
                        return f"Négatif chef. Rien de vérifiable sur le web pour '{q}'."
                    except:
                        return "Le web ne répond pas chef."

                def _action_rediger(self, question):
                    if "relance" in question.lower():
                        return "Objet: Relance de paiement\nMonsieur/Madame,\n\nNous constatons que la facture reste impayée.\nMerci de régulariser sous 48h.\n\nASYMAS BUSINESS"
                    if "convocation" in question.lower():
                        return "Objet: Convocation\nVous êtes convoqué(e) le [DATE] à [HEURE] pour [OBJET].\n\nASYMAS BUSINESS"
                    return "Chef, précise: 'redige une relance' ou 'redige une convocation'."

                def _action_send_whatsapp(self, question):
                    nums = re.findall(r'\+?\d{9,15}', question)
                    if not nums:
                        return "Chef, donne-moi un numéro. Ex: 'envoie un message au +243995105623 salut'"
                    numero = nums[0].replace("+", "")
                    message = re.sub(r'envoie un message.*?\+?\d{9,15}', '', question).strip() or "Message de ASYMAS BUSINESS"
                    url = f"https://wa.me/{numero}?text={urllib.parse.quote(message)}"
                    return f"Lien WhatsApp prêt: {url}"

                def notify_internal(self, message):
                    try:
                        self.supabase.table("notifications").insert({
                            "message": f"[{st.session_state.get('user_name', 'PDG')}]: {message}",
                            "created_at": datetime.now().isoformat()
                        }).execute()
                        return "Notification envoyée à l’équipe chef."
                    except Exception as e:
                        return f"Échec notification: {e}"

                def _action_conseil(self, q):
                    if not self.df['articles'].empty and not self.df['compta'].empty:
                        stock_bas = len(self.df['articles'][self.df['articles']['stock'] < 5])
                        rev = self.df['compta'][self.df['compta']['type'] == 'Revenu']['montant'].sum()
                        return f"FAIT: {stock_bas} articles en stock bas. CA: {rev:,.0f} FC.\nCONSEIL: Réapprovisionne sous 48h.\nRISQUE: Rupture = perte de vente."
                    return "Chef, je croise vos données ASYMAS pour donner fait, conseil, risque."

                def _log_action(self, log_entry):
                    try:
                        self.supabase.table("floki_logs").insert(log_entry).execute()
                    except:
                        pass

            # === UI FLOKI ===
            if 'floki' not in st.session_state:
                dataframes = {
                    "articles": df_articles,
                    "compta": df_compta,
                    "biens": df_biens,
                    "voitures": df_voitures
                }
                st.session_state.floki = FLOKI(supabase, dataframes)

            with st.sidebar:
                st.divider()
                st.markdown("### 🤖 FLOKI")
                st.caption("Conseiller du PDG - Comprend le système ASYMAS")

                q = st.text_input("Ordre pour FLOKI", key="floki_input",
                                  placeholder="Ex: liste de mes voitures, voiture moins cher, CA du mois")

                st.info("🎤 Micro désactivé temporairement. Utilisez Chrome + localhost pour l'activer plus tard.")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Exécuter", type="primary", use_container_width=True):
                        if q:
                            with st.spinner("FLOKI réfléchit..."):
                                rep = st.session_state.floki.ask(q)
                                st.session_state.floki_rep = rep

                with col2:
                    if st.button("Notifier équipe", use_container_width=True):
                        if q:
                            msg = st.session_state.floki.notify_internal(q)
                            st.toast(msg)

                if 'floki_rep' in st.session_state:
                    rep_clean = st.session_state.floki_rep.replace('"', '\\"').replace("\n", " ").replace("'", "\\'")
                    st.components.v1.html(f"""
                        <script>
                        if ('speechSynthesis' in window) {{
                            window.speechSynthesis.cancel();
                            var msg = new SpeechSynthesisUtterance("{rep_clean}");
                            msg.lang = 'fr-FR';
                            msg.rate = 1;
                            window.speechSynthesis.speak(msg);
                        }}
                        </script>
                    """, height=0)
                    st.success(st.session_state.floki_rep)
        
            
