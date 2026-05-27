if "🛍️ Commerce" in tab_map:
    with tab_map["🛍️ Commerce"]:
        st.markdown("""
        <div style="position:relative; text-align:center; padding:70px 0; background:radial-gradient(circle at center, rgba(255,215,0,0.4) 0%, rgba(0,0,0,0.9) 70%); border-radius:30px; margin-bottom:40px; overflow:hidden;">
            <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:320px; height:320px; border:1px solid rgba(255,215,0,0.2); border-radius:50%; box-shadow:0 0 30px rgba(255,215,0,0.3);"></div>
            <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:250px; height:250px; border:1px dotted rgba(255,215,0,0.4); border-radius:50%; animation:rotate 15s linear infinite;"></div>
            <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:180px; height:180px; border:2px solid rgba(255,215,0,0.6); border-radius:50%; box-shadow:0 0 40px #FFD700;"></div>
            <div style="position:relative; z-index:10; width:120px; height:120px; margin:0 auto; background:radial-gradient(circle,#FFD700 0%,#FFA500 100%); border-radius:50%; box-shadow:0 0 50px #FFD700, 0 0 100px #FFA500; display:flex; align-items:center; justify-content:center; font-size:60px; animation:pulse 2s ease-in-out infinite;">🛒</div>
            <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:320px; height:320px;">
                <div style="position:absolute; top:0; left:50%; transform:translateX(-50%); background:rgba(0,0,0,0.6); backdrop-filter:blur(5px); border:2px solid rgba(255,215,0,0.7); border-radius:50%; width:55px; height:55px; display:flex; align-items:center; justify-content:center; font-size:26px; color:white; box-shadow:0 0 20px rgba(255,215,0,0.6);">🏪</div>
                <div style="position:absolute; top:20%; right:10%; background:rgba(0,0,0,0.6); backdrop-filter:blur(5px); border:2px solid rgba(255,215,0,0.7); border-radius:50%; width:55px; height:55px; display:flex; align-items:center; justify-content:center; font-size:26px; color:white; box-shadow:0 0 20px rgba(255,215,0,0.6);">🚚</div>
                <div style="position:absolute; bottom:20%; right:10%; background:rgba(0,0,0,0.6); backdrop-filter:blur(5px); border:2px solid rgba(255,215,0,0.7); border-radius:50%; width:55px; height:55px; display:flex; align-items:center; justify-content:center; font-size:26px; color:white; box-shadow:0 0 20px rgba(255,215,0,0.6);">📢</div>
                <div style="position:absolute; bottom:0; left:50%; transform:translateX(-50%); background:rgba(0,0,0,0.6); backdrop-filter:blur(5px); border:2px solid rgba(255,215,0,0.7); border-radius:50%; width:55px; height:55px; display:flex; align-items:center; justify-content:center; font-size:26px; color:white; box-shadow:0 0 20px rgba(255,215,0,0.6);">@</div>
                <div style="position:absolute; bottom:20%; left:10%; background:rgba(0,0,0,0.6); backdrop-filter:blur(5px); border:2px solid rgba(255,215,0,0.7); border-radius:50%; width:55px; height:55px; display:flex; align-items:center; justify-content:center; font-size:26px; color:white; box-shadow:0 0 20px rgba(255,215,0,0.6);">@</div>
                <div style="position:absolute; top:20%; left:10%; background:rgba(0,0,0,0.6); backdrop-filter:blur(5px); border:2px solid rgba(255,215,0,0.7); border-radius:50%; width:55px; height:55px; display:flex; align-items:center; justify-content:center; font-size:26px; color:white; box-shadow:0 0 20px rgba(255,215,0,0.6);">📶</div>
            </div>
        </div>
        <style>
        @keyframes pulse {0%, 100% { transform:scale(1); box-shadow:0 0 50px #FFD700, 0 0 100px #FFA500; } 50% { transform:scale(1.15); box-shadow:0 0 70px #FFD700, 0 0 140px #FFA500; }}
        @keyframes rotate {from { transform:translate(-50%,-50%) rotate(0deg); } to { transform:translate(-50%,-50%) rotate(360deg); }}
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("## 🛍️ Commerce - Point de Vente")
