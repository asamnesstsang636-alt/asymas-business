import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date, datetime, timedelta
from fpdf import FPDF
import base64
import io
import qrcode
from PIL import Image
import tempfile
import os
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

# === CONFIG SUPABASE ===
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="ASYMAS BUSINESS", layout="wide", page_icon="💎")

# === CACHE TOUT STREAMLIT ===
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

# === SYSTÈME DE MOTS DE PASSE ===
@st.cache_data(ttl=10)
def load_passwords():
    try:
        data = supabase.table("utilisateurs").select("nom,role,password").execute()
        passwords = {}
        for user in data.data:
            passwords[user['role']] = user['password']
        return passwords
    except:
        return {
            "PDG": "tsang2024",
            "GERANTE": "asiya2024",
            "UTILISATEUR": "basam2024"
        }

passwords_db = load_passwords()

if 'user_role' not in st.session_state:
    st.session_state.user_role = None
    st.session_state.user_name = None

if st.session_state.user_role is None:
    st.markdown("# 🔐 ASYMAS BUSINESS - CONNEXION")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("### Choisissez votre profil :")
        profil = st.selectbox("Utilisateur", ["-- Sélectionner --", "PDG TSANG", "Gérante ASIYA", "BASAM"])
        password = st.text_input("Mot de passe", type="password", key="pwd")
        if st.button("SE CONNECTER", width="stretch", type="primary"):
            if profil == "PDG TSANG" and password == passwords_db["PDG"]:
                st.session_state.user_role = "PDG"
                st.session_state.user_name = "TSANG"
                st.rerun()
            elif profil == "Gérante ASIYA" and password == passwords_db["GERANTE"]:
                st.session_state.user_role = "GERANTE"
                st.session_state.user_name = "ASIYA"
                st.rerun()
            elif profil == "BASAM" and password == passwords_db["UTILISATEUR"]:
                st.session_state.user_role = "UTILISATEUR"
                st.session_state.user_name = "BASAM"
                st.rerun()
            else:
                st.error("Profil ou mot de passe incorrect")
    st.stop()

# === CSS ===
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

# === QR CODE ===
def generer_qrcode(data_text):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=3, border=1)
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name)
    return temp_file.name

# === PDF FACTURE ===
def generer_pdf_facture(numero, type_op, client, details_list, montant, devise, tel_client="+243...", periode=""):
    def clean_text(txt):
        return str(txt).encode('latin-1', 'replace').decode('latin-1')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
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
    pdf.cell(50, 6, "FACTURE N°", ln=True, align="R")
    pdf.set_font("Arial", "", 10)
    pdf.set_xy(150, 14)
    pdf.cell(50, 6, clean_text(numero), ln=True, align="R")
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(150, 20)
    pdf.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")
    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"FACTURE {clean_text(type_op.upper())}", ln=True, fill=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.set_draw_color(0, 0, 0)
    pdf.cell(90, 7, "FACTURE A:", 1, 0, 'L')
    pdf.cell(10, 7, "", 0, 0)
    pdf.cell(90, 7, "DETAILS PAIEMENT:", 1, 1, 'L')
    pdf.set_font("Arial", "", 9)
    pdf.cell(90, 6, f"Client: {clean_text(client)}", 'LR', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(90, 6, "M-Pesa: +243817264448", 'LR', 1, 'L')
    pdf.cell(90, 6, f"Tel: {clean_text(tel_client)}", 'LR', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(90, 6, "Echeance: Immediate", 'LR', 1, 'L')
    pdf.cell(90, 6, f"Date emission: {date.today().strftime('%d/%m/%Y')}", 'LRB', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(90, 6, "", 'LRB', 1, 'L')
    pdf.ln(8)
    pdf.set_fill_color(0, 102, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(120, 8, "DESIGNATION", 1, 0, 'C', True)
    pdf.cell(30, 8, "QTE", 1, 0, 'C', True)
    pdf.cell(40, 8, f"MONTANT ({clean_text(devise)})", 1, 1, 'C', True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)
if isinstance(details_list, list) and details_list:
    for item in details_list:
        nom = clean_text(item.get('nom', ''))
        qte = item.get('qte', 1)
        prix = item.get('prix', 0) or 0
        montant_item = float(prix) * int(qte)
        pdf.cell(120, 7, nom, 1, 0, 'L')
        pdf.cell(30, 7, str(qte), 1, 0, 'C')
        pdf.cell(40, 7, f"{montant_item:,.0f}", 1, 1, 'R')
else:
    pdf.cell(120, 7, clean_text(str(details_list)), 1, 0, 'L')
    pdf.cell(30, 7, "1", 1, 0, 'C')
    pdf.cell(40, 7, f"{montant:,.0f}", 1, 1, 'R')
                    
                 if st.form_submit_button("💾 ENREGISTRER LES MOTS DE PASSE", width="stretch", type="primary"):
                    try:
                        supabase.table("utilisateurs").update({"password": new_pass_pdg}).eq("role", "PDG").execute()
                        supabase.table("utilisateurs").update({"password": new_pass_gerante}).eq("role", "GERANTE").execute()
                        supabase.table("utilisateurs").update({"password": new_pass_user}).eq("role", "UTILISATEUR").execute()
                        st.success("✅ Mots de passe mis à jour")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur mise à jour")
                        st.code(repr(e))
            
            st.divider()
            st.subheader("📋 Liste des Utilisateurs")
            st.dataframe(df_utilisateurs[['nom', 'role']], use_container_width=True, hide_index=True)
else:
    if tab9:
        with tab9:
            st.error("🔒 ACCÈS REFUSÉ - Section réservée au PDG uniquement")

st.sidebar.divider()
st.sidebar.caption(f"ASYMAS BUSINESS v2.0")
st.sidebar.caption(f"Connecté: {st.session_state.user_name}")
