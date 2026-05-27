import streamlit as st

st.set_page_config(layout="wide", page_title="ASYMAS Business")

# CSS : champ positionné dans le petit rectangle en bas de la base
st.markdown("""
<style>
.block-container{padding:0 !important;max-width:100% !important;}
.main{background:#0a0a0a;margin:0;padding:0;}

div[data-testid="stTextInput"]{
    position:absolute !important;
    bottom:28% !important;  /* monté dans le rectangle */
    left:50% !important;
    transform:translateX(-50%) !important;
    width:140px !important;
    height:38px !important;
    z-index:100 !important;
}

div[data-testid="stTextInput"] input{
    width:140px !important;
    height:38px !important;
    background:rgba(20,20,20,0.95) !important;
    border:2px solid #FFD700 !important;
    border-radius:8px !important;
    color:#FFD700 !important;
    text-align:center !important;
    font-size:12px !important;
    padding:0 !important;
}
div[data-testid="stTextInput"] label{display:none !important;}
</style>
""", unsafe_allow_html=True)

# Hologramme
st.markdown("""
<div style="position:relative;width:100vw;height:100vh;background:radial-gradient(ellipse at center 55%, rgba(255,215,0,0.6) 0%, rgba(15,15,15,1) 80%);overflow:hidden;">
    <div style="position:absolute;bottom:12%;left:50%;transform:translateX(-50%);width:320px;height:160px;background:linear-gradient(145deg,#2d2d2d,#1a1a1a);border-radius:40px;box-shadow:0 30px 60px rgba(0,0,0,0.9);border:3px solid #444;"></div>
    <div style="position:absolute;top:48%;left:50%;transform:translate(-50%,-50%);width:420px;height:420px;">
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:360px;height:360px;border:2px solid rgba(255,215,0,0.5);border-radius:50%;box-shadow:0 0 70px rgba(255,215,0,0.8);animation:pulseRing 3s ease-in-out infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:280px;height:280px;border:2px dotted rgba(255,215,0,0.9);border-radius:50%;animation:rotate 15s linear infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:200px;height:200px;border:3px solid #FFD700;border-radius:50%;box-shadow:0 0 80px #FFD700;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:150px;height:150px;background:radial-gradient(circle,#FFD700 0%,#FFA500 100%);border-radius:50%;box-shadow:0 0 90px #FFD700;display:flex;flex-direction:column;align-items:center;justify-content:center;animation:pulseCart 2s ease-in-out infinite;">
            <div style="font-size:45px;">🛒</div>
            <div style="font-size:14px;font-weight:bold;color:#000;margin-top:5px;">ASYMAS</div>
        </div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:360px;height:360px;">
            <div style="position:absolute;top:5px;left:50%;transform:translateX(-50%);background:#fff;border:3px solid #FFD700;border-radius:50%;width:55px;height:55px;display:flex;align-items:center;justify-content:center;font-size:26px;">🏪</div>
            <div style="position:absolute;top:50px;right:40px;background:#fff;border:3px solid #FFD700;border-radius:50%;width:55px;height:55px;display:flex;align-items:center;justify-content:center;font-size:26px;">🚚</div>
            <div style="position:absolute;bottom:50px;right:40px;background:#fff;border:3px solid #FFD700;border-radius:50%;width:55px;height:55px;display:flex;align-items:center;justify-content:center;font-size:26px;">📢</div>
            <div style="position:absolute;bottom:-5px;left:50%;transform:translateX(-50%);background:#fff;border:3px solid #FFD700;border-radius:50%;width:55px;height:55px;display:flex;align-items:center;justify-content:center;font-size:26px;">@</div>
            <div style="position:absolute;bottom:50px;left:40px;background:#fff;border:3px solid #FFD700;border-radius:50%;width:55px;height:55px;display:flex;align-items:center;justify-content:center;font-size:26px;">🧾</div>
            <div style="position:absolute;top:50px;left:40px;background:#fff;border:3px solid #FFD700;border-radius:50%;width:55px;height:55px;display:flex;align-items:center;justify-content:center;font-size:26px;">📊</div>
        </div>
    </div>
</div>
<style>
@keyframes pulseRing{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}50%{transform:translate(-50%,-50%) scale(1.12);opacity:1;}}
@keyframes pulseCart{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.18);}}
@keyframes rotate{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}
</style>
""", unsafe_allow_html=True)

# Champ mot de passe dans le rectangle
pwd = st.text_input("", type="password", placeholder="Mot de passe", key="auth_pwd")

if pwd == "asymas2025":
    st.success("Accès autorisé ✅")
elif pwd:
    st.error("Mot de passe incorrect ❌")
