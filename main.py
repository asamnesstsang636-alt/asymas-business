import streamlit as st
import pandas as pd

class FLOKI:
    def __init__(self, supabase_client, dfs): pass
    def ask(self, q): return f"FLOKI: {q}"
    def notify_internal(self, m): return f"Notifié: {m}"

st.set_page_config(
    page_title="ASYMAS BUSINESS",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="auto"
)
st.markdown("""<meta name="mobile-web-app-capable" content="yes">""", unsafe_allow_html=True)

from supabase import create_client, Client
from datetime import date, datetime, timedelta
from fpdf import FPDF
import base64, io, qrcode, tempfile, os, json
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
        return list(test.data[0].keys()) if test.data else []
    except:
        return []

@st.cache_data(ttl=10)
def load_passwords():
    try:
        data = supabase.table("utilisateurs").select("nom,role,password,permissions,categories_autorisees").execute()
        passwords, perms = {}, {}
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
        return {"PDG": "tsang2024", "GERANTE": "asiya2024", "UTILISATEUR": "basam2024"}

def generer_qrcode(data_text):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=3, border=1)
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name)
    return temp_file.name

def safe_pdf_txt(txt):
    if txt is None or pd.isna(txt): return ""
    txt = str(txt).replace('—', '-').replace('–', '-').replace('’', "'").replace('“', '"').replace('”', '"')
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
    pdf.cell(15, 7, "Unite", 1, 0, 'C', True)
    pdf.cell(20, 7, "Qte", 1, 0, 'C', True)
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
        ingenieur, tel_ing, adresse_ing = "SAMY TSANGYA", "+243 995 105 623", "Beni, Nord-Kivu, RDC"
    else:
        ingenieur, tel_ing, adresse_ing = "ESDRAS TSANGYA", "+243 972 888 690", "Beni, Nord-Kivu, RDC | esdrastsangya@gmail.com"
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
        if "categorie" in colonnes_compta: data_compta["categorie"] = str(type_op)
        if "devise" in colonnes_compta: data_compta["devise"] = str(devise)
        if "numero_facture" in colonnes_compta: data_compta["numero_facture"] = str(numero_facture)
        if "details" in colonnes_compta: data_compta["details"] = json.dumps(details_list)
        supabase.table("compta").insert(data_compta).execute()
        st.toast(f"✅ Enregistré par {st.session_state.user_name}", icon="✅")
    except Exception as e:
        st.error("❌ ERREUR INSERTION COMPTA")
        st.code(repr(e))
    return numero_facture, pdf_bytes

def generer_excel_pro(df_data, titre="Releve Comptable", total_revenu=0, total_depense=0, solde=0):
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
        worksheet['A3'] = f'{titre.upper()} - Edite le {date.today().strftime("%d/%m/%Y")}'
        worksheet['A3'].font = Font(size=14, bold=True, color='FF6600')
        worksheet['A3'].alignment = Alignment(horizontal='center')
        worksheet.merge_cells('A4:F4')
        worksheet['A4'] = f'Total Revenus: {total_revenu:,.0f} FC | Total Depenses: {total_depense:,.0f} FC | Solde: {solde:,.0f} FC'
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

# === CSS HOLOGRAPHIQUE ASYMAS ===
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%); overflow-x: hidden;}
h1 {color: #00ff41!important; text-align: center; font-size: 3rem!important;
    text-shadow: 0 0 10px #00ff41, 0 0 30px #00ff41, 0 0 50px #00ccff; margin-bottom: 50px;
    animation: pulseNeon 2s ease-in-out infinite;}
@keyframes pulseNeon {0%, 100% {text-shadow: 0 0 10px #00ff41, 0 0 30px #00ff41;}
                      50% {text-shadow: 0 0 20px #00ff41, 0 0 60px #00ccff;}}
.login-circle {
    width: 380px;
    height: 380px;
    border-radius: 50%;
    border: 3px solid #00ff41;
    box-shadow: 0 0 40px #00ff41, inset 0 0 30px rgba(0,255,65,0.2);
    margin: 50px auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle, rgba(0,255,65,0.1) 0%, rgba(0,0,0,0.9) 70%);
    animation: rotateGlow 4s linear infinite;
    padding: 25px;
}
@keyframes rotateGlow {
    0% {box-shadow: 0 0 40px #00ff41, inset 0 0 30px rgba(0,255,65,0.2);}
    50% {box-shadow: 0 0 60px #00ccff, inset 0 0 40px rgba(0,204,255,0.3);}
    100% {box-shadow: 0 0 40px #00ff41, inset 0 0 30px rgba(0,255,65,0.2);}
}
.login-circle h2 {
    color: #00ff41;
    text-shadow: 0 0 10px #00ff41;
    margin-bottom: 15px;
    font-size: 1.5rem;
}
.login-circle img {
    width: 100px;
    height: 100px;
    margin-bottom: 15px;
    filter: drop-shadow(0 0 10px #00ff41);
}
div[data-testid="stMetricValue"] {color: #00ff41!important; text-shadow: 0 0 15px #00ff41;
    font-size: 2.8rem!important; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

passwords_db = load_passwords()
if 'user_role' not in st.session_state:
    st.session_state.user_role, st.session_state.user_name, st.session_state.user_perms, st.session_state.user_cats = None, None, {}, []

# === LOGIN HOLOGRAPHIQUE DANS LE CERCLE ===
if st.session_state.user_role is None:
    st.markdown('<div class="login-circle">', unsafe_allow_html=True)
    st.markdown("<h2>🔐 CONNEXION</h2>", unsafe_allow_html=True)

    silhouette_svg = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxjaXJjbGUgY3g9IjEyIiBjeT0iOCIgcj0iNCIgZmlsbD0iIzAwZmY0MSIgb3BhY2l0eT0iMC44Ii8+PHBhdGggZD0iTTQgMjB2LTJhNiA2IDAgMCAxIDEyIDB2MiIgc3Ryb2tlPSIjMDBmZjQxIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgb3BhY2l0eT0iMC44Ii8+PC9zdmc+"
    st.image(silhouette_svg)

    df_users_login = load_table("utilisateurs")
    options_login = ["-- Selectionner --"] + [f"{row['nom']} - {row['role']}" for _, row in df_users_login.iterrows()] if not df_users_login.empty else ["-- Selectionner --", "PDG TSANG", "Gerante ASIYA", "BASAM"]

    profil = st.selectbox("Utilisateur", options_login, label_visibility="collapsed", key="profil_holo")
    password = st.text_input("Mot de passe", type="password", key="pwd_holo", label_visibility="collapsed", placeholder="Mot de passe")

    if st.button("SE CONNECTER", use_container_width=True, type="primary", key="btn_login_holo"):
        if profil!= "-- Selectionner --":
            nom_connect = profil.split(" - ")[0]
            df_users_login = pd.DataFrame(supabase.table("utilisateurs").select("id, nom, role, password, permissions, categories_autorisees").execute().data)
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

# === RESTE DU CODE ===
if 'user_role' in st.session_state and st.session_state.user_role is not None:
    with st.sidebar:
        if 'theme_choisi' not in st.session_state: st.session_state.theme_choisi = "Sombre ASYMAS"
        theme = st.selectbox("🎨", ["Sombre ASYMAS","Bleu Pro","Vert Agri","Noir Luxe"], key="theme_choisi", label_visibility="collapsed")
        if st.button("🚪 Deconnexion", use_container_width=True):
            st.session_state.user_role=None; st.session_state.user_name=None; st.session_state.user_perms={}; st.session_state.user_cats=[]
            st.rerun()
else:
    st.stop()
# === AUTOMOBILE ===
with tabs[4]:
    if check_perm('automobile'):
        st.markdown("## 🚗 Automobile - Point de Vente")
        if 'panier_voiture' not in st.session_state: st.session_state.panier_voiture = []
        if 'vente_auto_finie' not in st.session_state: st.session_state.vente_auto_finie = False
        if 'pdf_auto' not in st.session_state: st.session_state.pdf_auto = None
        if 'num_fact_auto' not in st.session_state: st.session_state.num_fact_auto = None
        if 'client_auto_nom' not in st.session_state: st.session_state.client_auto_nom = ""
        if 'client_auto_tel' not in st.session_state: st.session_state.client_auto_tel = "+243..."
        if 'total_auto' not in st.session_state: st.session_state.total_auto = 0

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
                        if st.button("🛒 AJOUTER AU PANIER", type="primary", use_container_width=True, key="add_voiture_unique"):
                            existant = next((item for item in st.session_state.panier_voiture if item['id'] == int(v['id'])), None)
                            if existant:
                                if existant['qte'] + qte <= qte_max:
                                    existant['qte'] += qte; st.success(f"Panier mis à jour: {existant['qte']}x")
                                else: st.error(f"Stock insuffisant! Max dispo: {qte_max}")
                            else:
                                st.session_state.panier_voiture.append({
                                    "id": int(v['id']), "nom": f"{v['marque']} {v['modele']} {v.get('annee','')}",
                                    "pu": float(v['prix']), "qte": int(qte), "plaque": v.get('plaque',''),
                                    "qualite": v.get('qualite',''), "code_qr": v.get('code_qr',''), "stock_max": qte_max
                                })
                                st.success("Ajouté au panier"); st.rerun()
            with col_droite:
                st.subheader("🛒 Panier Voiture")
                total_voiture = 0
                if st.session_state.vente_auto_finie and st.session_state.pdf_auto:
                    st.success(f"✅ Vente validée - {st.session_state.total_auto:,.0f} $")
                    st.info(f"📄 Facture: {st.session_state.num_fact_auto}")
                    if st.session_state.pdf_auto:
                        st.download_button("📥 TÉLÉCHARGER LE PDF", data=bytes(st.session_state.pdf_auto),
                            file_name=f"{st.session_state.num_fact_auto}.pdf", mime="application/pdf", use_container_width=True, key="dl_facture_auto")
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
                    if st.button("Nouvelle Vente", use_container_width=True, key="new_vente_auto"):
                        st.session_state.panier_voiture = []; st.session_state.vente_auto_finie = False
                        st.session_state.pdf_auto = None; st.session_state.num_fact_auto = None
                        st.session_state.client_auto_nom = ""; st.session_state.client_auto_tel = "+243..."; st.rerun()
                elif not st.session_state.panier_voiture:
                    st.info("Panier vide")
                else:
                    for idx, item in enumerate(st.session_state.panier_voiture):
                        col1, col2, col3, col4 = st.columns([3,1,1,1])
                        col1.write(f"**{item['nom']}** | {item.get('qualite','')} | {item['plaque']}")
                        col2.write(f"Qté: {item['qte']}")
                        col3.write(f"{item['pu'] * item['qte']:,.2f} $")
                        if col4.button("❌", key=f"del_v_{idx}"):
                            st.session_state.panier_voiture.pop(idx); st.rerun()
                        total_voiture += item['pu'] * item['qte']
                    st.metric("💰 TOTAL VOITURE", f"{total_voiture:,.2f} $")
                    st.markdown(f"**Client:** {st.session_state.client_auto_nom}")
                    st.markdown(f"**Tel:** {st.session_state.client_auto_tel}")
                    if st.button("✅ FINALISER VENTE VOITURE", type="primary", use_container_width=True):
                        if st.session_state.client_auto_nom and st.session_state.panier_voiture:
                            try:
                                details_list = [{"nom": f"{item['nom']} | {item.get('qualite','')} | {item['plaque']}",
                                                 "qte": item['qte'], "pu": item['pu']} for item in st.session_state.panier_voiture]
                                details_text = " | ".join([f"{item['qte']}x {item['nom']} ({item.get('qualite','')})"
                                                           for item in st.session_state.panier_voiture])
                                num_fact, pdf_bytes = creer_facture_auto(
                                    "Vente Voiture", st.session_state.client_auto_nom, details_text,
                                    total_voiture, "$", details_list, st.session_state.client_auto_tel, "", "Proforma"
                                )
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
    else:
        st.info("🔒 Accès Automobile restreint - Contacte le PDG")
# === GESTION PARC ===
with tabs[5]:
    if check_perm('parc'):
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
                                try: km_val = int(float(km_val)) if km_val else 0
                                except: km_val = 0
                                new_km = st.number_input("KM", value=km_val, key=f"km_v_{row['id']}")
                                data_update["kilometrage"] = int(new_km)
                        with c3:
                            if "carburant" in colonnes_voitures:
                                carburant_options = ["Essence", "Diesel", "Hybride", "Électrique"]
                                carb_val = row.get('carburant','Essence')
                                new_carb = st.selectbox("Carburant", carburant_options,
                                    index=carburant_options.index(carb_val) if carb_val in carburant_options else 0,
                                    key=f"carb_v_{row['id']}")
                                data_update["carburant"] = str(new_carb)
                            if "boite" in colonnes_voitures:
                                boite_options = ["Manuelle", "Automatique"]
                                boite_val = row.get('boite','Manuelle')
                                new_boite = st.selectbox("Boîte", boite_options,
                                    index=boite_options.index(boite_val) if boite_val in boite_options else 0,
                                    key=f"boite_v_{row['id']}")
                                data_update["boite"] = str(new_boite)
                            if "prix" in colonnes_voitures:
                                new_prix = st.number_input("Prix $", value=float(row.get('prix',0)), key=f"prix_v_{row['id']}")
                                data_update["prix"] = float(new_prix)
                            if "statut" in colonnes_voitures:
                                statut_options = ["Disponible", "En réparation", "Réservée", "Vendue"]
                                statut_val = row.get('statut','Disponible')
                                new_statut = st.selectbox("Statut", statut_options,
                                    index=statut_options.index(statut_val) if statut_val in statut_options else 0,
                                    key=f"statut_v_{row['id']}")
                                data_update["statut"] = str(new_statut)
                        if "quantite" in colonnes_voitures:
                            new_qte = st.number_input("Stock", value=int(row.get('quantite',1)), min_value=0, key=f"qte_v_{row['id']}")
                            data_update["quantite"] = int(new_qte)
                        if "qualite" in colonnes_voitures:
                            qualite_options = ["Neuf", "Occasion", "Reconditionné"]
                            qualite_val = row.get('qualite','Neuf')
                            new_qualite = st.selectbox("Qualité", qualite_options,
                                index=qualite_options.index(qualite_val) if qualite_val in qualite_options else 0,
                                key=f"qual_v_{row['id']}")
                            data_update["qualite"] = str(new_qualite)
                        if "code_qr" in colonnes_voitures:
                            new_code_qr = st.text_input("Code QR", value=row.get('code_qr',''), key=f"qr_v_{row['id']}")
                            data_update["code_qr"] = str(new_code_qr)
                        c1, c2 = st.columns(2)
                        if c1.button("✏️ Modifier", key=f"mod_v_parc_{row['id']}", use_container_width=True):
                            try:
                                supabase.table("voitures").update(data_update).eq("id", int(row['id'])).execute()
                                st.success("Modifié"); st.cache_data.clear(); st.rerun()
                            except Exception as e:
                                st.error("Erreur modif"); st.code(repr(e))
                        if st.session_state.user_role == "PDG" or perms.get('supprimer', False):
                            if c2.button("🗑️ Supprimer", key=f"del_v_parc_{row['id']}", use_container_width=True):
                                try:
                                    supabase.table("voitures").delete().eq("id", int(row['id'])).execute()
                                    st.success("Supprimé"); st.cache_data.clear(); st.rerun()
                                except Exception as e:
                                    st.error("Erreur suppression"); st.code(repr(e))

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
                    qte_perte_v = st.number_input("Quantité endommagée", min_value=1,
                        max_value=int(voiture_dict[voiture_choisie].get('quantite',1)) if voiture_choisie else 1)
                with col2:
                    motif_perte_v = st.selectbox("Type de dégât", ["Accident", "Vol", "Incendie", "Panne moteur", "Dégât carrosserie", "Pneus crevés", "Autre"])
                    detail_perte_v = st.text_area("Détails du dégât", placeholder="Ex: Pare-choc avant enfoncé + phare cassé")
                    responsable_v = st.text_input("Déclaré par", value=st.session_state.user_name, key="resp_v")
                if voiture_choisie:
                    voiture_data = voiture_dict[voiture_choisie]
                    valeur_perte_v = qte_perte_v * float(voiture_data.get('prix', 0))
                    st.error(f"💸 Valeur de la perte : {valeur_perte_v:,.2f} $")
                if st.button("🚨 ENREGISTRER LE DÉGÂT", type="primary", use_container_width=True, key="btn_perte_voiture"):
                    if voiture_choisie and qte_perte_v > 0:
                        voiture_data = voiture_dict[voiture_choisie]
                        try:
                            nouveau_stock_v = int(voiture_data.get('quantite', 1)) - qte_perte_v
                            nouveau_statut = "Vendue" if nouveau_stock_v == 0 else voiture_data.get('statut', 'Disponible')
                            supabase.table('voitures').update({
                                "quantite": nouveau_stock_v, "statut": nouveau_statut
                            }).eq("id", int(voiture_data['id'])).execute()
                            supabase.table('mouvements_stock').insert({
                                "article_id": int(voiture_data['id']),
                                "article_nom": f"{voiture_data['marque']} {voiture_data['modele']} - {voiture_data.get('plaque','')}",
                                "type": "PERTE_VOITURE", "quantite": -int(qte_perte_v),
                                "motif": f"{motif_perte_v} - {detail_perte_v}", "valeur": float(valeur_perte_v),
                                "created_by": responsable_v, "created_at": datetime.now().isoformat()
                            }).execute()
                            st.success(f"✅ Dégât enregistré. Nouveau stock {voiture_data['marque']} {voiture_data['modele']}: {nouveau_stock_v}")
                            st.cache_data.clear(); st.rerun()
                        except Exception as e:
                            st.error("Erreur enregistrement dégât"); st.code(repr(e))
            st.divider()
            st.subheader("📋 Historique Dégâts/Pertes Voitures")
            try: pertes_voitures = supabase.table('mouvements_stock').select("*").eq("type", "PERTE_VOITURE").order("created_at", desc=True).limit(20).execute().data
            except: pertes_voitures = []
            if not pertes_voitures:
                st.info("Aucun dégât enregistré")
            else:
                total_pertes_voitures = sum(p.get('valeur', 0) for p in pertes_voitures)
                st.metric("💸 TOTAL PERTES VOITURES", f"{total_pertes_voitures:,.2f} $")
                for p in pertes_voitures:
                    with st.expander(f"🔴 {p.get('article_nom')} - {abs(p.get('quantite',0))} - {p.get('created_at','')[:10]}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Qté perdue:** {abs(p.get('quantite', 0))}")
                            st.write(f"**Valeur:** {p.get('valeur', 0):,.2f} $")
                        with col2:
                            st.write(f"**Motif:** {p.get('motif', 'N/A')}")
                            st.write(f"**Par:** {p.get('created_by', 'N/A')}")
                        with col3:
                            if st.session_state.user_role == "PDG":
                                if st.button("🗑️ Supprimer", key=f"del_perte_voiture_{p.get('id')}"):
                                    supabase.table('mouvements_stock').delete().eq("id", p.get('id')).execute(); st.rerun()
    else:
        st.info("🔒 Accès Gestion Parc restreint - Contacte le PDG")

# === COMPTABILITÉ ===
with tabs[6]:
    if check_perm('comptabilite'):
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
                        st.success("Opération ajoutée"); st.cache_data.clear(); st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout"); st.code(repr(e))
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
                        if 'utilisateur' in df_cat.columns: colonnes_affiche.append('utilisateur')
                        st.dataframe(df_cat[colonnes_affiche], use_container_width=True, hide_index=True)
                        col_dl1, col_dl2 = st.columns(2)
                        excel_bytes_cat = generer_excel_pro(
                            df_cat, f"Releve {cat} {date_debut}-{date_fin}",
                            df_cat[df_cat['type']=='Revenu']['montant'].sum(),
                            df_cat[df_cat['type']=='Dépense']['montant'].sum(),
                            df_cat[df_cat['type']=='Revenu']['montant'].sum() - df_cat[df_cat['type']=='Dépense']['montant'].sum()
                        )
                        safe_cat = str(cat).replace(" ", "_").replace("/", "_")
                        col_dl1.download_button(
                            label=f"📥 {cat} - EXCEL", data=excel_bytes_cat,
                            file_name=f"Compta_{safe_cat}_{date_debut}_{date_fin}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True, key=f"dl_excel_compta_{safe_cat}_{date_debut}_{filtre_nom}"
                        )
                        pdf_cat = FPDF(); pdf_cat.add_page(); pdf_cat.set_fill_color(20, 50, 40)
                        pdf_cat.rect(0, 0, 210, 35, 'F'); pdf_cat.set_text_color(255, 255, 255)
                        pdf_cat.set_font("Arial", "B", 20); pdf_cat.set_xy(10, 8); pdf_cat.cell(0, 10, "ASYMAS BUSINESS", ln=True)
                        pdf_cat.set_font("Arial", "", 9); pdf_cat.set_xy(10, 16)
                        pdf_cat.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
                        pdf_cat.set_font("Arial", "B", 10); pdf_cat.set_xy(150, 8)
                        filtre_txt = f"Filtre: {filtre_nom}" if filtre_nom else "Tous"
                        pdf_cat.cell(50, 6, f"Periode: {date_debut} au {date_fin}", ln=True, align="R")
                        pdf_cat.set_xy(150, 14); pdf_cat.cell(50, 6, filtre_txt, ln=True, align="R"); pdf_cat.ln(15)
                        pdf_cat.set_text_color(0, 0, 0); pdf_cat.set_fill_color(255, 204, 0)
                        pdf_cat.set_font("Arial", "B", 14)
                        pdf_cat.cell(0, 10, f"RELEVE COMPTABLE - {safe_pdf_txt(cat).upper()}", ln=True, fill=True); pdf_cat.ln(5)
                        pdf_cat.set_font("Arial", "B", 11)
                        pdf_cat.cell(0, 8, f"Total FC: {total_cat_fc:,.0f} | USD: {total_cat_usd:,.0f} | EUR: {total_cat_eur:,.0f}", ln=True); pdf_cat.ln(3)
                        pdf_cat.set_font("Arial", "B", 9)
                        pdf_cat.cell(20, 7, "Date", 1); pdf_cat.cell(20, 7, "Type", 1); pdf_cat.cell(70, 7, "Description", 1)
                        pdf_cat.cell(25, 7, "Montant", 1); pdf_cat.cell(15, 7, "Dev", 1); pdf_cat.cell(30, 7, "Utilisateur", 1, ln=True)
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
                            except: continue
                        pdf_bytes_cat = bytes(pdf_cat.output(dest='S'))
                        col_dl2.download_button(
                            label=f"📥 {cat} - PDF", data=pdf_bytes_cat,
                            file_name=f"Compta_{safe_cat}_{date_debut}_{date_fin}.pdf",
                            mime="application/pdf", use_container_width=True,
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
    else:
        st.info("🔒 Accès Comptabilité restreint - Contacte le PDG")

# === FACTURES ===
with tabs[7]:
    if check_perm('factures'):
        st.markdown("## 📄 Factures - Relevé par Catégorie")
        if df_compta.empty:
            st.info("Aucune opération")
        else:
            df_compta_sorted = df_compta.sort_values('date', ascending=False)
            col_f1, col_f2, col_f3 = st.columns(3)
            date_debut = col_f1.date_input("📅 Date début", value=date.today() - timedelta(days=30), key="date_debut_fact")
            date_fin = col_f2.date_input("📅 Date fin", value=date.today(), key="date_fin_fact")
            col_f4, col_f5 = st.columns(2)
            if st.session_state.user_role!= "PDG":
                cats_user = st.session_state.get('user_cats', [])
                if cats_user and "Toutes" not in cats_user:
                    df_compta_sorted = df_compta_sorted[df_compta_sorted['categorie'].isin(cats_user)]
                elif not cats_user:
                    st.error("⛔ Aucune catégorie autorisée. Contacte le PDG."); st.stop()
            categories_fact = ["Toutes"] + list(df_compta_sorted.get('categorie', pd.Series(dtype=str)).dropna().unique())
            filtre_cat_fact = col_f4.selectbox("📂 Filtrer par Catégorie", categories_fact, key="filtre_cat_fact")
            filtre_client_fact = col_f5.text_input("👤 Nom Client contient", placeholder="Tape un nom...", key="filtre_client_fact")
            df_filtre_fact = df_compta_sorted[(df_compta_sorted['date'] >= str(date_debut)) & (df_compta_sorted['date'] <= str(date_fin))]
            if filtre_cat_fact!= "Toutes": df_filtre_fact = df_filtre_fact[df_filtre_fact.get('categorie', '') == filtre_cat_fact]
            if filtre_client_fact: df_filtre_fact = df_filtre_fact[df_filtre_fact['description'].str.contains(filtre_client_fact, case=False, na=False)]
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
                            col_a, col_b, col_c, col_d, col_e, col_f, col_g = st.columns([1.2,0.8,2.5,1,0.8,0.5,0.5])
                            col_a.write(f"**{row.get('date','')}**")
                            col_b.write(f"{row.get('type','')}")
                            col_c.write(f"{row.get('description','')}")
                            col_d.write(f"**{row.get('montant',0):,.0f} {row.get('devise','FC')}**")
                            col_e.write(f"👤 {row.get('utilisateur','N/A')}")
                            if st.session_state.user_role == "PDG":
                                if col_g.button("🗑️", key=f"del_compta_{row['id']}", help="Supprimer"):
                                    supabase.table("compta").delete().eq("id", int(row['id'])).execute()
                                    st.success("Facture supprimée"); st.cache_data.clear(); st.rerun()
                            else: col_g.write("")
                            try:
                                details_list = []
                                if row.get('details') and str(row.get('details'))!= 'nan':
                                    details_list = json.loads(row['details'])
                                else:
                                    details_list = [{"nom": row.get('description',''), "qte": 1, "pu": row.get('montant',0)}]
                                client_nom = row.get('description', '').split(' - ')[1] if ' - ' in row.get('description','') else 'Client'
                                pdf_bytes = generer_pdf_facture(
                                    row.get('numero_facture', f"FACT-{row['id']}"),
                                    row.get('categorie', 'Facture'), client_nom, details_list,
                                    row.get('montant',0), row.get('devise','FC'), "+243...", ""
                                )
                                col_f.download_button(
                                    "📥", data=pdf_bytes,
                                    file_name=f"{row.get('numero_facture', f'FACT-{row['id']}')}.pdf",
                                    mime="application/pdf", key=f"dl_fact_{row['id']}", help="Télécharger PDF"
                                )
                                pdf_b64 = base64.b64encode(pdf_bytes).decode()
                                col_g.markdown(f"""
                                    <button onclick="printPDF_{row['id']}()" style="width:100%; padding:2px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; font-size:16px;">🖨️</button>
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
                                col_f.write("❌"); col_g.write("❌")
    else:
        st.info("🔒 Accès Factures restreint - Contacte le PDG")

# === DEVIS ===
with tabs[8]:
    if check_perm('devis_batiment') or check_perm('devis_industriel') or st.session_state.user_role == "PDG":
        st.markdown("## 📋 Devis Consulting - Industriel & Bâtiment")
        if 'devis_sections' not in st.session_state: st.session_state.devis_sections = []
        if 'devis_bat_sections' not in st.session_state: st.session_state.devis_bat_sections = []
        if 'devis_bat_titre' not in st.session_state: st.session_state.devis_bat_titre = "DEVIS DE MATERIAUX POUR LA CONSTRUCTION DE CLOTURE DE 23.5m"
        if 'devis_bat_main_oeuvre' not in st.session_state: st.session_state.devis_bat_main_oeuvre = 1173.0
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
                        {"numero": "A", "titre": "ELECTRICITE", "items": [
                            {"type": "cable", "designation": "Câble 2.5mm²", "marque": "Nexans", "section": "2.5mm²", "longueur": 100, "unite": "m", "qte": 1, "pu": 1.2},
                            {"type": "interrupteur", "designation": "Interrupteur", "marque": "Legrand", "couleur": "Blanc", "qualite": "Standard", "unite": "pc", "qte": 5, "pu": 3.5},
                            {"type": "autre", "designation": "Goulotte 25x16", "unite": "m", "qte": 10, "pu": 2.5, "spec": ""}
                        ]}
                    ]
                total_general_ind = 0
                col_h1, col_h2, col_h3, col_h4, col_h5, col_h6, col_h7, col_h8 = st.columns([0.5, 3, 1.5, 1.5, 1, 1, 1, 0.5])
                col_h1.markdown("**N°**"); col_h2.markdown("**Désignation**"); col_h3.markdown("**Type/Marque**")
                col_h4.markdown("**Spécifications**"); col_h5.markdown("**Qté**"); col_h6.markdown("***PU***"); col_h7.markdown("***Total***"); col_h8.markdown("")
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
                    if st.button("➕ Section", key="add_section_ind", use_container_width=True):
                        if new_section_titre:
                            st.session_state.devis_sections.append({"numero": new_section_num, "titre": new_section_titre, "items": []})
                            st.rerun()
                st.divider()
                main_oeuvre = st.number_input("👷 Main d'oeuvre", min_value=0.0, key="mo_devis_ind")
                cout_total_ind = total_general_ind + main_oeuvre
                st.metric("COUT TOTAL DU PROJET", f"{cout_total_ind:,.2f} {devise_devis}")
                if st.button("📄 GÉNÉRER DEVIS PDF", type="primary", use_container_width=True, key="gen_devis_ind"):
                    if client_devis and titre_devis and st.session_state.devis_sections:
                        numero_devis = f"DEV-IND-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        try:
                            data_devis = {
                                "numero": numero_devis, "type": "Industriel", "client": client_devis,
                                "telephone": tel_client_devis, "titre": titre_devis, "parcelle": parcelle_devis,
                                "localisation": localisation_devis, "sections": st.session_state.devis_sections,
                                "main_oeuvre": main_oeuvre, "total": cout_total_ind, "devise": devise_devis,
                                "created_by": st.session_state.user_name, "created_at": datetime.now().isoformat()
                            }
                            supabase.table('devis').insert(data_devis).execute()
                            st.success(f"✅ Devis enregistré : {numero_devis}")
                            st.session_state.devis_sections = []
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur enregistrement"); st.code(repr(e))
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
                                        use_container_width=True
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
                                    if st.button("🗑️ Supprimer", key=f"del_ind_{numero}", use_container_width=True):
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
                        {"numero": "I", "titre": "Installation chantier / Demolitions", "items": [
                            {"num": "", "designation": "Installationchantier", "unite": "ff", "qte": 1, "pu": 200},
                            {"num": "", "designation": "Demolitions", "unite": "ff", "qte": 1, "pu": 70}
                        ]},
                        {"numero": "II", "titre": "fondation", "items": [
                            {"num": "1", "designation": "moellon", "unite": "Canters", "qte": 9, "pu": 50},
                            {"num": "2", "designation": "sable", "unite": "Canters", "qte": 4, "pu": 40},
                            {"num": "3", "designation": "ciment", "unite": "sac", "qte": 23, "pu": 13.5},
                            {"num": "4", "designation": "gravier", "unite": "Canters", "qte": 3, "pu": 80},
                            {"num": "5", "designation": "armature de 10", "unite": "pièce", "qte": 9, "pu": 9},
                            {"num": "", "designation": "armature de 8", "unite": "pièce", "qte": 4, "pu": 8},
                            {"num": "6", "designation": "armature de 6", "unite": "pièce", "qte": 12, "pu": 3.5},
                            {"num": "7", "designation": "Fil à ligature", "unite": "kg", "qte": 16, "pu": 2.5}
                        ]},
                        {"numero": "III", "titre": "Élévation de mur et corniche", "items": [
                            {"num": "1", "designation": "bloc ciment", "unite": "pièce", "qte": 987, "pu": 1},
                            {"num": "2", "designation": "sable", "unite": "Canters", "qte": 5, "pu": 40},
                            {"num": "3", "designation": "ciment", "unite": "sac", "qte": 15, "pu": 13.5},
                            {"num": "4", "designation": "gravier", "unite": "Canters", "qte": 0.5, "pu": 70},
                            {"num": "5", "designation": "Barre Corniche de6", "unite": "pièce", "qte": 8, "pu": 3},
                            {"num": "6", "designation": "Fil à ligature", "unite": "kg", "qte": 6, "pu": 2}
                        ]},
                        {"numero": "IV", "titre": "Coffrage Colonne, Cornice et Socle", "items": [
                            {"num": "1", "designation": "socle et longrine", "unite": "pièce", "qte": 8, "pu": 7},
                            {"num": "2", "designation": "Colonne", "unite": "pièce", "qte": 18, "pu": 7},
                            {"num": "3", "designation": "Corniche", "unite": "pièce", "qte": 6, "pu": 7},
                            {"num": "4", "designation": "clous de8", "unite": "kg", "qte": 15, "pu": 2},
                            {"num": "5", "designation": "clous de10", "unite": "kg", "qte": 10, "pu": 2}
                        ]},
                        {"numero": "V", "titre": "Finissage", "items": [
                            {"num": "", "designation": "ciment", "unite": "sac", "qte": 20, "pu": 13.5},
                            {"num": "", "designation": "sable", "unite": "Canters", "qte": 7, "pu": 40}
                        ]}
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
                    if st.button("➕ Section", key="add_section_bat", use_container_width=True):
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
                    if st.button("📄 GÉNÉRER DEVIS PDF", type="primary", use_container_width=True, key="gen_devis_bat"):
                        if client_devis_bat and st.session_state.devis_bat_titre:
                            numero_devis = f"DEV-BAT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            try:
                                data_devis = {
                                    "numero": numero_devis, "type": "Bâtiment", "client": client_devis_bat,
                                    "telephone": tel_client_devis_bat, "titre": st.session_state.devis_bat_titre,
                                    "parcelle": parcelle_devis_bat, "localisation": localisation_devis_bat,
                                    "sections": st.session_state.devis_bat_sections,
                                    "main_oeuvre": st.session_state.devis_bat_main_oeuvre,
                                    "total": cout_total, "devise": devise_devis_bat,
                                    "created_by": st.session_state.user_name, "created_at": datetime.now().isoformat()
                                }
                                supabase.table('devis').insert(data_devis).execute()
                                st.success(f"✅ Devis enregistré : {numero_devis}")
                                st.cache_data.clear()
                            except Exception as e:
                                st.error("Erreur enregistrement"); st.code(repr(e)); st.stop()
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
                            use_container_width=True,
                            key="dl_devis_bat"
                        )
                with col_btn3:
                    if st.button("🔄 Réinitialiser", key="reset_devis_bat", use_container_width=True):
                        st.session_state.devis_bat_sections = []
                        if 'pdf_devis_bat' in st.session_state: del st.session_state.pdf_devis_bat
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

    else:
        st.info("🔒 Accès Utilisateurs restreint - Contacte le PDG")

# FLOKI
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
                                
                            
