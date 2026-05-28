import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json
import base64
import difflib
import re
import urllib.parse
import requests
from fpdf import FPDF
from supabase import create_client, Client

# === CONFIG SUPABASE ===
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="ASYMAS BUSINESS", layout="wide", page_icon="📊")

# === SESSION STATE ===
if 'show_circle_menu' not in st.session_state:
    st.session_state.show_circle_menu = True
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "📊 Dashboard"
if 'user_role' not in st.session_state:
    st.session_state.user_role = "PDG"
    st.session_state.user_name = "PDG"
    st.session_state.perms = {}
    st.session_state.user_cats = []

# === MENU CIRCULAIRE ASYMAS ===
if st.session_state.show_circle_menu:
    st.markdown("""
    <style>
  .circle-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 75vh;
        background: radial-gradient(circle at center, #FFD700 0%, #1a1a2e 70%);
        border-radius: 20px;
        margin: 20px 0;
        position: relative;
    }
  .circle-menu {
        position: relative;
        width: 450px;
        height: 450px;
        border: 3px solid #FFD700;
        border-radius: 50%;
        animation: rotate 30s linear infinite;
    }
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
  .center-btn {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 160px;
        height: 160px;
        background: linear-gradient(135deg, #FFD700, #FFA500);
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        font-weight: bold;
        font-size: 20px;
        color: #000;
        box-shadow: 0 0 40px #FFD700;
        z-index: 10;
    }
    div[data-testid="stButton"] > button {
        background: white;
        color: black;
        font-weight: bold;
        border-radius: 50%;
        width: 90px;
        height: 90px;
        font-size: 12px;
        box-shadow: 0 0 15px #FFD700;
        animation: counter-rotate 30s linear infinite;
    }
    @keyframes counter-rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(-360deg); }
    }
    div[data-testid="stButton"] > button:hover {
        transform: scale(1.15);
        box-shadow: 0 0 25px #FFD700;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="circle-container"><div class="circle-menu">', unsafe_allow_html=True)
    st.markdown('<div class="center-btn">🛒<br>ASYMAS</div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    # Position des boutons en cercle
    col1, col2, col3 = st.columns([1,1,1])
    if col2.button("🏪\nCommerce", key="circle_Commerce", use_container_width=True):
        st.session_state.show_circle_menu = False
        st.session_state.active_tab = "🛍️ Commerce"
        st.rerun()

    col4, col5, col6 = st.columns([1,3,1])
    if col4.button("📊\nCompta", key="circle_Compta", use_container_width=True):
        st.session_state.show_circle_menu = False
        st.session_state.active_tab = "💰 Comptabilité"
        st.rerun()
    if col6.button("🚗\nAuto", key="circle_Auto", use_container_width=True):
        st.session_state.show_circle_menu = False
        st.session_state.active_tab = "🚗 Automobile"
        st.rerun()

    col7, col8, col9 = st.columns([1,1,1])
    if col7.button("📦\nStock", key="circle_Stock", use_container_width=True):
        st.session_state.show_circle_menu = False
        st.session_state.active_tab = "📦 Gestion Stock"
        st.rerun()
    if col8.button("🏠\nImmo", key="circle_Immo", use_container_width=True):
        st.session_state.show_circle_menu = False
        st.session_state.active_tab = "🏠 Immobilier"
        st.rerun()
    if col9.button("📄\nFactures", key="circle_Factures", use_container_width=True):
        st.session_state.show_circle_menu = False
        st.session_state.active_tab = "📄 Factures"
        st.rerun()

    st.divider()
    if st.button("📋 Voir tous les onglets", width="stretch"):
        st.session_state.show_circle_menu = False
        st.rerun()

    st.stop()

# === TABS PRINCIPAUX ===
tab_names = [
    "📊 Dashboard", "🛍️ Commerce", "📦 Gestion Stock", "🏠 Immobilier",
    "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures",
    "📋 Devis", "👥 Utilisateurs"
]

tab_map_list = st.tabs(tab_names)
tab_map = {name: tab for name, tab in zip(tab_names, tab_map_list)}

with st.sidebar:
    if st.button("🏠 Menu Circulaire"):
        st.session_state.show_circle_menu = True
        st.rerun()

# === FONCTIONS UTILES ===
def get_table_columns(table_name):
    try:
        result = supabase.table(table_name).select("*").limit(1).execute()
        return list(result.data[0].keys()) if result.data else []
    except:
        return []

def safe_pdf_txt(text):
    if pd.isna(text) or text is None:
        return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def generer_pdf_facture(numero, categorie, client, details, total, devise, tel, periode=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(20, 50, 40)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 20)
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, "ASYMAS BUSINESS", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(10, 16)
    pdf.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
    pdf.set_font("Arial", "B", 10)
    pdf.set_xy(150, 8)
    pdf.cell(50, 6, f"Facture: {numero}", ln=True, align="R")
    pdf.set_xy(150, 14)
    pdf.cell(50, 6, f"Date: {date.today()}", ln=True, align="R")
    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"FACTURE - {safe_pdf_txt(categorie).upper()}", ln=True, fill=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"Client: {safe_pdf_txt(client)}", ln=True)
    pdf.cell(0, 8, f"Tel: {safe_pdf_txt(tel)}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(80, 7, "Designation", 1)
    pdf.cell(20, 7, "Qte", 1)
    pdf.cell(30, 7, "PU", 1)
    pdf.cell(30, 7, "Total", 1, ln=True)
    pdf.set_font("Arial", "", 9)
    for item in details:
        pdf.cell(80, 6, safe_pdf_txt(item['nom'])[:40], 1)
        pdf.cell(20, 6, str(item['qte']), 1)
        pdf.cell(30, 6, f"{item['pu']:,.0f}", 1)
        pdf.cell(30, 6, f"{item['qte']*item['pu']:,.0f}", 1, ln=True)
    pdf.ln(3)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(130, 8, "TOTAL:", 0)
    pdf.cell(30, 8, f"{total:,.0f} {devise}", 1, ln=True)
    return bytes(pdf.output(dest='S'))

def creer_facture_auto(categorie, client, details_text, total, devise, details_list, tel, periode="", statut="Proforma"):
    num_fact = f"FACT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    pdf_bytes = generer_pdf_facture(num_fact, categorie, client, details_list, total, devise, tel, periode)
    supabase.table("compta").insert({
        "date": str(date.today()),
        "type": "Revenu",
        "categorie": categorie,
        "description": f"{categorie} - {client}",
        "montant": float(total),
        "devise": devise,
        "numero_facture": num_fact,
        "details": json.dumps(details_list),
        "utilisateur": st.session_state.user_name
    }).execute()
    return num_fact, pdf_bytes

def generer_excel_pro(df, titre, total_rev, total_dep, solde):
    return b"Excel placeholder"

def generer_pdf_devis_consulting(numero, type_devis, client, titre, parcelle, loc, sections, devise, tel, mo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"DEVIS {type_devis} - {numero}", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Client: {client}", ln=True)
    pdf.cell(0, 8, f"Titre: {titre}", ln=True)
    return bytes(pdf.output(dest='S'))

def qrcode_scanner(key="qr"):
    return st.text_input("Scanner QR", key=key)

# === CHARGEMENT DONNEES ===
@st.cache_data
def load_data():
    return {
        "articles": pd.DataFrame(supabase.table("articles").select("*").execute().data or []),
        "compta": pd.DataFrame(supabase.table("compta").select("*").execute().data or []),
        "biens": pd.DataFrame(supabase.table("biens").select("*").execute().data or []),
        "voitures": pd.DataFrame(supabase.table("voitures").select("*").execute().data or []),
        "utilisateurs": pd.DataFrame(supabase.table("utilisateurs").select("*").execute().data or [])
    }

data = load_data()
df_articles = data["articles"]
df_compta = data["compta"]
df_biens = data["biens"]
df_voitures = data["voitures"]
df_utilisateurs = data["utilisateurs"]
perms = st.session_state.perms

# === DASHBOARD ===
if "📊 Dashboard" in tab_map:
    with tab_map["📊 Dashboard"]:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🏠 Biens", len(df_biens))
        col2.metric("📦 Articles", len(df_articles))
        col3.metric("🚗 Voitures", len(df_voitures))
        if not df_compta.empty and 'type' in df_compta.columns and 'montant' in df_compta.columns:
            revenus = df_compta[df_compta['type']=='Revenu']['montant'].sum()
            col4.metric("💰 Revenus", f"{revenus:,.0f} FC")
        elif not df_compta.empty:
            col4.metric("💰 Écritures", len(df_compta))
        else:
            col4.metric("💰 Revenus", "0 FC")

# === COMMERCE ===
if "🛍️ Commerce" in tab_map:
    with tab_map["🛍️ Commerce"]:
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
        if 'last_qr' not in st.session_state:
            st.session_state.last_qr = ""

        col_gauche, col_droite = st.columns([2,1])
        with col_gauche:
            st.subheader("👤 Client")
            st.session_state.client_com_nom = st.text_input("Nom Client", value=st.session_state.client_com_nom, key="nom_client_c")
            st.session_state.client_com_tel = st.text_input("Téléphone Client", value=st.session_state.client_com_tel, key="tel_client_c")
            st.subheader("🔍 Scanner QR Code")
            col_scan1, col_scan2 = st.columns([2,1])
            with col_scan1:
                qr_code = qrcode_scanner(key='qr_commerce_unique')
            with col_scan2:
                recherche_manuelle = st.text_input("🔎 Recherche manuelle", placeholder="Tape le nom...", key="search_man_c")
            if qr_code and qr_code!= st.session_state.last_qr:
                st.session_state.last_qr = qr_code
                st.rerun()

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
                st.success(f"✅ {len(df_articles_filtre)} produit(s) disponible(s)")
                options_articles = []
                for _, p in df_articles_filtre.iterrows():
                    qr_txt = f" | QR:{p['code_qr']}" if 'code_qr' in p and p['code_qr'] else ""
                    prix_usd = f" | {p['prix_vente_usd']:,.2f}$" if 'prix_vente_usd' in p else ""
                    options_articles.append(f"{p['nom_article']} | Stock:{int(p['stock'])} | {p['prix_vente']:,.0f} FC{prix_usd}{qr_txt} | ID:{p['id']}")
                article_choisi = st.selectbox("Sélectionne le produit", options_articles, key="select_article_unique")
                if article_choisi:
                    id_choisi = int(article_choisi.split("ID:")[1])
                    p = df_articles_filtre[df_articles_filtre['id'] == id_choisi].iloc[0]
                    c1, c2, c3 = st.columns(3)
                    qte_max = int(p['stock'])
                    qte = c1.number_input("Quantité", min_value=1, max_value=qte_max, value=1, key="qte_c_unique")
                    c2.metric("Stock dispo", qte_max)
                    c3.metric("Prix unitaire", f"{p['prix_vente']:,.0f} FC")
                    st.info(f"**{p['nom_article']}** | Catégorie: {p.get('categorie','N/A')} | QR: {p.get('code_qr','N/A')}")
                    if st.button("🛒 AJOUTER AU PANIER", type="primary", width="stretch", key="add_article_unique"):
                        existant = next((item for item in st.session_state.panier_commerce if item['id'] == int(p['id'])), None)
                        if existant:
                            if existant['qte'] + qte <= qte_max:
                                existant['qte'] += qte
                                st.success(f"Panier mis à jour: {existant['qte']}x")
                            else:
                                st.error(f"Stock insuffisant! Max dispo: {qte_max}")
                        else:
                            st.session_state.panier_commerce.append({
                                "id": int(p['id']),
                                "nom": str(p['nom_article']),
                                "pu": float(p['prix_vente']),
                                "qte": int(qte),
                                "code_qr": p.get('code_qr',''),
                                "stock_max": qte_max
                            })
                            st.success("Ajouté au panier")
                        st.rerun()
        with col_droite:
            st.subheader("🛒 Panier")
            if st.session_state.vente_finie and st.session_state.pdf_data:
                st.success("✅ Vente enregistrée!")
                st.download_button("📥 Télécharger Facture PDF", data=st.session_state.pdf_data, file_name=f"{st.session_state.num_fact}.pdf", mime="application/pdf", width="stretch")
                pdf_b64 = base64.b64encode(st.session_state.pdf_data).decode()
                st.components.v1.html(f"""<button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">🖨️ IMPRIMER LA FACTURE</button><script>function printPDF() {{const pdfData = 'data:application/pdf;base64,{pdf_b64}';const win = window.open('', '_blank');win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');win.document.close();setTimeout(() => {{ win.print(); }}, 1000);}}</script>""", height=60)
                if st.button("NOUVELLE VENTE", width="stretch"):
                    st.session_state.vente_finie = False
                    st.session_state.pdf_data = None
                    st.session_state.num_fact = None
                    st.session_state.client_com_nom = ""
                    st.session_state.last_qr = ""
                    st.rerun()
            elif not st.session_state.panier_commerce:
                st.info("Panier vide")
            else:
                total_panier = 0
                for i, item in enumerate(st.session_state.panier_commerce):
                    col1, col2, col3 = st.columns([4,2,1])
                    col1.write(f"**{item['nom']}**")
                    col2.write(f"Qté: {item['qte']} | {item['pu']:,.0f} FC")
                    if col3.button("❌", key=f"d_{i}"):
                        st.session_state.panier_commerce.pop(i)
                        st.rerun()
                    total_panier += item['qte'] * item['pu']
                st.markdown(f"### Total: {total_panier:,.0f} FC")
                st.divider()
                if st.button("💾 FINALISER VENTE & FACTURE", width="stretch", type="primary"):
                    if not st.session_state.client_com_nom:
                        st.error("Nom du client obligatoire!")
                    else:
                        try:
                            num_fact = f"VTE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            details_list = []
                            for item in st.session_state.panier_commerce:
                                supabase.table("ventes").insert({"numero_facture": num_fact, "client_nom": st.session_state.client_com_nom, "article_id": item['id'], "quantite": item['qte'], "prix_unitaire": item['pu'], "total": item['qte'] * item['pu']}).execute()
                                stock_actuel = df_articles[df_articles['id'] == item['id']]['stock'].iloc[0]
                                supabase.table("articles").update({"stock": int(stock_actuel - item['qte'])}).eq("id", item['id']).execute()
                                details_list.append({"nom": item['nom'], "qte": item['qte'], "pu": item['pu'], "total": item['qte'] * item['pu']})
                            details_json = json.dumps(details_list)
                            supabase.table("compta").insert({"date": str(date.today()), "type": "Revenu", "categorie": "Vente Commerce", "description": f"Vente - {st.session_state.client_com_nom}", "montant": float(total_panier), "devise": "FC", "numero_facture": num_fact, "details": details_json, "utilisateur": st.session_state.user_name}).execute()
                            pdf_bytes = generer_pdf_facture(num_fact, "Vente Commerce", st.session_state.client_com_nom, details_list, total_panier, "FC", st.session_state.client_com_tel)
                            st.session_state.pdf_data = pdf_bytes
                            st.session_state.num_fact = num_fact
                            st.session_state.vente_finie = True
                            st.session_state.panier_commerce = []
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur finalisation vente")
                            st.code(repr(e))

# === GESTION STOCK ===
if "📦 Gestion Stock" in tab_map:
    with tab_map["📦 Gestion Stock"]:
        st.markdown("## 📦 Gestion Stock Commerce - Articles & Pertes")
        tab_stock, tab_ajout, tab_mvt, tab_pertes = st.tabs(["📊 Stock Actuel", "➕ Ajouter Article", "📈 Mouvements", "⚠️ Pertes & Casses"])
        with tab_stock:
            st.subheader("📊 Stock Actuel Commerce")
            if df_articles.empty:
                st.info("Aucun article en stock")
            else:
                for _, row in df_articles.iterrows():
                    col1, col2, col3, col4 = st.columns([3,1,1,1])
                    with col1:
                        st.write(f"**{row['nom_article']}** - {row.get('categorie','')} - QR:{row.get('code_qr','N/A')}")
                    with col2:
                        stock_val = int(row.get('stock',0))
                        if stock_val < 5:
                            st.error(f"⚠️ Stock: {stock_val}")
                        else:
                            st.success(f"✅ Stock: {stock_val}")
                    with col3:
                        st.write(f"PA: {row.get('prix_achat',0):,.0f}")
                    with col4:
                        st.write(f"PV: {row.get('prix_vente',0):,.0f} FC")
                    with st.expander(f"Modifier/Supprimer {row['nom_article']}"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            new_nom = st.text_input("Nom", value=row['nom_article'], key=f"nom_art_{row['id']}")
                            new_cat = st.text_input("Catégorie", value=row.get('categorie',''), key=f"cat_art_{row['id']}")
                            new_code_qr = st.text_input("Code QR", value=row.get('code_qr',''), key=f"qr_art_{row['id']}")
                        with c2:
                            new_prix_a = st.number_input("Prix Achat FC", value=float(row.get('prix_achat',0)), key=f"pa_art_{row['id']}")
                            new_prix_v = st.number_input("Prix Vente FC", value=float(row.get('prix_vente',0)), key=f"pv_art_{row['id']}")
                            new_prix_usd = st.number_input("Prix Vente $", value=float(row.get('prix_vente_usd',0)), key=f"pusd_art_{row['id']}")
                        with c3:
                            new_stock = st.number_input("Stock", value=int(row.get('stock',0)), key=f"stock_art_{row['id']}")
                        c1, c2 = st.columns(2)
                        if c1.button("✏️ Modifier", key=f"mod_art_{row['id']}", width="stretch"):
                            try:
                                data_update = {"nom_article": str(new_nom), "categorie": str(new_cat), "prix_achat": float(new_prix_a), "prix_vente": float(new_prix_v), "stock": int(new_stock), "code_qr": str(new_code_qr) if new_code_qr else None}
                                colonnes_articles = get_table_columns("articles")
                                if "prix_vente_usd" in colonnes_articles:
                                    data_update["prix_vente_usd"] = float(new_prix_usd)
                                supabase.table("articles").update(data_update).eq("id", int(row['id'])).execute()
                                st.success("Modifié")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur modif")
                                st.code(repr(e))
                        if st.session_state.user_role == "PDG" or perms.get('supprimer', False):
                            if c2.button("🗑️ Supprimer", key=f"del_art_{row['id']}", width="stretch"):
                                try:
                                    supabase.table("articles").delete().eq("id", int(row['id'])).execute()
                                    st.success("Supprimé")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erreur suppression")
                                    st.code(repr(e))
        with tab_ajout:
            st.subheader("➕ Ajouter Nouvel Article Commerce")
            qr_scan_ajout = qrcode_scanner(key='qr_add_article_com')
            if qr_scan_ajout:
                st.success(f"QR scanné : {qr_scan_ajout}")
                st.session_state.qr_code_temp = qr_scan_ajout
            with st.form("form_article_com", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nom = c1.text_input("Nom Article")
                cat = c2.text_input("Catégorie")
                code_qr = c3.text_input("Code QR", value=st.session_state.get('qr_code_temp', ''))
                c1, c2, c3 = st.columns(3)
                prix_achat_fc = c1.number_input("Prix Achat FC", min_value=0.0)
                prix_vente_fc = c2.number_input("Prix Vente FC", min_value=0.0)
                prix_vente_usd = c3.number_input("Prix Vente $", min_value=0.0)
                stock = c1.number_input("Stock Initial", min_value=0)
                if st.form_submit_button("💾 Ajouter Article"):
                    try:
                        data_insert = {"nom_article": str(nom), "categorie": str(cat), "prix_achat": float(prix_achat_fc), "prix_vente": float(prix_vente_fc), "stock": int(stock), "code_qr": str(code_qr) if code_qr else None}
                        colonnes_articles = get_table_columns("articles")
                        if "prix_vente_usd" in colonnes_articles:
                            data_insert["prix_vente_usd"] = float(prix_vente_usd)
                        supabase.table("articles").insert(data_insert).execute()
                        st.success(f"Article {nom} ajouté")
                        if 'qr_code_temp' in st.session_state:
                            del st.session_state.qr_code_temp
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout")
                        st.code(repr(e))
        with tab_mvt:
            st.subheader("📈 Mouvements de Stock Commerce")
            try:
                mvts = supabase.table('mouvements_stock').select("*").order("created_at", desc=True).limit(50).execute().data
            except:
                mvts = []
            if not mvts:
                st.info("Aucun mouvement enregistré")
            else:
                df_mvt = pd.DataFrame(mvts)
                st.dataframe(df_mvt[['article_nom', 'type', 'quantite', 'motif', 'created_by', 'created_at']], use_container_width=True, hide_index=True)
        with tab_pertes:
            st.subheader("⚠️ Déclarer Perte/Casse Article Commerce")
            articles_dispo = df_articles[df_articles['stock'] > 0].copy() if not df_articles.empty else pd.DataFrame()
            if articles_dispo.empty:
                st.warning("Aucun article en stock pour déclarer une perte")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    article_dict = {f"{a['nom_article']} - Stock:{int(a['stock'])}": a for _, a in articles_dispo.iterrows()}
                    article_choisi = st.selectbox("Article abîmé/perdu", list(article_dict.keys()))
                    qte_perte = st.number_input("Quantité abîmée", min_value=1, max_value=int(article_dict[article_choisi]['stock']) if article_choisi else 1)
                with col2:
                    motif_perte = st.selectbox("Motif", ["Casse", "Vol", "Péremption", "Défaut fabrication", "Accident", "Autre"])
                    detail_perte = st.text_area("Détails", placeholder="Ex: Carton mouillé lors livraison")
                    responsable = st.text_input("Déclaré par", value=st.session_state.user_name)
                if article_choisi:
                    article_data = article_dict[article_choisi]
                    valeur_perte = qte_perte * float(article_data.get('prix_achat', 0))
                    st.error(f"💸 Valeur de la perte : {valeur_perte:,.0f} FC")
                if st.button("🚨 ENREGISTRER LA PERTE", type="primary", width="stretch"):
                    if article_choisi and qte_perte > 0:
                        article_data = article_dict[article_choisi]
                        try:
                            nouveau_stock = int(article_data['stock']) - qte_perte
                            supabase.table('articles').update({"stock": nouveau_stock}).eq("id", int(article_data['id'])).execute()
                            supabase.table('mouvements_stock').insert({"article_id": int(article_data['id']), "article_nom": str(article_data['nom_article']), "type": "PERTE", "quantite": -int(qte_perte), "motif": f"{motif_perte} - {detail_perte}", "valeur": float(valeur_perte), "created_by": responsable, "created_at": datetime.now().isoformat()}).execute()
                            st.success(f"✅ Perte enregistrée. Nouveau stock {article_data['nom_article']}: {nouveau_stock}")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur enregistrement perte")
                            st.code(repr(e))
            st.divider()
            st.subheader("📋 Historique Pertes Commerce")
            try:
                pertes = supabase.table('mouvements_stock').select("*").eq("type", "PERTE").order("created_at", desc=True).limit(20).execute().data
            except:
                pertes = []
            if not pertes:
                st.info("Aucune perte enregistrée")
            else:
                total_pertes = sum(p.get('valeur', 0) for p in pertes)
                st.metric("💸 TOTAL PERTES COMMERCE", f"{total_pertes:,.0f} FC")
                for p in pertes:
                    with st.expander(f"🔴 {p.get('article_nom')} - {abs(p.get('quantite',0))} - {p.get('created_at','')[:10]}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Qté perdue:** {abs(p.get('quantite', 0))}")
                            st.write(f"**Valeur:** {p.get('valeur', 0):,.0f} FC")
                        with col2:
                            st.write(f"**Motif:** {p.get('motif', 'N/A')}")
                            st.write(f"**Par:** {p.get('created_by', 'N/A')}")
                        with col3:
                            if st.session_state.user_role == "PDG":
                                if st.button("🗑️ Supprimer", key=f"del_perte_com_{p.get('id')}"):
                                    supabase.table('mouvements_stock').delete().eq("id", p.get('id')).execute()
                                    st.rerun()

# === IMMOBILIER ===
if "🏠 Immobilier" in tab_map:
    with tab_map["🏠 Immobilier"]:
        st.markdown("## 🏠 Immobilier - Générer Facture")
        nom_client = st.text_input("👤 Nom du client", key="nom_client_bien")
        tel_client = st.text_input("Téléphone Client", value="+243...", key="tel_client_bien")
        col1, col2, col3 = st.columns(3)
        with col1:
            type_bien = st.selectbox("Type", ["Maison", "Appartement", "Bureau", "Terrain"], key="type_bien")
            adresse = st.text_input("Adresse", key="adresse_bien")
        with col2:
            prix = st.number_input("💰 Loyer USD", min_value=0.0, key="prix_bien")
            electricite = st.number_input("⚡ Électricité USD", min_value=0.0, key="elec_bien")
        with col3:
            eau = st.number_input("💧 Eau USD", min_value=0.0, key="eau_bien")
            duree_contrat = st.text_input("📅 Durée", placeholder="Ex: 6 mois", key="duree_bien")
        total_mensuel = float(prix) + float(electricite) + float(eau)
        st.info(f"💎 **TOTAL : {total_mensuel:,.2f} USD**")
        if st.button("📄 GÉNÉRER FACTURE PDF", type="primary", width="stretch", key="btn_facture_immo"):
            if nom_client and adresse:
                details_list = [{"nom": f"Loyer {type_bien} | Adresse: {adresse} | Duree: {duree_contrat}", "qte": 1, "pu": prix},
                                {"nom": f"Electricite | {type_bien} - {adresse}", "qte": 1, "pu": electricite},
                                {"nom": f"Eau | {type_bien} - {adresse}", "qte": 1, "pu": eau}]
                        details_text = f"LOUER: {type_bien} | Adresse: {adresse} | Duree Contrat: {duree_contrat} | Loyer: {prix} $ | Electricite: {electricite} $ | Eau: {eau} $"
                        periode = date.today().strftime("%B %Y")
                        num_fact, pdf_bytes = creer_facture_auto("Loyer", nom_client, details_text, total_mensuel, "$", details_list, tel_client, periode, "Proforma")
                        st.success(f"✅ Facture générée : {num_fact}")
                        st.download_button(label="📥 Télécharger Facture PDF", data=bytes(pdf_bytes), file_name=f"{num_fact}.pdf", mime="application/pdf", width="stretch", key="dl_facture_immo")
                        pdf_b64 = base64.b64encode(pdf_bytes).decode()
                        st.components.v1.html(f"""<button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">🖨️ IMPRIMER LA FACTURE</button><script>function printPDF() {{const pdfData = 'data:application/pdf;base64,{pdf_b64}';const win = window.open('', '_blank');win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');win.document.close();setTimeout(() => {{ win.print(); }}, 1000);}}</script>""", height=60)
                        st.cache_data.clear()
                    else:
                        st.error("Nom client + Adresse obligatoires")

# === AUTOMOBILE ===
if "🚗 Automobile" in tab_map:
    with tab_map["🚗 Automobile"]:
        st.markdown("## 🚗 Automobile - Point de Vente")
        if 'panier_voiture' not in st.session_state:
            st.session_state.panier_voiture = []
        if 'vente_auto_finie' not in st.session_state:
            st.session_state.vente_auto_finie = False
        if 'pdf_auto' not in st.session_state:
            st.session_state.pdf_auto = None
        if 'num_fact_auto' not in st.session_state:
            st.session_state.num_fact_auto = None
        if 'client_auto_nom' not in st.session_state:
            st.session_state.client_auto_nom = ""
        if 'client_auto_tel' not in st.session_state:
            st.session_state.client_auto_tel = "+243..."
        if df_voitures.empty:
            st.error("Aucune voiture disponible - Ajoute des voitures dans Gestion Parc")
        else:
            col_gauche, col_droite = st.columns([2,1])
            with col_gauche:
                st.subheader("👤 Client")
                st.session_state.client_auto_nom = st.text_input("Nom Client", value=st.session_state.client_auto_nom, key="nom_client_v")
                st.session_state.client_auto_tel = st.text_input("Téléphone Client", value=st.session_state.client_auto_tel, key="tel_client_v")
                st.subheader("🔍 Choisir Voiture")
                search_qr = st.text_input("QR Code, Plaque, Marque ou Modèle", placeholder="Filtre la liste...", key="search_voiture_qr").strip()
                df_voitures_dispo = df_voitures[(df_voitures['statut'] == 'Disponible') & (df_voitures['quantite'] > 0)]
                if search_qr:
                    search_clean = search_qr.upper()
                    df_voitures_dispo = df_voitures_dispo[df_voitures_dispo['code_qr'].str.contains(search_clean, case=False, na=False) | df_voitures_dispo['plaque'].str.contains(search_clean, case=False, na=False) | df_voitures_dispo['marque'].str.contains(search_clean, case=False, na=False) | df_voitures_dispo['modele'].str.contains(search_clean, case=False, na=False)]
                if df_voitures_dispo.empty:
                    st.warning("⚠️ Aucune voiture disponible")
                else:
                    st.success(f"✅ {len(df_voitures_dispo)} véhicule(s) disponible(s)")
                    options_voitures = []
                    for _, v in df_voitures_dispo.iterrows():
                        options_voitures.append(f"{v['marque']} {v['modele']} {v.get('annee','')} | {v.get('couleur','')} | {v['plaque']} | Stock:{int(v.get('quantite',1))} | {v['prix']:,.0f}$ | ID:{v['id']}")
                    voiture_choisie = st.selectbox("Sélectionne le véhicule", options_voitures, key="select_voiture_unique")
                    if voiture_choisie:
                        id_choisi = int(voiture_choisie.split("ID:")[1])
                        v = df_voitures_dispo[df_voitures_dispo['id'] == id_choisi].iloc[0]
                        c1, c2, c3 = st.columns(3)
                        qte_max = int(v.get('quantite', 1))
                        qte = c1.number_input("Quantité", min_value=1, max_value=qte_max, value=1, key=f"qte_v_unique")
                        c2.metric("Stock dispo", qte_max)
                        c3.metric("Prix unitaire", f"{v['prix']:,.0f}$")
                        st.info(f"**{v['marque']} {v['modele']}** | Couleur: {v.get('couleur','N/A')} | Qualité: {v.get('qualite','N/A')} | QR: {v.get('code_qr','N/A')}")
                        if st.button("🛒 AJOUTER AU PANIER", type="primary", width="stretch", key="add_voiture_unique"):
                            existant = next((item for item in st.session_state.panier_voiture if item['id'] == int(v['id'])), None)
                            if existant:
                                if existant['qte'] + qte <= qte_max:
                                    existant['qte'] += qte
                                    st.success(f"Panier mis à jour: {existant['qte']}x")
                                else:
                                    st.error(f"Stock insuffisant! Max dispo: {qte_max}")
                            else:
                                st.session_state.panier_voiture.append({
                                    "id": int(v['id']),
                                    "nom": f"{v['marque']} {v['modele']} {v.get('annee','')}",
                                    "pu": float(v['prix']),
                                    "qte": int(qte),
                                    "plaque": v.get('plaque',''),
                                    "qualite": v.get('qualite',''),
                                    "code_qr": v.get('code_qr',''),
                                    "stock_max": qte_max
                                })
                                st.success("Ajouté au panier")
                            st.rerun()
            with col_droite:
                st.subheader("🛒 Panier Voiture")
                total_voiture = 0
                if st.session_state.vente_auto_finie and st.session_state.pdf_auto:
                    st.success(f"✅ Vente validée - {st.session_state.total_auto:,.0f} $")
                    st.info(f"📄 Facture: {st.session_state.num_fact_auto}")
                    if st.session_state.pdf_auto:
                        st.download_button(label="📥 TÉLÉCHARGER LE PDF", data=bytes(st.session_state.pdf_auto), file_name=f"{st.session_state.num_fact_auto}.pdf", mime="application/pdf", width="stretch", key="dl_facture_auto")
                    pdf_b64 = base64.b64encode(st.session_state.pdf_auto).decode()
                    st.components.v1.html(f"""<button onclick="printPDFAuto()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">🖨️ IMPRIMER LA FACTURE</button><script>function printPDFAuto() {{const pdfData = 'data:application/pdf;base64,{pdf_b64}';const win = window.open('', '_blank');win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');win.document.close();setTimeout(() => {{ win.print(); }}, 1000);}}</script>""", height=60)
                    if st.button("Nouvelle Vente", width="stretch", key="new_vente_auto"):
                        st.session_state.panier_voiture = []
                        st.session_state.vente_auto_finie = False
                        st.session_state.pdf_auto = None
                        st.session_state.num_fact_auto = None
                        st.session_state.client_auto_nom = ""
                        st.session_state.client_auto_tel = "+243..."
                        st.rerun()
                elif not st.session_state.panier_voiture:
                    st.info("Panier vide")
                else:
                    for idx, item in enumerate(st.session_state.panier_voiture):
                        col1, col2, col3, col4 = st.columns([3,1,1,1])
                        col1.write(f"**{item['nom']}** | {item.get('qualite','')} | {item['plaque']}")
                        col2.write(f"Qté: {item['qte']}")
                        col3.write(f"{item['pu'] * item['qte']:,.2f} $")
                        if col4.button("❌", key=f"del_v_{idx}"):
                            st.session_state.panier_voiture.pop(idx)
                            st.rerun()
                        total_voiture += item['pu'] * item['qte']
                    st.metric("💰 TOTAL VOITURE", f"{total_voiture:,.2f} $")
                    st.markdown(f"**Client:** {st.session_state.client_auto_nom}")
                    st.markdown(f"**Tel:** {st.session_state.client_auto_tel}")
                    if st.button("✅ FINALISER VENTE VOITURE", type="primary", width="stretch"):
                        if st.session_state.client_auto_nom and st.session_state.panier_voiture:
                            try:
                                details_list = [{"nom": f"{item['nom']} | {item.get('qualite','')} | {item['plaque']}", "qte": item['qte'], "pu": item['pu']} for item in st.session_state.panier_voiture]
                                details_text = " | ".join([f"{item['qte']}x {item['nom']} ({item.get('qualite','')})" for item in st.session_state.panier_voiture])
                                num_fact, pdf_bytes = creer_facture_auto("Vente Voiture", st.session_state.client_auto_nom, details_text, total_voiture, "$", details_list, st.session_state.client_auto_tel, "", "Proforma")
                                for item in st.session_state.panier_voiture:
                                    supabase.table("voitures").update({"quantite": item['stock_max'] - item['qte'], "statut": "Vendue" if item['stock_max'] - item['qte'] == 0 else "Disponible"}).eq("id", item['id']).execute()
                                st.session_state.vente_auto_finie = True
                                st.session_state.pdf_auto = pdf_bytes
                                st.session_state.num_fact_auto = num_fact
                                st.session_state.total_auto = total_voiture
                                st.session_state.panier_voiture = []
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur finalisation: {e}")
                        else:
                            st.error("Nom client obligatoire - Remplis à gauche")

# === GESTION PARC ===
if "🚘 Gestion Parc" in tab_map:
    with tab_map["🚘 Gestion Parc"]:
        st.markdown("## 🚘 Gestion Parc Automobile & Pertes")
        tab_ajout_v, tab_liste_v, tab_pertes_v = st.tabs(["➕ Ajouter Voiture", "📋 Liste Voitures", "⚠️ Pertes/Dégâts Voitures"])
        colonnes_voitures = get_table_columns("voitures")
        with tab_ajout_v:
            st.subheader("➕ Ajouter Nouvelle Voiture au Parc")
            with st.form("form_voiture_parc", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                marque = c1.text_input("Marque")
                modele = c2.text_input("Modèle")
                annee = c3.text_input("Année")
                data_insert = {"marque": str(marque), "modele": str(modele), "annee": str(annee)}
                if "plaque" in colonnes_voitures:
                    plaque = c1.text_input("Plaque")
                    data_insert["plaque"] = str(plaque)
                if "couleur" in colonnes_voitures:
                    couleur = c2.text_input("Couleur")
                    data_insert["couleur"] = str(couleur)
                if "kilometrage" in colonnes_voitures:
                    km = c3.number_input("Kilométrage", min_value=0, value=0)
                    data_insert["kilometrage"] = int(km)
                if "carburant" in colonnes_voitures:
                    carburant = c1.selectbox("Carburant", ["Essence", "Diesel", "Hybride", "Électrique"])
                    data_insert["carburant"] = str(carburant)
                if "boite" in colonnes_voitures:
                    boite = c2.selectbox("Boîte", ["Manuelle", "Automatique"])
                    data_insert["boite"] = str(boite)
                if "prix" in colonnes_voitures:
                    prix = c3.number_input("Prix Achat $", min_value=0.0, value=0.0)
                    data_insert["prix"] = float(prix)
                if "statut" in colonnes_voitures:
                    statut = c1.selectbox("Statut", ["Disponible", "En réparation", "Réservée", "Vendue"])
                    data_insert["statut"] = str(statut)
                if "quantite" in colonnes_voitures:
                    quantite = c2.number_input("Quantité en Stock", min_value=1, value=1)
                    data_insert["quantite"] = int(quantite)
                if "qualite" in colonnes_voitures:
                    qualite = c3.selectbox("Qualité", ["Neuf", "Occasion", "Reconditionné"])
                    data_insert["qualite"] = str(qualite)
                if "code_qr" in colonnes_voitures:
                    code_qr = c1.text_input("Code QR", placeholder="Scanner ou générer")
                    data_insert["code_qr"] = str(code_qr)
                if st.form_submit_button("💾 Ajouter Voiture"):
                    try:
                        supabase.table("voitures").insert(data_insert).execute()
                        st.success(f"Voiture {marque} {modele} ajoutée")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout")
                        st.code(repr(e))
        with tab_liste_v:
            st.subheader("📋 Liste des Voitures - Modifier/Supprimer")
            if df_voitures.empty:
                st.info("Aucune voiture")
            else:
                for _, row in df_voitures.iterrows():
                    with st.expander(f"{row['marque']} {row['modele']} - {row.get('plaque','')} - Stock:{row.get('quantite',0)} - {row.get('statut','')}"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            new_marque = st.text_input("Marque", value=row['marque'], key=f"marque_v_{row['id']}")
                            new_modele = st.text_input("Modèle", value=row['modele'], key=f"modele_v_{row['id']}")
                            new_annee = st.text_input("Année", value=row.get('annee',''), key=f"annee_v_{row['id']}")
                        data_update = {"marque": str(new_marque), "modele": str(new_modele), "annee": str(new_annee)}
                        with c2:
                            if "plaque" in colonnes_voitures:
                                new_plaque = st.text_input("Plaque", value=row.get('plaque',''), key=f"plaque_v_{row['id']}")
                                data_update["plaque"] = str(new_plaque)
                            if "couleur" in colonnes_voitures:
                                new_couleur = st.text_input("Couleur", value=row.get('couleur',''), key=f"couleur_v_{row['id']}")
                                data_update["couleur"] = str(new_couleur)
                            if "kilometrage" in colonnes_voitures:
                                km_val = row.get('kilometrage', 0)
                                try:
                                    km_val = int(float(km_val)) if km_val else 0
                                except:
                                    km_val = 0
                                new_km = st.number_input("KM", value=km_val, key=f"km_v_{row['id']}")
                                data_update["kilometrage"] = int(new_km)
                        with c3:
                            if "carburant" in colonnes_voitures:
                                carburant_options = ["Essence", "Diesel", "Hybride", "Électrique"]
                                carb_val = row.get('carburant','Essence')
                                new_carb = st.selectbox("Carburant", carburant_options, index=carburant_options.index(carb_val) if carb_val in carburant_options else 0, key=f"carb_v_{row['id']}")
                                data_update["carburant"] = str(new_carb)
                            if "boite" in colonnes_voitures:
                                boite_options = ["Manuelle", "Automatique"]
                                boite_val = row.get('boite','Manuelle')
                                new_boite = st.selectbox("Boîte", boite_options, index=boite_options.index(boite_val) if boite_val in boite_options else 0, key=f"boite_v_{row['id']}")
                                data_update["boite"] = str(new_boite)
                            if "prix" in colonnes_voitures:
                                new_prix = st.number_input("Prix $", value=float(row.get('prix',0)), key=f"prix_v_{row['id']}")
                                data_update["prix"] = float(new_prix)
                            if "statut" in colonnes_voitures:
                                statut_options = ["Disponible", "En réparation", "Réservée", "Vendue"]
                                statut_val = row.get('statut','Disponible')
                                new_statut = st.selectbox("Statut", statut_options, index=statut_options.index(statut_val) if statut_val in statut_options else 0, key=f"statut_v_{row['id']}")
                                data_update["statut"] = str(new_statut)
                        if "quantite" in colonnes_voitures:
                            new_qte = st.number_input("Stock", value=int(row.get('quantite',1)), min_value=0, key=f"qte_v_{row['id']}")
                            data_update["quantite"] = int(new_qte)
                        if "qualite" in colonnes_voitures:
                            qualite_options = ["Neuf", "Occasion", "Reconditionné"]
                            qualite_val = row.get('qualite','Neuf')
                            new_qualite = st.selectbox("Qualité", qualite_options, index=qualite_options.index(qualite_val) if qualite_val in qualite_options else 0, key=f"qual_v_{row['id']}")
                            data_update["qualite"] = str(new_qualite)
                        if "code_qr" in colonnes_voitures:
                            new_code_qr = st.text_input("Code QR", value=row.get('code_qr',''), key=f"qr_v_{row['id']}")
                            data_update["code_qr"] = str(new_code_qr)
                        c1, c2 = st.columns(2)
                        if c1.button("✏️ Modifier", key=f"mod_v_parc_{row['id']}", width="stretch"):
                            try:
                                supabase.table("voitures").update(data_update).eq("id", int(row['id'])).execute()
                                st.success("Modifié")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur modif")
                                st.code(repr(e))
                        if st.session_state.user_role == "PDG" or perms.get('supprimer', False):
                            if c2.button("🗑️ Supprimer", key=f"del_v_parc_{row['id']}", width="stretch"):
                                try:
                                    supabase.table("voitures").delete().eq("id", int(row['id'])).execute()
                                    st.success("Supprimé")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erreur suppression")
                                    st.code(repr(e))
        with tab_pertes_v:
            st.subheader("⚠️ Déclarer Dégât/Perte Voiture")
            voitures_dispo = df_voitures[df_voitures.get('quantite', 1) > 0].copy() if not df_voitures.empty else pd.DataFrame()
            if voitures_dispo.empty:
                st.warning("Aucune voiture en stock pour déclarer un dégât")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    voiture_dict = {f"{v['marque']} {v['modele']} - {v.get('plaque','')} - Stock:{int(v.get('quantite',1))}": v for _, v in voitures_dispo.iterrows()}
                    voiture_choisie = st.selectbox("Voiture endommagée/perdue", list(voiture_dict.keys()))
                    qte_perte_v = st.number_input("Quantité endommagée", min_value=1, max_value=int(voiture_dict[voiture_choisie].get('quantite',1)) if voiture_choisie else 1)
                with col2:
                    motif_perte_v = st.selectbox("Type de dégât", ["Accident", "Vol", "Incendie", "Panne moteur", "Dégât carrosserie", "Pneus crevés", "Autre"])
                    detail_perte_v = st.text_area("Détails du dégât", placeholder="Ex: Pare-choc avant enfoncé + phare cassé")
                    responsable_v = st.text_input("Déclaré par", value=st.session_state.user_name, key="resp_v")
                if voiture_choisie:
                    voiture_data = voiture_dict[voiture_choisie]
                    valeur_perte_v = qte_perte_v * float(voiture_data.get('prix', 0))
                    st.error(f"💸 Valeur de la perte : {valeur_perte_v:,.2f} $")
                if st.button("🚨 ENREGISTRER DÉGÂT VOITURE", type="primary", width="stretch"):
                    if voiture_choisie and qte_perte_v > 0:
                        voiture_data = voiture_dict[voiture_choisie]
                        try:
                            nouveau_stock_v = int(voiture_data.get('quantite',1)) - qte_perte_v
                            nouveau_statut = "En réparation" if nouveau_stock_v > 0 else "Endommagée"
                            supabase.table('voitures').update({"quantite": nouveau_stock_v, "statut": nouveau_statut}).eq("id", int(voiture_data['id'])).execute()
                            supabase.table('mouvements_stock').insert({"article_id": int(voiture_data['id']), "article_nom": f"{voiture_data['marque']} {voiture_data['modele']} - {voiture_data.get('plaque','')}", "type": "PERTE_VOITURE", "quantite": -int(qte_perte_v), "motif": f"{motif_perte_v} - {detail_perte_v}", "valeur": float(valeur_perte_v), "created_by": responsable_v, "created_at": datetime.now().isoformat()}).execute()
                            st.success(f"✅ Dégât enregistré. Stock {voiture_data['marque']} {voiture_data['modele']}: {nouveau_stock_v}")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur enregistrement dégât")
                            st.code(repr(e))
            st.divider()
            st.subheader("📋 Historique Dégâts/Pertes Voitures")
            try:
                pertes_v = supabase.table('mouvements_stock').select("*").eq("type", "PERTE_VOITURE").order("created_at", desc=True).limit(20).execute().data
            except Exception as e:
                st.error("Erreur lecture pertes")
                pertes_v = []
            if not pertes_v:
                st.info("Aucun dégât de voiture enregistré")
            else:
                total_pertes_v = sum(p.get('valeur', 0) for p in pertes_v)
                st.metric("💸 TOTAL PERTES VOITURES", f"{total_pertes_v:,.2f} $")
                for p in pertes_v:
                    with st.expander(f"🔴 {p.get('article_nom','N/A')} - Qté: {abs(p.get('quantite',0))} - {p.get('created_at','')[:10]}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Qté endommagée:** {abs(p.get('quantite', 0))}")
                            st.write(f"**Valeur:** {p.get('valeur', 0):,.2f} $")
                        with col2:
                            st.write(f"**Motif:** {p.get('motif', 'N/A')}")
                            st.write(f"**Par:** {p.get('created_by', 'N/A')}")
                        with col3:
                            if st.session_state.user_role == "PDG":
                                if st.button("🗑️ Supprimer", key=f"del_perte_v_{p.get('id')}"):
                                    try:
                                        supabase.table('mouvements_stock').delete().eq("id", p.get('id')).execute()
                                        st.success("Supprimé")
                                        st.cache_data.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error("Erreur suppression")
                                        st.code(repr(e))

# === COMPTABILITÉ ===
if "💰 Comptabilité" in tab_map:
    with tab_map["💰 Comptabilité"]:
        st.markdown("## 💰 Comptabilité Générale ASYMAS")
        if 'compta_form_key' not in st.session_state:
            st.session_state.compta_form_key = 0
        with st.form(key=f"form_compta_{st.session_state.compta_form_key}", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                type_op = st.selectbox("Type", ["Revenu", "Dépense"])
                categorie = st.text_input("Catégorie", placeholder="Ex: Vente, Loyer, Achat...")
            with col2:
                description = st.text_input("Description")
                montant = st.number_input("Montant", min_value=0.0)
            with col3:
                devise = st.selectbox("Devise", ["FC", "$", "€"])
                date_op = st.date_input("Date", value=date.today())
            if st.form_submit_button("💾 Enregistrer Opération", type="primary", width="stretch"):
                if categorie and description and montant > 0:
                    try:
                        supabase.table("compta").insert({"date": str(date_op), "type": type_op, "categorie": categorie, "description": description, "montant": float(montant), "devise": devise, "utilisateur": st.session_state.user_name}).execute()
                        st.success("Opération enregistrée")
                        st.session_state.compta_form_key += 1
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur enregistrement")
                        st.code(repr(e))
                else:
                    st.error("Tous les champs obligatoires")
        st.divider()
        if not df_compta.empty:
            df_comp = df_compta.copy()
            total_rev_fc = df_comp[(df_comp['type'] == 'Revenu') & (df_comp['devise'] == 'FC')]['montant'].sum()
            total_dep_fc = df_comp[(df_comp['type'] == 'Dépense') & (df_comp['devise'] == 'FC')]['montant'].sum()
            total_rev_usd = df_comp[(df_comp['type'] == 'Revenu') & (df_comp['devise'] == '$')]['montant'].sum()
            total_dep_usd = df_comp[(df_comp['type'] == 'Dépense') & (df_comp['devise'] == '$')]['montant'].sum()
            total_rev_eur = df_comp[(df_comp['type'] == 'Revenu') & (df_comp['devise'] == '€')]['montant'].sum()
            total_dep_eur = df_comp[(df_comp['type'] == 'Dépense') & (df_comp['devise'] == '€')]['montant'].sum()
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("💵 Revenus FC", f"{total_rev_fc:,.0f}")
            col2.metric("💸 Dépenses FC", f"{total_dep_fc:,.0f}")
            col3.metric("💵 Revenus USD", f"{total_rev_usd:,.0f}")
            col4.metric("💸 Dépenses USD", f"{total_dep_usd:,.0f}")
            col5.metric("💶 Revenus EUR", f"{total_rev_eur:,.0f}")
            col6.metric("💸 Dépenses EUR", f"{total_dep_eur:,.0f}")
            st.metric("💰 Solde FC", f"{total_rev_fc - total_dep_fc:,.0f}")
            st.divider()
            df_comp['date'] = pd.to_datetime(df_comp['date'])
            df_comp = df_comp.sort_values('date', ascending=False)
            for _, row in df_comp.head(50).iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns([1.5,1,2,1,1,0.5])
                col1.write(row['date'].strftime('%d/%m/%Y'))
                col2.write(f"**{row['type']}**")
                col3.write(f"{row['categorie']} - {row['description']}")
                col4.write(f"**{row['montant']:,.0f} {row['devise']}**")
                col5.write(row['utilisateur'])
                if st.session_state.user_role == "PDG" or perms.get('supprimer', False):
                    if col6.button("🗑️", key=f"del_comp_{row['id']}"):
                        supabase.table("compta").delete().eq("id", int(row['id'])).execute()
                        st.cache_data.clear()
                        st.rerun()
            if st.button("📥 Télécharger Excel Comptabilité", width="stretch"):
                excel_data = generer_excel_pro(df_comp, "COMPTABILITE_ASYMAS", total_rev_fc, total_dep_fc, total_rev_fc - total_dep_fc)
                st.download_button("Télécharger", data=excel_data, file_name="comptabilite_asymas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("Aucune opération comptable")

# === FACTURES ===
if "📄 Factures" in tab_map:
    with tab_map["📄 Factures"]:
        st.markdown("## 📄 Factures - Relevé par Catégorie")
        if df_compta.empty:
            st.info("Aucune opération")
        else:
            df_compta_sorted = df_compta.sort_values('date', ascending=False)
            col_f1, col_f2, col_f3 = st.columns(3)
            date_debut = col_f1.date_input("📅 Date début", value=date.today() - timedelta(days=30), key="date_debut_fact")
            date_fin = col_f2.date_input("📅 Date fin", value=date.today(), key="date_fin_fact")
            col_f4, col_f5 = st.columns(2)
            if st.session_state.user_role!= "PDG":
                cats_user = st.session_state.get('user_cats', [])
                if cats_user and "Toutes" not in cats_user:
                    df_compta_sorted = df_compta_sorted[df_compta_sorted['categorie'].isin(cats_user)]
                else:
                    if not cats_user:
                        st.error("⛔ Aucune catégorie autorisée. Contacte le PDG.")
                        st.stop()
            categories_fact = ["Toutes"] + list(df_compta_sorted.get('categorie', pd.Series(dtype=str)).dropna().unique())
            filtre_cat_fact = col_f4.selectbox("📂 Filtrer par Catégorie", categories_fact, key="filtre_cat_fact")
            filtre_client_fact = col_f5.text_input("👤 Nom Client contient", placeholder="Tape un nom...", key="filtre_client_fact")
            df_filtre_fact = df_compta_sorted[(df_compta_sorted['date'] >= str(date_debut)) & (df_compta_sorted['date'] <= str(date_fin))]
            if filtre_cat_fact!= "Toutes":
                df_filtre_fact = df_filtre_fact[df_filtre_fact.get('categorie', '') == filtre_cat_fact]
            if filtre_client_fact:
                df_filtre_fact = df_filtre_fact[df_filtre_fact['description'].str.contains(filtre_client_fact, case=False, na=False)]
            col_t1, col_t2, col_t3 = st.columns(3)
            total_fc = df_filtre_fact[df_filtre_fact.get('devise','FC')=='FC']['montant'].sum()
            total_usd = df_filtre_fact[df_filtre_fact.get('devise','FC')=='$']['montant'].sum()
            total_eur = df_filtre_fact[df_filtre_fact.get('devise','FC')=='€']['montant'].sum()
            col_t1.metric("💵 Total FC", f"{total_fc:,.0f}")
            col_t2.metric("💵 Total USD", f"{total_usd:,.0f}")
            col_t3.metric("💵 Total EUR", f"{total_eur:,.0f}")
            st.divider()
            categories = df_filtre_fact.get('categorie', pd.Series(dtype=str)).dropna().unique()
            if len(categories) == 0:
                st.info("Aucune catégorie trouvée dans la période sélectionnée")
            else:
                for cat in sorted(categories):
                    df_cat = df_filtre_fact[df_filtre_fact.get('categorie', '') == cat]
                    total_cat_fc = df_cat[df_cat.get('devise','FC')=='FC']['montant'].sum()
                    total_cat_usd = df_cat[df_cat.get('devise','FC')=='$']['montant'].sum()
                    total_cat_eur = df_cat[df_cat.get('devise','FC')=='€']['montant'].sum()
                    with st.expander(f"📁 {cat} - {len(df_cat)} opérations | FC: {total_cat_fc:,.0f} | $: {total_cat_usd:,.0f} | €: {total_cat_eur:,.0f}", expanded=True):
                        for idx, row in df_cat.iterrows():
                            col_a, col_b, col_c, col_d, col_e, col_f, col_g = st.columns([1.2,0.8,2.5,1,0.8,0.5,0.5])
                            col_a.write(f"**{row.get('date','')}**")
                            col_b.write(f"{row.get('type','')}")
                            col_c.write(f"{row.get('description','')}")
                            col_d.write(f"**{row.get('montant',0):,.0f} {row.get('devise','FC')}**")
                            col_e.write(f"👤 {row.get('utilisateur','N/A')}")
                            if st.session_state.user_role == "PDG":
                                if col_g.button("🗑️", key=f"del_compta_{row['id']}", help="Supprimer"):
                                    supabase.table("compta").delete().eq("id", int(row['id'])).execute()
                                    st.success("Facture supprimée")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    col_g.write("")
                            try:
                                details_list = []
                                if row.get('details') and str(row.get('details'))!= 'nan':
                                    details_list = json.loads(row['details'])
                                else:
                                    details_list = [{"nom": row.get('description',''), "qte": 1, "pu": row.get('montant',0)}]
                                client_nom = row.get('description', '').split(' - ')[1] if ' - ' in row.get('description','') else 'Client'
                                pdf_bytes = generer_pdf_facture(
                                    row.get('numero_facture', f"FACT-{row['id']}"),
                                    row.get('categorie', 'Facture'),
                                    client_nom,
                                    details_list,
                                    row.get('montant',0),
                                    row.get('devise','FC'),
                                    "+243...",
                                    ""
                                )
                                col_f.download_button(
                                    "📥",
                                    data=pdf_bytes,
                                    file_name=f"{row.get('numero_facture', f'FACT-{row['id']}')}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_fact_{row['id']}",
                                    help="Télécharger PDF"
                                )
                                pdf_b64 = base64.b64encode(pdf_bytes).decode()
                                col_g.markdown(f"""
                                    <button onclick="printPDF_{row['id']}()" style="width:100%; padding:2px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; font-size:16px;">
                                        🖨️
                                    </button>
                                    <script>
                                    function printPDF_{row['id']}() {{
                                        const pdfData = 'data:application/pdf;base64,{pdf_b64}';
                                        const win = window.open('', '_blank');
                                        win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');
                                        win.document.close();
                                        setTimeout(() => {{ win.print(); }}, 1000);
                                    }}
                                    </script>
                                """, unsafe_allow_html=True)
                            except Exception as e:
                                col_f.write("❌")
                                col_g.write("❌")

# === DEVIS ===
if "📋 Devis" in tab_map:
    with tab_map["📋 Devis"]:
        st.markdown("## 📋 Devis Consulting - Industriel & Bâtiment")
        if 'devis_sections' not in st.session_state:
            st.session_state.devis_sections = []
        if 'devis_bat_sections' not in st.session_state:
            st.session_state.devis_bat_sections = []
        if 'devis_bat_titre' not in st.session_state:
            st.session_state.devis_bat_titre = "DEVIS DE MATERIAUX POUR LA CONSTRUCTION DE CLOTURE DE 23.5m"
        if 'devis_bat_main_oeuvre' not in st.session_state:
            st.session_state.devis_bat_main_oeuvre = 1173.0
        tab_industriel, tab_batiment = st.tabs(["🏭 Devis Industriel", "🏗️ Devis Bâtiment"])
        with tab_industriel:
            peut_creer_ind = st.session_state.user_role == "PDG" or perms.get('devis_industriel', False)
            if peut_creer_ind:
                st.session_state.devis_type = "Industriel"
                st.subheader("🏭 Nouveau Devis Industriel")
                col1, col2, col3 = st.columns(3)
                with col1:
                    client_devis = st.text_input("👤 Client", key="client_devis_ind")
                    tel_client_devis = st.text_input("📞 Téléphone", value="+243...", key="tel_devis_ind")
                with col2:
                    titre_devis = st.text_input("📋 Titre Projet", key="titre_devis_ind")
                    parcelle_devis = st.text_input("🗺️ Parcelle N°", key="parcelle_devis_ind")
                with col3:
                    localisation_devis = st.text_input("📍 Localisation", key="loc_devis_ind")
                    devise_devis = st.selectbox("💵 Devise", ["USD", "FC", "€"], key="devise_devis_ind")
                st.divider()
                st.markdown("### 📊 Tableau Complet Éditable")
                if not st.session_state.devis_sections:
                    st.session_state.devis_sections = [{
                        "numero": "A",
                        "titre": "ELECTRICITE",
                        "items": [
                            {"type": "cable", "designation": "Câble 2.5mm²", "marque": "Nexans", "section": "2.5mm²", "longueur": 100, "unite": "m", "qte": 1, "pu": 1.2},
                            {"type": "interrupteur", "designation": "Interrupteur", "marque": "Legrand", "couleur": "Blanc", "qualite": "Standard", "unite": "pc", "qte": 5, "pu": 3.5},
                            {"type": "autre", "designation": "Goulotte 25x16", "unite": "m", "qte": 10, "pu": 2.5, "spec": ""}
                        ]
                    }]
                total_general_ind = 0
                col_h1, col_h2, col_h3, col_h4, col_h5, col_h6, col_h7, col_h8 = st.columns([0.5, 3, 1.5, 1.5, 1, 1, 1, 0.5])
                col_h1.markdown("**N°**")
                col_h2.markdown("**Désignation**")
                col_h3.markdown("**Type/Marque**")
                col_h4.markdown("**Spécifications**")
                col_h5.markdown("**Qté**")
                col_h6.markdown("**PU**")
                col_h7.markdown("**Total**")
                col_h8.markdown("")
                st.divider()
                for idx, section in enumerate(st.session_state.devis_sections):
                    col_titre, col_del_sec = st.columns([5, 1])
                    with col_titre:
                        st.markdown(f"**{section['numero']}. {section['titre']}**")
                    with col_del_sec:
                        if st.button("🗑️ Supprimer Section", key=f"del_sec_ind_{idx}"):
                            st.session_state.devis_sections.pop(idx)
                            st.rerun()
                    sous_total_sec = 0
                    for i, item in enumerate(section['items']):
                        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.5, 3, 1.5, 1.5, 1, 1, 1, 0.5])
                        with col1:
                            new_num = st.text_input("N°", value=str(item.get('num', '')), key=f"num_ind_{idx}_{i}", label_visibility="collapsed")
                            section['items'][i]['num'] = new_num
                        with col2:
                            new_des = st.text_input("Désignation", value=item.get('designation', ''), key=f"des_ind_{idx}_{i}", label_visibility="collapsed")
                            section['items'][i]['designation'] = new_des
                        with col3:
                            type_item = st.selectbox("Type", ["cable", "interrupteur", "prise", "disjoncteur", "autre"], index=["cable", "interrupteur", "prise", "disjoncteur", "autre"].index(item.get('type', 'autre')), key=f"type_ind_{idx}_{i}", label_visibility="collapsed")
                            section['items'][i]['type'] = type_item
                        with col4:
                            if type_item == "cable":
                                marque = st.text_input("Marque", value=item.get('marque', ''), key=f"marque_ind_{idx}_{i}", label_visibility="collapsed", placeholder="Marque")
                                section_cable = st.text_input("Section", value=item.get('section', ''), key=f"sec_ind_{idx}_{i}", label_visibility="collapsed", placeholder="2.5mm²")
                                longueur = st.number_input("Long", value=float(item.get('longueur', 0)), key=f"long_ind_{idx}_{i}", label_visibility="collapsed", format="%.1f")
                                section['items'][i]['marque'] = marque
                                section['items'][i]['section'] = section_cable
                                section['items'][i]['longueur'] = longueur
                                section['items'][i]['spec'] = f"{marque} - {section_cable} - {longueur}m"
                            elif type_item == "interrupteur":
                                marque = st.text_input("Marque", value=item.get('marque', ''), key=f"marque_int_{idx}_{i}", label_visibility="collapsed", placeholder="Marque")
                                couleur = st.selectbox("Couleur", ["Blanc", "Noir", "Gris", "Beige"], index=["Blanc", "Noir", "Gris", "Beige"].index(item.get('couleur', 'Blanc')) if item.get('couleur') in ["Blanc", "Noir", "Gris", "Beige"] else 0, key=f"coul_int_{idx}_{i}", label_visibility="collapsed")
                                qualite = st.selectbox("Qualité", ["Standard", "Premium", "Pro"], index=["Standard", "Premium", "Pro"].index(item.get('qualite', 'Standard')) if item.get('qualite') in ["Standard", "Premium", "Pro"] else 0, key=f"qual_int_{idx}_{i}", label_visibility="collapsed")
                                section['items'][i]['marque'] = marque
                                section['items'][i]['couleur'] = couleur
                                section['items'][i]['qualite'] = qualite
                                section['items'][i]['spec'] = f"{marque} - {couleur} - {qualite}"
                            else:
                                spec = st.text_input("Détails", value=item.get('spec', ''), key=f"spec_ind_{idx}_{i}", label_visibility="collapsed", placeholder="Détails")
                                section['items'][i]['spec'] = spec
                        with col5:
                            unite = st.selectbox("Unité", ["m", "pc", "kg", "lot", "m²", "m³"], index=["m", "pc", "kg", "lot", "m²", "m³"].index(item.get('unite', 'pc')) if item.get('unite') in ["m", "pc", "kg", "lot", "m²", "m³"] else 1, key=f"unit_ind_{idx}_{i}", label_visibility="collapsed")
                            new_qte = st.number_input("Qté", value=float(item.get('qte', 0)), min_value=0.0, key=f"qte_ind_{idx}_{i}", label_visibility="collapsed", format="%.2f")
                            section['items'][i]['unite'] = unite
                            section['items'][i]['qte'] = new_qte
                        with col6:
                            new_pu = st.number_input("PU", value=float(item.get('pu', 0)), min_value=0.0, key=f"pu_ind_{idx}_{i}", label_visibility="collapsed", format="%.2f")
                            section['items'][i]['pu'] = new_pu
                        with col7:
                            pt = new_qte * new_pu
                            st.markdown(f"**{pt:,.2f}**")
                            sous_total_sec += pt
                        with col8:
                            if st.button("❌", key=f"del_item_ind_{idx}_{i}", help="Supprimer"):
                                section['items'].pop(i)
                                st.rerun()
                    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.5, 3, 1.5, 1.5, 1, 1, 1, 0.5])
                    with col1:
                        num_item = st.text_input("N°", key=f"num_ind_{idx}_new", label_visibility="collapsed", placeholder="N°")
                    with col2:
                        design = st.text_input("Désignation", key=f"des_ind_{idx}_new", label_visibility="collapsed", placeholder="Ajouter article...")
                    with col3:
                        type_new = st.selectbox("Type", ["cable", "interrupteur", "prise", "disjoncteur", "autre"], key=f"type_ind_{idx}_new", label_visibility="collapsed")
                    with col4:
                        if type_new == "cable":
                            marque_new = st.text_input("Marque", key=f"marque_ind_{idx}_new", label_visibility="collapsed", placeholder="Marque")
                            section_new = st.text_input("Section", key=f"sec_ind_{idx}_new", label_visibility="collapsed", placeholder="2.5mm²")
                            longueur_new = st.number_input("Long", min_value=0.0, key=f"long_ind_{idx}_new", label_visibility="collapsed", format="%.1f")
                        elif type_new == "interrupteur":
                            marque_new = st.text_input("Marque", key=f"marque_int_{idx}_new", label_visibility="collapsed", placeholder="Marque")
                            couleur_new = st.selectbox("Couleur", ["Blanc", "Noir", "Gris", "Beige"], key=f"coul_int_{idx}_new", label_visibility="collapsed")
                            qualite_new = st.selectbox("Qualité", ["Standard", "Premium", "Pro"], key=f"qual_int_{idx}_new", label_visibility="collapsed")
                        else:
                            spec_new = st.text_input("Détails", key=f"spec_ind_{idx}_new", label_visibility="collapsed", placeholder="Détails")
                    with col5:
                        unite = st.selectbox("Unité", ["m", "pc", "kg", "lot"], key=f"unit_ind_{idx}_new", label_visibility="collapsed")
                        qte = st.number_input("Qté", min_value=0.0, key=f"qte_ind_{idx}_new", label_visibility="collapsed", format="%.2f")
                    with col6:
                        pu = st.number_input("PU", min_value=0.0, key=f"pu_ind_{idx}_new", label_visibility="collapsed", format="%.2f")
                    with col7:
                        st.markdown(f"**{qte*pu:,.2f}**")
                    with col8:
                        if st.button("➕", key=f"add_item_ind_{idx}", help="Ajouter"):
                            if design:
                                new_item = {"num": num_item, "designation": design, "type": type_new, "unite": unite, "qte": qte, "pu": pu}
                                if type_new == "cable":
                                    new_item.update({"marque": marque_new, "section": section_new, "longueur": longueur_new})
                                elif type_new == "interrupteur":
                                    new_item.update({"marque": marque_new, "couleur": couleur_new, "qualite": qualite_new})
                                else:
                                    new_item.update({"spec": spec_new})
                                section['items'].append(new_item)
                                st.rerun()
                    col_st1, col_st2, col_st3 = st.columns([7.5, 1, 0.5])
                    col_st1.markdown(f"**Sous-total {section['titre']}**")
                    col_st2.markdown(f"**{sous_total_sec:,.2f}**")
                    total_general_ind += sous_total_sec
                    st.divider()
                col_add1, col_add2, col_add3 = st.columns([1,4,1])
                with col_add1:
                    new_section_num = st.text_input("N° Section", placeholder="B", key="new_sec_num_ind", label_visibility="collapsed")
                with col_add2:
                    new_section_titre = st.text_input("Titre Section", placeholder="Nouvelle section...", key="new_sec_titre_ind", label_visibility="collapsed")
                with col_add3:
                    if st.button("➕ Section", key="add_section_ind", width="stretch"):
                        if new_section_titre:
                            st.session_state.devis_sections.append({"numero": new_section_num, "titre": new_section_titre, "items": []})
                            st.rerun()
                st.divider()
                main_oeuvre = st.number_input("👷 Main d'oeuvre", min_value=0.0, key="mo_devis_ind")
                cout_total_ind = total_general_ind + main_oeuvre
                st.metric("COUT TOTAL DU PROJET", f"{cout_total_ind:,.2f} {devise_devis}")
                if st.button("📄 GÉNÉRER DEVIS PDF", type="primary", width="stretch", key="gen_devis_ind"):
                    if client_devis and titre_devis and st.session_state.devis_sections:
                        numero_devis = f"DEV-IND-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        try:
                            data_devis = {"numero": numero_devis, "type": "Industriel", "client": client_devis, "telephone": tel_client_devis, "titre": titre_devis, "parcelle": parcelle_devis, "localisation": localisation_devis, "sections": st.session_state.devis_sections, "main_oeuvre": main_oeuvre, "total": cout_total_ind, "devise": devise_devis, "created_by": st.session_state.user_name, "created_at": datetime.now().isoformat()}
                            supabase.table('devis').insert(data_devis).execute()
                            st.success(f"✅ Devis enregistré : {numero_devis}")
                            st.session_state.devis_sections = []
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur enregistrement")
                            st.code(repr(e))
                    else:
                        st.error("Client, Titre et au moins 1 section requis")
            else:
                st.info("🔒 Vous n'avez pas l'autorisation de créer des devis industriels")
            peut_telecharger_ind = st.session_state.user_role == "PDG" or perms.get('devis_industriel_download', False)
            peut_imprimer_ind = st.session_state.user_role == "PDG" or perms.get('devis_industriel_print', False)
            if peut_telecharger_ind or peut_imprimer_ind:
                st.divider()
                st.subheader("📚 Devis Industriel Enregistrés")
                try:
                    devis_ind_list = supabase.table('devis').select("*").eq("type", "Industriel").order("created_at", desc=True).limit(10).execute().data
                except:
                    devis_ind_list = []
                if not devis_ind_list:
                    st.info("Aucun devis industriel enregistré")
                else:
                    for d in devis_ind_list:
                        numero = d.get('numero', 'N/A')
                        client = d.get('client', 'N/A')
                        total = d.get('total', 0)
                        devise = d.get('devise', 'USD')
                        date_crea = d.get('created_at', '')[:10] if d.get('created_at') else 'N/A'
                        with st.expander(f"{numero} - {client} - {total:,.0f} {devise} - {date_crea}"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**Projet:** {d.get('titre','N/A')}")
                                st.write(f"**Parcelle:** {d.get('parcelle','N/A')}")
                                st.write(f"**Localisation:** {d.get('localisation','N/A')}")
                            with col2:
                                st.write(f"**Main d'oeuvre:** {d.get('main_oeuvre',0):,.0f} {devise}")
                                st.write(f"**TOTAL:** {total:,.0f} {devise}")
                                st.write(f"**Par:** {d.get('created_by','N/A')}")
                            with col3:
                                if peut_telecharger_ind:
                                    pdf_bytes = generer_pdf_devis_consulting(numero, "Industriel", client, d.get('titre',''), d.get('parcelle',''), d.get('localisation',''), d.get('sections',[]), devise, d.get('telephone',''), d.get('main_oeuvre',0))
                                    st.download_button(label="📥 Télécharger", data=pdf_bytes, file_name=f"{numero}.pdf", mime="application/pdf", key=f"dl_ind_hist_{numero}", width="stretch")
                                if peut_imprimer_ind:
                                    pdf_bytes = generer_pdf_devis_consulting(numero, "Industriel", client, d.get('titre',''), d.get('parcelle',''), d.get('localisation',''), d.get('sections',[]), devise, d.get('telephone',''), d.get('main_oeuvre',0))
                                    pdf_b64 = base64.b64encode(pdf_bytes).decode()
                                    safe_id = numero.replace('-', '_')
                                    st.components.v1.html(f"""<button onclick="printPDF_{safe_id}()" style="width:100%; padding:8px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:5px;">🖨️ Imprimer</button><script>function printPDF_{safe_id}() {{const pdfData = 'data:application/pdf;base64,{pdf_b64}';const win = window.open('', '_blank');win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');win.document.close();setTimeout(() => {{ win.print(); }}, 1000);}}</script>""", height=45)
                                if st.session_state.user_role == "PDG":
                                    if st.button("🗑️ Supprimer", key=f"del_ind_{numero}", width="stretch"):
                                        supabase.table('devis').delete().eq("numero", numero).execute()
                                        st.success("Supprimé")
                                        st.rerun()
        with tab_batiment:
            peut_creer_bat = st.session_state.user_role == "PDG" or perms.get('devis_batiment', False)
            if peut_creer_bat:
                st.session_state.devis_type = "Bâtiment"
                st.subheader("🏗️ Nouveau Devis Bâtiment - ASYMAS CONSULTING")
                if not st.session_state.devis_bat_sections:
                    st.session_state.devis_bat_sections = [
                        {"numero": "I", "titre": "Installation chantier / Demolitions", "items": [{"num": "", "designation": "Installationchantier", "unite": "ff", "qte": 1, "pu": 200}, {"num": "", "designation": "Demolitions", "unite": "ff", "qte": 1, "pu": 70}]},
                        {"numero": "II", "titre": "fondation", "items": [{"num": "1", "designation": "moellon", "unite": "Canters", "qte": 9, "pu": 50}, {"num": "2", "designation": "sable", "unite": "Canters", "qte": 4, "pu": 40}, {"num": "3", "designation": "ciment", "unite": "sac", "qte": 23, "pu": 13.5}, {"num": "4", "designation": "gravier", "unite": "Canters", "qte": 3, "pu": 80}, {"num": "5", "designation": "armature de 10", "unite": "pièce", "qte": 9, "pu": 9}, {"num": "", "designation": "armature de 8", "unite": "pièce", "qte": 4, "pu": 8}, {"num": "6", "designation": "armature de 6", "unite": "pièce", "qte": 12, "pu": 3.5}, {"num": "7", "designation": "Fil à ligature", "unite": "kg", "qte": 16, "pu": 2.5}]},
                        {"numero": "III", "titre": "Élévation de mur et corniche", "items": [{"num": "1", "designation": "bloc ciment", "unite": "pièce", "qte": 987, "pu": 1}, {"num": "2", "designation": "sable", "unite": "Canters", "qte": 5, "pu": 40}, {"num": "3", "designation": "ciment", "unite": "sac", "qte": 15, "pu": 13.5}, {"num": "4", "designation": "gravier", "unite": "Canters", "qte": 0.5, "pu": 70}, {"num": "5", "designation": "Barre Corniche de6", "unite": "pièce", "qte": 8, "pu": 3}, {"num": "6", "designation": "Fil à ligature", "unite": "kg", "qte": 6, "pu": 2}]},
                        {"numero": "IV", "titre": "Coffrage Colonne, Cornice et Socle", "items": [{"num": "1", "designation": "socle et longrine", "unite": "pièce", "qte": 8, "pu": 7}, {"num": "2", "designation": "Colonne", "unite": "pièce", "qte": 18, "pu": 7}, {"num": "3", "designation": "Corniche", "unite": "pièce", "qte": 6, "pu": 7}, {"num": "4", "designation": "clous de8", "unite": "kg", "qte": 15, "pu": 2}, {"num": "5", "designation": "clous de10", "unite": "kg", "qte": 10, "pu": 2}]},
                        {"numero": "V", "titre": "Finissage", "items": [{"num": "", "designation": "ciment", "unite": "sac", "qte": 20, "pu": 13.5}, {"num": "", "designation": "sable", "unite": "Canters", "qte": 7, "pu": 40}]}
                    ]
                col1, col2, col3 = st.columns(3)
                with col1:
                    client_devis_bat = st.text_input("👤 Client", key="client_devis_bat")
                    tel_client_devis_bat = st.text_input("📞 Téléphone", value="+243...", key="tel_devis_bat")
                with col2:
                    st.session_state.devis_bat_titre = st.text_input("📋 Titre du Devis", value=st.session_state.devis_bat_titre, key="titre_devis_bat")
                    parcelle_devis_bat = st.text_input("🗺️ Parcelle N°", key="parcelle_devis_bat")
                with col3:
                    localisation_devis_bat = st.text_input("📍 Localisation", key="loc_devis_bat")
                    devise_devis_bat = st.selectbox("💵 Devise", ["USD", "FC", "€"], key="devise_devis_bat")
                st.divider()
                st.markdown("### 📊 Tableau Complet Éditable")
                total_general = 0
                col_h1, col_h2, col_h3, col_h4, col_h5, col_h6, col_h7 = st.columns([0.5, 4, 1.5, 1.5, 1.5, 1.5, 0.5])
                col_h1.markdown("**no**")
                col_h2.markdown("**désignation**")
                col_h3.markdown("**unité**")
                col_h4.markdown("**quantité**")
                col_h5.markdown("**pu USD**")
                col_h6.markdown("**PT USD**")
                col_h7.markdown("")
                st.divider()
                for idx, section in enumerate(st.session_state.devis_bat_sections):
                    st.markdown(f"**{section['numero']}. {section['titre']}**")
                    sous_total_sec = 0
                    for i, item in enumerate(section['items']):
                        col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 4, 1.5, 1.5, 1.5, 1.5, 0.5])
                        with col1:
                            new_num = st.text_input("N°", value=str(item['num']), key=f"num_bat_{idx}_{i}", label_visibility="collapsed")
                            section['items'][i]['num'] = new_num
                        with col2:
                            new_des = st.text_input("Désignation", value=item['designation'], key=f"des_bat_{idx}_{i}", label_visibility="collapsed")
                            section['items'][i]['designation'] = new_des
                        with col3:
                            options_unit = ["Canters", "sac", "pièce", "kg", "ff", "m3", "m2", "ml", "t", "barre"]
                            new_unit = st.selectbox("Unité", options_unit, index=options_unit.index(item['unite']) if item['unite'] in options_unit else 0, key=f"unit_bat_{idx}_{i}", label_visibility="collapsed")
                            section['items'][i]['unite'] = new_unit
                        with col4:
                            new_qte = st.number_input("Qté", value=float(item['qte']), min_value=0.0, key=f"qte_bat_{idx}_{i}", label_visibility="collapsed", format="%.2f")
                            section['items'][i]['qte'] = new_qte
                        with col5:
                            new_pu = st.number_input("PU", value=float(item['pu']), min_value=0.0, key=f"pu_bat_{idx}_{i}", label_visibility="collapsed", format="%.2f")
                            section['items'][i]['pu'] = new_pu
                        with col6:
                            pt = new_qte * new_pu
                            st.markdown(f"**{pt:,.2f}**")
                            sous_total_sec += pt
                        with col7:
                            if st.button("❌", key=f"del_item_bat_{idx}_{i}", help="Supprimer"):
                                section['items'].pop(i)
                                st.rerun()
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 4, 1.5, 1.5, 1.5, 1.5, 0.5])
                    with col1:
                        num_item = st.text_input("N°", key=f"num_bat_{idx}_new", label_visibility="collapsed", placeholder="N°")
                    with col2:
                        design = st.text_input("Désignation", key=f"des_bat_{idx}_new", label_visibility="collapsed", placeholder="Ajouter article...")
                    with col3:
                        unite = st.selectbox("Unité", ["Canters", "sac", "pièce", "kg", "ff", "m3", "m2", "ml", "t", "barre"], key=f"unit_bat_{idx}_new", label_visibility="collapsed")
                    with col4:
                        qte = st.number_input("Qté", min_value=0.0, key=f"qte_bat_{idx}_new", label_visibility="collapsed", format="%.2f")
                    with col5:
                        pu = st.number_input("PU", min_value=0.0, key=f"pu_bat_{idx}_new", label_visibility="collapsed", format="%.2f")
                    with col6:
                        st.markdown(f"**{qte*pu:,.2f}**")
                    with col7:
                        if st.button("➕", key=f"add_item_bat_{idx}", help="Ajouter"):
                            if design:
                                section['items'].append({"num": num_item, "designation": design, "unite": unite, "qte": qte, "pu": pu})
                                st.rerun()
                    col_st1, col_st2, col_st3 = st.columns([6.5, 1.5, 0.5])
                    col_st1.markdown(f"**sous-total**")
                    col_st2.markdown(f"**{sous_total_sec:,.2f}**")
                    total_general += sous_total_sec
                    st.divider()
                col_add1, col_add2, col_add3 = st.columns([1,4,1])
                with col_add1:
                    new_section_num_bat = st.text_input("N° Section", placeholder="VI", key="new_sec_num_bat", label_visibility="collapsed")
                with col_add2:
                    new_section_titre_bat = st.text_input("Titre Section", placeholder="Nouvelle section...", key="new_sec_titre_bat", label_visibility="collapsed")
                with col_add3:
                    if st.button("➕ Section", key="add_section_bat", width="stretch"):
                        if new_section_titre_bat:
                            st.session_state.devis_bat_sections.append({"numero": new_section_num_bat, "titre": new_section_titre_bat, "items": []})
                            st.rerun()
                st.divider()
                col_mo1, col_mo2, col_mo3 = st.columns(3)
                with col_mo1:
                    st.metric("TOTAL MATERIAUX", f"{total_general:,.2f} {devise_devis_bat}")
                with col_mo2:
                    st.session_state.devis_bat_main_oeuvre = st.number_input("Main d'oeuvre", value=st.session_state.devis_bat_main_oeuvre, min_value=0.0, key="mo_devis_bat", format="%.2f")
                with col_mo3:
                    cout_total = total_general + st.session_state.devis_bat_main_oeuvre
                    st.metric("COUT TOTAL DU PROJET", f"{cout_total:,.2f} {devise_devis_bat}")
                st.markdown("**Architecte VINCENT KALAVI**")
                st.divider()
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if st.button("📄 GÉNÉRER DEVIS PDF", type="primary", width="stretch", key="gen_devis_bat"):
                        if client_devis_bat and st.session_state.devis_bat_titre:
                            numero_devis = f"DEV-BAT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            try:
                                data_devis = {"numero": numero_devis, "type": "Bâtiment", "client": client_devis_bat, "telephone": tel_client_devis_bat, "titre": st.session_state.devis_bat_titre, "parcelle": parcelle_devis_bat, "localisation": localisation_devis_bat, "sections": st.session_state.devis_bat_sections, "main_oeuvre": st.session_state.devis_bat_main_oeuvre, "total": cout_total, "devise": devise_devis_bat, "created_by": st.session_state.user_name, "created_at": datetime.now().isoformat()}
                                supabase.table('devis').insert(data_devis).execute()
                                st.success(f"✅ Devis enregistré : {numero_devis}")
                                st.cache_data.clear()
                            except Exception as e:
                                st.error("Erreur enregistrement")
                                st.code(repr(e))
                                                 st.stop()
                        pdf_bytes = generer_pdf_devis_consulting(numero_devis, "Bâtiment", client_devis_bat, st.session_state.devis_bat_titre, parcelle_devis_bat, localisation_devis_bat, st.session_state.devis_bat_sections, devise_devis_bat, tel_client_devis_bat, st.session_state.devis_bat_main_oeuvre)
                        st.session_state.pdf_devis_bat = pdf_bytes
                        st.session_state.num_devis_bat = numero_devis
                        st.rerun()
                    else:
                        st.error("Client et Titre requis")
            with col_btn2:
                if 'pdf_devis_bat' in st.session_state and st.session_state.pdf_devis_bat:
                    st.download_button(label="📥 Télécharger PDF", data=st.session_state.pdf_devis_bat, file_name=f"{st.session_state.num_devis_bat}.pdf", mime="application/pdf", width="stretch", key="dl_devis_bat")
            with col_btn3:
                if st.button("🔄 Réinitialiser", key="reset_devis_bat", width="stretch"):
                    st.session_state.devis_bat_sections = []
                    if 'pdf_devis_bat' in st.session_state:
                        del st.session_state.pdf_devis_bat
                    st.rerun()
            if 'pdf_devis_bat' in st.session_state and st.session_state.pdf_devis_bat:
                pdf_b64 = base64.b64encode(st.session_state.pdf_devis_bat).decode()
                st.components.v1.html(f"""<button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">🖨️ IMPRIMER LE DEVIS</button><script>function printPDF() {{const pdfData = 'data:application/pdf;base64,{pdf_b64}';const win = window.open('', '_blank');win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');win.document.close();setTimeout(() => {{ win.print(); }}, 1000);}}</script>""", height=60)
        else:
            st.info("🔒 Vous n'avez pas l'autorisation de créer des devis bâtiment")
        peut_telecharger_bat = st.session_state.user_role == "PDG" or perms.get('devis_batiment_download', False)
        peut_imprimer_bat = st.session_state.user_role == "PDG" or perms.get('devis_batiment_print', False)
        if peut_telecharger_bat or peut_imprimer_bat:
            st.divider()
            st.subheader("📚 Devis Bâtiment Enregistrés")
            try:
                devis_bat_list = supabase.table('devis').select("*").eq("type", "Bâtiment").order("created_at", desc=True).limit(5).execute().data
            except:
                devis_bat_list = []
            if not devis_bat_list:
                st.info("Aucun devis bâtiment enregistré")
            else:
                for d in devis_bat_list:
                    numero = d.get('numero', 'N/A')
                    client = d.get('client', 'N/A')
                    total = d.get('total', 0)
                    devise = d.get('devise', 'USD')
                    col1, col2, col3, col4 = st.columns([3,2,1,1])
                    with col1:
                        st.write(f"**{numero}** - {client}")
                    with col2:
                        st.write(f"{total:,.0f} {devise}")
                    with col3:
                        if peut_telecharger_bat:
                            pdf_bytes = generer_pdf_devis_consulting(numero, "Bâtiment", client, d.get('titre',''), d.get('parcelle',''), d.get('localisation',''), d.get('sections',[]), devise, d.get('telephone',''), d.get('main_oeuvre',0))
                            st.download_button(label="📥", data=pdf_bytes, file_name=f"{numero}.pdf", mime="application/pdf", key=f"dl_bat_bas_{numero}")
                        else:
                            st.write("🔒")
                    with col4:
                        if peut_imprimer_bat:
                            pdf_bytes = generer_pdf_devis_consulting(numero, "Bâtiment", client, d.get('titre',''), d.get('parcelle',''), d.get('localisation',''), d.get('sections',[]), devise, d.get('telephone',''), d.get('main_oeuvre',0))
                            pdf_b64 = base64.b64encode(pdf_bytes).decode()
                            safe_id = numero.replace('-', '_')
                            st.components.v1.html(f"""<button onclick="printPDF_{safe_id}()" style="width:100%; padding:6px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer;">🖨️</button><script>function printPDF_{safe_id}() {{const pdfData = 'data:application/pdf;base64,{pdf_b64}';const win = window.open('', '_blank');win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');win.document.close();setTimeout(() => {{ win.print(); }}, 1000);}}</script>""", height=40)
                        else:
                            st.write("🔒")

# === UTILISATEURS ===
if "👥 Utilisateurs" in tab_map:
    with tab_map["👥 Utilisateurs"]:
        st.markdown("## 👥 Gestion Utilisateurs - Droits d'Accès")
        with st.expander("➕ Ajouter Nouvel Utilisateur", expanded=True):
            with st.form("form_user", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nom_user = c1.text_input("Nom *", placeholder="Ex: Jean KABAMBA")
                role_user = c2.selectbox("Rôle *", ["PDG", "GERANTE", "UTILISATEUR", "CAISSIER", "COMMERCIAL"])
                pwd_user = c3.text_input("Mot de passe *", type="password")
                st.markdown("**🔐 Autorisations d'onglets :**")
                col1, col2, col3, col4 = st.columns(4)
                perm_dashboard = col1.checkbox("Dashboard", value=True)
                perm_commerce = col2.checkbox("Commerce", value=True)
                perm_stock = col3.checkbox("Gestion Stock")
                perm_immobilier = col4.checkbox("Immobilier")
                perm_automobile = col1.checkbox("Automobile")
                perm_parc = col2.checkbox("Gestion Parc")
                perm_comptabilite = col3.checkbox("Comptabilité")
                perm_factures = col4.checkbox("Factures")
                perm_supprimer = col1.checkbox("🗑️ Peut Supprimer")
                perm_users = col2.checkbox("👥 Gérer Utilisateurs")
                st.markdown("**📋 Autorisations Devis :**")
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    st.markdown("*Devis Industriel*")
                    perm_devis_ind = st.checkbox("Créer", key="perm_ind_creer")
                    perm_devis_ind_dl = st.checkbox("Télécharger", key="perm_ind_dl")
                    perm_devis_ind_pr = st.checkbox("Imprimer", key="perm_ind_pr")
                with col_d2:
                    st.markdown("*Devis Bâtiment*")
                    perm_devis_bat = st.checkbox("Créer", key="perm_bat_creer")
                    perm_devis_bat_dl = st.checkbox("Télécharger", key="perm_bat_dl")
                    perm_devis_bat_pr = st.checkbox("Imprimer", key="perm_bat_pr")
                with col_d3:
                    st.markdown("*Historique*")
                    perm_devis_hist = st.checkbox("Voir Historique", key="perm_hist")
                st.markdown("**📂 Catégories de Factures Visibles :**")
                cats_dispo = sorted(df_compta['categorie'].dropna().unique().tolist()) if 'categorie' in df_compta.columns else []
                cats_autorisees = st.multiselect("Sélectionne les catégories que cet utilisateur peut voir dans Factures", ["Toutes"] + cats_dispo, default=["Toutes"], key="cats_factures")
                if st.form_submit_button("💾 Ajouter Utilisateur", type="primary"):
                    if nom_user and pwd_user:
                        try:
                            perms_dict = {"dashboard": perm_dashboard, "commerce": perm_commerce, "stock": perm_stock, "immobilier": perm_immobilier, "automobile": perm_automobile, "parc": perm_parc, "comptabilite": perm_comptabilite, "factures": perm_factures, "supprimer": perm_supprimer, "users": perm_users, "devis_industriel": perm_devis_ind, "devis_industriel_download": perm_devis_ind_dl, "devis_industriel_print": perm_devis_ind_pr, "devis_batiment": perm_devis_bat, "devis_batiment_download": perm_devis_bat_dl, "devis_batiment_print": perm_devis_bat_pr, "devis_historique": perm_devis_hist}
                            supabase.table("utilisateurs").insert({"nom": nom_user, "role": role_user, "password": pwd_user, "permissions": perms_dict, "categories_autorisees": cats_autorisees if "Toutes" not in cats_autorisees else []}).execute()
                            st.success(f"Utilisateur {nom_user} ajouté")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur ajout")
                            st.code(repr(e))
                    else:
                        st.error("Nom et mot de passe obligatoires")
        st.divider()
        st.subheader("📋 Liste des Utilisateurs")
        if df_utilisateurs.empty:
            st.info("Aucun utilisateur")
        else:
            for _, user in df_utilisateurs.iterrows():
                current_perms = user.get('permissions', {})
                if isinstance(current_perms, str):
                    try:
                        current_perms = json.loads(current_perms)
                    except:
                        current_perms = {}
                with st.expander(f"{user['nom']} - {user['role']}"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.write("**Onglets :**")
                        if current_perms.get('dashboard'): st.write("✅ Dashboard")
                        if current_perms.get('commerce'): st.write("✅ Commerce")
                        if current_perms.get('stock'): st.write("✅ Stock")
                        if current_perms.get('immobilier'): st.write("✅ Immobilier")
                        if current_perms.get('automobile'): st.write("✅ Automobile")
                        if current_perms.get('parc'): st.write("✅ Parc")
                        if current_perms.get('comptabilite'): st.write("✅ Comptabilité")
                        if current_perms.get('factures'): st.write("✅ Factures")
                        if current_perms.get('users'): st.write("✅ Utilisateurs")
                        if current_perms.get('supprimer'): st.write("✅ Supprimer")
                    with c2:
                        st.write("**Devis Industriel :**")
                        if current_perms.get('devis_industriel'): st.write("✅ Créer")
                        if current_perms.get('devis_industriel_download'): st.write("✅ Télécharger")
                        if current_perms.get('devis_industriel_print'): st.write("✅ Imprimer")
                    with c3:
                        st.write("**Devis Bâtiment :**")
                        if current_perms.get('devis_batiment'): st.write("✅ Créer")
                        if current_perms.get('devis_batiment_download'): st.write("✅ Télécharger")
                        if current_perms.get('devis_batiment_print'): st.write("✅ Imprimer")
                        if current_perms.get('devis_historique'): st.write("✅ Historique")
                    st.divider()
                    if st.session_state.user_role == "PDG":
                        st.markdown("**✏️ Modifier les autorisations :**")
                        with st.form(f"edit_user_{user['id']}"):
                            col1, col2, col3, col4 = st.columns(4)
                            perm_dashboard = col1.checkbox("Dashboard", value=current_perms.get('dashboard', False), key=f"edit_dash_{user['id']}")
                            perm_commerce = col2.checkbox("Commerce", value=current_perms.get('commerce', False), key=f"edit_com_{user['id']}")
                            perm_stock = col3.checkbox("Gestion Stock", value=current_perms.get('stock', False), key=f"edit_stock_{user['id']}")
                            perm_immobilier = col4.checkbox("Immobilier", value=current_perms.get('immobilier', False), key=f"edit_immo_{user['id']}")
                            perm_automobile = col1.checkbox("Automobile", value=current_perms.get('automobile', False), key=f"edit_auto_{user['id']}")
                            perm_parc = col2.checkbox("Gestion Parc", value=current_perms.get('parc', False), key=f"edit_parc_{user['id']}")
                            perm_comptabilite = col3.checkbox("Comptabilité", value=current_perms.get('comptabilite', False), key=f"edit_comp_{user['id']}")
                            perm_factures = col4.checkbox("Factures", value=current_perms.get('factures', False), key=f"edit_fact_{user['id']}")
                            perm_supprimer = col1.checkbox("🗑️ Peut Supprimer", value=current_perms.get('supprimer', False), key=f"edit_sup_{user['id']}")
                            perm_users = col2.checkbox("👥 Gérer Utilisateurs", value=current_perms.get('users', False), key=f"edit_users_{user['id']}")
                            st.markdown("**📋 Devis Industriel :**")
                            col_i1, col_i2, col_i3 = st.columns(3)
                            perm_devis_ind = col_i1.checkbox("Créer", value=current_perms.get('devis_industriel', False), key=f"edit_ind_{user['id']}")
                            perm_devis_ind_dl = col_i2.checkbox("Télécharger", value=current_perms.get('devis_industriel_download', False), key=f"edit_ind_dl_{user['id']}")
                            perm_devis_ind_pr = col_i3.checkbox("Imprimer", value=current_perms.get('devis_industriel_print', False), key=f"edit_ind_pr_{user['id']}")
                            st.markdown("**📋 Devis Bâtiment :**")
                            col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                            perm_devis_bat = col_b1.checkbox("Créer", value=current_perms.get('devis_batiment', False), key=f"edit_bat_{user['id']}")
                            perm_devis_bat_dl = col_b2.checkbox("Télécharger", value=current_perms.get('devis_batiment_download', False), key=f"edit_bat_dl_{user['id']}")
                            perm_devis_bat_pr = col_b3.checkbox("Imprimer", value=current_perms.get('devis_batiment_print', False), key=f"edit_bat_pr_{user['id']}")
                            perm_devis_hist = col_b4.checkbox("Historique", value=current_perms.get('devis_historique', False), key=f"edit_hist_{user['id']}")
                            col_btn1, col_btn2 = st.columns(2)
                            if col_btn1.form_submit_button("💾 Enregistrer Modifications", type="primary", width="stretch"):
                                new_perms = {"dashboard": perm_dashboard, "commerce": perm_commerce, "stock": perm_stock, "immobilier": perm_immobilier, "automobile": perm_automobile, "parc": perm_parc, "comptabilite": perm_comptabilite, "factures": perm_factures, "supprimer": perm_supprimer, "users": perm_users, "devis_industriel": perm_devis_ind, "devis_industriel_download": perm_devis_ind_dl, "devis_industriel_print": perm_devis_ind_pr, "devis_batiment": perm_devis_bat, "devis_batiment_download": perm_devis_bat_dl, "devis_batiment_print": perm_devis_bat_pr, "devis_historique": perm_devis_hist}
                                try:
                                    supabase.table("utilisateurs").update({"permissions": new_perms}).eq("id", int(user['id'])).execute()
                                    st.success(f"Permissions de {user['nom']} mises à jour")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erreur modification")
                                    st.code(repr(e))
                        if user['nom']!= st.session_state.user_name:
                            if st.button("🗑️ Supprimer cet utilisateur", key=f"del_user_{user['id']}", type="secondary", width="stretch"):
                                try:
                                    supabase.table("utilisateurs").delete().eq("id", int(user['id'])).execute()
                                    st.success(f"Utilisateur {user['nom']} supprimé")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erreur suppression")
                                    st.code(repr(e))
                        else:
                            st.info("🔒 Vous ne pouvez pas supprimer votre propre compte")
                    else:
                        st.info("🔒 Seul le PDG peut modifier les autorisations")

# === FLOKI SOLDAT COMPLET ===
import difflib
import re
import urllib.parse
import json
import requests

class FLOKI:
    def __init__(self, supabase_client, dataframes):
        self.supabase = supabase_client
        self.df = dataframes
        self.system_knowledge = self._get_supabase_schema()
    def _get_supabase_schema(self):
        schema = {}
        tables = ["articles", "compta", "biens", "voitures", "mouvements_stock", "devis", "notifications", "floki_logs"]
        for t in tables:
            try:
                result = self.supabase.table(t).select("*").limit(1).execute()
                schema[t] = list(result.data[0].keys()) if result.data else []
            except:
                schema[t] = []
        return schema
    def ask(self, question):
        q = question.lower().strip()
        log_entry = {"demande": question, "date": datetime.now().isoformat(), "source": "ASYMAS"}
        if any(g in q for g in ["slt", "salut", "bonjour", "hello", "yo"]):
            return "Présent chef. FLOKI opérationnel. Donnez l'ordre."
        if "envoie" in q and "message" in q and "numero" in q:
            result = self._action_send_whatsapp(question)
            log_entry.update({"action": "whatsapp_send", "reponse": result})
            self._log_action(log_entry)
            return result
        if any(k in q for k in ["redige", "rédige", "lettre", "relance", "convocation"]):
            result = self._action_rediger(question)
            log_entry.update({"action": "redaction", "reponse": result})
            self._log_action(log_entry)
            return result
        if any(k in q for k in ["conseil", "avis", "opportunite", "risque", "que faire"]):
            result = self._action_conseil(q)
            log_entry.update({"action": "conseil", "reponse": result})
            self._log_action(log_entry)
            return result
        q_clean = re.sub(r'(trouve moi|donne moi|donne|trouve|cherche|le prix de|prix du|du|de|le|la|un|une|pour moi|combien)', '', q).strip()
        rep = self._search_asymas(q_clean)
        if rep:
            log_entry.update({"source": "ASYMAS", "reponse": rep})
            self._log_action(log_entry)
            return rep + "\n\nSource: ASYMAS"
        web_rep = self._search_web(question)
        log_entry.update({"source": "WEB", "reponse": web_rep})
        self._log_action(log_entry)
        return web_rep + "\n\nSource: WEB"
    def _search_asymas(self, q):
        if "voiture" in q and ("moins cher" in q or "prix" in q):
            return self._get_voiture_moins_cher()
        if "voiture" in q and ("liste" in q or "donne" in q):
            return self._get_voitures_stock()
        rep = self._search_product(q)
        if rep: return rep
        if "perte" in q and "commerce" in q:
            return self._get_pertes_commerce()
        if any(k in q for k in ["stock bas", "rupture", "manque"]):
            return self._stock_bas()
        if any(k in q for k in ["ca", "chiffre", "revenu", "vente", "argent", "benefice", "solde"]):
            return self._chiffre_affaires()
        return None
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
    def _get_pertes_commerce(self):
        try:
            result = self.supabase.table("mouvements_stock").select("*").eq("type", "perte").eq("categorie", "commerce").order("date", desc=True).limit(10).execute()
            if not result.data:
                return "Aucune perte commerce enregistrée chef."
            txt = "\n".join([f"- {r.get('article', 'N/A')}: {r.get('montant', 0):,.0f} FC le {r.get('date', '')[:10]}" for r in result.data])
            return f"Dernières pertes commerce:\n{txt}"
        except Exception as e:
            return f"Erreur lecture pertes: {e}. Vérifiez RLS sur mouvements_stock."
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
        noms = articles['nom_clean'].tolist()
        closest = difflib.get_close_matches(q_clean, noms, n=1, cutoff=0.45)
        if closest:
            r = articles[articles['nom_clean'] == closest[0]].iloc[0]
            return f"{r['nom_article']}: Stock {int(r['stock'])} unités, Prix {float(r['prix_vente']):,.0f} FC"
        return None
    def _stock_bas(self):
        if self.df['articles'].empty:
            return "Pas d'articles chef."
        low = self.df['articles'][self.df['articles']['stock'] < 5]
        if low.empty:
            return "Stock OK chef. Rien en dessous de 5 unités."
        txt = "\n".join([f"- {r['nom_article']}: {r['stock']} unités" for _, r in low.iterrows()])
        return f"Attention chef, stock bas:\n{txt}"
    def _chiffre_affaires(self):
        if self.df['compta'].empty:
            return "Pas de données compta chef."
        rev = self.df['compta'][self.df['compta']['type'] == 'Revenu']['montant'].sum()
        dep = self.df['compta'][self.df['compta']['type'] == 'Dépense']['montant'].sum()
        return f"Rapport compta:\nRevenus: {rev:,.0f} FC\nDépenses: {dep:,.0f} FC\nSolde: {rev-dep:,.0f} FC"
    def _search_web(self, q):
        try:
            url = f"https://api.duckgo.com/?q={urllib.parse.quote(q)}&format=json&no_html=1"
            r = requests.get(url, timeout=4)
            data = r.json()
            if data.get('AbstractText'):
                return f"Info vérifiée: {data['AbstractText']}"
            return f"Négatif chef. Rien de vérifiable sur le web pour '{q}'."
        except:
            return "Le web ne répond pas chef."
    def _action_rediger(self, question):
        if "relance" in question.lower():
            return "Objet: Relance de paiement\nMonsieur/Madame,\n\nNous constatons que la facture reste impayée.\nMerci de régulariser sous 48h.\n\nASYMAS BUSINESS"
        if "convocation" in question.lower():
            return "Objet: Convocation\nVous êtes convoqué(e) le [DATE] à [HEURE] pour [OBJET].\n\nASYMAS BUSINESS"
        return "Chef, précise: 'redige une relance' ou 'redige une convocation'."
    def _action_send_whatsapp(self, question):
        nums = re.findall(r'\+?\d{9,15}', question)
        if not nums:
            return "Chef, donne-moi un numéro. Ex: 'envoie un message au +243995105623 salut'"
        numero = nums[0].replace("+", "")
        message = re.sub(r'envoie un message.*?\+?\d{9,15}', '', question).strip() or "Message de ASYMAS BUSINESS"
        url = f"https://wa.me/{numero}?text={urllib.parse.quote(message)}"
        return f"Lien WhatsApp prêt: {url}"
    def notify_internal(self, message):
        try:
            self.supabase.table("notifications").insert({"message": f"[{st.session_state.get('user_name', 'PDG')}]: {message}", "created_at": datetime.now().isoformat()}).execute()
            return "Notification envoyée à l’équipe chef."
        except Exception as e:
            return f"Échec notification: {e}"
    def _action_conseil(self, q):
        if not self.df['articles'].empty and not self.df['compta'].empty:
            stock_bas = len(self.df['articles'][self.df['articles']['stock'] < 5])
            rev = self.df['compta'][self.df['compta']['type'] == 'Revenu']['montant'].sum()
            return f"FAIT: {stock_bas} articles en stock bas. CA: {rev:,.0f} FC.\nCONSEIL: Réapprovisionne sous 48h.\nRISQUE: Rupture = perte de vente."
        return "Chef, je croise vos données ASYMAS pour donner fait, conseil, risque."
    def _log_action(self, log_entry):
        try:
            self.supabase.table("floki_logs").insert(log_entry).execute()
        except:
            pass

# === UI FLOKI ===
if 'floki' not in st.session_state:
    dataframes = {"articles": df_articles, "compta": df_compta, "biens": df_biens, "voitures": df_voitures}
    st.session_state.floki = FLOKI(supabase, dataframes)

with st.sidebar:
    st.divider()
    st.markdown("### 🤖 FLOKI")
    st.caption("Conseiller du PDG - Comprend le système ASYMAS")
    q = st.text_input("Ordre pour FLOKI", key="floki_input", placeholder="Ex: liste de mes voitures, voiture moins cher, CA du mois")
    st.info("🎤 Micro désactivé temporairement. Utilisez Chrome + localhost pour l'activer plus tard.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Exécuter", type="primary", use_container_width=True):
            if q:
                with st.spinner("FLOKI réfléchit..."):
                    rep = st.session_state.floki.ask(q)
                    st.session_state.floki_rep = rep
    with col2:
        if st.button("Notifier équipe", use_container_width=True):
            if q:
                msg = st.session_state.floki.notify_internal(q)
                st.toast(msg)
    if 'floki_rep' in st.session_state:
        rep_clean = st.session_state.floki_rep.replace('"', '\\"').replace("\n", " ").replace("'", "\\'")
        st.components.v1.html(f"""<script>if ('speechSynthesis' in window) {{window.speechSynthesis.cancel();var msg = new SpeechSynthesisUtterance("{rep_clean}");msg.lang = 'fr-FR';msg.rate = 1;window.speechSynthesis.speak(msg);}}</script>""", height=0)
        st.success(st.session_state.floki_rep)
