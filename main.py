import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import date, timedelta
from fpdf import FPDF
import base64
import qrcode
from io import BytesIO
from PIL import Image
import streamlit_qrcode_scanner

st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="💎", layout="wide")

# --- Connexion Supabase ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Erreur de connexion à Supabase : {e}")
    st.stop()
def generer_excel_pro(df, nom_fichier, total_revenu, total_depense, solde):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Releve', index=False)
        worksheet = writer.sheets['Releve']
        worksheet.append([])
        worksheet.append(['TOTAL REVENUS', total_revenu])
        worksheet.append(['TOTAL DEPENSES', total_depense])
        worksheet.append(['SOLDE', solde])
    return output.getvalue()

def creer_facture_auto(type_operation, nom_client, details, montant_total, devise, details_list=None, tel_client="", periode=""):
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

    num_fact = f"ASB-{date.today().strftime('%Y%m%d')}-{int(pd.Timestamp.now().timestamp()) % 10000:04d}"
    pdf.set_font("Arial", "B", 10)
    pdf.set_xy(150, 8)
    pdf.cell(50, 6, f"Facture No: {num_fact}", ln=True, align="R")
    pdf.set_xy(150, 14)
    pdf.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")

    pdf.ln(15)

    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"FACTURE - {type_operation.upper()}", ln=True, fill=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "CLIENT:", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Nom: {nom_client}", ln=True)
    if tel_client:
        pdf.cell(0, 6, f"Telephone: {tel_client}", ln=True)
    if periode:
        pdf.cell(0, 6, f"Periode: {periode}", ln=True)
    pdf.ln(3)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "DETAILS:", ln=True)
    pdf.ln(2)

    if details_list:
        pdf.set_font("Arial", "B", 9)
        pdf.cell(110, 7, "Designation", 1)
        pdf.cell(20, 7, "QTE", 1)
        pdf.cell(30, 7, "Prix Unit.", 1)
        pdf.cell(30, 7, "Total", 1, ln=True)

        pdf.set_font("Arial", "", 9)
        for item in details_list:
            nom = str(item.get('nom', ''))[:50]
            qte = int(item.get('qte', 1))
            prix = float(item.get('prix', 0))
            total = qte * prix
            pdf.cell(110, 7, nom, 1)
            pdf.cell(20, 7, str(qte), 1)
            pdf.cell(30, 7, f"{prix:,.0f}", 1)
            pdf.cell(30, 7, f"{total:,.0f}", 1, ln=True)
    else:
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 6, str(details))

    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(130, 10, "TOTAL A PAYER:", 1, 0, 'R', True)
    pdf.cell(60, 10, f"{montant_total:,.0f} {devise}", 1, 1, 'R', True)

    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 5, "Merci pour votre confiance!", ln=True, align="C")
    pdf.cell(0, 5, "ASYMAS BUSINESS - Votre partenaire de confiance", ln=True, align="C")

    return num_fact, pdf.output(dest='S').encode('latin-1')

@st.cache_data(ttl=300)
def get_table_data(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_table_columns(table_name):
    try:
        response = supabase.table(table_name).select("*").limit(1).execute()
        if response.data:
            return list(response.data[0].keys())
        return []
    except:
        return []

def get_users_from_db():
    try:
        response = supabase.table("utilisateurs").select("*").execute()
        return {u['role']: u['password'] for u in response.data}
    except:
        return {"PDG": "tsang2024", "GERANTE": "asiya2024", "UTILISATEUR": "basam2024"}

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

if not st.session_state.authenticated:
    st.title("💎 ASYMAS BUSINESS - CONNEXION")
    passwords_db = get_users_from_db()
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
            st.markdown("### 🔐 Connexion Sécurisée")
            username = st.selectbox("Utilisateur", ["TSANG (PDG)", "ASIYA (GÉRANTE)", "BASAM (UTILISATEUR)"])
            password = st.text_input("Mot de passe", type="password")
            if st.button("🚀 CONNEXION", width="stretch", type="primary"):
                role_map = {"TSANG (PDG)": "PDG", "ASIYA (GÉRANTE)": "GERANTE", "BASAM (UTILISATEUR)": "UTILISATEUR"}
                role = role_map[username]
                if password == passwords_db.get(role):
                    st.session_state.authenticated = True
                    st.session_state.user_role = role
                    st.session_state.user_name = username.split(" (")[0]
                    st.rerun()
                else:
                    st.error("❌ Mot de passe incorrect")
    st.stop()

st.sidebar.title(f"💎 ASYMAS")
st.sidebar.success(f"**{st.session_state.user_name}**\n{st.session_state.user_role}")
if st.sidebar.button("🚪 Déconnexion"):
    st.session_state.authenticated = False
    st.rerun()

st.title("💎 ASYMAS BUSINESS MANAGEMENT")

df_articles = get_table_data("articles")
df_voitures = get_table_data("voitures")
df_compta = get_table_data("comptabilite")
df_utilisateurs = get_table_data("utilisateurs")
passwords_db = get_users_from_db()

if st.session_state.user_role == "PDG":
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Tableau de Bord", "🛒 Commerce", "📦 Gestion Stock", "🏠 Immobilier",
        "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures", "👥 Utilisateurs"
    ])
elif st.session_state.user_role == "GERANTE":
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Tableau de Bord", "🛒 Commerce", "📦 Gestion Stock", "🏠 Immobilier",
        "🚗 Automobile", "🚘 Gestion Parc", "💰 Comptabilité", "📄 Factures", None
    ])
else:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Tableau de Bord", "🛒 Commerce", None, None, None, None, None
    ])

if tab1:
    with tab1:
        st.markdown("## 📊 Tableau de Bord")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Articles", len(df_articles))
        col2.metric("🚗 Voitures", len(df_voitures))
        col3.metric("💰 Revenus", f"{df_compta[df_compta['type']=='Revenu']['montant'].sum():,.0f}")
        col4.metric("💸 Dépenses", f"{df_compta[df_compta['type']=='Dépense']['montant'].sum():,.0f}")

        st.divider()

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("📦 Stock Faible")
            if not df_articles.empty:
                stock_faible = df_articles[df_articles['stock'] < 10]
                if not stock_faible.empty:
                    st.dataframe(stock_faible[['nom_article', 'stock', 'prix_vente']], use_container_width=True, hide_index=True)
                else:
                    st.success("✅ Stock OK")
            else:
                st.info("Aucun article")

        with col_g2:
            st.subheader("🚗 Voitures Disponibles")
            if not df_voitures.empty:
                voitures_dispo = df_voitures[df_voitures.get('statut', '') == 'Disponible']
                if not voitures_dispo.empty:
                    st.dataframe(voitures_dispo[['marque', 'modele', 'annee', 'prix']], use_container_width=True, hide_index=True)
                else:
                    st.info("Aucune voiture disponible")
            else:
                st.info("Aucune voiture")

if tab2:
    with tab2:
        st.markdown("## 🛒 Commerce - Point de Vente")

        if 'panier' not in st.session_state:
            st.session_state.panier = []
        if 'vente_finie' not in st.session_state:
            st.session_state.vente_finie = False
        if 'pdf_bytes' not in st.session_state:
            st.session_state.pdf_bytes = None
        if 'num_fact' not in st.session_state:
            st.session_state.num_fact = None

        if df_articles.empty:
            st.error("Aucun article disponible - Ajoute des articles dans Gestion Stock")
        else:
            col_gauche, col_droite = st.columns([2,1])

            with col_gauche:
                st.subheader("👤 Client")
                nom_client = st.text_input("Nom Client", key="nom_client")
                tel_client = st.text_input("Téléphone Client", value="+243...", key="tel_client")

                st.subheader("📦 Articles")

                with st.expander("📷 Scanner Code Barre", expanded=False):
                    code_scanned = streamlit_qrcode_scanner.qrcode_scanner(key="qr_scanner")
                    if code_scanned:
                        st.success(f"✅ Code scanné: {code_scanned}")
                        if 'code_barre' in df_articles.columns:
                            article_trouve = df_articles[df_articles['code_barre'] == code_scanned]
                            if not article_trouve.empty:
                                st.session_state.article_scanned = article_trouve.iloc[0]
                                st.rerun()
                            else:
                                st.warning("Code-barres non trouvé dans la base")
                        else:
                            st.error("Colonne 'code_barre' manquante dans la table articles")

                recherche = st.text_input("🔍 Chercher un article", placeholder="Nom, catégorie...", key="search")

                df_articles_filtre = df_articles.copy()
                if recherche:
                    mask = (df_articles['nom_article'].str.contains(recherche, case=False, na=False) |
                            df_articles.get('categorie', pd.Series(dtype=str)).str.contains(recherche, case=False, na=False))
                    df_articles_filtre = df_articles

                if not df_articles_filtre.empty:
                    options = []
                    for _, row in df_articles_filtre.iterrows():
                        details = f"{row['nom_article']} - {row.get('categorie','')} - {row.get('prix_vente',0):,.0f} FC - Stock: {row.get('stock',0)}"
                        if row.get('code_barre'):
                            details += f" | Code: {row.get('code_barre')}"
                        options.append(details)

                    default_idx = 0
                    if 'article_scanned' in st.session_state:
                        article_scan = st.session_state.article_scanned
                        for idx, row in df_articles_filtre.iterrows():
                            if row['id'] == article_scan['id']:
                                default_idx = df_articles_filtre.index.get_loc(idx)
                                break

                    choix = st.selectbox("Choisir l'article", options, index=default_idx, key="choix_art")
                    idx_choisi = options.index(choix)
                    article_choisi = df_articles_filtre.iloc[idx_choisi]

                    with st.container(border=True):
                        st.markdown(f"### {article_choisi['nom_article']}")
                        c1, c2, c3 = st.columns(3)
                        c1.markdown(f"**Catégorie:** {article_choisi.get('categorie','N/A')}")
                        c2.markdown(f"**Prix:** {article_choisi.get('prix_vente',0):,.0f} FC")
                        c3.markdown(f"**Stock:** {article_choisi.get('stock',0)}")
                        if article_choisi.get('code_barre'):
                            st.markdown(f"**Code-barres:** {article_choisi.get('code_barre')}")

                    c1, c2 = st.columns([1,1])
                    qte = c1.number_input("QTE", min_value=1, value=1, key="qte_art")

                    if c2.button("➕ Ajouter au Panier", width="stretch", key="add_panier"):
                        if article_choisi.get('stock', 0) < qte:
                            st.error(f"Stock insuffisant! Disponible: {article_choisi.get('stock', 0)}")
                            st.stop()
                        st.session_state.panier.append({
                            "id": int(article_choisi['id']),
                            "nom_article": str(article_choisi['nom_article']),
                            "categorie": str(article_choisi.get('categorie','')),
                            "prix": float(article_choisi.get('prix_vente',0)),
                            "qte": int(qte),
                            "stock_dispo": int(article_choisi.get('stock',0)),
                            "code_barre": str(article_choisi.get('code_barre',''))
                        })
                        st.session_state.vente_finie = False
                        if 'article_scanned' in st.session_state:
                            del st.session_state.article_scanned
                        st.rerun()
                else:
                    st.info("Aucun article trouvé")

            with col_droite:
                st.subheader("🛒 Panier")
                total = 0

                if st.session_state.vente_finie and st.session_state.pdf_bytes:
                    st.success(f"✅ Vente validée - {st.session_state.total_vente:,.0f} FC")
                    st.info(f"📄 Facture PDF générée: {st.session_state.num_fact}")
                    st.download_button(
                        label="📥 TÉLÉCHARGER LE PDF MAINTENANT",
                        data=st.session_state.pdf_bytes,
                        file_name=f"{st.session_state.num_fact}.pdf",
                        mime="application/pdf",
                        width="stretch",
                        key="dl_facture"
                    )
                    pdf_b64 = base64.b64encode(st.session_state.pdf_bytes).decode()
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
                    if st.button("Nouvelle Vente", width="stretch", key="new_vente"):
                        st.session_state.panier = []
                        st.session_state.vente_finie = False
                        st.session_state.pdf_bytes = None
                        st.session_state.num_fact = None
                        st.rerun()
                elif not st.session_state.panier:
                    st.info("Panier vide")
                else:
                    for i, item in enumerate(st.session_state.panier):
                        with st.container(border=True):
                            st.markdown(f"**{item['nom_article']}**")
                            st.caption(f"Catégorie: {item.get('categorie','')}")
                            if item.get('code_barre'):
                                st.caption(f"Code: {item.get('code_barre')}")
                            c1, c2 = st.columns([2,1])
                            st.session_state.panier[i]['qte'] = c1.number_input("QTE", min_value=1, max_value=item['stock_dispo'], value=item['qte'], key=f"qte_panier_{i}")
                            sous_total = float(item['prix']) * int(st.session_state.panier[i]['qte'])
                            c2.markdown(f"**{sous_total:,.0f} FC**")
                            if st.button("❌ Supprimer", key=f"del_{i}"):
                                st.session_state.panier.pop(i)
                                st.rerun()
                            total += sous_total

                    st.divider()
                    st.markdown(f"### Total : **{total:,.0f} FC**")

                    if st.button("💳 Finaliser Vente", type="primary", width="stretch", key="btn_facture"):
                        try:
                            if not nom_client or not st.session_state.panier:
                                st.warning("Nom client + panier requis")
                                st.stop()

                            with st.spinner("Enregistrement vente..."):
                                total = sum(float(i['prix']) * int(i['qte']) for i in st.session_state.panier)

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

                                for i in st.session_state.panier:
                                    supabase.table("ventes_details").insert({
                                        "id_vente": id_vente,
                                        "id_article": int(i['id']),
                                        "quantite": int(i['qte']),
                                        "prix_unitaire": float(i['prix']),
                                        "sous_total": float(i['prix']) * int(i['qte'])
                                    }).execute()
                                    try:
                                        supabase.table("articles").update({"stock": int(i['stock_dispo'] - i['qte'])}).eq("id", i['id']).execute()
                                    except:
                                        pass

                                details_list = []
                                for i in st.session_state.panier:
                                    nom_complet = f"{i['nom_article']} - {i.get('categorie','')}"
                                    if i.get('code_barre'):
                                        nom_complet += f" | Code: {i.get('code_barre')}"
                                    details_list.append({"nom": nom_complet, "qte": i['qte'], "prix": i['prix']})

                                num_fact, pdf_bytes = creer_facture_auto("Vente", nom_client, f"Vente {len(st.session_state.panier)} article(s)", total, "FC", details_list, tel_client)

                                st.session_state.vente_finie = True
                                st.session_state.pdf_bytes = pdf_bytes
                                st.session_state.num_fact = num_fact
                                st.session_state.total_vente = total
                                st.session_state.panier = []
                                st.cache_data.clear()
                                st.rerun()

                        except Exception as e:
                            st.error(f"ERREUR SUPABASE : {e}")
                            st.code(str(e))

if tab3 and st.session_state.user_role in ["PDG", "GERANTE"]:
    with tab3:
        st.markdown("## 📦 Gestion Stock - Articles")

        colonnes_articles = get_table_columns("articles")

        with st.expander("➕ Ajouter Nouvel Article", expanded=False):
            st.markdown("#### 📷 Scanner d'abord le code-barres")
            code_scanned_ajout = streamlit_qrcode_scanner.qrcode_scanner(key="qr_scanner_ajout")

            article_existant = None
            if code_scanned_ajout and 'code_barre' in colonnes_articles:
                article_trouve = df_articles[df_articles['code_barre'] == code_scanned_ajout]
                if not article_trouve.empty:
                    article_existant = article_trouve.iloc[0]
                    st.success(f"✅ Article trouvé: {article_existant['nom_article']} - Stock actuel: {article_existant.get('stock',0)}")

                    col_auto1, col_auto2, col_auto3 = st.columns(3)
                    qte_ajout = col_auto1.number_input("Quantité à ajouter", min_value=1, value=1, key="qte_scan_auto")
                    new_prix_v = col_auto2.number_input("Nouveau Prix Vente FC", value=float(article_existant.get('prix_vente',0)), key="prix_v_scan_auto")

                    if col_auto3.button("⚡ AJOUTER STOCK AUTO", type="primary", width="stretch"):
                        try:
                            nouveau_stock = int(article_existant.get('stock',0)) + int(qte_ajout)
                            supabase.table("articles").update({
                                "stock": nouveau_stock,
                                "prix_vente": float(new_prix_v)
                            }).eq("id", int(article_existant['id'])).execute()
                            st.success(f"✅ +{qte_ajout} ajouté. Nouveau stock: {nouveau_stock}")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur mise à jour")
                            st.code(repr(e))
                else:
                    st.info(f"📦 Nouveau produit - Code: {code_scanned_ajout}")

            st.divider()
            st.markdown("#### ✍️ Créer/Modifier Article")

            with st.form("form_article", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)

                val_nom = article_existant['nom_article'] if article_existant is not None else ""
                val_cat = article_existant.get('categorie','') if article_existant is not None else ""
                val_prix_a = float(article_existant.get('prix_achat',0)) if article_existant is not None else 0.0
                val_prix_v = float(article_existant.get('prix_vente',0)) if article_existant is not None else 0.0
                val_stock = int(article_existant.get('stock',0)) if article_existant is not None else 0
                val_code = code_scanned_ajout if code_scanned_ajout else (article_existant.get('code_barre','') if article_existant is not None else "")

                nom = c1.text_input("Nom Article", value=val_nom)
                cat = c2.text_input("Catégorie", value=val_cat)
                prix_a = c3.number_input("Prix Achat FC", min_value=0.0, value=val_prix_a)

                data_insert = {
                    "nom_article": str(nom),
                    "categorie": str(cat),
                    "prix_achat": float(prix_a)
                }

                if "prix_vente" in colonnes_articles:
                    prix_v = c1.number_input("Prix Vente FC", min_value=0.0, value=val_prix_v)
                    data_insert["prix_vente"] = float(prix_v)
                if "stock" in colonnes_articles:
                    stock = c2.number_input("Stock", min_value=0, value=val_stock)
                    data_insert["stock"] = int(stock)
                if "code_barre" in colonnes_articles:
                    code = c3.text_input("Code-Barres/QR", value=val_code, placeholder="Scanne ou tape le code")
                    if code:
                        data_insert["code_barre"] = str(code)

                if st.form_submit_button("💾 Ajouter/Modifier Article"):
                    try:
                        if article_existant is not None:
                            supabase.table("articles").update(data_insert).eq("id", int(article_existant['id'])).execute()
                            st.success("✅ Article modifié")
                        else:
                            supabase.table("articles").insert(data_insert).execute()
                            st.success("✅ Article ajouté")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout/modif")
                        st.code(repr(e))

        st.divider()
        st.subheader("📋 Liste des Articles - Modifier/Supprimer")

        if df_articles.empty:
            st.info("Aucun article")
        else:
            for _, row in df_articles.iterrows():
                with st.expander(f"{row['nom_article']} - {row.get('categorie','')} - {row.get('stock',0)} unités"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        new_nom = st.text_input("Nom", value=row['nom_article'], key=f"nom_{row['id']}")
                        new_cat = st.text_input("Catégorie", value=row.get('categorie',''), key=f"cat_{row['id']}")

                    data_update = {
                        "nom_article": str(new_nom),
                        "categorie": str(new_cat)
                    }

                    with c2:
                        if "prix_achat" in colonnes_articles:
                            new_prix_a = st.number_input("Prix Achat", value=float(row.get('prix_achat',0)), key=f"pa_{row['id']}")
                            data_update["prix_achat"] = float(new_prix_a)
                        if "prix_vente" in colonnes_articles:
                            new_prix_v = st.number_input("Prix Vente", value=float(row.get('prix_vente',0)), key=f"pv_{row['id']}")
                            data_update["prix_vente"] = float(new_prix_v)

                    with c3:
                        if "stock" in colonnes_articles:
                            new_stock = st.number_input("Stock", value=int(row.get('stock',0)), key=f"stock_{row['id']}")
                            data_update["stock"] = int(new_stock)
                        if "code_barre" in colonnes_articles:
                            new_code = st.text_input("Code-barres", value=row.get('code_barre',''), key=f"code_{row['id']}")
                            if new_code:
                                data_update["code_barre"] = str(new_code)

                    c1, c2 = st.columns(2)
                    if c1.button("✏️ Modifier", key=f"mod_art_{row['id']}", width="stretch"):
                        try:
                            supabase.table("articles").update(data_update).eq("id", int(row['id'])).execute()
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
                    df_voitures_filtre = df_voitures

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

            df_filtre_fact = df_compta_sorted[(df_compta_sorted['date'] >= date_debut) & (df_compta_sorted['date'] <= date_fin)]

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
                st.markdown("### Nouveaux mots de passe")
                c1, c2, c3 = st.columns(3)

                new_pdg = c1.text_input("Nouveau MDP PDG", type="password", value=passwords_db.get("PDG",""))
                new_gerante = c2.text_input("Nouveau MDP Gérante", type="password", value=passwords_db.get("GERANTE",""))
                new_user = c3.text_input("Nouveau MDP Utilisateur", type="password", value=passwords_db.get("UTILISATEUR",""))

                if st.form_submit_button("💾 Sauvegarder les Mots de Passe", type="primary"):
                    try:
                        if new_pdg:
                            supabase.table("utilisateurs").update({"password": new_pdg}).eq("role", "PDG").execute()
                        if new_gerante:
                            supabase.table("utilisateurs").update({"password": new_gerante}).eq("role", "GERANTE").execute()
                        if new_user:
                            supabase.table("utilisateurs").update({"password": new_user}).eq("role", "UTILISATEUR").execute()

                        st.success("✅ Mots de passe mis à jour dans Supabase")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur mise à jour")
                        st.code(repr(e))

            st.divider()
            st.subheader("👥 Liste des Utilisateurs")
            st.dataframe(df_utilisateurs[['nom', 'role']], use_container_width=True, hide_index=True)
