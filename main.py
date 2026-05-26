import streamlit as st
import pandas as pd
st.set_page_config(
    page_title="ASYMAS BUSINESS",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CSS SIDEBAR ICÔNES + TITRE COURBÉ ===
st.markdown("""
<style>
/* Sidebar fine 70px */
section[data-testid="stSidebar"] {
    width: 70px!important; min-width: 70px!important;
    background: #0a0d14!important; border-right: 1px solid #2a3142;
    padding-top: 15px;
}
/* Cache le texte, garde les icônes */
section[data-testid="stSidebar"] label {font-size: 0!important;}
section[data-testid="stSidebar"] label div {
    font-size: 24px!important; text-align: center; padding: 14px 0; color: #666;
}
/* Icône active en vert fluo */
section[data-testid="stSidebar"] [role="radiogroup"] > div > div[data-selected="true"] {
    color: #00ff88!important; background: rgba(0,255,136,0.12)!important;
    border-left: 3px solid #00ff88;
}
/* Fond global */
.stApp {background: #0a0d14; color: #fff;}
/* Titre ASYMAS courbé */
.title-curved {
    font-size: 42px; font-weight: 800; text-align: center;
    background: linear-gradient(90deg, #00d4ff, #ff00ff, #00ff88);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: 8px; margin: 20px 0 30px 0;
    transform: perspective(300px) rotateX(10deg);
}
h1, h2, h3 {
    color: #00ff41!important; font-weight: 900!important;
    border-bottom: 3px solid #00ff41!important; margin-bottom: 20px!important;
}
.stButton>button {background-color: #00ff41!important; color: black!important; font-weight: bold; border: none;}
#MainMenu, header, footer {visibility: hidden!important;}
</style>
""", unsafe_allow_html=True)

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
        st.toast(f"Enregistre par {st.session_state.user_name}", icon="OK")
    except Exception as e:
        st.error("ERREUR INSERTION COMPTA")
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

# === CHARGEMENT DONNEES ===
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

# === CONNEXION ===
passwords_db = load_passwords()
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.session_state.user_perms = {}
    st.session_state.user_cats = []

if st.session_state.user_role is None:
    st.markdown("# ASYMAS BUSINESS - CONNEXION")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("### Choisissez votre profil :")
        df_users_login = load_table("utilisateurs")
        if not df_users_login.empty:
            options_login = ["-- Selectionner --"] + [f"{row['nom']} - {row['role']}" for _, row in df_users_login.iterrows()]
        else:
            options_login = ["-- Selectionner --", "PDG TSANG", "Gerante ASIYA", "BASAM"]
        profil = st.selectbox("Utilisateur", options_login)
        password = st.text_input("Mot de passe", type="password", key="pwd")
        if st.button("SE CONNECTER", width="stretch", type="primary"):
            if profil!= "-- Selectionner --":
                nom_connect = profil.split(" - ")[0]
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

# === TITRE COURBE + SIDEBAR ICÔNES ===
st.markdown('<div class="title-curved">ASYMAS</div>', unsafe_allow_html=True)
st.markdown(f"### {st.session_state.user_name} - Agriculture • Commerce • Immobilier • Automobile")

perms = st.session_state.user_perms
if isinstance(perms, str):
    try: perms = json.loads(perms)
    except: perms = {}

with st.sidebar:
    st.markdown("<div style='text-align:center;font-size:26px;color:#00ff88'>⚡</div>", unsafe_allow_html=True)
    st.markdown("---")
    nav = {}
    if st.session_state.user_role == "PDG" or perms.get('dashboard', True): nav["📊"] = "Dashboard"
    if st.session_state.user_role == "PDG" or perms.get('commerce', True): nav["🛍️"] = "Commerce"
    if st.session_state.user_role == "PDG" or perms.get('stock', False): nav["📦"] = "Gestion Stock"
    if st.session_state.user_role == "PDG" or perms.get('immobilier', False): nav["🏠"] = "Immobilier"
    if st.session_state.user_role == "PDG" or perms.get('automobile', False): nav["🚗"] = "Automobile"
    if st.session_state.user_role == "PDG" or perms.get('parc', False): nav["🚘"] = "Gestion Parc"
    if st.session_state.user_role == "PDG" or perms.get('comptabilite', False): nav["💰"] = "Comptabilite"
    if st.session_state.user_role == "PDG" or perms.get('factures', False): nav["📄"] = "Factures"
    if st.session_state.user_role == "PDG" or perms.get('devis_industriel', False) or perms.get('devis_batiment', False): nav["📋"] = "Devis"
    if st.session_state.user_role == "PDG" or perms.get('users', False): nav["👥"] = "Utilisateurs"
    if not nav: nav = {"📊": "Dashboard", "🛍️": "Commerce"}
    menu = nav[st.radio("", list(nav.keys()), label_visibility="collapsed", key="nav")]
    st.markdown("---")
    if st.button("🚪", use_container_width=True):
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.session_state.user_perms = {}
        st.session_state.user_cats = []
        st.rerun()

# === PAGES ===
if menu == "Dashboard":
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏠 Biens", len(df_biens))
    col2.metric("📦 Articles", len(df_articles))
    col3.metric("🚗 Voitures", len(df_voitures))
    if not df_compta.empty and 'type' in df_compta.columns and 'montant' in df_compta.columns:
        revenus = df_compta[df_compta['type']=='Revenu']['montant'].sum()
        col4.metric("💰 Revenus", f"{revenus:,.0f} FC")
    else:
        col4.metric("💰 Revenus", "0 FC")

elif menu == "Commerce":
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

elif menu == "Gestion Stock":
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

elif menu == "Immobilier":
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

elif menu == "Automobile":
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

elif menu == "Gestion Parc":
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
                        with c2:
                            new_plaque = st.text_input("Plaque", value=row.get('plaque',''), key=f"plaque_v_{row['id']}")
                            new_couleur = st.text_input("Couleur", value=row.get('couleur',''), key=f"coul_v_{row['id']}")
                            new_km = st.number_input("Kilométrage", value=int(row.get('kilometrage',0)), key=f"km_v_{row['id']}")
                        with c3:
                            new_prix = st.number_input("Prix $", value=float(row.get('prix',0)), key=f"prix_v_{row['id']}")
                            new_quantite = st.number_input("Quantité", value=int(row.get('quantite',1)), key=f"qt_v_{row['id']}")
                            new_statut = st.selectbox("Statut", ["Disponible","En réparation","Réservée","Vendue"], 
                                                      index=["Disponible","En réparation","Réservée","Vendue"].index(row.get('statut','Disponible')), 
                                                      key=f"stat_v_{row['id']}")
                        
                        c1, c2 = st.columns(2)
                        if c1.button("✏️ Modifier", key=f"mod_v_{row['id']}", width="stretch"):
                            try:
                                data_update = {
                                    "marque": str(new_marque), "modele": str(new_modele), "annee": str(new_annee),
                                    "plaque": str(new_plaque), "couleur": str(new_couleur), "kilometrage": int(new_km),
                                    "prix": float(new_prix), "quantite": int(new_quantite), "statut": str(new_statut)
                                }
                                supabase.table("voitures").update(data_update).eq("id", int(row['id'])).execute()
                                st.success("Modifié")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur modif")
                                st.code(repr(e))
                        if st.session_state.user_role == "PDG":
                            if c2.button("🗑️ Supprimer", key=f"del_v_{row['id']}", width="stretch"):
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
            voitures_dispo = df_voitures[df_voitures['quantite'] > 0].copy() if not df_voitures.empty else pd.DataFrame()
            if voitures_dispo.empty:
                st.warning("Aucune voiture en stock")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    voiture_dict = {f"{v['marque']} {v['modele']} - {v.get('plaque','')}": v for _, v in voitures_dispo.iterrows()}
                    voiture_choisie = st.selectbox("Voiture endommagée", list(voiture_dict.keys()))
                    qte_perte = st.number_input("Quantité perdue", min_value=1, max_value=int(voiture_dict[voiture_choisie]['quantite']) if voiture_choisie else 1)
                with col2:
                    motif_perte = st.selectbox("Motif", ["Accident","Vol","Panne moteur","Casse","Autre"])
                    detail_perte = st.text_area("Détails")
                    responsable = st.text_input("Déclaré par", value=st.session_state.user_name)
                
                if voiture_choisie:
                    voiture_data = voiture_dict[voiture_choisie]
                    valeur_perte = qte_perte * float(voiture_data.get('prix', 0))
                    st.error(f"💸 Valeur de la perte : {valeur_perte:,.0f} $")
                
                if st.button("🚨 ENREGISTRER LA PERTE VOITURE", type="primary", width="stretch"):
                    if voiture_choisie and qte_perte > 0:
                        voiture_data = voiture_dict[voiture_choisie]
                        try:
                            nouveau_stock = int(voiture_data['quantite']) - qte_perte
                            supabase.table('voitures').update({"quantite": nouveau_stock, "statut": "Vendue" if nouveau_stock==0 else "Disponible"}).eq("id", int(voiture_data['id'])).execute()
                            supabase.table('mouvements_stock').insert({
                                "article_id": int(voiture_data['id']),
                                "article_nom": f"{voiture_data['marque']} {voiture_data['modele']}",
                                "type": "PERTE",
                                "quantite": -int(qte_perte),
                                "motif": f"{motif_perte} - {detail_perte}",
                                "valeur": float(valeur_perte),
                                "created_by": responsable,
                                "created_at": datetime.now().isoformat()
                            }).execute()
                            st.success(f"✅ Perte enregistrée. Nouveau stock: {nouveau_stock}")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur enregistrement perte")
                            st.code(repr(e))

elif menu == "Comptabilite":
    st.markdown("## 💰 Comptabilité ASYMAS")
    col1, col2, col3 = st.columns(3)
    if not df_compta.empty and 'type' in df_compta.columns and 'montant' in df_compta.columns:
        total_revenus = df_compta[df_compta['type']=='Revenu']['montant'].sum()
        total_depenses = df_compta[df_compta['type']=='Depense']['montant'].sum()
        solde = total_revenus - total_depenses
    else:
        total_revenus = total_depenses = solde = 0
    
    col1.metric("💰 Revenus", f"{total_revenus:,.0f} FC")
    col2.metric("💸 Dépenses", f"{total_depenses:,.0f} FC")
    col3.metric("📊 Solde", f"{solde:,.0f} FC", delta=f"{solde:,.0f}")

    tab_releve, tab_ajout_ecriture, tab_export = st.tabs(["📊 Relevé", "➕ Ajouter", "📥 Export"])

    with tab_releve:
        if df_compta.empty:
            st.info("Aucune écriture comptable")
        else:
            st.dataframe(df_compta[['date','type','categorie','description','montant','devise','utilisateur']], 
                         use_container_width=True, hide_index=True)

    with tab_ajout_ecriture:
        with st.form("form_ecriture", clear_on_submit=True):
            c1, c2 = st.columns(2)
            type_ecr = c1.selectbox("Type", ["Revenu","Depense"])
            categorie = c2.text_input("Catégorie")
            description = st.text_input("Description")
            c1, c2, c3 = st.columns(3)
            montant = c1.number_input("Montant", min_value=0.0)
            devise = c2.selectbox("Devise", ["FC","$"])
            date_ecr = c3.date_input("Date", value=date.today())
            if st.form_submit_button("💾 Enregistrer"):
                try:
                    supabase.table("compta").insert({
                        "type": type_ecr,
                        "categorie": str(categorie),
                        "description": str(description),
                        "montant": float(montant),
                        "devise": str(devise),
                        "date": str(date_ecr),
                        "utilisateur": st.session_state.user_name
                    }).execute()
                    st.success("Ecriture enregistrée")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error("Erreur ajout")
                    st.code(repr(e))

    with tab_export:
        if not df_compta.empty:
            excel_data = generer_excel_pro(df_compta, "Releve Comptable ASYMAS", total_revenus, total_depenses, solde)
            st.download_button(
                "📥 Télécharger Excel Complet",
                data=excel_data,
                file_name=f"Releve_Compta_ASYMAS_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch"
            )

elif menu == "Factures":
    st.markdown("## 📄 Historique Factures & Proforma")
    if df_factures.empty:
        st.info("Aucune facture générée")
    else:
        st.dataframe(df_factures, use_container_width=True, hide_index=True)

elif menu == "Devis":
    st.markdown("## 📋 Devis Consulting")
    tab_indus, tab_bat = st.tabs(["🏭 Devis Industriel", "🏗️ Devis Bâtiment"])
    
    with tab_indus:
        st.info("Module Devis Industriel - A compléter selon ton besoin")
    
    with tab_bat:
        st.info("Module Devis Bâtiment - A compléter selon ton besoin")

elif menu == "Utilisateurs":
    st.markdown("## 👥 Gestion Utilisateurs")
    if st.session_state.user_role == "PDG":
        if not df_utilisateurs.empty:
            st.dataframe(df_utilisateurs[['nom','role','categories_autorisees']], use_container_width=True, hide_index=True)
        else:
            st.info("Aucun utilisateur")
    else:
        st.warning("Accès réservé au PDG")
                    
                
