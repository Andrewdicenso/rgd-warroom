import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

# --- 1. CONFIGURAZIONE PERCORSI E AMBIENTE (UNIFICATA) ---
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
if str(PROJECT_ROOT / "core") not in sys.path:
    sys.path.append(str(PROJECT_ROOT / "core"))

load_dotenv()

# --- MODULI CORE & AUTH ---
from core.ingestor import IngestoreDati
from core.engine import DataGateway
from core.database import DatabaseAziendale
from core.notifier import Sentinella
from auth.auth import inizializza_sessione, login_utente, logout_utente
from core.experimental_modules.warroom_engine import assegna_categoria_warroom
from core.experimental_modules.reparti_engine import mostra_interfaccia_4_aree, genera_percorso_salvataggio
from visuals import genera_grafico_predittivo

try:
    from simulator import SimulatoreRischio
except Exception as e:
    class SimulatoreRischio: 
        def __init__(self, *args, **kwargs): pass
        def esegui_stress_test(self, *args, **kwargs): return {"probabilita_crisi": 0, "percorsi_raw": None}

# --- 2. CONFIGURAZIONE PAGINA STREAMLIT ---
st.set_page_config(
    page_title="War Room Strategica | RGandja",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. INIZIALIZZAZIONE SESSIONE (UNA SOLA VOLTA) ---
inizializza_sessione() 
db = DatabaseAziendale()
upload_path = os.getenv("UPLOAD_DIR", "/tmp/rgd_uploads")
UPLOAD_DIR = Path(upload_path)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- 4. STILE CSS RGANDJA PREMIUM ---
st.markdown("""
<style>
    .stApp { background-color: #f4f7f9; }
    .warroom-header {
        background: linear-gradient(135deg, #102a43 0%, #243b53 100%);
        padding: 2rem; border-radius: 15px; margin-bottom: 2rem;
        border-bottom: 5px solid #d4af37; box-shadow: 0 10px 20px rgba(0,0,0,0.1); color: white;
    }
    .metric-card {
        background: white; padding: 1.5rem; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;
        border-top: 5px solid #3498db;
    }
    .metric-card .value { font-size: 2.2rem; font-weight: bold; color: #102a43; }
    .welcome-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem; border-radius: 1rem; color: white; margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. LOGICA REGISTRAZIONE PULITA ---
def registra_nuovo_utente(email: str, password: str, conferma: str):
    if not email or password != conferma:
        st.error("Dati non validi o password non coincidenti.")
        return
    try:
        if db.get_utente_by_email(email):
            st.error("Email già registrata.")
            return
        admin_email_env = os.getenv("ADMIN_EMAIL", "andrewdicenso@libero.it").lower()
        ruolo = "admin" if email.lower() == admin_email_env else "user"
        if db.crea_utente(email=email, password=password, ruolo=ruolo, azienda=None):
            st.success(f"✅ Registrazione completata come {ruolo.upper()}.")
            st.balloons()
    except Exception as e:
        st.error(f"Errore tecnico registrazione: {e}")

# --- 6. SCHERMATA AUTH ---
if not st.session_state.autenticato:
    tab_login, tab_register = st.tabs(["🔐 Login", "🆕 Registrazione"])
    with tab_login:
        st.title("🔐 Accesso Utente")
        e_login = st.text_input("Email", key="l_email").strip()
        p_login = st.text_input("Password", type="password", key="l_pwd").strip()
        if st.button("Accedi"):
            if login_utente(db, e_login, p_login): st.rerun()
            else: st.error("Credenziali errate.")
    with tab_register:
        st.title("🆕 Crea account Beta")
        e_reg = st.text_input("Email", key="r_email").strip()
        p_reg = st.text_input("Password", type="password", key="r_pwd").strip()
        c_reg = st.text_input("Conferma", type="password", key="r_conf").strip()
        if st.button("Registrati"): registra_nuovo_utente(e_reg, p_reg, c_reg)
    st.stop()

# --- 7. NAVIGAZIONE ---
user_id, azienda, ruolo = st.session_state.user_id, st.session_state.azienda, st.session_state.ruolo
st.sidebar.title("🛡️ RGD-ALPHA")
st.sidebar.write(f"Operatore: **{azienda}**")
menu = ["🏠 Home", "📊 War Room Strategica", "📜 Archivio Storico"]
if ruolo == "admin": menu.insert(1, "🕵️ Centrale Admin")
scelta = st.sidebar.radio("Navigazione", menu)
if st.sidebar.button("Logout"): logout_utente()

# =========================
#   WAR ROOM STRATEGICA (PULITA)
# =========================
if scelta == "📊 War Room Strategica":
    st.markdown(f"<div class='warroom-header'><h1>🚀 War Room Strategica</h1><p>Digital Twin & Risk Intelligence • {azienda}</p></div>", unsafe_allow_html=True)
    
    # GUIDA
    st.markdown("### 🎯 Configurazione Protocollo Alpha")
    st.info("Seleziona il Dipartimento e carica i documenti per avviare il calcolo di precisione.")

    # SELEZIONE DIPARTIMENTO (CHIAMATA UNICA)
    struttura = mostra_interfaccia_4_aree()
    dipartimento_scelto = struttura['Dipartimento']

    st.markdown("---")

    # UPLOAD FILES (UNICO E CENTRALE)
    uploaded_file = st.file_uploader(f"📥 Upload Files: {dipartimento_scelto}", type=["csv", "xlsx"])

    with st.sidebar:
        st.write("---")
        w1 = st.slider("Peso Presente (W1)", 0.1, 1.0, 0.7)
        w2 = st.slider("Peso Storico (W2)", 0.1, 1.0, 0.3)
        ritardo = st.slider("Ritardo Fornitori (Giorni)", 0, 30, 0)
        f_stress = 1.0 + (ritardo / 50.0)

    if uploaded_file:
        with st.status("🔄 Analisi Alpha in corso...") as status:
            path = genera_percorso_salvataggio(UPLOAD_DIR, azienda, dipartimento_scelto, uploaded_file.name)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f: f.write(uploaded_file.getbuffer())
            
            ingestor = IngestoreDati()
            lista_asset = ingestor.elabora_file(str(path), azienda)
            if lista_asset:
                engine = DataGateway()
                db.registra_caricamento(user_id, dipartimento_scelto.upper(), uploaded_file.name)
                report = engine.esegui_scan_strategico(lista_asset, dipartimento_scelto, fattore_stress=f_stress, weights=(w1, w2))
                for r in report: 
                    db.salva_asset(user_id, r['asset'], r['rischio'], tipo=r['settore'], momentum=r['momentum_score'])
                st.success(f"Analisi completata: {len(report)} nodi processati.")
            else:
                st.error("Dataset non valido.")

    # DASHBOARD KPI
    kpis = db.calcola_e_salva_kpi_correnti(user_id)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-card'><h3>Solidità</h3><div class='value'>{kpis['solidita']}%</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'><h3>Rischio</h3><div class='value'>{kpis['rischio_medio']}/10</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card'><h3>Asset</h3><div class='value'>{len(db.recupera_attivita_globale())}</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-card'><h3>Impatto</h3><div class='value'>{kpis['impatto_30gg']}</div></div>", unsafe_allow_html=True)

# =========================
#   ALTRE SEZIONI
# =========================
elif scelta == "🏠 Home":
    st.markdown("<div class='welcome-card'><h1>🛡️ RGD-Alpha</h1><p>Benvenuto nel sistema di Risk Intelligence aziendale.</p></div>", unsafe_allow_html=True)

elif scelta == "🕵️ Centrale Admin":
    st.title("🕵️ Centrale Admin")
    st.dataframe(db.supervisione_admin_metriche_globali(), use_container_width=True)

elif scelta == "📜 Archivio Storico":
    st.title("📜 Archivio Storico")
    df_log = db.recupera_log_caricamenti_admin()
    st.dataframe(df_log, use_container_width=True)

# ==============================================================================
# 🛡️ PROTOCOLLO ALPHA-V2-FINALE: CODICE BLINDATO - NON MODIFICARE OLTRE 🛡️
# ==============================================================================