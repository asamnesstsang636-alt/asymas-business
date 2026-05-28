import streamlit as st
import pandas as pd
st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<meta name="mobile-web-app-capable" content="yes">""", unsafe_allow_html=True)

from supabase import create_client, Client

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'selected_module' not in st.session_state: st.session_state.selected_module = None

st.markdown("""
<style>
.block-container{padding:0!important;max-width:100%!important;margin-top:-80px!important;}
.main{background:#0a0a0a;margin:0;padding:0;}
div[data-testid="stTextInput"]{position:absolute!important; bottom:8%!important; left:50%!important; transform:translateX(-50%)!important; width:180px!important; z-index:100!important;}
div[data-testid="stTextInput"] input{background:rgba(0,0,0,0.9)!important; border:2px solid #FFD700!important; border-radius:10px!important; color:#FFD700!important; text-align:center!important; padding:10px!important;}
div[data-testid="stTextInput"] label{display:none!important;}
div[data-testid="stButton"] button{width:60px!important;height:60px!important;border:3px solid #FFD700!important;border-radius:50%!important;background:#fff!important;box-shadow:0 0 20px #FFD700!important;font-size:24px!important;padding:0!important;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1.1;}
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

def show_login():
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
        st.rerun()
    st.stop()

def show_home():
    # Container relatif de 650px de haut pour forcer le centrage
    st.markdown('<div style="position:relative;width:100%;height:650px;background:radial-gradient(ellipse at center 55%, rgba(255,215,0,0.7) 0%, rgba(15,15,15,1) 85%);overflow:hidden;">', unsafe_allow_html=True)

    # Le cercle centré
    st.markdown("""
    <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:450px;height:450px;">
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:380px;height:380px;border:2px solid rgba(255,215,0,0.5);border-radius:50%;box-shadow:0 0 80px rgba(255,215,0,0.8);animation:pulseRing 3s ease-in-out infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:300px;height:300px;border:2px dotted rgba(255,215,0,0.9);border-radius:50%;animation:rotate 15s linear infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:220px;height:220px;border:3px solid #FFD700;border-radius:50%;box-shadow:0 0 90px #FFD700;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:170px;height:170px;background:radial-gradient(circle,#FFD700 0%,#FFA500 100%);border-radius:50%;box-shadow:0 0 100px #FFD700;display:flex;flex-direction:column;align-items:center;justify-content:center;animation:pulseCart 2s ease-in-out infinite;">
            <div style="font-size:50px;">🛒</div>
            <div style="font-size:16px;font-weight:bold;color:#000;margin-top:5px;">ASYMAS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Boutons positionnés par rapport au centre du container
    positions = [
        {"top": "50%", "left": "50%", "transform": "translate(-50%,-50%) rotate(0deg) translate(190px) rotate(0deg)"},
        {"top": "50%", "left": "50%", "transform": "translate(-50%,-50%) rotate(60deg) translate(190px) rotate(-60deg)"},
        {"top": "50%", "left": "50%", "transform": "translate(-50%,-50%) rotate(120deg) translate(190px) rotate(-120deg)"},
        {"top": "50%", "left": "50%", "transform": "translate(-50%,-50%) rotate(180deg) translate(190px) rotate(-180deg)"},
        {"top": "50%", "left": "50%", "transform": "translate(-50%,-50%) rotate(240deg) translate(190px) rotate(-240deg)"},
        {"top": "50%", "left": "50%", "transform": "translate(-50%,-50%) rotate(300deg) translate(190px) rotate(-300deg)"}
    ]

    labels = ["🏪\nCommerce", "🚚\nAuto", "🧾\nFactures", "🏠\nImmo", "📦\nStock", "📊\nCompta"]
    modules = ["Commerce", "Auto", "Factures", "Immo", "Stock", "Compta"]

    for i in range(6):
        st.markdown(f'<div style="position:absolute;top:{positions[i]["top"]};left:{positions[i]["left"]};transform:{positions[i]["transform"]};z-index:10;">', unsafe_allow_html=True)
        if st.button(labels[i], key=f"btn_{modules[i]}"):
            st.session_state.selected_module = modules[i]
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Bouton déconnexion
    st.markdown('<div style="position:absolute;top:20px;right:20px;z-index:20;">', unsafe_allow_html=True)
    if st.button("🚪 Déconnexion", key="logout"):
        st.session_state.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.logged_in:
    show_login()
else:
    show_home()

    if st.session_state.selected_module:
        st.divider()
        col1, col2 = st.columns([6,1])
        with col1:
            st.markdown(f"### {st.session_state.selected_module}")
        with col2:
            st.button("← Retour", key="back", on_click=lambda: st.session_state.update(selected_module=None))

        if st.session_state.selected_module == "Commerce":
            df = load_table("articles")
            st.dataframe(df, use_container_width=True)
        elif st.session_state.selected_module == "Stock":
            df = load_table("articles")
            st.dataframe(df, use_container_width=True)
        elif st.session_state.selected_module == "Immo":
            df = load_table("biens")
            st.dataframe(df, use_container_width=True)
        elif st.session_state.selected_module == "Auto":
            df = load_table("voitures")
            st.dataframe(df, use_container_width=True)
        elif st.session_state.selected_module == "Compta":
            df = load_table("compta")
            st.dataframe(df, use_container_width=True)
        elif st.session_state.selected_module == "Factures":
            df = load_table("factures_proforma")
            st.dataframe(df, use_container_width=True)
