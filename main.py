import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

from supabase import create_client, Client
from datetime import date, datetime, timedelta
from fpdf import FPDF
import tempfile, os, json, qrcode, base64, io
from PIL import Image
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from streamlit_qrcode_scanner import qrcode_scanner
import difflib, re, urllib.parse, requests

# =========================
# CONFIG & CSS
# =========================
st.set_page_config(
    page_title="ASYMAS BUSINESS",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown(
    """<meta name="mobile-web-app-capable" content="yes">""",
    unsafe_allow_html=True
)

st.markdown(
    """
<style>
.block-container{padding:0!important;max-width:100%!important;}
.main{background:#0a0a0a;margin:0;padding:0;}
/* Champ mot de passe sur l'écran login */
div[data-testid="stTextInput"]{
    position:absolute!important;
    bottom:8%!important;
    left:50%!important;
    transform:translateX(-50%)!important;
    width:180px!important;
    z-index:100!important;
}
div[data-testid="stTextInput"] input{
    background:rgba(0,0,0,0.9)!important;
    border:2px solid #FFD700!important;
    border-radius:10px!important;
    color:#FFD700!important;
    text-align:center!important;
    padding:10px!important;
}
div[data-testid="stTextInput"] label{display:none!important;}

#MainMenu, header,.stAppToolbar,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stHeader"],
footer,.stDeployButton,
[data-testid="stStatusWidget"] {
    display: none!important;
    visibility: hidden!important;
}

h1, h2, h3 {
    color: #00ff41!important;
    font-size: 2.2rem!important;
    font-weight: 900!important;
    padding: 10px 0!important;
    border-bottom: 3px solid #00ff41!important;
    margin-bottom: 20px!important;
}
div[data-testid="stMetricValue"] {color: #00ff41!important;}
.stButton>button {
    background-color: #00ff41!important;
    color: black!important;
    font-weight: bold;
    border: none;
}
</style>
""",
    unsafe_allow_html=True
)

# =========================
# SUPABASE
# =========================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# SESSION STATE
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = ""
    st.session_state.user_name = ""
    st.session_state.perms = {}
    st.session_state.user_cats = []

# module sélectionné (Commerce, Stock, Immo, Auto, Compta, Factures)
if "selected_module" not in st.session_state:
    st.session_state.selected_module = None

# synchroniser avec query params (ex: ?module=Commerce)
if "module" in st.query_params and st.session_state.selected_module is None:
    st.session_state.selected_module = st.query_params["module"]
    st.rerun()

# =========================
# FONCTIONS UTILITAIRES
# =========================
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
        return list(test.data[0].keys()) if test.data else []
    except:
        return []

def generer_qrcode(data_text: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=1,
    )
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    img.save(temp_file.name)
    return temp_file.name

def safe_pdf_txt(txt):
    if txt is None or (isinstance(txt, float) and pd.isna(txt)):
        return ""
    txt = str(txt)
    txt = (
        txt.replace("—", "-")
        .replace("–", "-")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("•", "-")
        .replace("…", "...")
    )
    txt = "".join(c if ord(c) < 128 else "?" for c in txt)
    return txt.replace("\n", " ").replace("\r", "").strip()

def generer_pdf_facture(
    numero,
    type_op,
    client,
    details_list,
    montant,
    devise,
    tel_client="+243...",
    periode="",
    type_facture="Simple",
):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False, margin=10)

    # Bandeau
    pdf.set_fill_color(20, 50, 40)
    pdf.rect(0, 0, 210, 35, "F")
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
    titre_fact = "FACTURE N" if type_facture == "Simple" else "PROFORMA N"
    pdf.cell(50, 6, titre_fact, ln=True, align="R")
    pdf.set_font("Arial", "", 10)
    pdf.set_xy(150, 14)
    pdf.cell(50, 6, safe_pdf_txt(numero), ln=True, align="R")
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(150, 20)
    pdf.cell(50, 6, f"Date: {date.today().strftime('%d/%m/%Y')}", ln=True, align="R")

    y_pos = 45
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 14)
    pdf.set_xy(10, y_pos)
    pdf.cell(0, 10, f"{type_facture.upper()} {safe_pdf_txt(type_op.upper())}", ln=True, fill=True)
    y_pos += 15

    pdf.set_font("Arial", "B", 10)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_xy(10, y_pos)
    pdf.cell(85, 7, "FACTURE A:", 1, 0, "L")
    pdf.cell(10, 7, "", 0, 0)
    pdf.cell(85, 7, "DETAILS PAIEMENT:", 1, 1, "L")
    y_pos += 7

    pdf.set_font("Arial", "", 9)
    pdf.set_xy(10, y_pos)
    pdf.cell(85, 6, f"Client: {safe_pdf_txt(client)}", "LR", 0, "L")
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(85, 6, "M-Pesa: +243817264448", "LR", 1, "L")
    y_pos += 6

    pdf.set_xy(10, y_pos)
    pdf.cell(85, 6, f"Tel: {safe_pdf_txt(tel_client)}", "LR", 0, "L")
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(85, 6, "Echeance: Immediate", "LR", 1, "L")
    y_pos += 6

    pdf.set_xy(10, y_pos)
    pdf.cell(85, 6, f"Date emission: {date.today().strftime('%d/%m/%Y')}", "LRB", 0, "L")
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(85, 6, "", "LRB", 1, "L")
    y_pos += 14

    # Tableau
    pdf.set_fill_color(0, 102, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.set_xy(10, y_pos)
    pdf.cell(115, 8, "DESIGNATION", 1, 0, "C", True)
    pdf.cell(25, 8, "QTE", 1, 0, "C", True)
    pdf.cell(40, 8, f"MONTANT ({safe_pdf_txt(devise)})", 1, 1, "C", True)
    y_pos += 8

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)

    if isinstance(details_list, list) and details_list:
        for item in details_list:
            if y_pos > 240:
                pdf.add_page()
                y_pos = 30
            nom = safe_pdf_txt(item.get("nom", ""))
            qte = item.get("qte", 1)
            pu = item.get("pu", item.get("prix", 0))
            montant_item = pu * qte
            pdf.set_xy(10, y_pos)
            pdf.cell(115, 7, nom, 1, 0, "L")
            pdf.cell(25, 7, str(qte), 1, 0, "C")
            pdf.cell(40, 7, f"{montant_item:,.0f}", 1, 1, "R")
            y_pos += 7

    # Total
    pdf.set_fill_color(255, 204, 0)
    pdf.set_font("Arial", "B", 11)
    pdf.set_xy(10, y_pos)
    pdf.cell(140, 10, "MONTANT TOTAL A PAYER", 1, 0, "R", True)
    pdf.cell(40, 10, f"{montant:,.0f} {safe_pdf_txt(devise)}", 1, 1, "R", True)
    y_pos += 15

    if y_pos > 220:
        pdf.add_page()
        y_pos = 30

    # Signature
    pdf.set_xy(10, y_pos)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, "SIGNATURE RESPONSABLE:", ln=True)
    y_pos += 11
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, y_pos, 100, y_pos)
    y_pos += 1
    pdf.set_font("Arial", "", 9)
    pdf.set_xy(10, y_pos)
    pdf.cell(90, 5, "Ing. SAMY TSANGYA", ln=True)
    y_pos += 5
    pdf.set_xy(10, y_pos)
    pdf.cell(90, 5, "Tel: +243 995 105 623", ln=True)
    y_pos += 10

    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(0, 102, 0)
    pdf.set_xy(10, y_pos)
    pdf.cell(0, 6, "Merci pour votre confiance! ASYMAS BUSINESS", ln=True, align="C")

    qr_data = (
        f"ASYMAS BUSINESS\nFacture: {numero}\nType: {type_op}\n"
        f"Client: {client}\nMontant: {montant:,.0f} {devise}"
    )
    qr_path = generer_qrcode(qr_data)
    pdf.image(qr_path, x=155, y=y_pos - 25, w=25)
    os.unlink(qr_path)

    return bytes(pdf.output(dest="S"))

def creer_facture_auto(
    type_op,
    client,
    details,
    montant,
    devise="FC",
    details_list=None,
    tel="+243...",
    periode="",
    type_facture="Simple",
):
    numero_facture = f"AS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if details_list is None:
        details_list = [{"nom": details, "qte": 1, "pu": montant}]
    pdf_bytes = generer_pdf_facture(
        numero_facture,
        type_op,
        client,
        details_list,
        montant,
        devise,
        tel,
        periode,
        type_facture,
    )
    try:
        data_compta = {
            "type": "Revenu",
            "description": f"{type_op} - {client} - {details}",
            "montant": float(montant),
            "date": str(date.today()),
            "utilisateur": st.session_state.user_name,
            "categorie": str(type_op),
            "devise": str(devise),
            "numero_facture": str(numero_facture),
            "details": json.dumps(details_list),
        }
        supabase.table("compta").insert(data_compta).execute()
        st.toast(f"✅ Enregistré par {st.session_state.user_name}", icon="✅")
    except Exception as e:
        st.error("❌ ERREUR INSERTION COMPTA")
        st.code(repr(e))
    return numero_facture, pdf_bytes

def generer_excel_pro(
    df_data,
    titre="Relevé Comptable",
    total_revenu=0,
    total_depense=0,
    solde=0,
):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_data.to_excel(writer, sheet_name="Releve", index=False, startrow=6)
        workbook = writer.book
        worksheet = writer.sheets["Releve"]

        worksheet.merge_cells("A1:F1")
        worksheet["A1"] = "ASYMAS BUSINESS"
        worksheet["A1"].font = Font(size=20, bold=True, color="006600")
        worksheet["A1"].alignment = Alignment(horizontal="center")

        worksheet.merge_cells("A2:F2")
        worksheet["A2"] = (
            "Beni, Nord-Kivu, RDC | Tel: +243 995 105 623 | asamnesstsang636@gmail.com"
        )
        worksheet["A2"].font = Font(size=10, italic=True)
        worksheet["A2"].alignment = Alignment(horizontal="center")

        worksheet.merge_cells("A3:F3")
        worksheet["A3"] = f"{titre.upper()} - Edité le {date.today().strftime('%d/%m/%Y')}"
        worksheet["A3"].font = Font(size=14, bold=True, color="FF6600")
        worksheet["A3"].alignment = Alignment(horizontal="center")

        worksheet.merge_cells("A4:F4")
        worksheet["A4"] = (
            f"Total Revenus: {total_revenu:,.0f} FC | "
            f"Total Dépenses: {total_depense:,.0f} FC | "
            f"Solde: {solde:,.0f} FC"
        )
        worksheet["A4"].font = Font(size=11, bold=True)
        worksheet["A4"].alignment = Alignment(horizontal="center")
        worksheet["A4"].fill = PatternFill(
            start_color="FFCC00",
            end_color="FFCC00",
            fill_type="solid",
        )

        header_fill = PatternFill(
            start_color="006600", end_color="006600", fill_type="solid"
        )
        header_font = Font(bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        for col in range(1, len(df_data.columns) + 1):
            cell = worksheet.cell(row=7, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
            cell.border = thin_border

        for row in range(7, len(df_data) + 8):
            for col in range(1, len(df_data.columns) + 1):
                c = worksheet.cell(row=row, column=col)
                c.border = thin_border
                c.alignment = Alignment(horizontal="left")

        for col in range(1, len(df_data.columns) + 1):
            worksheet.column_dimensions[get_column_letter(col)].width = 18

    return output.getvalue()

def check_perm(key: str) -> bool:
    perms = st.session_state.perms
    if isinstance(perms, str):
        try:
            perms = json.loads(perms)
        except:
            perms = {}
    return st.session_state.user_role == "PDG" or perms.get(key, False)

# =========================
# ÉCRAN LOGIN (cercle seul)
# =========================
if not st.session_state.logged_in:
    st.markdown(
        """
    <div style="position:relative;width:100vw;height:100vh;
                background:radial-gradient(ellipse at center 55%,
                rgba(255,215,0,0.7) 0%, rgba(15,15,15,1) 85%);
                overflow:hidden;">
        <!-- Carte bas -->
        <div style="position:absolute;bottom:10%;left:50%;
                    transform:translateX(-50%);
                    width:340px;height:170px;
                    background:linear-gradient(145deg,#2d2d2d,#1a1a1a);
                    border-radius:45px;
                    box-shadow:0 35px 70px rgba(0,0,0,0.9);
                    border:3px solid #444;">
        </div>

        <!-- Cercle central -->
        <div style="position:absolute;top:50%;left:50%;
                    transform:translate(-50%,-50%);
                    width:450px;height:450px;">

            <div style="position:absolute;top:50%;left:50%;
                        transform:translate(-50%,-50%);
                        width:380px;height:380px;
                        border:2px solid rgba(255,215,0,0.5);
                        border-radius:50%;
                        box-shadow:0 0 80px rgba(255,215,0,0.8);
                        animation:pulseRing 3s ease-in-out infinite;">
            </div>

            <div style="position:absolute;top:50%;left:50%;
                        transform:translate(-50%,-50%);
                        width:300px;height:300px;
                        border:2px dotted rgba(255,215,0,0.9);
                        border-radius:50%;
                        animation:rotate 15s linear infinite;">
            </div>

            <div style="position:absolute;top:50%;left:50%;
                        transform:translate(-50%,-50%);
                        width:220px;height:220px;
                        border:3px solid #FFD700;
                        border-radius:50%;
                        box-shadow:0 0 90px #FFD700;">
            </div>

            <div style="position:absolute;top:50%;left:50%;
                        transform:translate(-50%,-50%);
                        width:170px;height:170px;
                        background:radial-gradient(circle,#FFD700 0%,#FFA500 100%);
                        border-radius:50%;
                        box-shadow:0 0 100px #FFD700;
                        display:flex;flex-direction:column;
                        align-items:center;justify-content:center;
                        animation:pulseCart 2s ease-in-out infinite;">
                <div style="font-size:50px;">🛒</div>
                <div style="font-size:16px;font-weight:bold;color:#000;margin-top:5px;">
                    ASYMAS
                </div>
            </div>
        </div>
    </div>

    <style>
    @keyframes pulseRing{
        0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}
        50%{transform:translate(-50%,-50%) scale(1.12);opacity:1;}
    }
    @keyframes pulseCart{
        0%,100%{transform:translate(-50%,-50%) scale(1);}
        50%{transform:translate(-50%,-50%) scale(1.18);}
    }
    @keyframes rotate{
        from{transform:translate(-50%,-50%) rotate(0deg);}
        to{transform:translate(-50%,-50%) rotate(360deg);}
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    pwd = st.text_input("", type="password", placeholder="Mot de passe ASYMAS")

    if pwd:
        try:
            result = supabase.table("utilisateurs").select("*").eq("password", pwd).execute()
        except Exception as e:
            result = None
            st.error("Erreur connexion base utilisateurs")
            st.code(repr(e))

        if result and result.data:
            u = result.data[0]
            st.session_state.logged_in = True
            st.session_state.user_role = u["role"]
            st.session_state.user_name = u["nom"]
            st.session_state.perms = u.get("permissions", {})
            st.session_state.user_cats = u.get("categories_autorisees", [])
            st.rerun()
        elif pwd == "asymas2025":
            st.session_state.logged_in = True
            st.session_state.user_role = "PDG"
            st.session_state.user_name = "PDG"
            st.session_state.perms = {}
            st.session_state.user_cats = []
            st.rerun()

    st.stop()

# ==================================
# ICI : UTILISATEUR CONNECTÉ
# ==================================

# Charger permissions sous forme dict
perms = st.session_state.perms
if isinstance(perms, str):
    try:
        perms = json.loads(perms)
    except:
        perms = {}

# =========================
# ACCUEIL : CERCLE + 6 BOUTONS
# =========================
if st.session_state.selected_module is None:
    # calcul des droits pour les 6 modules
    can_commerce = check_perm("commerce")
    can_auto = check_perm("automobile")
    can_factures = check_perm("factures")
    can_immo = check_perm("immobilier")
    can_stock = check_perm("stock")
    can_compta = check_perm("comptabilite")

    html_buttons = f"""
    <script>
      const perms = {{
        Commerce: {str(can_commerce).lower()},
        Auto: {str(can_auto).lower()},
        Factures: {str(can_factures).lower()},
        Immo: {str(can_immo).lower()},
        Stock: {str(can_stock).lower()},
        Compta: {str(can_compta).lower()}
      }};

      function openModule(mod) {{
        if (!perms[mod]) {{
          alert("⛔ Vous n'avez pas l'autorisation pour " + mod);
          return;
        }}
        window.location.search='?module=' + mod;
      }}
    </script>

    <div style="position:relative;width:100%;height:700px;
                background:radial-gradient(ellipse at center 55%,
                rgba(255,215,0,0.7) 0%, rgba(15,15,15,1) 85%);
                overflow:hidden;">

        <!-- Cercle central (même design que login) -->
        <div style="position:absolute;top:50%;left:50%;
                    transform:translate(-50%,-50%);
                    width:450px;height:450px;">
            <div style="position:absolute;top:50%;left:50%;
                        transform:translate(-50%,-50%);
                        width:380px;height:380px;
                        border:2px solid rgba(255,215,0,0.5);
                        border-radius:50%;
                        box-shadow:0 0 80px rgba(255,215,0,0.8);
                        animation:pulseRing 3s ease-in-out infinite;">
            </div>
            <div style="position:absolute;top:50%;left:50%;
                        transform:translate(-50%,-50%);
                        width:300px;height:300px;
                        border:2px dotted rgba(255,215,0,0.9);
                        border-radius:50%;
                        animation:rotate 15s linear infinite;">
            </div>
            <div style="position:absolute;top:50%;left:50%;
                        transform:translate(-50%,-50%);
                        width:220px;height:220px;
                        border:3px solid #FFD700;
                        border-radius:50%;
                        box-shadow:0 0 90px #FFD700;">
            </div>
            <div style="position:absolute;top:50%;left:50%;
                        transform:translate(-50%,-50%);
                        width:170px;height:170px;
                        background:radial-gradient(circle,#FFD700 0%,#FFA500 100%);
                        border-radius:50%;
                        box-shadow:0 0 100px #FFD700;
                        display:flex;flex-direction:column;
                        align-items:center;justify-content:center;
                        animation:pulseCart 2s ease-in-out infinite;">
                <div style="font-size:50px;">🛒</div>
                <div style="font-size:16px;font-weight:bold;color:#000;margin-top:5px;">
                    ASYMAS
                </div>
            </div>
        </div>

        <!-- Boutons modules autour -->
        <button onclick="openModule('Commerce')"
            style="position:absolute;top:50%;left:50%;
                   transform:translate(-50%,-50%) rotate(90deg) translate(190px) rotate(-90deg);
                   width:60px;height:60px;
                   border:3px solid #FFD700;border-radius:50%;
                   background:#fff;box-shadow:0 0 25px #FFD700;
                   font-size:11px;font-weight:bold;color:#000;cursor:pointer;">
            🏪<br>Commerce
        </button>

        <button onclick="openModule('Auto')"
            style="position:absolute;top:50%;left:50%;
                   transform:translate(-50%,-50%) rotate(30deg) translate(190px) rotate(-30deg);
                   width:60px;height:60px;
                   border:3px solid #FFD700;border-radius:50%;
                   background:#fff;box-shadow:0 0 25px #FFD700;
                   font-size:11px;font-weight:bold;color:#000;cursor:pointer;">
            🚚<br>Auto
        </button>

        <button onclick="openModule('Factures')"
            style="position:absolute;top:50%;left:50%;
                   transform:translate(-50%,-50%) rotate(-30deg) translate(190px) rotate(30deg);
                   width:60px;height:60px;
                   border:3px solid #FFD700;border-radius:50%;
                   background:#fff;box-shadow:0 0 25px #FFD700;
                   font-size:11px;font-weight:bold;color:#000;cursor:pointer;">
            🧾<br>Factures
        </button>

        <button onclick="openModule('Immo')"
            style="position:absolute;top:50%;left:50%;
                   transform:translate(-50%,-50%) rotate(-90deg) translate(190px) rotate(90deg);
                   width:60px;height:60px;
                   border:3px solid #FFD700;border-radius:50%;
                   background:#fff;box-shadow:0 0 25px #FFD700;
                   font-size:11px;font-weight:bold;color:#000;cursor:pointer;">
            🏠<br>Immo
        </button>

        <button onclick="openModule('Stock')"
            style="position:absolute;top:50%;left:50%;
                   transform:translate(-50%,-50%) rotate(-150deg) translate(190px) rotate(150deg);
                   width:60px;height:60px;
                   border:3px solid #FFD700;border-radius:50%;
                   background:#fff;box-shadow:0 0 25px #FFD700;
                   font-size:11px;font-weight:bold;color:#000;cursor:pointer;">
            📦<br>Stock
        </button>

        <button onclick="openModule('Compta')"
            style="position:absolute;top:50%;left:50%;
                   transform:translate(-50%,-50%) rotate(150deg) translate(190px) rotate(-150deg);
                   width:60px;height:60px;
                   border:3px solid #FFD700;border-radius:50%;
                   background:#fff;box-shadow:0 0 25px #FFD700;
                   font-size:11px;font-weight:bold;color:#000;cursor:pointer;">
            📊<br>Compta
        </button>
    </div>

    <style>
    @keyframes pulseRing{
        0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.7;}
        50%{transform:translate(-50%,-50%) scale(1.12);opacity:1;}
    }
    @keyframes pulseCart{
        0%,100%{transform:translate(-50%,-50%) scale(1);}
        50%{transform:translate(-50%,-50%) scale(1.18);}
    }
    @keyframes rotate{
        from{transform:translate(-50%,-50%) rotate(0deg);}
        to{transform:translate(-50%,-50%) rotate(360deg);}
    }
    </style>
    """

    components.html(html_buttons, height=700)

    # petit menu basique pour déconnexion
    col_logout, col_empty = st.columns([1, 5])
    with col_logout:
        if st.button("🚪 Déconnexion"):
            st.session_state.clear()
            st.rerun()

    # on s'arrête là sur la page d'accueil
    st.stop()

# =====================================================
# SI ON ARRIVE ICI : UN MODULE EST SELECTIONNÉ
# =====================================================

# barre latérale commune
with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.user_name}")
    st.markdown(f"**Rôle : {st.session_state.user_role}**")
    st.info("ASYMAS BUSINESS v3.0")
    if st.button("🏠 Retour Accueil"):
        st.session_state.selected_module = None
        st.query_params.clear()
        st.rerun()
    if st.button("🔄 Actualiser"):
        st.cache_data.clear()
        st.rerun()
    if st.button("🔒 Déconnexion"):
        st.session_state.clear()
        st.rerun()

# chargement global des tables pour les modules
df_biens = load_table("biens")
df_articles = load_table("articles")
df_voitures = load_table("voitures")
df_compta = load_table("compta")
df_factures = load_table("factures_proforma")
df_devis = load_table("devis")
df_utilisateurs = load_table("utilisateurs")

if "montant" not in df_compta.columns:
    df_compta["montant"] = 0
if "type" not in df_compta.columns:
    df_compta["type"] = "Inconnu"
if "date" in df_compta.columns:
    df_compta["date"] = pd.to_datetime(df_compta["date"], errors="coerce")
    df_compta = df_compta.sort_values("date", ascending=False)

# Vérification permission du module demandé
perm_map = {
    "Commerce": "commerce",
    "Stock": "stock",
    "Immo": "immobilier",
    "Auto": "automobile",
    "Compta": "comptabilite",
    "Factures": "factures",
}
module = st.session_state.selected_module
perm_key = perm_map.get(module, "")

if perm_key and not check_perm(perm_key):
    st.error(f"⛔ Pas d'autorisation pour {module}")
    if st.button("← Retour Accueil"):
        st.session_state.selected_module = None
        st.query_params.clear()
        st.rerun()
    st.stop()

# entête module
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown(f"# ASYMAS BUSINESS - {st.session_state.user_name}")
    st.markdown(f"### Module : {module}")
with col2:
    if st.button("← Retour Accueil"):
        st.session_state.selected_module = None
        st.query_params.clear()
        st.rerun()

st.divider()

# ====================
# MODULE : COMMERCE
# ====================
if module == "Commerce":
    st.markdown("## 🛍️ Commerce - Point de Vente")

    if "panier_commerce" not in st.session_state:
        st.session_state.panier_commerce = []
    if "vente_finie" not in st.session_state:
        st.session_state.vente_finie = False
    if "pdf_data" not in st.session_state:
        st.session_state.pdf_data = None
    if "num_fact" not in st.session_state:
        st.session_state.num_fact = None
    if "client_com_nom" not in st.session_state:
        st.session_state.client_com_nom = ""
    if "client_com_tel" not in st.session_state:
        st.session_state.client_com_tel = "+243..."
    if "last_qr" not in st.session_state:
        st.session_state.last_qr = ""

    col_gauche, col_droite = st.columns([2, 1])

    with col_gauche:
        st.subheader("👤 Client")
        st.session_state.client_com_nom = st.text_input(
            "Nom Client", value=st.session_state.client_com_nom, key="nom_client_c"
        )
        st.session_state.client_com_tel = st.text_input(
            "Téléphone Client", value=st.session_state.client_com_tel, key="tel_client_c"
        )

        st.subheader("🔍 Scanner QR Code")
        col_scan1, col_scan2 = st.columns([2, 1])
        with col_scan1:
            qr_code = qrcode_scanner(key="qr_commerce_unique")
        with col_scan2:
            recherche_manuelle = st.text_input(
                "🔎 Recherche manuelle",
                placeholder="Tape le nom...",
                key="search_man_c",
            )

        if qr_code and qr_code != st.session_state.last_qr:
            st.session_state.last_qr = qr_code
            st.rerun()

        df_articles_filtre = df_articles[df_articles["stock"] > 0].copy()

        if qr_code:
            qr_clean = str(qr_code).strip().upper()
            df_articles_filtre = df_articles_filtre[
                df_articles_filtre["code_qr"]
                .astype(str)
                .str.strip()
                .str.upper()
                == qr_clean
            ]
        elif recherche_manuelle:
            mask = df_articles_filtre["nom_article"].str.contains(
                recherche_manuelle, case=False, na=False
            )
            df_articles_filtre = df_articles_filtre[mask]

        if df_articles_filtre.empty:
            st.warning("Aucun produit disponible")
        else:
            options_articles = []
            for _, p in df_articles_filtre.iterrows():
                qr_txt = f" | QR:{p['code_qr']}" if "code_qr" in p and p["code_qr"] else ""
                prix_usd = (
                    f" | {p['prix_vente_usd']:,.2f}$" if "prix_vente_usd" in p else ""
                )
                options_articles.append(
                    f"{p['nom_article']} | Stock:{int(p['stock'])} | "
                    f"{p['prix_vente']:,.0f} FC{prix_usd}{qr_txt} | ID:{p['id']}"
                )

            article_choisi = st.selectbox(
                "Sélectionne le produit", options_articles, key="select_article_unique"
            )

            if article_choisi:
                id_choisi = int(article_choisi.split("ID:")[1])
                p = df_articles_filtre[df_articles_filtre["id"] == id_choisi].iloc[0]
                c1, c2, c3 = st.columns(3)
                qte_max = int(p["stock"])
                qte = c1.number_input(
                    "Quantité",
                    min_value=1,
                    max_value=qte_max,
                    value=1,
                    key="qte_c_unique",
                )
                c2.metric("Stock dispo", qte_max)
                c3.metric("Prix unitaire", f"{p['prix_vente']:,.0f} FC")

                if st.button(
                    "🛒 AJOUTER AU PANIER",
                    type="primary",
                    use_container_width=True,
                    key="add_article_unique",
                ):
                    existant = next(
                        (
                            item
                            for item in st.session_state.panier_commerce
                            if item["id"] == int(p["id"])
                        ),
                        None,
                    )
                    if existant:
                        if existant["qte"] + qte <= qte_max:
                            existant["qte"] += qte
                            st.success(f"Panier mis à jour: {existant['qte']}x")
                        else:
                            st.error(f"Stock insuffisant! Max dispo: {qte_max}")
                    else:
                        st.session_state.panier_commerce.append(
                            {
                                "id": int(p["id"]),
                                "nom": str(p["nom_article"]),
                                "pu": float(p["prix_vente"]),
                                "qte": int(qte),
                                "code_qr": p.get("code_qr", ""),
                                "stock_max": qte_max,
                            }
                        )
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
                use_container_width=True,
            )
            if st.button("NOUVELLE VENTE", use_container_width=True):
                st.session_state.vente_finie = False
                st.session_state.pdf_data = None
                st.session_state.num_fact = None
                st.session_state.client_com_nom = ""
                st.session_state.last_qr = ""
                st.rerun()

        elif st.session_state.panier_commerce:
            total_panier = 0
            for i, item in enumerate(st.session_state.panier_commerce):
                col1, col2, col3 = st.columns([4, 2, 1])
                col1.write(f"**{item['nom']}**")
                col2.write(f"Qté: {item['qte']} | {item['pu']:,.0f} FC")
                if col3.button("❌", key=f"d_{i}"):
                    st.session_state.panier_commerce.pop(i)
                    st.rerun()
                total_panier += item["qte"] * item["pu"]

            st.markdown(f"### Total: {total_panier:,.0f} FC")
            if st.button(
                "💾 FINALISER VENTE & FACTURE",
                use_container_width=True,
                type="primary",
            ):
                if not st.session_state.client_com_nom:
                    st.error("Nom du client obligatoire!")
                else:
                    num_fact = f"VTE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    details_list = []
                    for item in st.session_state.panier_commerce:
                        supabase.table("ventes").insert(
                            {
                                "numero_facture": num_fact,
                                "client_nom": st.session_state.client_com_nom,
                                "article_id": item["id"],
                                "quantite": item["qte"],
                                "prix_unitaire": item["pu"],
                                "total": item["qte"] * item["pu"],
                            }
                        ).execute()
                        stock_actuel = df_articles[
                            df_articles["id"] == item["id"]
                        ]["stock"].iloc[0]
                        supabase.table("articles").update(
                            {"stock": int(stock_actuel - item["qte"])}
                        ).eq("id", item["id"]).execute()
                        details_list.append(
                            {
                                "nom": item["nom"],
                                "qte": item["qte"],
                                "pu": item["pu"],
                                "total": item["qte"] * item["pu"],
                            }
                        )
                    details_json = json.dumps(details_list)
                    supabase.table("compta").insert(
                        {
                            "date": str(date.today()),
                            "type": "Revenu",
                            "categorie": "Vente Commerce",
                            "description": f"Vente - {st.session_state.client_com_nom}",
                            "montant": float(total_panier),
                            "devise": "FC",
                            "numero_facture": num_fact,
                            "details": details_json,
                            "utilisateur": st.session_state.user_name,
                        }
                    ).execute()
                    pdf_bytes = generer_pdf_facture(
                        num_fact,
                        "Vente Commerce",
                        st.session_state.client_com_nom,
                        details_list,
                        total_panier,
                        "FC",
                        st.session_state.client_com_tel,
                    )
                    st.session_state.pdf_data = pdf_bytes
                    st.session_state.num_fact = num_fact
                    st.session_state.vente_finie = True
                    st.session_state.panier_commerce = []
                    st.cache_data.clear()
                    st.rerun()

        else:
            st.info("Panier vide")

# ====================
# MODULE : STOCK
# ====================
elif module == "Stock":
    st.markdown("## 📦 Gestion Stock Commerce - Articles & Pertes")

    tab_stock, tab_ajout, tab_mvt, tab_pertes = st.tabs(
        ["📊 Stock Actuel", "➕ Ajouter Article", "📈 Mouvements", "⚠️ Pertes & Casses"]
    )

    with tab_stock:
        st.subheader("📊 Stock Actuel Commerce")
        if df_articles.empty:
            st.info("Aucun article en stock")
        else:
            for _, row in df_articles.iterrows():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(
                        f"**{row['nom_article']}** - {row.get('categorie','')} - "
                        f"QR:{row.get('code_qr','N/A')}"
                    )
                with col2:
                    stock_val = int(row.get("stock", 0))
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
                        new_nom = st.text_input(
                            "Nom", value=row["nom_article"], key=f"nom_art_{row['id']}"
                        )
                        new_cat = st.text_input(
                            "Catégorie",
                            value=row.get("categorie", ""),
                            key=f"cat_art_{row['id']}",
                        )
                        new_code_qr = st.text_input(
                            "Code QR",
                            value=row.get("code_qr", ""),
                            key=f"qr_art_{row['id']}",
                        )
                    with c2:
                        new_prix_a = st.number_input(
                            "Prix Achat FC",
                            value=float(row.get("prix_achat", 0)),
                            key=f"pa_art_{row['id']}",
                        )
                        new_prix_v = st.number_input(
                            "Prix Vente FC",
                            value=float(row.get("prix_vente", 0)),
                            key=f"pv_art_{row['id']}",
                        )
                        new_prix_usd = st.number_input(
                            "Prix Vente $",
                            value=float(row.get("prix_vente_usd", 0)),
                            key=f"pusd_art_{row['id']}",
                        )
                    with c3:
                        new_stock = st.number_input(
                            "Stock",
                            value=int(row.get("stock", 0)),
                            key=f"stock_art_{row['id']}",
                        )

                    c1b, c2b = st.columns(2)
                    if c1b.button(
                        "✏️ Modifier",
                        key=f"mod_art_{row['id']}",
                        use_container_width=True,
                    ):
                        data_update = {
                            "nom_article": str(new_nom),
                            "categorie": str(new_cat),
                            "prix_achat": float(new_prix_a),
                            "prix_vente": float(new_prix_v),
                            "stock": int(new_stock),
                            "code_qr": str(new_code_qr) if new_code_qr else None,
                            "prix_vente_usd": float(new_prix_usd),
                        }
                        supabase.table("articles").update(data_update).eq(
                            "id", int(row["id"])
                        ).execute()
                        st.success("Modifié")
                        st.cache_data.clear()
                        st.rerun()

                    if st.session_state.user_role == "PDG" or perms.get(
                        "supprimer", False
                    ):
                        if c2b.button(
                            "🗑️ Supprimer",
                            key=f"del_art_{row['id']}",
                            use_container_width=True,
                        ):
                            supabase.table("articles").delete().eq(
                                "id", int(row["id"])
                            ).execute()
                            st.success("Supprimé")
                            st.cache_data.clear()
                            st.rerun()

    with tab_ajout:
        st.subheader("➕ Ajouter Nouvel Article Commerce")
        qr_scan_ajout = qrcode_scanner(key="qr_add_article_com")
        if qr_scan_ajout:
            st.success(f"QR scanné : {qr_scan_ajout}")
            st.session_state.qr_code_temp = qr_scan_ajout

        with st.form("form_article_com", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nom = c1.text_input("Nom Article")
            cat = c2.text_input("Catégorie")
            code_qr = c3.text_input(
                "Code QR", value=st.session_state.get("qr_code_temp", "")
            )

            c1b, c2b, c3b = st.columns(3)
            prix_achat_fc = c1b.number_input("Prix Achat FC", min_value=0.0)
            prix_vente_fc = c2b.number_input("Prix Vente FC", min_value=0.0)
            prix_vente_usd = c3b.number_input("Prix Vente $", min_value=0.0)
            stock = c1b.number_input("Stock Initial", min_value=0)

            if st.form_submit_button("💾 Ajouter Article"):
                data_insert = {
                    "nom_article": str(nom),
                    "categorie": str(cat),
                    "prix_achat": float(prix_achat_fc),
                    "prix_vente": float(prix_vente_fc),
                    "stock": int(stock),
                    "code_qr": str(code_qr) if code_qr else None,
                    "prix_vente_usd": float(prix_vente_usd),
                }
                supabase.table("articles").insert(data_insert).execute()
                st.success(f"Article {nom} ajouté")
                if "qr_code_temp" in st.session_state:
                    del st.session_state.qr_code_temp
                st.cache_data.clear()
                st.rerun()

    with tab_mvt:
        st.subheader("📈 Mouvements de Stock Commerce")
        try:
            mvts = (
                supabase.table("mouvements_stock")
                .select("*")
                .order("created_at", desc=True)
                .limit(50)
                .execute()
                .data
            )
        except:
            mvts = []

        if not mvts:
            st.info("Aucun mouvement enregistré")
        else:
            df_mvt = pd.DataFrame(mvts)
            cols_aff = [
                c
                for c in [
                    "article_nom",
                    "type",
                    "quantite",
                    "motif",
                    "created_by",
                    "created_at",
                ]
                if c in df_mvt.columns
            ]
            st.dataframe(
                df_mvt[cols_aff], use_container_width=True, hide_index=True
            )

    with tab_pertes:
        st.subheader("⚠️ Déclarer Perte/Casse Article Commerce")

        articles_dispo = (
            df_articles[df_articles["stock"] > 0].copy()
            if not df_articles.empty
            else pd.DataFrame()
        )

        if articles_dispo.empty:
            st.warning("Aucun article en stock pour déclarer une perte")
        else:
            col1p, col2p = st.columns(2)
            with col1p:
                article_dict = {
                    f"{a['nom_article']} - Stock:{int(a['stock'])}": a
                    for _, a in articles_dispo.iterrows()
                }
                article_choisi = st.selectbox(
                    "Article abîmé/perdu", list(article_dict.keys())
                )
                qte_perte = st.number_input(
                    "Quantité abîmée",
                    min_value=1,
                    max_value=int(article_dict[article_choisi]["stock"])
                    if article_choisi
                    else 1,
                )
            with col2p:
                motif_perte = st.selectbox(
                    "Motif",
                    [
                        "Casse",
                        "Vol",
                        "Péremption",
                        "Défaut fabrication",
                        "Accident",
                        "Autre",
                    ],
                )
                detail_perte = st.text_area(
                    "Détails", placeholder="Ex: Carton mouillé lors livraison"
                )
                responsable = st.text_input(
                    "Déclaré par", value=st.session_state.user_name
                )

            if article_choisi:
                article_data = article_dict[article_choisi]
                valeur_perte = qte_perte * float(article_data.get("prix_achat", 0))
                st.error(f"💸 Valeur de la perte : {valeur_perte:,.0f} FC")

            if st.button(
                "🚨 ENREGISTRER LA PERTE",
                type="primary",
                use_container_width=True,
            ):
                if article_choisi and qte_perte > 0:
                    article_data = article_dict[article_choisi]
                    nouveau_stock = int(article_data["stock"]) - qte_perte
                    supabase.table("articles").update(
                        {"stock": nouveau_stock}
                    ).eq("id", int(article_data["id"])).execute()
                    supabase.table("mouvements_stock").insert(
                        {
                            "article_id": int(article_data["id"]),
                            "article_nom": str(article_data["nom_article"]),
                            "type": "PERTE",
                            "quantite": -int(qte_perte),
                            "motif": f"{motif_perte} - {detail_perte}",
                            "valeur": float(valeur_perte),
                            "created_by": responsable,
                            "created_at": datetime.now().isoformat(),
                        }
                    ).execute()
                    st.success(
                        f"✅ Perte enregistrée. Nouveau stock {article_data['nom_article']}: {nouveau_stock}"
                    )
                    st.cache_data.clear()
                    st.rerun()

        st.divider()
        st.subheader("📋 Historique Pertes Commerce")
        try:
            pertes = (
                supabase.table("mouvements_stock")
                .select("*")
                .eq("type", "PERTE")
                .order("created_at", desc=True)
                .limit(20)
                .execute()
                .data
            )
        except:
            pertes = []

        if not pertes:
            st.info("Aucune perte enregistrée")
        else:
            total_pertes = sum(p.get("valeur", 0) for p in pertes)
            st.metric("💸 TOTAL PERTES COMMERCE", f"{total_pertes:,.0f} FC")
            for p in pertes:
                with st.expander(
                    f"🔴 {p.get('article_nom')} - "
                    f"{abs(p.get('quantite',0))} - "
                    f"{p.get('created_at','')[:10]}"
                ):
                    c1p, c2p, c3p = st.columns(3)
                    with c1p:
                        st.write(f"**Qté perdue:** {abs(p.get('quantite', 0))}")
                        st.write(f"**Valeur:** {p.get('valeur', 0):,.0f} FC")
                    with c2p:
                        st.write(f"**Motif:** {p.get('motif', 'N/A')}")
                        st.write(f"**Par:** {p.get('created_by', 'N/A')}")
                    with c3p:
                        if st.session_state.user_role == "PDG":
                            if st.button(
                                "🗑️ Supprimer",
                                key=f"del_perte_com_{p.get('id')}",
                            ):
                                supabase.table("mouvements_stock").delete().eq(
                                    "id", p.get("id")
                                ).execute()
                                st.rerun()

# ====================
# MODULE : IMMO
# ====================
elif module == "Immo":
    st.markdown("## 🏠 Immobilier - Générer Facture")
    nom_client = st.text_input("👤 Nom du client", key="nom_client_bien")
    tel_client = st.text_input(
        "Téléphone Client", value="+243...", key="tel_client_bien"
    )
    col1i, col2i, col3i = st.columns(3)
    with col1i:
        type_bien = st.selectbox(
            "Type", ["Maison", "Appartement", "Bureau", "Terrain"], key="type_bien"
        )
        adresse = st.text_input("Adresse", key="adresse_bien")
    with col2i:
        prix = st.number_input("💰 Loyer USD", min_value=0.0, key="prix_bien")
        electricite = st.number_input(
            "⚡ Électricité USD", min_value=0.0, key="elec_bien"
        )
    with col3i:
        eau = st.number_input("💧 Eau USD", min_value=0.0, key="eau_bien")
        duree_contrat = st.text_input(
            "📅 Durée", placeholder="Ex: 6 mois", key="duree_bien"
        )

    total_mensuel = float(prix) + float(electricite) + float(eau)
    st.info(f"💎 **TOTAL : {total_mensuel:,.2f} USD**")

    if st.button(
        "📄 GÉNÉRER FACTURE PDF",
        type="primary",
        use_container_width=True,
        key="btn_facture_immo",
    ):
        if nom_client and adresse:
            details_list = [
                {
                    "nom": f"Loyer {type_bien} | Adresse: {adresse} | Duree: {duree_contrat}",
                    "qte": 1,
                    "pu": prix,
                },
                {
                    "nom": f"Electricite | {type_bien} - {adresse}",
                    "qte": 1,
                    "pu": electricite,
                },
                {"nom": f"Eau | {type_bien} - {adresse}", "qte": 1, "pu": eau},
            ]
            details_text = (
                f"LOUER: {type_bien} | Adresse: {adresse} | "
                f"Duree Contrat: {duree_contrat} | "
                f"Loyer: {prix} $ | Electricite: {electricite} $ | Eau: {eau} $"
            )
            periode = date.today().strftime("%B %Y")
            num_fact, pdf_bytes = creer_facture_auto(
                "Loyer",
                nom_client,
                details_text,
                total_mensuel,
                "$",
                details_list,
                tel_client,
                periode,
                "Proforma",
            )
            st.success(f"✅ Facture générée : {num_fact}")
            st.download_button(
                label="📥 Télécharger Facture PDF",
                data=pdf_bytes,
                file_name=f"{num_fact}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="dl_facture_immo",
            )
            st.cache_data.clear()
        else:
            st.error("Nom client + Adresse obligatoires")

# ====================
# MODULE : AUTO
# ====================
elif module == "Auto":
    st.markdown("## 🚗 Automobile - (Interface simplifiée)")
    if df_voitures.empty:
        st.info("Aucune voiture enregistrée")
    else:
        st.dataframe(df_voitures, use_container_width=True, hide_index=True)
        st.markdown(
            "_Pour une version complète (vente voiture + facture), on peut reprendre le bloc de la première version._"
        )

# ====================
# MODULE : COMPTA
# ====================
elif module == "Compta":
    st.markdown("## 💰 Comptabilité ASYMAS")
    col1c, col2c, col3c = st.columns(3)
    with col1c:
        date_debut = st.date_input(
            "Date début", value=date.today().replace(day=1)
        )
    with col2c:
        date_fin = st.date_input("Date fin", value=date.today())
    with col3c:
        type_filter = st.selectbox("Type", ["Tous", "Revenu", "Dépense"])

    df_filtre = df_compta.copy()
    if not df_filtre.empty and "date" in df_filtre.columns:
        df_filtre = df_filtre[
            (df_filtre["date"].dt.date >= date_debut)
            & (df_filtre["date"].dt.date <= date_fin)
        ]
    if type_filter != "Tous":
        df_filtre = df_filtre[df_filtre["type"] == type_filter]

    if not df_filtre.empty:
        total_rev = df_filtre[df_filtre["type"] == "Revenu"]["montant"].sum()
        total_dep = df_filtre[df_filtre["type"] == "Dépense"]["montant"].sum()
        solde = total_rev - total_dep
        c1m, c2m, c3m = st.columns(3)
        c1m.metric("💰 Revenus", f"{total_rev:,.0f} FC")
        c2m.metric("💸 Dépenses", f"{total_dep:,.0f} FC")
        c3m.metric("💎 Solde", f"{solde:,.0f} FC")

        excel_data = generer_excel_pro(
            df_filtre,
            f"Relevé {date_debut} au {date_fin}",
            total_rev,
            total_dep,
            solde,
        )
        st.download_button(
            "📥 Télécharger Excel Pro",
            data=excel_data,
            file_name=f"releve_compta_{date_debut}_{date_fin}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        st.dataframe(df_filtre, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune donnée sur cette période")

# ====================
# MODULE : FACTURES
# ====================
elif module == "Factures":
    st.markdown("## 📄 Gestion Factures & Proformas")

    # Historique factures simples / proformas
    st.subheader("Historique Factures")
    if df_factures.empty:
        st.info("Aucune facture générée")
    else:
        st.dataframe(df_factures, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📄 Facture rapide (saisie manuelle)")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        client_f = st.text_input("Client", key="fast_client")
        desc_f = st.text_area("Désignation / Détails", key="fast_desc")
    with col_f2:
        montant_f = st.number_input("Montant", min_value=0.0, key="fast_montant")
        devise_f = st.selectbox("Devise", ["FC", "USD", "€"], key="fast_devise")
        tel_f = st.text_input("Téléphone client", value="+243...", key="fast_tel")

    if st.button("📄 Générer Facture rapide", type="primary", use_container_width=True):
        if not client_f or montant_f <= 0:
            st.error("Client et Montant obligatoires")
        else:
            details_list = [{
                "nom": desc_f or "Facture rapide",
                "qte": 1,
                "pu": montant_f
            }]
            num, pdf_bytes = creer_facture_auto(
                "Facture rapide",
                client_f,
                desc_f or "Facture rapide",
                montant_f,
                devise_f,
                details_list,
                tel_f,
                "",
                "Simple",
            )
            st.success(f"✅ Facture générée : {num}")
            st.download_button(
                "📥 Télécharger Facture PDF",
                data=pdf_bytes,
                file_name=f"{num}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

# ====================
# MODULE : DEVIS
# ====================
elif module == "Devis":
    st.markdown("## 📋 Devis ASYMAS Consulting")

    # Droits devis
    can_devis_ind = check_perm("devis_industriel")
    can_devis_bat = check_perm("devis_batiment")
    can_devis_hist = check_perm("devis_historique")

    if not (can_devis_ind or can_devis_bat or can_devis_hist):
        st.error("⛔ Vous n'avez pas l'autorisation d'accéder aux devis.")
        st.stop()

    tabs_devis = []
    if can_devis_ind:
        tabs_devis.append("🏭 Devis Industriel")
    if can_devis_bat:
        tabs_devis.append("🏗️ Devis Bâtiment")
    if can_devis_hist:
        tabs_devis.append("📚 Historique")

    t_objects = st.tabs(tabs_devis)
    name_to_tab = dict(zip(tabs_devis, t_objects))

    # -------- Devis Industriel --------
    if "🏭 Devis Industriel" in name_to_tab:
        with name_to_tab["🏭 Devis Industriel"]:
            st.subheader("Devis Industriel (version simplifiée)")

            col_i1, col_i2 = st.columns(2)
            with col_i1:
                client_ind = st.text_input("Client", key="client_ind")
                loc_ind = st.text_input("Localisation", value="Beni, RDC", key="loc_ind")
            with col_i2:
                tel_ind = st.text_input("Téléphone", value="+243...", key="tel_ind")
                devise_ind = st.selectbox("Devise", ["USD", "FC", "€"], key="devise_ind")

            titre_ind = st.text_input("Titre Projet", key="titre_ind")
            parcelle_ind = st.text_input("Parcelle (optionnel)", key="parcelle_ind")

            st.markdown("### Lignes de devis")
            des1 = st.text_input("Désignation 1", key="des1_ind", value="Prestation industrielle")
            qte1 = st.number_input("Qté 1", min_value=0.0, value=1.0, key="qte1_ind")
            pu1 = st.number_input("Prix unitaire 1", min_value=0.0, value=0.0, key="pu1_ind")

            des2 = st.text_input("Désignation 2", key="des2_ind", value="")
            qte2 = st.number_input("Qté 2", min_value=0.0, value=0.0, key="qte2_ind")
            pu2 = st.number_input("Prix unitaire 2", min_value=0.0, value=0.0, key="pu2_ind")

            main_oeuvre_ind = st.number_input(
                "Main d'oeuvre globale", min_value=0.0, value=0.0, key="mo_ind"
            )

            items = []
            if des1 and qte1 > 0 and pu1 > 0:
                items.append({
                    "num": "1.1",
                    "designation": des1,
                    "unite": "Forfait",
                    "qte": qte1,
                    "pu": pu1,
                })
            if des2 and qte2 > 0 and pu2 > 0:
                items.append({
                    "num": "1.2",
                    "designation": des2,
                    "unite": "Forfait",
                    "qte": qte2,
                    "pu": pu2,
                })

            sections = [{
                "numero": "1",
                "titre": titre_ind or "Prestation industrielle",
                "items": items,
            }]

            total_lignes = sum(it["qte"] * it["pu"] for it in items)
            total_general = total_lignes + main_oeuvre_ind
            st.metric("Montant estimatif", f"{total_general:,.2f} {devise_ind}")

            if st.button("📄 Générer Devis Industriel", type="primary", use_container_width=True):
                if client_ind and titre_ind and items:
                    num_devis = f"DEV-IND-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    pdf_bytes = generer_pdf_devis_consulting(
                        num_devis,
                        "Industriel",
                        client_ind,
                        titre_ind,
                        parcelle_ind,
                        loc_ind,
                        sections,
                        devise_ind,
                        tel_ind,
                        main_oeuvre_ind,
                    )
                    # enregistrement base
                    try:
                        supabase.table("devis").insert({
                            "numero": num_devis,
                            "type": "Industriel",
                            "client": client_ind,
                            "telephone": tel_ind,
                            "titre": titre_ind,
                            "parcelle": parcelle_ind,
                            "localisation": loc_ind,
                            "sections": json.dumps(sections, ensure_ascii=False),
                            "main_oeuvre": main_oeuvre_ind,
                            "total": float(total_general),
                            "devise": devise_ind,
                            "created_by": st.session_state.user_name,
                            "created_at": datetime.now().isoformat(),
                        }).execute()
                    except Exception as e:
                        st.error("Erreur enregistrement devis industriel")
                        st.code(repr(e))

                    st.success(f"✅ Devis {num_devis} généré")
                    st.download_button(
                        "📥 Télécharger Devis Industriel",
                        data=pdf_bytes,
                        file_name=f"{num_devis}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.error("Client, Titre et au moins une ligne de devis sont obligatoires")

    # -------- Devis Bâtiment --------
    if "🏗️ Devis Bâtiment" in name_to_tab:
        with name_to_tab["🏗️ Devis Bâtiment"]:
            st.subheader("Devis Bâtiment (version simplifiée)")

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                client_b = st.text_input("Client", key="client_bat")
                loc_b = st.text_input("Localisation", value="Beni, RDC", key="loc_bat")
            with col_b2:
                tel_b = st.text_input("Téléphone", value="+243...", key="tel_bat")
                devise_b = st.selectbox("Devise", ["USD", "FC", "€"], key="devise_bat")

            titre_b = st.text_input("Titre Projet", key="titre_bat")
            parcelle_b = st.text_input("Parcelle (optionnel)", key="parcelle_bat")

            st.markdown("### Lignes de devis")
            des1b = st.text_input("Désignation 1", key="des1_bat", value="Prestation bâtiment")
            qte1b = st.number_input("Qté 1", min_value=0.0, value=1.0, key="qte1_bat")
            pu1b = st.number_input("Prix unitaire 1", min_value=0.0, value=0.0, key="pu1_bat")

            des2b = st.text_input("Désignation 2", key="des2_bat", value="")
            qte2b = st.number_input("Qté 2", min_value=0.0, value=0.0, key="qte2_bat")
            pu2b = st.number_input("Prix unitaire 2", min_value=0.0, value=0.0, key="pu2_bat")

            main_oeuvre_b = st.number_input(
                "Main d'oeuvre globale", min_value=0.0, value=0.0, key="mo_bat"
            )

            items_b = []
            if des1b and qte1b > 0 and pu1b > 0:
                items_b.append({
                    "num": "1.1",
                    "designation": des1b,
                    "unite": "Forfait",
                    "qte": qte1b,
                    "pu": pu1b,
                })
            if des2b and qte2b > 0 and pu2b > 0:
                items_b.append({
                    "num": "1.2",
                    "designation": des2b,
                    "unite": "Forfait",
                    "qte": qte2b,
                    "pu": pu2b,
                })

            sections_b = [{
                "numero": "1",
                "titre": titre_b or "Prestation bâtiment",
                "items": items_b,
            }]

            total_lignes_b = sum(it["qte"] * it["pu"] for it in items_b)
            total_general_b = total_lignes_b + main_oeuvre_b
            st.metric("Montant estimatif", f"{total_general_b:,.2f} {devise_b}")

            if st.button("📄 Générer Devis Bâtiment", type="primary", use_container_width=True):
                if client_b and titre_b and items_b:
                    num_devis_b = f"DEV-BAT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    pdf_bytes_b = generer_pdf_devis_consulting(
                        num_devis_b,
                        "Bâtiment",
                        client_b,
                        titre_b,
                        parcelle_b,
                        loc_b,
                        sections_b,
                        devise_b,
                        tel_b,
                        main_oeuvre_b,
                    )
                    try:
                        supabase.table("devis").insert({
                            "numero": num_devis_b,
                            "type": "Bâtiment",
                            "client": client_b,
                            "telephone": tel_b,
                            "titre": titre_b,
                            "parcelle": parcelle_b,
                            "localisation": loc_b,
                            "sections": json.dumps(sections_b, ensure_ascii=False),
                            "main_oeuvre": main_oeuvre_b,
                            "total": float(total_general_b),
                            "devise": devise_b,
                            "created_by": st.session_state.user_name,
                            "created_at": datetime.now().isoformat(),
                        }).execute()
                    except Exception as e:
                        st.error("Erreur enregistrement devis bâtiment")
                        st.code(repr(e))

                    st.success(f"✅ Devis {num_devis_b} généré")
                    st.download_button(
                        "📥 Télécharger Devis Bâtiment",
                        data=pdf_bytes_b,
                        file_name=f"{num_devis_b}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.error("Client, Titre et au moins une ligne de devis sont obligatoires")

    # -------- Historique --------
    if "📚 Historique" in name_to_tab:
        with name_to_tab["📚 Historique"]:
            st.subheader("Historique des devis")
            if df_devis.empty:
                st.info("Aucun devis enregistré")
            else:
                st.dataframe(df_devis, use_container_width=True, hide_index=True)

# ====================
# MODULE : UTILISATEURS
# ====================
elif module == "Utilisateurs":
    # seul PDG ou perms.users
    if not (st.session_state.user_role == "PDG" or check_perm("users")):
        st.error("⛔ Vous n'avez pas l'autorisation pour gérer les utilisateurs.")
        st.stop()

    st.markdown("## 👥 Gestion Utilisateurs - Droits d'Accès")

    # Ajout utilisateur
    with st.expander("➕ Ajouter Nouvel Utilisateur", expanded=True):
        with st.form("form_user", clear_on_submit=True):
            c1u, c2u, c3u = st.columns(3)
            nom_user = c1u.text_input("Nom *", placeholder="Ex: Jean KABAMBA")
            role_user = c2u.selectbox(
                "Rôle *", ["PDG", "GERANTE", "UTILISATEUR", "CAISSIER", "COMMERCIAL"]
            )
            pwd_user = c3u.text_input("Mot de passe *", type="password")

            st.markdown("**🔐 Autorisations d'onglets :**")
            col1p, col2p, col3p, col4p = st.columns(4)
            perm_dashboard = col1p.checkbox("Dashboard", value=True)
            perm_commerce = col2p.checkbox("Commerce", value=True)
            perm_stock = col3p.checkbox("Gestion Stock")
            perm_immobilier = col4p.checkbox("Immobilier")
            perm_automobile = col1p.checkbox("Automobile")
            perm_parc = col2p.checkbox("Gestion Parc")
            perm_comptabilite = col3p.checkbox("Comptabilité")
            perm_factures = col4p.checkbox("Factures")
            perm_supprimer = col1p.checkbox("🗑️ Peut Supprimer")
            perm_users = col2p.checkbox("👥 Gérer Utilisateurs")

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
            cats_dispo = (
                sorted(df_compta["categorie"].dropna().unique().tolist())
                if "categorie" in df_compta.columns
                else []
            )
            cats_autorisees = st.multiselect(
                "Catégories visibles dans Factures",
                ["Toutes"] + cats_dispo,
                default=["Toutes"],
                key="cats_factures",
            )

            if st.form_submit_button("💾 Ajouter Utilisateur", type="primary"):
                if nom_user and pwd_user:
                    try:
                        perms_dict = {
                            "dashboard": perm_dashboard,
                            "commerce": perm_commerce,
                            "stock": perm_stock,
                            "immobilier": perm_immobilier,
                            "automobile": perm_automobile,
                            "parc": perm_parc,
                            "comptabilite": perm_comptabilite,
                            "factures": perm_factures,
                            "supprimer": perm_supprimer,
                            "users": perm_users,
                            "devis_industriel": perm_devis_ind,
                            "devis_industriel_download": perm_devis_ind_dl,
                            "devis_industriel_print": perm_devis_ind_pr,
                            "devis_batiment": perm_devis_bat,
                            "devis_batiment_download": perm_devis_bat_dl,
                            "devis_batiment_print": perm_devis_bat_pr,
                            "devis_historique": perm_devis_hist,
                        }
                        supabase.table("utilisateurs").insert({
                            "nom": nom_user,
                            "role": role_user,
                            "password": pwd_user,
                            "permissions": perms_dict,
                            "categories_autorisees": cats_autorisees
                            if "Toutes" not in cats_autorisees
                            else [],
                        }).execute()
                        st.success(f"Utilisateur {nom_user} ajouté")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout utilisateur")
                        st.code(repr(e))
                else:
                    st.error("Nom et mot de passe obligatoires")

    st.divider()
    st.subheader("📋 Liste des Utilisateurs")
    if df_utilisateurs.empty:
        st.info("Aucun utilisateur")
    else:
        for _, user in df_utilisateurs.iterrows():
            current_perms = user.get("permissions", {})
            if isinstance(current_perms, str):
                try:
                    current_perms = json.loads(current_perms)
                except:
                    current_perms = {}

            with st.expander(f"{user['nom']} - {user['role']}"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.write("**Onglets :**")
                    if current_perms.get("dashboard"): st.write("✅ Dashboard")
                    if current_perms.get("commerce"): st.write("✅ Commerce")
                    if current_perms.get("stock"): st.write("✅ Stock")
                    if current_perms.get("immobilier"): st.write("✅ Immobilier")
                    if current_perms.get("automobile"): st.write("✅ Automobile")
                    if current_perms.get("parc"): st.write("✅ Parc")
                    if current_perms.get("comptabilite"): st.write("✅ Comptabilité")
                    if current_perms.get("factures"): st.write("✅ Factures")
                    if current_perms.get("users"): st.write("✅ Utilisateurs")
                    if current_perms.get("supprimer"): st.write("✅ Supprimer")
                with c2:
                    st.write("**Devis Industriel :**")
                    if current_perms.get("devis_industriel"): st.write("✅ Créer")
                    if current_perms.get("devis_industriel_download"): st.write("✅ Télécharger")
                    if current_perms.get("devis_industriel_print"): st.write("✅ Imprimer")
                with c3:
                    st.write("**Devis Bâtiment :**")
                    if current_perms.get("devis_batiment"): st.write("✅ Créer")
                    if current_perms.get("devis_batiment_download"): st.write("✅ Télécharger")
                    if current_perms.get("devis_batiment_print"): st.write("✅ Imprimer")
                    if current_perms.get("devis_historique"): st.write("✅ Historique")

                st.divider()

                if st.session_state.user_role == "PDG":
                    st.markdown("**✏️ Modifier les autorisations :**")
                    with st.form(f"edit_user_{user['id']}"):
                        col1e, col2e, col3e, col4e = st.columns(4)
                        perm_dashboard_e = col1e.checkbox(
                            "Dashboard",
                            value=current_perms.get("dashboard", False),
                            key=f"edit_dash_{user['id']}",
                        )
                        perm_commerce_e = col2e.checkbox(
                            "Commerce",
                            value=current_perms.get("commerce", False),
                            key=f"edit_com_{user['id']}",
                        )
                        perm_stock_e = col3e.checkbox(
                            "Gestion Stock",
                            value=current_perms.get("stock", False),
                            key=f"edit_stock_{user['id']}",
                        )
                        perm_immobilier_e = col4e.checkbox(
                            "Immobilier",
                            value=current_perms.get("immobilier", False),
                            key=f"edit_immo_{user['id']}",
                        )
                        perm_automobile_e = col1e.checkbox(
                            "Automobile",
                            value=current_perms.get("automobile", False),
                            key=f"edit_auto_{user['id']}",
                        )
                        perm_parc_e = col2e.checkbox(
                            "Gestion Parc",
                            value=current_perms.get("parc", False),
                            key=f"edit_parc_{user['id']}",
                        )
                        perm_comptabilite_e = col3e.checkbox(
                            "Comptabilité",
                            value=current_perms.get("comptabilite", False),
                            key=f"edit_comp_{user['id']}",
                        )
                        perm_factures_e = col4e.checkbox(
                            "Factures",
                            value=current_perms.get("factures", False),
                            key=f"edit_fact_{user['id']}",
                        )
                        perm_supprimer_e = col1e.checkbox(
                            "🗑️ Peut Supprimer",
                            value=current_perms.get("supprimer", False),
                            key=f"edit_sup_{user['id']}",
                        )
                        perm_users_e = col2e.checkbox(
                            "👥 Gérer Utilisateurs",
                            value=current_perms.get("users", False),
                            key=f"edit_users_{user['id']}",
                        )

                        st.markdown("**📋 Devis Industriel :**")
                        col_i1e, col_i2e, col_i3e = st.columns(3)
                        perm_devis_ind_e = col_i1e.checkbox(
                            "Créer",
                            value=current_perms.get("devis_industriel", False),
                            key=f"edit_ind_{user['id']}",
                        )
                        perm_devis_ind_dl_e = col_i2e.checkbox(
                            "Télécharger",
                            value=current_perms.get("devis_industriel_download", False),
                            key=f"edit_ind_dl_{user['id']}",
                        )
                        perm_devis_ind_pr_e = col_i3e.checkbox(
                            "Imprimer",
                            value=current_perms.get("devis_industriel_print", False),
                            key=f"edit_ind_pr_{user['id']}",
                        )

                        st.markdown("**📋 Devis Bâtiment :**")
                        col_b1e, col_b2e, col_b3e, col_b4e = st.columns(4)
                        perm_devis_bat_e = col_b1e.checkbox(
                            "Créer",
                            value=current_perms.get("devis_batiment", False),
                            key=f"edit_bat_{user['id']}",
                        )
                        perm_devis_bat_dl_e = col_b2e.checkbox(
                            "Télécharger",
                            value=current_perms.get("devis_batiment_download", False),
                            key=f"edit_bat_dl_{user['id']}",
                        )
                        perm_devis_bat_pr_e = col_b3e.checkbox(
                            "Imprimer",
                            value=current_perms.get("devis_batiment_print", False),
                            key=f"edit_bat_pr_{user['id']}",
                        )
                        perm_devis_hist_e = col_b4e.checkbox(
                            "Historique",
                            value=current_perms.get("devis_historique", False),
                            key=f"edit_hist_{user['id']}",
                        )

                        col_btn1, col_btn2 = st.columns(2)
                        if col_btn1.form_submit_button(
                            "💾 Enregistrer Modifications",
                            type="primary",
                            use_container_width=True,
                        ):
                            new_perms = {
                                "dashboard": perm_dashboard_e,
                                "commerce": perm_commerce_e,
                                "stock": perm_stock_e,
                                "immobilier": perm_immobilier_e,
                                "automobile": perm_automobile_e,
                                "parc": perm_parc_e,
                                "comptabilite": perm_comptabilite_e,
                                "factures": perm_factures_e,
                                "supprimer": perm_supprimer_e,
                                "users": perm_users_e,
                                "devis_industriel": perm_devis_ind_e,
                                "devis_industriel_download": perm_devis_ind_dl_e,
                                "devis_industriel_print": perm_devis_ind_pr_e,
                                "devis_batiment": perm_devis_bat_e,
                                "devis_batiment_download": perm_devis_bat_dl_e,
                                "devis_batiment_print": perm_devis_bat_pr_e,
                                "devis_historique": perm_devis_hist_e,
                            }
                            try:
                                supabase.table("utilisateurs").update(
                                    {"permissions": new_perms}
                                ).eq("id", int(user["id"])).execute()
                                st.success(f"Permissions de {user['nom']} mises à jour")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur modification permissions")
                                st.code(repr(e))

                    if user["nom"] != st.session_state.user_name:
                        if st.button(
                            "🗑️ Supprimer cet utilisateur",
                            key=f"del_user_{user['id']}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            try:
                                supabase.table("utilisateurs").delete().eq(
                                    "id", int(user["id"])
                                ).execute()
                                st.success(f"Utilisateur {user['nom']} supprimé")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur suppression utilisateur")
                                st.code(repr(e))
                    else:
                        st.info("🔒 Vous ne pouvez pas supprimer votre propre compte")
                else:
                    st.info("🔒 Seul le PDG peut modifier les autorisations")
