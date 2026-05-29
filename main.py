import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide", initial_sidebar_state="auto")
st.markdown("""<meta name="mobile-web-app-capable" content="yes">""", unsafe_allow_html=True)

from supabase import create_client, Client
from datetime import date, datetime, timedelta
from fpdf import FPDF
import tempfile, os, json, qrcode, base64, io
from PIL import Image
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from streamlit_qrcode_scanner import qrcode_scanner
import difflib, re, urllib.parse, requests

# === SESSION STATE ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = ""
    st.session_state.user_name = ""
    st.session_state.perms = {}
    st.session_state.user_cats = []
if 'selected_module' not in st.session_state:
    st.session_state.selected_module = None

# Récupère module depuis URL
if 'module' in st.query_params and st.session_state.selected_module is None:
    st.session_state.selected_module = st.query_params['module']
    st.rerun()

# === CSS ===
st.markdown("""
<style>
.block-container{padding:0!important;max-width:100%!important;}
.main{background:#0a0a0a;margin:0;padding:0;}
div[data-testid="stTextInput"]{position:absolute!important; bottom:8%!important; left:50%!important; transform:translateX(-50%)!important; width:180px!important; z-index:100!important;}
div[data-testid="stTextInput"] input{background:rgba(0,0,0,0.9)!important; border:2px solid #FFD700!important; border-radius:10px!important; color:#FFD700!important; text-align:center!important; padding:10px!important;}
div[data-testid="stTextInput"] label{display:none!important;}
#MainMenu {visibility: hidden!important;}
header {visibility: hidden!important;}
.stAppToolbar {display: none!important;}
[data-testid="stToolbar"] {display: none!important;}
[data-testid="stDecoration"] {display: none!important;}
[data-testid="stHeader"] {display: none!important;}
footer {visibility: hidden!important;}
.stDeployButton {display:none!important;}
[data-testid="stStatusWidget"] {display: none!important;}
[data-testid="stDecoration"] {display: none!important;}
[data-testid="stHeader"] {display: none!important;}
button[kind="header"] {display: none!important;}
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

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

def check_perm(key):
    return st.session_state.user_role == "PDG" or st.session_state.perms.get(key, False)

# === LOGIN HOLOGRAMME ===
if not st.session_state.logged_in:
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
        </div>
    </div>
    <style>@keyframes pulseRing{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}50%{transform:translate(-50%,-50%) scale(1.12);opacity:1;}}
    @keyframes pulseCart{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.18);}}
    @keyframes rotate{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}</style>
    """, unsafe_allow_html=True)

    pwd = st.text_input("", type="password", placeholder="Mot de passe ASYMAS")
    if pwd:
        result = supabase.table("utilisateurs").select("*").eq("password", pwd).execute()
        if result.data:
            u = result.data[0]
            st.session_state.logged_in = True
            st.session_state.user_role = u['role']
            st.session_state.user_name = u['nom']
            st.session_state.perms = u.get('permissions', {})
            st.session_state.user_cats = u.get('categories_autorisees', [])
            st.rerun()
        elif pwd == "asymas2025":
            st.session_state.logged_in = True
            st.session_state.user_role = "PDG"
            st.session_state.user_name = "PDG"
            st.session_state.perms = {}
            st.session_state.user_cats = []
            st.rerun()
    st.stop()

# === ACCUEIL AVEC 6 BOUTONS CLIQUABLES ===
if st.session_state.selected_module is None:
    html_buttons = """
    <div style="position:relative;width:100%;height:700px;background:radial-gradient(ellipse at center 55%, rgba(255,215,0,0.7) 0%, rgba(15,15,15,1) 85%);overflow:hidden;">
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:450px;height:450px;">
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:380px;height:380px;border:2px solid rgba(255,215,0,0.5);border-radius:50%;box-shadow:0 0 80px rgba(255,215,0,0.8);animation:pulseRing 3s ease-in-out infinite;"></div>
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:300px;height:300px;border:2px dotted rgba(255,215,0,0.9);border-radius:50%;animation:rotate 15s linear infinite;"></div>
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:220px;height:220px;border:3px solid #FFD700;border-radius:50%;box-shadow:0 0 90px #FFD700;"></div>
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:170px;height:170px;background:radial-gradient(circle,#FFD700 0%,#FFA500 100%);border-radius:50%;box-shadow:0 0 100px #FFD700;display:flex;flex-direction:column;align-items:center;justify-content:center;animation:pulseCart 2s ease-in-out infinite;">
                <div style="font-size:50px;">🛒</div>
                <div style="font-size:16px;font-weight:bold;color:#000;margin-top:5px;">ASYMAS</div>
            </div>
        </div>
        <button onclick="window.location.search='?module=Commerce'" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(90deg) translate(190px) rotate(-90deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🏪<br>Commerce</button>
        <button onclick="window.location.search='?module=Auto'" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(30deg) translate(190px) rotate(-30deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🚚<br>Auto</button>
        <button onclick="window.location.search='?module=Factures'" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-30deg) translate(190px) rotate(30deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🧾<br>Factures</button>
        <button onclick="window.location.search='?module=Immo'" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-90deg) translate(190px) rotate(90deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🏠<br>Immo</button>
        <button onclick="window.location.search='?module=Stock'" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-150deg) translate(190px) rotate(150deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">📦<br>Stock</button>
        <button onclick="window.location.search='?module=Compta'" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(150deg) translate(190px) rotate(-150deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">📊<br>Compta</button>
    </div>
    <style>@keyframes pulseRing{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}50%{transform:translate(-50%,-50%) scale(1.12);opacity:1;}}
    @keyframes pulseCart{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.18);}}
    @keyframes rotate{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}</style>
    """
    components.html(html_buttons, height=700)

    if st.button("🚪 Déconnexion"):
        st.session_state.clear()
        st.rerun()

# === VERIFICATION DROIT AVANT AFFICHAGE MODULE ===
elif st.session_state.selected_module:
    perm_map = {
        "Commerce": "commerce", "Stock": "stock", "Immo": "immobilier",
        "Auto": "automobile", "Compta": "comptabilite", "Factures": "factures"
    }
    perm_key = perm_map.get(st.session_state.selected_module, "")

    if not check_perm(perm_key):
        st.error(f"⛔ Vous n'avez pas l'autorisation d'accéder au module {st.session_state.selected_module}")
        if st.button("← Retour Accueil"):
            st.session_state.selected_module = None
            st.query_params.clear()
            st.rerun()
        st.stop()

    st.divider()
    col1, col2 = st.columns([6,1])
    with col1:
        st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
        st.markdown(f"### {st.session_state.selected_module}")
    with col2:
        if st.button("← Retour"):
            st.session_state.selected_module = None
            st.query_params.clear()
            st.rerun()

    table_map = {
        "Commerce": "articles", "Stock": "articles", "Immo": "biens",
        "Auto": "voitures", "Compta": "compta", "Factures": "factures_proforma"
    }
    df = load_table(table_map.get(st.session_state.selected_module, "articles"))
    st.dataframe(df, use_container_width=True)

# === CHARGEMENT DATA GLOBAL ===
else:
    with st.sidebar:
        st.markdown(f"## 👤 {st.session_state.user_name}")
        st.markdown(f"**Rôle : {st.session_state.user_role}**")
        st.info("ASYMAS BUSINESS v3.0")
        if st.button("🏠 Retour Accueil"):
            st.session_state.selected_module = None
            st.query_params.clear()
            st.rerun()
        if st.button("🔄 Actualiser"):
            st.cache_data.clear()
            st.rerun()
        if st.button("🔒 Déconnexion"):
            st.session_state.clear()
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

    perms = st.session_state.perms
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
            st.markdown("## 📊 Dashboard ASYMAS")
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
            if not df_compta.empty:
                st.subheader("📈 Dernières transactions")
                st.dataframe(df_compta.head(10), use_container_width=True)

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
                                nouveau_stock = int(article_data['stock']) - qte_perte
                                supabase.table('articles').update({"stock": nouveau_stock}).eq("id", int(article_data['id'])).execute()

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
                    data=pdf_bytes,
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
                    data=pdf_bytes,
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

if "🚘 Gestion Parc" in tab_map:
    with tab_map["🚘 Gestion Parc"]:
        st.markdown("## 🚘 Gestion Parc Automobile")
        st.info("Module en cours de développement - Utilise Automobile pour générer les factures location/achat")

if "💰 Comptabilité" in tab_map:
    with tab_map["💰 Comptabilité"]:
        st.markdown("## 💰 Comptabilité ASYMAS")
        col1, col2, col3 = st.columns(3)
        with col1:
            date_debut = st.date_input("Date début", value=date.today().replace(day=1))
        with col2:
            date_fin = st.date_input("Date fin", value=date.today())
        with col3:
            type_filter = st.selectbox("Type", ["Tous", "Revenu", "Dépense"])

        df_filtre = df_compta.copy()
        if not df_filtre.empty and 'date' in df_filtre.columns:
            df_filtre = df_filtre[(df_filtre['date'].dt.date >= date_debut) & (df_filtre['date'].dt.date <= date_fin)]
        if type_filter!= "Tous":
            df_filtre = df_filtre[df_filtre['type'] == type_filter]

        if not df_filtre.empty:
            total_rev = df_filtre[df_filtre['type']=='Revenu']['montant'].sum()
            total_dep = df_filtre[df_filtre['type']=='Dépense']['montant'].sum()
            solde = total_rev - total_dep
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Revenus", f"{total_rev:,.0f} FC")
            col2.metric("💸 Dépenses", f"{total_dep:,.0f} FC")
            col3.metric("💎 Solde", f"{solde:,.0f} FC")

            excel_data = generer_excel_pro(df_filtre, f"Relevé {date_debut} au {date_fin}", total_rev, total_dep, solde)
            st.download_button("📥 Télécharger Excel Pro", data=excel_data, file_name=f"releve_compta_{date_debut}_{date_fin}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
            st.dataframe(df_filtre, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune donnée sur cette période")

if "📄 Factures" in tab_map:
    with tab_map["📄 Factures"]:
        st.markdown("## 📄 Gestion Factures & Proformas")
        st.subheader("Historique Factures")
        if df_factures.empty:
            st.info("Aucune facture générée")
        else:
            st.dataframe(df_factures, use_container_width=True, hide_index=True)

if "📋 Devis" in tab_map:
    with tab_map["📋 Devis"]:
        st.markdown("## 📋 Devis ASYMAS Consulting")
        tab_devis_ind, tab_devis_bat = st.tabs(["🏭 Devis Industriel", "🏗️ Devis Bâtiment"])

        with tab_devis_ind:
            st.subheader("Devis Industriel")
            client_ind = st.text_input("Client", key="client_ind")
            titre_ind = st.text_input("Titre Projet", key="titre_ind")
            if st.button("📄 Générer Devis Industriel", type="primary"):
                if client_ind and titre_ind:
                    num_devis = f"DEV-IND-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    sections = [{"numero": "1", "titre": titre_ind, "items": [{"num": "1.1", "designation": "Prestation industrielle", "unite": "Forfait", "qte": 1, "pu": 0}]}]
                    pdf_bytes = generer_pdf_devis_consulting(num_devis, "Industriel", client_ind, titre_ind, "", sections)
                    st.success(f"✅ Devis {num_devis} généré")
                    st.download_button("📥 Télécharger Devis", data=bytes(pdf_bytes), file_name=f"{num_devis}.pdf", mime="application/pdf")

        with tab_devis_bat:
            st.subheader("Devis Bâtiment")
            client_bat = st.text_input("Client", key="client_bat")
            titre_bat = st.text_input("Titre Projet", key="titre_bat")
            if st.button("📄 Générer Devis Bâtiment", type="primary"):
                if client_bat and titre_bat:
                    num_devis = f"DEV-BAT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    sections = [{"numero": "1", "titre": titre_bat, "items": [{"num": "1.1", "designation": "Prestation bâtiment", "unite": "Forfait", "qte": 1, "pu": 0}]}]
                    pdf_bytes = generer_pdf_devis_consulting(num_devis, "Bâtiment", client_bat, titre_bat, "", sections)
                    st.success(f"✅ Devis {num_devis} généré")
                    st.download_button("📥 Télécharger Devis", data=bytes(pdf_bytes), file_name=f"{num_devis}.pdf", mime="application/pdf")

if "👥 Utilisateurs" in tab_map:
    with tab_map["👥 Utilisateurs"]:
        st.markdown("## 👥 Gestion Utilisateurs")
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
