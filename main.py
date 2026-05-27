import streamlit as st

st.set_page_config(layout="wide", page_title="ASYMAS Business")

# CSS pour positionner le champ dans le cercle blanc de la base
st.markdown("""
<style>
.block-container{padding:0 !important;max-width:100% !important;}
.main{background:linear-gradient(180deg,#1a1a2e 0%,#0a0a0a 100%);margin:0;padding:0;}

/* Positionne le champ dans le cercle blanc en bas */
div[data-testid="stTextInput"]{
    position:absolute !important;
    bottom:8% !important;
    left:50% !important;
    transform:translateX(-50%) !important;
    width:80px !important;
    height:80px !important;
    z-index:100 !important;
}

/* Style du champ pour qu’il remplisse le cercle */
div[data-testid="stTextInput"] input{
    width:80px !important;
    height:80px !important;
    border-radius:50% !important;
    background:rgba(0,0,0,0.7) !important;
    border:3px solid #FFD700 !important;
    color:#FFD700 !important;
    text-align:center !important;
    font-size:12px !important;
    padding:0 !important;
}
div[data-testid="stTextInput"] input::placeholder{
    color:rgba(255,215,0,0.5) !important;
    font-size:10px !important;
}
div[data-testid="stTextInput"] label{display:none !important;}
</style>
""", unsafe_allow_html=True)

# Ton hologramme ASYMAS
st.markdown("""
<div style="position:relative;width:100vw;height:100vh;overflow:hidden;">
    <div style="position:absolute;bottom:5%;left:50%;transform:translateX(-50%);width:300px;height:140px;background:linear-gradient(145deg,#2d2d2d,#1a1a1a);border-radius:35px;box-shadow:0 25px 50px rgba(0,0,0,0.8);border:2px solid #555;"></div>
    
    <div style="position:absolute;top:45%;left:50%;transform:translate(-50%,-50%);width:400px;height:400px;">
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:340px;height:340px;border:2px solid rgba(255,215,0,0.5);border-radius:50%;box-shadow:0 0 60px rgba(255,215,0,0.8);animation:pulseRing 3s ease-in-out infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:260px;height:260px;border:2px dotted rgba(255,215,0,0.9);border-radius:50%;animation:rotate 15s linear infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:180px;height:180px;background:radial-gradient(circle,#FFA500 0%,#FF8C00 100%);border-radius:50%;box-shadow:0 0 70px #FFA500;display:flex;flex-direction:column;align-items:center;justify-content:center;animation:pulseCart 2s ease-in-out infinite;">
            <div style="font-size:40px;">🛒</div>
            <div style="font-size:13px;font-weight:bold;color:#000;margin-top:3px;">ASYMAS</div>
        </div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:340px;height:340px;">
            <div style="position:absolute;top:0;left:50%;transform:translateX(-50%);background:#fff;border:2px solid #FFD700;border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;font-size:22px;">📊</div>
            <div style="position:absolute;top:45px;right:35px;background:#fff;border:2px solid #FFD700;border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;font-size:22px;">🚚</div>
            <div style="position:absolute;bottom:45px;right:35px;background:#fff;border:2px solid #FFD700;border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;font-size:22px;">📢</div>
            <div style="position:absolute;bottom:0;left:50%;transform:translateX(-50%);background:#fff;border:2px solid #FFD700;border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;font-size:22px;">🧾</div>
            <div style="position:absolute;bottom:45px;left:35px;background:#fff;border:2px solid #FFD700;border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;font-size:22px;">🏪</div>
        </div>
    </div>
</div>
<style>
@keyframes pulseRing{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}50%{transform:translate(-50%,-50%) scale(1.1);opacity:1;}}
@keyframes pulseCart{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.15);}}
@keyframes rotate{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}
</style>
""", unsafe_allow_html=True)

# Champ mot de passe dans le cercle blanc
pwd = st.text_input("", type="password", placeholder="PWD", key="auth")

if pwd:
    if pwd == "asymas2025":
        st.success("Accès autorisé ✅")
        # Ici tu mets ton dashboard
    else:
        st.error("Mot de passe incorrect ❌")
