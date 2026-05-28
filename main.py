import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide", initial_sidebar_state="auto")
st.markdown("""<meta name="mobile-web-app-capable" content="yes">""", unsafe_allow_html=True)

from supabase import create_client, Client
from datetime import date, datetime
from fpdf import FPDF
import tempfile, os, json, qrcode
from streamlit_qrcode_scanner import qrcode_scanner

# === SESSION STATE ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'selected_module' not in st.session_state:
    st.session_state.selected_module = None

# Récupère module depuis URL si présent
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
</style>
""", unsafe_allow_html=True)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=60)
def load_table(table_name):
    try:
        data = supabase.table(table_name).select("*").order("id", desc=True).execute()
        return pd.DataFrame(data.data)
    except:
        return pd.DataFrame()

# === LOGIN ===
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
    if pwd == "asymas2025":
        st.session_state.logged_in = True
        st.session_state.user_role = "PDG"
        st.session_state.user_name = "PDG"
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

# === AFFICHAGE MODULE UNIQUE ===
elif st.session_state.selected_module:
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

# === TON ANCIEN CODE TABS ===
else:
    st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
    st.markdown("### Agriculture • Commerce • Immobilier • Automobile • Beni RDC")

    with st.sidebar:
        st.markdown(f"## 👤 {st.session_state.user_name}")
        st.markdown(f"**Rôle : {st.session_state.user_role}**")
        st.info("ASYMAS BUSINESS v3.0 Hologram")
        if 'theme_choisi' not in st.session_state:
            st.session_state.theme_choisi = "Sombre ASYMAS"
        theme = st.selectbox("🎨", ["Sombre ASYMAS","Bleu Pro","Vert Agri","Noir Luxe"], key="theme_choisi", label_visibility="collapsed")
        if st.button("🔄 Actualiser", key="btn_save"):
            st.cache_data.clear()
            st.rerun()

    if theme=="Sombre ASYMAS":
        st.markdown("""<style>.stApp{background:#0E1117;color:#E0E0E0}h1,h2,h3{color:#14B814!important}</style>""",unsafe_allow_html=True)
    elif theme=="Bleu Pro":
        st.markdown("""<style>.stApp{background:#0A1929;color:#E3F2FD}h1,h2,h3{color:#2196F3!important}</style>""",unsafe_allow_html=True)
    elif theme=="Vert Agri":
        st.markdown("""<style>.stApp{background:#1B2A1B;color:#E8F5E9}h1,h2,h3{color:#4CAF50!important}</style>""",unsafe_allow_html=True)
    elif theme=="Noir Luxe":
        st.markdown("""<style>.stApp{background:#000;color:#FFF}h1,h2,h3{color:#FFD700!important}</style>""",unsafe_allow_html=True)

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

    tabs_dispo = ["📊 Dashboard", "🛍️ Commerce", "📦 Gestion Stock", "🏠 Immobilier", "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures", "📋 Devis", "👥 Utilisateurs"]
    tabs = st.tabs(tabs_dispo)
    tab_map = {name: tab for name, tab in zip(tabs_dispo, tabs)}

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

    # ... garde tout ton code des autres tabs ici tel quel ...
