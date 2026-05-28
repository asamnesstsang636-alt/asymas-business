import streamlit as st
import pandas as pd
st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<meta name="mobile-web-app-capable" content="yes">""", unsafe_allow_html=True)

from supabase import create_client, Client
from datetime import date, datetime, timedelta
from fpdf import FPDF
import base64, io, qrcode, tempfile, os, json
from PIL import Image
from streamlit_qrcode_scanner import qrcode_scanner

# === INIT SESSION ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'module_actif' not in st.session_state:
    st.session_state.module_actif = None

# === CSS NETTOYÉ ===
st.markdown("""
<style>
.block-container{padding:0!important;max-width:100%!important;}
.main{background:#0a0a0a;margin:0;padding:0;}
</style>
""", unsafe_allow_html=True)

# === HOLOGRAMME ===
def afficher_hologramme():
    st.markdown("""
    <div style="position:relative;width:100vw;height:70vh;background:radial-gradient(ellipse at center 55%, rgba(255,215,0,0.7) 0%, rgba(15,15,15,1) 85%);overflow:hidden;">
        <!-- Rectangle du bas -->
        <div style="position:absolute;bottom:8%;left:50%;transform:translateX(-50%);width:340px;height:170px;background:linear-gradient(145deg,#2d2d2d,#1a1a1a);border-radius:45px;box-shadow:0 35px 70px rgba(0,0,0,0.9);border:3px solid #444;"></div>
        <!-- Cercle + 6 boutons -->
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

# === ÉCRAN LOGIN ===
if not st.session_state.logged_in:
    afficher_hologramme()
    
    # Champ login positionné pile sur le rectangle
    col1,col2,col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<div style='margin-top:-25vh;background:rgba(0,0,0,0.95);padding:20px;border:3px solid #FFD700;border-radius:15px;box-shadow:0 0 30px #FFD700;'>", unsafe_allow_html=True)
        pwd = st.text_input("Accès ASYMAS", type="password", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
    
    if pwd == "asymas2025":
        st.session_state.logged_in = True
        st.session_state.user_role = "PDG"
        st.session_state.user_name = "PDG"
        st.rerun()
    elif pwd:
        st.error("Mot de passe incorrect")
    st.stop()

# === APRÈS LOGIN : PAGE D'ACCUEIL + 6 BOUTONS ===
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=60)
def load_table(table_name):
    try:
        data = supabase.table(table_name).select("*").order("id", desc=True).execute()
        return pd.DataFrame(data.data)
    except: return pd.DataFrame()

df_biens = load_table("biens")
df_articles = load_table("articles")
df_voitures = load_table("voitures")
df_compta = load_table("compta")

st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
st.markdown("### Agriculture • Commerce • Immobilier • Automobile • Beni RDC")

# 6 BOUTONS CLIQUABLES SUR 2 LIGNES
col1,col2,col3 = st.columns(3)
if col1.button("🏪 Commerce", width="stretch"):
    st.session_state.module_actif = "Commerce"
if col2.button("📦 Stock", width="stretch"):
    st.session_state.module_actif = "Stock"
if col3.button("🏠 Immo", width="stretch"):
    st.session_state.module_actif = "Immo"

col4,col5,col6 = st.columns(3)
if col4.button("🚗 Auto", width="stretch"):
    st.session_state.module_actif = "Auto"
if col5.button("🧾 Factures", width="stretch"):
    st.session_state.module_actif = "Factures"
if col6.button("📊 Compta", width="stretch"):
    st.session_state.module_actif = "Compta"

st.divider()

# === AFFICHAGE D'UN SEUL MODULE SELON LE CLIC ===
if st.session_state.module_actif == "Commerce":
    st.markdown("## 🛍️ Commerce - Point de Vente")
    st.dataframe(df_articles, use_container_width=True)
    
elif st.session_state.module_actif == "Stock":
    st.markdown("## 📦 Gestion Stock")
    st.dataframe(df_articles, use_container_width=True)
    
elif st.session_state.module_actif == "Immo":
    st.markdown("## 🏠 Immobilier")
    st.dataframe(df_biens, use_container_width=True)
    
elif st.session_state.module_actif == "Auto":
    st.markdown("## 🚗 Automobile")
    st.dataframe(df_voitures, use_container_width=True)
    
elif st.session_state.module_actif == "Factures":
    st.markdown("## 🧾 Factures")
    st.info("Module factures en cours")
    
elif st.session_state.module_actif == "Compta":
    st.markdown("## 💰 Comptabilité")
    st.dataframe(df_compta, use_container_width=True)

# Sidebar avec déconnexion
with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.user_name}")
    st.markdown(f"**Rôle : {st.session_state.user_role}**")
    if st.button("🚪 Déconnexion", width="stretch"):
        st.session_state.clear()
        st.rerun()
