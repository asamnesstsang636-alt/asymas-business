import streamlit as st
st.set_page_config(page_title="Holo Commerce", layout="wide")
st.markdown("""<style>.main {background: #0a0a0a;}</style>""", unsafe_allow_html=True)
st.markdown("""
<div style="position:relative; text-align:center; padding:130px 0; background:radial-gradient(circle at center, rgba(255,215,0,0.6) 0%, rgba(10,10,10,0.99) 80%); border-radius:40px; margin:20px auto; max-width:1100px; width:95%; overflow:hidden;">
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:500px; height:500px; border:1px solid rgba(255,215,0,0.25); border-radius:50%; box-shadow:0 0 60px rgba(255,215,0,0.5);"></div>
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:380px; height:380px; border:2px dotted rgba(255,215,0,0.7); border-radius:50%; animation:rotate 15s linear infinite;"></div>
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:280px; height:280px; border:3px solid rgba(255,215,0,0.95); border-radius:50%; box-shadow:0 0 80px #FFD700;"></div>
    <div style="position:relative; z-index:10; width:170px; height:170px; margin:0 auto; background:radial-gradient(circle,#FFD700 0%,#FFA500 100%); border-radius:50%; box-shadow:0 0 90px #FFD700, 0 0 180px #FFA500; display:flex; align-items:center; justify-content:center; font-size:85px; animation:pulse 2s ease-in-out infinite;">🛒</div>
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:500px; height:500px;">
        <div style="position:absolute; top:20px; left:50%; transform:translateX(-50%); background:rgba(0,0,0,0.85); backdrop-filter:blur(10px); border:3px solid white; border-radius:50%; width:75px; height:75px; display:flex; align-items:center; justify-content:center; font-size:38px; box-shadow:0 0 35px rgba(255,255,255,0.9);">🏪</div>
        <div style="position:absolute; top:95px; right:40px; background:rgba(0,0,0,0.85); backdrop-filter:blur(10px); border:3px solid white; border-radius:50%; width:75px; height:75px; display:flex; align-items:center; justify-content:center; font-size:38px; box-shadow:0 0 35px rgba(255,255,255,0.9);">📊</div>
        <div style="position:absolute; bottom:95px; right:40px; background:rgba(0,0,0,0.85); backdrop-filter:blur(10px); border:3px solid white; border-radius:50%; width:75px; height:75px; display:flex; align-items:center; justify-content:center; font-size:38px; box-shadow:0 0 35px rgba(255,255,255,0.9);">🧾</div>
        <div style="position:absolute; bottom:20px; left:50%; transform:translateX(-50%); background:rgba(0,0,0,0.85); backdrop-filter:blur(10px); border:3px solid white; border-radius:50%; width:75px; height:75px; display:flex; align-items:center; justify-content:center; font-size:38px; box-shadow:0 0 35px rgba(255,255,255,0.9);">📢</div>
        <div style="position:absolute; bottom:95px; left:40px; background:rgba(0,0,0,0.85); backdrop-filter:blur(10px); border:3px solid white; border-radius:50%; width:75px; height:75px; display:flex; align-items:center; justify-content:center; font-size:38px; box-shadow:0 0 35px rgba(255,255,255,0.9);">@</div>
        <div style="position:absolute; top:95px; left:40px; background:rgba(0,0,0,0.85); backdrop-filter:blur(10px); border:3px solid white; border-radius:50%; width:75px; height:75px; display:flex; align-items:center; justify-content:center; font-size:38px; box-shadow:0 0 35px rgba(255,255,255,0.9);">🚚</div>
    </div>
</div>
<style>
@keyframes pulse {0%,100%{transform:scale(1);box-shadow:0 0 90px #FFD700,0 0 180px #FFA500;}50%{transform:scale(1.2);box-shadow:0 0 110px #FFD700,0 0 220px #FFA500;}}
@keyframes rotate {from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}
</style>
""", unsafe_allow_html=True)
