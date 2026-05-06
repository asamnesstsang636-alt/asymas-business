import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import json
import base64
from fpdf import FPDF
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🏢", layout="wide")

# === SUPABASE ===
@st.cache_resource
def init_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase: Client = init_supabase()

# === LOAD DATA ===
@st.cache_data(ttl=30)
def load_table(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_table_columns(table_name):
    try:
        response = supabase.table(table_name).select("*").limit(1).execute()
        return list(response.data[0].keys()) if response.data else []
    except:
        return []

df_articles = load_table("articles")
df_voitures = load_table("voitures")
df_compta = load_table("compta")
df_devis = load_table("devis")
df_utilisateurs = load_table("utilisateurs")
df_proforma = load_table("factures_proforma")

# === SESSION STATE ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'user_role' not in st.session_state:
    st.session_state.user_role = ""
if 'user_permissions' not in st.session_state:
    st.session_state.user_permissions = {}
if 'panier_commerce' not in st.session_state:
    st.session_state.panier_commerce = []
if 'panier_voiture' not in st.session_state:
    st.session_state.panier_voiture = []

# === LOGIN ===
if not st.session_state.logged_in:
    st.markdown("# 🏢 ASYMAS BUSINESS")
    st.markdown("### Connexion")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            nom = st.text_input("Nom d'utilisateur")
            pwd = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("🔓 Se connecter", width="stretch"):
                user = df_utilisateurs[df_utilisateurs['nom'] == nom]
                if not user.empty and user.iloc[0]['password'] == pwd:
                    st.session_state.logged_in = True
                    st.session_state.user_name = nom
                    st.session_state.user_role = user.iloc[0]['role']
                    st.session_state.user_permissions = json.loads(user.iloc[0]['permissions']) if isinstance(user.iloc[0]['permissions'], str) else user.iloc[0]['permissions']
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
    st.stop()

# === PERMISSIONS ===
perms = st.session_state.user_permissions

# === QR SCANNER ===
def qrcode_scanner(key):
    try:
        from streamlit_qrcode_scanner import qrcode_scanner
        return qrcode_scanner(key=key)
    except:
        return st.text_input("Scanner QR Code", key=key, placeholder="Tape le code QR")

# === PDF GENERATOR ===
def generer_pdf_facture(numero, type_fact, client, details_list, total, devise, tel_client="+243..."):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "ASYMAS BUSINESS", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, "Commerce - Immobilier - Automobile", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"FACTURE {type_fact.upper()}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 6, f"Numero: {numero}", ln=False)
    pdf.cell(95, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(95, 6, f"Client: {client}", ln=False)
    pdf.cell(95, 6, f"Tel: {tel_client}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(100, 8, "Designation", 1)
    pdf.cell(20, 8, "Qte", 1)
    pdf.cell(35, 8, "PU", 1)
    pdf.cell(35, 8, "Total", 1, ln=True)
    pdf.set_font("Arial", "", 9)
    for item in details_list:
        pdf.cell(100, 7, str(item['nom'])[:50], 1)
        pdf.cell(20, 7, str(item['qte']), 1, align="C")
        pdf.cell(35, 7, f"{item['pu']:,.0f}", 1, align="R")
        pdf.cell(35, 7, f"{item['qte'] * item['pu']:,.0f}", 1, align="R", ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(155, 10, "TOTAL", 1)
    pdf.cell(35, 10, f"{total:,.0f} {devise}", 1, ln=True, align="R")
    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 5, "Merci pour votre confiance!", ln=True, align="C")
    return pdf.output(dest='S').encode('latin-1')

def generer_pdf_devis_consulting(numero, type_devis, client, titre_projet, parcelle, localisation, details_sections, devise, tel_client, main_oeuvre=0):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "ASYMAS CONSULTING", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, "Bureau d'Etudes - Construction - Genie Civil", ln=True, align="C")
    pdf.ln(3)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, f"DEVIS {type_devis.upper()}", ln=True, align="C")
    pdf.ln(3)
    pdf.set_font("Arial", "", 9)
    pdf.cell(95, 5, f"N°: {numero}", ln=False)
    pdf.cell(95, 5, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(95, 5, f"Client: {client}", ln=False)
    pdf.cell(95, 5, f"Tel: {tel_client}", ln=True)
    pdf.cell(0, 5, f"Projet: {titre_projet}", ln=True)
    if parcelle: pdf.cell(0, 5, f"Parcelle: {parcelle}", ln=True)
    pdf.cell(0, 5, f"Localisation: {localisation}", ln=True)
    pdf.ln(3)

    total_general = 0
    for section in details_sections:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 7, f"{section['numero']}. {section['titre']}", ln=True, fill=True)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(10, 6, "No", 1)
        pdf.cell(80, 6, "Designation", 1)
        pdf.cell(15, 6, "Unite", 1)
        pdf.cell(20, 6, "Qte", 1)
        pdf.cell(30, 6, "PU", 1)
        pdf.cell(35, 6, "PT", 1, ln=True)
        pdf.set_font("Arial", "", 8)
        sous_total = 0
        for item in section['items']:
            pt = item['qte'] * item['pu']
            sous_total += pt
            pdf.cell(10, 6, str(item['num']), 1)
            pdf.cell(80, 6, str(item['designation'])[:45], 1)
            pdf.cell(15, 6, str(item['unite']), 1, align="C")
            pdf.cell(20, 6, f"{item['qte']:g}", 1, align="C")
            pdf.cell(30, 6, f"{item['pu']:,.2f}", 1, align="R")
            pdf.cell(35, 6, f"{pt:,.2f}", 1, align="R", ln=True)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(155, 7, f"Sous-total {section['titre']}", 1)
        pdf.cell(35, 7, f"{sous_total:,.2f}", 1, align="R", ln=True)
        total_general += sous_total
        pdf.ln(2)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(155, 8, "TOTAL MATERIAUX", 1)
    pdf.cell(35, 8, f"{total_general:,.2f} {devise}", 1, align="R", ln=True)
    if main_oeuvre > 0:
        pdf.cell(155, 8, "Main d'oeuvre", 1)
        pdf.cell(35, 8, f"{main_oeuvre:,.2f} {devise}", 1, align="R", ln=True)
        total_general += main_oeuvre
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(155, 10, "COUT TOTAL DU PROJET", 1, fill=True)
    pdf.cell(35, 10, f"{total_general:,.2f} {devise}", 1, fill=True, align="R", ln=True)
    pdf.ln(5)

    if type_devis == "Industriel":
        ingenieur = "SAMY TSANGYA"
        tel_ing = "+243 995 105 623"
        adresse_ing = "Beni, Nord-Kivu, RDC"
    else:
        ingenieur = "ESDRAS TSANGYA"
        tel_ing = "+243 972 888 690"
        adresse_ing = "Beni, Nord-Kivu, RDC | Av. du 30 Juin, Q. Malepe"

    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 6, f"Ingenieur: {ingenieur}", ln=True)
    pdf.cell(0, 6, f"Tel: {tel_ing}", ln=True)
    pdf.cell(0, 6, f"Adresse: {adresse_ing}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

def generer_excel_pro(df, titre, total_rev=0, total_dep=0, solde=0):
    wb = Workbook()
    ws = wb.active
    ws.title = "Releve"
    ws.merge_cells('A1:F1')
    ws['A1'] = f"ASYMAS BUSINESS - {titre}"
    ws['A1'].font = Font(size=16, bold=True, color="FFFFFF")
    ws['A1'].fill = PatternFill(start_color="00B050", end_color="00B050", fill_type="solid")
    ws['A1'].alignment = Alignment(horizontal="center")
    row = 3
    for col_idx, col_name in enumerate(df.columns, 1):
        cell = ws.cell(row=row, column=col_idx, value=col_name)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="00B050", end_color="00B050", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    row += 1
    for _, data_row in df.iterrows():
        for col_idx, value in enumerate(data_row, 1):
            ws.cell(row=row, column=col_idx, value=value)
        row += 1
    if total_rev > 0 or total_dep > 0:
        row += 1
        ws.cell(row=row, column=1, value="TOTAL REVENUS").font = Font(bold=True)
        ws.cell(row=row, column=2, value=total_rev)
        row += 1
        ws.cell(row=row, column=1, value="TOTAL DEPENSES").font = Font(bold=True)
        ws.cell(row=row, column=2, value=total_dep)
        row += 1
        ws.cell(row=row, column=1, value="SOLDE").font = Font(bold=True)
        ws.cell(row=row, column=2, value=solde)
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    return excel_file.getvalue()

def creer_facture_auto(type_fact, client, details, total, devise, details_list=None, tel_client="+243...", periode=""):
    numero = f"{type_fact[:3].upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    details_json = json.dumps(details_list) if details_list else "[]"
    supabase.table("compta").insert({
        "date": str(date.today()),
        "type": "Revenu",
        "categorie": type_fact,
        "description": f"{type_fact} - {client}",
        "montant": float(total),
        "devise": devise,
        "numero_facture": numero,
        "details": details_json,
        "utilisateur": st.session_state.user_name
    }).execute()
    pdf_bytes = generer_pdf_facture(numero, type_fact, client, details_list if details_list else [{"nom": details, "qte": 1, "pu": total}], total, devise, tel_client)
    return numero, pdf_bytes

# === SIDEBAR ===
st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
st.sidebar.markdown(f"**Rôle:** {st.session_state.user_role}")
if st.sidebar.button("🚪 Déconnexion", width="stretch"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# === TABS ===
tabs_dispo = []
if st.session_state.user_role == "PDG" or perms.get('dashboard', False):
    tabs_dispo.append("📊 Dashboard")
if st.session_state.user_role == "PDG" or perms.get('commerce', False):
    tabs_dispo.append("🛒 Commerce")
if st.session_state.user_role == "PDG" or perms.get('stock', False):
    tabs_dispo.append("📦 Gestion Stock")
if st.session_state.user_role == "PDG" or perms.get('immobilier', False):
    tabs_dispo.append("🏠 Immobilier")
if st.session_state.user_role == "PDG" or perms.get('automobile', False):
    tabs_dispo.append("🚗 Automobile")
if st.session_state.user_role == "PDG" or perms.get('parc', False):
    tabs_dispo.append("🚘 Gestion Parc")
if st.session_state.user_role == "PDG" or perms.get('comptabilite', False):
    tabs_dispo.append("💰 Comptabilité")
if st.session_state.user_role == "PDG" or perms.get('factures', False):
    tabs_dispo.append("📄 Factures")
if st.session_state.user_role == "PDG" or perms.get('devis_industriel', False) or perms.get('devis_batiment', False):
    tabs_dispo.append("📋 Devis")
if st.session_state.user_role == "PDG" or perms.get('users', False):
    tabs_dispo.append("👥 Utilisateurs")

if not tabs_dispo:
    st.error("Aucun accès - Contacte le PDG")
    st.stop()

tabs = st.tabs(tabs_dispo)
tab_map = {name: tab for name, tab in zip(tabs_dispo, tabs)}

# === DASHBOARD ===
if "📊 Dashboard" in tab_map:
    with tab_map["📊 Dashboard"]:
        st.markdown("## 📊 Dashboard ASYMAS BUSINESS")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Articles", len(df_articles))
        col2.metric("🚗 Voitures", len(df_voitures))
        col3.metric("💰 Revenus", f"{df_compta[df_compta['type']=='Revenu']['montant'].sum():,.0f} FC" if not df_compta.empty else "0 FC")
        col4.metric("📋 Devis", len(df_devis))
        st.divider()
        if not df_compta.empty:
            st.subheader("📈 Évolution Revenus")
            df_compta['date'] = pd.to_datetime(df_compta['date'])
            df_rev = df_compta[df_compta['type']=='Revenu'].groupby('date')['montant'].sum().reset_index()
            st.line_chart(df_rev.set_index('date'))

# === COMMERCE ===
if "🛒 Commerce" in tab_map:
    with tab_map["🛒 Commerce"]:
        st.markdown("## 🛒 Point de Vente Commerce")
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
        if df_articles.empty:
            st.error("Aucun article disponible - Ajoute des articles dans Gestion Stock")
        else:
            col_gauche, col_droite = st.columns([2,1])
            with col_gauche:
                st.subheader("👤 Client")
                st.session_state.client_com_nom = st.text_input("Nom Client", value=st.session_state.client_com_nom, key="nom_client_com")
                st.session_state.client_com_tel = st.text_input("Téléphone Client", value=st.session_state.client_com_tel, key="tel_client_com")
                st.subheader("📷 Scanner QR Code Article")
                qr_code_scan = qrcode_scanner(key='qr_scanner_commerce')
                if qr_code_scan and qr_code_scan!= st.session_state.last_qr:
                    st.session_state.last_qr = qr_code_scan
                    st.success(f"✅ QR scanné : {qr_code_scan}")
                    df_articles_filtre = df_articles[df_articles['code_qr'] == qr_code_scan]
                    if not df_articles_filtre.empty:
                        p = df_articles_filtre.iloc[0]
                        existant = next((item for item in st.session_state.panier_commerce if item['id'] == int(p['id'])), None)
                        if existant:
                            if existant['qte'] < int(p['stock']):
                                existant['qte'] += 1
                                st.success(f"Quantité augmentée: {existant['qte']}x")
                            else:
                                st.error("Stock insuffisant!")
                        else:
                            st.session_state.panier_commerce.append({
                                "id": int(p['id']),
                                "nom": str(p['nom_article']),
                                "pu": float(p['prix_vente']),
                                "qte": 1,
                                "code_qr": p.get('code_qr',''),
                                "stock_max": int(p['stock'])
                            })
                            st.success(f"Ajouté: {p['nom_article']}")
                        st.rerun()
                    else:
                        st.error("❌ Article introuvable")
                st.subheader("🔍 Ou Recherche Manuelle")
                search_article = st.text_input("Nom, Code QR ou Catégorie", placeholder="Tape pour filtrer...", key="search_article_manuel").strip()
                df_articles_filtre = df_articles.copy()
                if search_article:
                    search_clean = search_article.upper()
                    df_articles_filtre = df_articles_filtre[
                        df_articles_filtre['nom_article'].str.contains(search_clean, case=False, na=False) |
                        df_articles_filtre['code_qr'].str.contains(search_clean, case=False, na=False) |
                        df_articles_filtre['categorie'].str.contains(search_clean, case=False, na=False)
                    ]
                if df_articles_filtre.empty:
                    st.warning("⚠️ Aucun article trouvé")
                else:
                    st.success(f"✅ {len(df_articles_filtre)} article(s) disponible(s)")
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
                    st.download_button(
                        "📥 Télécharger Facture PDF",
                        data=st.session_state.pdf_data,
                        file_name=f"{st.session_state.num_fact}.pdf",
                        mime="application/pdf",
                        width="stretch"
                    )
                    pdf_b64 = base64.b64encode(st.session_state.pdf_data).decode()
                    st.components.v1.html(f"""
                        <button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">
                            🖨️ IMPRIMER LA FACTURE
                        </button>
                        <script>
                        function printPDF() {{
                            const pdfData = 'data:application/pdf;base64,{pdf_b64}';
                            const win = window.open('', '_blank');
                            win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');
                            win.document.close();
                            setTimeout(() => {{ win.print(); }}, 1000);
                        }}
                        </script>
                    """, height=60)
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
                                    supabase.table("ventes").insert({
                                        "numero_facture": num_fact,
                                        "client_nom": st.session_state.client_com_nom,
                                        "article_id": item['id'],
                                        "quantite": item['qte'],
                                        "prix_unitaire": item['pu'],
                                        "total": item['qte'] * item['pu']
                                    }).execute()
                                    stock_actuel = df_articles[df_articles['id'] == item['id']]['stock'].iloc[0]
                                    supabase.table("articles").update({"stock": int(stock_actuel - item['qte'])}).eq("id", item['id']).execute()
                                    details_list.append({
                                        "nom": item['nom'],
                                        "qte": item['qte'],
                                        "pu": item['pu'],
                                        "total": item['qte'] * item['pu']
                                    })
                                details_json = json.dumps(details_list)
                                supabase.table("compta").insert({
                                    "date": str(date.today()),
                                    "type": "Revenu",
                                    "categorie": "Vente Commerce",
                                    "description": f"Vente - {st.session_state.client_com_nom}",
                                    "montant": float(total_panier),
                                    "devise": "FC",
                                    "numero_facture": num_fact,
                                    "details": details_json,
                                    "utilisateur": st.session_state.user_name
                                }).execute()
                                pdf_bytes = generer_pdf_facture(
                                    num_fact,
                                    "Vente Commerce",
                                    st.session_state.client_com_nom,
                                    details_list,
                                    total_panier,
                                    "FC",
                                    st.session_state.client_com_tel
                                )
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
        st.markdown("## 📦 Gestion Stock - Articles")
        with st.expander("➕ Ajouter Nouvel Article"):
            st.subheader("Scanner QR pour remplir le code")
            qr_scan_ajout = qrcode_scanner(key='qr_add_article')
            if qr_scan_ajout:
                st.success(f"QR scanné : {qr_scan_ajout}")
                st.session_state.qr_code_temp = qr_scan_ajout
            with st.form("form_article", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nom = c1.text_input("Nom Article")
                cat = c2.text_input("Catégorie")
                code_qr = c3.text_input("Code QR", value=st.session_state.get('qr_code_temp', ''), placeholder="Scanne ou tape le code")
                c1, c2, c3 = st.columns(3)
                prix_achat_fc = c1.number_input("Prix Achat FC", min_value=0.0)
                prix_vente_fc = c2.number_input("Prix Vente FC", min_value=0.0)
                prix_vente_usd = c3.number_input("Prix Vente $", min_value=0.0)
                stock = c1.number_input("Stock", min_value=0)
                if st.form_submit_button("💾 Ajouter Article"):
                    try:
                        data_insert = {
                            "nom_article": str(nom),
                            "categorie": str(cat),
                            "prix_achat": float(prix_achat_fc),
                            "prix_vente": float(prix_vente_fc),
                            "stock": int(stock),
                            "code_qr": str(code_qr) if code_qr else None
                        }
                        colonnes_articles = get_table_columns("articles")
                        if "prix_vente_usd" in colonnes_articles:
                            data_insert["prix_vente_usd"] = float(prix_vente_usd)
                        supabase.table("articles").insert(data_insert).execute()
                        st.success(f"Article {nom} ajouté avec QR: {code_qr}")
                        if 'qr_code_temp' in st.session_state:
                            del st.session_state.qr_code_temp
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout")
                        st.code(repr(e))
        st.divider()
        st.subheader("📋 Liste des Articles - Modifier/Supprimer")
        if df_articles.empty:
            st.info("Aucun article")
        else:
            for _, row in df_articles.iterrows():
                with st.expander(f"{row['nom_article']} - {row.get('prix_vente',0):,.0f} FC - Stock:{row.get('stock',0)}"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        new_nom = st.text_input("Nom", value=row['nom_article'], key=f"nom_{row['id']}")
                        new_cat = st.text_input("Catégorie", value=row.get('categorie',''), key=f"cat_{row['id']}")
                        new_code_qr = st.text_input("Code QR", value=row.get('code_qr',''), key=f"qr_art_{row['id']}")
                    with c2:
                        new_prix_a = st.number_input("Prix Achat FC", value=float(row.get('prix_achat',0)), key=f"pa_{row['id']}")
                        new_prix_v = st.number_input("Prix Vente FC", value=float(row.get('prix_vente',0)), key=f"pv_{row['id']}")
                        new_prix_usd = st.number_input("Prix Vente $", value=float(row.get('prix_vente_usd',0)), key=f"pusd_{row['id']}")
                    with c3:
                        new_stock = st.number_input("Stock", value=int(row.get('stock',0)), key=f"stock_{row['id']}")
                    c1, c2 = st.columns(2)
                    if c1.button("✏️ Modifier", key=f"mod_art_{row['id']}", width="stretch"):
                        try:
                            data_update = {
                                "nom_article": str(new_nom),
                                "categorie": str(new_cat),
                                "prix_achat": float(new_prix_a),
                                "prix_vente": float(new_prix_v),
                                "stock": int(new_stock),
                                "code_qr": str(new_code_qr) if new_code_qr else None
                            }
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
                    else:
                        c2.info("🔒 Suppression non autorisée")

# === IMMOBILIER ===
if "🏠 Immobilier" in tab_map:
    with tab_map["🏠 Immobilier"]:
        st.markdown("## 🏠 Gestion Immobilière")
        with st.expander("➕ Ajouter Bien Immobilier"):
            with st.form("form_immobilier", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nom = c1.text_input("Nom du Bien")
                type_bien = c2.selectbox("Type", ["Maison", "Appartement", "Bureau", "Terrain", "Commerce"])
                adresse = c3.text_input("Adresse")
                c1, c2, c3 = st.columns(3)
                loyer = c1.number_input("Loyer Mensuel", min_value=0.0)
                superficie = c2.number_input("Superficie m²", min_value=0.0)
                statut = c3.selectbox("Statut", ["Libre", "Loué", "Vendu"])
                if st.form_submit_button("💾 Ajouter Bien"):
                    try:
                        supabase.table("immobilier").insert({
                            "nom": nom,
                            "type": type_bien,
                            "adresse": adresse,
                            "loyer_mensuel": float(loyer),
                            "superficie": float(superficie),
                            "statut": statut,
                            "utilisateur": st.session_state.user_name
                        }).execute()
                        st.success("Bien ajouté")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout")
                        st.code(repr(e))
        st.divider()
        df_immo = load_table("immobilier")
        if df_immo.empty:
            st.info("Aucun bien immobilier")
        else:
            for _, row in df_immo.iterrows():
                with st.expander(f"{row['nom']} - {row['type']} - {row['loyer_mensuel']:,.0f} FC/mois"):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Adresse:** {row['adresse']}")
                    c2.write(f"**Superficie:** {row['superficie']} m²")
                    c3.write(f"**Statut:** {row['statut']}")
                    if row['statut'] == "Libre":
                        if c3.button("💰 Louer", key=f"louer_{row['id']}", width="stretch"):
                            client = st.text_input("Nom Locataire", key=f"locataire_{row['id']}")
                            if client:
                                numero_fact = f"LOY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                                details_list = [{"nom": f"Loyer {row['nom']}", "qte": 1, "pu": row['loyer_mensuel']}]
                                num_fact, pdf_bytes = creer_facture_auto("Loyer", client, f"Loyer {row['nom']}", row['loyer_mensuel'], "FC", details_list)
                                supabase.table("immobilier").update({"statut": "Loué", "locataire": client}).eq("id", int(row['id'])).execute()
                                st.success(f"Loué à {client}")
                                st.download_button("📥 Télécharger Facture", data=pdf_bytes, file_name=f"{num_fact}.pdf", mime="application/pdf", key=f"dl_loyer_{row['id']}")
                                st.cache_data.clear()
                                st.rerun()

# === AUTOMOBILE ===
if "🚗 Automobile" in tab_map:
    with tab_map["🚗 Automobile"]:
        st.markdown("## 🚗 Vente Automobile")
        if df_voitures.empty:
            st.info("Aucune voiture en stock - Ajoute dans Gestion Parc")
        else:
            df_dispo = df_voitures[df_voitures['statut'] == "Disponible"]
            if df_dispo.empty:
                st.warning("Aucune voiture disponible")
            else:
                for _, row in df_dispo.iterrows():
                    with st.expander(f"{row['marque']} {row['modele']} - {row['annee']} - {row['prix_vente']:,.0f} FC"):
                        c1, c2, c3 = st.columns(3)
                        c1.write(f"**Plaque:** {row.get('plaque','N/A')}")
                        c2.write(f"**Couleur:** {row.get('couleur','')}")
                        c3.write(f"**KM:** {row.get('kilometrage',0):,}")
                        client_nom = st.text_input("Nom Acheteur", key=f"acheteur_{row['id']}")
                        if st.button("💰 VENDRE", key=f"vendre_{row['id']}", type="primary", width="stretch"):
                            if not client_nom:
                                st.error("Nom acheteur obligatoire")
                            else:
                                try:
                                    details_list = [{"nom": f"{row['marque']} {row['modele']} {row['annee']}", "qte": 1, "pu": row['prix_vente']}]
                                    num_fact, pdf_bytes = creer_facture_auto("Vente Voiture", client_nom, f"Vente {row['marque']} {row['modele']}", row['prix_vente'], "FC", details_list)
                                    supabase.table("voitures").update({"statut": "Vendu", "acheteur": client_nom, "date_vente": str(date.today())}).eq("id", int(row['id'])).execute()
                                    st.success(f"Vendu à {client_nom}")
                                    st.download_button("📥 Télécharger Facture", data=pdf_bytes, file_name=f"{num_fact}.pdf", mime="application/pdf", key=f"dl_auto_{row['id']}")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erreur vente")
                                    st.code(repr(e))

# === GESTION PARC ===
if "🚘 Gestion Parc" in tab_map:
    with tab_map["🚘 Gestion Parc"]:
        st.markdown("## 🚘 Gestion Parc Automobile")
        with st.expander("➕ Ajouter Voiture au Parc"):
            st.subheader("Scanner QR Plaque")
            qr_scan_voiture = qrcode_scanner(key='qr_add_voiture')
            if qr_scan_voiture:
                st.success(f"QR scanné : {qr_scan_voiture}")
                st.session_state.qr_voiture_temp = qr_scan_voiture
            with st.form("form_voiture", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                marque = c1.text_input("Marque")
                modele = c2.text_input("Modèle")
                annee = c3.number_input("Année", min_value=1990, max_value=2026, value=2020)
                c1, c2, c3 = st.columns(3)
                plaque = c1.text_input("Plaque", value=st.session_state.get('qr_voiture_temp', ''))
                couleur = c2.text_input("Couleur")
                km = c3.number_input("Kilométrage", min_value=0)
                c1, c2 = st.columns(2)
                prix_achat = c1.number_input("Prix Achat FC", min_value=0.0)
                prix_vente = c2.number_input("Prix Vente FC", min_value=0.0)
                if st.form_submit_button("💾 Ajouter au Parc"):
                    try:
                        supabase.table("voitures").insert({
                            "marque": marque,
                            "modele": modele,
                            "annee": int(annee),
                            "plaque": plaque,
                            "couleur": couleur,
                            "kilometrage": int(km),
                            "prix_achat": float(prix_achat),
                            "prix_vente": float(prix_vente),
                            "statut": "Disponible",
                            "utilisateur": st.session_state.user_name
                        }).execute()
                        st.success(f"Voiture {marque} {modele} ajoutée")
                        if 'qr_voiture_temp' in st.session_state:
                            del st.session_state.qr_voiture_temp
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout voiture")
                        st.code(repr(e))
        st.divider()
        st.subheader("📋 Parc Complet")
        if df_voitures.empty:
            st.info("Parc vide")
        else:
            for _, row in df_voitures.iterrows():
                with st.expander(f"{row['marque']} {row['modele']} - {row['plaque']} - {row['statut']}"):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Année:** {row['annee']} | **KM:** {row.get('kilometrage',0):,}")
                    c2.write(f"**Achat:** {row.get('prix_achat',0):,.0f} FC")
                    c3.write(f"**Vente:** {row.get('prix_vente',0):,.0f} FC")
                    if row['statut'] == "Vendu":
                        st.success(f"Vendu à {row.get('acheteur','')} le {row.get('date_vente','')}")

# === COMPTABILITÉ ===
if "💰 Comptabilité" in tab_map:
    with tab_map["💰 Comptabilité"]:
        st.markdown("## 💰 Comptabilité - Relevé par Catégorie")
        colonnes_compta = get_table_columns("compta")
        with st.expander("➕ Ajouter Opération"):
            with st.form("form_compta", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                type_op = c1.selectbox("Type", ["Revenu", "Dépense"])
                cat = c2.text_input("Catégorie", placeholder="Ex: Loyer, Vente Auto, Carburant")
                montant = c3.number_input("Montant", min_value=0.0)
                data_insert = {"type": str(type_op), "categorie": str(cat), "montant": float(montant), "utilisateur": st.session_state.user_name}
                if "description" in colonnes_compta:
                    desc = c1.text_input("Description", placeholder="Ex: Loyer - Client Jean")
                    data_insert["description"] = str(desc)
                if "devise" in colonnes_compta:
                    devise = c2.selectbox("Devise", ["FC", "$", "€"])
                    data_insert["devise"] = str(devise)
                if "date" in colonnes_compta:
                    date_op = c3.date_input("Date", value=date.today())
                    data_insert["date"] = str(date_op)
                if st.form_submit_button("💾 Ajouter Opération"):
                    try:
                        supabase.table("compta").insert(data_insert).execute()
                        st.success("Opération ajoutée")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout")
                        st.code(repr(e))
        st.divider()
        if df_compta.empty:
            st.info("Aucune opération")
        else:
            df_compta_sorted = df_compta.sort_values('date', ascending=False)
            col_f1, col_f2, col_f3 = st.columns(3)
            date_debut = col_f1.date_input("📅 Date début", value=date.today() - timedelta(days=30), key="date_debut_compta")
            date_fin = col_f2.date_input("📅 Date fin", value=date.today(), key="date_fin_compta")
            filtre_nom = col_f3.text_input("👤 Nom Client", placeholder="Tape un nom...", key="filtre_nom_compta")
            df_filtre_compta = df_compta_sorted[(df_compta_sorted['date'] >= str(date_debut)) & (df_compta_sorted['date'] <= str(date_fin))]
            if filtre_nom:
                df_filtre_compta = df_filtre_compta[df_filtre_compta['description'].str.contains(filtre_nom, case=False, na=False)]
            col_t1, col_t2, col_t3 = st.columns(3)
            total_rev = df_filtre_compta[df_filtre_compta['type']=='Revenu']['montant'].sum()
            total_dep = df_filtre_compta[df_filtre_compta['type']=='Dépense']['montant'].sum()
            solde = total_rev - total_dep
            col_t1.metric("💚 Revenus", f"{total_rev:,.0f} FC")
            col_t2.metric("💸 Dépenses", f"{total_dep:,.0f} FC")
            col_t3.metric("💰 Solde", f"{solde:,.0f} FC", delta=f"{solde:,.0f}")
            if not df_filtre_compta.empty:
                excel_data = generer_excel_pro(df_filtre_compta, "Releve Comptable", total_rev, total_dep, solde)
                st.download_button(label="📥 Télécharger Relevé Excel", data=excel_data, file_name=f"releve_compta_{date_debut}_{date_fin}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
            st.divider()
            st.subheader("📊 Relevé par Catégorie")
            categories_autorisees = []
            if st.session_state.user_role == "PDG":
                categories_autorisees = df_filtre_compta['categorie'].dropna().unique().tolist()
            else:
                if perms.get('commerce', False): categories_autorisees.append("Vente Commerce")
                if perms.get('immobilier', False): categories_autorisees.append("Loyer")
                if perms.get('automobile', False): categories_autorisees.append("Vente Voiture")
            if 'categorie' in df_filtre_compta.columns:
                categories = [c for c in df_filtre_compta['categorie'].dropna().unique() if c in categories_autorisees or st.session_state.user_role == "PDG"]
                for cat in categories:
                    df_cat = df_filtre_compta[df_filtre_compta['categorie'] == cat]
                    total_cat = df_cat['montant'].sum()
                    with st.expander(f"📁 {cat} - Total: {total_cat:,.0f} FC ({len(df_cat)} opérations)"):
                        for idx, row in df_cat.iterrows():
                            c1, c2, c3, c4 = st.columns([3,2,2,2])
                            c1.write(f"**{row['date']}** | {row.get('description','')}")
                            c2.write(f"{row['montant']:,.0f} {row.get('devise','FC')}")
                            c3.write(f"Par: {row.get('utilisateur','')}")
                            if 'numero_facture' in row and pd.notna(row['numero_facture']):
                                if c4.button("📄 PDF", key=f"pdf_fact_{row['id']}"):
                                    try:
                                        details_list = json.loads(row.get('details', '[]')) if row.get('details') else [{"nom": row.get('description',''), "qte": 1, "pu": row['montant']}]
                                        client_nom = row.get('description','').split(' - ')[1] if ' - ' in row.get('description','') else 'Client'
                                        pdf_bytes = generer_pdf_facture(row['numero_facture'], row.get('categorie','Vente'), client_nom, details_list, row['montant'], row.get('devise','FC'))
                                        st.download_button(label="📥 Télécharger", data=bytes(pdf_bytes), file_name=f"{row['numero_facture']}.pdf", mime="application/pdf", key=f"dl_compta_{row['id']}")
                                        pdf_b64 = base64.b64encode(pdf_bytes).decode()
                                        st.components.v1.html(f"""<button onclick="printPDF()" style="width:100%; padding:5px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:3px; cursor:pointer;">🖨️ Imprimer</button><script>function printPDF() {{const pdfData = 'data:application/pdf;base64,{pdf_b64}'; const win = window.open('', '_blank'); win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>'); win.document.close(); setTimeout(() => {{ win.print(); }}, 1000);}}</script>""", height=35)
                                    except Exception as e:
                                        st.error("Erreur génération PDF")
                            else:
                                c4.write("")
            else:
                st.dataframe(df_filtre_compta, width="stretch", hide_index=True)

# === FACTURES ===
if "📄 Factures" in tab_map:
    with tab_map["📄 Factures"]:
        st.markdown("## 📄 Toutes les Factures")
        df_proforma = load_table("factures_proforma")
        df_compta_factures = df_compta[df_compta['numero_facture'].notna()] if 'numero_facture' in df_compta.columns else pd.DataFrame()
        peut_industriel = st.session_state.user_role == "PDG" or perms.get('devis_industriel', False)
        peut_batiment = st.session_state.user_role == "PDG" or perms.get('devis_batiment', False)
        with st.expander("➕ Créer Facture Proforma Technique"):
            if not peut_industriel and not peut_batiment:
                st.error("🔒 Accès non autorisé - Contacte le PDG")
                st.stop()
            if 'lignes_proforma' not in st.session_state:
                st.session_state.lignes_proforma = [{"nom": "", "qte": 1, "pu": 0.0}]
            types_dispo = []
            if peut_industriel: types_dispo.append("Industriel")
            if peut_batiment: types_dispo.append("Bâtiment & Génie Civil")
            c1, c2, c3 = st.columns(3)
            if len(types_dispo) == 1:
                type_proforma = types_dispo[0]
                c1.info(f"Type autorisé : {type_proforma}")
            else:
                type_proforma = c1.selectbox("Type Proforma", types_dispo, key="type_proforma")
            client_proforma = c2.text_input("Client", key="client_proforma")
            tel_proforma = c3.text_input("Téléphone", value="+243...", key="tel_proforma")
            c1, c2 = st.columns(2)
            devise_proforma = c1.selectbox("Devise", ["$", "€", "FC"], key="devise_proforma")
            date_validite = c2.date_input("Valable jusqu'au", value=date.today() + timedelta(days=30), key="date_validite_proforma")
            titre_projet = st.text_input("Titre du projet", value="FOURNITURE MATÉRIELS", key="titre_projet_proforma")
            localisation = st.text_input("Localisation", value="Beni, Nord-Kivu", key="localisation_proforma")
            st.markdown("### Détails Matériaux / Prestations")
            col_btn1, col_btn2 = st.columns([3,1])
            if col_btn1.button("➕ Ajouter Ligne", key="add_ligne_proforma"):
                st.session_state.lignes_proforma.append({"nom": "", "qte": 1, "pu": 0.0})
                st.rerun()
            total_proforma = 0
            for i, ligne in enumerate(st.session_state.lignes_proforma):
                c1, c2, c3, c4 = st.columns([4,1,2,1])
                ligne['nom'] = c1.text_input(f"Designation {i+1}", value=ligne['nom'], key=f"nom_prof_{i}")
                ligne['qte'] = c2.number_input(f"Qté {i+1}", min_value=1, value=ligne['qte'], key=f"qte_prof_{i}")
                ligne['pu'] = c3.number_input(f"PU {i+1}", min_value=0.0, value=ligne['pu'], key=f"pu_prof_{i}")
                if c4.button("❌", key=f"del_prof_{i}") and len(st.session_state.lignes_proforma) > 1:
                    st.session_state.lignes_proforma.pop(i)
                    st.rerun()
                total_proforma += ligne['qte'] * ligne['pu']
            main_oeuvre_prof = st.number_input("💪 Main d'Oeuvre", min_value=0.0, value=0.0, key="mo_proforma")
            montant_global_prof = total_proforma + main_oeuvre_prof
            st.metric("💰 COUT GLOBAL PROFORMA", f"{montant_global_prof:,.2f} {devise_proforma}")
            st.info(f"Total matériaux: {total_proforma:,.2f} + Main d'oeuvre: {main_oeuvre_prof:,.2f}")
            if st.button("💾 GÉNÉRER PROFORMA TECHNIQUE", type="primary", width="stretch"):
                if not client_proforma:
                    st.error("⚠️ Nom du client obligatoire")
                    st.stop()
                try:
                    numero_proforma = f"PRO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    ingenieur = "SAMY TSANGYA" if type_proforma == "Industriel" else "ESDRAS TSANGYA"
                    tel_ing = "+243 995 105 623" if type_proforma == "Industriel" else "+243 972 888 690"
                    details_sections = [{"numero": "I", "titre": "MATERIAUX / PRESTATIONS", "items": [{"num": f"{i+1}", "designation": l['nom'], "unite": "U", "qte": l['qte'], "pu": l['pu']} for i, l in enumerate(st.session_state.lignes_proforma) if l['nom']]}]
                    supabase.table("factures_proforma").insert({"numero": numero_proforma, "client": client_proforma, "telephone": tel_proforma, "categorie": f"Proforma {type_proforma}", "type_proforma": type_proforma, "titre_projet": titre_projet, "localisation": localisation, "montant": float(montant_global_prof), "main_oeuvre": float(main_oeuvre_prof), "devise": devise_proforma, "date": str(date.today()), "date_validite": str(date_validite), "details": json.dumps(st.session_state.lignes_proforma), "ingenieur": ingenieur, "telephone_ingenieur": tel_ing, "statut": "En attente", "utilisateur": st.session_state.user_name}).execute()
                    pdf_bytes = generer_pdf_devis_consulting(numero_proforma, type_proforma, client_proforma, titre_projet, "", localisation, details_sections, devise_proforma, tel_proforma, main_oeuvre_prof)
                    st.success(f"✅ Proforma {numero_proforma} créée - {type_proforma}")
                    st.download_button(label="📥 TÉLÉCHARGER PROFORMA PDF", data=bytes(pdf_bytes), file_name=f"{numero_proforma}.pdf", mime="application/pdf", width="stretch", type="primary")
                    pdf_b64 = base64.b64encode(pdf_bytes).decode()
                    st.components.v1.html(f"""<button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">🖨️ IMPRIMER PROFORMA</button><script>function printPDF() {{const pdfData = 'data:application/pdf;base64,{pdf_b64}'; const win = window.open('', '_blank'); win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>'); win.document.close(); setTimeout(() => {{ win.print(); }}, 1000);}}</script>""", height=60)
                    st.session_state.lignes_proforma = [{"nom": "", "qte": 1, "pu": 0.0}]
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error("Erreur création proforma")
                    st.code(repr(e))
        st.divider()
        col_f1, col_f2, col_f3 = st.columns(3)
        date_debut_fact = col_f1.date_input("📅 Date début", value=date.today() - timedelta(days=30), key="date_debut_fact")
        date_fin_fact = col_f2.date_input("📅 Date fin", value=date.today(), key="date_fin_fact")
        filtre_nom_fact = col_f3.text_input("👤 Nom Client", placeholder="Tape un nom...", key="filtre_nom_fact")
        st.subheader("📋 Factures Proforma Techniques")
        df_proforma_filtre = df_proforma.copy()
        if 'date' in df_proforma_filtre.columns:
            df_proforma_filtre = df_proforma_filtre[(df_proforma_filtre['date'] >= str(date_debut_fact)) & (df_proforma_filtre['date'] <= str(date_fin_fact))]
        if filtre_nom_fact:
            df_proforma_filtre = df_proforma_filtre[df_proforma_filtre['client'].str.contains(filtre_nom_fact, case=False, na=False)]
        if st.session_state.user_role!= "PDG":
            types_autorises = []
            if peut_industriel: types_autorises.append("Industriel")
            if peut_batiment: types_autorises.append("Bâtiment & Génie Civil")
            if 'type_proforma' in df_proforma_filtre.columns:
                df_proforma_filtre = df_proforma_filtre[df_proforma_filtre['type_proforma'].isin(types_autorises)]
        if df_proforma_filtre.empty:
            st.info("Aucune proforma pour cette période")
        else:
            types_prof = df_proforma_filtre['type_proforma'].dropna().unique() if 'type_proforma' in df_proforma_filtre.columns else ['Proforma']
            for type_p in types_prof:
                df_type = df_proforma_filtre[df_proforma_filtre['type_proforma'] == type_p] if 'type_proforma' in df_proforma_filtre.columns else df_proforma_filtre
                total_type = df_type['montant'].sum()
                with st.expander(f"📁 Proforma {type_p} - Total: {total_type:,.2f} ({len(df_type)} proforma)"):
                    for idx, row in df_type.iterrows():
                        col_info, col_btn1, col_btn2, col_btn3 = st.columns([3,1,1,1])
                        col_info.markdown(f"**{row['numero']}** | {row.get('date','')} | {row['client']} | **{row.get('montant',0):,.0f} {row.get('devise','$')}** | Ing: {row.get('ingenieur','')}")
                        if col_btn1.button("👁️ Voir", key=f"voir_prof_{row['id']}", width="stretch"):
                            st.json(json.loads(row.get('details','[]')))
                        if col_btn2.button("📥 PDF", key=f"dl_prof_{row['id']}", width="stretch"):
                            details = json.loads(row.get('details', '[]'))
                            details_sections = [{"numero": "I", "titre": "MATERIAUX / PRESTATIONS", "items": [{"num": f"{i+1}", "designation": d['nom'], "unite": "U", "qte": d['qte'], "pu": d['pu']} for i, d in enumerate(details)]}]
                            pdf_bytes = generer_pdf_devis_consulting(row['numero'], row.get('type_proforma','Industriel'), row['client'], row.get('titre_projet','PROJET'), "", row.get('localisation',''), details_sections, row.get('devise','$'), row.get('telephone',''), row.get('main_oeuvre',0))
                            st.download_button(label="💾 Télécharger", data=bytes(pdf_bytes), file_name=f"{row['numero']}.pdf", mime="application/pdf", key=f"dl_btn_prof_{row['id']}")
                        if st.session_state.user_role == "PDG":
                            if col_btn3.button("🗑️", key=f"del_prof_{row['id']}", width="stretch"):
                                supabase.table("factures_proforma").delete().eq("id", int(row['id'])).execute()
                                st.success("Proforma supprimée")
                                st.cache_data.clear()
                                st.rerun()
        st.divider()
        st.subheader("📋 Factures Automatiques - Triées par Catégorie")
        if st.session_state.user_role!= "PDG":
            categories_autorisees = []
            if perms.get('commerce', False): categories_autorisees.append("Vente Commerce")
            if perms.get('immobilier', False): categories_autorisees.append("Loyer")
            if perms.get('automobile', False): categories_autorisees.append("Vente Voiture")
            df_compta_factures = df_compta_factures[df_compta_factures['categorie'].isin(categories_autorisees)]
        df_compta_factures = df_compta_factures[(df_compta_factures['date'] >= str(date_debut_fact)) & (df_compta_factures['date'] <= str(date_fin_fact))]
        if filtre_nom_fact:
            df_compta_factures = df_compta_factures[df_compta_factures['description'].str.contains(filtre_nom_fact, case=False, na=False)]
        if df_compta_factures.empty:
            st.info("Aucune facture auto pour cette période")
        else:
            categories = df_compta_factures['categorie'].dropna().unique()
            for cat in categories:
                df_cat = df_compta_factures[df_compta_factures['categorie'] == cat]
                total_cat = df_cat['montant'].sum()
                with st.expander(f"📁 {cat} - Total: {total_cat:,.0f} FC ({len(df_cat)} factures)"):
                    for idx, row in df_cat.iterrows():
                        col_info, col_btn1, col_btn2 = st.columns([4,1,1])
                        client_nom = row.get('description','').split(' - ')[1] if ' - ' in row.get('description','') else 'Client'
                        col_info.markdown(f"**{row['numero_facture']}** | {row['date']} | {client_nom} | **{row['montant']:,.0f} {row.get('devise','FC')}**")
                        if col_btn1.button("📥 PDF", key=f"dl_fact_auto_{row['id']}", width="stretch"):
                            try:
                                details_list = json.loads(row.get('details', '[]')) if row.get('details') else [{"nom": row.get('description',''), "qte": 1, "pu": row['montant']}]
                                pdf_bytes = generer_pdf_facture(row['numero_facture'], row.get('categorie','Vente'), client_nom, details_list, row['montant'], row.get('devise','FC'))
                                st.download_button(label="💾 Télécharger", data=bytes(pdf_bytes), file_name=f"{row['numero_facture']}.pdf", mime="application/pdf", key=f"dl_btn_fact_auto_{row['id']}")
                            except:
                                st.error("Erreur PDF")
                        if col_btn2.button("🖨️ Imprimer", key=f"print_fact_auto_{row['id']}", width="stretch"):
                            try:
                                details_list = json.loads(row.get('details', '[]')) if row.get('details') else [{"nom": row.get('description',''), "qte": 1, "pu": row['montant']}]
                                pdf_bytes = generer_pdf_facture(row['numero_facture'], row.get('categorie','Vente'), client_nom, details_list, row['montant'], row.get('devise','FC'))
                                pdf_b64 = base64.b64encode(pdf_bytes).decode()
                                st.components.v1.html(f"""<script>const pdfData = 'data:application/pdf;base64,{pdf_b64}'; const win = window.open('', '_blank'); win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>'); win.document.close(); setTimeout(() => {{ win.print(); }}, 1000);</script>""", height=0)
                                st.success("Impression lancée")
                            except:
                                st.error("Erreur impression")

# === DEVIS ===
if "📋 Devis" in tab_map:
    with tab_map["📋 Devis"]:
        st.markdown("## 📋 Devis International - ASYMAS CONSULTING")
        peut_industriel = st.session_state.user_role == "PDG" or perms.get('devis_industriel', False)
        peut_batiment = st.session_state.user_role == "PDG" or perms.get('devis_batiment', False)
        if not peut_industriel and not peut_batiment:
            st.error("🔒 Accès non autorisé - Contacte le PDG")
            st.stop()
        if peut_batiment:
            tab_devis_bat, tab_devis_vide = st.tabs(["🧱 Modèle Clôture 23.5m", "📝 Devis Vide"])
        else:
            tab_devis_vide = st.container()
        if peut_batiment:
            with tab_devis_bat:
                st.markdown("### DEVIS DE MATERIAUX POUR LA CONSTRUCTION DE CLOTURE DE 23.5m")
                if 'lignes_cloture' not in st.session_state:
                    st.session_state.lignes_cloture = [
                        {"section": "I", "no": "", "designation": "Installation chantier", "unite": "ff", "qte": 1, "pu": 200, "is_section": False},
                        {"section": "I", "no": "", "designation": "Demolitions", "unite": "ff", "qte": 1, "pu": 70, "is_section": False},
                        {"section": "II", "no": "1", "designation": "moellon", "unite": "Canters", "qte": 9, "pu": 50, "is_section": False},
                        {"section": "II", "no": "2", "designation": "sable", "unite": "Canters", "qte": 4, "pu": 40, "is_section": False},
                        {"section": "II", "no": "3", "designation": "ciment", "unite": "sac", "qte": 23, "pu": 13.5, "is_section": False},
                        {"section": "II", "no": "4", "designation": "gravier", "unite": "Canters", "qte": 3, "pu": 80, "is_section": False},
                        {"section": "II", "no": "5", "designation": "armature de 10", "unite": "pièce", "qte": 9, "pu": 9, "is_section": False},
                        {"section": "II", "no": "6", "designation": "armature de 8", "unite": "pièce", "qte": 4, "pu": 8, "is_section": False},
                        {"section": "II", "no": "7", "designation": "armature de 6", "unite": "pièce", "qte": 12, "pu": 3.5, "is_section": False},
                        {"section": "II", "no": "8", "designation": "Fil à ligature", "unite": "kg", "qte": 16, "pu": 2.5, "is_section": False},
                        {"section": "III", "no": "1", "designation": "bloc ciment", "unite": "pièce", "qte": 987, "pu": 1, "is_section": False},
                        {"section": "III", "no": "2", "designation": "sable", "unite": "Canters", "qte": 5, "pu": 40, "is_section": False},
                        {"section": "III", "no": "3", "designation": "ciment", "unite": "sac", "qte": 15, "pu": 13.5, "is_section": False},
                        {"section": "III", "no": "4", "designation": "gravier", "unite": "Canters", "qte": 0.5, "pu": 70, "is_section": False},
                        {"section": "III", "no": "5", "designation": "Barre Corniche de6", "unite": "pièce", "qte": 8, "pu": 3, "is_section": False},
                        {"section": "III", "no": "6", "designation": "Fil à ligature", "unite": "kg", "qte": 6, "pu": 2, "is_section": False},
                        {"section": "IV", "no": "1", "designation": "socle et longrine", "unite": "pièce", "qte": 8, "pu": 7, "is_section": False},
                        {"section": "IV", "no": "2", "designation": "Colonne", "unite": "pièce", "qte": 18, "pu": 7, "is_section": False},
                        {"section": "IV", "no": "3", "designation": "Corniche", "unite": "pièce", "qte": 6, "pu": 7, "is_section": False},
                        {"section": "IV", "no": "4", "designation": "clous de8", "unite": "kg", "qte": 15, "pu": 2, "is_section": False},
                        {"section": "IV", "no": "5", "designation": "clous de10", "unite": "kg", "qte": 10, "pu": 2, "is_section": False},
                        {"section": "V", "no": "1", "designation": "ciment", "unite": "sac", "qte": 20, "pu": 13.5, "is_section": False},
                        {"section": "V", "no": "2", "designation": "sable", "unite": "Canters", "qte": 7, "pu": 40, "is_section": False},
                    ]

                c1, c2 = st.columns(2)
                client_cloture = c1.text_input("Client", key="client_cloture")
                tel_cloture = c2.text_input("Téléphone", value="+243...", key="tel_cloture")
                localisation_cloture = st.text_input("Localisation", value="Beni, Nord-Kivu", key="loc_cloture")
                parcelle_cloture = st.text_input("N° Parcelle", key="parc_cloture")

                st.markdown("#### Sections : I.Installation | II.Fondation | III.Élévation | IV.Coffrage | V.Finissage")

                if st.button("➕ Ajouter Ligne Matériau", key="add_ligne_cloture"):
                    st.session_state.lignes_cloture.append({"section": "V", "no": "", "designation": "", "unite": "pièce", "qte": 1, "pu": 0, "is_section": False})
                    st.rerun()

                total_mat = 0
                sections = {"I": "Installation chantier", "II": "Fondation", "III": "Élévation de mur et corniche", "IV": "Coffrage Colonne, Corniche et Socle", "V": "Finissage"}

                for section_code, section_nom in sections.items():
                    st.markdown(f"**{section_code}. {section_nom}**")
                    lignes_section = [l for l in st.session_state.lignes_cloture if l['section'] == section_code]
                    sous_total = 0

                    for i, ligne in enumerate(lignes_section):
                        idx_global = st.session_state.lignes_cloture.index(ligne)
                        c1, c2, c3, c4, c5, c6 = st.columns([0.5, 3, 1, 1, 1, 0.5])
                        ligne['no'] = c1.text_input("No", value=ligne['no'], key=f"no_clot_{idx_global}", label_visibility="collapsed")
                        ligne['designation'] = c2.text_input("Désignation", value=ligne['designation'], key=f"des_clot_{idx_global}", label_visibility="collapsed")
                        ligne['unite'] = c3.text_input("Unité", value=ligne['unite'], key=f"unit_clot_{idx_global}", label_visibility="collapsed")
                        ligne['qte'] = c4.number_input("Qté", value=float(ligne['qte']), key=f"qte_clot_{idx_global}", label_visibility="collapsed")
                        ligne['pu'] = c5.number_input("PU", value=float(ligne['pu']), key=f"pu_clot_{idx_global}", label_visibility="collapsed")
                        if c6.button("❌", key=f"del_clot_{idx_global}"):
                            st.session_state.lignes_cloture.pop(idx_global)
                            st.rerun()

                        pt = ligne['qte'] * ligne['pu']
                        sous_total += pt
                        total_mat += pt

                    st.caption(f"Sous-total {section_nom}: {sous_total:,.2f} USD")
                    st.divider()

                main_oeuvre_cloture = st.number_input("💪 Main d'œuvre USD", min_value=0.0, value=1173.0, key="mo_cloture")
                cout_total = total_mat + main_oeuvre_cloture

                col_t1, col_t2, col_t3 = st.columns(3)
                col_t1.metric("TOTAL MATERIAUX", f"{total_mat:,.2f} $")
                col_t2.metric("MAIN D'OEUVRE", f"{main_oeuvre_cloture:,.2f} $")
                col_t3.metric("COUT TOTAL PROJET", f"{cout_total:,.2f} $")

                if st.button("💾 GÉNÉRER DEVIS CLÔTURE PDF", type="primary", width="stretch"):
                    if not client_cloture:
                        st.error("⚠️ Nom du client obligatoire")
                        st.stop()
                    try:
                        numero = f"DEV-CLOT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        
                        details_sections = []
                        for section_code, section_nom in sections.items():
                            items = []
                            for l in st.session_state.lignes_cloture:
                                if l['section'] == section_code and l['designation']:
                                    items.append({"num": l['no'], "designation": l['designation'], "unite": l['unite'], "qte": l['qte'], "pu": l['pu']})
                            if items:
                                details_sections.append({"numero": section_code, "titre": section_nom, "items": items})

                        supabase.table("devis").insert({
                            "numero": numero,
                            "client": client_cloture,
                            "telephone": tel_cloture,
                            "type_devis": "Bâtiment & Génie Civil",
                            "description_longue": f"CONSTRUCTION CLOTURE DE 23.5m\nLocalisation: {localisation_cloture}\nParcelle: {parcelle_cloture}",
                            "montant_global": float(cout_total),
                            "main_oeuvre": float(main_oeuvre_cloture),
                            "devise": "$",
                            "ingenieur": "ESDRAS TSANGYA",
                            "telephone_ingenieur": "+243 972 888 690",
                            "details": json.dumps(st.session_state.lignes_cloture),
                            "utilisateur": st.session_state.user_name,
                            "statut": "Validé",
                            "date": str(date.today())
                        }).execute()

                        pdf_bytes = generer_pdf_devis_consulting(
                            numero, "Bâtiment & Génie Civil", client_cloture,
                            "CONSTRUCTION CLOTURE DE 23.5m", parcelle_cloture, localisation_cloture,
                            details_sections, "$", tel_cloture, main_oeuvre_cloture
                        )

                        st.success(f"✅ Devis {numero} généré - Ing. ESDRAS TSANGYA")
                        st.download_button(
                            label="📥 TÉLÉCHARGER LE PDF",
                            data=bytes(pdf_bytes),
                            file_name=f"{numero}.pdf",
                            mime="application/pdf",
                            width="stretch",
                            type="primary"
                        )

                        pdf_b64 = base64.b64encode(pdf_bytes).decode()
                        st.components.v1.html(f"""
                            <button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">
                                🖨️ IMPRIMER LE DEVIS
                            </button>
                            <script>
                            function printPDF() {{
                                const pdfData = 'data:application/pdf;base64,{pdf_b64}';
                                const win = window.open('', '_blank');
                                win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');
                                win.document.close();
                                setTimeout(() => {{ win.print(); }}, 1000);
                            }}
                            </script>
                        """, height=60)

                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur génération devis")
                        st.code(repr(e))

        with tab_devis_vide:
            if 'devis_pdf_bytes' not in st.session_state:
                st.session_state.devis_pdf_bytes = None
            if 'devis_numero_genere' not in st.session_state:
                st.session_state.devis_numero_genere = None

            with st.expander("➕ Créer Nouveau Devis"):
                if 'lignes_devis' not in st.session_state:
                    st.session_state.lignes_devis = [{"nom": "", "qte": 1, "pu": 0.0}]

                c1, c2 = st.columns(2)
                client = c1.text_input("Client", key="client_devis")
                tel = c2.text_input("Téléphone", value="+243...", key="tel_devis")

                types_dispo = []
                if peut_industriel: types_dispo.append("Industriel")
                if peut_batiment: types_dispo.append("Bâtiment & Génie Civil")

                if len(types_dispo) == 1:
                    type_devis = types_dispo[0]
                    st.info(f"Type autorisé : {type_devis}")
                else:
                    c1, c2 = st.columns(2)
                    type_devis = c1.selectbox("Type Devis", types_dispo, key="type_devis")

                c1, c2 = st.columns(2)
                devise = c1.selectbox("Devise", ["$", "€", "FC"], key="devise_devis")

                titre_projet = st.text_input("Titre du projet", value="CONSTRUCTION MAISON D'HABITATION", key="titre_projet_devis")
                parcelle = st.text_input("N° Parcelle", value="", key="parcelle_devis")
                localisation = st.text_input("Localisation", value="Beni, Nord-Kivu", key="localisation_devis")

                st.markdown("### Détails Matériaux / Prestations")

                col_btn1, col_btn2 = st.columns([3,1])
                if col_btn1.button("➕ Ajouter Ligne", key="add_ligne_devis"):
                    st.session_state.lignes_devis.append({"nom": "", "qte": 1, "pu": 0.0})
                    st.rerun()

                total_matieres = 0
                for i, ligne in enumerate(st.session_state.lignes_devis):
                    c1, c2, c3, c4 = st.columns([4,1,2,1])
                    ligne['nom'] = c1.text_input(f"Designation {i+1}", value=ligne['nom'], key=f"nom_d_{i}")
                    ligne['qte'] = c2.number_input(f"Qté {i+1}", min_value=1, value=ligne['qte'], key=f"qte_d_{i}")
                    ligne['pu'] = c3.number_input(f"PU {i+1}", min_value=0.0, value=ligne['pu'], key=f"pu_d_{i}")
                    if c4.button("❌", key=f"del_ligne_{i}") and len(st.session_state.lignes_devis) > 1:
                        st.session_state.lignes_devis.pop(i)
                        st.rerun()
                    total_matieres += ligne['qte'] * ligne['pu']

                st.divider()

                with st.form("form_devis_final", clear_on_submit=True):
                    description_devis = st.text_area(
                        "📝 Description détaillée du projet",
                        placeholder="Décris les travaux/prestations en détail...\nLigne 1\nLigne 2\nLigne 3\nLigne 4\nLigne 5",
                        height=200,
                        key="desc_devis"
                    )

                    main_oeuvre = st.number_input("💪 Main d'Oeuvre", min_value=0.0, value=0.0)
                    montant_global = total_matieres + main_oeuvre

                    st.metric("💰 COUT GLOBAL", f"{montant_global:,.2f} {devise}")
                    st.info(f"Total matériaux: {total_matieres:,.2f} {devise} + Main d'oeuvre: {main_oeuvre:,.2f} {devise}")

                    if st.form_submit_button("💾 GÉNÉRER DEVIS PDF", type="primary"):
                        if not client:
                            st.error("⚠️ Nom du client obligatoire")
                            st.stop()
                        if not description_devis or len(description_devis.strip().split('\n')) < 2:
                            st.error("⚠️ La description doit avoir minimum 2 lignes")
                            st.stop()
                        try:
                            numero = f"DEV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            ingenieur = "SAMY TSANGYA" if type_devis == "Industriel" else "ESDRAS TSANGYA"
                            tel_ing = "+243 995 105 623" if type_devis == "Industriel" else "+243 972 888 690"

                            details_sections = [{
                                "numero": "I",
                                "titre": "TRAVAUX / MATERIAUX",
                                "items": [{"num": f"{i+1}", "designation": l['nom'], "unite": "U", "qte": l['qte'], "pu": l['pu']} for i, l in enumerate(st.session_state.lignes_devis) if l['nom']]
                            }]

                            supabase.table("devis").insert({
                                "numero": numero,
                                "client": client,
                                "telephone": tel,
                                "type_devis": type_devis,
                                "description_longue": description_devis,
                                "montant_global": float(montant_global),
                                "main_oeuvre": float(main_oeuvre),
                                "devise": devise,
                                "ingenieur": ingenieur,
                                "telephone_ingenieur": tel_ing,
                                "details": json.dumps(st.session_state.lignes_devis),
                                "utilisateur": st.session_state.user_name,
                                "statut": "Validé",
                                "date": str(date.today())
                            }).execute()

                            pdf_bytes = generer_pdf_devis_consulting(numero, type_devis, client, titre_projet, parcelle, localisation, details_sections, devise, tel, main_oeuvre)

                            st.session_state.devis_pdf_bytes = pdf_bytes
                            st.session_state.devis_numero_genere = numero
                            st.session_state.devis_ingenieur = ingenieur

                            st.session_state.lignes_devis = [{"nom": "", "qte": 1, "pu": 0.0}]
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur création devis")
                            st.code(repr(e))

            if st.session_state.devis_pdf_bytes and st.session_state.devis_numero_genere:
                st.success(f"✅ Devis {st.session_state.devis_numero_genere} généré - Signé par Ing. {st.session_state.devis_ingenieur}")

                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        label="📥 TÉLÉCHARGER LE PDF",
                        data=st.session_state.devis_pdf_bytes,
                        file_name=f"{st.session_state.devis_numero_genere}.pdf",
                        mime="application/pdf",
                        width="stretch",
                        type="primary"
                    )
                with col_dl2:
                    pdf_b64 = base64.b64encode(st.session_state.devis_pdf_bytes).decode()
                    st.components.v1.html(f"""
                        <button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer;">
                            🖨️ IMPRIMER LE DEVIS
                        </button>
                        <script>
                        function printPDF() {{
                            const pdfData = 'data:application/pdf;base64,{pdf_b64}';
                            const win = window.open('', '_blank');
                            win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');
                            win.document.close();
                            setTimeout(() => {{ win.print(); }}, 1000);
                        }}
                        </script>
                    """, height=50)

                if st.button("🆕 NOUVEAU DEVIS", width="stretch"):
                    st.session_state.devis_pdf_bytes = None
                    st.session_state.devis_numero_genere = None
                    st.rerun()

        st.divider()
        st.subheader("📋 Liste des Devis")
        if df_devis.empty:
            st.info("Aucun devis")
        else:
            df_devis_filtre = df_devis.copy()
            if st.session_state.user_role!= "PDG":
                types_autorises = []
                if peut_industriel: types_autorises.append("Industriel")
                if peut_batiment: types_autorises.append("Bâtiment & Génie Civil")
                df_devis_filtre = df_devis_filtre[df_devis_filtre['type_devis'].isin(types_autorises)]
                st.caption(f"🔒 Filtrage actif : Tu vois uniquement les devis {', '.join(types_autorises)}")

            if df_devis_filtre.empty:
                st.warning("Aucun devis pour ta partie")
            else:
                for _, row in df_devis_filtre.iterrows():
                    with st.expander(f"{row['numero']} - {row['client']} - {row['type_devis']} - {row.get('montant_global',0):,.2f} {row.get('devise','$')}"):
                        st.write(f"**Client:** {row['client']} | **Tel:** {row.get('telephone','')}")
                        st.write(f"**Ingénieur:** {row.get('ingenieur','')} | **Tel:** {row.get('telephone_ingenieur','')}")
                        st.write(f"**Main d'oeuvre:** {row.get('main_oeuvre',0):,.2f} {row.get('devise','$')}")
                        st.write(f"**Statut:** {row.get('statut','')} | **Créé par:** {row.get('utilisateur','')}")

                        if row.get('description_longue'):
                            st.text_area("Description", value=row.get('description_longue',''), height=150, disabled=True, key=f"desc_view_{row['id']}")

                        c1, c2, c3 = st.columns(3)
                        if c1.button("📄 Télécharger PDF", key=f"dl_devis_{row['id']}", width="stretch"):
                            details = json.loads(row.get('details', '[]'))
                            details_sections = [{
                                "numero": "I",
                                "titre": "TRAVAUX / MATERIAUX",
                                "items": [{"num": f"{i+1}", "designation": d['nom'], "unite": "U", "qte": d['qte'], "pu": d['pu']} for i, d in enumerate(details)]
                            }]
                            pdf_bytes = generer_pdf_devis_consulting(
                                row['numero'], row['type_devis'], row['client'],
                                row.get('description_longue','').split('\n')[0] if row.get('description_longue') else "PROJET",
                                "", "", details_sections,
                                row.get('devise','$'), row.get('telephone',''), row.get('main_oeuvre',0)
                            )
                            st.download_button(
                                label="📥 Download",
                                data=bytes(pdf_bytes),
                                file_name=f"{row['numero']}.pdf",
                                mime="application/pdf",
                                key=f"dl_btn_{row['id']}"
                            )

                        if st.session_state.user_role == "PDG":
                            if c3.button("🗑️ Supprimer", key=f"del_devis_{row['id']}", width="stretch"):
                                supabase.table("devis").delete().eq("id", int(row['id'])).execute()
                                st.success("Devis supprimé")
                                st.cache_data.clear()
                                st.rerun()

if "👥 Utilisateurs" in tab_map:
    with tab_map["👥 Utilisateurs"]:
        st.markdown("## 👥 Gestion des Utilisateurs")
        with st.expander("➕ Ajouter Utilisateur"):
            with st.form("form_user", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nom_user = c1.text_input("Nom")
                role_user = c2.selectbox("Rôle", ["PDG", "GERANTE", "UTILISATEUR", "COMMERCANT"])
                pwd_user = c3.text_input("Mot de passe", type="password")

                st.markdown("**Permissions :**")
                col1, col2, col3, col4 = st.columns(4)
                perms_dict = {}
                perms_dict['dashboard'] = col1.checkbox("Dashboard", value=True)
                perms_dict['commerce'] = col2.checkbox("Commerce", value=True)
                perms_dict['stock'] = col3.checkbox("Stock")
                perms_dict['immobilier'] = col4.checkbox("Immobilier")
                perms_dict['automobile'] = col1.checkbox("Automobile")
                perms_dict['parc'] = col2.checkbox("Parc Auto")
                perms_dict['comptabilite'] = col3.checkbox("Comptabilité")
                perms_dict['factures'] = col4.checkbox("Factures")
                perms_dict['devis_industriel'] = col1.checkbox("Devis Industriel")
                perms_dict['devis_batiment'] = col2.checkbox("Devis Bâtiment")
                perms_dict['users'] = col3.checkbox("Gestion Users")
                perms_dict['supprimer'] = col4.checkbox("Supprimer données")

                if st.form_submit_button("💾 Ajouter Utilisateur"):
                    try:
                        supabase.table("utilisateurs").insert({
                            "nom": nom_user,
                            "role": role_user,
                            "password": pwd_user,
                            "permissions": perms_dict,
                            "categories_autorisees": []
                        }).execute()
                        st.success(f"Utilisateur {nom_user} ajouté")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout utilisateur")
                        st.code(repr(e))

        st.divider()
        st.subheader("📋 Liste des Utilisateurs")
        if df_utilisateurs.empty:
            st.info("Aucun utilisateur")
        else:
            for _, row in df_utilisateurs.iterrows():
                with st.expander(f"{row['nom']} - {row['role']}"):
                    st.json(row.get('permissions', {}))
                    if st.session_state.user_role == "PDG" and row['nom']!= st.session_state.user_name:
                        if st.button("🗑️ Supprimer", key=f"del_user_{row['id']}"):
                            supabase.table("utilisateurs").delete().eq("id", int(row['id'])).execute()
                            st.success("Utilisateur supprimé")
                            st.cache_data.clear()
                            st.rerun()
