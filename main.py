import streamlit as st

st.set_page_config(layout="wide")

st.markdown("""<style>.block-container{padding:0 !important;max-width:100% !important;}.main{background:#000;margin:0;padding:0;}</style>""", unsafe_allow_html=True)

st.markdown("""
<div style="position:relative;width:100vw;height:100vh;background:radial-gradient(ellipse at center 55%, rgba(255,215,0,0.5) 0%, rgba(10,10,10,1) 75%);overflow:hidden;">
    <div style="position:absolute;bottom:12%;left:50%;transform:translateX(-50%);width:300px;height:150px;background:linear-gradient(145deg,#3a3a3a,#1f1f1f);border-radius:35px;box-shadow:0 25px 50px rgba(0,0,0,0.9);border:3px solid #444;"></div>
    <div style="position:absolute;top:48%;left:50%;transform:translate(-50%,-50%);width:400px;height:400px;">
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:340px;height:340px;border:1px solid rgba(255,215,0,0.4);border-radius:50%;box-shadow:0 0 60px rgba(255,215,0,0.7);animation:pulseRing 3s ease-in-out infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:260px;height:260px;border:2px dotted rgba(255,215,0,0.8);border-radius:50%;animation:rotate 12s linear infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:180px;height:180px;border:3px solid rgba(255,215,0,1);border-radius:50%;box-shadow:0 0 70px #FFD700;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:130px;height:130px;background:radial-gradient(circle,#FFD700 0%,#FFA500 100%);border-radius:50%;box-shadow:0 0 80px #FFD700,0 0 160px #FFA500;display:flex;align-items:center;justify-content:center;font-size:65px;animation:pulseCart 2s ease-in-out infinite;">🛒</div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:340px;height:340px;">
            <div style="position:absolute;top:8px;left:50%;transform:translateX(-50%);background:rgba(255,255,255,0.9);border:2px solid white;border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 0 25px rgba(255,255,255,0.8);">🏪</div>
            <div style="position:absolute;top:45px;right:35px;background:rgba(255,255,255,0.9);border:2px solid white;border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 0 25px rgba(255,255,255,0.8);">🚚</div>
            <div style="position:absolute;bottom:45px;right:35px;background:rgba(255,255,255,0.9);border:2px solid white;border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 0 25px rgba(255,255,255,0.8);">📢</div>
            <div style="position:absolute;bottom:-5px;left:50%;transform:translateX(-50%);background:rgba(255,255,255,0.9);border:2px solid white;border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 0 25px rgba(255,255,255,0.8);">@</div>
            <div style="position:absolute;bottom:45px;left:35px;background:rgba(255,255,255,0.9);border:2px solid white;border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 0 25px rgba(255,255,255,0.8);">@</div>
            <div style="position:absolute;top:45px;left:35px;background:rgba(255,255,255,0.9);border:2px solid white;border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 0 25px rgba(255,255,255,0.8);">📊</div>
        </div>
    </div>
</div>
<style>
@keyframes pulseRing{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}50%{transform:translate(-50%,-50%) scale(1.1);opacity:1;}}
@keyframes pulseCart{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.2);}}
@keyframes rotate{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}
</style>
""", unsafe_allow_html=True)
