import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import date, datetime, timedelta
from fpdf import FPDF
import tempfile, os, json, qrcode, base64, io
from PIL import Image
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from streamlit_qrcode_scanner import qrcode_scanner
from supabase import create_client, Client

# === CONFIG PAGE ===
st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide", initial_sidebar_state="auto")
st.markdown("""<meta name="mobile-web-app-capable" content="yes">""", unsafe_allow_html=True)

# === SUPABASE ===
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === SESSION STATE ===
for k, v in [('logged_in', False), ('user_role', ""), ('user_name', ""), ('perms', {}),
             ('selected_module', None), ('user_cats', [])].items():
    if k not in st.session_state:
        st.session_state[k] = v

if 'module' in st.query_params and st.session_state.selected_module is None:
    st.session_state.selected_module = st.query_params['module']
    st.rerun()

# === CSS ===
st.markdown("""
<style>
.block-container{padding:0!important;max-width:100%!important;}
.main{background:#0a0a0a;margin:0;padding:0;}
div[data-testid="stTextInput"]{position:absolute!important; bottom:8%!important; left:50%!important;
transform:translateX(-50%)!important; width:180px!important; z-index:100!important;}
div[data-testid="stTextInput"] input{background:rgba(0,0,0,0.9)!important; border:2px solid #FFD700!important;
border-radius:10px!important; color:#FFD700!important; text-align:center!important; padding:10px!important;}
div[data-testid="stTextInput"] label{display:none!important;}
</style>
""", unsafe_allow_html=True)

# === FONCTIONS ===
@st.cache_data(ttl=60)
def load_table(table_name):
    try:
        data = supabase.table(table_name).select("*").order("id", desc=True).execute()
        return pd.DataFrame(data.data)
    except:
        return pd.DataFrame()

def check_perm(key):
    return st.session_state.user_role == "PDG" or st.session_state.perms.get(key, False)

def safe_pdf_txt(txt):
    if txt is None or pd.isna(txt): return ""
    txt = str(txt).replace('—','-').replace('–','-').replace('’',"'").replace('“','"').replace('”','"')
    return ''.join(c if ord(c) < 128 else '?' for c in txt).replace('\n',' ').strip()

def generer_qrcode(data_text):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=3, border=1)
    qr.add_data(data_text); qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name)
    return temp_file.name

def generer_pdf_facture(numero, type_op, client, details_list, montant, devise, tel_client="+243...", periode="", type_facture="Simple"):
    pdf = FPDF(); pdf.add_page(); pdf.set_auto_page_break(auto=False, margin=10)
    pdf.set_fill_color(20, 50, 40); pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 20)
    pdf.set_xy(10, 8); pdf.cell(0, 10, "ASYMAS BUSINESS", ln=True)
    pdf.set_font("Arial", "", 9); pdf.set_xy(10, 16)
    pdf.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
    pdf.set_font("Arial", "B", 10); pdf.set_xy(150, 8)
    titre_fact = "FACTURE N" if type_facture == "Simple" else "PROFORMA N"
    pdf.cell(50, 6, titre_fact, ln=True, align="R")
    pdf.set_font("Arial", "", 10); pdf.set_xy(150, 14)
    pdf.cell(50, 6, safe_pdf_txt(numero), ln=True, align="R")
    pdf.set_font("Arial", "", 9); pdf.set_xy(150, 20)
    pdf.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")
    y_pos = 45; pdf.set_text_color(0, 0, 0); pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 14); pdf.set_xy(10, y_pos)
    pdf.cell(0, 10, f"{type_facture.upper()} {safe_pdf_txt(type_op.upper())}", ln=True, fill=True)
    y_pos += 15; pdf.set_font("Arial", "B", 10)
    pdf.set_xy(10, y_pos); pdf.cell(85, 7, "FACTURE A:", 1, 0, 'L')
    pdf.cell(10, 7, "", 0, 0); pdf.cell(85, 7, "DETAILS PAIEMENT:", 1, 1, 'L')
    y_pos += 7; pdf.set_font("Arial", "", 9)
    pdf.set_xy(10, y_pos); pdf.cell(85, 6, f"Client: {safe_pdf_txt(client)}", 'LR', 0, 'L')
    pdf.cell(10, 6, "", 0, 0); pdf.cell(85, 6, "M-Pesa: +243817264448", 'LR', 1, 'L')
    y_pos += 6; pdf.set_xy(10, y_pos)
    pdf.cell(85, 6, f"Tel: {safe_pdf_txt(tel_client)}", 'LR', 0, 'L')
    pdf.cell(10, 6, "", 0, 0); pdf.cell(85, 6, "Echeance: Immediate", 'LR', 1, 'L')
    y_pos += 14; pdf.set_fill_color(0, 102, 0); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10); pdf.set_xy(10, y_pos)
    pdf.cell(115, 8, "DESIGNATION", 1, 0, 'C', True)
    pdf.cell(25, 8, "QTE", 1, 0, 'C', True)
    pdf.cell(40, 8, f"MONTANT ({safe_pdf_txt(devise)})", 1, 1, 'C', True)
    y_pos += 8; pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 9)
    for item in details_list if isinstance(details_list, list) else [{"nom": details_list, "qte": 1, "pu": montant}]:
        nom = safe_pdf_txt(item.get('nom', '')); qte = item.get('qte', 1)
        pu = item.get('pu', item.get('prix', 0)); montant_item = pu * qte
        pdf.set_xy(10, y_pos); pdf.cell(115, 7, nom, 1, 0, 'L')
        pdf.cell(25, 7, str(qte), 1, 0, 'C'); pdf.cell(40, 7, f"{montant_item:,.0f}", 1, 1, 'R')
        y_pos += 7
    pdf.set_fill_color(255, 204, 0); pdf.set_font("Arial", "B", 11)
    pdf.set_xy(10, y_pos); pdf.cell(140, 10, "MONTANT TOTAL A PAYER", 1, 0, 'R', True)
    pdf.cell(40, 10, f"{montant:,.0f} {safe_pdf_txt(devise)}", 1, 1, 'R', True)
    qr_data = f"ASYMAS BUSINESS\nFacture: {numero}\nType: {type_op}\nClient: {client}\nMontant: {montant:,.0f} {devise}"
    qr_path = generer_qrcode(qr_data); pdf.image(qr_path, x=155, y=y_pos+10, w=25); os.unlink(qr_path)
    return bytes(pdf.output(dest='S'))

def creer_facture_auto(type_op, client, details, montant, devise="FC", details_list=None, tel="+243...", periode="", type_facture="Simple"):
    numero_facture = f"AS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if details_list is None:
        details_list = [{"nom": details, "qte": 1, "pu": montant}]
    pdf_bytes = generer_pdf_facture(numero_facture, type_op, client, details_list, montant, devise, tel, periode, type_facture)
    try:
        data_compta = {
            "type": "Revenu", "description": str(f"{type_op} - {client} - {details}"),
            "montant": float(montant), "date": str(date.today()),
            "utilisateur": st.session_state.user_name, "categorie": str(type_op),
            "devise": str(devise), "numero_facture": str(numero_facture),
            "details": json.dumps(details_list)
        }
        supabase.table("compta").insert(data_compta).execute()
        st.toast(f"✅ Enregistré par {st.session_state.user_name}", icon="✅")
    except Exception as e:
        st.error("❌ ERREUR INSERTION COMPTA"); st.code(repr(e))
    return numero_facture, pdf_bytes

# === LOGIN HOLOGRAMME ===
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
    if pwd:
        result = supabase.table("utilisateurs").select("*").eq("password", pwd).execute()
        if result.data:
            u = result.data[0]
            st.session_state.logged_in = True
            st.session_state.user_role = u['role']
            st.session_state.user_name = u['nom']
            st.session_state.perms = u.get('permissions', {})
            st.session_state.user_cats = u.get('categories_autorisees', [])
            st.rerun()
        elif pwd == "asymas2025":
            st.session_state.logged_in = True
            st.session_state.user_role = "PDG"
            st.session_state.user_name = "PDG"
            st.session_state.perms = {}
            st.rerun()
    st.stop()

# === ACCUEIL CERCLE ===
if st.session_state.selected_module is None:
    html_buttons = """
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
        <button onclick="window.location.search='?module=Commerce'" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(90deg) translate(190px) rotate(-90deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🏪<br>Commerce</button>
        <button onclick="window.location.search='?module=Auto'" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(30deg) translate(190px) rotate(-30deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🚚<br>Auto</button>
        <button onclick="window.location.search='?module=Factures'" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-30deg) translate(190px) rotate(30deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🧾<br>Factures</button>
        <button onclick="window.location.search='?module=Immo'" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-90deg) translate(190px) rotate(90deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">🏠<br>Immo</button>
        <button onclick="window.location.search='?module=Stock'" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-150deg) translate(190px) rotate(150deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">📦<br>Stock</button>
        <button onclick="window.location.search='?module=Compta'" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(150deg) translate(190px) rotate(-150deg);width:60px;height:60px;border:3px solid #FFD700;border-radius:50%;background:#fff;box-shadow:0 0 25px #FFD700;font-size:11px;font-weight:bold;color:#000;cursor:pointer;">📊<br>Compta</button>
    </div>
    <style>@keyframes pulseRing{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}50%{transform:translate(-50%,-50%) scale(1.12);opacity:1;}}
    @keyframes pulseCart{0%,100%{transform:translate(-50%,-50%) scale(1);}50%{transform:translate(-50%,-50%) scale(1.18);}}
    @keyframes rotate{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}</style>
    """
    components.html(html_buttons, height=700)
    if st.button("🚪 Déconnexion"):
        st.session_state.clear(); st.rerun()

# === VERIF DROIT MODULE ===
elif st.session_state.selected_module:
    perm_map = {"Commerce": "commerce", "Stock": "stock", "Immo": "immobilier",
                "Auto": "automobile", "Compta": "comptabilite", "Factures": "factures"}
    perm_key = perm_map.get(st.session_state.selected_module, "")
    if not check_perm(perm_key):
        st.error(f"⛔ Vous n'avez pas l'autorisation d'accéder au module {st.session_state.selected_module}")
        if st.button("← Retour Accueil"):
            st.session_state.selected_module = None; st.query_params.clear(); st.rerun()
        st.stop()

    st.divider()
    col1, col2 = st.columns([6,1])
    with col1:
        st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
        st.markdown(f"### {st.session_state.selected_module}")
    with col2:
        if st.button("← Retour"):
            st.session_state.selected_module = None; st.query_params.clear(); st.rerun()

    table_map = {"Commerce": "articles", "Stock": "articles", "Immo": "biens",
                 "Auto": "voitures", "Compta": "compta", "Factures": "factures_proforma"}
    df = load_table(table_map.get(st.session_state.selected_module, "articles"))
    st.dataframe(df, use_container_width=True)

# === TABS COMPLETS ===
else:
    with st.sidebar:
        st.markdown(f"## 👤 {st.session_state.user_name}")
        st.markdown(f"**Rôle : {st.session_state.user_role}**")
        st.info("ASYMAS BUSINESS v3.0")
        if st.button("🏠 Retour Accueil"):
            st.session_state.selected_module = None; st.query_params.clear(); st.rerun()
        if st.button("🔄 Actualiser"):
            st.cache_data.clear(); st.rerun()
        if st.button("🔒 Déconnexion"):
            st.session_state.clear(); st.rerun()

    df_biens = load_table("biens")
    df_articles = load_table("articles")
    df_voitures = load_table("voitures")
    df_compta = load_table("compta")
    df_factures = load_table("factures_proforma")
    df_devis = load_table("devis")
    df_utilisateurs = load_table("utilisateurs")

    if 'montant' not in df_compta.columns: df_compta['montant'] = 0
    if 'type' not in df_compta.columns: df_compta['type'] = 'Inconnu'
    if 'date' in df_compta.columns:
        df_compta['date'] = pd.to_datetime(df_compta['date'], errors='coerce')
        df_compta = df_compta.sort_values('date', ascending=False)

    tabs_dispo = ["📊 Dashboard", "🛍️ Commerce", "📦 Gestion Stock", "🏠 Immobilier",
                  "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures",
                  "📋 Devis", "👥 Utilisateurs"]
    tabs = st.tabs(tabs_dispo)
    tab_map = {name: tab for name, tab in zip(tabs_dispo, tabs)}

    perms = st.session_state.perms
    is_pdg = st.session_state.user_role == "PDG"

    # === DASHBOARD ===
    with tab_map["📊 Dashboard"]:
        st.markdown("## 📊 Dashboard ASYMAS")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🏠 Biens", len(df_biens))
        col2.metric("📦 Articles", len(df_articles))
        col3.metric("🚗 Voitures", len(df_voitures))
        revenus = df_compta[df_compta['type']=='Revenu']['montant'].sum() if not df_compta.empty else 0
        col4.metric("💰 Revenus", f"{revenus:,.0f} FC")
        if not df_compta.empty:
            st.subheader("📈 Dernières transactions")
            st.dataframe(df_compta.head(10), use_container_width=True)

    # === COMMERCE ===
    if "🛍️ Commerce" in tab_map:
        with tab_map["🛍️ Commerce"]:
            if not (is_pdg or perms.get('commerce', False)):
                st.error("⛔ Vous n'avez pas l'autorisation Commerce")
            else:
                st.markdown("## 🛍️ Commerce - Point de Vente")
                if 'panier_commerce' not in st.session_state:
                    st.session_state.panier_commerce = []
                if 'vente_finie' not in st.session_state:
                    st.session_state.vente_finie = False
                if 'pdf_data' not in st.session_state:
                    st.session_state.pdf_data = None
                if 'num_fact' not in st.session_state:
                    st.session_state.num_fact = None
                if 'client_com_nom' not in st.session_state:
                    st.session_state.client_com_nom = ""
                if 'client_com_tel' not in st.session_state:
                    st.session_state.client_com_tel = "+243..."

                col_gauche, col_droite = st.columns([2,1])
                with col_gauche:
                    st.subheader("👤 Client")
                    st.session_state.client_com_nom = st.text_input("Nom Client", value=st.session_state.client_com_nom, key="nom_client_c")
                    st.session_state.client_com_tel = st.text_input("Téléphone Client", value=st.session_state.client_com_tel, key="tel_client_c")
                    st.subheader("🔍 Scanner QR Code")
                    qr_code = qrcode_scanner(key='qr_commerce_unique')
                    recherche_manuelle = st.text_input("🔎 Recherche manuelle", placeholder="Tape le nom...", key="search_man_c")

                    df_articles_filtre = df_articles[df_articles['stock'] > 0].copy() if not df_articles.empty else pd.DataFrame()
                    if qr_code:
                        qr_clean = str(qr_code).strip().upper()
                        df_articles_filtre = df_articles_filtre[df_articles_filtre['code_qr'].astype(str).str.strip().str.upper() == qr_clean]
                        if not df_articles_filtre.empty:
                            st.success(f"✅ QR Trouvé : {df_articles_filtre.iloc[0]['nom_article']}")
                        else:
                            st.error(f"❌ QR {qr_code} : Produit introuvable")
                    elif recherche_manuelle:
                        mask = df_articles_filtre['nom_article'].str.contains(recherche_manuelle, case=False, na=False)
                        df_articles_filtre = df_articles_filtre[mask]

                    if df_articles_filtre.empty:
                        st.warning("⚠️ Aucun produit disponible")
                    else:
                        options_articles = [f"{p['nom_article']} | Stock:{int(p['stock'])} | {p['prix_vente']:,.0f} FC | ID:{p['id']}"
                                            for _, p in df_articles_filtre.iterrows()]
                        article_choisi = st.selectbox("Sélectionne le produit", options_articles, key="select_article_unique")
                        if article_choisi:
                            id_choisi = int(article_choisi.split("ID:")[1])
                            p = df_articles_filtre[df_articles_filtre['id'] == id_choisi].iloc[0]
                            c1, c2, c3 = st.columns(3)
                            qte_max = int(p['stock'])
                            qte = c1.number_input("Quantité", min_value=1, max_value=qte_max, value=1, key="qte_c_unique")
                            c2.metric("Stock dispo", qte_max)
                            c3.metric("Prix unitaire", f"{p['prix_vente']:,.0f} FC")
                            if st.button("🛒 AJOUTER AU PANIER", type="primary", width="stretch"):
                                existant = next((item for item in st.session_state.panier_commerce if item['id'] == int(p['id'])), None)
                                if existant:
                                    if existant['qte'] + qte <= qte_max:
                                        existant['qte'] += qte
                                    else:
                                        st.error(f"Stock insuffisant! Max: {qte_max}")
                                else:
                                    st.session_state.panier_commerce.append({
                                        "id": int(p['id']), "nom": str(p['nom_article']),
                                        "pu": float(p['prix_vente']), "qte": int(qte), "stock_max": qte_max
                                    })
                                st.rerun()

                with col_droite:
                    st.subheader("🛒 Panier")
                    total_panier = 0
                    for i, item in enumerate(st.session_state.panier_commerce):
                        c1, c2, c3 = st.columns([4,2,1])
                        c1.write(f"**{item['nom']}**")
                        c2.write(f"Qté: {item['qte']}")
                        if c3.button("❌", key=f"d_{i}"):
                            st.session_state.panier_commerce.pop(i); st.rerun()
                        total_panier += item['qte'] * item['pu']
                    st.metric("💰 Total", f"{total_panier:,.0f} FC")
                    if st.button("💾 FINALISER VENTE", type="primary", width="stretch"):
                        if st.session_state.client_com_nom and st.session_state.panier_commerce:
                            num_fact = f"VTE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            details_list = [{"nom": item['nom'], "qte": item['qte'], "pu": item['pu']} for item in st.session_state.panier_commerce]
                            pdf_bytes = generer_pdf_facture(num_fact, "Vente Commerce", st.session_state.client_com_nom, details_list, total_panier, "FC", st.session_state.client_com_tel)
                            for item in st.session_state.panier_commerce:
                                supabase.table("articles").update({"stock": item['stock_max'] - item['qte']}).eq("id", item['id']).execute()
                            st.session_state.pdf_data = pdf_bytes
                            st.session_state.num_fact = num_fact
                            st.session_state.vente_finie = True
                            st.session_state.panier_commerce = []
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Nom client obligatoire")

                    if st.session_state.vente_finie and st.session_state.pdf_data:
                        st.download_button("📥 Télécharger Facture", data=st.session_state.pdf_data, file_name=f"{st.session_state.num_fact}.pdf", mime="application/pdf", width="stretch")
                        if st.button("Nouvelle Vente"):
                            st.session_state.vente_finie = False; st.session_state.pdf_data = None; st.session_state.num_fact = None; st.session_state.client_com_nom = ""; st.rerun()

    # === GESTION STOCK ===
    if "📦 Gestion Stock" in tab_map:
        with tab_map["📦 Gestion Stock"]:
            if not (is_pdg or perms.get('stock', False)):
                st.error("⛔ Vous n'avez pas l'autorisation Gestion Stock")
            else:
                st.markdown("## 📦 Gestion Stock")
                st.dataframe(df_articles, use_container_width=True)

    # === IMMOBILIER ===
    if "🏠 Immobilier" in tab_map:
        with tab_map["🏠 Immobilier"]:
            if not (is_pdg or perms.get('immobilier', False)):
                st.error("⛔ Vous n'avez pas l'autorisation Immobilier")
            else:
                st.markdown("## 🏠 Immobilier")
                st.dataframe(df_biens, use_container_width=True)

    # === AUTOMOBILE ===
    if "🚗 Automobile" in tab_map:
        with tab_map["🚗 Automobile"]:
            if not (is_pdg or perms.get('automobile', False)):
                st.error("⛔ Vous n'avez pas l'autorisation Automobile")
            else:
                st.markdown("## 🚗 Automobile")
                st.dataframe(df_voitures, use_container_width=True)

    # === COMPTABILITÉ ===
    if "💰 Comptabilité" in tab_map:
        with tab_map["💰 Comptabilité"]:
            if not (is_pdg or perms.get('comptabilite', False)):
                st.error("⛔ Vous n'avez pas l'autorisation Comptabilité")
            else:
                st.markdown("## 💰 Comptabilité")
                st.dataframe(df_compta, use_container_width=True)

    # === FACTURES ===
    if "📄 Factures" in tab_map:
        with tab_map["📄 Factures"]:
            if not (is_pdg or perms.get('factures', False)):
                st.error("⛔ Vous n'avez pas l'autorisation Factures")
            else:
                st.markdown("## 📄 Factures")
                st.dataframe(df_compta[df_compta['numero_facture'].notna()], use_container_width=True)

    # === DEVIS ===
    if "📋 Devis" in tab_map:
        with tab_map["📋 Devis"]:
            if not (is_pdg or perms.get('devis_industriel', False) or perms.get('devis_batiment', False)):
                st.error("⛔ Vous n'avez pas l'autorisation Devis")
            else:
                st.markdown("## 📋 Devis")
                st.dataframe(df_devis, use_container_width=True)

    # === UTILISATEURS ===
    if "👥 Utilisateurs" in tab_map:
        with tab_map["👥 Utilisateurs"]:
            if not (is_pdg or perms.get('users', False)):
                st.error("⛔ Vous n'avez pas l'autorisation Utilisateurs")
            else:
                st.markdown("## 👥 Gestion Utilisateurs")
                st.dataframe(df_utilisateurs[['nom', 'role']], use_container_width=True)
