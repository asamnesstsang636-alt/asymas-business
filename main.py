import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide", initial_sidebar_state="auto")
st.markdown("""<meta name="mobile-web-app-capable" content="yes">""", unsafe_allow_html=True)

from supabase import create_client, Client
from datetime import date, datetime
from fpdf import FPDF
import tempfile, os, json, qrcode
from streamlit_qrcode_scanner import qrcode_scanner

# === SESSION STATE ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'selected_module' not in st.session_state:
    st.session_state.selected_module = None

# === CSS ===
st.markdown("""
<style>
.block-container{padding:0!important;max-width:100%!important;}
.main{background:#0a0a0a;margin:0;padding:0;}
div[data-testid="stTextInput"]{position:absolute!important; bottom:8%!important; left:50%!important; transform:translateX(-50%)!important; width:180px!important; z-index:100!important;}
div[data-testid="stTextInput"] input{background:rgba(0,0,0,0.9)!important; border:2px solid #FFD700!important; border-radius:10px!important; color:#FFD700!important; text-align:center!important; padding:10px!important;}
div[data-testid="stTextInput"] label{display:none!important;}
</style>
""", unsafe_allow_html=True)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=60)
def load_table(table_name):
    try:
        data = supabase.table(table_name).select("*").order("id", desc=True).execute()
        return pd.DataFrame(data.data)
    except:
        return pd.DataFrame()

# === LOGIN ===
if not st.session_state.logged_in:
    st.markdown("""
    <div style="position:relative;width:100vw;height:100vh;background:radial-gradient(ellipse at center 55%, rgba(255,215,0,0.7) 0%, rgba(15,15,15,1) 85%);overflow:hidden;">
        <div style="position:absolute;bottom:10%;left:50%;transform:translateX(-50%);width:340px;height:170px;background:linear-gradient(145deg,#2d2d2d,#1a1a1a);border-radius:45px;box-shadow:0 35px 70px rgba(0,0,0,0.9);border:3px solid #444;"></div>
        <div style="position:absolute;top:45%;left:50%;transform:translate(-50%,-50%);width:450px;height:450px;">
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:380px;height:380px;border:2px solid rgba(255,215,0,0.5);border-radius:50%;box-shadow:0 0 80px rgba(255,215,0,0.8);animation:pulseRing 3s ease-in-out infinite;"></div>
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:300px;height:300px;border:2px dotted rgba(255,215,0,0.9);border-radius:50%;animation:rotate 15s linear infinite;"></div>
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:220px;height:220px;border:3px solid #FFD700;border-radius:50%;box-shadow:0 0 90px #FFD700;"></div>
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:170px;height:170px;background:radial-gradient(circle,#FFD700 0%,#FFA500 100%);border-radius:50%;box-shadow:0 0 100px #FFD700;display:flex;flex-direction:column;align-items:center;justify-content:center;animation:pulseCart 2s ease-in-out infinite;">
                <div style="font-size:50px;">🛒</div>
                <div style="font-size:16px;font-weight:bold;color:#000;margin-top:5px;">ASYMAS</div>
            </div>
        </div>
    </div>
    <style>@keyframes pulseRing{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}50%{transform:translate(-50%,-50%) scale(1.12);opacity:1;}}
    @keyframes pulseCart{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.18);}}
    @keyframes rotate{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}</style>
    """, unsafe_allow_html=True)

    pwd = st.text_input("", type="password", placeholder="Mot de passe ASYMAS")
    if pwd == "asymas2025":
        st.session_state.logged_in = True
        st.session_state.user_role = "PDG"
        st.session_state.user_name = "PDG"
        st.rerun()
    st.stop()

# === ACCUEIL AVEC 6 BOUTONS CLIQUABLES SUR LE CERCLE ===
html_buttons = """
<div style="position:relative;width:100%;height:700px;background:radial-gradient(ellipse at center 55%, rgba(255,215,0,0.7) 0%, rgba(15,15,15,1) 85%);overflow:hidden;">
    <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:450px;height:450px;pointer-events:none;">
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:380px;height:380px;border:2px solid rgba(255,215,0,0.5);border-radius:50%;box-shadow:0 0 80px rgba(255,215,0,0.8);animation:pulseRing 3s ease-in-out infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:300px;height:300px;border:2px dotted rgba(255,215,0,0.9);border-radius:50%;animation:rotate 15s linear infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:220px;height:220px;border:3px solid #FFD700;border-radius:50%;box-shadow:0 0 90px #FFD700;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:170px;height:170px;background:radial-gradient(circle,#FFD700 0%,#FFA500 100%);border-radius:50%;box-shadow:0 0 100px #FFD700;display:flex;flex-direction:column;align-items:center;justify-content:center;animation:pulseCart 2s ease-in-out infinite;">
            <div style="font-size:50px;">🛒</div>
            <div style="font-size:16px;font-weight:bold;color:#000;margin-top:5px;">ASYMAS</div>
        </div>
    </div>
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Commerce'}, '*')" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(90deg) translate(190px) rotate(-90deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🏪<br>Commerce</button>
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Auto'}, '*')" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(30deg) translate(190px) rotate(-30deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🚚<br>Auto</button>
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Factures'}, '*')" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-30deg) translate(190px) rotate(30deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🧾<br>Factures</button>
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Immo'}, '*')" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-90deg) translate(190px) rotate(90deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🏠<br>Immo</button>
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Stock'}, '*')" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-150deg) translate(190px) rotate(150deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">📦<br>Stock</button>
    <button onclick="window.parent.postMessage({type:'streamlit:setComponentValue', value:'Compta'}, '*')" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(150deg) translate(190px) rotate(-150deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">📊<br>Compta</button>
</div>
<style>@keyframes pulseRing{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}50%{transform:translate(-50%,-50%) scale(1.12);opacity:1;}}
@keyframes pulseCart{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.18);}}
@keyframes rotate{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}</style>
"""

clicked = components.html(html_buttons, height=700)
if clicked:
    st.session_state.selected_module = clicked
    st.rerun()

if st.button("🚪 Déconnexion"):
    st.session_state.clear()
    st.rerun()

# === AFFICHAGE MODULE ===
if st.session_state.selected_module:
    st.divider()
    col1, col2 = st.columns([6,1])
    with col1:
        st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
        st.markdown(f"### {st.session_state.selected_module}")
    with col2:
        if st.button("← Retour"):
            st.session_state.selected_module = None
            st.rerun()

    table_map = {
        "Commerce": "articles", "Stock": "articles", "Immo": "biens",
        "Auto": "voitures", "Compta": "compta", "Factures": "factures_proforma"
    }
    df = load_table(table_map.get(st.session_state.selected_module, "articles"))
    st.dataframe(df, use_container_width=True)
else:
    # === TON ANCIEN CODE TABS ===
    st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
    st.markdown("### Agriculture • Commerce • Immobilier • Automobile • Beni RDC")

    with st.sidebar:
        st.markdown(f"## 👤 {st.session_state.user_name}")
        st.markdown(f"**Rôle : {st.session_state.user_role}**")
        st.info("ASYMAS BUSINESS v3.0 Hologram")
        if 'theme_choisi' not in st.session_state:
            st.session_state.theme_choisi = "Sombre ASYMAS"
        theme = st.selectbox("🎨", ["Sombre ASYMAS","Bleu Pro","Vert Agri","Noir Luxe"], key="theme_choisi", label_visibility="collapsed")
        if st.button("🔄 Actualiser", key="btn_save"):
            st.cache_data.clear()
            st.rerun()

    if theme=="Sombre ASYMAS":
        st.markdown("""<style>.stApp{background:#0E1117;color:#E0E0E0}h1,h2,h3{color:#14B814!important}</style>""",unsafe_allow_html=True)
    elif theme=="Bleu Pro":
        st.markdown("""<style>.stApp{background:#0A1929;color:#E3F2FD}h1,h2,h3{color:#2196F3!important}</style>""",unsafe_allow_html=True)
    elif theme=="Vert Agri":
        st.markdown("""<style>.stApp{background:#1B2A1B;color:#E8F5E9}h1,h2,h3{color:#4CAF50!important}</style>""",unsafe_allow_html=True)
    elif theme=="Noir Luxe":
        st.markdown("""<style>.stApp{background:#000;color:#FFF}h1,h2,h3{color:#FFD700!important}</style>""",unsafe_allow_html=True)

    df_biens = load_table("biens")
    df_articles = load_table("articles")
    df_voitures = load_table("voitures")
    df_compta = load_table("compta")
    df_factures = load_table("factures_proforma")
    df_devis = load_table("devis")
    df_utilisateurs = load_table("utilisateurs")

    if 'montant' not in df_compta.columns:
        df_compta['montant'] = 0
    if 'type' not in df_compta.columns:
        df_compta['type'] = 'Inconnu'
    if 'date' in df_compta.columns:
        df_compta['date'] = pd.to_datetime(df_compta['date'], errors='coerce')
        df_compta = df_compta.sort_values('date', ascending=False)

    tabs_dispo = ["📊 Dashboard", "🛍️ Commerce", "📦 Gestion Stock", "🏠 Immobilier", "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures", "📋 Devis", "👥 Utilisateurs"]
    tabs = st.tabs(tabs_dispo)
    tab_map = {name: tab for name, tab in zip(tabs_dispo, tabs)}

    with tab_map["📊 Dashboard"]:
        st.markdown("## 📊 Dashboard ASYMAS")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🏠 Biens", len(df_biens))
        col2.metric("📦 Articles", len(df_articles))
        col3.metric("🚗 Voitures", len(df_voitures))
        if not df_compta.empty and 'type' in df_compta.columns and 'montant' in df_compta.columns:
            revenus = df_compta[df_compta['type']=='Revenu']['montant'].sum()
            col4.metric("💰 Revenus", f"{revenus:,.0f} FC")
        else:
            col4.metric("💰 Revenus", "0 FC")
        st.divider()
        if not df_compta.empty:
            st.subheader("📈 Dernières transactions")
            st.dataframe(df_compta.head(10), use_container_width=True)

    # === TAB COMMERCE ===
    with tab_map["🛍️ Commerce"]:
        st.markdown("## 🛍️ Commerce - Point de Vente")
        if not df_articles.empty:
            df_disp = df_articles[df_articles['stock'] > 0] if 'stock' in df_articles.columns else df_articles
            st.dataframe(df_disp, use_container_width=True)
        else:
            st.info("Aucun article trouvé")

    # === TAB GESTION STOCK ===
    with tab_map["📦 Gestion Stock"]:
        st.markdown("## 📦 Gestion Stock Commerce")
        st.dataframe(df_articles, use_container_width=True)

    # === TAB IMMOBILIER ===
    with tab_map["🏠 Immobilier"]:
        st.markdown("## 🏠 Immobilier")
        st.dataframe(df_biens, use_container_width=True)

    # === TAB AUTOMOBILE ===
    with tab_map["🚗 Automobile"]:
        st.markdown("## 🚗 Automobile")
        st.dataframe(df_voitures, use_container_width=True)

    # === TAB GESTION PARC ===
    with tab_map["🚘 Gestion Parc"]:
        st.markdown("## 🚘 Gestion Parc Automobile")
        st.dataframe(df_voitures, use_container_width=True)

    # === TAB COMPTABILITÉ ===
    with tab_map["💰 Comptabilité"]:
        st.markdown("## 💰 Comptabilité ASYMAS")
        if not df_compta.empty and 'type' in df_compta.columns and 'montant' in df_compta.columns:
            total_rev = df_compta[df_compta['type']=='Revenu']['montant'].sum()
            total_dep = df_compta[df_compta['type']=='Dépense']['montant'].sum()
            solde = total_rev - total_dep
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Revenus", f"{total_rev:,.0f} FC")
            col2.metric("💸 Dépenses", f"{total_dep:,.0f} FC")
            col3.metric("💎 Solde", f"{solde:,.0f} FC")
        st.dataframe(df_compta, use_container_width=True, hide_index=True)

    # === TAB FACTURES ===
    with tab_map["📄 Factures"]:
        st.markdown("## 📄 Gestion Factures & Proformas")
        st.dataframe(df_factures, use_container_width=True, hide_index=True)

    # === TAB DEVIS ===
    with tab_map["📋 Devis"]:
        st.markdown("## 📋 Devis ASYMAS Consulting")
        st.dataframe(df_devis, use_container_width=True, hide_index=True)

    # === TAB UTILISATEURS ===
    with tab_map["👥 Utilisateurs"]:
        st.markdown("## 👥 Gestion Utilisateurs")
        st.dataframe(df_utilisateurs, use_container_width=True, hide_index=True)
# ==================== FLOKI SOLDAT COMPLET ====================
class FLOKI:
    def __init__(self, supabase_client, dataframes):
        self.supabase = supabase_client
        self.df = dataframes

    def ask(self, question):
        q = question.lower().strip()
        if any(g in q for g in ["slt", "salut", "bonjour", "hello", "yo"]):
            return "Présent chef. FLOKI opérationnel. Donnez l'ordre."
        if "voiture" in q and ("moins cher" in q or "prix" in q):
            return self._get_voiture_moins_cher()
        if "voiture" in q and ("liste" in q or "donne" in q):
            return self._get_voitures_stock()
        rep = self._search_product(q)
        if rep: 
            return rep + "\n\nSource: ASYMAS"
        return f"Négatif chef. Rien de vérifiable pour '{question}'."

    def _get_voiture_moins_cher(self):
        if self.df['voitures'].empty:
            return "Pas de données voitures chef."
        prix_col = next((col for col in ['prix', 'prix_vente', 'prix_achat', 'montant'] if col in self.df['voitures'].columns), None)
        if not prix_col:
            return "Chef, je ne trouve pas la colonne prix dans voitures."
        dispo = self.df['voitures'][self.df['voitures'].get('quantite', 1) > 0]
        if dispo.empty:
            return "Aucune voiture en stock chef."
        moins_chere = dispo.loc[dispo[prix_col].idxmin()]
        modele = moins_chere.get('modele', moins_chere.get('nom', 'N/A'))
        prix = float(moins_chere[prix_col])
        return f"Voiture la moins chère: {modele} à {prix:,.0f} FC"

    def _get_voitures_stock(self):
        if self.df['voitures'].empty:
            return "Pas de données voitures chef."
        dispo = self.df['voitures'][self.df['voitures'].get('quantite', 0) > 0]
        if dispo.empty:
            return "Aucune voiture en stock chef."
        txt = "\n".join([f"- {r.get('modele', r.get('nom', 'N/A'))}: {int(r.get('quantite', 0))} unités - {float(r.get('prix', r.get('prix_vente', 0))):,.0f} FC" for _, r in dispo.iterrows()])
        return f"Voitures en stock:\n{txt}"

    def _search_product(self, q):
        if self.df['articles'].empty:
            return None
        articles = self.df['articles'].copy()
        articles['nom_clean'] = articles['nom_article'].astype(str).str.lower().str.replace(r'[^a-z0-9\s]', '', regex=True).str.replace(r'\s+', ' ', regex=True).str.strip()
        q_clean = re.sub(r'[^a-z0-9\s]', '', q).strip()
        mots_q = [w for w in q_clean.split() if len(w) > 2]
        if mots_q:
            for _, r in articles.iterrows():
                if all(word in r['nom_clean'] for word in mots_q):
                    return f"{r['nom_article']}: Stock {int(r['stock'])} unités, Prix {float(r['prix_vente']):,.0f} FC"
        return None

# ==================== INIT FLOKI APRÈS CHARGEMENT DATA ====================
if 'floki' not in st.session_state:
    dataframes = {
        "articles": df_articles if not df_articles.empty else pd.DataFrame(),
        "compta": df_compta if not df_compta.empty else pd.DataFrame(),
        "biens": df_biens if not df_biens.empty else pd.DataFrame(),
        "voitures": df_voitures if not df_voitures.empty else pd.DataFrame()
    }
    st.session_state.floki = FLOKI(supabase, dataframes)

# ==================== SIDEBAR FLOKI ====================
with st.sidebar:
    st.divider()
    st.markdown("### 🤖 FLOKI")
    st.caption("Conseiller du PDG - Comprend le système ASYMAS")
    q = st.text_input("Ordre pour FLOKI", key="floki_input", placeholder="Ex: liste de mes voitures, voiture moins cher, CA du mois")
    if st.button("Exécuter", type="primary", use_container_width=True):
        if q:
            with st.spinner("FLOKI réfléchit..."):
                rep = st.session_state.floki.ask(q)
                st.session_state.floki_rep = rep
    if 'floki_rep' in st.session_state:
        st.success(st.session_state.floki_rep)
