import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import date, datetime, timedelta
from fpdf import FPDF
import tempfile, os, json, qrcode, base64, io
from PIL import Image
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from streamlit_qrcode_scanner import qrcode_scanner
from supabase import create_client, Client

# === CONFIG PAGE ===
st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide", initial_sidebar_state="auto")
st.markdown("""<meta name="mobile-web-app-capable" content="yes">""", unsafe_allow_html=True)

# === SUPABASE ===
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === SESSION STATE ===
for k, v in [('logged_in', False), ('user_role', ""), ('user_name', ""), ('perms', {}),
             ('selected_module', None), ('user_cats', []), ('devis_sections', []),
             ('devis_bat_sections', []), ('devis_bat_titre', "DEVIS DE MATERIAUX POUR LA CONSTRUCTION DE CLOTURE DE 23.5m"),
             ('devis_bat_main_oeuvre', 1173.0)].items():
    if k not in st.session_state:
        st.session_state[k] = v

if 'module' in st.query_params and st.session_state.selected_module is None:
    st.session_state.selected_module = st.query_params['module']
    st.rerun()

# === CSS ===
st.markdown("""
<style>
.block-container{padding:0!important;max-width:100%!important;}
.main{background:#0a0a0a;margin:0;padding:0;}
div[data-testid="stTextInput"]{position:absolute!important; bottom:8%!important; left:50%!important;
transform:translateX(-50%)!important; width:180px!important; z-index:100!important;}
div[data-testid="stTextInput"] input{background:rgba(0,0,0,0.9)!important; border:2px solid #FFD700!important;
border-radius:10px!important; color:#FFD700!important; text-align:center!important; padding:10px!important;}
div[data-testid="stTextInput"] label{display:none!important;}
</style>
""", unsafe_allow_html=True)

# === FONCTIONS ===
@st.cache_data(ttl=60)
def load_table(table_name):
    try:
        data = supabase.table(table_name).select("*").order("id", desc=True).execute()
        return pd.DataFrame(data.data)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_table_columns(table_name):
    try:
        test = supabase.table(table_name).select("*").limit(1).execute()
        return list(test.data[0].keys()) if test.data else []
    except:
        return []

def check_perm(key):
    return st.session_state.user_role == "PDG" or st.session_state.perms.get(key, False)

def safe_pdf_txt(txt):
    if txt is None or pd.isna(txt): return ""
    txt = str(txt).replace('—','-').replace('–','-').replace('’',"'").replace('“','"').replace('”','"')
    return ''.join(c if ord(c) < 128 else '?' for c in txt).replace('\n',' ').strip()

def generer_qrcode(data_text):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=3, border=1)
    qr.add_data(data_text); qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name)
    return temp_file.name

def generer_pdf_facture(numero, type_op, client, details_list, montant, devise, tel_client="+243...", periode="", type_facture="Simple"):
    pdf = FPDF(); pdf.add_page(); pdf.set_auto_page_break(auto=False, margin=10)
    pdf.set_fill_color(20, 50, 40); pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 20)
    pdf.set_xy(10, 8); pdf.cell(0, 10, "ASYMAS BUSINESS", ln=True)
    pdf.set_font("Arial", "", 9); pdf.set_xy(10, 16)
    pdf.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
    pdf.set_font("Arial", "B", 10); pdf.set_xy(150, 8)
    titre_fact = "FACTURE N" if type_facture == "Simple" else "PROFORMA N"
    pdf.cell(50, 6, titre_fact, ln=True, align="R")
    pdf.set_font("Arial", "", 10); pdf.set_xy(150, 14)
    pdf.cell(50, 6, safe_pdf_txt(numero), ln=True, align="R")
    pdf.set_font("Arial", "", 9); pdf.set_xy(150, 20)
    pdf.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")
    y_pos = 45; pdf.set_text_color(0, 0, 0); pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 14); pdf.set_xy(10, y_pos)
    pdf.cell(0, 10, f"{type_facture.upper()} {safe_pdf_txt(type_op.upper())}", ln=True, fill=True)
    y_pos += 15; pdf.set_font("Arial", "B", 10)
    pdf.set_xy(10, y_pos); pdf.cell(85, 7, "FACTURE A:", 1, 0, 'L')
    pdf.cell(10, 7, "", 0, 0); pdf.cell(85, 7, "DETAILS PAIEMENT:", 1, 1, 'L')
    y_pos += 7; pdf.set_font("Arial", "", 9)
    pdf.set_xy(10, y_pos); pdf.cell(85, 6, f"Client: {safe_pdf_txt(client)}", 'LR', 0, 'L')
    pdf.cell(10, 6, "", 0, 0); pdf.cell(85, 6, "M-Pesa: +243817264448", 'LR', 1, 'L')
    y_pos += 6; pdf.set_xy(10, y_pos)
    pdf.cell(85, 6, f"Tel: {safe_pdf_txt(tel_client)}", 'LR', 0, 'L')
    pdf.cell(10, 6, "", 0, 0); pdf.cell(85, 6, "Echeance: Immediate", 'LR', 1, 'L')
    y_pos += 14; pdf.set_fill_color(0, 102, 0); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10); pdf.set_xy(10, y_pos)
    pdf.cell(115, 8, "DESIGNATION", 1, 0, 'C', True)
    pdf.cell(25, 8, "QTE", 1, 0, 'C', True)
    pdf.cell(40, 8, f"MONTANT ({safe_pdf_txt(devise)})", 1, 1, 'C', True)
    y_pos += 8; pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 9)
    for item in details_list if isinstance(details_list, list) else [{"nom": details_list, "qte": 1, "pu": montant}]:
        nom = safe_pdf_txt(item.get('nom', '')); qte = item.get('qte', 1)
        pu = item.get('pu', item.get('prix', 0)); montant_item = pu * qte
        pdf.set_xy(10, y_pos); pdf.cell(115, 7, nom, 1, 0, 'L')
        pdf.cell(25, 7, str(qte), 1, 0, 'C'); pdf.cell(40, 7, f"{montant_item:,.0f}", 1, 1, 'R')
        y_pos += 7
    pdf.set_fill_color(255, 204, 0); pdf.set_font("Arial", "B", 11)
    pdf.set_xy(10, y_pos); pdf.cell(140, 10, "MONTANT TOTAL A PAYER", 1, 0, 'R', True)
    pdf.cell(40, 10, f"{montant:,.0f} {safe_pdf_txt(devise)}", 1, 1, 'R', True)
    qr_data = f"ASYMAS BUSINESS\nFacture: {numero}\nType: {type_op}\nClient: {client}\nMontant: {montant:,.0f} {devise}"
    qr_path = generer_qrcode(qr_data); pdf.image(qr_path, x=155, y=y_pos+10, w=25); os.unlink(qr_path)
    return bytes(pdf.output(dest='S'))

def generer_pdf_devis_consulting(numero, type_devis, client, titre_projet, parcelle, localisation, details_sections, devise="USD", tel_client="+243...", main_oeuvre=0):
    pdf = FPDF(); pdf.add_page(); pdf.set_auto_page_break(auto=False, margin=10)
    pdf.set_fill_color(20, 50, 40); pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 20)
    pdf.set_xy(10, 8); pdf.cell(0, 10, "ASYMAS CONSULTING", ln=True)
    pdf.set_font("Arial", "", 9); pdf.set_xy(10, 16)
    pdf.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
    pdf.set_font("Arial", "B", 10); pdf.set_xy(150, 8)
    pdf.cell(50, 6, "DEVIS N", ln=True, align="R")
    pdf.set_font("Arial", "", 10); pdf.set_xy(150, 14)
    pdf.cell(50, 6, safe_pdf_txt(numero), ln=True, align="R")
    pdf.set_font("Arial", "", 9); pdf.set_xy(150, 20)
    pdf.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")
    y_pos = 45; pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "B", 12)
    pdf.set_xy(10, y_pos); pdf.multi_cell(0, 6, safe_pdf_txt(titre_projet.upper()), align="C")
    y_pos = pdf.get_y() + 3; pdf.set_font("Arial", "B", 10)
    if parcelle: pdf.set_xy(10, y_pos); pdf.cell(0, 6, f"PARCELLE N {safe_pdf_txt(parcelle)}", ln=True); y_pos += 6
    if localisation: pdf.set_xy(10, y_pos); pdf.cell(0, 6, f"LOCALISATION: {safe_pdf_txt(localisation)}", ln=True); y_pos += 6
    pdf.set_xy(10, y_pos); pdf.cell(0, 6, f"CLIENT: {safe_pdf_txt(client)}", ln=True); y_pos += 6
    if tel_client: pdf.set_xy(10, y_pos); pdf.cell(0, 6, f"TEL: {safe_pdf_txt(tel_client)}", ln=True); y_pos += 6
    y_pos += 5; pdf.set_font("Arial", "B", 9); pdf.set_fill_color(220, 220, 220)
    pdf.set_xy(10, y_pos); pdf.cell(10, 7, "N", 1, 0, 'C', True); pdf.cell(90, 7, "DESIGNATION DES OUVRAGES", 1, 0, 'C', True)
    pdf.cell(15, 7, "Unité", 1, 0, 'C', True); pdf.cell(20, 7, "Qté", 1, 0, 'C', True)
    pdf.cell(25, 7, "Prix U", 1, 0, 'C', True); pdf.cell(30, 7, "Prix total", 1, 1, 'C', True); y_pos += 7
    pdf.set_font("Arial", "", 8); grand_total = 0
    for section in details_sections:
        if y_pos > 240: pdf.add_page(); y_pos = 30
        pdf.set_font("Arial", "B", 9); pdf.set_fill_color(200, 200, 200)
        pdf.set_xy(10, y_pos); pdf.cell(10, 6, section['numero'], 1, 0, 'L', True)
        pdf.cell(180, 6, safe_pdf_txt(section['titre']), 1, 1, 'L', True); y_pos += 6
        pdf.set_font("Arial", "", 8); sous_total = 0
        for item in section['items']:
            if y_pos > 250: pdf.add_page(); y_pos = 30
            qte = item.get('qte', 0); pu = item.get('pu', 0); total_item = qte * pu; sous_total += total_item
            pdf.set_xy(10, y_pos); pdf.cell(10, 5, item.get('num', ''), 1, 0, 'C')
            pdf.cell(90, 5, safe_pdf_txt(item.get('designation', '')), 1, 0, 'L')
            pdf.cell(15, 5, item.get('unite', ''), 1, 0, 'C')
            pdf.cell(20, 5, f"{qte:,.2f}" if qte else "", 1, 0, 'R')
            pdf.cell(25, 5, f"{pu:,.0f}" if pu else "", 1, 0, 'R')
            pdf.cell(30, 5, f"{total_item:,.0f}" if total_item else "", 1, 1, 'R'); y_pos += 5
        pdf.set_font("Arial", "B", 8); pdf.set_xy(10, y_pos)
        pdf.cell(160, 6, "Sous Total", 1, 0, 'R', True)
        pdf.cell(30, 6, f"{sous_total:,.0f}", 1, 1, 'R', True); y_pos += 6; grand_total += sous_total
    if main_oeuvre > 0:
        if y_pos > 250: pdf.add_page(); y_pos = 30
        pdf.set_xy(10, y_pos); pdf.cell(160, 6, "MAIN D'OEUVRE", 1, 0, 'R')
        pdf.cell(30, 6, f"{main_oeuvre:,.0f}", 1, 1, 'R'); y_pos += 6; grand_total += main_oeuvre
    pdf.set_fill_color(255, 204, 0); pdf.set_font("Arial", "B", 10)
    pdf.set_xy(10, y_pos); pdf.cell(160, 8, f"TOTAL GENERAL ({devise})", 1, 0, 'R', True)
    pdf.cell(30, 8, f"{grand_total:,.0f}", 1, 1, 'R', True)
    return bytes(pdf.output(dest='S'))

def creer_facture_auto(type_op, client, details, montant, devise="FC", details_list=None, tel="+243...", periode="", type_facture="Simple"):
    numero_facture = f"AS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if details_list is None: details_list = [{"nom": details, "qte": 1, "pu": montant}]
    pdf_bytes = generer_pdf_facture(numero_facture, type_op, client, details_list, montant, devise, tel, periode, type_facture)
    try:
        data_compta = {"type": "Revenu", "description": str(f"{type_op} - {client} - {details}"),
                       "montant": float(montant), "date": str(date.today()),
                       "utilisateur": st.session_state.user_name, "categorie": str(type_op),
                       "devise": str(devise), "numero_facture": str(numero_facture),
                       "details": json.dumps(details_list)}
        supabase.table("compta").insert(data_compta).execute()
        st.toast(f"✅ Enregistré par {st.session_state.user_name}", icon="✅")
    except Exception as e:
        st.error("❌ ERREUR INSERTION COMPTA"); st.code(repr(e))
    return numero_facture, pdf_bytes

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
            st.session_state.logged_in = True; st.session_state.user_role = "PDG"; st.session_state.user_name = "PDG"; st.session_state.perms = {}; st.rerun()
    st.stop()

# === ACCUEIL CERCLE ===
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
        st.session_state.clear(); st.rerun()

# === VERIF DROIT MODULE ===
elif st.session_state.selected_module:
    perm_map = {"Commerce": "commerce", "Stock": "stock", "Immo": "immobilier",
                "Auto": "automobile", "Compta": "comptabilite", "Factures": "factures"}
    perm_key = perm_map.get(st.session_state.selected_module, "")
    if not check_perm(perm_key):
        st.error(f"⛔ Vous n'avez pas l'autorisation d'accéder au module {st.session_state.selected_module}")
        if st.button("← Retour Accueil"):
            st.session_state.selected_module = None; st.query_params.clear(); st.rerun()
        st.stop()

    st.divider()
    col1, col2 = st.columns([6,1])
    with col1:
        st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
        st.markdown(f"### {st.session_state.selected_module}")
    with col2:
        if st.button("← Retour"):
            st.session_state.selected_module = None; st.query_params.clear(); st.rerun()

    table_map = {"Commerce": "articles", "Stock": "articles", "Immo": "biens",
                 "Auto": "voitures", "Compta": "compta", "Factures": "factures_proforma"}
    df = load_table(table_map.get(st.session_state.selected_module, "articles"))
    st.dataframe(df, use_container_width=True)

# === TABS COMPLETS ===
else:
    with st.sidebar:
        st.markdown(f"## 👤 {st.session_state.user_name}")
        st.markdown(f"**Rôle : {st.session_state.user_role}**")
        st.info("ASYMAS BUSINESS v3.0")
        if st.button("🏠 Retour Accueil"):
            st.session_state.selected_module = None; st.query_params.clear(); st.rerun()
        if st.button("🔄 Actualiser"):
            st.cache_data.clear(); st.rerun()
        if st.button("🔒 Déconnexion"):
            st.session_state.clear(); st.rerun()

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

    tabs_dispo = ["📊 Dashboard", "🛍️ Commerce", "📦 Gestion Stock", "🏠 Immobilier",
                  "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures",
                  "📋 Devis", "👥 Utilisateurs"]
    tabs = st.tabs(tabs_dispo)
    tab_map = {name: tab for name, tab in zip(tabs_dispo, tabs)}

    perms = st.session_state.perms
    is_pdg = st.session_state.user_role == "PDG"

    # === DASHBOARD ===
    with tab_map["📊 Dashboard"]:
        st.markdown("## 📊 Dashboard ASYMAS")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🏠 Biens", len(df_biens))
        col2.metric("📦 Articles", len(df_articles))
        col3.metric("🚗 Voitures", len(df_voitures))
        revenus = df_compta[df_compta['type']=='Revenu']['montant'].sum() if not df_compta.empty else 0
        col4.metric("💰 Revenus", f"{revenus:,.0f} FC")
        if not df_compta.empty:
            st.subheader("📈 Dernières transactions")
            st.dataframe(df_compta.head(10), use_container_width=True)

    # === DEVIS COMPLET ===
    if "📋 Devis" in tab_map:
        with tab_map["📋 Devis"]:
            if not (is_pdg or perms.get('devis_industriel', False) or perms.get('devis_batiment', False)):
                st.error("⛔ Vous n'avez pas l'autorisation Devis")
            else:
                st.markdown("## 📋 Devis Consulting - Industriel & Bâtiment")
                tab_industriel, tab_batiment = st.tabs(["🏭 Devis Industriel", "🏗️ Devis Bâtiment"])

                # === DEVIS INDUSTRIEL ===
                with tab_industriel:
                    peut_creer_ind = is_pdg or perms.get('devis_industriel', False)
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
                            st.session_state.devis_sections = [{"numero": "A", "titre": "ELECTRICITE", "items": [
                                {"type": "cable", "designation": "Câble 2.5mm²", "marque": "Nexans", "section": "2.5mm²", "longueur": 100, "unite": "m", "qte": 1, "pu": 1.2}]}]
                        total_general_ind = 0
                        col_h1, col_h2, col_h3, col_h4, col_h5, col_h6, col_h7, col_h8 = st.columns([0.5, 3, 1.5, 1.5, 1, 1, 1, 0.5])
                        col_h1.markdown("**N°**"); col_h2.markdown("**Désignation**"); col_h3.markdown("**Type/Marque**")
                        col_h4.markdown("**Spécifications**"); col_h5.markdown("**Qté**")
                        col_h6.markdown("**PU**"); col_h7.markdown("**Total**"); col_h8.markdown("")
                        st.divider()
                        for idx, section in enumerate(st.session_state.devis_sections):
                            col_titre, col_del_sec = st.columns([5, 1])
                            with col_titre: st.markdown(f"**{section['numero']}. {section['titre']}**")
                            with col_del_sec:
                                if st.button("🗑️ Supprimer Section", key=f"del_sec_ind_{idx}"):
                                    st.session_state.devis_sections.pop(idx); st.rerun()
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
                            st.error("Erreur enregistrement")
                            st.code(repr(e))
                    else:
                        st.error("Client, Titre et au moins 1 section requis")
            else:
                st.info("🔒 Vous n'avez pas l'autorisation de créer des devis industriels")

            peut_telecharger_ind = is_pdg or perms.get('devis_industriel_download', False)
            peut_imprimer_ind = is_pdg or perms.get('devis_industriel_print', False)

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
                                if is_pdg:
                                    if st.button("🗑️ Supprimer", key=f"del_ind_{numero}", width="stretch"):
                                        supabase.table('devis').delete().eq("numero", numero).execute()
                                        st.success("Supprimé")
                                        st.rerun()

        # === DEVIS BATIMENT ===
        with tab_batiment:
            peut_creer_bat = is_pdg or perms.get('devis_batiment', False)

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
                col_h1.markdown("**no**"); col_h2.markdown("**désignation**"); col_h3.markdown("**unité**")
                col_h4.markdown("**quantité**"); col_h5.markdown("**pu USD**"); col_h6.markdown("**PT USD**"); col_h7.markdown("")
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

            peut_telecharger_bat = is_pdg or perms.get('devis_batiment_download', False)
            peut_imprimer_bat = is_pdg or perms.get('devis_batiment_print', False)

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
                                st.download_button(label="📥", data=pdf_bytes, file_name=f"{numero}.pdf",
                                                   mime="application/pdf", key=f"dl_bat_bas_{numero}")
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

    # === UTILISATEURS ===
    if "👥 Utilisateurs" in tab_map:
        with tab_map["👥 Utilisateurs"]:
            if not (is_pdg or perms.get('users', False)):
                st.error("⛔ Vous n'avez pas l'autorisation Utilisateurs")
            else:
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
                                    st.success
