import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date, datetime, timedelta
from fpdf import FPDF
import base64
import io
import qrcode
from PIL import Image
import tempfile
import os
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

# === CONFIG SUPABASE ===
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="ASYMAS BUSINESS", layout="wide", page_icon="💎")

# === CACHE TOUT STREAMLIT SAUF POUR LE PDG ===
st.markdown("""
    <style>
    #MainMenu {visibility: hidden!important;}
    header {visibility: hidden!important;}
  .stAppToolbar {display: none!important;}
    [data-testid="stToolbar"] {display: none!important;}
    [data-testid="stDecoration"] {display: none!important;}
    [data-testid="stHeader"] {display: none!important;}
    footer {visibility: hidden!important;}
  .stDeployButton {display:none!important;}
    [data-testid="stStatusWidget"] {display: none!important;}
    [data-testid="manage-app-button"] {display: none!important;}
    iframe[src*="streamlit.io"] {display: none!important;}
    button[kind="header"] {display: none!important;}
    div[data-testid="stBottomBlockContainer"] {display: none!important;}
  .st-emotion-cache-1wbqy5l {display: none!important;}
    button[title="Manage app"] {display: none!important;}
    a[href*="share.streamlit.io"] {display: none!important;}
    </style>
""", unsafe_allow_html=True)

# === SYSTÈME DE MOTS DE PASSE PERSISTANT DANS SUPABASE ===
@st.cache_data(ttl=10)
def load_passwords():
    try:
        data = supabase.table("utilisateurs").select("nom,role,password").execute()
        passwords = {}
        for user in data.data:
            passwords[user['role']] = user['password']
        return passwords
    except:
        return {
            "PDG": "tsang2024",
            "GERANTE": "asiya2024",
            "UTILISATEUR": "basam2024"
        }

passwords_db = load_passwords()

if 'user_role' not in st.session_state:
    st.session_state.user_role = None
    st.session_state.user_name = None

if st.session_state.user_role is None:
    st.markdown("# 🔐 ASYMAS BUSINESS - CONNEXION")

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("### Choisissez votre profil :")
        profil = st.selectbox("Utilisateur", ["-- Sélectionner --", "PDG TSANG", "Gérante ASIYA", "BASAM"])
        password = st.text_input("Mot de passe", type="password", key="pwd")

        if st.button("SE CONNECTER", width="stretch", type="primary"):
            if profil == "PDG TSANG" and password == passwords_db["PDG"]:
                st.session_state.user_role = "PDG"
                st.session_state.user_name = "TSANG"
                st.rerun()
            elif profil == "Gérante ASIYA" and password == passwords_db["GERANTE"]:
                st.session_state.user_role = "GERANTE"
                st.session_state.user_name = "ASIYA"
                st.rerun()
            elif profil == "BASAM" and password == passwords_db["UTILISATEUR"]:
                st.session_state.user_role = "UTILISATEUR"
                st.session_state.user_name = "BASAM"
                st.rerun()
            else:
                st.error("Profil ou mot de passe incorrect")
    st.stop()

# === CSS FOND BLANC SIMPLE SANS REFLETS ===
st.markdown("""
<style>
h1, h2, h3 {
    color: #00ff41!important;
    font-size: 2.2rem!important;
    font-weight: 900!important;
    padding: 10px 0!important;
    border-bottom: 3px solid #00ff41!important;
    margin-bottom: 20px!important;
}
div[data-testid="stMetricValue"] {color: #00ff41!important;}
.stButton>button {background-color: #00ff41!important; color: black!important; font-weight: bold; border: none;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_table(table_name):
    try:
        with st.spinner(f"Chargement {table_name}..."):
            data = supabase.table(table_name).select("*").order("id", desc=True).execute()
        return pd.DataFrame(data.data)
    except Exception as e:
        st.error(f"Erreur chargement {table_name}")
        st.code(repr(e))
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_table_columns(table_name):
    try:
        test = supabase.table(table_name).select("*").limit(1).execute()
        if test.data:
            return list(test.data[0].keys())
        return []
    except:
        return []

# === GÉNÉRER QR CODE - VERSION CORRIGÉE AVEC FICHIER TEMP ===
def generer_qrcode(data_text):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=1,
    )
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name)
    return temp_file.name

# === GÉNÉRATEUR PDF FACTURE - BENI RDC AVEC QR EN BAS + SIGNATURE ===
def generer_pdf_facture(numero, type_op, client, details_list, montant, devise, tel_client="+243...", periode=""):
    def clean_text(txt):
        return str(txt).encode('latin-1', 'replace').decode('latin-1')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_fill_color(20, 50, 40)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 20)
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, "ASYMAS BUSINESS", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(10, 16)
    pdf.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
    pdf.set_xy(10, 21)
    pdf.cell(0, 5, "Email: asamnesstsang636@gmail.com", ln=True)

    pdf.set_font("Arial", "B", 10)
    pdf.set_xy(150, 8)
    pdf.cell(50, 6, "FACTURE N°", ln=True, align="R")
    pdf.set_font("Arial", "", 10)
    pdf.set_xy(150, 14)
    pdf.cell(50, 6, clean_text(numero), ln=True, align="R")
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(150, 20)
    pdf.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")

    pdf.ln(15)

    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"FACTURE {clean_text(type_op.upper())}", ln=True, fill=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 10)
    pdf.set_draw_color(0, 0, 0)
    pdf.cell(90, 7, "FACTURE A:", 1, 0, 'L')
    pdf.cell(10, 7, "", 0, 0)
    pdf.cell(90, 7, "DETAILS PAIEMENT:", 1, 1, 'L')

    pdf.set_font("Arial", "", 9)
    pdf.cell(90, 6, f"Client: {clean_text(client)}", 'LR', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(90, 6, "M-Pesa: +243817264448", 'LR', 1, 'L')

    pdf.cell(90, 6, f"Tel: {clean_text(tel_client)}", 'LR', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(90, 6, "Echeance: Immediate", 'LR', 1, 'L')

    pdf.cell(90, 6, f"Date emission: {date.today().strftime('%d/%m/%Y')}", 'LRB', 0, 'L')
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(90, 6, "", 'LRB', 1, 'L')

    pdf.ln(8)

    pdf.set_fill_color(0, 102, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(120, 8, "DESIGNATION", 1, 0, 'C', True)
    pdf.cell(30, 8, "QTE", 1, 0, 'C', True)
    pdf.cell(40, 8, f"MONTANT ({clean_text(devise)})", 1, 1, 'C', True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)

    if isinstance(details_list, list) and details_list:
        for item in details_list:
            nom = clean_text(item.get('nom', ''))
            qte = item.get('qte', 1)
            montant_item = item.get('prix', 0) * qte
            pdf.cell(120, 7, nom, 1, 0, 'L')
            pdf.cell(30, 7, str(qte), 1, 0, 'C')
            pdf.cell(40, 7, f"{montant_item:,.0f}", 1, 1, 'R')
    else:
        pdf.cell(120, 7, clean_text(details_list), 1, 0, 'L')
        pdf.cell(30, 7, "1", 1, 0, 'C')
        pdf.cell(40, 7, f"{montant:,.0f}", 1, 1, 'R')

    if periode:
        pdf.cell(120, 7, f"Periode: {clean_text(periode)}", 1, 0, 'L')
        pdf.cell(30, 7, "", 1, 0, 'C')
        pdf.cell(40, 7, "", 1, 1, 'R')

    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(150, 10, "MONTANT TOTAL A PAYER", 1, 0, 'R', True)
    pdf.cell(40, 10, f"{montant:,.0f} {clean_text(devise)}", 1, 1, 'R', True)

    pdf.ln(10)

    if type_op in ["Loyer", "Vente Auto"]:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, "SIGNATURE CLIENT:", ln=True)
        pdf.ln(3)
        pdf.set_draw_color(0, 0, 0)
        pdf.line(10, pdf.get_y(), 100, pdf.get_y())
        pdf.set_font("Arial", "", 8)
        pdf.set_xy(10, pdf.get_y() + 1)
        pdf.cell(90, 5, f"Nom: {clean_text(client)}", ln=True)
        pdf.set_xy(10, pdf.get_y())
        pdf.cell(90, 5, "Date: ___________________", ln=True)
        pdf.ln(5)

    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(0, 102, 0)
    pdf.cell(0, 6, "Merci pour votre confiance! ASYMAS BUSINESS - Votre partenaire de croissance", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    qr_data = f"""ASYMAS BUSINESS
Facture: {numero}
Type: {type_op}
Client: {client}
Montant: {montant:,.0f} {devise}
Date: {date.today().strftime('%d/%m/%Y')}
Tel: +243 995 105 623"""
    qr_path = generer_qrcode(qr_data)

    y_position = pdf.get_y()
    if y_position > 250:
        pdf.add_page()
        y_position = 30

    pdf.image(qr_path, x=160, y=y_position, w=30)
    os.unlink(qr_path)

    pdf.set_xy(10, y_position + 5)
    pdf.set_font("Arial", "", 8)
    pdf.cell(140, 5, "Scannez ce QR Code pour verifier l'authenticite de la facture", ln=False)
    pdf.set_xy(10, y_position + 10)
    pdf.cell(140, 5, "ASYMAS BUSINESS - Beni, Nord-Kivu, RDC", ln=False)

    return pdf.output(dest='S').encode('latin-1')

def creer_facture_auto(type_op, client, details, montant, devise="FC", details_list=None, tel="+243...", periode=""):
    numero_facture = f"AS-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    if details_list is None:
        details_list = [{"nom": details, "qte": 1, "prix": montant}]

    pdf_bytes = generer_pdf_facture(numero_facture, type_op, client, details_list, montant, devise, tel, periode)

    try:
        colonnes_compta = get_table_columns("comptabilite")
        data_compta = {
            "type": "Revenu",
            "description": str(f"{type_op} - {client} - {details}"),
            "montant": float(montant),
            "date": str(date.today())
        }
        if "categorie" in colonnes_compta:
            data_compta["categorie"] = str(type_op)
        if "devise" in colonnes_compta:
            data_compta["devise"] = str(devise)

        supabase.table("comptabilite").insert(data_compta).execute()
        st.toast(f"✅ Enregistré compta", icon="✅")
    except Exception as e:
        st.error("❌ ERREUR INSERTION COMPTA")
        st.code(repr(e))

    try:
        data_facture = {
            "numero_facture": str(numero_facture),
            "type_operation": str(type_op),
            "nom_client": str(client),
            "details": str(details),
            "montant": float(montant),
            "devise": str(devise),
            "date": str(date.today())
        }
        supabase.table("factures_proforma").insert(data_facture).execute()
        st.toast(f"✅ Enregistré factures", icon="✅")
    except Exception as e:
        st.warning("Table factures_proforma non trouvée - Crée-la dans Supabase")

    return numero_facture, pdf_bytes

# === FONCTION EXCEL PRO ===
def generer_excel_pro(df_data, titre="Relevé Comptable", total_revenu=0, total_depense=0, solde=0):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_data.to_excel(writer, sheet_name='Releve', index=False, startrow=6)

        workbook = writer.book
        worksheet = writer.sheets['Releve']

        worksheet.merge_cells('A1:F1')
        worksheet['A1'] = 'ASYMAS BUSINESS'
        worksheet['A1'].font = Font(size=20, bold=True, color='006600')
        worksheet['A1'].alignment = Alignment(horizontal='center')

        worksheet.merge_cells('A2:F2')
        worksheet['A2'] = 'Beni, Nord-Kivu, RDC | Tel: +243 995 105 623 | asamnesstsang636@gmail.com'
        worksheet['A2'].font = Font(size=10, italic=True)
        worksheet['A2'].alignment = Alignment(horizontal='center')

        worksheet.merge_cells('A3:F3')
        worksheet['A3'] = f'{titre.upper()} - Edité le {date.today().strftime("%d/%m/%Y")}'
        worksheet['A3'].font = Font(size=14, bold=True, color='FF6600')
        worksheet['A3'].alignment = Alignment(horizontal='center')

        worksheet.merge_cells('A4:F4')
        worksheet['A4'] = f'Total Revenus: {total_revenu:,.0f} FC | Total Dépenses: {total_depense:,.0f} FC | Solde: {solde:,.0f} FC'
        worksheet['A4'].font = Font(size=11, bold=True)
        worksheet['A4'].alignment = Alignment(horizontal='center')
        worksheet['A4'].fill = PatternFill(start_color='FFCC00', end_color='FFCC00', fill_type='solid')

        header_fill = PatternFill(start_color='006600', end_color='006600', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')
        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                            top=Side(style='thin'), bottom=Side(style='thin'))

        for col in range(1, len(df_data.columns) + 1):
            cell = worksheet.cell(row=7, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border

        for row in range(7, len(df_data) + 8):
            for col in range(1, len(df_data.columns) + 1):
                worksheet.cell(row=row, column=col).border = thin_border
                worksheet.cell(row=row, column=col).alignment = Alignment(horizontal='left')

        for col in range(1, len(df_data.columns) + 1):
            worksheet.column_dimensions[get_column_letter(col)].width = 18

    return output.getvalue()

df_biens = load_table("biens")
df_articles = load_table("articles")
df_voitures = load_table("voitures")
df_compta = load_table("comptabilite")
df_factures = load_table("factures_proforma")
df_utilisateurs = load_table("utilisateurs")

# === FIX KEYERROR MONTANT ===
if 'montant' not in df_compta.columns:
    df_compta['montant'] = 0
if 'type' not in df_compta.columns:
    df_compta['type'] = 'Inconnu'

st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
st.markdown("### Agriculture • Commerce • Immobilier • Automobile • Beni RDC")

with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.user_name}")
    st.markdown(f"**Rôle : {st.session_state.user_role}**")
    st.info("ASYMAS BUSINESS v1.0")

    if st.button("🔄 Actualiser", key="btn_save"):
        st.cache_data.clear()
        st.rerun()
    if st.button("🚪 DÉCONNEXION", key="logout", width="stretch"):
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.rerun()

if st.session_state.user_role == "UTILISATEUR":
    tab2, = st.tabs(["🛍️ Commerce"])
    tab1 = tab3 = tab4 = tab5 = tab6 = tab7 = tab8 = tab9 = None
elif st.session_state.user_role == "PDG":
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Dashboard", "🛍️ Commerce", "📦 Gestion Stock", "🏠 Immobilier", "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures", "👥 Utilisateurs"
    ])
else:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📊 Dashboard", "🛍️ Commerce", "📦 Gestion Stock", "🏠 Immobilier", "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures"
    ])
    tab9 = None

if tab1 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab1:
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

with tab2:
    st.markdown("## 🛍️ Commerce - Point de Vente")

    if 'panier_commerce' not in st.session_state:
        st.session_state.panier_commerce = []
    if 'vente_finie' not in st.session_state:
        st.session_state.vente_finie = False
    if 'pdf_data' not in st.session_state:
        st.session_state.pdf_data = None
    if 'num_fact' not in st.session_state:
        st.session_state.num_fact = None

    if df_articles.empty:
        st.error("Aucun article disponible - Ajoute des articles dans Gestion Stock")
    else:
        col_gauche, col_droite = st.columns([2,1])

        with col_gauche:
            st.subheader("👤 Client")
            nom_client = st.text_input("Nom Client", key="nom_client_c")
            tel_client = st.text_input("Téléphone Client", value="+243...", key="tel_client_c")

            st.subheader("📦 Rubrique Produit")
            recherche = st.text_input("🔍 Chercher un produit", placeholder="Tape le nom...", key="search_c")

            df_articles_filtre = df_articles.copy()
            if recherche:
                mask = df_articles['nom_article'].str.contains(recherche, case=False, na=False)
                df_articles_filtre = df_articles # <-- BUG FIXÉ: ÉTAIT df_articles_filtre = df_articles

            if not df_articles_filtre.empty:
                options = [f"{row['nom_article']} - {row.get('prix_vente',0):,.0f} FC - Stock:{row.get('stock','?')}" for _, row in df_articles_filtre.iterrows()]
                choix = st.selectbox("Choisir le produit", options, key="choix_prod_c")
                idx_choisi = options.index(choix)
                produit_choisi = df_articles_filtre.iloc[idx_choisi]

                c1, c2, c3 = st.columns([1,1,1])
                qte = c1.number_input("QTE", min_value=1, value=1, key="qte_c")
                c2.markdown(f"### Prix: **{produit_choisi.get('prix_vente',0):,.0f} FC**")

                if c3.button("➕ Ajouter au Panier", width="stretch", key="add_panier_c"):
                    stock_dispo = int(produit_choisi.get('stock', 0))
                    if stock_dispo < qte:
                        st.error(f"Stock insuffisant! Disponible: {stock_dispo}")
                        st.stop()
                    st.session_state.panier_commerce.append({
                        "id": int(produit_choisi['id']),
                        "nom": str(produit_choisi['nom_article']),
                        "prix": float(produit_choisi.get('prix_vente',0)),
                        "qte": int(qte),
                        "stock_dispo": stock_dispo
                    })
                    st.session_state.vente_finie = False
                    st.rerun()
            else:
                st.info("Aucun produit trouvé")

        with col_droite:
            st.subheader("🛒 Panier")
            total = 0

            if st.session_state.vente_finie and st.session_state.pdf_data:
                st.success(f"✅ Vente validée - {st.session_state.total_vente:,.0f} FC")
                st.info(f"📄 Facture: {st.session_state.num_fact}")
                st.download_button(
                    label="📥 Télécharger Facture PDF",
                    data=st.session_state.pdf_data,
                    file_name=f"{st.session_state.num_fact}.pdf",
                    mime="application/pdf",
                    width="stretch",
                    key="dl_facture_commerce"
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
                if st.button("Nouvelle Vente", width="stretch", key="new_vente_c"):
                    st.session_state.panier_commerce = []
                    st.session_state.vente_finie = False
                    st.session_state.pdf_data = None
                    st.session_state.num_fact = None
                    st.rerun()
            elif not st.session_state.panier_commerce:
                st.info("Panier vide")
            else:
                for i, item in enumerate(st.session_state.panier_commerce):
                    with st.container(border=True):
                        st.markdown(f"**{item['nom']}**")
                        c1, c2 = st.columns([2,1])
                        new_qte = c1.number_input("QTE", min_value=1, value=item['qte'], key=f"qte_panier_c_{i}")
                        if new_qte > item.get('stock_dispo', 999):
                            st.error(f"Stock max: {item.get('stock_dispo', 999)}")
                            new_qte = item['qte']
                        st.session_state.panier_commerce[i]['qte'] = new_qte
                        sous_total = float(item['prix']) * int(st.session_state.panier_commerce[i]['qte'])
                        c2.markdown(f"**{sous_total:,.0f} FC**")
                        if st.button("❌ Supprimer", key=f"del_c_{i}"):
                            st.session_state.panier_commerce.pop(i)
                            st.rerun()
                        total += sous_total

                st.divider()
                st.markdown(f"### Total : **{total:,.0f} FC**")

                if st.button("💳 Finaliser Vente", type="primary", width="stretch", key="final_c"):
                    try:
                        if not nom_client or not st.session_state.panier_commerce:
                            st.warning("Nom client + panier requis")
                            st.stop()

                        with st.spinner("Enregistrement..."):
                            vente_result = supabase.table("ventes").insert({
                                "total": float(total),
                                "id_utilisateur": 1 if st.session_state.user_name == "TSANG" else 2 if st.session_state.user_name == "ASIYA" else 3,
                                "nom_client": str(nom_client),
                                "telephone_client": str(tel_client)
                            }).execute()

                            id_vente = vente_result.data[0]['id']

                            for i in st.session_state.panier_commerce:
                                supabase.table("ventes_details").insert({
                                    "id_vente": id_vente,
                                    "id_article": int(i['id']),
                                    "quantite": int(i['qte']),
                                    "prix_unitaire": float(i['prix']),
                                    "sous_total": float(i['prix']) * int(i['qte'])
                                }).execute()
                                supabase.table("articles").update({"stock": i['stock_dispo'] - i['qte']}).eq("id", i['id']).execute()

                            details_list = [{"nom": i['nom'], "qte": i['qte'], "prix": i['prix']} for i in st.session_state.panier_commerce]
                            details_text = ", ".join([f"{i['nom']} x{i['qte']}" for i in st.session_state.panier_commerce])
                            num_fact, pdf_bytes = creer_facture_auto("Vente Commerce", nom_client, details_text, total, "FC", details_list, tel_client)

                            st.session_state.vente_finie = True
                            st.session_state.pdf_data = pdf_bytes
                            st.session_state.num_fact = num_fact
                            st.session_state.total_vente = total
                            st.session_state.panier_commerce = []
                            st.cache_data.clear()
                            st.rerun()

                    except Exception as e:
                        st.error(f"ERREUR SUPABASE : {e}")
                        st.code(str(e))

if tab3 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab3:
        st.markdown("## 📦 Gestion Stock - Articles")
        with st.expander("➕ Ajouter Nouvel Article"):
            with st.form("form_article", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nom = c1.text_input("Nom Article")
                cat = c2.text_input("Catégorie")
                prix_achat = c3.number_input("Prix Achat FC", min_value=0.0)
                prix_vente = c1.number_input("Prix Vente FC", min_value=0.0)
                stock = c2.number_input("Stock", min_value=0)

                if st.form_submit_button("💾 Ajouter Article"):
                    try:
                        supabase.table("articles").insert({
                            "nom_article": str(nom), "categorie": str(cat),
                            "prix_achat": float(prix_achat), "prix_vente": float(prix_vente), "stock": int(stock)
                        }).execute()
                        st.success("Article ajouté")
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
                    c1, c2 = st.columns(2)
                    with c1:
                        new_nom = st.text_input("Nom", value=row['nom_article'], key=f"nom_{row['id']}")
                        new_cat = st.text_input("Catégorie", value=row.get('categorie',''), key=f"cat_{row['id']}")
                        new_prix_a = st.number_input("Prix Achat", value=float(row.get('prix_achat',0)), key=f"pa_{row['id']}")
                    with c2:
                        new_prix_v = st.number_input("Prix Vente", value=float(row.get('prix_vente',0)), key=f"pv_{row['id']}")
                        new_stock = st.number_input("Stock", value=int(row.get('stock',0)), key=f"stock_{row['id']}")

                    c1, c2 = st.columns(2)
                    if c1.button("✏️ Modifier", key=f"mod_art_{row['id']}", width="stretch"):
                        try:
                            supabase.table("articles").update({
                                "nom_article": str(new_nom), "categorie": str(new_cat),
                                "prix_achat": float(new_prix_a), "prix_vente": float(new_prix_v), "stock": int(new_stock)
                            }).eq("id", int(row['id'])).execute()
                            st.success("Modifié")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur modif")
                            st.code(repr(e))

                    if st.session_state.user_role == "PDG":
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
                        c2.info("🔒 Suppression réservée au PDG")

if tab4 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab4:
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
                details_list = [
                    {"nom": f"Loyer {type_bien} | Adresse: {adresse} | Durée: {duree_contrat}", "qte": 1, "prix": prix},
                    {"nom": f"Electricite | {type_bien} - {adresse}", "qte": 1, "prix": electricite},
                    {"nom": f"Eau | {type_bien} - {adresse}", "qte": 1, "prix": eau}
                ]
                details_text = f"LOUER: {type_bien} | Adresse: {adresse} | Durée Contrat: {duree_contrat} | Loyer: {prix} $ | Electricité: {electricite} $ | Eau: {eau} $"
                periode = date.today().strftime("%B %Y")
                num_fact, pdf_bytes = creer_facture_auto("Loyer", nom_client, details_text, total_mensuel, "$", details_list, tel_client, periode)
                st.success(f"✅ Facture générée : {num_fact}")
                st.download_button(
                    label="📥 TÉLÉCHARGER LE PDF MAINTENANT",
                    data=pdf_bytes,
                    file_name=f"{num_fact}.pdf",
                    mime="application/pdf",
                    width="stretch",
                    key="dl_facture_immo"
                )
                pdf_b64 = base64.b64encode(pdf_bytes).decode()
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
                st.cache_data.clear()
            else:
                st.error("Nom client + Adresse obligatoires")

if tab5 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab5:
        st.markdown("## 🚗 Automobile - Point de Vente")

        if 'panier_voiture' not in st.session_state:
            st.session_state.panier_voiture = []
        if 'vente_auto_finie' not in st.session_state:
            st.session_state.vente_auto_finie = False
        if 'pdf_auto' not in st.session_state:
            st.session_state.pdf_auto = None
        if 'num_fact_auto' not in st.session_state:
            st.session_state.num_fact_auto = None

        if df_voitures.empty:
            st.error("Aucune voiture disponible - Ajoute des voitures dans Gestion Parc")
        else:
            col_gauche, col_droite = st.columns([2,1])

            with col_gauche:
                st.subheader("👤 Client")
                nom_client = st.text_input("Nom Client", key="nom_client_v")
                tel_client = st.text_input("Téléphone Client", value="+243...", key="tel_client_v")

                st.subheader("🚗 Rubrique Véhicule")
                recherche_voiture = st.text_input("🔍 Chercher une voiture", placeholder="Marque, modèle, plaque...", key="search_v")

                df_voitures_filtre = df_voitures.copy()
                if recherche_voiture:
                    mask = (df_voitures['marque'].str.contains(recherche_voiture, case=False, na=False) |
                            df_voitures['modele'].str.contains(recherche_voiture, case=False, na=False) |
                            df_voitures.get('plaque', pd.Series(dtype=str)).str.contains(recherche_voiture, case=False, na=False))
                    df_voitures_filtre = df_voitures # <-- BUG FIXÉ ICI

                if not df_voitures_filtre.empty:
                    options = []
                    for _, row in df_voitures_filtre.iterrows():
                        details = f"{row['marque']} {row['modele']} - {row.get('annee','')} - {row.get('plaque','')} - {row.get('prix',0):,.0f} $ - {row.get('statut','')}"
                        options.append(details)

                    choix = st.selectbox("Choisir le véhicule", options, key="choix_veh_v")
                    idx_choisi = options.index(choix)
                    voiture_choisie = df_voitures_filtre.iloc[idx_choisi]

                    with st.container(border=True):
                        st.markdown(f"### {voiture_choisie['marque']} {voiture_choisie['modele']}")
                        c1, c2, c3 = st.columns(3)
                        c1.markdown(f"**Année:** {voiture_choisie.get('annee','N/A')}")
                        c1.markdown(f"**Plaque:** {voiture_choisie.get('plaque','N/A')}")
                        c2.markdown(f"**Couleur:** {voiture_choisie.get('couleur','N/A')}")
                        km_val = voiture_choisie.get('kilometrage')
                        km_display = f"{int(km_val):,}" if km_val and str(km_val).isdigit() else 'N/A'
                        c2.markdown(f"**KM:** {km_display}")
                        c3.markdown(f"**Carburant:** {voiture_choisie.get('carburant','N/A')}")
                        c3.markdown(f"**Boîte:** {voiture_choisie.get('boite','N/A')}")
                        st.markdown(f"**Statut:** {voiture_choisie.get('statut','N/A')}")
                        st.markdown(f"### Prix: **{voiture_choisie.get('prix',0):,.0f} $**")

                    c1, c2 = st.columns([1,1])
                    qte = c1.number_input("QTE", min_value=1, value=1, key="qte_v")

                    if c2.button("➕ Ajouter au Panier", width="stretch", key="add_panier_v"):
                        if voiture_choisie.get('statut') == 'Vendue':
                            st.error("Cette voiture est déjà vendue!")
                            st.stop()
                        st.session_state.panier_voiture.append({
                            "id": int(voiture_choisie['id']),
                            "marque": str(voiture_choisie['marque']),
                            "modele": str(voiture_choisie['modele']),
                            "annee": str(voiture_choisie.get('annee','')),
                            "plaque": str(voiture_choisie.get('plaque','')),
                            "couleur": str(voiture_choisie.get('couleur','')),
                            "kilometrage": str(voiture_choisie.get('kilometrage','')),
                            "carburant": str(voiture_choisie.get('carburant','')),
                            "boite": str(voiture_choisie.get('boite','')),
                            "statut": str(voiture_choisie.get('statut','')),
                            "prix": float(voiture_choisie.get('prix',0)),
                            "qte": int(qte)
                        })
                        st.session_state.vente_auto_finie = False
                        st.rerun()
                else:
                    st.info("Aucune voiture trouvée")

            with col_droite:
                st.subheader("🛒 Panier")
                total = 0

                if st.session_state.vente_auto_finie and st.session_state.pdf_auto:
                    st.success(f"✅ Vente validée - {st.session_state.total_auto:,.0f} $")
                    st.info(f"📄 Facture PDF générée: {st.session_state.num_fact_auto}")
                    st.download_button(
                        label="📥 TÉLÉCHARGER LE PDF MAINTENANT",
                        data=st.session_state.pdf_auto,
                        file_name=f"{st.session_state.num_fact_auto}.pdf",
                        mime="application/pdf",
                        width="stretch",
                        key="dl_facture_auto"
                    )
                    pdf_b64 = base64.b64encode(st.session_state.pdf_auto).decode()
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
                    if st.button("Nouvelle Vente", width="stretch", key="new_vente_auto"):
                        st.session_state.panier_voiture = []
                        st.session_state.vente_auto_finie = False
                        st.session_state.pdf_auto = None
                        st.session_state.num_fact_auto = None
                        st.rerun()
                elif not st.session_state.panier_voiture:
                    st.info("Panier vide")
                else:
                    for i, item in enumerate(st.session_state.panier_voiture):
                        with st.container(border=True):
                            st.markdown(f"**{item['marque']} {item['modele']}**")
                            st.caption(f"Année: {item.get('annee','')} | Plaque: {item.get('plaque','')}")
                            c1, c2 = st.columns([2,1])
                            st.session_state.panier_voiture[i]['qte'] = c1.number_input("QTE", min_value=1, value=item['qte'], key=f"qte_panier_v_{i}")
                            sous_total = float(item['prix']) * int(st.session_state.panier_voiture[i]['qte'])
                            c2.markdown(f"**{sous_total:,.0f} $**")
                            if st.button("❌ Supprimer", key=f"del_v_{i}"):
                                st.session_state.panier_voiture.pop(i)
                                st.rerun()
                            total += sous_total

                    st.divider()
                    st.markdown(f"### Total : **{total:,.0f} $**")

                    if st.button("💳 Finaliser Vente", type="primary", width="stretch", key="btn_facture_auto"):
                        try:
                            if not nom_client or not st.session_state.panier_voiture:
                                st.warning("Nom client + panier requis")
                                st.stop()

                            with st.spinner("Enregistrement vente..."):
                                total = sum(float(i['prix']) * int(i['qte']) for i in st.session_state.panier_voiture)

                                id_utilisateur = 1
                                if st.session_state.user_name == "ASIYA":
                                    id_utilisateur = 2
                                elif st.session_state.user_name == "BASAM":
                                    id_utilisateur = 3

                                vente_result = supabase.table("ventes").insert({
                                    "total": total,
                                    "id_utilisateur": id_utilisateur,
                                    "nom_client": str(nom_client),
                                    "telephone_client": str(tel_client)
                                }).execute()

                                id_vente = vente_result.data[0]['id']

                                details_list = []
                                for i in st.session_state.panier_voiture:
                                    nom_complet = f"{i['marque']} {i['modele']} - {i.get('annee','')} - {i.get('plaque','')} - {i.get('couleur','')} - {i.get('kilometrage','')} KM"
                                    details_list.append({"nom": nom_complet, "qte": i['qte'], "prix": i['prix']})

                                    supabase.table("ventes_details").insert({
                                        "id_vente": id_vente,
                                        "id_article": int(i['id']),
                                        "quantite": int(i['qte']),
                                        "prix_unitaire": float(i['prix']),
                                        "sous_total": float(i['prix']) * int(i['qte'])
                                    }).execute()

                                    supabase.table("voitures").update({"statut": "Vendue"}).eq("id", i['id']).execute()

                                num_fact, pdf_bytes = creer_facture_auto("Vente Voiture", nom_client, f"Vente {len(st.session_state.panier_voiture)} véhicule(s)", total, "$", details_list, tel_client)

                                st.session_state.vente_auto_finie = True
                                st.session_state.pdf_auto = pdf_bytes
                                st.session_state.num_fact_auto = num_fact
                                st.session_state.total_auto = total
                                st.session_state.panier_voiture = []
                                st.cache_data.clear()
                                st.rerun()

                        except Exception as e:
                            st.error(f"ERREUR SUPABASE : {e}")
                            st.code(str(e))

if tab6 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab6:
        st.markdown("## 🚘 Gestion Parc Automobile")

        colonnes_voitures = get_table_columns("voitures")

        with st.expander("➕ Ajouter Nouvelle Voiture"):
            with st.form("form_voiture", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                marque = c1.text_input("Marque")
                modele = c2.text_input("Modèle")
                annee = c3.text_input("Année")

                data_insert = {
                    "marque": str(marque),
                    "modele": str(modele),
                    "annee": str(annee)
                }

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
                    prix = c3.number_input("Prix $", min_value=0.0, value=0.0)
                    data_insert["prix"] = float(prix)
                if "statut" in colonnes_voitures:
                    statut = c1.selectbox("Statut", ["Disponible", "Réservée", "Vendue"])
                    data_insert["statut"] = str(statut)

                if st.form_submit_button("💾 Ajouter Voiture"):
                    try:
                        supabase.table("voitures").insert(data_insert).execute()
                        st.success("Voiture ajoutée")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout")
                        st.code(repr(e))

        st.divider()
        st.subheader("📋 Liste des Voitures")

        if df_voitures.empty:
            st.info("Aucune voiture")
        else:
            for _, row in df_voitures.iterrows():
                with st.expander(f"{row['marque']} {row['modele']} - {row.get('plaque','')} - {row.get('statut','')}"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        new_marque = st.text_input("Marque", value=row['marque'], key=f"marque_{row['id']}")
                        new_modele = st.text_input("Modèle", value=row['modele'], key=f"modele_{row['id']}")
                        new_annee = st.text_input("Année", value=row.get('annee',''), key=f"annee_{row['id']}")

                    data_update = {
                        "marque": str(new_marque),
                        "modele": str(new_modele),
                        "annee": str(new_annee)
                    }

                    with c2:
                        if "plaque" in colonnes_voitures:
                            new_plaque = st.text_input("Plaque", value=row.get('plaque',''), key=f"plaque_{row['id']}")
                            data_update["plaque"] = str(new_plaque)
                        if "couleur" in colonnes_voitures:
                            new_couleur = st.text_input("Couleur", value=row.get('couleur',''), key=f"couleur_{row['id']}")
                            data_update["couleur"] = str(new_couleur)
                        if "kilometrage" in colonnes_voitures:
                            new_km = st.number_input("KM", value=int(row.get('kilometrage',0)), key=f"km_{row['id']}")
                            data_update["kilometrage"] = int(new_km)

                    with c3:
                        if "carburant" in colonnes_voitures:
                            new_carb = st.selectbox("Carburant", ["Essence", "Diesel", "Hybride", "Électrique"], index=["Essence", "Diesel", "Hybride", "Électrique"].index(row.get('carburant','Essence')), key=f"carb_{row['id']}")
                            data_update["carburant"] = str(new_carb)
                        if "boite" in colonnes_voitures:
                            new_boite = st.selectbox("Boîte", ["Manuelle", "Automatique"], index=["Manuelle", "Automatique"].index(row.get('boite','Manuelle')), key=f"boite_{row['id']}")
                            data_update["boite"] = str(new_boite)
                        if "prix" in colonnes_voitures:
                            new_prix = st.number_input("Prix $", value=float(row.get('prix',0)), key=f"prix_{row['id']}")
                            data_update["prix"] = float(new_prix)
                        if "statut" in colonnes_voitures:
                            new_statut = st.selectbox("Statut", ["Disponible", "Réservée", "Vendue"], index=["Disponible", "Réservée", "Vendue"].index(row.get('statut','Disponible')), key=f"statut_{row['id']}")
                            data_update["statut"] = str(new_statut)

                    c1, c2 = st.columns(2)
                    if c1.button("✏️ Modifier", key=f"mod_v_{row['id']}", width="stretch"):
                        try:
                            supabase.table("voitures").update(data_update).eq("id", int(row['id'])).execute()
                            st.success("Modifié")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur modif")
                            st.code(repr(e))

                    if st.session_state.user_role == "PDG":
                        if c2.button("🗑️ Supprimer", key=f"del_v_{row['id']}", width="stretch"):
                            try:
                                supabase.table("voitures").delete().eq("id", int(row['id'])).execute()
                                st.success("Supprimé")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur suppression")
                                st.code(repr(e))
                    else:
                        c2.info("🔒 Suppression réservée au PDG")

if tab7 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab7:
        st.markdown("## 💰 Comptabilité - Relevé par Catégorie")

        colonnes_compta = get_table_columns("comptabilite")

        with st.expander("➕ Ajouter Opération"):
            with st.form("form_compta", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                type_op = c1.selectbox("Type", ["Revenu", "Dépense"])
                cat = c2.text_input("Catégorie", placeholder="Ex: Loyer, Vente, Salaire")
                montant = c3.number_input("Montant", min_value=0.0)

                data_insert = {
                    "type": str(type_op),
                    "categorie": str(cat),
                    "montant": float(montant)
                }

                if "description" in colonnes_compta:
                    desc = c1.text_input("Description")
                    data_insert["description"] = str(desc)
                if "devise" in colonnes_compta:
                    devise = c2.selectbox("Devise", ["FC", "$", "€"])
                    data_insert["devise"] = str(devise)
                if "date" in colonnes_compta:
                    date_op = c3.date_input("Date", value=date.today())
                    data_insert["date"] = str(date_op)

                if st.form_submit_button("💾 Ajouter Opération"):
                    try:
                        supabase.table("comptabilite").insert(data_insert).execute()
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
            col1, col2, col3 = st.columns(3)
            total_revenu = df_compta[df_compta['type']=='Revenu']['montant'].sum()
            total_depense = df_compta[df_compta['type']=='Dépense']['montant'].sum()
            solde = total_revenu - total_depense

            col1.metric("💰 Total Revenus", f"{total_revenu:,.0f}")
            col2.metric("💸 Total Dépenses", f"{total_depense:,.0f}")
            col3.metric("💎 Solde", f"{solde:,.0f}")

            st.divider()

            categories = df_compta.get('categorie', pd.Series(dtype=str)).dropna().unique()
            if len(categories) > 0:
                st.subheader("📂 Relevé par Catégorie")
                for cat in sorted(categories):
                    df_cat = df_compta[df_compta.get('categorie', '') == cat]
                    total_cat = df_cat['montant'].sum()
                    with st.expander(f"📁 {cat} - {len(df_cat)} opérations - Total: {total_cat:,.0f}"):
                        st.dataframe(df_cat, use_container_width=True, hide_index=True)

if tab8 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab8:
        st.markdown("## 📄 Factures - Relevé par Catégorie")

        if df_compta.empty:
            st.info("Aucune opération")
        else:
            df_compta_sorted = df_compta.sort_values('date', ascending=False)

            col_f1, col_f2, col_f3 = st.columns(3)
            date_debut = col_f1.date_input("📅 Date début", value=date.today() - timedelta(days=30))
            date_fin = col_f2.date_input("📅 Date fin", value=date.today())
            col_f3.markdown("### ")

            col_f4, col_f5 = st.columns(2)
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

                        st.dataframe(
                            df_cat[['date', 'type', 'description', 'montant', 'devise']],
                            use_container_width=True,
                            hide_index=True
                        )

                        col_dl1, col_dl2 = st.columns(2)

                        excel_bytes_cat = generer_excel_pro(df_cat, f"Releve {cat} {date_debut}-{date_fin}",
                                                           df_cat[df_cat['type']=='Revenu']['montant'].sum(),
                                                           df_cat[df_cat['type']=='Dépense']['montant'].sum(),
                                                           df_cat[df_cat['type']=='Revenu']['montant'].sum() - df_cat[df_cat['type']=='Dépense']['montant'].sum())

                        col_dl1.download_button(
                            label=f"📥 Télécharger {cat} - EXCEL",
                            data=excel_bytes_cat,
                            file_name=f"Releve_{cat}_{date_debut}_{date_fin}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            width="stretch",
                            key=f"dl_excel_cat_{cat}_{date_debut}"
                        )

                        pdf_cat = FPDF()
                        pdf_cat.add_page()
                        pdf_cat.set_fill_color(20, 50, 40)
                        pdf_cat.rect(0, 0, 210, 35, 'F')
                        pdf_cat.set_text_color(255, 255, 255)
                        pdf_cat.set_font("Arial", "B", 20)
                        pdf_cat.set_xy(10, 8)
                        pdf_cat.cell(0, 10, "ASYMAS BUSINESS", ln=True)
                        pdf_cat.set_font("Arial", "", 9)
                        pdf_cat.set_xy(10, 16)
                        pdf_cat.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
                        pdf_cat.set_xy(10, 21)
                        pdf_cat.cell(0, 5, "Email: asamnesstsang636@gmail.com", ln=True)
                        pdf_cat.set_font("Arial", "B", 10)
                        pdf_cat.set_xy(150, 8)
                        pdf_cat.cell(50, 6, f"Periode: {date_debut} au {date_fin}", ln=True, align="R")
                        pdf_cat.ln(15)
                        pdf_cat.set_text_color(0, 0, 0)
                        pdf_cat.set_fill_color(255, 204, 0)
                        pdf_cat.set_font("Arial", "B", 14)
                        pdf_cat.cell(0, 10, f"RELEVE - {cat.upper()}", ln=True, fill=True)
                        pdf_cat.ln(5)
                        pdf_cat.set_font("Arial", "B", 11)
                        pdf_cat.cell(0, 8, f"Total FC: {total_cat_fc:,.0f} | Total USD: {total_cat_usd:,.0f} | Total EUR: {total_cat_eur:,.0f}", ln=True)
                        pdf_cat.ln(3)
                        pdf_cat.set_font("Arial", "B", 9)
                        pdf_cat.cell(25, 7, "Date", 1)
                        pdf_cat.cell(25, 7, "Type", 1)
                        pdf_cat.cell(90, 7, "Description", 1)
                        pdf_cat.cell(30, 7, "Montant", 1)
                        pdf_cat.cell(20, 7, "Devise", 1, ln=True)
                        pdf_cat.set_font("Arial", "", 8)
                        for _, row in df_cat.iterrows():
                            pdf_cat.cell(25, 6, str(row.get('date','')), 1)
                            pdf_cat.cell(25, 6, str(row.get('type','')), 1)
                            desc = str(row.get('description',''))[:45]
                            pdf_cat.cell(90, 6, desc, 1)
                            pdf_cat.cell(30, 6, f"{row.get('montant',0):,.0f}", 1)
                            pdf_cat.cell(20, 6, str(row.get('devise','FC')), 1, ln=True)

                        pdf_bytes_cat = pdf_cat.output(dest='S').encode('latin-1')

                        col_dl2.download_button(
                            label=f"📥 Télécharger {cat} - PDF",
                            data=pdf_bytes_cat,
                            file_name=f"Releve_{cat}_{date_debut}_{date_fin}.pdf",
                            mime="application/pdf",
                            width="stretch",
                            key=f"dl_pdf_cat_{cat}_{date_debut}"
                        )

                st.divider()

                st.subheader("📥 Télécharger Relevé Complet Filtré")
                col_dl_g1, col_dl_g2 = st.columns(2)

                total_revenu_global = df_filtre_fact[df_filtre_fact['type']=='Revenu']['montant'].sum()
                total_depense_global = df_filtre_fact[df_filtre_fact['type']=='Dépense']['montant'].sum()
                solde_global = total_revenu_global - total_depense_global

                excel_bytes_global = generer_excel_pro(df_filtre_fact, f"Releve Filtré {date_debut}-{date_fin}",
                                                      total_revenu_global, total_depense_global, solde_global)

                col_dl_g1.download_button(
                    label="📥 TÉLÉCHARGER TOUT - EXCEL",
                    data=excel_bytes_global,
                    file_name=f"Releve_Filtre_{date_debut}_{date_fin}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch",
                    key="dl_excel_global_filtre"
                )

                pdf_global = FPDF()
                pdf_global.add_page()
                pdf_global.set_fill_color(20, 50, 40)
                pdf_global.rect(0, 0, 210, 35, 'F')
                pdf_global.set_text_color(255, 255, 255)
                pdf_global.set_font("Arial", "B", 20)
                pdf_global.set_xy(10, 8)
                pdf_global.cell(0, 10, "ASYMAS BUSINESS", ln=True)
                pdf_global.set_font("Arial", "", 9)
                pdf_global.set_xy(10, 16)
                pdf_global.cell(0, 5, "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623", ln=True)
                pdf_global.set_xy(10, 21)
                pdf_global.cell(0, 5, "Email: asamnesstsang636@gmail.com", ln=True)
                pdf_global.set_font("Arial", "B", 10)
                pdf_global.set_xy(150, 8)
                pdf_global.cell(50, 6, f"Periode: {date_debut} au {date_fin}", ln=True, align="R")
                pdf_global.ln(15)
                pdf_global.set_text_color(0, 0, 0)
                pdf_global.set_fill_color(255, 204, 0)
                pdf_global.set_font("Arial", "B", 14)
                pdf_global.cell(0, 10, "RELEVE GENERAL FILTRE", ln=True, fill=True)
                pdf_global.ln(5)
                pdf_global.set_font("Arial", "B", 11)
                pdf_global.cell(0, 8, f"Total FC: {total_fc:,.0f} | Total USD: {total_usd:,.0f} | Total EUR: {total_eur:,.0f}", ln=True)
                pdf_global.ln(3)

                for cat in sorted(categories):
                    df_cat = df_filtre_fact[df_filtre_fact.get('categorie', '') == cat]
                    total_cat_fc = df_cat[df_cat.get('devise','FC')=='FC']['montant'].sum()
                    total_cat_usd = df_cat[df_cat.get('devise','FC')=='$']['montant'].sum()

                    pdf_global.set_font("Arial", "B", 12)
                    pdf_global.cell(0, 8, f"CATEGORIE: {cat} - {len(df_cat)} operations", ln=True)
                    pdf_global.set_font("Arial", "B", 10)
                    pdf_global.cell(0, 6, f"Total: FC {total_cat_fc:,.0f} | USD {total_cat_usd:,.0f}", ln=True)
                    pdf_global.ln(2)

                    pdf_global.set_font("Arial", "B", 9)
                    pdf_global.cell(25, 7, "Date", 1)
                    pdf_global.cell(25, 7, "Type", 1)
                    pdf_global.cell(90, 7, "Description", 1)
                    pdf_global.cell(30, 7, "Montant", 1)
                    pdf_global.cell(20, 7, "Devise", 1, ln=True)

                    pdf_global.set_font("Arial", "", 8)
                    for _, row in df_cat.iterrows():
                        pdf_global.cell(25, 6, str(row.get('date','')), 1)
                        pdf_global.cell(25, 6, str(row.get('type','')), 1)
                        desc = str(row.get('description',''))[:45]
                        pdf_global.cell(90, 6, desc, 1)
                        pdf_global.cell(30, 6, f"{row.get('montant',0):,.0f}", 1)
                        pdf_global.cell(20, 6, str(row.get('devise','FC')), 1, ln=True)

                    pdf_global.ln(5)

                pdf_bytes_global = pdf_global.output(dest='S').encode('latin-1')

                col_dl_g2.download_button(
                    label="📥 TÉLÉCHARGER TOUT - PDF",
                    data=pdf_bytes_global,
                    file_name=f"Releve_Filtre_{date_debut}_{date_fin}.pdf",
                    mime="application/pdf",
                    width="stretch",
                    key="dl_pdf_global_filtre"
                )

if tab9 and st.session_state.user_role == "PDG":
    with tab9:
        st.markdown("## 👥 Gestion Utilisateurs - PDG UNIQUEMENT")

        if df_utilisateurs.empty:
            st.warning("Table 'utilisateurs' vide. Crée-la dans Supabase avec colonnes: id, nom, role, password")
            st.code("""
CREATE TABLE utilisateurs (
    id SERIAL PRIMARY KEY,
    nom TEXT NOT NULL,
    role TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);
            INSERT INTO utilisateurs (nom, role, password) VALUES
('TSANG', 'PDG', 'tsang2024'),
('ASIYA', 'GERANTE', 'asiya2024'),
('BASAM', 'UTILISATEUR', 'basam2024');
            """, language="sql")
        else:
            st.subheader("🔐 Changer les Mots de Passe")

            with st.form("form_passwords", clear_on_submit=False):
                st.markdown("### 🔑 Nouveaux mots de passe")
                c1, c2, c3 = st.columns(3)
                
                new_pass_pdg = c1.text_input("PDG", value=passwords_db.get("PDG", ""), type="password", key="pass_pdg")
                new_pass_gerante = c2.text_input("GÉRANTE", value=passwords_db.get("GERANTE", ""), type="password", key="pass_ger")
                new_pass_user = c3.text_input("UTILISATEUR", value=passwords_db.get("UTILISATEUR", ""), type="password", key="pass_user")
                
                if st.form_submit_button("💾 ENREGISTRER LES MOTS DE PASSE", width="stretch", type="primary"):
                    try:
                        supabase.table("utilisateurs").update({"password": new_pass_pdg}).eq("role", "PDG").execute()
                        supabase.table("utilisateurs").update({"password": new_pass_gerante}).eq("role", "GERANTE").execute()
                        supabase.table("utilisateurs").update({"password": new_pass_user}).eq("role", "UTILISATEUR").execute()
                        st.success("✅ Mots de passe mis à jour")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur mise à jour")
                        st.code(repr(e))
            
            st.divider()
            st.subheader("📋 Liste des Utilisateurs")
            st.dataframe(df_utilisateurs[['nom', 'role']], use_container_width=True, hide_index=True)
else:
    if tab9:
        with tab9:
            st.error("🔒 ACCÈS REFUSÉ - Section réservée au PDG uniquement")

st.sidebar.divider()
st.sidebar.caption(f"ASYMAS BUSINESS v2.0")
st.sidebar.caption(f"Connecté: {st.session_state.user_name}")
