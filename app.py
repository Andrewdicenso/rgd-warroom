import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Librerie di terze parti
from dotenv import load_dotenv
from groq import Groq

# Moduli interni del progetto
from auth.auth import *
from core.database import DatabaseAziendale
from core.engine import DataGateway
from core.simulator import SimulatoreRischio
from data_refinery import DataRefinery  # Si trova nella root principale
from ingestor import IngestoreDati  # Si trova nella root principale

# Router pagine
from page import warroom

# ==========================================
# 1. CONFIGURAZIONE UI (Unica e Iniziale)
# ==========================================
st.set_page_config(
    page_title="RGD-Alpha | War Room Strategica",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded",
)

# ==========================================
# 2. CARICAMENTO STILE CSS PERSONALIZZATO
# ==========================================
if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ==========================================
# 4. CONFIGURAZIONI PATH & AMBIENTE
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()
DATA_ROOT = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_ROOT / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# Inizializzazione Sessione (Fondamentale per Auth)
inizializza_sessione()
# Inizializzazione sicura del Database
db = DatabaseAziendale()
# --- LOGICA DI RECUPERO TOKEN ---
query_params = st.query_params
reset_token = query_params.get("reset_token")


# ==========================================
#   GESTIONE ESTETICA (CSS ESTERNO)
# ==========================================
def load_css(file_name="style.css"):
    """Carica il design system del progetto."""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(
            "⚠️ Sistema visivo RGD non caricato. Verifica la presenza di style.css"
        )


# Attivazione Veste Grafica
load_css()

# Inizializzazione Database (Unica istanza globale)
db = DatabaseAziendale()


# ==========================================
#   GESTIONE REGISTRAZIONE & AUTH
# ==========================================
def registra_nuovo_utente(email: str, password: str, conferma: str):
    if not email or not password or not conferma:
        st.error("Compila tutti i campi.")
        return
    if password != conferma:
        st.error("Le password non coincidono.")
        return
    try:
        if db.get_utente_by_email(email):
            st.error("Email già registrata.")
            return

        # Recupero Admin Email
        admin_email_env = os.getenv("ADMIN_EMAIL", "andrewdicenso@libero.it").lower()
        ruolo = "admin" if email.lower() == admin_email_env else "user"

        if db.crea_utente(email=email, password=password, ruolo=ruolo):
            st.success(
                "✅ Registrazione completata. Effettua il login nel Tab 'Login'."
            )
            st.balloons()
    except Exception as e:
        st.error(f"Errore critico durante la registrazione: {e}")


# --- BLOCCO DI ACCESSO UNIFICATO ---
# Deve essere fuori dalla funzione sopra e allineato correttamente
if not st.session_state.get("autenticato", False):
    # 1. Recupero il token dalla URL per il recupero password
    reset_token = st.query_params.get("reset_token")

    # 2. Creo i Tab una sola volta
    t1, t2, t3 = st.tabs(["🔐 Login", "🆕 Registrazione", "🔄 Recupero Password"])

    # TAB 1: LOGIN
    with t1:
        e = st.text_input("Email Aziendale", key="l_e").strip()
        p = st.text_input("Password", type="password", key="l_p").strip()

        if st.button("Accedi al Sistema"):
            # Controllo Amministratore Unico
            if e.lower() == "andrewdicenso@libero.it" and p == "WarRoom123!":
                st.session_state.autenticato = True
                st.session_state.user_id = "96a3b344-723b-410c-99d7-84a229a1b18d"
                st.session_state.email = "andrewdicenso@libero.it"
                st.session_state.ruolo = "admin"
                st.session_state.azienda = "RGD-Alpha"
                st.success("Accesso Amministratore eseguito!")
                st.rerun()
            # Controllo Utente Standard
            elif login_utente(db, e, p):
                st.rerun()
            else:
                st.error("Credenziali non valide. Riprova.")

    # --- TAB 2: REGISTRAZIONE ---
    with t2:
        re = st.text_input("Email per registrazione", key="r_e").strip()
        rp = st.text_input("Scegli Password", type="password", key="r_p").strip()
        rc = st.text_input("Conferma Password", type="password", key="r_c").strip()
        if st.button("Crea Account Enterprise"):
            registra_nuovo_utente(re, rp, rc)

    # --- TAB 3: RECUPERO PASSWORD ---
    with t3:
        st.subheader("🔄 Recupero Credenziali Sicuro")
        if not reset_token:
            st.info("Inserisci la tua email per ricevere il link di recupero.")
            email_richiesta = st.text_input(
                "Email per recupero", key="email_forget"
            ).strip()
            if st.button("Invia Link di Recupero"):
                import uuid

                nuovo_token = str(uuid.uuid4())
                if db.salva_token_reset(email_richiesta, nuovo_token):
                    link = f"https://rgd-warroom-app.onrender.com/?reset_token={nuovo_token}"
                    if invia_email_recupero(email_richiesta, link):
                        st.success("📧 Link inviato! Controlla la tua email.")
                    else:
                        st.error("Errore nell'invio della mail.")
        else:
            st.warning("Modalità Reset Attiva")
            nuova_p = st.text_input("Nuova Password", type="password", key="new_p")
            conferma_p = st.text_input(
                "Conferma Nuova Password", type="password", key="conf_p"
            )
            if st.button("Conferma Cambio Password"):
                if nuova_p == conferma_p and len(nuova_p) >= 8:
                    if db.valida_e_resetta_password(reset_token, nuova_p):
                        st.success("✅ Password aggiornata! Ora puoi fare il login.")
                        st.query_params.clear()
                    else:
                        st.error("Link scaduto o non valido.")
                else:
                    st.error(
                        "Le password non coincidono o sono troppo brevi (min 8 car.)."
                    )

    st.stop()  # Blocca il resto dell'app finché non sei loggato

# ==========================================
#   MENU DINAMICO
# ==========================================
menu = ["🏠 Home", "📊 War Room Strategica", "📜 Archivio Storico"]

if st.session_state.get("is_admin", False):
    menu.insert(1, "🕵️ Centrale Admin")

scelta = st.sidebar.radio("Navigazione", menu)

st.sidebar.markdown("---")
st.sidebar.subheader("🚨 Simulazione Stress Test")
f_stress = st.sidebar.slider(
    "Moltiplicatore Inefficienze",
    min_value=1.0,
    max_value=2.5,
    value=1.0,
    step=0.1,
    help="Simula un aumento del rischio operativo globale.",
)
st.sidebar.caption("Leva attiva per simulazione scenari di crisi.")

st.sidebar.markdown("---")
if st.sidebar.button("Logout", key="logout_sidebar"):
    logout_utente()

    # --- INIZIO BLOCCO TUTELA LEGALE RGANDJA ---
    st.sidebar.markdown("---")
    with st.sidebar.expander("⚖️ Note Legali & Copyright"):
        st.markdown(
            """
            <div style="font-size: 0.85em; color: #555; line-height: 1.4;">
                <strong>Proprietario Intellettuale:</strong><br>
                [Andrew Di Censo]<br><br>
                <strong>Marchio Registrato:</strong><br>
                Rgandja® (Classi 9, 42)<br><br>
                <strong>Tutela Algoritmica:</strong><br>
                La metodologia <em>H(prod)</em> e i calcoli di
                <em>Momentum Strategico</em> sono protetti come
                <strong>Segreto Industriale</strong> (D.Lgs. 30/2005).
            </div>
            <hr style="margin: 10px 0;">
            <div style="font-size: 0.75em; color: gray; text-align: justify;">
                È vietata la riproduzione, decompilazione o reverse engineering
                del software. Ogni accesso è tracciato nel log di sicurezza Enterprise.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.sidebar.caption("© 2024 Rgandja. Tutti i diritti riservati.")
# --- FINE BLOCCO TUTELA LEGALE ---

# ==========================================
#   PAGINA 1: HOME EXECUTIVE
# ==========================================
if scelta == "🏠 Home":
    st.markdown(
        """
        <div style="text-align: center; padding: 40px 0;">
            <h1 style="color: #d4af37; font-size: 3.5rem; margin-bottom: 10px;">🛡️ RGD-WARROOM ALPHA</h1>
            <p style="font-size: 1.3rem; color: #334e68; font-weight: 500;">
                Il Digital Twin per la Governance Aziendale e il Risk Management Predittivo
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class="ai-reasoning" style="height: 280px;">
                <h3 style="color: #3498db;">📊 Intelligence Hub</h3>
                <p>Monitora la <b>Resilience Aziendale</b> con algoritmi EMA di nuova generazione.
                Isoliamo i trend critici dalle fluttuazioni operative per garantirti una visione cristallina della solidità.</p>
                <div style="margin-top:15px; border-top: 1px solid rgba(212,175,55,0.2); padding-top:10px;">
                    <small style="color: #d4af37;">➔ FOCUS: PREVENZIONE DEL DECLINO OPERATIVO</small>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="ai-reasoning" style="height: 280px; margin-top:20px;">
                <h3 style="color: #e74c3c;">🚨 Scenario Simulation</h3>
                <p>Anticipa il mercato con lo <b>Stress-Test Multivariabile</b>.
                Simula scenari di crisi e inefficienze per testare la tenuta dei tuoi margini in un ambiente Sandbox sicuro.</p>
                <div style="margin-top:15px; border-top: 1px solid rgba(212,175,55,0.2); padding-top:10px;">
                    <small style="color: #d4af37;">➔ FOCUS: MITIGAZIONE PROATTIVA DEL RISCHIO</small>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="ai-reasoning" style="height: 280px;">
                <h3 style="color: #2ecc71;">🧠 AI Advisory Board</h3>
                <p>Supera la 'Dashboard Fatigue'. Il nostro motore basato su <b>LLM Llama-3.3</b> trasforma i dati complessi
                in <b>Protocolli Esecutivi</b> chiari e pronti all'azione.</p>
                <div style="margin-top:15px; border-top: 1px solid rgba(212,175,55,0.2); padding-top:10px;">
                    <small style="color: #d4af37;">➔ FOCUS: DECISION-MAKING ASSISTITO DA IA</small>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="ai-reasoning" style="height: 280px; margin-top:20px;">
                <h3 style="color: #9b59b6;">📜 Governance Audit</h3>
                <p>Mantieni un <b>Audit Trail</b> completo di ogni analisi.
                Monitora l'evoluzione della tua strategia nel tempo grazie al database criptato ad alta sicurezza.</p>
                <div style="margin-top:15px; border-top: 1px solid rgba(212,175,55,0.2); padding-top:10px;">
                    <small style="color: #d4af37;">➔ FOCUS: COMPLIANCE E TRACCIABILITÀ STORICA</small>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.info(
        "💡 **Executive Insight:** L'80% dei fallimenti aziendali deriva da una cattiva interpretazione dei trend. "
        "Inizia caricando i dati operativi nell'Intelligence Hub."
    )

# ==========================================
#   PAGINA 2: CENTRALE ADMIN (SOLO ADMIN)
# ==========================================
elif scelta == "🕵️ Centrale Admin" and is_admin:
    st.markdown(
        """
        <div style="background-color: #1e3c72; padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;">
            <h2 style="margin: 0; color: white;">🕵️ Centrale di Supervisione Admin</h2>
            <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.8);">
                Monitoraggio globale delle attività di sistema e degli accessi utente.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        # 1. VISUALIZZAZIONE UTENTI
        df_utenti = db.supervisione_admin_metriche_globali()
        if df_utenti is not None and not df_utenti.empty:
            st.subheader("👥 Utenti Registrati")
            st.dataframe(df_utenti, use_container_width=True, hide_index=True)
        else:
            st.info("Nessun utente registrato oltre all'amministratore.")

        # 2. VISUALIZZAZIONE LOG ATTIVITÀ
        st.subheader("📈 Log Attività Recente")
        df_asset_globale = db.recupera_attivita_globale()
        if df_asset_globale is not None and not df_asset_globale.empty:
            st.dataframe(df_asset_globale, use_container_width=True)
        else:
            st.warning("Nessuna attività registrata negli asset logs.")
    except Exception as e:
        st.error(f"❌ Errore critico nel caricamento del pannello Admin: {e}")

# ==========================================
#   PAGINA 3: WAR ROOM STRATEGICA (ALLINEATA)
# ==========================================
elif scelta == "📊 War Room Strategica":
    # Recuperiamo il nome dell'azienda dalla sessione di Streamlit per evitare il NameError
    azienda = st.session_state.get("azienda", "Azienda N/D")
    user_id = st.session_state.get(
        "user_id", 1
    )  # O il modo in cui salvi l'id utente nel login

    report_analisi = []

    st.markdown(
        f"""
        <div class='warroom-header'>
            <h1>🚀 War Room Strategica</h1>
            <p>
                Analisi quantitativa oraria $H_{{(prod)}}$ e solidità in tempo reale per:
                <strong>{azienda}</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "📁 Carica file dati operativi (SAP, Salesforce, Excel Custom)",
        type=["csv", "xlsx", "xls"],
    )

    if uploaded_file:
        path_raw = UPLOAD_DIR / azienda / uploaded_file.name
        path_raw.parent.mkdir(parents=True, exist_ok=True)

        with open(path_raw, "wb") as f:
            f.write(uploaded_file.getbuffer())
            settore_ia = "GENERAL"

        with st.status(
            "🔄 Protocollo Analitico RGD-Alpha in corso...", expanded=True
        ) as status:
            status.write("🔍 Fase 1: Identificazione impronta digitale e pulizia...")
            paese_calendar = st.session_state.get("paese_azienda", "IT")
            refinery = DataRefinery(country=paese_calendar)
            refined_result = refinery.refine_file(str(path_raw))

            status.write("📥 Fase 2 & 3: Ingestione Intelligente SAP/Excel...")
            ingestor = IngestoreDati()
            lista_asset = ingestor.elabora_csv(str(path_raw), azienda)

            if lista_asset:
                engine = DataGateway()
                db.registra_caricamento(user_id, "WAR_ROOM", uploaded_file.name)

                status.write("📈 Fase 4: Calcolo quantitativo predittivo...")
                report_analisi = engine.esegui_scan_strategico(
                    lista_asset,
                    "UNIVERSAL",
                    fattore_stress=f_stress,
                    weights=(0.7, 0.3),
                )

                db.calcola_e_salva_kpi_correnti(user_id)
                kpi_reali = (
                    db.get_kpi_recenti(user_id)
                    if hasattr(db, "get_kpi_recenti")
                    else {}
                )

                df_p = pd.DataFrame(report_analisi)
                df_p.columns = [str(c).lower().strip() for c in df_p.columns]

                if not isinstance(kpi_reali, dict) or not kpi_reali:
                    kpi_reali = {
                        "solidita": 85,
                        "rischio_medio": round(
                            (
                                df_p["risk_factor"].mean()
                                if "risk_factor" in df_p.columns
                                else 4
                            ),
                            1,
                        ),
                        "trend": "In Monitoraggio",
                    }

                status.update(
                    label="✅ Protocollo RGD-Alpha Completato con Successo!",
                    state="complete",
                )

                rischio_val = kpi_reali.get("rischio_medio", 0)
                trend_testo = kpi_reali.get("trend", "Stabile")
                solidita_val = kpi_reali.get("solidita", 0)

                col_ore = [c for c in df_p.columns if "ore" in c or "effettive" in c]
                ore_totale = (
                    pd.to_numeric(df_p[col_ore[0]], errors="coerce").sum()
                    if col_ore
                    else 0
                )

                st.markdown("### 📊 Intelligence Report: Analisi Strategica")
                c1, c2, c3, c4 = st.columns(4)
                col_r = (
                    "#e74c3c"
                    if rischio_val > 7
                    else "#f39c12" if rischio_val > 4 else "#27ae60"
                )

                c1.markdown(
                    f"<div class='metric-card'><h3>Solidità</h3><div class='value'>{solidita_val}%</div></div>",
                    unsafe_allow_html=True,
                )
                c2.markdown(
                    f"<div class='metric-card' style='border-top-color:{col_r}'><h3>Rischio</h3>"
                    f"<div class='value' style='color:{col_r};'>{rischio_val}/10</div></div>",
                    unsafe_allow_html=True,
                )
                c3.markdown(
                    f"<div class='metric-card'><h3>Trend AI</h3>"
                    f"<div class='value' style='font-size:1.2rem'>{trend_testo}</div></div>",
                    unsafe_allow_html=True,
                )
                c4.markdown(
                    f"<div class='metric-card'><h3>Ore Analizzate</h3>"
                    f"<div class='value'>{int(ore_totale)} h</div></div>",
                    unsafe_allow_html=True,
                )

        with st.expander("📊 Analisi Tecnica: Dettaglio Asset"):
            st.dataframe(df_p, width="stretch", hide_index=True)

            st.subheader("🧠 Diagnostica Strategica RGD + IA")

            # Calcoliamo le metriche di supporto per l'IA
            media_m = round(
                (
                    df_p["momentum_score"].mean()
                    if "momentum_score" in df_p.columns
                    else 0
                ),
                2,
            )
            settore_ia = (
                lista_asset[0].__class__.__name__.replace("AssetDi", "")
                if lista_asset
                else "GENERAL"
            )

            # Importiamo la funzione pulita dal modulo explainer di Gemini
            from ai_modules.explainer import spiega_war_room_strategica

            if st.button("🚀 ESEGUI ANALISI STRATEGICA PRESCRITTIVA"):
                with st.spinner(
                    "Google Gemini Enterprise al lavoro per il report predittivo..."
                ):
                    try:
                        # Chiamata alla funzione che genera il report discorsivo e la formula 30/60/90 giorni
                        report_enterprise = spiega_war_room_strategica(
                            azienda=azienda,
                            settore=settore_ia,
                            solidita=solidita_val,
                            rischio=rischio_val,
                            momentum=media_m,
                            ore=int(ore_totale),
                            df_str=df_p.to_string(index=False),
                        )

                        st.markdown(
                            "### 📋 Report Strategico & Predittivo Semplificato (30/60/90 Giorni)"
                        )
                        st.markdown(
                            f"<div class='ai-reasoning'>{report_enterprise}</div>",
                            unsafe_allow_html=True,
                        )

                    except Exception as e:
                        st.error(f"Errore durante l'analisi con Gemini: {e}")

# ==========================================
#   PAGINA 4: ARCHIVIO STORICO (VERSIONE EXECUTIVE)
# ==========================================
elif scelta == "📜 Archivio Storico":
    st.title("📜 Archivio Storico Caricamenti")

    try:
        df_logs = db.recupera_log_caricamenti_admin()

        if df_logs is not None and not df_logs.empty:
            if is_admin:
                st.info("👁️ Vista Admin: Monitoraggio Globale del Sistema")
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.info(f"📁 Registro Analisi Strategiche per: **{azienda}**")
                df_filtrato = df_logs[df_logs["azienda"] == azienda]

                if not df_filtrato.empty:
                    st.dataframe(df_filtrato, use_container_width=True, hide_index=True)
                else:
                    st.warning(
                        f"Nessuna operazione registrata per l'azienda {azienda}."
                    )
        else:
            st.warning(
                "L'archivio centrale è attualmente vuoto. Carica un file nella War Room per iniziare."
            )
    except Exception as e:
        st.error(f"❌ Errore critico di sincronizzazione archivio: {e}")
