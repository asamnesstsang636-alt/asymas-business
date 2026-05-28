import streamlit as st
import pandas as pd
st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide")

from supabase import create_client, Client
from datetime import date, datetime
import json

# === SESSION STATE INIT ===
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'user_permissions' not in st.session_state:
    st.session_state.user_permissions = {}
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# === SUPABASE ===
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=60)
def load_table(table_name):
    try:
        data = supabase.table(table_name).select("*").order("id", desc=True).execute()
        return pd.DataFrame(data.data)
    except Exception as e:
        st.error(f"Erreur chargement {table_name}: {e}")
        return pd.DataFrame()

df_utilisateurs = load_table("utilisateurs")

# === LOGIN SIMPLE SANS CSS CASSÉ ===
if not st.session_state.user_role:
    st.markdown("<h1 style='text-align:center;color:#FFD700'>ASYMAS BUSINESS</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;color:#fff'>Connexion</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        pwd = st.text_input("Mot de passe", type="password", placeholder="Tape ton mot de passe")
        if st.button("Se connecter", use_container_width=True, type="primary"):
            if pwd == "asymas2025":
                st.session_state.user_role = "PDG"
                st.session_state.user_name = "PDG"
                st.session_state.user_permissions = {
                    "dashboard": True, "commerce": True, "stock": True, "immobilier": True,
                    "automobile": True, "parc": True, "comptabilite": True, "factures": True,
                    "devis": True, "users": True, "supprimer": True
                }
                st.rerun()
            else:
                user_row = df_utilisateurs[df_utilisateurs['password'] == pwd]
                if not user_row.empty:
                    st.session_state.user_role = user_row.iloc[0]['role']
                    st.session_state.user_name = user_row.iloc[0]['nom']
                    perms = user_row.iloc[0].get('permissions', {})
                    if isinstance(perms, str):
                        perms = json.loads(perms)
                    st.session_state.user_permissions = perms
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")
    st.stop()

# === APP APRÈS LOGIN ===
st.success(f"Connecté en tant que {st.session_state.user_name}")

# Style app seulement après login
st.markdown("""
<style>
.block-container{padding:1rem!important;max-width:100%!important;}
.main{background:#0a0a0a;}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.user_name}")
    st.markdown(f"**Rôle : {st.session_state.user_role}**")
    if st.button("🚪 Déconnexion", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Chargement données
df_biens = load_table("biens")
df_articles = load_table("articles")
df_voitures = load_table("voitures")
df_compta = load_table("compta")
df_factures = load_table("factures_proforma")

if 'montant' not in df_compta.columns: df_compta['montant'] = 0
if 'type' not in df_compta.columns: df_compta['type'] = 'Inconnu'

# === NAVIGATION HOLOGRAMME ===
if st.session_state.page == "home":
    st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")

    # Hologramme
    st.markdown("""
    <div style="position:relative;width:100%;height:60vh;background:radial-gradient(ellipse at center 55%, rgba(255,215,0,0.7) 0%, rgba(15,15,15,1) 85%);border-radius:20px;">
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:300px;height:300px;border:3px solid #FFD700;border-radius:50%;box-shadow:0 0 90px #FFD700;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:170px;height:170px;background:radial-gradient(circle,#FFD700 0%,#FFA500 100%);border-radius:50%;box-shadow:0 0 100px #FFD700;display:flex;flex-direction:column;align-items:center;justify-content:center;">
            <div style="font-size:50px;">🛒</div>
            <div style="font-size:16px;font-weight:bold;color:#000;margin-top:5px;">ASYMAS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    btn_config = [
        ("🏪", "Commerce", "commerce", 0, -170),
        ("🚚", "Auto", "automobile", 100, -130),
        ("🧾", "Factures", "factures", 100, 130),
        ("🏠", "Immo", "immobilier", 0, 170),
        ("📦", "Stock", "stock", -100, 130),
        ("📊", "Compta", "comptabilite", -100, -130)
    ]

    for icon, label, key, x, y in btn_config:
        if st.button(f"{icon} {label}", key=f"btn_{key}"):
            if st.session_state.user_permissions.get(key, False) or st.session_state.user_role == "PDG":
                st.session_state.page = key
                st.rerun()
            else:
                st.toast(f"🔒 Accès refusé à {label}", icon="⚠️")

        st.markdown(f"""
        <style>
        button[kind="secondary"]:has(div p:contains("{icon} {label}")) {{
            position: absolute;
            left: calc(50% + {x}px);
            top: calc(50% + {y}px);
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: #fff;
            border: 3px solid #FFD700;
            box-shadow: 0 0 20px #FFD700;
            z-index: 999;
            transform: translate(-50%, -50%);
            margin-top: 200px;
        }}
        </style>
        """, unsafe_allow_html=True)

# === PAGES MODULES ===
else:
    if st.button("← Retour Accueil", type="primary"):
        st.session_state.page = "home"
        st.rerun()
    st.divider()

    if st.session_state.page == "stock":
        if not st.session_state.user_permissions.get("stock", False) and st.session_state.user_role!= "PDG":
            st.warning("🔒 Accès refusé")
        else:
            st.markdown("## 📦 Gestion Stock")
            st.dataframe(df_articles, use_container_width=True)

    elif st.session_state.page == "commerce":
        if not st.session_state.user_permissions.get("commerce", False) and st.session_state.user_role!= "PDG":
            st.warning("🔒 Accès refusé")
        else:
            st.markdown("## 🛍️ Commerce")

    elif st.session_state.page == "immobilier":
        if not st.session_state.user_permissions.get("immobilier", False) and st.session_state.user_role!= "PDG":
            st.warning("🔒 Accès refusé")
        else:
            st.markdown("## 🏠 Immobilier")
            st.dataframe(df_biens, use_container_width=True)

    elif st.session_state.page == "automobile":
        if not st.session_state.user_permissions.get("automobile", False) and st.session_state.user_role!= "PDG":
            st.warning("🔒 Accès refusé")
        else:
            st.markdown("## 🚗 Automobile")
            st.dataframe(df_voitures, use_container_width=True)

    elif st.session_state.page == "comptabilite":
        if not st.session_state.user_permissions.get("comptabilite", False) and st.session_state.user_role!= "PDG":
            st.warning("🔒 Accès refusé")
        else:
            st.markdown("## 💰 Comptabilité")
            st.dataframe(df_compta, use_container_width=True)

    elif st.session_state.page == "factures":
        if not st.session_state.user_permissions.get("factures", False) and st.session_state.user_role!= "PDG":
            st.warning("🔒 Accès refusé")
        else:
            st.markdown("## 📄 Factures")
            st.dataframe(df_factures, use_container_width=True)
