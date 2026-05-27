import streamlit as st

st.set_page_config(page_title="Holo Commerce", layout="wide")

st.markdown("""
<style>
.block-container {padding: 0 !important; max-width: 100% !important;}
.main {background: #000; margin: 0; padding: 0;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="position:relative; width:100vw; height:95vh; background:radial-gradient(circle at center, rgba(255,215,0,0.7) 0%, rgba(10,10,10,1) 60%); overflow:hidden; margin:0;">
    
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:350px; height:350px; border:1px solid rgba(255,215,0,0.3); border-radius:50%; box-shadow:0 0 60px rgba(255,215,0,0.6);"></div>
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:270px; height:270px; border:2px dotted rgba(255,215,0,0.8); border-radius:50%; animation:rotate 15s linear infinite;"></div>
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:200px; height:200px; border:3px solid rgba(255,215,0,1); border-radius:50%; box-shadow:0 0 80px #FFD700;"></div>
    
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:140px; height:140px; background:radial-gradient(circle,#FFD700 0%,#FFA500 100%); border-radius:50%; box-shadow:0 0 90px #FFD700, 0 0 180px #FFA500; display:flex; align-items:center; justify-content:center; font-size:70px; animation:pulse 2s ease-in-out infinite;">🛒</div>
    
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:350px; height:350px;">
        <div style="position:absolute; top:10px; left:50%; transform:translateX(-50%); background:rgba(0,0,0,0.9); border:3px solid white; border-radius:50%; width:65px; height:65px; display:flex; align-items:center; justify-content:center; font-size:32px; box-shadow:0 0 30px rgba(255,255,255,1);">🏪</div>
        <div style="position:absolute; top:70px; right:20px; background:rgba(0,0,0,0.9); border:3px solid white; border-radius:50%; width:65px; height:65px; display:flex; align-items:center; justify-content:center; font-size:32px; box-shadow:0 0 30px rgba(255,255,255,1);">📊</div>
        <div style="position:absolute; bottom:70px; right:20px; background:rgba(0,0,0,0.9); border:3px solid white; border-radius:50%; width:65px; height:65px; display:flex; align-items:center; justify-content:center; font-size:32px; box-shadow:0 0 30px rgba(255,255,255,1);">🧾</div>
        <div style="position:absolute; bottom:10px; left:50%; transform:translateX(-50%); background:rgba(0,0,0,0.9); border:3px solid white; border-radius:50%; width:65px; height:65px; display:flex; align-items:center; justify-content:center; font-size:32px; box-shadow:0 0 30px rgba(255,255,255,1);">📢</div>
        <div style="position:absolute; bottom:70px; left:20px; background:rgba(0,0,0,0.9); border:3px solid white; border-radius:50%; width:65px; height:65px; display:flex; align-items:center; justify-content:center; font-size:32px; box-shadow:0 0 30px rgba(255,255,255,1);">@</div>
        <div style="position:absolute; top:70px; left:20px; background:rgba(0,0,0,0.9); border:3px solid white; border-radius:50%; width:65px; height:65px; display:flex; align-items:center; justify-content:center; font-size:32px; box-shadow:0 0 30px rgba(255,255,255,1);">🚚</div>
    </div>
</div>
<style>
@keyframes pulse {0%,100%{transform:translate(-50%,-50%) scale(1);box-shadow:0 0 90px #FFD700,0 0 180px #FFA500;}50%{transform:translate(-50%,-50%) scale(1.15);box-shadow:0 0 110px #FFD700,0 0 220px #FFA500;}}
@keyframes rotate {from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}
</style>
""", unsafe_allow_html=True)
