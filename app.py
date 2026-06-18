# 1. LIBRERIE STANDARD DI PYTHON (Native)
import os
import sys
from datetime import datetime
from pathlib import Path

# 2. LIBRERIE DI TERZE PARTI (Installate con pip)
from dotenv import load_dotenv
from groq import Groq
import pandas as pd
import plotly.express as px
import streamlit as st

# 3. MODULI CORE & AUTH (I tuoi file locali)
from auth.auth import inizializza_sessione, login_utente, logout_utente
from core.database import DatabaseAziendale
from core.engine import DataGateway
from core.ingestor import IngestoreDati

# --- RISOLUZIONE DINAMICA PATH INTERNI ---
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ==========================================
#   CONFIGURAZIONE BASE
# ==========================================
load_dotenv()
DATA_ROOT = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_ROOT / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="RGD-Alpha | War Room Strategica", layout="wide", page_icon="🛡️"
)

inizializza_sessione()

# ==========================================
#   CSS ENTERPRISE POTENZIATO
# ==========================================
st.markdown(
    """
    <style>
    .kpi-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #007BFF; margin-bottom: 15px; }
    .kpi-box-critical { background-color: #fff5f5; padding: 20px; border-radius: 10px; border-left: 5px solid #dc3545; margin-bottom: 15px; }
    .ai-reasoning { background: #0e1117; border: 1px solid #d4af37; padding: 25px; border-radius: 15px; color: #e2e8f0; line-height: 1.6; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .crew-box { padding:15px; border-radius:10px; background:rgba(255,255,255,0.02); margin-bottom:10px; border-left: 5px solid #ccc; }
    
    .warroom-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem; border-radius: 1rem; margin-bottom: 2rem; border-left: 5px solid #e74c3c;
    }
    .warroom-header h1 { color: white; margin: 0; }
    .metric-card {
        background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center; border-top: 4px solid #3498db;
    }
    </style>
""",
    unsafe_allow_html=True,
)

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
        admin_email_env = os.getenv(
            "ADMIN_EMAIL", "andrewdicenso@libero.it"
        ).lower()
        ruolo = "admin" if email.lower() == admin_email_env else "user"
        if db.crea_utente(email=email, password=password, ruolo=ruolo):
            st.success("✅ Registrazione completata. Effettua il login.")
            st.balloons()
    except Exception as e:
        st.error(f"Errore registrazione: {e}")


if not st.session_state.autenticato:
    t1, t2 = st.tabs(["🔐 Login", "🆕 Registrazione"])
    with t1:
        e = st.text_input("Email", key="l_e").strip()
        p = st.text_input("Password", type="password", key="l_p").strip()
        if st.button("Accedi"):
            if login_utente(db, e, p):
                st.rerun()
            else:
                st.error("Credenziali errate.")
    with t2:
        re = st.text_input("Email", key="r_e").strip()
        rp = st.text_input("Password", type="password", key="r_p").strip()
        rc = st.text_input("Conferma", type="password", key="r_c").strip()
        if st.button("Registrati"):
            registra_nuovo_utente(re, rp, rc)
    st.stop()

# ==========================================
#   NAVIGAZIONE SIDEBAR
# ==========================================
user_id = st.session_state.user_id
azienda = st.session_state.azienda
ruolo = st.session_state.ruolo
is_admin = ruolo == "admin"

st.sidebar.title("🛡️ RGD-ALPHA")
st.sidebar.write(f"Operatore: **{azienda}**")

# Menu dinamico: la Centrale Admin appare solo se l'utente è admin
menu = ["🏠 Home", "📊 War Room Strategica", "📜 Archivio Storico"]
if is_admin:
    menu.insert(1, "🕵️ Centrale Admin")

scelta = st.sidebar.radio("Navigazione", menu)

if st.sidebar.button("Logout"):
    logout_utente()

# ==========================================
#   PAGINA 1: HOME / BENVENUTO
# ==========================================
if scelta == "🏠 Home":
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='font-size: 3rem; margin: 0;'>🛡️ RGD-Alpha</h1>
            <p style='color: #7f8c8d; font-size: 1.2rem;'>Sistema di Risk Intelligence & Solidità Operativa</p>
        </div>
    """,
        unsafe_allow_html=True,
)

    st.markdown(
        f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 25px; border-radius: 15px; color: white; margin-bottom: 30px;'>
            <h3 style='margin-top:0;'>👋 Benvenuto, {azienda}</h3>
            <p>Il sistema RGD-Alpha analizza l'efficienza reale delle tue risorse utilizzando l'algoritmo 
            <strong>H(prod)</strong> per identificare colli di bottiglia e rischi latenti prima che colpiscano il bilancio.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.subheader("🚀 Roadmap Operativa")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(
            "**1. Caricamento**\n\nVai nella War Room e carica il file CSV dei tuoi asset o dipendenti."
        )
    with col2:
        st.warning(
            "**2. Calibrazione**\n\nRegola i pesi EMA e lo Stress Test per simulare scenari di crisi."
        )
    with col3:
        st.success(
            "**3. Risultato**\n\nOttieni il punteggio di Solidità e il Piano d'Azione IA immediato."
        )

    st.markdown("---")

    # Metriche di riepilogo rapido
    st.markdown("### 📊 Overview Moduli")
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Analisi Predittiva", "Attiva", delta="Algoritmo EMA")
    m_col2.metric("Sicurezza Dati", "AES-256", delta="Vault Criptato")
    m_col3.metric("Certificazione", "Audit Trail", delta="Notarizzato")

# ==========================================
#   PAGINA 2: CENTRALE ADMIN (SOLO ADMIN)
# ==========================================
elif scelta == "🕵️ Centrale Admin" and is_admin:
    st.title("🕵️ Centrale di Supervisione Admin")
    st.write("Monitoraggio globale di tutti gli utenti e le attività di sistema.")

    try:
        df_utenti = db.supervisione_admin_metriche_globali()
        if not df_utenti.empty:
            st.subheader("👥 Utenti Registrati")
            st.dataframe(df_utenti, use_container_width=True, hide_index=True)
        else:
            st.info("Nessun utente registrato oltre all'admin.")

        st.subheader("📈 Attività Recente Asset")
        df_asset_globale = db.recupera_attivita_globale()
        if not df_asset_globale.empty:
            st.dataframe(df_asset_globale, use_container_width=True)
    except Exception as e:
        st.error(f"Errore caricamento dati Admin: {e}")

# ==========================================
#   PAGINA 3: WAR ROOM STRATEGICA
# ==========================================
elif scelta == "📊 War Room Strategica":
    st.markdown(
        f"""
        <div class='warroom-header'>
            <h1>🚀 War Room Strategica</h1>
            <p>Analisi quantitativa oraria $H_{{(prod)}}$ e solidità in tempo reale per: <strong>{azienda}</strong></p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Placeholder iniziale Metriche (Visualizzate prima del caricamento)
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        st.markdown(
            "<div class='metric-card'><h3>Solidità</h3><div class='value'>N/D</div><div class='delta'>%</div></div>",
            unsafe_allow_html=True,
        )
    with col_p2:
        st.markdown(
            "<div class='metric-card' style='border-top-color: #e74c3c;'><h3>Rischio</h3><div class='value'>N/D</div><div class='delta'>/10</div></div>",
            unsafe_allow_html=True,
        )
    with col_p3:
        st.markdown(
            "<div class='metric-card' style='border-top-color: #f39c12;'><h3>Ore Effettive</h3><div class='value'>0</div><div class='delta'>H(prod)</div></div>",
            unsafe_allow_html=True,
        )
    with col_p4:
        st.markdown(
            "<div class='metric-card' style='border-top-color: #27ae60;'><h3>Produttività</h3><div class='value'>N/D</div><div class='delta'>Indice Orario</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    uploaded_file = st.file_uploader(
        "📁 Carica file dati operativi", 
    type=["csv", "xlsx", "xls"]
    )
    if uploaded_file:
        path = UPLOAD_DIR / azienda / uploaded_file.name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.status(
            "🔄 Protocollo Analitico RGD-Alpha in corso..."
        ) as status:
            ingestor = IngestoreDati()
            lista_asset = ingestor.elabora_csv(str(path), azienda)

            if lista_asset:
                engine = DataGateway()
                db.registra_caricamento(user_id, "WAR_ROOM", uploaded_file.name)

                # ESECUZIONE LOGICA PREDITTIVA (EMA + STRESS TEST)
                report_analisi = engine.esegui_scan_strategico(
                    lista_asset,
                    "Produttività",
                    fattore_stress=f_stress,
                    weights=(w1, w2),
                )
                kpi_reali = db.calcola_e_salva_kpi_correnti(user_id)
                status.update(
                    label="✅ Analisi Quantitativa Completata!",
                    state="complete",
                )

                # ==========================================
                # MODULO 2: RISULTATI CON TREND AUTO-ADATTIVO
                # ==========================================
                st.markdown("### 📊 Intelligence Report: Analisi Strategica")
                
                # Usiamo le card potenziate per mostrare il Trend (Modulo 2)
                c1, c2, c3, c4 = st.columns(4)

                rischio_val = kpi_reali.get("rischio_medio", 0)
                trend_testo = kpi_reali.get("trend", "Stabile")
                
                # Colore dinamico basato sul rischio
                col_r = "#e74c3c" if rischio_val > 7 else "#f39c12" if rischio_val > 4 else "#27ae60"
                
                # Card 1: Solidità con variazione (Delta)
                c1.markdown(
                    f"<div class='metric-card'><h3>Solidità</h3><div class='value'>{kpi_reali.get('solidita', 0)}%</div><small>Trend: {trend_testo}</small></div>",
                    unsafe_allow_html=True,
                )
                # Card 2: Rischio con colore dinamico
                c2.markdown(
                    f"<div class='metric-card' style='border-top-color:{col_r};'><h3>Rischio</h3><div class='value' style='color:{col_r};'>{rischio_val}/10</div></div>",
                    unsafe_allow_html=True,
                )
                # Card 3: Trend (La novità del Modulo 2)
                col_t = "#e74c3c" if "Peggioramento" in trend_testo else "#27ae60"
                c3.markdown(
                    f"<div class='metric-card' style='border-top-color:{col_t};'><h3>Trend AI</h3><div class='value' style='color:{col_t}; font-size:1.2rem;'>{trend_testo}</div></div>",
                    unsafe_allow_html=True,
                )
                # Card 4: Resilience
                c4.markdown(
                    f"<div class='metric-card' style='border-top-color:#3498db;'><h3>Resilience</h3><div class='value'>{max(0, round(100-(rischio_val*8),1))}%</div></div>",
                    unsafe_allow_html=True,
                )

                # --- GRAFICO MOMENTUM ---
                st.subheader("📈 Accelerazione Inefficienze (Algoritmo EMA)")
                df_p = pd.DataFrame(report_analisi)
                fig = px.bar(
                    df_p,
                    x="asset",
                    y="momentum_score",
                    color="stato",
                    color_discrete_map={
                        "CRITICO": "#ff5f56",
                        "ATTENZIONE": "#ffbd2e",
                        "OTTIMALE": "#27c93f",
                    },
                    title="Analisi Momentum per Reparto"
                )
                st.plotly_chart(fig, use_container_width=True)

                # --- RAGIONAMENTO IA CON GROQ (VERSIONE PRESCRITTIVA) ---
                st.subheader("🧠 Diagnostica Strategica RGD + IA")
                
                api_key = os.getenv("GROQ_API_KEY")

                if not api_key:
                    st.warning("⚠️ Configura GROQ_API_KEY su Render per attivare la Diagnostica.")
                else:
                    client = Groq(api_key=api_key)
                    media_momentum = round(df_p['momentum_score'].mean(), 2)
                    
                    settore_scelto = st.selectbox(
                        "In quale settore opera l'azienda?",
                        ["Marketing", "Logistica", "Produzione", "Servizi", "Retail"],
                        key="settore_ia"
                    )

                    if st.button("🚀 Genera Analisi Prescrittiva"):
                        with st.spinner("L'AI sta elaborando la strategia..."):
                            try:
                                # Prompt potenziato secondo i suggerimenti del mercato (Analisi Prescrittiva)
                                prompt_config = f"""
                                Sei un Senior Business Consultant. Analizza questi dati per l'azienda {azienda} ({settore_scelto}):
                                - Solidità: {kpi_reali.get('solidita', 0)}% (Trend: {trend_testo})
                                - Rischio: {rischio_val}/10
                                - Momentum Medio: {media_momentum}

                                Compito:
                                1. Spiega brevemente perché il trend è {trend_testo}.
                                2. Fornisci 3 AZIONI PRATICHE immediate (Prescriptive Actions) per migliorare la solidità.
                                3. Indica il rischio di 'Dashboard Fatigue' se i dati non vengono corretti entro 7 giorni.
                                Usa un tono professionale e diretto.
                                """

                                chat_completion = client.chat.completions.create(
                                    messages=[
                                        {"role": "system", "content": "Sei un analista strategico esperto in Digital Twin aziendali."},
                                        {"role": "user", "content": prompt_config},
                                    ],
                                    model="llama-3.3-70b-versatile",
                                )

                                risposta_testo = chat_completion.choices[0].message.content

                                # Visualizzazione con la classe CSS ai-reasoning che hai definito
                                st.markdown(
                                    f"""
                                    <div class="ai-reasoning">
                                        <h4 style='color:#d4af37;'>📋 Resoconto Esecutivo AI</h4>
                                        <div style='color:#e2e8f0;'>{risposta_testo}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            except Exception as e:
                                st.error(f"Errore IA: {e}")

                                # --- RAGIONAMENTO IA CON GROQ ---
                st.subheader("🧠 Diagnostica Strategica RGD + IA")
                
                api_key = os.getenv("GROQ_API_KEY")

                if not api_key:
                    st.warning("⚠️ Configura GROQ_API_KEY su Render per attivare la Diagnostica.")
                else:
                    client = Groq(api_key=api_key)
                    media_momentum = round(df_p['momentum_score'].mean(), 2)
                    
                    settore_scelto = st.selectbox(
                        "In quale settore opera l'azienda?",
                        ["Marketing", "Logistica", "Produzione", "Servizi", "Retail"],
                        key="settore_ia"
                    )

                    if st.button("🚀 Genera Diagnostica Approfondita"):
                        with st.spinner("Stiamo analizzando i file..."):
                            try:
                                prompt_config = f"""
                                Analizza i dati per l'azienda {azienda} (Settore: {settore_scelto}):
                                - Solidità attuale: {kpi_reali.get('solidita', 0)}%
                                - Rischio rilevato: {rischio_val}/10
                                - Ore lavorate analizzate: {int(ore_totale)}
                                - Accelerazione Inefficienze: {media_momentum}

                                Rispondi seguendo questo schema:
                                1. Conferma analisi documenti.
                                2. Diagnosi basata sui numeri.
                                3. Soglie ottimali per il settore {settore_scelto}.
                                4. Azione 'Opzionale' specifica.
                                5. Conclusione sul monitoraggio futuro.
                                """

                                chat_completion = client.chat.completions.create(
                                    messages=[
                                        {"role": "system", "content": "Sei un analista strategico esperto."},
                                        {"role": "user", "content": prompt_config},
                                    ],
                                    model="llama-3.3-70b-versatile", # Modello aggiornato e funzionante
                                )

                                risposta_testo = chat_completion.choices[0].message.content

                                st.markdown(
                                    f"""
                                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #2ecc71; color: #1f1f1f;">
                                        {risposta_testo}
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            except Exception as e:
                                st.error(f"Errore IA: {e}")

                # --- DETTAGLIO ASSET ---
                st.subheader("📝 Piano d'Azione per Reparto")
                for asset in report_analisi:
                    r = asset.get("rischio", 0)
                    box = "kpi-box-critical" if r > 7 else "kpi-box"
                    st.markdown(
                        f"""
                    <div class="{box}">
                        <b>{asset.get('asset', 'Reparto Ignoto')}</b> | Rischio: {r} | Momentum: {asset.get('momentum_score', 0)}
                        <br><small>🎯 <b>IA ADVICE:</b> {asset.get('consiglio_strategico', 'In attesa di dati...')}</small>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

# ==========================================
#   PAGINA 4: ARCHIVIO STORICO
# ==========================================
elif scelta == "📜 Archivio Storico":
    st.title("📜 Archivio Storico Caricamenti")
    try:
        if is_admin:
            st.info("👁️ Vista Admin: Storico Globale")
            df_logs = db.recupera_log_caricamenti_admin()
        else:
            st.info(f"📁 Archivio Caricamenti per: {azienda}")
            # Supponiamo di avere un metodo per log filtrati
            df_logs = db.recupera_log_caricamenti_admin()  # Filtra se necessario
            if not df_logs.empty:
                df_logs = df_logs[df_logs["azienda"] == azienda]

        if not df_logs.empty:
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
        else:
            st.warning("Nessun caricamento trovato in archivio.")
    except Exception as e:
        st.error(f"Errore recupero archivio: {e}")