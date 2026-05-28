import streamlit.components.v1 as components

if not st.session_state.logged_in:
    # ... ton code login reste identique ...
    st.stop()

# === ACCUEIL AVEC BOUTONS QUI TIENTENT ===
html_code = """
<div style="position:relative;width:100%;height:700px;background:radial-gradient(ellipse at center 55%, rgba(255,215,0,0.7) 0%, rgba(15,15,15,1) 85%);overflow:hidden;">
    <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:450px;height:450px;">
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:380px;height:380px;border:2px solid rgba(255,215,0,0.5);border-radius:50%;box-shadow:0 0 80px rgba(255,215,0,0.8);animation:pulseRing 3s ease-in-out infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:300px;height:300px;border:2px dotted rgba(255,215,0,0.9);border-radius:50%;animation:rotate 15s linear infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:220px;height:220px;border:3px solid #FFD700;border-radius:50%;box-shadow:0 0 90px #FFD700;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:170px;height:170px;background:radial-gradient(circle,#FFD700 0%,#FFA500 100%);border-radius:50%;box-shadow:0 0 100px #FFD700;display:flex;flex-direction:column;align-items:center;justify-content:center;animation:pulseCart 2s ease-in-out infinite;">
            <div style="font-size:50px;">🛒</div>
            <div style="font-size:16px;font-weight:bold;color:#000;margin-top:5px;">ASYMAS</div>
        </div>
    </div>
    
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Commerce'}, '*')" 
    style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(90deg) translate(190px) rotate(-90deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;z-index:999;">🏪<br>Commerce</button>
    
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Auto'}, '*')" 
    style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(30deg) translate(190px) rotate(-30deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;z-index:999;">🚚<br>Auto</button>
    
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Factures'}, '*')" 
    style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-30deg) translate(190px) rotate(30deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;z-index:999;">🧾<br>Factures</button>
    
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Immo'}, '*')" 
    style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-90deg) translate(190px) rotate(90deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;z-index:999;">🏠<br>Immo</button>
    
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Stock'}, '*')" 
    style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-150deg) translate(190px) rotate(150deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;z-index:999;">📦<br>Stock</button>
    
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Compta'}, '*')" 
    style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(150deg) translate(190px) rotate(-150deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;z-index:999;">📊<br>Compta</button>
</div>

<style>@keyframes pulseRing{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}50%{transform:translate(-50%,-50%) scale(1.12);opacity:1;}}
@keyframes pulseCart{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.18);}}
@keyframes rotate{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}</style>
"""

clicked = components.html(html_code, height=700)

if clicked:
    st.session_state.selected_module = clicked
    st.rerun()

# Bouton déconnexion
if st.button("🚪 Déconnexion"):
    st.session_state.clear()
    st.rerun()

# Affichage module
if st.session_state.get('selected_module'):
    st.divider()
    st.markdown(f"### {st.session_state.selected_module}")
    if st.button("← Retour"):
        st.session_state.selected_module = None
        st.rerun()
    
    df = load_table(st.session_state.selected_module.lower())
    st.dataframe(df, use_container_width=True)
