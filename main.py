import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date, datetime
from fpdf import FPDF
import base64
import io

# === CONFIG SUPABASE ===
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="ASYMAS BUSINESS", layout="wide", page_icon="💎")

# === SYSTÈME DE MOTS DE PASSE MODIFIABLES ===
if 'passwords' not in st.session_state:
    st.session_state.passwords = {
        "PDG": "tsang2024",
        "GERANTE": "asiya2024",
        "UTILISATEUR": "basam2024"
    }

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

        if st.button("SE CONNECTER", use_container_width=True, type="primary"):
            if profil == "PDG TSANG" and password == st.session_state.passwords["PDG"]:
                st.session_state.user_role = "PDG"
                st.session_state.user_name = "TSANG"
                st.rerun()
            elif profil == "Gérante ASIYA" and password == st.session_state.passwords["GERANTE"]:
                st.session_state.user_role = "GERANTE"
                st.session_state.user_name = "ASIYA"
                st.rerun()
            elif profil == "BASAM" and password == st.session_state.passwords["UTILISATEUR"]:
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

# === GÉNÉRATEUR PDF FACTURE - BENI RDC ===
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

    pdf.set_fill_color(0, 102)
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

    return pdf.output(dest='S').encode('latin-1')

def creer_facture_auto(type_op, client, details, montant, devise="FC", details_list=None, tel="+243...", periode=""):
    numero_facture = f"AS-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    if details_list is None:
        details_list = [{"nom": details, "qte": 1, "prix": montant}]

    pdf_bytes = generer_pdf_facture(numero_facture, type_op, client, details_list, montant, devise, tel, periode)

    try:
        colonnes_compta = get_table_columns("compta")
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

        supabase.table("compta").insert(data_compta).execute()
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

df_biens = load_table("biens")
df_articles = load_table("articles")
df_voitures = load_table("voitures")
df_compta = load_table("compta")
df_factures = load_table("factures_proforma")

st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
st.markdown("### Agriculture • Commerce • Immobilier • Automobile • Beni RDC")

with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.user_name}")
    st.markdown(f"**Rôle : {st.session_state.user_role}**")
    st.info("ASYMAS BUSINESS v1.0")

    if st.session_state.user_role == "PDG":
        with st.expander("🔐 GESTION ACCÈS", expanded=False):
            st.markdown("### Modifier les mots de passe")
            c1, c2 = st.columns(2)
            new_pwd_pdg = c1.text_input("PDG", value=st.session_state.passwords["PDG"], type="password", key="pwd_pdg")
            new_pwd_gerante = c2.text_input("Gérante", value=st.session_state.passwords["GERANTE"], type="password", key="pwd_gerante")
            new_pwd_user = c1.text_input("BASAM", value=st.session_state.passwords["UTILISATEUR"], type="password", key="pwd_user")

            if st.button("💾 Sauvegarder Mots de Passe", use_container_width=True):
                st.session_state.passwords["PDG"] = new_pwd_pdg
                st.session_state.passwords["GERANTE"] = new_pwd_gerante
                st.session_state.passwords["UTILISATEUR"] = new_pwd_user
                st.success("Mots de passe mis à jour")

    if st.button("🔄 Actualiser", key="btn_save"):
        st.cache_data.clear()
        st.rerun()
    if st.button("🚪 DÉCONNEXION", key="logout", use_container_width=True):
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.rerun()

if st.session_state.user_role == "UTILISATEUR":
    tab2, = st.tabs(["🛍️ Commerce"])
    tab1 = tab3 = tab4 = tab5 = tab6 = tab7 = tab8 = None
else:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📊 Dashboard", "🛍️ Commerce", "📦 Gestion Stock", "🏠 Immobilier", "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures"
    ])

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

            df_articles_filtre = df_articles
            if recherche:
                mask = df_articles['nom_article'].str.contains(recherche, case=False, na=False)
                df_articles_filtre = df_articles

            if not df_articles_filtre.empty:
                options = [f"{row['nom_article']} - {row.get('prix_vente',0):,.0f} FC - Stock:{row.get('stock','?')}" for _, row in df_articles_filtre.iterrows()]
                choix = st.selectbox("Choisir le produit", options, key="choix_prod_c")
                idx_choisi = options.index(choix)
                produit_choisi = df_articles_filtre.iloc[idx_choisi]

                c1, c2, c3 = st.columns([1,1,1])
                qte = c1.number_input("QTE", min_value=1, value=1, key="qte_c")
                c2.markdown(f"### Prix: **{produit_choisi.get('prix_vente',0):,.0f} FC**")

                if c3.button("➕ Ajouter au Panier", use_container_width=True, key="add_panier_c"):
                    st.session_state.panier_commerce.append({
                        "id": int(produit_choisi['id']),
                        "nom": str(produit_choisi['nom_article']),
                        "prix": float(produit_choisi.get('prix_vente',0)),
                        "qte": int(qte)
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
                    use_container_width=True,
                    key="dl_facture_commerce"
                )
                if st.button("Nouvelle Vente", use_container_width=True, key="new_vente_c"):
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
                        st.session_state.panier_commerce[i]['qte'] = c1.number_input("QTE", min_value=1, value=item['qte'], key=f"qte_panier_c_{i}")
                        sous_total = float(item['prix']) * int(st.session_state.panier_commerce[i]['qte'])
                        c2.markdown(f"**{sous_total:,.0f} FC**")
                        if st.button("❌ Supprimer", key=f"del_c_{i}"):
                            st.session_state.panier_commerce.pop(i)
                            st.rerun()
                        total += sous_total

                st.divider()
                st.markdown(f"### Total : **{total:,.0f} FC**")

                if st.button("💳 Finaliser Vente", type="primary", use_container_width=True, key="final_c"):
                    if nom_client and st.session_state.panier_commerce:
                        with st.spinner("Enregistrement + Génération PDF..."):
                            details_list = [{"nom": i['nom'], "qte": i['qte'], "prix": i['prix']} for i in st.session_state.panier_commerce]
                            details_text = ", ".join([f"{i['nom']} x{i['qte']}" for i in st.session_state.panier_commerce])

                            num_fact, pdf_bytes = creer_facture_auto("Vente Commerce", nom_client, details_text, total, "FC", details_list, tel_client)

                            if pdf_bytes and len(pdf_bytes) > 100:
                                st.session_state.vente_finie = True
                                st.session_state.pdf_data = pdf_bytes
                                st.session_state.num_fact = num_fact
                                st.session_state.total_vente = total
                                st.session_state.panier_commerce = []
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("PDF vide - Réessaye")
                    else:
                        st.warning("Nom client + panier requis")

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
                    if c1.button("✏️ Modifier", key=f"mod_art_{row['id']}", use_container_width=True):
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
                        if c2.button("🗑️ Supprimer", key=f"del_art_{row['id']}", use_container_width=True):
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

        if st.button("📄 GÉNÉRER FACTURE PDF", type="primary", use_container_width=True, key="btn_facture_immo"):
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
                    use_container_width=True,
                    key="dl_facture_immo"
                )
                st.cache_data.clear()
            else:
                st.error("Nom client + Adresse obligatoires")

# === AUTOMOBILE - PDG ET GERANTE SEULEMENT ===
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

                df_voitures_filtre = df_voitures
                if recherche_voiture:
                    mask = df_voitures['marque'].str.contains(recherche_voiture, case=False, na=False) | \
                           df_voitures['modele'].str.contains(recherche_voiture, case=False, na=False) | \
                           df_voitures.get('plaque', pd.Series()).str.contains(recherche_voiture, case=False, na=False)
                    df_voitures_filtre = df_voitures

                if not df_voitures_filtre.empty:
                    options = []
                    for _, row in df_voitures_filtre.iterrows():
                        details = f"{row['marque']} {row['modele']} - {row.get('annee','')} - {row.get('plaque','')} - {row.get('prix',0):,.0f} $"
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
                        c2.markdown(f"**KM:** {voiture_choisie.get('kilometrage','N/A')}")
                        c3.markdown(f"**Carburant:** {voiture_choisie.get('carburant','N/A')}")
                        c3.markdown(f"**Boîte:** {voiture_choisie.get('boite','N/A')}")
                        st.markdown(f"**Statut:** {voiture_choisie.get('statut','N/A')}")
                        st.markdown(f"### Prix: **{voiture_choisie.get('prix',0):,.0f} $**")

                    c1, c2 = st.columns([1,1])
                    qte = c1.number_input("QTE", min_value=1, value=1, key="qte_v")

                    if c2.button("➕ Ajouter au Panier", use_container_width=True, key="add_panier_v"):
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
                        use_container_width=True,
                        key="dl_facture_auto"
                    )
                    if st.button("Nouvelle Vente", use_container_width=True, key="new_vente_auto"):
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
                            st.caption(f"Année: {item.get('annee','')} | Plaque: {item.get('plaque','')} | Couleur: {item.get('couleur','')}")
                            st.caption(f"KM: {item.get('kilometrage','')} | Carburant: {item.get('carburant','')} | Boîte: {item.get('boite','')}")
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

                    # === BLOC CORRIGÉ - FINALISER VENTE ===
                    if st.button("💳 Finaliser Vente", type="primary", use_container_width=True, key="btn_facture_auto"):
                        try:
                            if not nom_client or not st.session_state.panier_voiture:
                                st.warning("Nom client + panier requis")
                                st.stop()

                            with st.spinner("Enregistrement vente..."):
                                # 1. INSÉRER LA VENTE PRINCIPALE
                                total = sum(float(i['prix']) * int(i['qte']) for i in st.session_state.panier_voiture)

                                # Récupérer l'ID utilisateur depuis Supabase
                                user_data = supabase.table("users").select("id").eq("nom", st.session_state.user_name).execute()
                                id_utilisateur = user_data.data[0]['id'] if user_data.data else 1

                                vente_result = supabase.table("ventes").insert({
                                    "total": total,
                                    "id_utilisateur": id_utilisateur,
                                    "nom_client": nom_client,
                                    "telephone_client": tel_client
                                }).execute
