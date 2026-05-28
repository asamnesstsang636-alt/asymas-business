import streamlit as st
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="ASYMAS", layout="wide")

# === SESSION STATE ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "📊 Dashboard"
if 'user_permissions' not in st.session_state:
    st.session_state.user_permissions = {}

# === SUPABASE ===
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# === LOGIN ===
if not st.session_state.logged_in:
    st.title("🔐 ASYMAS - Connexion")
    username = st.text_input("Nom utilisateur")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter", type="primary"):
        if username == "PDG" and password == "admin123":
            st.session_state.logged_in = True
            st.session_state.user_role = "PDG"
            st.session_state.user_name = "PDG"
            # PDG a toutes les permissions
            st.session_state.user_permissions = {
                "📦 Gestion Stock": True, "🛍️ Commerce": True,
                "🏠 Immobilier": True, "🚗 Automobile": True,
                "💰 Comptabilité": True, "📄 Factures": True
            }
            st.rerun()
        else:
            # Charge depuis Supabase
            df_users = supabase.table("utilisateurs").select("*").eq("nom", username).execute().data
            if df_users and df_users[0]['mot_de_passe'] == password:
                st.session_state.logged_in = True
                st.session_state.user_role = df_users[0]['role']
                st.session_state.user_name = username
                # Charge les permissions
                st.session_state.user_permissions = {
                    "📦 Gestion Stock": bool(df_users[0].get('can_stock', False)),
                    "🛍️ Commerce": bool(df_users[0].get('can_commerce', False)),
                    "🏠 Immobilier": bool(df_users[0].get('can_immo', False)),
                    "🚗 Automobile": bool(df_users[0].get('can_auto', False)),
                    "💰 Comptabilité": bool(df_users[0].get('can_compta', False)),
                    "📄 Factures": bool(df_users[0].get('can_factures', False))
                }
                st.rerun()
            else:
                st.error("Identifiants incorrects")
    st.stop()

# === DASHBOARD ===
st.title(f"ASYMAS - Bonjour {st.session_state.user_name}")

# Hologramme
st.markdown("""
<style>
.holo-container {position: relative; width: 300px; height: 300px; margin: auto;}
.holo-circle {width: 300px; height: 300px; border: 3px solid gold; border-radius: 50%;
box-shadow: 0 0 30px gold, inset 0 0 30px gold; animation: spin 4s linear infinite;}
@keyframes spin {from {transform: rotate(0deg);} to {transform: rotate(360deg);}}
</style>
<div class="holo-container"><div class="holo-circle"></div></div>
""", unsafe_allow_html=True)

# Boutons cliquables sur le hologramme
btn_positions = [
    ("📦 Gestion Stock", 50, 35), ("🛍️ Commerce", 150, 35),
    ("🏠 Immobilier", 50, 135), ("🚗 Automobile", 150, 135),
    ("💰 Comptabilité", 50, 235), ("📄 Factures", 150, 235)
]

for label, left, top in btn_positions:
    clicked = st.button(label, key=f"btn_{label}")
    st.markdown(f"""
    <style>
    div[data-testid="stButton"] button[kind="secondary"]:has(div:contains("{label}")) {{
        position: absolute;
        left: {left}px;
        top: {top}px;
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: transparent;
        border: none;
        z-index: 200;
        cursor: pointer;
        margin-top: -320px;
        margin-left: 0px;
    }}
    </style>
    """, unsafe_allow_html=True)

    if clicked:
        if st.session_state.user_permissions.get(label, False):
            st.session_state.active_tab = label
            st.rerun()
        else:
            st.toast(f"🔒 Accès refusé à {label}. Demande au PDG.", icon="⚠️")

# Onglets
tabs = st.tabs(["📊 Dashboard", "📦 Gestion Stock", "🛍️ Commerce", "🏠 Immobilier",
                "🚗 Automobile", "💰 Comptabilité", "📄 Factures", "👥 Utilisateurs"])
tab_map = dict(zip(["📊 Dashboard", "📦 Gestion Stock", "🛍️ Commerce", "🏠 Immobilier",
                    "🚗 Automobile", "💰 Comptabilité", "📄 Factures", "👥 Utilisateurs"], tabs))
