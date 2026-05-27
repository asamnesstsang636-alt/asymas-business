import streamlit as st
import pandas as pd
st.set_page_config(page_title="ASYMAS BUSINESS", page_icon="🌾", layout="wide", initial_sidebar_state="auto")
st.markdown('<meta name="mobile-web-app-capable" content="yes">', unsafe_allow_html=True)

from supabase import create_client, Client
from datetime import date, datetime, timedelta
from fpdf import FPDF
import base64, io, qrcode, tempfile, os, json
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from streamlit_qrcode_scanner import qrcode_scanner

# === CONFIG SUPABASE ===
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === FONCTIONS ===
@st.cache_data(ttl=60)
def load_table(table_name):
    try:
        data = supabase.table(table_name).select("*").order("id", desc=True).execute()
        return pd.DataFrame(data.data)
    except Exception as e:
        st.error(f"Erreur {table_name}"); st.code(repr(e)); return pd.DataFrame()

@st.cache_data(ttl=300)
def get_table_columns(table_name):
    try:
        test = supabase.table(table_name).select("*").limit(1).execute()
        return list(test.data[0].keys()) if test.data else []
    except: return []

@st.cache_data(ttl=10)
def load_passwords():
    try:
        data = supabase.table("utilisateurs").select("nom,role,password,permissions,categories_autorisees").execute()
        passwords, perms = {}, {}
        for user in data.data:
            passwords[user['role']] = user['password']
            perms[user['role']] = {'permissions': user.get('permissions', {}), 'categories_autorisees': user.get('categories_autorisees', [])}
        st.session_state.permissions_db = perms; return passwords
    except:
        st.session_state.permissions_db = {}; return {"PDG":"tsang2024","GERANTE":"asiya2024","UTILISATEUR":"basam2024"}

def safe_pdf_txt(txt):
    if txt is None or pd.isna(txt): return ""
    txt = str(txt).replace('—','-').replace('–','-').replace('’',"'").replace('“','"').replace('”','"').replace('•','-').replace('…','...')
    return ''.join(c if ord(c)<128 else '?' for c in txt).replace('\n',' ').strip()

def generer_pdf_facture(numero, type_op, client, details_list, montant, devise, tel_client="+243...", periode="", type_facture="Simple"):
    pdf = FPDF(); pdf.add_page(); pdf.set_auto_page_break(auto=False, margin=10)
    pdf.set_fill_color(20,50,40); pdf.rect(0,0,210,35,'F'); pdf.set_text_color(255,255,255)
    pdf.set_font("Arial","B",20); pdf.set_xy(10,8); pdf.cell(0,10,"ASYMAS BUSINESS",ln=True)
    pdf.set_font("Arial","",9); pdf.set_xy(10,16); pdf.cell(0,5,"Beni, Nord-Kivu, RDC | Tel: +243 995 105 623",ln=True)
    pdf.set_xy(10,21); pdf.cell(0,5,"Email: asamnesstsang636@gmail.com",ln=True)
    pdf.set_font("Arial","B",10); pdf.set_xy(150,8); pdf.cell(50,6,"FACTURE N" if type_facture=="Simple" else "PROFORMA N",ln=True,align="R")
    pdf.set_font("Arial","",10); pdf.set_xy(150,14); pdf.cell(50,6,safe_pdf_txt(numero),ln=True,align="R")
    pdf.set_font("Arial","",9); pdf.set_xy(150,20); pdf.cell(50,6,f"Date: {date.today().strftime('%d/%m/%Y')}",ln=True,align="R")
    y_pos=45; pdf.set_text_color(0,0,0); pdf.set_fill_color(255,204,0); pdf.set_font("Arial","B",14)
    pdf.set_xy(10,y_pos); pdf.cell(0,10,f"{type_facture.upper()} {safe_pdf_txt(type_op.upper())}",ln=True,fill=True); y_pos+=15
    pdf.set_font("Arial","B",10); pdf.set_draw_color(0,0,0); pdf.set_xy(10,y_pos)
    pdf.cell(85,7,"FACTURE A:",1,0,'L'); pdf.cell(10,7,"",0,0); pdf.cell(85,7,"DETAILS PAIEMENT:",1,1,'L'); y_pos+=7
    pdf.set_font("Arial","",9); pdf.set_xy(10,y_pos); pdf.cell(85,6,f"Client: {safe_pdf_txt(client)}",'LR',0,'L')
    pdf.cell(10,6,"",0,0); pdf.cell(85,6,"M-Pesa: +243817264448",'LR',1,'L'); y_pos+=6
    pdf.set_xy(10,y_pos); pdf.cell(85,6,f"Tel: {safe_pdf_txt(tel_client)}",'LR',0,'L'); pdf.cell(10,6,"",0,0)
    pdf.cell(85,6,"Echeance: Immediate",'LR',1,'L'); y_pos+=6
    pdf.set_xy(10,y_pos); pdf.cell(85,6,f"Date emission: {date.today().strftime('%d/%m/%Y')}",'LRB',0,'L')
    pdf.cell(10,6,"",0,0); pdf.cell(85,6,"",'LRB',1,'L'); y_pos+=14
    pdf.set_fill_color(0,102,0); pdf.set_text_color(255,255,255); pdf.set_font("Arial","B",10)
    pdf.set_xy(10,y_pos); pdf.cell(115,8,"DESIGNATION",1,0,'C',True); pdf.cell(25,8,"QTE",1,0,'C',True)
    pdf.cell(40,8,f"MONTANT ({safe_pdf_txt(devise)})",1,1,'C',True); y_pos+=8; pdf.set_text_color(0,0,0); pdf.set_font("Arial","",9)
    for item in details_list if isinstance(details_list,list) else [{"nom":details_list,"qte":1,"pu":montant}]:
        if y_pos>240: pdf.add_page(); y_pos=30
        nom=safe_pdf_txt(item.get('nom','')); qte=item.get('qte',1); pu=item.get('pu',item.get('prix',0)); montant_item=pu*qte
        pdf.set_xy(10,y_pos); pdf.cell(115,7,nom,1,0,'L'); pdf.cell(25,7,str(qte),1,0,'C'); pdf.cell(40,7,f"{montant_item:,.0f}",1,1,'R'); y_pos+=7
    if periode:
        if y_pos>240: pdf.add_page(); y_pos=30
        pdf.set_xy(10,y_pos); pdf.cell(115,7,f"Periode: {safe_pdf_txt(periode)}",1,0,'L'); pdf.cell(25,7,"",1,0,'C'); pdf.cell(40,7,"",1,1,'R'); y_pos+=7
    pdf.set_fill_color(255,204,0); pdf.set_font("Arial","B",11); pdf.set_xy(10,y_pos)
    pdf.cell(140,10,"MONTANT TOTAL A PAYER",1,0,'R',True); pdf.cell(40,10,f"{montant:,.0f} {safe_pdf_txt(devise)}",1,1,'R',True); y_pos+=15
    if y_pos>220: pdf.add_page(); y_pos=30
    pdf.set_xy(10,y_pos); pdf.set_font("Arial","B",10); pdf.cell(0,8,"SIGNATURE RESPONSABLE:",ln=True); y_pos+=11
    pdf.set_draw_color(0,0,0); pdf.line(10,y_pos,100,y_pos); y_pos+=1; pdf.set_font("Arial","",9)
    pdf.set_xy(10,y_pos); pdf.cell(90,5,"Ing. SAMY TSANGYA",ln=True); y_pos+=5; pdf.set_xy(10,y_pos); pdf.cell(90,5,"Tel: +243 995 105 623",ln=True)
    y_pos+=5; pdf.set_xy(10,y_pos); pdf.cell(90,5,"Beni, Nord-Kivu, RDC",ln=True); y_pos+=10
    pdf.set_font("Arial","I",10); pdf.set_text_color(0,102,0); pdf.set_xy(10,y_pos)
    pdf.cell(0,6,"Merci pour votre confiance! ASYMAS BUSINESS - Votre partenaire de croissance",ln=True,align="C")
    return bytes(pdf.output(dest='S'))

def creer_facture_auto(type_op, client, details, montant, devise="FC", details_list=None, tel="+243...", periode="", type_facture="Simple"):
    numero_facture=f"AS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if details_list is None: details_list=[{"nom":details,"qte":1,"pu":montant}]
    pdf_bytes=generer_pdf_facture(numero_facture,type_op,client,details_list,montant,devise,tel,periode,type_facture)
    try:
        colonnes_compta=get_table_columns("compta")
        data_compta={"type":"Revenu","description":str(f"{type_op} - {client} - {details}"),"montant":float(montant),"date":str(date.today()),"utilisateur":st.session_state.user_name}
        if "categorie" in colonnes_compta: data_compta["categorie"]=str(type_op)
        if "devise" in colonnes_compta: data_compta["devise"]=str(devise)
        if "numero_facture" in colonnes_compta: data_compta["numero_facture"]=str(numero_facture)
        if "details" in colonnes_compta: data_compta["details"]=json.dumps(details_list)
        supabase.table("compta").insert(data_compta).execute(); st.toast(f"✅ Enregistré par {st.session_state.user_name}",icon="✅")
    except Exception as e: st.error("❌ ERREUR INSERTION COMPTA"); st.code(repr(e))
    return numero_facture,pdf_bytes

def generer_excel_pro(df_data,titre="Relevé Comptable",total_revenu=0,total_depense=0,solde=0):
    output=io.BytesIO()
    with pd.ExcelWriter(output,engine='openpyxl') as writer:
        df_data.to_excel(writer,sheet_name='Releve',index=False,startrow=6)
        workbook=writer.book; worksheet=writer.sheets['Releve']
        worksheet.merge_cells('A1:F1'); worksheet['A1']='ASYMAS BUSINESS'
        worksheet['A1'].font=Font(size=20,bold=True,color='006600'); worksheet['A1'].alignment=Alignment(horizontal='center')
        worksheet.merge_cells('A2:F2'); worksheet['A2']='Beni, Nord-Kivu, RDC | Tel: +243 995 105 623 | asamnesstsang636@gmail.com'
        worksheet['A2'].font=Font(size=10,italic=True); worksheet['A2'].alignment=Alignment(horizontal='center')
        worksheet.merge_cells('A3:F3'); worksheet['A3']=f'{titre.upper()} - Edité le {date.today().strftime("%d/%m/%Y")}'
        worksheet['A3'].font=Font(size=14,bold=True,color='FF6600'); worksheet['A3'].alignment=Alignment(horizontal='center')
        worksheet.merge_cells('A4:F4'); worksheet['A4']=f'Total Revenus: {total_revenu:,.0f} FC | Total Dépenses: {total_depense:,.0f} FC | Solde: {solde:,.0f} FC'
        worksheet['A4'].font=Font(size=11,bold=True); worksheet['A4'].alignment=Alignment(horizontal='center')
        worksheet['A4'].fill=PatternFill(start_color='FFCC00',end_color='FFCC00',fill_type='solid')
        header_fill=PatternFill(start_color='006600',end_color='006600',fill_type='solid'); header_font=Font(bold=True,color='FFFFFF')
        thin_border=Border(left=Side(style='thin'),right=Side(style='thin'),top=Side(style='thin'),bottom=Side(style='thin'))
        for col in range(1,len(df_data.columns)+1):
            cell=worksheet.cell(row=7,column=col); cell.fill=header_fill; cell.font=header_font
            cell.alignment=Alignment(horizontal='center'); cell.border=thin_border
        for row in range(7,len(df_data)+8):
            for col in range(1,len(df_data.columns)+1):
                worksheet.cell(row=row,column=col).border=thin_border; worksheet.cell(row=row,column=col).alignment=Alignment(horizontal='left')
        for col in range(1,len(df_data.columns)+1): worksheet.column_dimensions[get_column_letter(col)].width=18
    return output.getvalue()

# === CSS GLOBAL ===
st.markdown("""
<style>
#MainMenu,header,.stAppToolbar,[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stHeader"],footer,.stDeployButton{display:none!important;}
h1,h2,h3{color:#00ff41!important;font-size:2.2rem!important;font-weight:900!important;padding:10px 0!important;border-bottom:3px solid #00ff41!important;margin-bottom:20px!important;}
div[data-testid="stMetricValue"]{color:#00ff41!important;}
.stButton>button{background-color:#00ff41!important;color:black!important;font-weight:bold;border:none;}
</style>
""",unsafe_allow_html=True)

passwords_db=load_passwords()
if 'user_role' not in st.session_state: st.session_state.user_role=None; st.session_state.user_name=None; st.session_state.user_perms={}; st.session_state.user_cats=[]

if st.session_state.user_role is None:
    st.markdown("# 🔐 ASYMAS BUSINESS - CONNEXION")
    col1,col2,col3=st.columns([1,2,1])
    with col2:
        st.markdown("### Choisissez votre profil :")
        df_users_login=load_table("utilisateurs")
        options_login=["-- Sélectionner --"]+[f"{row['nom']} - {row['role']}" for _,row in df_users_login.iterrows()] if not df_users_login.empty else ["-- Sélectionner --","PDG TSANG","Gérante ASIYA","BASAM"]
        profil=st.selectbox("Utilisateur",options_login); password=st.text_input("Mot de passe",type="password",key="pwd")
        if st.button("SE CONNECTER",width="stretch",type="primary"):
            if profil!="-- Sélectionner --":
                nom_connect=profil.split(" - ")[0]
                df_users_login=pd.DataFrame(supabase.table("utilisateurs").select("id,nom,role,password,permissions,categories_autorisees").execute().data)
                user_data=df_users_login[df_users_login['nom']==nom_connect]
                if not user_data.empty and password==user_data.iloc[0]['password']:
                    st.session_state.user_role=user_data.iloc[0]['role']; st.session_state.user_name=user_data.iloc[0]['nom']
                    st.session_state.user_perms=user_data.iloc[0].get('permissions',{}); st.session_state.user_cats=user_data.iloc[0].get('categories_autorisees',[]); st.rerun()
                else: st.error("Profil ou mot de passe incorrect")
    st.stop()

with st.sidebar:
    if 'theme_choisi' not in st.session_state: st.session_state.theme_choisi="Sombre ASYMAS"
    theme=st.selectbox("🎨",["Sombre ASYMAS","Bleu Pro","Vert Agri","Noir Luxe"],key="theme_choisi",label_visibility="collapsed")
    if st.button("🚪 Déconnexion",use_container_width=True): st.session_state.user_role=None; st.session_state.user_name=None; st.session_state.user_perms={}; st.session_state.user_cats=[]; st.rerun()

if theme=="Sombre ASYMAS": st.markdown("""<style>.stApp{background:#0E1117;color:#E0E0E0}h1,h2,h3{color:#14B814!important}</style>""",unsafe_allow_html=True)
elif theme=="Bleu Pro": st.markdown("""<style>.stApp{background:#0A1929;color:#E3F2FD}h1,h2,h3{color:#2196F3!important}</style>""",unsafe_allow_html=True)
elif theme=="Vert Agri": st.markdown("""<style>.stApp{background:#1B2A1B;color:#E8F5E9}h1,h2,h3{color:#4CAF50!important}</style>""",unsafe_allow_html=True)
elif theme=="Noir Luxe": st.markdown("""<style>.stApp{background:#000;color:#FFF}h1,h2,h3{color:#FFD700!important}</style>""",unsafe_allow_html=True)

df_biens=load_table("biens"); df_articles=load_table("articles"); df_voitures=load_table("voitures")
df_compta=load_table("compta"); df_factures=load_table("factures_proforma"); df_devis=load_table("devis"); df_utilisateurs=load_table("utilisateurs")

if 'montant' not in df_compta.columns: df_compta['montant']=0
if 'type' not in df_compta.columns: df_compta['type']='Inconnu'
if 'date' in df_compta.columns: df_compta['date']=pd.to_datetime(df_compta['date'],errors='coerce'); df_compta=df_compta.sort_values('date',ascending=False)

st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
st.markdown("### Agriculture • Commerce • Immobilier • Automobile • Beni RDC")

with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.user_name}")
    st.markdown(f"**Rôle : {st.session_state.user_role}**")
    st.info("ASYMAS BUSINESS v2.6")
    if st.button("🔄 Actualiser",key="btn_save"): st.cache_data.clear(); st.rerun()

perms=st.session_state.user_perms
if isinstance(perms,str):
    try: perms=json.loads(perms)
    except: perms={}

tabs_dispo=[]
if st.session_state.user_role=="PDG" or perms.get('dashboard',True): tabs_dispo.append("📊 Dashboard")
if st.session_state.user_role=="PDG" or perms.get('commerce',True): tabs_dispo.append("🛍️ Commerce")
if st.session_state.user_role=="PDG" or perms.get('stock',False): tabs_dispo.append("📦 Gestion Stock")
if st.session_state.user_role=="PDG" or perms.get('immobilier',False): tabs_dispo.append("🏠 Immobilier")
if st.session_state.user_role=="PDG" or perms.get('automobile',False): tabs_dispo.append("🚗 Automobile")
if st.session_state.user_role=="PDG" or perms.get('parc',False): tabs_dispo.append("🚘 Gestion Parc")
if st.session_state.user_role=="PDG" or perms.get('comptabilite',False): tabs_dispo.append("💰 Comptabilité")
if st.session_state.user_role=="PDG" or perms.get('factures',False): tabs_dispo.append("📄 Factures")
if st.session_state.user_role=="PDG" or perms.get('devis_industriel',False) or perms.get('devis_batiment',False): tabs_dispo.append("📋 Devis")
if st.session_state.user_role=="PDG" or perms.get('users',False): tabs_dispo.append("👥 Utilisateurs")
if not tabs_dispo: tabs_dispo=["📊 Dashboard","🛍️ Commerce"]

tabs=st.tabs(tabs_dispo); tab_map={name:tab for name,tab in zip(tabs_dispo,tabs)}

# === DASHBOARD ===
if "📊 Dashboard" in tab_map:
    with tab_map["📊 Dashboard"]:
        col1,col2,col3,col4=st.columns(4)
        col1.metric("🏠 Biens",len(df_biens)); col2.metric("📦 Articles",len(df_articles)); col3.metric("🚗 Voitures",len(df_voitures))
        revenus=df_compta[df_compta['type']=='Revenu']['montant'].sum() if not df_compta.empty and 'type' in df_compta.columns else 0
        col4.metric("💰 Revenus",f"{revenus:,.0f} FC")

# === COMMERCE AVEC STYLE HOLOGRAPHIQUE ===
if "🛍️ Commerce" in tab_map:
    with tab_map["🛍️ Commerce"]:
        # Bannière holographique style image
        st.markdown("""
        <div style="text-align:center;padding:30px 0;background:linear-gradient(135deg,#000 0%,#1a1a00 100%);border-radius:20px;margin-bottom:30px;">
            <div style="width:200px;height:200px;margin:0 auto 30px;border-radius:50%;
                background:radial-gradient(circle,#FFD700 0%,#FFA500 60%,#FF8C00 100%);
                box-shadow:0 0 50px #FFD700,0 0 100px #FFA500;display:flex;align-items:center;justify-content:center;
                font-size:90px;animation:pulse 2s ease-in-out infinite;border:3px solid #FFD700;">🛒</div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;max-width:600px;margin:0 auto;padding:0 20px;">
                <div style="grid-column:2;"><div style="color:#FFD700;font-size:45px;text-shadow:0 0 20px #FFD700;">🏪</div>
                    <div style="color:#FFD700;font-size:12px;margin-top:5px;">BOUTIQUE</div></div>
                <div><div style="color:#FFD700;font-size:45px;text-shadow:0 0 20px #FFD700;">📶</div>
                    <div style="color:#FFD700;font-size:12px;margin-top:5px;">CONNECTÉ</div></div>
                <div><div style="color:#FFD700;font-size:45px;text-shadow:0 0 20px #FFD700;">🧾</div>
                    <div style="color:#FFD700;font-size:12px;margin-top:5px;">CAISSE</div></div>
                <div><div style="color:#FFD700;font-size:45px;text-shadow:0 0 20px #FFD700;">@</div>
                    <div style="color:#FFD700;font-size:12px;margin-top:5px;">EMAIL</div></div>
                <div><div style="color:#FFD700;font-size:45px;text-shadow:0 0 20px #FFD700;">📢</div>
                    <div style="color:#FFD700;font-size:12px;margin-top:5px;">PUB</div></div>
                <div><div style="color:#FFD700;font-size:45px;text-shadow:0 0 20px #FFD700;">@</div>
                    <div style="color:#FFD700;font-size:12px;margin-top:5px;">EMAIL</div></div>
                <div style="grid-column:2;"><div style="color:#FFD700;font-size:45px;text-shadow:0 0 20px #FFD700;">🚚</div>
                    <div style="color:#FFD700;font-size:12px;margin-top:5px;">LIVRAISON</div></div>
            </div>
        </div>
        <style>@keyframes pulse{0%,100%{transform:scale(1);box-shadow:0 0 50px #FFD700,0 0 100px #FFA500;}
            50%{transform:scale(1.08);box-shadow:0 0 70px #FFD700,0 0 140px #FFA500;}}</style>
        """,unsafe_allow_html=True)

        st.markdown("## 🛍️ Commerce - Point de Vente")
        if 'panier_commerce' not in st.session_state: st.session_state.panier_commerce=[]
        if 'vente_finie' not in st.session_state: st.session_state.vente_finie=False
        if 'pdf_data' not in st.session_state: st.session_state.pdf_data=None
        if 'num_fact' not in st.session_state: st.session_state.num_fact=None
        if 'client_com_nom' not in st.session_state: st.session_state.client_com_nom=""
        if 'client_com_tel' not in st.session_state: st.session_state.client_com_tel="+243..."
        if 'last_qr' not in st.session_state: st.session_state.last_qr=""

        col_gauche,col_droite=st.columns([2,1])
        with col_gauche:
            st.subheader("👤 Client")
            st.session_state.client_com_nom=st.text_input("Nom Client",value=st.session_state.client_com_nom,key="nom_client_c")
            st.session_state.client_com_tel=st.text_input("Téléphone Client",value=st.session_state.client_com_tel,key="tel_client_c")
            st.subheader("🔍 Scanner QR Code")
            col_scan1,col_scan2=st.columns([2,1])
            with col_scan1: qr_code=qrcode_scanner(key='qr_commerce_unique')
            with col_scan2: recherche_manuelle=st.text_input("🔎 Recherche manuelle",placeholder="Tape le nom...",key="search_man_c")
            if qr_code and qr_code!=st.session_state.last_qr: st.session_state.last_qr=qr_code; st.rerun()

            df_articles_filtre=df_articles[df_articles['stock']>0].copy()
            if qr_code:
                qr_clean=str(qr_code).strip().upper()
                df_articles_filtre=df_articles_filtre[df_articles_filtre['code_qr'].astype(str).str.strip().str.upper()==qr_clean]
                if not df_articles_filtre.empty: st.success(f"✅ QR Trouvé : {df_articles_filtre.iloc[0]['nom_article']}")
                else: st.error(f"❌ QR {qr_code} : Produit introuvable")
            elif recherche_manuelle:
                mask=df_articles_filtre['nom_article'].str.contains(recherche_manuelle,case=False,na=False)
                df_articles_filtre=df_articles_filtre[mask]

            if df_articles_filtre.empty: st.warning("⚠️ Aucun produit disponible")
            else:
                st.success(f"✅ {len(df_articles_filtre)} produit(s) disponible(s)")
                options_articles=[]
                for _,p in df_articles_filtre.iterrows():
                    qr_txt=f" | QR:{p['code_qr']}" if 'code_qr' in p and p['code_qr'] else ""
                    prix_usd=f" | {p['prix_vente_usd']:,.2f}$" if 'prix_vente_usd' in p else ""
                    options_articles.append(f"{p['nom_article']} | Stock:{int(p['stock'])} | {p['prix_vente']:,.0f} FC{prix_usd}{qr_txt} | ID:{p['id']}")
                article_choisi=st.selectbox("Sélectionne le produit",options_articles,key="select_article_unique")
                if article_choisi:
                    id_choisi=int(article_choisi.split("ID:")[1]); p=df_articles_filtre[df_articles_filtre['id']==id_choisi].iloc[0]
                    c1,c2,c3=st.columns(3); qte_max=int(p['stock']); qte=c1.number_input("Quantité",min_value=1,max_value=qte_max,value=1,key="qte_c_unique")
                    c2.metric("Stock dispo",qte_max); c3.metric("Prix unitaire",f"{p['prix_vente']:,.0f} FC")
                    st.info(f"**{p['nom_article']}** | Catégorie: {p.get('categorie','N/A')} | QR: {p.get('code_qr','N/A')}")
                    if st.button("🛒 AJOUTER AU PANIER",type="primary",width="stretch",key="add_article_unique"):
                        existant=next((item for item in st.session_state.panier_commerce if item['id']==int(p['id'])),None)
                        if existant:
                            if existant['qte']+qte<=qte_max: existant['qte']+=qte; st.success(f"Panier mis à jour: {existant['qte']}x")
                            else: st.error(f"Stock insuffisant! Max dispo: {qte_max}")
                        else:
                            st.session_state.panier_commerce.append({"id":int(p['id']),"nom":str(p['nom_article']),"pu":float(p['prix_vente']),
                                "qte":int(qte),"code_qr":p.get('code_qr',''),"stock_max":qte_max}); st.success("Ajouté au panier"); st.rerun()
        with col_droite:
            st.subheader("🛒 Panier")
            if st.session_state.vente_finie and st.session_state.pdf_data:
                st.success("✅ Vente enregistrée!")
                st.download_button("📥 Télécharger Facture PDF",data=st.session_state.pdf_data,file_name=f"{st.session_state.num_fact}.pdf",mime="application/pdf",width="stretch")
                pdf_b64=base64.b64encode(st.session_state.pdf_data).decode()
                st.components.v1.html(f"""<button onclick="printPDF()" style="width:100%;padding:10px;background:#00ff41;color:black;font-weight:bold;border:none;border-radius:5px;cursor:pointer;margin-top:10px;">🖨️ IMPRIMER LA FACTURE</button>
                    <script>function printPDF(){{const pdfData='data:application/pdf;base64,{pdf_b64}';const win=window.open('','_blank');
                    win.document.write('<iframe src="'+pdfData+'" width="100%" height="100%" style="border:none;"></iframe>');
                    win.document.close();setTimeout(()=>{{win.print();}},1000);}}</script>""",height=60)
                if st.button("NOUVELLE VENTE",width="stretch"):
                    st.session_state.vente_finie=False; st.session_state.pdf_data=None; st.session_state.num_fact=None
                    st.session_state.client_com_nom=""; st.session_state.last_qr=""; st.rerun()
            elif not st.session_state.panier_commerce: st.info("Panier vide")
            else:
                total_panier=0
                for i,item in enumerate(st.session_state.panier_commerce):
                    col1,col2,col3=st.columns([4,2,1]); col1.write(f"**{item['nom']}**")
                    col2.write(f"Qté: {item['qte']} | {item['pu']:,.0f} FC")
                    if col3.button("❌",key=f"d_{i}"): st.session_state.panier_commerce.pop(i); st.rerun()
                    total_panier+=item['qte']*item['pu']
                st.markdown(f"### Total: {total_panier:,.0f} FC"); st.divider()
                if st.button("💾 FINALISER VENTE & FACTURE",width="stretch",type="primary"):
                    if not st.session_state.client_com_nom: st.error("Nom du client obligatoire!")
                    else:
                        try:
                            num_fact=f"VTE-{datetime.now().strftime('%Y%m%d%H%M%S')}"; details_list=[]
                            for item in st.session_state.panier_commerce:
                                supabase.table("ventes").insert({"numero_facture":num_fact,"client_nom":st.session_state.client_com_nom,
                                    "article_id":item['id'],"quantite":item['qte'],"prix_unitaire":item['pu'],"total":item['qte']*item['pu']}).execute()
                                stock_actuel=df_articles[df_articles['id']==item['id']]['stock'].iloc[0]
                                supabase.table("articles").update({"stock":int(stock_actuel-item['qte'])}).eq("id",item['id']).execute()
                                details_list.append({"nom":item['nom'],"qte":item['qte'],"pu":item['pu'],"total":item['qte']*item['pu']})
                            details_json=json.dumps(details_list)
                            supabase.table("compta").insert({"date":str(date.today()),"type":"Revenu","categorie":"Vente Commerce",
                                "description":f"Vente - {st.session_state.client_com_nom}","montant":float(total_panier),"devise":"FC",
                                "numero_facture":num_fact,"details":details_json,"utilisateur":st.session_state.user_name}).execute()
                            pdf_bytes=generer_pdf_facture(num_fact,"Vente Commerce",st.session_state.client_com_nom,details_list,total_panier,"FC",st.session_state.client_com_tel)
                            st.session_state.pdf_data=pdf_bytes; st.session_state.num_fact=num_fact; st.session_state.vente_finie=True
                            st.session_state.panier_commerce=[]; st.cache_data.clear(); st.rerun()
                        except Exception as e: st.error("Erreur finalisation vente"); st.code(repr(e))

# === GESTION STOCK ===
if "📦 Gestion Stock" in tab_map:
    with tab_map["📦 Gestion Stock"]:
        st.markdown("## 📦 Gestion Stock Commerce")
        tab_stock,tab_ajout,tab_mvt,tab_pertes=st.tabs(["📊 Stock Actuel","➕ Ajouter Article","📈 Mouvements","⚠️ Pertes"])
        with tab_stock:
            if df_articles.empty: st.info("Aucun article")
            else:
                for _,row in df_articles.iterrows():
                    col1,col2,col3,col4=st.columns([3,1,1,1])
                    with col1: st.write(f"**{row['nom_article']}** - {row.get('categorie','')} - QR:{row.get('code_qr','N/A')}")
                    with col2: st.error(f"⚠️ Stock: {int(row.get('stock',0))}") if int(row.get('stock',0))<5 else st.success(f"✅ Stock: {int(row.get('stock',0))}")
                    with col3: st.write(f"PA: {row.get('prix_achat',0):,.0f}")
                    with col4: st.write(f"PV: {row.get('prix_vente',0):,.0f} FC")
        with tab_ajout:
            with st.form("form_article_com",clear_on_submit=True):
                c1,c2,c3=st.columns(3); nom=c1.text_input("Nom Article"); cat=c2.text_input("Catégorie"); code_qr=c3.text_input("Code QR")
                c1,c2,c3=st.columns(3); prix_achat_fc=c1.number_input("Prix Achat FC",min_value=0.0); prix_vente_fc=c2.number_input("Prix Vente FC",min_value=0.0)
                                prix_vente_usd=c3.number_input("Prix Vente $",min_value=0.0)
                stock=c1.number_input("Stock Initial",min_value=0)
                if st.form_submit_button("💾 Ajouter Article"):
                    try:
                        data_insert={"nom_article":str(nom),"categorie":str(cat),"prix_achat":float(prix_achat_fc),"prix_vente":float(prix_vente_fc),"stock":int(stock),"code_qr":str(code_qr) if code_qr else None}
                        colonnes_articles=get_table_columns("articles")
                        if "prix_vente_usd" in colonnes_articles: data_insert["prix_vente_usd"]=float(prix_vente_usd)
                        supabase.table("articles").insert(data_insert).execute()
                        st.success(f"Article {nom} ajouté"); st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error("Erreur ajout"); st.code(repr(e))

        with tab_mvt:
            st.subheader("📈 Mouvements de Stock Commerce")
            try: mvts=supabase.table('mouvements_stock').select("*").order("created_at",desc=True).limit(50).execute().data
            except: mvts=[]
            if not mvts: st.info("Aucun mouvement enregistré")
            else: df_mvt=pd.DataFrame(mvts); st.dataframe(df_mvt[['article_nom','type','quantite','motif','created_by','created_at']],use_container_width=True,hide_index=True)

        with tab_pertes:
            st.subheader("⚠️ Déclarer Perte/Casse Article Commerce")
            articles_dispo=df_articles[df_articles['stock']>0].copy() if not df_articles.empty else pd.DataFrame()
            if articles_dispo.empty: st.warning("Aucun article en stock pour déclarer une perte")
            else:
                col1,col2=st.columns(2)
                with col1:
                    article_dict={f"{a['nom_article']} - Stock:{int(a['stock'])}":a for _,a in articles_dispo.iterrows()}
                    article_choisi=st.selectbox("Article abîmé/perdu",list(article_dict.keys()))
                    qte_perte=st.number_input("Quantité abîmée",min_value=1,max_value=int(article_dict[article_choisi]['stock']) if article_choisi else 1)
                with col2:
                    motif_perte=st.selectbox("Motif",["Casse","Vol","Péremption","Défaut fabrication","Accident","Autre"])
                    detail_perte=st.text_area("Détails",placeholder="Ex: Carton mouillé lors livraison")
                    responsable=st.text_input("Déclaré par",value=st.session_state.user_name)
                if article_choisi:
                    article_data=article_dict[article_choisi]; valeur_perte=qte_perte*float(article_data.get('prix_achat',0))
                    st.error(f"💸 Valeur de la perte : {valeur_perte:,.0f} FC")
                if st.button("🚨 ENREGISTRER LA PERTE",type="primary",width="stretch"):
                    if article_choisi and qte_perte>0:
                        article_data=article_dict[article_choisi]
                        try:
                            nouveau_stock=int(article_data['stock'])-qte_perte
                            supabase.table('articles').update({"stock":nouveau_stock}).eq("id",int(article_data['id'])).execute()
                            supabase.table('mouvements_stock').insert({"article_id":int(article_data['id']),"article_nom":str(article_data['nom_article']),"type":"PERTE","quantite":-int(qte_perte),"motif":f"{motif_perte} - {detail_perte}","valeur":float(valeur_perte),"created_by":responsable,"created_at":datetime.now().isoformat()}).execute()
                            st.success(f"✅ Perte enregistrée. Nouveau stock {article_data['nom_article']}: {nouveau_stock}"); st.cache_data.clear(); st.rerun()
                        except Exception as e: st.error("Erreur enregistrement perte"); st.code(repr(e))
            st.divider(); st.subheader("📋 Historique Pertes Commerce")
            try: pertes=supabase.table('mouvements_stock').select("*").eq("type","PERTE").order("created_at",desc=True).limit(20).execute().data
            except: pertes=[]
            if not pertes: st.info("Aucune perte enregistrée")
            else:
                total_pertes=sum(p.get('valeur',0) for p in pertes); st.metric("💸 TOTAL PERTES COMMERCE",f"{total_pertes:,.0f} FC")
                for p in pertes:
                    with st.expander(f"🔴 {p.get('article_nom')} - {abs(p.get('quantite',0))} - {p.get('created_at','')[:10]}"):
                        col1,col2,col3=st.columns(3)
                        with col1: st.write(f"**Qté perdue:** {abs(p.get('quantite',0))}"); st.write(f"**Valeur:** {p.get('valeur',0):,.0f} FC")
                        with col2: st.write(f"**Motif:** {p.get('motif','N/A')}"); st.write(f"**Par:** {p.get('created_by','N/A')}")
                        with col3:
                            if st.session_state.user_role=="PDG":
                                if st.button("🗑️ Supprimer",key=f"del_perte_com_{p.get('id')}"): supabase.table('mouvements_stock').delete().eq("id",p.get('id')).execute(); st.rerun()

# === IMMOBILIER ===
if "🏠 Immobilier" in tab_map:
    with tab_map["🏠 Immobilier"]:
        st.markdown("## 🏠 Immobilier - Générer Facture")
        nom_client=st.text_input("👤 Nom du client",key="nom_client_bien")
        tel_client=st.text_input("Téléphone Client",value="+243...",key="tel_client_bien")
        col1,col2,col3=st.columns(3)
        with col1: type_bien=st.selectbox("Type",["Maison","Appartement","Bureau","Terrain"],key="type_bien"); adresse=st.text_input("Adresse",key="adresse_bien")
        with col2: prix=st.number_input("💰 Loyer USD",min_value=0.0,key="prix_bien"); electricite=st.number_input("⚡ Électricité USD",min_value=0.0,key="elec_bien")
        with col3: eau=st.number_input("💧 Eau USD",min_value=0.0,key="eau_bien"); duree_contrat=st.text_input("📅 Durée",placeholder="Ex: 6 mois",key="duree_bien")
        total_mensuel=float(prix)+float(electricite)+float(eau); st.info(f"💎 **TOTAL : {total_mensuel:,.2f} USD**")
        if st.button("📄 GÉNÉRER FACTURE PDF",type="primary",width="stretch",key="btn_facture_immo"):
            if nom_client and adresse:
                details_list=[{"nom":f"Loyer {type_bien} | Adresse: {adresse} | Duree: {duree_contrat}","qte":1,"pu":prix},
                              {"nom":f"Electricite | {type_bien} - {adresse}","qte":1,"pu":electricite},
                              {"nom":f"Eau | {type_bien} - {adresse}","qte":1,"pu":eau}]
                details_text=f"LOUER: {type_bien} | Adresse: {adresse} | Duree Contrat: {duree_contrat} | Loyer: {prix} $ | Electricite: {electricite} $ | Eau: {eau} $"
                periode=date.today().strftime("%B %Y")
                num_fact,pdf_bytes=creer_facture_auto("Loyer",nom_client,details_text,total_mensuel,"$",details_list,tel_client,periode,"Proforma")
                st.success(f"✅ Facture générée : {num_fact}")
                st.download_button(label="📥 Télécharger Facture PDF",data=bytes(pdf_bytes),file_name=f"{num_fact}.pdf",mime="application/pdf",width="stretch",key="dl_facture_immo")
                pdf_b64=base64.b64encode(pdf_bytes).decode()
                st.components.v1.html(f"""<button onclick="printPDF()" style="width:100%;padding:10px;background:#00ff41;color:black;font-weight:bold;border:none;border-radius:5px;cursor:pointer;margin-top:10px;">🖨️ IMPRIMER LA FACTURE</button>
                    <script>function printPDF(){{const pdfData='data:application/pdf;base64,{pdf_b64}';const win=window.open('','_blank');
                    win.document.write('<iframe src="'+pdfData+'" width="100%" height="100%" style="border:none;"></iframe>');
                    win.document.close();setTimeout(()=>{{win.print();}},1000);}}</script>""",height=60)
                st.cache_data.clear()
            else: st.error("Nom client + Adresse obligatoires")

# === AUTOMOBILE ===
if "🚗 Automobile" in tab_map:
    with tab_map["🚗 Automobile"]:
        st.markdown("## 🚗 Automobile - Point de Vente")
        if 'panier_voiture' not in st.session_state: st.session_state.panier_voiture=[]
        if 'vente_auto_finie' not in st.session_state: st.session_state.vente_auto_finie=False
        if 'pdf_auto' not in st.session_state: st.session_state.pdf_auto=None
        if 'num_fact_auto' not in st.session_state: st.session_state.num_fact_auto=None
        if 'client_auto_nom' not in st.session_state: st.session_state.client_auto_nom=""
        if 'client_auto_tel' not in st.session_state: st.session_state.client_auto_tel="+243..."
        if df_voitures.empty: st.error("Aucune voiture disponible - Ajoute des voitures dans Gestion Parc")
        else:
            col_gauche,col_droite=st.columns([2,1])
            with col_gauche:
                st.subheader("👤 Client"); st.session_state.client_auto_nom=st.text_input("Nom Client",value=st.session_state.client_auto_nom,key="nom_client_v")
                st.session_state.client_auto_tel=st.text_input("Téléphone Client",value=st.session_state.client_auto_tel,key="tel_client_v")
                st.subheader("🔍 Choisir Voiture")
                search_qr=st.text_input("QR Code, Plaque, Marque ou Modèle",placeholder="Filtre la liste...",key="search_voiture_qr").strip()
                df_voitures_dispo=df_voitures[(df_voitures['statut']=='Disponible')&(df_voitures['quantite']>0)]
                if search_qr:
                    search_clean=search_qr.upper()
                    df_voitures_dispo=df_voitures_dispo[df_voitures_dispo['code_qr'].str.contains(search_clean,case=False,na=False)|df_voitures_dispo['plaque'].str.contains(search_clean,case=False,na=False)|df_voitures_dispo['marque'].str.contains(search_clean,case=False,na=False)|df_voitures_dispo['modele'].str.contains(search_clean,case=False,na=False)]
                if df_voitures_dispo.empty: st.warning("⚠️ Aucune voiture disponible")
                else:
                    st.success(f"✅ {len(df_voitures_dispo)} véhicule(s) disponible(s)")
                    options_voitures=[]
                    for _,v in df_voitures_dispo.iterrows(): options_voitures.append(f"{v['marque']} {v['modele']} {v.get('annee','')} | {v.get('couleur','')} | {v['plaque']} | Stock:{int(v.get('quantite',1))} | {v['prix']:,.0f}$ | ID:{v['id']}")
                    voiture_choisie=st.selectbox("Sélectionne le véhicule",options_voitures,key="select_voiture_unique")
                    if voiture_choisie:
                        id_choisi=int(voiture_choisie.split("ID:")[1]); v=df_voitures_dispo[df_voitures_dispo['id']==id_choisi].iloc[0]
                        c1,c2,c3=st.columns(3); qte_max=int(v.get('quantite',1)); qte=c1.number_input("Quantité",min_value=1,max_value=qte_max,value=1,key=f"qte_v_unique")
                        c2.metric("Stock dispo",qte_max); c3.metric("Prix unitaire",f"{v['prix']:,.0f}$")
                        st.info(f"**{v['marque']} {v['modele']}** | Couleur: {v.get('couleur','N/A')} | Qualité: {v.get('qualite','N/A')} | QR: {v.get('code_qr','N/A')}")
                        if st.button("🛒 AJOUTER AU PANIER",type="primary",width="stretch",key="add_voiture_unique"):
                            existant=next((item for item in st.session_state.panier_voiture if item['id']==int(v['id'])),None)
                            if existant:
                                if existant['qte']+qte<=qte_max: existant['qte']+=qte; st.success(f"Panier mis à jour: {existant['qte']}x")
                                else: st.error(f"Stock insuffisant! Max dispo: {qte_max}")
                            else:
                                st.session_state.panier_voiture.append({"id":int(v['id']),"nom":f"{v['marque']} {v['modele']} {v.get('annee','')}","pu":float(v['prix']),"qte":int(qte),"plaque":v.get('plaque',''),"qualite":v.get('qualite',''),"code_qr":v.get('code_qr',''),"stock_max":qte_max}); st.success("Ajouté au panier"); st.rerun()
            with col_droite:
                st.subheader("🛒 Panier Voiture"); total_voiture=0
                if st.session_state.vente_auto_finie and st.session_state.pdf_auto:
                    st.success(f"✅ Vente validée - {st.session_state.total_auto:,.0f} $"); st.info(f"📄 Facture: {st.session_state.num_fact_auto}")
                    if st.session_state.pdf_auto: st.download_button(label="📥 TÉLÉCHARGER LE PDF",data=bytes(st.session_state.pdf_auto),file_name=f"{st.session_state.num_fact_auto}.pdf",mime="application/pdf",width="stretch",key="dl_facture_auto")
                    pdf_b64=base64.b64encode(st.session_state.pdf_auto).decode()
                    st.components.v1.html(f"""<button onclick="printPDFAuto()" style="width:100%;padding:10px;background:#00ff41;color:black;font-weight:bold;border:none;border-radius:5px;cursor:pointer;margin-top:10px;">🖨️ IMPRIMER LA FACTURE</button>
                        <script>function printPDFAuto(){{const pdfData='data:application/pdf;base64,{pdf_b64}';const win=window.open('','_blank');
                        win.document.write('<iframe src="'+pdfData+'" width="100%" height="100%" style="border:none;"></iframe>');
                        win.document.close();setTimeout(()=>{{win.print();}},1000);}}</script>""",height=60)
                    if st.button("Nouvelle Vente",width="stretch",key="new_vente_auto"):
                        st.session_state.panier_voiture=[]; st.session_state.vente_auto_finie=False; st.session_state.pdf_auto=None; st.session_state.num_fact_auto=None
                        st.session_state.client_auto_nom=""; st.session_state.client_auto_tel="+243..."; st.rerun()
                elif not st.session_state.panier_voiture: st.info("Panier vide")
                else:
                    for idx,item in enumerate(st.session_state.panier_voiture):
                        col1,col2,col3,col4=st.columns([3,1,1,1]); col1.write(f"**{item['nom']}** | {item.get('qualite','')} | {item['plaque']}")
                        col2.write(f"Qté: {item['qte']}"); col3.write(f"{item['pu']*item['qte']:,.2f} $")
                        if col4.button("❌",key=f"del_v_{idx}"): st.session_state.panier_voiture.pop(idx); st.rerun()
                        total_voiture+=item['pu']*item['qte']
                    st.metric("💰 TOTAL VOITURE",f"{total_voiture:,.2f} $"); st.markdown(f"**Client:** {st.session_state.client_auto_nom}"); st.markdown(f"**Tel:** {st.session_state.client_auto_tel}")
                    if st.button("✅ FINALISER VENTE VOITURE",type="primary",width="stretch"):
                        if st.session_state.client_auto_nom and st.session_state.panier_voiture:
                            try:
                                details_list=[{"nom":f"{item['nom']} | {item.get('qualite','')} | {item['plaque']}","qte":item['qte'],"pu":item['pu']} for item in st.session_state.panier_voiture]
                                details_text=" | ".join([f"{item['qte']}x {item['nom']} ({item.get('qualite','')})" for item in st.session_state.panier_voiture])
                                num_fact,pdf_bytes=creer_facture_auto("Vente Voiture",st.session_state.client_auto_nom,details_text,total_voiture,"$",details_list,st.session_state.client_auto_tel,"","Proforma")
                                for item in st.session_state.panier_voiture: supabase.table("voitures").update({"quantite":item['stock_max']-item['qte'],"statut":"Vendue" if item['stock_max']-item['qte']==0 else "Disponible"}).eq("id",item['id']).execute()
                                st.session_state.vente_auto_finie=True; st.session_state.pdf_auto=pdf_bytes; st.session_state.num_fact_auto=num_fact; st.session_state.total_auto=total_voiture; st.session_state.panier_voiture=[]; st.cache_data.clear(); st.rerun()
                            except Exception as e: st.error(f"Erreur finalisation: {e}")
                        else: st.error("Nom client obligatoire - Remplis à gauche")

# === GESTION PARC ===
if "🚘 Gestion Parc" in tab_map:
    with tab_map["🚘 Gestion Parc"]:
        st.markdown("## 🚘 Gestion Parc Automobile & Pertes")
        tab_ajout_v,tab_liste_v,tab_pertes_v=st.tabs(["➕ Ajouter Voiture","📋 Liste Voitures","⚠️ Pertes/Dégâts Voitures"])
        colonnes_voitures=get_table_columns("voitures")
        with tab_ajout_v:
            st.subheader("➕ Ajouter Nouvelle Voiture au Parc")
            with st.form("form_voiture_parc",clear_on_submit=True):
                c1,c2,c3=st.columns(3); marque=c1.text_input("Marque"); modele=c2.text_input("Modèle"); annee=c3.text_input("Année")
                data_insert={"marque":str(marque),"modele":str(modele),"annee":str(annee)}
                if "plaque" in colonnes_voitures: plaque=c1.text_input("Plaque"); data_insert["plaque"]=str(plaque)
                if "couleur" in colonnes_voitures: couleur=c2.text_input("Couleur"); data_insert["couleur"]=str(couleur)
                if "kilometrage" in colonnes_voitures: km=c3.number_input("Kilométrage",min_value=0,value=0); data_insert["kilometrage"]=int(km)
                if "carburant" in colonnes_voitures: carburant=c1.selectbox("Carburant",["Essence","Diesel","Hybride","Électrique"]); data_insert["carburant"]=str(carburant)
                if "boite" in colonnes_voitures: boite=c2.selectbox("Boîte",["Manuelle","Automatique"]); data_insert["boite"]=str(boite)
                if "prix" in colonnes_voitures: prix=c3.number_input("Prix Achat $",min_value=0.0,value=0.0); data_insert["prix"]=float(prix)
                if "statut" in colonnes_voitures: statut=c1.selectbox("Statut",["Disponible","En réparation","Réservée","Vendue"]); data_insert["statut"]=str(statut)
                if "quantite" in colonnes_voitures: quantite=c2.number_input("Quantité en Stock",min_value=1,value=1); data_insert["quantite"]=int(quantite)
                if "qualite" in colonnes_voitures: qualite=c3.selectbox("Qualité",["Neuf","Occasion","Reconditionné"]); data_insert["qualite"]=str(qualite)
                if "code_qr" in colonnes_voitures: code_qr=c1.text_input("Code QR",placeholder="Scanner ou générer"); data_insert["code_qr"]=str(code_qr)
                if st.form_submit_button("💾 Ajouter Voiture"):
                    try: supabase.table("voitures").insert(data_insert).execute(); st.success(f"Voiture {marque} {modele} ajoutée"); st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error("Erreur ajout"); st.code(repr(e))
        with tab_liste_v:
            st.subheader("📋 Liste des Voitures - Modifier/Supprimer")
            if df_voitures.empty: st.info("Aucune voiture")
            else:
                for _,row in df_voitures.iterrows():
                    with st.expander(f"{row['marque']} {row['modele']} - {row.get('plaque','')} - Stock:{row.get('quantite',0)} - {row.get('statut','')}"):
                        c1,c2,c3=st.columns(3)
                        with c1: new_marque=st.text_input("Marque",value=row['marque'],key=f"marque_v_{row['id']}"); new_modele=st.text_input("Modèle",value=row['modele'],key=f"modele_v_{row['id']}"); new_annee=st.text_input("Année",value=row.get('annee',''),key=f"annee_v_{row['id']}")
                        data_update={"marque":str(new_marque),"modele":str(new_modele),"annee":str(new_annee)}
                        with c2:
                            if "plaque" in colonnes_voitures: new_plaque=st.text_input("Plaque",value=row.get('plaque',''),key=f"plaque_v_{row['id']}"); data_update["plaque"]=str(new_plaque)
                            if "couleur" in colonnes_voitures: new_couleur=st.text_input("Couleur",value=row.get('couleur',''),key=f"couleur_v_{row['id']}"); data_update["couleur"]=str(new_couleur)
                            if "kilometrage" in colonnes_voitures: km_val=row.get('kilometrage',0); km_val=int(float(km_val)) if km_val else 0; new_km=st.number_input("KM",value=km_val,key=f"km_v_{row['id']}"); data_update["kilometrage"]=int(new_km)
                        with c3:
                            if "carburant" in colonnes_voitures: carburant_options=["Essence","Diesel","Hybride","Électrique"]; carb_val=row.get('carburant','Essence'); new_carb=st.selectbox("Carburant",carburant_options,index=carburant_options.index(carb_val) if carb_val in carburant_options else 0,key=f"carb_v_{row['id']}"); data_update["carburant"]=str(new_carb)
                            if "boite" in colonnes_voitures: boite_options=["Manuelle","Automatique"]; boite_val=row.get('boite','Manuelle'); new_boite=st.selectbox("Boîte",boite_options,index=boite_options.index(boite_val) if boite_val in boite_options else 0,key=f"boite_v_{row['id']}"); data_update["boite"]=str(new_boite)
                            if "prix" in colonnes_voitures: new_prix=st.number_input("Prix $",value=float(row.get('prix',0)),key=f"prix_v_{row['id']}"); data_update["prix"]=float(new_prix)
                            if "statut" in colonnes_voitures: statut_options=["Disponible","En réparation","Réservée","Vendue"]; statut_val=row.get('statut','Disponible'); new_statut=st.selectbox("Statut",statut_options,index=statut_options.index(statut_val) if statut_val in statut_options else 0,key=f"statut_v_{row['id']}"); data_update["statut"]=str(new_statut)
                        if "quantite" in colonnes_voitures: new_qte=st.number_input("Stock",value=int(row.get('quantite',1)),min_value=0,key=f"qte_v_{row['id']}"); data_update["quantite"]=int(new_qte)
                        if "qualite" in colonnes_voitures: qualite_options=["Neuf","Occasion","Reconditionné"]; qualite_val=row.get('qualite','Neuf'); new_qualite=st.selectbox("Qualité",qualite_options,index=qualite_options.index(qualite_val) if qualite_val in qualite_options else 0,key=f"qual_v_{row['id']}"); data_update["qualite"]=str(new_qualite)
                        if "code_qr" in colonnes_voitures: new_code_qr=st.text_input("Code QR",value=row.get('code_qr',''),key=f"qr_v_{row['id']}"); data_update["code_qr"]=str(new_code_qr)
                        c1,c2=st.columns(2)
                        if c1.button("✏️ Modifier",key=f"mod_v_parc_{row['id']}",width="stretch"):
                            try: supabase.table("voitures").update(data_update).eq("id",int(row['id'])).execute(); st.success("Modifié"); st.cache_data.clear(); st.rerun()
                            except Exception as e: st.error("Erreur modif"); st.code(repr(e))
                        if st.session_state.user_role=="PDG" or perms.get('supprimer',False):
                            if c2.button("🗑️ Supprimer",key=f"del_v_parc_{row['id']}",width="stretch"):
                                try: supabase.table("voitures").delete().eq("id",int(row['id'])).execute(); st.success("Supprimé"); st.cache_data.clear(); st.rerun()
                                except Exception as e: st.error("Erreur suppression"); st.code(repr(e))
        with tab_pertes_v:
            st.subheader("⚠️ Déclarer Dégât/Perte Voiture")
            voitures_dispo=df_voitures[df_voitures.get('quantite',1)>0].copy() if not df_voitures.empty else pd.DataFrame()
            if voitures_dispo.empty: st.warning("Aucune voiture en stock pour déclarer un dégât")
            else:
                col1,col2=st.columns(2)
                with col1: voiture_dict={f"{v['marque']} {v['modele']} - {v.get('plaque','')} - Stock:{int(v.get('quantite',1))}":v for _,v in voitures_dispo.iterrows()}; voiture_choisie=st.selectbox("Voiture endommagée/perdue",list(voiture_dict.keys())); qte_perte_v=st.number_input("Quantité endommagée",min_value=1,max_value=int(voiture_dict[voiture_choisie].get('quantite',1)) if voiture_choisie else 1)
                with col2: motif_perte_v=st.selectbox("Type de dégât",["Accident","Vol","Incendie","Panne moteur","Dégât carrosserie","Pneus crevés","Autre"]); detail_perte_v=st.text_area("Détails du dégât",placeholder="Ex: Pare-choc avant enfoncé + phare cassé"); responsable_v=st.text_input("Déclaré par",value=st.session_state.user_name,key="resp_v")
                if voiture_choisie: voiture_data=voiture_dict[voiture_choisie]; valeur_perte_v=qte_perte_v*float(voiture_data.get('prix',0)); st.error(f"💸 Valeur de la perte : {valeur_perte_v:,.2f} $")
                if st.button("🚨 ENREGISTRER DÉGÂT VOITURE",type="primary",width="stretch"):
                    if voiture_choisie and qte_perte_v>0:
                        voiture_data=voiture_dict[voiture_choisie]
                        try:
                            nouveau_stock_v=int(voiture_data.get('quantite',1))-qte_perte_v; nouveau_statut="En réparation" if nouveau_stock_v>0 else "Endommagée"
                            supabase.table('voitures').update({"quantite":nouveau_stock_v,"statut":nouveau_statut}).eq("id",int(voiture_data['id'])).execute()
                            supabase.table('mouvements_stock').insert({"article_id":int(voiture_data['id']),"article_nom":f"{voiture_data['marque']} {voiture_data['modele']} - {voiture_data.get('plaque','')}","type":"PERTE_VOITURE","quantite":-int(qte_perte_v),"motif":f"{motif_perte_v} - {detail_perte_v}","valeur":float(valeur_perte_v),"created_by":responsable_v,"created_at":datetime.now().isoformat()}).execute()
                            st.success(f"✅ Dégât enregistré. Stock {voiture_data['marque']} {voiture_data['modele']}: {nouveau_stock_v}"); st.cache_data.clear(); st.rerun()
                        except Exception as e: st.error("Erreur enregistrement dégât"); st.code(repr(e))
            st.divider(); st.subheader("📋 Historique Dégâts/Pertes Voitures")
            try: pertes_v=supabase.table('mouvements_stock').select("*").eq("type","PERTE_VOITURE").order("created_at",desc=True).limit(20).execute().data
            except: pertes_v=[]
            if not pertes_v: st.info("Aucun dégât de voiture enregistré")
            else:
                total_pertes_v=sum(p.get('valeur',0) for p in pertes_v); st.metric("💸 TOTAL PERTES VOITURES",f"{total_pertes_v:,.2f} $")
                for p in pertes_v:
                    with st.expander(f"🔴 {p.get('article_nom')} - {abs(p.get('quantite',0))} - {p.get('created_at','')[:10]}"):
                        col1,col2,col3=st.columns(3)
                        with col1: st.write(f"**Qté endommagée:** {abs(p.get('quantite',0))}"); st.write(f"**Valeur:** {p.get('valeur',0):,.2f} $")
                        with col2: st.write(f"**Motif:** {p.get('motif','N/A')}"); st.write(f"**Par:** {p.get('created_by','N/A')}")
                        with col3:
                            if st.session_state.user_role=="PDG":
                                if st.button("🗑️ Supprimer",key=f"del_perte_v_{p.get('id')}"): supabase.table('mouvements_stock').delete().eq("id",p.get('id')).execute(); st.rerun()

# === COMPTABILITÉ ===
if "💰 Comptabilité" in tab_map:
    with tab_map["💰 Comptabilité"]:
        st.markdown("## 💰 Comptabilité - Relevé par Catégorie")
        colonnes_compta=get_table_columns("compta")
        with st.expander("➕ Ajouter Opération"):
            with st.form("form_compta",clear_on_submit=True):
                c1,c2,c3=st.columns(3); type_op=c1.selectbox("Type",["Revenu","Dépense"]); cat=c2.text_input("Catégorie",placeholder="Ex: Loyer, Vente Auto, Carburant"); montant=c3.number_input("Montant",min_value=0.0)
                data_insert={"type":str(type_op),"categorie":str(cat),"montant":float(montant),"utilisateur":st.session_state.user_name}
                if "description" in colonnes_compta: desc=c1.text_input("Description",placeholder="Ex: Loyer - Client Jean"); data_insert["description"]=str(desc)
                if "devise" in colonnes_compta: devise=c2.selectbox("Devise",["FC","$","€"]); data_insert["devise"]=str(devise)
                if "date" in colonnes_compta: date_op=c3.date_input("Date",value=date.today()); data_insert["date"]=str(date_op)
                if st.form_submit_button("💾 Ajouter Opération"):
                    try: supabase.table("compta").insert(data_insert).execute(); st.success("Opération ajoutée"); st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error("Erreur ajout"); st.code(repr(e))
        st.divider()
        if df_compta.empty: st.info("Aucune opération")
        else:
            df_compta_sorted=df_compta.sort_values('date',ascending=False)
            col_f1,col_f2,col_f3=st.columns(3); date_debut=col_f1.date_input("📅 Date début",value=date.today()-timedelta(days=30),key="date_debut_compta")
            date_fin=col_f2.date_input("📅 Date fin",value=date.today(),key="date_fin_compta"); filtre_nom=col_f3.text_input("👤 Nom Client",placeholder="Tape un nom...",key="filtre_nom_compta")
            df_filtre_compta=df_compta_sorted[(df_compta_sorted['date']>=str(date_debut))&(df_compta_sorted['date']<=str(date_fin))]
            if filtre_nom: df_filtre_compta=df_filtre_compta[df_filtre_compta['description'].str.contains(filtre_nom,case=False,na=False)]
            col_t1,col_t2,col_t3=st.columns(3); total_fc=df_filtre_compta[df_filtre_compta.get('devise','FC')=='FC']['montant'].sum()
            total_usd=df_filtre_compta[df_filtre_compta.get('devise','FC')=='$']['montant'].sum(); total_eur=df_filtre_compta[df_filtre_compta.get('devise','FC')=='€']['montant'].sum()
            col_t1.metric("💵 Total FC",f"{total_fc:,.0f}"); col_t2.metric("💵 Total USD",f"{total_usd:,.0f}"); col_t3.metric("💵 Total EUR",f"{total_eur:,.0f}"); st.divider()
            categories=df_filtre_compta.get('categorie',pd.Series(dtype=str)).dropna().unique()
            if len(categories)==0: st.info("Aucune opération trouvée avec ces filtres")
            else:
                for cat in sorted(categories):
                    df_cat=df_filtre_compta[df_filtre_compta.get('categorie','')==cat]
                    total_cat_eur=df_cat[df_cat.get('devise','FC')=='€']['montant'].sum(); total_cat=total_cat_fc+total_cat_usd+total_cat_eur
                    with st.expander(f"📁 {cat} - {len(df_cat)} opérations - Total: {total_cat:,.0f}",expanded=False):
                        colonnes_affiche=['date','type','description','montant','devise']
                        if 'utilisateur' in df_cat.columns: colonnes_affiche.append('utilisateur')
                        st.dataframe(df_cat[colonnes_affiche],use_container_width=True,hide_index=True)
                        col_dl1,col_dl2=st.columns(2)
                        excel_bytes_cat=generer_excel_pro(df_cat,f"Releve {cat} {date_debut}-{date_fin}",df_cat[df_cat['type']=='Revenu']['montant'].sum(),df_cat[df_cat['type']=='Dépense']['montant'].sum(),df_cat[df_cat['type']=='Revenu']['montant'].sum()-df_cat[df_cat['type']=='Dépense']['montant'].sum()])
                        safe_cat=str(cat).replace(" ","_").replace("/","_")
                        col_dl1.download_button(label=f"📥 {cat} - EXCEL",data=excel_bytes_cat,file_name=f"Compta_{safe_cat}_{date_debut}_{date_fin}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",width="stretch",key=f"dl_excel_compta_{safe_cat}_{date_debut}_{filtre_nom}")
                        pdf_cat=FPDF(); pdf_cat.add_page(); pdf_cat.set_fill_color(20,50,40); pdf_cat.rect(0,0,210,35,'F'); pdf_cat.set_text_color(255,255,255)
                        pdf_cat.set_font("Arial","B",20); pdf_cat.set_xy(10,8); pdf_cat.cell(0,10,"ASYMAS BUSINESS",ln=True)
                        pdf_cat.set_font("Arial","",9); pdf_cat.set_xy(10,16); pdf_cat.cell(0,5,"Beni, Nord-Kivu, RDC | Tel: +243 995 105 623",ln=True)
                        pdf_cat.set_font("Arial","B",10); pdf_cat.set_xy(150,8); filtre_txt=f"Filtre: {filtre_nom}" if filtre_nom else "Tous"
                        pdf_cat.cell(50,6,f"Periode: {date_debut} au {date_fin}",ln=True,align="R"); pdf_cat.set_xy(150,14); pdf_cat.cell(50,6,filtre_txt,ln=True,align="R"); pdf_cat.ln(15)
                        pdf_cat.set_text_color(0,0,0); pdf_cat.set_fill_color(255,204,0); pdf_cat.set_font("Arial","B",14); pdf_cat.cell(0,10,f"RELEVE COMPTABLE - {safe_pdf_txt(cat).upper()}",ln=True,fill=True); pdf_cat.ln(5)
                        pdf_cat.set_font("Arial","B",11); pdf_cat.cell(0,8,f"Total FC: {total_cat_fc:,.0f} | USD: {total_cat_usd:,.0f} | EUR: {total_cat_eur:,.0f}",ln=True); pdf_cat.ln(3)
                        pdf_cat.set_font("Arial","B",9); pdf_cat.cell(20,7,"Date",1,0,'C'); pdf_cat.cell(20,7,"Type",1,0,'C'); pdf_cat.cell(80,7,"Description",1,0,'C'); pdf_cat.cell(25,7,"Montant",1,0,'C'); pdf_cat.cell(15,7,"Devise",1,1,'C')
                        pdf_cat.set_font("Arial","",8)
                        for _,row in df_cat.iterrows():
                            if pdf_cat.get_y()>270: pdf_cat.add_page(); pdf_cat.set_font("Arial","B",9); pdf_cat.cell(20,7,"Date",1,0,'C'); pdf_cat.cell(20,7,"Type",1,0,'C'); pdf_cat.cell(80,7,"Description",1,0,'C'); pdf_cat.cell(25,7,"Montant",1,0,'C'); pdf_cat.cell(15,7,"Devise",1,1,'C'); pdf_cat.set_font("Arial","",8)
                            pdf_cat.cell(20,6,str(row.get('date',''))[:10],1,0,'C'); pdf_cat.cell(20,6,str(row.get('type','')),1,0,'C'); pdf_cat.cell(80,6,safe_pdf_txt(str(row.get('description',''))[:45]),1,0,'L'); pdf_cat.cell(25,6,f"{row.get('montant',0):,.0f}",1,0,'R'); pdf_cat.cell(15,6,str(row.get('devise','FC')),1,1,'C')
                        pdf_cat.ln(3); pdf_cat.set_fill_color(255,204,0); pdf_cat.set_font("Arial","B",11)
                        pdf_cat.cell(120,8,"TOTAL REVENU",1,0,'R',True); pdf_cat.cell(25,8,f"{df_cat[df_cat['type']=='Revenu']['montant'].sum():,.0f}",1,0,'R',True)
                        pdf_cat.cell(15,8,"FC",1,1,'C',True)
                        pdf_cat.cell(120,8,"TOTAL DEPENSE",1,0,'R',True); pdf_cat.cell(25,8,f"{df_cat[df_cat['type']=='Dépense']['montant'].sum():,.0f}",1,0,'R',True)
                        pdf_cat.cell(15,8,"FC",1,1,'C',True)
                        pdf_bytes=bytes(pdf_cat.output(dest='S'))
                        col_dl2.download_button(label=f"📄 {cat} - PDF",data=pdf_bytes,file_name=f"Compta_{safe_cat}_{date_debut}_{date_fin}.pdf",mime="application/pdf",width="stretch",key=f"dl_pdf_compta_{safe_cat}_{date_debut}_{filtre_nom}")

# === FACTURES ===
if "📄 Factures" in tab_map:
    with tab_map["📄 Factures"]:
        st.markdown("## 📄 Générer Facture/Proforma")
        tab_fact,tab_pro=st.tabs(["📄 Facture Simple","📋 Proforma"])
        with tab_fact:
            st.subheader("Facture Simple - Vente/Réparation")
            nom_client=st.text_input("👤 Nom Client",key="nom_client_fact")
            tel_client=st.text_input("Téléphone Client",value="+243...",key="tel_client_fact")
            col1,col2=st.columns(2)
            with col1: type_op=st.selectbox("Type Opération",["Vente Article","Vente Voiture","Loyer","Réparation","Consulting","Service","Autre"],key="type_fact")
            with col2: devise=st.selectbox("Devise",["FC","$","€"],key="devise_fact")
            details=st.text_area("Détails",placeholder="Ex: Vente 5 sacs ciment + transport",key="details_fact")
            montant=st.number_input("Montant Total",min_value=0.0,key="montant_fact")
            if st.button("📄 GÉNÉRER FACTURE",type="primary",width="stretch",key="btn_fact"):
                if nom_client and details and montant>0:
                    details_list=[{"nom":details,"qte":1,"pu":montant}]
                    num_fact,pdf_bytes=creer_facture_auto(type_op,nom_client,details,montant,devise,details_list,tel_client,"","Simple")
                    st.success(f"✅ Facture générée : {num_fact}")
                    st.download_button(label="📥 Télécharger Facture PDF",data=bytes(pdf_bytes),file_name=f"{num_fact}.pdf",mime="application/pdf",width="stretch",key="dl_fact_simple")
                    pdf_b64=base64.b64encode(pdf_bytes).decode()
                    st.components.v1.html(f"""<button onclick="printPDFFact()" style="width:100%;padding:10px;background:#00ff41;color:black;font-weight:bold;border:none;border-radius:5px;cursor:pointer;margin-top:10px;">🖨️ IMPRIMER LA FACTURE</button>
                        <script>function printPDFFact(){{const pdfData='data:application/pdf;base64,{pdf_b64}';const win=window.open('','_blank');
                        win.document.write('<iframe src="'+pdfData+'" width="100%" height="100%" style="border:none;"></iframe>');
                        win.document.close();setTimeout(()=>{{win.print();}},1000);}}</script>""",height=60)
                    st.cache_data.clear()
                else: st.error("Remplis tous les champs obligatoires")
        with tab_pro:
            st.subheader("Proforma - Devis Détaillé")
            nom_client_p=st.text_input("👤 Nom Client",key="nom_client_pro")
            tel_client_p=st.text_input("Téléphone Client",value="+243...",key="tel_client_pro")
            col1,col2=st.columns(2)
            with col1: type_op_p=st.selectbox("Type Opération",["Proforma Vente","Proforma Travaux","Proforma Location"],key="type_pro")
            with col2: devise_p=st.selectbox("Devise",["FC","$","€"],key="devise_pro")
            st.markdown("### Lignes de la Proforma")
            if 'lignes_pro' not in st.session_state: st.session_state.lignes_pro=[{"nom":"","qte":1,"pu":0.0}]
            total_pro=0
            for i in range(len(st.session_state.lignes_pro)):
                c1,c2,c3,c4=st.columns([4,1,2,1])
                st.session_state.lignes_pro[i]["nom"]=c1.text_input(f"Désignation {i+1}",value=st.session_state.lignes_pro[i]["nom"],key=f"nom_pro_{i}")
                st.session_state.lignes_pro[i]["qte"]=c2.number_input(f"Qté {i+1}",min_value=1,value=int(st.session_state.lignes_pro[i]["qte"]),key=f"qte_pro_{i}")
                st.session_state.lignes_pro[i]["pu"]=c3.number_input(f"P.U {i+1}",min_value=0.0,value=float(st.session_state.lignes_pro[i]["pu"]),key=f"pu_pro_{i}")
                total_ligne=st.session_state.lignes_pro[i]["qte"]*st.session_state.lignes_pro[i]["pu"]; total_pro+=total_ligne
                c4.write(f"= {total_ligne:,.0f}")
            st.markdown(f"### TOTAL PROFORMA: {total_pro:,.0f} {devise_p}")
            col_btn1,col_btn2=st.columns(2)
            if col_btn1.button("➕ Ajouter Ligne",width="stretch"): st.session_state.lignes_pro.append({"nom":"","qte":1,"pu":0.0}); st.rerun()
            if col_btn2.button("📄 GÉNÉRER PROFORMA",type="primary",width="stretch"):
                if nom_client_p and total_pro>0:
                    details_text=" | ".join([f"{l['qte']}x {l['nom']}" for l in st.session_state.lignes_pro if l['nom']])
                    num_fact,pdf_bytes=creer_facture_auto(type_op_p,nom_client_p,details_text,total_pro,devise_p,st.session_state.lignes_pro,tel_client_p,"","Proforma")
                    st.success(f"✅ Proforma générée : {num_fact}")
                    st.download_button(label="📥 Télécharger Proforma PDF",data=bytes(pdf_bytes),file_name=f"{num_fact}.pdf",mime="application/pdf",width="stretch",key="dl_proforma")
                    pdf_b64=base64.b64encode(pdf_bytes).decode()
                    st.components.v1.html(f"""<button onclick="printPDFPro()" style="width:100%;padding:10px;background:#00ff41;color:black;font-weight:bold;border:none;border-radius:5px;cursor:pointer;margin-top:10px;">🖨️ IMPRIMER LA PROFORMA</button>
                        <script>function printPDFPro(){{const pdfData='data:application/pdf;base64,{pdf_b64}';const win=window.open('','_blank');
                        win.document.write('<iframe src="'+pdfData+'" width="100%" height="100%" style="border:none;"></iframe>');
                        win.document.close();setTimeout(()=>{{win.print();}},1000);}}</script>""",height=60)
                    st.session_state.lignes_pro=[{"nom":"","qte":1,"pu":0.0}]; st.cache_data.clear()
                else: st.error("Remplis nom client et au moins une ligne")

# === DEVIS ===
if "📋 Devis" in tab_map:
    with tab_map["📋 Devis"]:
        st.markdown("## 📋 Générateur Devis ASYMAS CONSULTING")
        type_devis=st.selectbox("Type de Devis",["Industriel","Bâtiment"],key="type_devis")
        col1,col2=st.columns(2)
        with col1: client=st.text_input("👤 Nom Client",key="client_devis"); titre_projet=st.text_input("📝 Titre du Projet",key="titre_devis")
        with col2: parcelle=st.text_input("📍 N° Parcelle",key="parcelle_devis"); localisation=st.text_input("🌍 Localisation",key="loc_devis")
        tel_client_devis=st.text_input("📞 Téléphone Client",value="+243...",key="tel_devis")
        devise_devis=st.selectbox("💰 Devise",["USD","FC","€"],key="devise_devis")
        st.markdown("### Sections du Devis")
        if 'sections_devis' not in st.session_state: st.session_state.sections_devis=[{"numero":"1","titre":"","items":[{"num":"1.1","designation":"","unite":"","qte":0.0,"pu":0.0}]}]
        grand_total=0
        for s_idx,section in enumerate(st.session_state.sections_devis):
            st.markdown(f"#### Section {section['numero']}")
            section['titre']=st.text_input(f"Titre Section {section['numero']}",value=section['titre'],key=f"titre_sec_{s_idx}")
            sous_total=0
            for i_idx,item in enumerate(section['items']):
                c1,c2,c3,c4,c5,c6=st.columns([1,4,1,1,2,1])
                item['num']=c1.text_input(f"N° {s_idx}-{i_idx}",value=item['num'],key=f"num_item_{s_idx}_{i_idx}")
                item['designation']=c2.text_input(f"Désignation {s_idx}-{i_idx}",value=item['designation'],key=f"des_item_{s_idx}_{i_idx}")
                item['unite']=c3.text_input(f"U {s_idx}-{i_idx}",value=item['unite'],key=f"unite_item_{s_idx}_{i_idx}")
                item['qte']=c4.number_input(f"Qté {s_idx}-{i_idx}",min_value=0.0,value=float(item['qte']),key=f"qte_item_{s_idx}_{i_idx}")
                item['pu']=c5.number_input(f"P.U {s_idx}-{i_idx}",min_value=0.0,value=float(item['pu']),key=f"pu_item_{s_idx}_{i_idx}")
                total_item=item['qte']*item['pu']; sous_total+=total_item; c6.write(f"= {total_item:,.0f}")
            st.markdown(f"**Sous-total Section {section['numero']}: {sous_total:,.0f} {devise_devis}**"); grand_total+=sous_total
            if st.button(f"➕ Ajouter Item Section {section['numero']}",key=f"add_item_{s_idx}"):
                new_num=f"{section['numero']}.{len(section['items'])+1}"; section['items'].append({"num":new_num,"designation":"","unite":"","qte":0.0,"pu":0.0}); st.rerun()
        main_oeuvre=st.number_input(f"🔧 Main d'Œuvre {devise_devis}",min_value=0.0,value=0.0,key="mo_devis")
        grand_total+=main_oeuvre; st.markdown(f"## 💎 TOTAL GÉNÉRAL: {grand_total:,.0f} {devise_devis}")
        col_btn1,col_btn2=st.columns(2)
        if col_btn1.button("➕ Nouvelle Section",width="stretch"):
            new_sec_num=str(len(st.session_state.sections_devis)+1); st.session_state.sections_devis.append({"numero":new_sec_num,"titre":"","items":[{"num":f"{new_sec_num}.1","designation":"","unite":"","qte":0.0,"pu":0.0}]}); st.rerun()
        if col_btn2.button("📄 GÉNÉRER DEVIS PDF",type="primary",width="stretch"):
            if client and titre_projet:
                numero_devis=f"DC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                pdf_bytes=generer_pdf_devis_consulting(numero_devis,type_devis,client,titre_projet,parcelle,localisation,st.session_state.sections_devis,devise_devis,tel_client_devis,main_oeuvre)
                st.success(f"✅ Devis généré : {numero_devis}")
                st.download_button(label="📥 Télécharger Devis PDF",data=bytes(pdf_bytes),file_name=f"{numero_devis}.pdf",mime="application/pdf",width="stretch",key="dl_devis")
                pdf_b64=base64.b64encode(pdf_bytes).decode()
                st.components.v1.html(f"""<button onclick="printPDFDevis()" style="width:100%;padding:10px;background:#00ff41;color:black;font-weight:bold;border:none;border-radius:5px;cursor:pointer;margin-top:10px;">🖨️ IMPRIMER LE DEVIS</button>
                    <script>function printPDFDevis(){{const pdfData='data:application/pdf;base64,{pdf_b64}';const win=window.open('','_blank');
                    win.document.write('<iframe src="'+pdfData+'" width="100%" height="100%" style="border:none;"></iframe>');
                    win.document.close();setTimeout(()=>{{win.print();}},1000);}}</script>""",height=60)
                st.session_state.sections_devis=[{"numero":"1","titre":"","items":[{"num":"1.1","designation":"","unite":"","qte":0.0,"pu":0.0}]}]
            else: st.error("Remplis Client et Titre du Projet")

# === UTILISATEURS ===
if "👥 Utilisateurs" in tab_map and st.session_state.user_role=="PDG":
    with tab_map["👥 Utilisateurs"]:
        st.markdown("## 👥 Gestion des Utilisateurs")
        with st.expander("➕ Ajouter Nouvel Utilisateur"):
            with st.form("form_user",clear_on_submit=True):
                c1,c2=st.columns(2); nom=c1.text_input("Nom Complet"); role=c2.selectbox("Rôle",["PDG","GERANTE","UTILISATEUR","COMMERCIAL","COMPTABLE"])
                password=st.text_input("Mot de passe",type="password"); st.markdown("**Permissions:**")
                perm_dashboard=st.checkbox("Dashboard",value=True); perm_commerce=st.checkbox("Commerce",value=True)
                perm_stock=st.checkbox("Gestion Stock",value=False); perm_immo=st.checkbox("Immobilier",value=False)
                perm_auto=st.checkbox("Automobile",value=False); perm_parc=st.checkbox("Gestion Parc",value=False)
                perm_compta=st.checkbox("Comptabilité",value=False); perm_fact=st.checkbox("Factures",value=False)
                perm_devis_ind=st.checkbox("Devis Industriel",value=False); perm_devis_bat=st.checkbox("Devis Bâtiment",value=False); perm_users=st.checkbox("Gérer Utilisateurs",value=False)
                perm_suppr=st.checkbox("Supprimer Données",value=False)
                if st.form_submit_button("💾 Créer Utilisateur"):
                    try:
                        permissions={"dashboard":perm_dashboard,"commerce":perm_commerce,"stock":perm_stock,"immobilier":perm_immo,"automobile":perm_auto,"parc":perm_parc,"comptabilite":perm_compta,"factures":perm_fact,"devis_industriel":perm_devis_ind,"devis_batiment":perm_devis_bat,"users":perm_users,"supprimer":perm_suppr}
                        supabase.table("utilisateurs").insert({"nom":str(nom),"role":str(role),"password":str(password),"permissions":permissions,"categories_autorisees":[]}).execute()
                        st.success(f"Utilisateur {nom} créé"); st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error("Erreur création"); st.code(repr(e))
        st.divider(); st.subheader("📋 Liste Utilisateurs")
        if df_utilisateurs.empty: st.info("Aucun utilisateur")
        else:
            for _,user in df_utilisateurs.iterrows():
                with st.expander(f"{user['nom']} - {user['role']}"):
                    c1,c2=st.columns(2)
                    with c1: st.write(f"**Nom:** {user['nom']}"); st.write(f"**Rôle:** {user['role']}")
                    with c2:
                        if st.button("🗑️ Supprimer",key=f"del_user_{user['id']}"):
                            if user['role']!="PDG":
                                try: supabase.table("utilisateurs").delete().eq("id",user['id']).execute(); st.success("Supprimé"); st.cache_data.clear(); st.rerun()
                                except Exception as e: st.error("Erreur suppression"); st.code(repr(e))
                            else: st.error("Impossible de supprimer le PDG")

# === FLOKI ASSISTANT ===
st.sidebar.markdown("---"); st.sidebar.markdown("### 🤖 FLOKI Assistant")
question=st.sidebar.text_input("Pose ta question à FLOKI",placeholder="Ex: Total revenus ce mois",key="floki_q")
if st.sidebar.button("❓ Demander",key="btn_floki"):
    if question:
        q=question.lower(); reponse="Désolé, je n'ai pas compris."
        if "revenu" in q or "chiffre" in q:
            total=df_compta[df_compta['type']=='Revenu']['montant'].sum() if not df_compta.empty else 0; reponse=f"💰 Total revenus: {total:,.0f} FC"
        elif "dépense" in q or "charge" in q:
            total=df_compta[df_compta['type']=='Dépense']['montant'].sum() if not df_compta.empty else 0; reponse=f"💸 Total dépenses: {total:,.0f} FC"
        elif "stock" in q or "article" in q: reponse=f"📦 Articles en stock: {len(df_articles)}"
        elif "voiture" in q: reponse=f"🚗 Voitures: {len(df_voitures)}"
        elif "client" in q: reponse=f"👤 Clients enregistrés: {len(df_compta['description'].unique()) if not df_compta.empty else 0}"
        st.sidebar.success(reponse)
    else: st.sidebar.warning("Pose une question")
                    
