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
if 'user_name' not in st.session_state:
    st.session_state.user_name = "Invité"
if 'user_role' not in st.session_state:
    st.session_state.user_role = "Visiteur"

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

SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase URL et KEY doivent être définis dans st.secrets.")
    st.stop()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=60)
def load_table(table_name):
    try:
        data = supabase.table(table_name).select("*").order("id", desc=True).execute()
        return pd.DataFrame(data.data or [])
    except Exception as e:
        st.error(f"Erreur de chargement de la table {table_name} : {e}")
        return pd.DataFrame()

# === ACCUEIL AVEC 6 BOUTONS CLIQUABLES ===
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
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Commerce'}, '*')" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(90deg) translate(190px) rotate(-90deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🏪<br>Commerce</button>
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Auto'}, '*')" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(30deg) translate(190px) rotate(-30deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🚚<br>Auto</button>
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Factures'}, '*')" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-30deg) translate(190px) rotate(30deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🧾<br>Factures</button>
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Immo'}, '*')" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-90deg) translate(190px) rotate(90deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🏠<br>Immo</button>
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Stock'}, '*')" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-150deg) translate(190px) rotate(150deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">📦<br>Stock</button>
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Compta'}, '*')" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(150deg) translate(190px) rotate(-150deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">📊<br>Compta</button>
</div>
<style>@keyframes pulseRing{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}50%{transform:translate(-50%,-50%) scale(1.12);opacity:1;}}
@keyframes pulseCart{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.18);}}
@keyframes rotate{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}</style>
"""

html_buttons_locked = """
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
    <button disabled style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(90deg) translate(190px) rotate(-90deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:not-allowed;opacity:0.5;">🏪<br>Commerce</button>
    <button disabled style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(30deg) translate(190px) rotate(-30deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:not-allowed;opacity:0.5;">🚚<br>Auto</button>
    <button disabled style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-30deg) translate(190px) rotate(30deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:not-allowed;opacity:0.5;">🧾<br>Factures</button>
    <button disabled style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-90deg) translate(190px) rotate(90deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:not-allowed;opacity:0.5;">🏠<br>Immo</button>
    <button disabled style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-150deg) translate(190px) rotate(150deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:not-allowed;opacity:0.5;">📦<br>Stock</button>
    <button disabled style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(150deg) translate(190px) rotate(-150deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:not-allowed;opacity:0.5;">📊<br>Compta</button>
</div>
<style>@keyframes pulseRing{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}50%{transform:translate(-50%,-50%) scale(1.12);opacity:1;}}
@keyframes pulseCart{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.18);}}
@keyframes rotate{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}</style>
"""

module_authorizations = {
    "PDG": ["Commerce", "Auto", "Factures", "Immo", "Stock", "Compta"],
    "Visiteur": []
}

def is_authorized(module_name: str) -> bool:
    return module_name in module_authorizations.get(st.session_state.user_role, [])

if st.session_state.logged_in:
    st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
    st.markdown("### Page d'accueil")

    if st.button("🚪 Déconnexion", key="logout"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.selected_module is None:
        st.markdown("Cliquez sur un module pour démarrer l'opération. Seules les actions autorisées sont accessibles.")
        clicked = components.html(html_buttons, height=720)
        if clicked:
            if is_authorized(clicked):
                st.session_state.selected_module = clicked
                st.rerun()
            else:
                st.warning("Vous n'êtes pas autorisé à accéder à ce module.")
    else:
        st.divider()
        col1, col2 = st.columns([6,1])
        with col1:
            st.markdown(f"## Module : {st.session_state.selected_module}")
            st.markdown("Sélectionnez une opération dans ce module ou revenez à l'accueil.")
        with col2:
            if st.button("← Accueil", key="back_home"):
                st.session_state.selected_module = None
                st.rerun()
            if st.button("🚪 Déconnexion", key="logout2"):
                st.session_state.clear()
                st.rerun()

        table_map = {
            "Commerce": "articles",
            "Stock": "articles",
            "Immo": "biens",
            "Auto": "voitures",
            "Compta": "compta",
            "Factures": "factures_proforma"
        }
        df = load_table(table_map.get(st.session_state.selected_module, "articles"))
        st.dataframe(df, use_container_width=True)
else:
    st.markdown("# ASYMAS BUSINESS")
    st.markdown("### Accès sécurisé")
    st.markdown("Entrez le mot de passe ci-dessous pour activer les boutons du cercle.")
    components.html(html_buttons_locked, height=720)
    pwd = st.text_input("Code d'accès", type="password", placeholder="Entrez votre mot de passe", key="access_pwd")
    if st.button("Accéder", key="login_button"):
        if pwd == "asymas2025":
            st.session_state.logged_in = True
            st.session_state.user_role = "PDG"
            st.session_state.user_name = "PDG"
            st.session_state.selected_module = None
            st.rerun()
        else:
            st.error("Code incorrect. Réessayez.")
