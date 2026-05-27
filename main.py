import streamlit as st

st.set_page_config(page_title="Holo Commerce", layout="wide")

st.markdown("""
<style>
    .main {background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="position:relative; text-align:center; padding:100px 0; background:radial-gradient(circle at center, rgba(255,215,0,0.55) 0%, rgba(10,10,10,0.99) 80%); border-radius:40px; margin:20px auto; max-width:800px; overflow:hidden;">
    
    <!-- Cercles lumineux -->
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:380px; height:380px; border:1px solid rgba(255,215,0,0.2); border-radius:50%; box-shadow:0 0 50px rgba(255,215,0,0.4);"></div>
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:300px; height:300px; border:2px dotted rgba(255,215,0,0.6); border-radius:50%; animation:rotate 16s linear infinite;"></div>
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:220px; height:220px; border:3px solid rgba(255,215,0,0.9); border-radius:50%; box-shadow:0 0 70px #FFD700;"></div>
    
    <!-- Panier central -->
    <div style="position:relative; z-index:10; width:150px; height:150px; margin:0 auto; background:radial-gradient(circle,#FFD700 0%,#FFA500 100%); border-radius:50%; box-shadow:0 0 80px #FFD700, 0 0 150px #FFA500; display:flex; align-items:center; justify-content:center; font-size:75px; animation:pulse 2s ease-in-out infinite;">🛒</div>
    
    <!-- Icônes en cercle -->
    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:380px; height:380px;">
        <div style="position:absolute; top:10px; left:50%; transform:translateX(-50%); background:rgba(0,0,0,0.8); backdrop-filter:blur(10px); border:3px solid rgba(255,255,255,0.9); border-radius:50%; width:65px; height:65px; display:flex; align-items:center; justify-content:center; font-size:32px; color:white; box-shadow:0 0 30px rgba(255,255,255,0.8);">🏪</div>
        
        <div style="position:absolute; top:70px; right:30px; background:rgba(0,0,0,0.8); backdrop-filter:blur(10px); border:3px solid rgba(255,255,255,0.9); border-radius:50%; width:65px; height:65px; display:flex; align-items:center; justify-content:center; font-size:32px; color:white; box-shadow:0 0 30px rgba(255,255,255,0.8);">🧾</div>
        
        <div style="position:absolute; bottom:70px; right:30px; background:rgba(0,0,0,0.8); backdrop-filter:blur(10px); border:3px solid rgba(255,255,255,0.9); border-radius:50%; width:65px; height:65px; display:flex; align-items:center; justify-content:center; font-size:32px; color:white; box-shadow:0 0 30px rgba(255,255,255,0.8);">🚚</div>
        
        <div style="position:absolute; bottom:10px; left:50%; transform:translateX(-50%); background:rgba(0,0,0,0.8); backdrop-filter:blur(10px); border:3px solid rgba(255,255,255,0.9); border-radius:50%; width:65px; height:65px; display:flex; align-items:center; justify-content:center; font-size:32px; color:white; box-shadow:0 0 30px rgba(255,255,255,0.8);">📢</div>
        
        <div style="position:absolute; bottom:70px; left:30px; background:rgba(0,0,0,0.8); backdrop-filter:blur(10px); border:3px solid rgba(255,255,255,0.9); border-radius:50%; width:65px; height:65px; display:flex; align-items:center; justify-content:center; font-size:32px; color:white; box-shadow:0 0 30px rgba(255,255,255,0.8);">@</div>
        
        <div style="position:absolute; top:70px; left:30px; background:rgba(0,0,0,0.8); backdrop-filter:blur(10px); border:3px solid rgba(255,255,255,0.9); border-radius:50%; width:65px; height:65px; display:flex; align-items:center; justify-content:center; font-size:32px; color:white; box-shadow:0 0 30px rgba(255,255,255,0.8);">📶</div>
    </div>
</div>

<style>
@keyframes pulse {
    0%, 100% { transform:scale(1); box-shadow:0 0 80px #FFD700, 0 0 150px #FFA500; }
    50% { transform:scale(1.25); box-shadow:0 0 100px #FFD700, 0 0 200px #FFA500; }
}
@keyframes rotate {
    from { transform:translate(-50%,-50%) rotate(0deg); }
    to { transform:translate(-50%,-50%) rotate(360deg); }
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#FFD700; margin-top:40px;'>HOLO COMMERCE</h1>", unsafe_allow_html=True)
