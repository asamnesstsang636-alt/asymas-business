import streamlit as st
import pandas as pd
st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide", initial_sidebar_state="auto")

from supabase import create_client, Client
import json

# === SESSION STATE INIT ===
for key, default in [('page', 'home'), ('user_permissions', {}), ('user_role', None), ('user_name', None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# === SUPABASE ===
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

df_utilisateurs = load_table("utilisateurs")

# === CSS GLOBAL ===
st.markdown("""
<style>
.block-container{padding:0!important;max-width:100%!important;}
.main{background:#0a0a0a;margin:0;padding:0;}
</style>
""", unsafe_allow_html=True)

# === LOGIN ===
if not st.session_state.user_role:
    st.markdown("""
    <div style="position:fixed;bottom:10%;left:50%;transform:translateX(-50%);z-index:1000;background:rgba(0,0,0,0.9);padding:20px;border:2px solid #FFD700;border-radius:15px;">
    """, unsafe_allow_html=True)
    pwd = st.text_input("", type="password", placeholder="Mot de passe ASYMAS", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    if pwd:
        if pwd == "asymas2025":
            st.session_state.user_role = "PDG"
            st.session_state.user_name = "PDG"
            st.session_state.user_permissions = {k:True for k in ["dashboard","commerce","stock","immobilier","automobile","parc","comptabilite","factures","devis","users","supprimer"]}
            st.rerun()
        else:
            user_row = df_utilisateurs[df_utilisateurs['password'] == pwd]
            if not user_row.empty:
                st.session_state.user_role = user_row.iloc[0]['role']
                st.session_state.user_name = user_row.iloc[0]['nom']
                perms = user_row.iloc[0].get('permissions', {})
                if isinstance(perms, str): perms = json.loads(perms)
                st.session_state.user_permissions = perms
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
    st.stop()

# === CHARGEMENT DONNEES ===
df_biens = load_table("biens")
df_articles = load_table("articles")
df_voitures = load_table("voitures")
df_compta = load_table("compta")
df_factures = load_table("factures_proforma")

if 'montant' not in df_compta.columns: df_compta['montant'] = 0
if 'type' not in df_compta.columns: df_compta['type'] = 'Inconnu'

# === SIDEBAR ===
with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.user_name}")
    st.markdown(f"**Rôle : {st.session_state.user_role}**")
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear(); st.rerun()

# === PAGE ACCUEIL : HOLOGRAMME ANIMÉ + BOUTONS SUR LE CERCLE ===
if st.session_state.page == "home":
    st.markdown(f"<h1 style='text-align:center;color:#FFD700'>ASYMAS BUSINESS - {st.session_state.user_name}</h1>", unsafe_allow_html=True)

    # Hologramme animé exact
    st.markdown("""
    <div style="position:relative;width:100vw;height:75vh;background:radial-gradient(ellipse at center 55%, rgba(255,215,0,0.7) 0%, rgba(15,15,15,1) 85%);overflow:hidden;">
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
    <style>
    @keyframes pulseRing{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}50%{transform:translate(-50%,-50%) scale(1.12);opacity:1;}}
    @keyframes pulseCart{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.18);}}
    @keyframes rotate{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}
    </style>
    """, unsafe_allow_html=True)

    # 6 boutons toujours visibles, positionnés sur le cercle
    btn_config = [
        ("🏪", "Commerce", "commerce", 0, -190),
        ("🚚", "Auto", "automobile", 110, -145),
        ("🧾", "Factures", "factures", 110, 145),
        ("🏠", "Immo", "immobilier", 0, 190),
        ("📦", "Stock", "stock", -110, 145),
        ("📊", "Compta", "comptabilite", -110, -145)
    ]

    for icon, label, key, x, y in btn_config:
        if st.button(f"{icon} {label}", key=f"btn_{key}"):
            if st.session_state.user_permissions.get(key, False) or st.session_state.user_role == "PDG":
                st.session_state.page = key
                st.rerun()
            else:
                st.toast(f"🔒 Accès refusé à {label}", icon="⚠️")

        # CSS pour coller le bouton sur le cercle
        st.markdown(f"""
        <style>
        div[data-testid="stButton"] button[kind="secondary"] p:contains("{icon}") {{
            position: absolute!important;
            left: calc(50% + {x}px)!important;
            top: calc(45% + {y}px)!important;
            width: 70px!important;
            height: 70px!important;
            border-radius: 50%!important;
            background: #fff!important;
            border: 3px solid #FFD700!important;
            box-shadow: 0 0 20px #FFD700!important;
            z-index: 999!important;
            transform: translate(-50%, -50%)!important;
            margin-top: -80vh!important;
            display:flex!important;align-items:center!important;justify-content:center!important;
            font-size:11px!important;font-weight:bold!important;
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
