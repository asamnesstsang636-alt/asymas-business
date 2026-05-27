import streamlit as st

st.set_page_config(layout="wide")
st.markdown("""
<style>
.block-container {padding:0 !important; max-width:100% !important;}
.main {margin:0; padding:0;}
</style>
""", unsafe_allow_html=True)

# Image de fond : main + téléphone. Tu peux remplacer l'URL par ta propre photo
bg_url = "https://i.imgur.com/8QZ3V7L.jpg"  

st.markdown(f"""
<div style="position:relative; width:100vw; height:100vh; background:url('{bg_url}') center/cover no-repeat; overflow:hidden;">

    <!-- Hologramme positionné au-dessus du téléphone -->
    <div style="position:absolute; top:42%; left:50%; transform:translate(-50%,-50%); width:380px; height:380px;">
        
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:320px; height:320px; border:1px solid rgba(255,215,0,0.4); border-radius:50%; box-shadow:0 0 50px rgba(255,215,0,0.7); animation:pulseRing 3s ease-in-out infinite;"></div>
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:240px; height:240px; border:2px dotted rgba(255,215,0,0.8); border-radius:50%; animation:rotate 12s linear infinite;"></div>
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:170px; height:170px; border:3px solid rgba(255,215,0,1); border-radius:50%; box-shadow:0 0 60px #FFD700;"></div>
        
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:120px; height:120px; background:radial-gradient(circle,#FFD700 0%,#FFA500 100%); border-radius:50%; box-shadow:0 0 70px #FFD700, 0 0 140px #FFA500; display:flex; align-items:center; justify-content:center; font-size:60px; animation:pulseCart 2s ease-in-out infinite;">🛒</div>
        
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:320px; height:320px;">
            <div style="position:absolute; top:5px; left:50%; transform:translateX(-50%); background:rgba(255,255,255,0.15); backdrop-filter:blur(5px); border:2px solid rgba(255,255,255,0.8); border-radius:50%; width:55px; height:55px; display:flex; align-items:center; justify-content:center; font-size:28px; color:white; box-shadow:0 0 20px rgba(255,255,255,0.6);">🏪</div>
            <div style="position:absolute; top:55px; right:15px; background:rgba(255,255,255,0.15); backdrop-filter:blur(5px); border:2px solid rgba(255,255,255,0.8); border-radius:50%; width:55px; height:55px; display:flex; align-items:center; justify-content:center; font-size:28px; color:white; box-shadow:0 0 20px rgba(255,255,255,0.6);">🚚</div>
            <div style="position:absolute; bottom:55px; right:15px; background:rgba(255,255,255,0.15); backdrop-filter:blur(5px); border:2px solid rgba(255,255,255,0.8); border-radius:50%; width:55px; height:55px; display:flex; align-items:center; justify-content:center; font-size:28px; color:white; box-shadow:0 0 20px rgba(255,255,255,0.6);">📢</div>
            <div style="position:absolute; bottom:5px; left:50%; transform:translateX(-50%); background:rgba(255,255,255,0.15); backdrop-filter:blur(5px); border:2px solid rgba(255,255,255,0.8); border-radius:50%; width:55px; height:55px; display:flex; align-items:center; justify-content:center; font-size:28px; color:white; box-shadow:0 0 20px rgba(255,255,255,0.6);">@</div>
            <div style="position:absolute; bottom:55px; left:15px; background:rgba(255,255,255,0.15); backdrop-filter:blur(5px); border:2px solid rgba(255,255,255,0.8); border-radius:50%; width:55px; height:55px; display:flex; align-items:center; justify-content:center; font-size:28px; color:white; box-shadow:0 0 20px rgba(255,255,255,0.6);">@</div>
            <div style="position:absolute; top:55px; left:15px; background:rgba(255,255,255,0.15); backdrop-filter:blur(5px); border:2px solid rgba(255,255,255,0.8); border-radius:50%; width:55px; height:55px; display:flex; align-items:center; justify-content:center; font-size:28px; color:white; box-shadow:0 0 20px rgba(255,255,255,0.6);">📶</div>
        </div>
    </div>
</div>

<style>
@keyframes pulseRing {{0%,100%{{transform:translate(-50%,-50%) scale(1);opacity:0.7;}}50%{{transform:translate(-50%,-50%) scale(1.1);opacity:1;}}}}
@keyframes pulseCart {{0%,100%{{transform:translate(-50%,-50%) scale(1);}}50%{{transform:translate(-50%,-50%) scale(1.2);}}}}
@keyframes rotate {{from{{transform:translate(-50%,-50%) rotate(0deg);}}to{{transform:translate(-50%,-50%) rotate(360deg);}}}}
</style>
""", unsafe_allow_html=True)
