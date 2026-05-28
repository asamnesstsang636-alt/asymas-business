import streamlit as st
import pandas as pd
st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide", initial_sidebar_state="auto")
st.markdown("""<meta name="mobile-web-app-capable" content="yes">""", unsafe_allow_html=True)

from supabase import create_client, Client
from datetime import date, datetime
import json, tempfile, os, qrcode
from fpdf import FPDF
from streamlit_qrcode_scanner import qrcode_scanner

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

# === LOGIN ===
df_utilisateurs = load_table("utilisateurs")

if not st.session_state.user_role:
    pwd = st.text_input("", type="password", placeholder="Mot de passe ASYMAS")
    if not pwd:
        st.stop()
    if pwd == "asymas2025":
        st.session_state.user_role = "PDG"
        st.session_state.user_name = "PDG"
        st.session_state.user_permissions = {
            "dashboard": True, "commerce": True, "stock": True, "immobilier": True,
            "automobile": True, "parc": True, "comptabilite": True, "factures": True,
            "devis": True, "users": True, "supprimer": True
        }
    else:
        user_row = df_utilisateurs[df_utilisateurs['password'] == pwd]
        if not user_row.empty:
            st.session_state.user_role = user_row.iloc[0]['role']
            st.session_state.user_name = user_row.iloc[0]['nom']
            perms = user_row.iloc[0].get('permissions', {})
            if isinstance(perms, str):
                perms = json.loads(perms)
            st.session_state.user_permissions = perms
        else:
            st.error("Mot de passe incorrect")
            st.stop()
    st.rerun()

st.success(f"Accès autorisé ✅ - {st.session_state.user_name}")

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

# === SIDEBAR ===
with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.user_name}")
    st.markdown(f"**Rôle : {st.session_state.user_role}**")
    st.info("ASYMAS BUSINESS v3.0 Hologram")
    if 'theme_choisi' not in st.session_state: st.session_state.theme_choisi = "Sombre ASYMAS"
    theme = st.selectbox("🎨", ["Sombre ASYMAS","Bleu Pro","Vert Agri","Noir Luxe"], key="theme_choisi", label_visibility="collapsed")
    if st.button("🚪 Déconnexion", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    if st.button("🔄 Actualiser", key="btn_save"):
        st.cache_data.clear(); st.rerun()

if theme=="Sombre ASYMAS": st.markdown("""<style>.stApp{background:#0E1117;color:#E0E0E0}h1,h2,h3{color:#14B814!important}</style>""",unsafe_allow_html=True)
elif theme=="Bleu Pro": st.markdown("""<style>.stApp{background:#0A1929;color:#E3F2FD}h1,h2,h3{color:#2196F3!important}</style>""",unsafe_allow_html=True)
elif theme=="Vert Agri": st.markdown("""<style>.stApp{background:#1B2A1B;color:#E8F5E9}h1,h2,h3{color:#4CAF50!important}</style>""",unsafe_allow_html=True)
elif theme=="Noir Luxe": st.markdown("""<style>.stApp{background:#000;color:#FFF}h1,h2,h3{color:#FFD700!important}</style>""",unsafe_allow_html=True)

# === PAGE D'ACCUEIL : HOLOGRAMME + BOUTONS ===
if st.session_state.page == "home":
    st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
    st.markdown("### Agriculture • Commerce • Immobilier • Automobile • Beni RDC")

    # Hologramme
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

    # 6 boutons toujours visibles
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

# === PAGES MODULES ===
else:
    if st.button("← Retour Accueil", type="primary"):
        st.session_state.page = "home"
        st.rerun()
    st.divider()

    # DASHBOARD
    if st.session_state.page == "dashboard":
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

    # STOCK
    elif st.session_state.page == "stock":
        if not st.session_state.user_permissions.get("stock", False) and st.session_state.user_role!= "PDG":
            st.warning("🔒 Accès refusé. Demande l'autorisation au PDG.")
        else:
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

    # COMMERCE
    elif st.session_state.page == "commerce":
        if not st.session_state.user_permissions.get("commerce", False) and st.session_state.user_role!= "PDG":
            st.warning("🔒 Accès refusé. Demande l'autorisation au PDG.")
        else:
            st.markdown("## 🛍️ Commerce - Point de Vente")
            st.info("Colle ici ton code commerce existant")

    # IMMOBILIER
    elif st.session_state.page == "immobilier":
        if not st.session_state.user_permissions.get("immobilier", False) and st.session_state.user_role!= "PDG":
            st.warning("🔒 Accès refusé. Demande l'autorisation au PDG.")
        else:
            st.markdown("## 🏠 Immobilier")
            st.dataframe(df_biens, use_container_width=True)

    # AUTOMOBILE
    elif st.session_state.page == "automobile":
        if not st.session_state.user_permissions.get("automobile", False) and st.session_state.user_role!= "PDG":
            st.warning("🔒 Accès refusé. Demande l'autorisation au PDG.")
        else:
            st.markdown("## 🚗 Automobile")
            st.dataframe(df_voitures, use_container_width=True)

    # COMPTABILITÉ
    elif st.session_state.page == "comptabilite":
        if not st.session_state.user_permissions.get("comptabilite", False) and st.session_state.user_role!= "PDG":
            st.warning("🔒 Accès refusé. Demande l'autorisation au PDG.")
        else:
            st.markdown("## 💰 Comptabilité")
            st.dataframe(df_compta, use_container_width=True)

    # FACTURES
    elif st.session_state.page == "factures":
        if not st.session_state.user_permissions.get("factures", False) and st.session_state.user_role!= "PDG":
            st.warning("🔒 Accès refusé. Demande l'autorisation au PDG.")
        else:
            st.markdown("## 📄 Factures & Proformas")
            st.dataframe(df_factures, use_container_width=True)
