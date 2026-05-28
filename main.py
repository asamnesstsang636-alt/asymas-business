import streamlit as st
import pandas as pd
st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide", initial_sidebar_state="collapsed")

from supabase import create_client, Client
from datetime import date, datetime

# === SESSION ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

st.markdown("""
<style>
.block-container{padding:0!important;max-width:100%!important;}
.main{background:#0a0a0a;margin:0;padding:0;}
.holo-container{position:relative;width:100%;height:80vh;}
.holo-btn{position:absolute;transform:translate(-50%,-50%);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;
background:#fff;color:#000;font-size:24px;font-weight:bold;cursor:pointer;box-shadow:0 0 20px #FFD700;z-index:10;}
.holo-btn:hover{transform:translate(-50%,-50%) scale(1.15);box-shadow:0 0 40px #FFD700;}
</style>
""", unsafe_allow_html=True)

def afficher_hologramme(avec_boutons=False):
    btn_html = ""
    if avec_boutons:
        btn_html = """
        <button class="holo-btn" style="top:0%;left:50%;" onclick="window.location.href='?module=Commerce'">🏪</button>
        <button class="holo-btn" style="top:22%;left:82%;" onclick="window.location.href='?module=Auto'">🚚</button>
        <button class="holo-btn" style="top:78%;left:82%;" onclick="window.location.href='?module=Factures'">🧾</button>
        <button class="holo-btn" style="top:100%;left:50%;" onclick="window.location.href='?module=Immo'">🏠</button>
        <button class="holo-btn" style="top:78%;left:18%;" onclick="window.location.href='?module=Stock'">📦</button>
        <button class="holo-btn" style="top:22%;left:18%;" onclick="window.location.href='?module=Compta'">📊</button>
        """
    
    st.markdown("""
    <div class="holo-container">
        <div style="position:absolute;top:45%;left:50%;transform:translate(-50%,-50%);width:450px;height:450px;">
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:380px;height:380px;border:2px solid rgba(255,215,0,0.5);border-radius:50%;box-shadow:0 0 80px rgba(255,215,0,0.8);animation:pulseRing 3s ease-in-out infinite;"></div>
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:300px;height:300px;border:2px dotted rgba(255,215,0,0.9);border-radius:50%;animation:rotate 15s linear infinite;"></div>
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:220px;height:220px;border:3px solid #FFD700;border-radius:50%;box-shadow:0 0 90px #FFD700;"></div>
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:170px;height:170px;background:radial-gradient(circle,#FFD700 0%,#FFA500 100%);border-radius:50%;box-shadow:0 0 100px #FFD700;display:flex;flex-direction:column;align-items:center;justify-content:center;animation:pulseCart 2s ease-in-out infinite;">
                <div style="font-size:50px;">🛒</div>
                <div style="font-size:16px;font-weight:bold;color:#000;margin-top:5px;">ASYMAS</div>
            </div>
            """ + btn_html + """
        </div>
    </div>
    <style>
    @keyframes pulseRing{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}50%{transform:translate(-50%,-50%) scale(1.12);opacity:1;}}
    @keyframes pulseCart{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.18);}}
    @keyframes rotate{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}
    </style>
    """, unsafe_allow_html=True)

# === LOGIN ===
if not st.session_state.logged_in:
    afficher_hologramme(avec_boutons=False)
    
    col1,col2,col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<div style='margin-top:-10vh;background:rgba(0,0,0,0.95);padding:20px;border:3px solid #FFD700;border-radius:15px;box-shadow:0 0 30px #FFD700;'>", unsafe_allow_html=True)
        pwd = st.text_input("Accès ASYMAS", type="password", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
    
    if pwd == "asymas2025":
        st.session_state.logged_in = True
        st.rerun()
    elif pwd:
        st.error("Mot de passe incorrect")
    st.stop()

# === APRÈS LOGIN ===
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

module = st.query_params.get("module", None)

afficher_hologramme(avec_boutons=True)

st.divider()

if module == "Commerce":
    st.markdown("## 🛍️ Commerce - Point de Vente")
    st.dataframe(df_articles, use_container_width=True)
elif module == "Stock":
    st.markdown("## 📦 Gestion Stock")
    st.dataframe(df_articles, use_container_width=True)
elif module == "Immo":
    st.markdown("## 🏠 Immobilier")
    st.dataframe(df_biens, use_container_width=True)
elif module == "Auto":
    st.markdown("## 🚗 Automobile")
    st.dataframe(df_voitures, use_container_width=True)
elif module == "Factures":
    st.markdown("## 🧾 Factures")
    st.info("Module factures en cours")
elif module == "Compta":
    st.markdown("## 💰 Comptabilité")
    st.dataframe(df_compta, use_container_width=True)

with st.sidebar:
    st.markdown("## 👤 PDG")
    if st.button("🚪 Déconnexion", width="stretch"):
        st.session_state.clear()
        st.rerun()
