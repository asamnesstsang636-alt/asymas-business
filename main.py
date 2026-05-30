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

# LIT L'URL?module=Commerce ET OUVRE LE MODULE
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
#MainMenu, header,.stAppToolbar, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stHeader"], footer,.stDeployButton, [data-testid="stStatusWidget"] {display: none!important; visibility: hidden!important;}
h1, h2, h3 {color: #00ff41!important; font-size: 2.2rem!important; font-weight: 900!important; padding: 10px 0!important; border-bottom: 3px solid #00ff41!important; margin-bottom: 20px!important;}
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
        return list(test.data[0].keys()) if test.data else []
    except:
        return []

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
    txt = txt.replace('—', '-').replace('–', '-').replace('’', "'").replace('“', '"').replace('”', '"').replace('•', '-').replace('…', '...')
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
    y_pos += 10
    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(0, 102, 0)
    pdf.set_xy(10, y_pos)
    pdf.cell(0, 6, "Merci pour votre confiance! ASYMAS BUSINESS", ln=True, align="C")
    qr_data = f"ASYMAS BUSINESS\nFacture: {numero}\nType: {type_op}\nClient: {client}\nMontant: {montant:,.0f} {devise}"
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
    return bytes(pdf.output(dest='S'))

def creer_facture_auto(type_op, client, details, montant, devise="FC", details_list=None, tel="+243...", periode="", type_facture="Simple"):
    numero_facture = f"AS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if details_list is None:
        details_list = [{"nom": details, "qte": 1, "pu": montant}]
    pdf_bytes = generer_pdf_facture(numero_facture, type_op, client, details_list, montant, devise, tel, periode, type_facture)
    try:
        data_compta = {"type": "Revenu", "description": f"{type_op} - {client} - {details}", "montant": float(montant), "date": str(date.today()), "utilisateur": st.session_state.user_name, "categorie": str(type_op), "devise": str(devise), "numero_facture": str(numero_facture), "details": json.dumps(details_list)}
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

# === LOGIN : CHAMP ICI, CERCLE VERROUILLÉ ===
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

# === ACCUEIL : CERCLE CLIQUABLE APRÈS ACCÈS ===
if st.session_state.selected_module is None:

    # Détermine quels modules sont autorisés selon le rôle + perms
    perms = st.session_state.perms if isinstance(st.session_state.perms, dict) else {}
    authorized = {
        "Commerce": st.session_state.user_role == "PDG" or perms.get("commerce", False),
        "Auto": st.session_state.user_role == "PDG" or perms.get("automobile", False),
        "Factures": st.session_state.user_role == "PDG" or perms.get("factures", False),
        "Immo": st.session_state.user_role == "PDG" or perms.get("immobilier", False),
        "Stock": st.session_state.user_role == "PDG" or perms.get("stock", False),
        "Compta": st.session_state.user_role == "PDG" or perms.get("comptabilite", False),
    }

    def btn_html(module, angle, emoji, label):
        if authorized[module]:
            return f"""<button onclick="window.location.href='?module={module}'"
                style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate({angle}deg) translate(190px) rotate(-{angle}deg);
                width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;
                font-size:11px;font-weight:bold;color:#000;cursor:pointer;">{emoji}<br>{label}</button>"""
        else:
            return f"""<button disabled
                style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate({angle}deg) translate(190px) rotate(-{angle}deg);
                width:60px;height:60px;border:3px solid #555;border-radius:50%;background:#222;box-shadow:0 0 10px #555;
                font-size:11px;font-weight:bold;color:#666;cursor:not-allowed;opacity:0.4;">{emoji}<br>{label}</button>"""

    html_buttons = f"""
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
        {btn_html("Commerce", 90, "🏪", "Commerce")}
        {btn_html("Auto", 30, "🚚", "Auto")}
        {btn_html("Factures", -30, "🧾", "Factures")}
        {btn_html("Immo", -90, "🏠", "Immo")}
        {btn_html("Stock", -150, "📦", "Stock")}
        {btn_html("Compta", 150, "📊", "Compta")}
    </div>
    <style>@keyframes pulseRing{{0%,100%{{transform:translate(-50%,-50%) scale(1);opacity:0.7;}}50%{{transform:translate(-50%,-50%) scale(1.12);opacity:1;}}}}
    @keyframes pulseCart{{0%,100%{{transform:translate(-50%,-50%) scale(1);}}50%{{transform:translate(-50%,-50%) scale(1.18);}}}}
    @keyframes rotate{{from{{transform:translate(-50%,-50%) rotate(0deg);}}to{{transform:translate(-50%,-50%) rotate(360deg);}}}}</style>
    """
    components.html(html_buttons, height=700)

    if st.button("🚪 Déconnexion"):
        st.session_state.clear()
        st.rerun()
    table_map = {"Commerce": "articles", "Stock": "articles", "Immo": "biens", "Auto": "voitures", "Compta": "compta", "Factures": "factures_proforma"}
    df = load_table(table_map.get(st.session_state.selected_module, "articles"))
    st.dataframe(df, use_container_width=True)
