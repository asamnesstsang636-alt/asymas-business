import streamlit as st
import pandas as pd
st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide", initial_sidebar_state="auto")
st.markdown("""<meta name="mobile-web-app-capable" content="yes">""", unsafe_allow_html=True)

from supabase import create_client, Client
from datetime import date, datetime, timedelta
from fpdf import FPDF
import base64, io, qrcode, tempfile, os, json
from PIL import Image
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from streamlit_qrcode_scanner import qrcode_scanner

# === SESSION STATE INIT ===
if 'user_permissions' not in st.session_state:
    st.session_state.user_permissions = {}
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "📊 Dashboard"
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# === STYLE ===
st.markdown("""
<style>
.block-container{padding:0!important;max-width:100%!important;}
.main{background:#0a0a0a;margin:0;padding:0;}
div[data-testid="stTextInput"]{position:absolute!important; bottom:8%!important; left:50%!important; transform:translateX(-50%)!important; width:180px!important; z-index:100!important;}
div[data-testid="stTextInput"] input{background:rgba(0,0,0,0.9)!important; border:2px solid #FFD700!important; border-radius:10px!important; color:#FFD700!important; text-align:center!important; padding:10px!important;}
div[data-testid="stTextInput"] label{display:none!important;}
</style>
""", unsafe_allow_html=True)

# === PAGE D'ACCUEIL : HOLOGRAMME + BOUTONS TOUJOURS VISIBLES ===
if st.session_state.page == "home":
    st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
    
    # Ton hologramme
    st.markdown("""
    <div style="position:relative;width:100vw;height:70vh;background:radial-gradient(ellipse at center 55%, rgba(255,215,0,0.7) 0%, rgba(15,15,15,1) 85%);overflow:hidden;">
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

    # Les 6 boutons toujours visibles
    btn_config = [
        ("🏪", "Commerce", "commerce", 0, -190),
        ("🚚", "Auto", "automobile", 110, -145),
        ("🧾", "Factures", "factures", 110, 145),
        ("🏠", "Immo", "immobilier", 0, 190),
        ("📦", "Stock", "stock", -110, 145),
        ("📊", "Compta", "comptabilite", -110, -145)
    ]

    for icon, label, key, x, y in btn_config:
        if st.button(f"{icon}\n{label}", key=f"btn_{key}"):
            # Vérification autorisation au clic
            if st.session_state.user_permissions.get(key, False) or st.session_state.user_role == "PDG":
                st.session_state.page = key
                st.rerun()
            else:
                st.toast(f"🔒 Accès refusé à {label}. Demande au PDG.", icon="⚠️")

        st.markdown(f"""
        <style>
        button[kind="secondary"]:has(div p:contains("{icon}")) {{
            position: absolute;
            left: calc(50% + {x}px);
            top: calc(45% + {y}px);
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: #fff;
            border: 3px solid #FFD700;
            box-shadow: 0 0 20px #FFD700;
            z-index: 999;
            cursor: pointer;
            transform: translate(-50%, -50%);
            margin-top: -85vh;
        }}
        </style>
        """, unsafe_allow_html=True)
# === TES FONCTIONS ===
def generer_qrcode(data_text):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=3, border=1)
    qr.add_data(data_text); qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name); return temp_file.name

def safe_pdf_txt(txt):
    if txt is None or pd.isna(txt): return ""
    txt = str(txt).replace('—','-').replace('’',"'").replace('“','"').replace('”','"')
    return ''.join(c if ord(c) < 128 else '?' for c in txt)

# === CHARGEMENT DONNEES ===
df_biens = load_table("biens")
df_articles = load_table("articles")
df_voitures = load_table("voitures")
df_compta = load_table("compta")
df_factures = load_table("factures_proforma")
df_devis = load_table("devis")

if 'montant' not in df_compta.columns: df_compta['montant'] = 0
if 'type' not in df_compta.columns: df_compta['type'] = 'Inconnu'
if 'date' in df_compta.columns:
    df_compta['date'] = pd.to_datetime(df_compta['date'], errors='coerce')
    df_compta = df_compta.sort_values('date', ascending=False)

st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
st.markdown("### Agriculture • Commerce • Immobilier • Automobile • Beni RDC")

with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.user_name}")
    st.markdown(f"**Rôle : {st.session_state.user_role}**")
    st.info("ASYMAS BUSINESS v3.0 Hologram")
    if 'theme_choisi' not in st.session_state: st.session_state.theme_choisi = "Sombre ASYMAS"
    theme = st.selectbox("🎨", ["Sombre ASYMAS","Bleu Pro","Vert Agri","Noir Luxe"], key="theme_choisi", label_visibility="collapsed")
    if st.button("🚪 Déconnexion", use_container_width=True): st.session_state.clear(); st.rerun()
    if st.button("🔄 Actualiser", key="btn_save"): st.cache_data.clear(); st.rerun()

if theme=="Sombre ASYMAS": st.markdown("""<style>.stApp{background:#0E1117;color:#E0E0E0}h1,h2,h3{color:#14B814!important}</style>""",unsafe_allow_html=True)
elif theme=="Bleu Pro": st.markdown("""<style>.stApp{background:#0A1929;color:#E3F2FD}h1,h2,h3{color:#2196F3!important}</style>""",unsafe_allow_html=True)
elif theme=="Vert Agri": st.markdown("""<style>.stApp{background:#1B2A1B;color:#E8F5E9}h1,h2,h3{color:#4CAF50!important}</style>""",unsafe_allow_html=True)
elif theme=="Noir Luxe": st.markdown("""<style>.stApp{background:#000;color:#FFF}h1,h2,h3{color:#FFD700!important}</style>""",unsafe_allow_html=True)

tabs_dispo = ["📊 Dashboard", "🛍️ Commerce", "📦 Gestion Stock", "🏠 Immobilier", "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures", "📋 Devis", "👥 Utilisateurs"]
tabs = st.tabs(tabs_dispo)
tab_map = {name: tab for name, tab in zip(tabs_dispo, tabs)}

# === DASHBOARD ===
with tab_map["📊 Dashboard"]:
    st.markdown("## 📊 Dashboard ASYMAS")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏠 Biens", len(df_biens))
    col2.metric("📦 Articles", len(df_articles))
    col3.metric("🚗 Voitures", len(df_voitures))
    if not df_compta.empty and 'type' in df_compta.columns and 'montant' in df_compta.columns:
        revenus = df_compta[df_compta['type']=='Revenu']['montant'].sum()
        col4.metric("💰 Revenus", f"{revenus:,.0f} FC")
    else:
        col4.metric("💰 Revenus", "0 FC")
    st.divider()
    if not df_compta.empty:
        st.subheader("📈 Dernières transactions")
        st.dataframe(df_compta.head(10), use_container_width=True)

# === COMMERCE ===
with tab_map["🛍️ Commerce"]:
    if not st.session_state.user_permissions.get("commerce", False) and st.session_state.user_role!= "PDG":
        st.warning("🔒 Accès refusé. Demande l'autorisation au PDG.")
        st.stop()
    st.markdown("## 🛍️ Commerce - Point de Vente")
    #... ton code commerce existant

# === GESTION STOCK ===
with tab_map["📦 Gestion Stock"]:
    if not st.session_state.user_permissions.get("stock", False) and st.session_state.user_role!= "PDG":
        st.warning("🔒 Accès refusé. Demande l'autorisation au PDG.")
        st.stop()
    st.markdown("## 📦 Gestion Stock")
    st.dataframe(df_articles, use_container_width=True)
    with st.expander("➕ Ajouter Article"):
        with st.form("form_article"):
            nom = st.text_input("Nom Article")
            stock = st.number_input("Stock", min_value=0)
            prix = st.number_input("Prix Vente FC", min_value=0.0)
            if st.form_submit_button("Ajouter"):
                supabase.table("articles").insert({"nom_article": nom, "stock": stock, "prix_vente": prix}).execute()
                st.cache_data.clear(); st.rerun()

# === IMMOBILIER ===
with tab_map["🏠 Immobilier"]:
    if not st.session_state.user_permissions.get("immobilier", False) and st.session_state.user_role!= "PDG":
        st.warning("🔒 Accès refusé. Demande l'autorisation au PDG.")
        st.stop()
    st.markdown("## 🏠 Immobilier")
    st.dataframe(df_biens, use_container_width=True)

# === AUTOMOBILE ===
with tab_map["🚗 Automobile"]:
    if not st.session_state.user_permissions.get("automobile", False) and st.session_state.user_role!= "PDG":
        st.warning("🔒 Accès refusé. Demande l'autorisation au PDG.")
        st.stop()
    st.markdown("## 🚗 Automobile")
    st.dataframe(df_voitures, use_container_width=True)

# === GESTION PARC ===
with tab_map["🚘 Gestion Parc"]:
    if not st.session_state.user_permissions.get("parc", False) and st.session_state.user_role!= "PDG":
        st.warning("🔒 Accès refusé. Demande l'autorisation au PDG.")
        st.stop()
    st.markdown("## 🚘 Gestion Parc")
    st.write("Module en cours...")

# === COMPTABILITÉ ===
with tab_map["💰 Comptabilité"]:
    if not st.session_state.user_permissions.get("comptabilite", False) and st.session_state.user_role!= "PDG":
        st.warning("🔒 Accès refusé. Demande l'autorisation au PDG.")
        st.stop()
    st.markdown("## 💰 Comptabilité")
    st.dataframe(df_compta, use_container_width=True)

# === FACTURES ===
with tab_map["📄 Factures"]:
    if not st.session_state.user_permissions.get("factures", False) and st.session_state.user_role!= "PDG":
        st.warning("🔒 Accès refusé. Demande l'autorisation au PDG.")
        st.stop()
    st.markdown("## 📄 Factures & Proformas")
    st.dataframe(df_factures, use_container_width=True)

# === DEVIS ===
with tab_map["📋 Devis"]:
    if not st.session_state.user_permissions.get("devis", False) and st.session_state.user_role!= "PDG":
        st.warning("🔒 Accès refusé. Demande l'autorisation au PDG.")
        st.stop()
    st.markdown("## 📋 Devis Consulting")
    st.dataframe(df_devis, use_container_width=True)

# === UTILISATEURS ===
with tab_map["👥 Utilisateurs"]:
    st.markdown("## 👥 Gestion Utilisateurs - Droits d'Accès")
    #... ton code utilisateurs complet ici
