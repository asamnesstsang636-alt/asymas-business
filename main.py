import streamlit as st
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide", initial_sidebar_state="auto")

# === SESSION STATE ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'selected_module' not in st.session_state:
    st.session_state.selected_module = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = "Invité"
if 'user_role' not in st.session_state:
    st.session_state.user_role = "Visiteur"

# === CSS POUR LE CERCLE ===
st.markdown("""
<style>
.block-container{padding-top:2rem;}
.main{background:#0a0a0a;}
.circle-container{position:relative;width:500px;height:500px;margin:40px auto;}
.center-circle{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:160px;height:160px;
background:radial-gradient(circle,#FFD700 0%,#FFA500 100%);border-radius:50%;box-shadow:0 0 80px #FFD700;
display:flex;flex-direction:column;align-items:center;justify-content:center;font-weight:bold;font-size:18px;color:#000;}
.module-btn{position:absolute;width:80px;height:80px;border-radius:50%;background:#fff;border:3px solid #FFD700;
box-shadow:0 0 25px #FFD700;font-weight:bold;font-size:11px;color:#000;cursor:pointer;}
</style>
""", unsafe_allow_html=True)

# === SUPABASE ===
SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase URL et KEY doivent être définis dans st.secrets.")
    st.stop()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=60)
def load_table(table_name):
    try:
        data = supabase.table(table_name).select("*").order("id", desc=True).execute()
        return pd.DataFrame(data.data or [])
    except Exception as e:
        st.error(f"Erreur: {e}")
        return pd.DataFrame()

module_authorizations = {
    "PDG": ["Commerce", "Auto", "Factures", "Immo", "Stock", "Compta"],
    "Visiteur": []
}

def is_authorized(module_name: str) -> bool:
    return module_name in module_authorizations.get(st.session_state.user_role, [])

# === APP ===
if st.session_state.logged_in:
    st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")

    if st.button("🚪 Déconnexion", key="logout"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.selected_module is None:
        st.markdown("### Cliquez sur un module pour démarrer")

        # Cercle avec 6 boutons
        st.markdown('<div class="circle-container">', unsafe_allow_html=True)
        st.markdown('<div class="center-circle">🛒<br>ASYMAS</div>', unsafe_allow_html=True)

        # Position des 6 boutons en cercle
        positions = [
            (250, 50), # Commerce - haut
            (400, 125), # Auto - haut droite
            (400, 325), # Factures - bas droite
            (250, 400), # Immo - bas
            (100, 325), # Stock - bas gauche
            (100, 125) # Compta - haut gauche
        ]
        modules = ["Commerce", "Auto", "Factures", "Immo", "Stock", "Compta"]
        emojis = ["🏪", "🚚", "🧾", "🏠", "📦", "📊"]

        for i, mod in enumerate(modules):
            x, y = positions[i]
            if st.button(f"{emojis[i]}\n{mod}", key=f"btn_{mod}"):
                if is_authorized(mod):
                    st.session_state.selected_module = mod
                    st.rerun()
                else:
                    st.warning("Module non autorisé")
            # Positionnement CSS du bouton
            st.markdown(f"""
            <style>button[kind="secondary"][data-testid="baseButton-secondary"]:has(div:contains('{mod}')){{
                position:absolute!important; left:{x}px!important; top:{y}px!important;
                transform:translate(-50%,-50%)!important;
            }}</style>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.divider()
        col1, col2 = st.columns([6,1])
        with col1:
            st.markdown(f"## Module : {st.session_state.selected_module}")
        with col2:
            if st.button("← Accueil", key="back_home"):
                st.session_state.selected_module = None
                st.rerun()
            if st.button("🚪 Déconnexion", key="logout2"):
                st.session_state.clear()
                st.rerun()

        table_map = {
            "Commerce": "articles", "Stock": "articles", "Immo": "biens",
            "Auto": "voitures", "Compta": "compta", "Factures": "factures_proforma"
        }
        df = load_table(table_map.get(st.session_state.selected_module, "articles"))
        st.dataframe(df, use_container_width=True)

else:
    st.markdown("# ASYMAS BUSINESS")
    st.markdown("### Accès sécurisé")
    st.markdown("Cercle désactivé. Entrez le mot de passe pour débloquer.")

    # Cercle grisé quand pas connecté
    st.markdown('<div class="circle-container" style="opacity:0.4;">', unsafe_allow_html=True)
    st.markdown('<div class="center-circle">🛒<br>ASYMAS</div>', unsafe_allow_html=True)
    for i in range(6):
        x, y = positions[i] if 'positions' in locals() else (250, 50)
        st.button("🔒", key=f"locked_{i}", disabled=True)
        st.markdown(f"""
        <style>button[kind="secondary"][data-testid="baseButton-secondary"]:has(div:contains('🔒')){{
            position:absolute!important; left:{x}px!important; top:{y}px!important;
            transform:translate(-50%,-50%)!important;
        }}</style>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    pwd = st.text_input("Code d'accès", type="password", placeholder="asymas2025", key="access_pwd")
    if st.button("Accéder", key="login_button"):
        if pwd == "asymas2025":
            st.session_state.logged_in = True
            st.session_state.user_role = "PDG"
            st.session_state.user_name = "PDG"
            st.session_state.selected_module = None
            st.rerun()
        else:
            st.error("Code incorrect.")
