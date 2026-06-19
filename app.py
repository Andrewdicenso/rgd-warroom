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
#   CARICAMENTO CSS ESTERNO (style.css)
# ==========================================
def load_css(file_name="style.css"):
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Esegui il caricamento degli stili estratti
load_css()

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
#   NAVIGAZIONE SIDEBAR EXECUTIVE (MODIFICATA)
# ==========================================
user_id = st.session_state.user_id
azienda = st.session_state.azienda
ruolo = st.session_state.ruolo
is_admin = ruolo == "admin"

st.sidebar.title("🛡️ RGD-ALPHA")
st.sidebar.write(f"Operatore: **{azienda}**")

menu = ["🏠 Home", "📊 War Room Strategica", "📜 Archivio Storico"]
if is_admin:
    menu.insert(1, "🕵️ Centrale Admin")

scelta = st.sidebar.radio("Navigazione", menu)

# --- STRESS TEST PULITO (Senza tendina vuota) ---
st.sidebar.markdown("---")
st.sidebar.subheader("🚨 Simulazione Stress Test")
f_stress = st.sidebar.slider("Moltiplicatore Inefficienze", 1.0, 2.5, 1.0, 0.1)
st.sidebar.caption("Leva attiva per simulazione scenari.")

st.sidebar.markdown("---")
if st.sidebar.button("Logout"):
    logout_utente()

# ==========================================
#   PAGINA 1: HOME / BENVENUTO
# ==========================================
if scelta == "🏠 Home":
    # Header con stile Enterprise
    st.markdown("""
        <div style="text-align: center; padding: 40px 0;">
            <h1 style="color: #d4af37; font-size: 3rem; margin-bottom: 10px;">🛡️ RGD-WARROOM ALPHA</h1>
            <p style="font-size: 1.2rem; color: #e2e8f0; opacity: 0.8;">
                Advanced Business Intelligence & Predictive Risk Management System
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Griglia di presentazione Funzioni
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
            <div class="ai-reasoning" style="height: 250px;">
                <h3 style="color: #3498db;">📊 War Room Strategica</h3>
                <p>Analisi in tempo reale della produttività e della solidità aziendale. 
                Il sistema integra algoritmi <b>EMA Auto-Adattivi</b> per isolare i trend reali dalle oscillazioni temporanee.</p>
                <small>➔ Carica i tuoi KPI per iniziare l'analisi.</small>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="ai-reasoning" style="height: 250px; margin-top:20px;">
                <h3 style="color: #e74c3c;">🚨 Stress Test What-If</h3>
                <p>Simula scenari macroeconomici e operativi complessi. 
                Valuta l'impatto di inefficienze sulla <b>Resilience</b> complessiva prima che si verifichino nella realtà.</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="ai-reasoning" style="height: 250px;">
                <h3 style="color: #2ecc71;">🧠 Diagnostica Prescrittiva</h3>
                <p>Non solo dati, ma decisioni. L'integrazione con <b>LLM Llama-3.3 (Groq)</b> fornisce suggerimenti azionabili 
                per ottimizzare i processi e prevenire la 'Dashboard Fatigue'.</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="ai-reasoning" style="height: 250px; margin-top:20px;">
                <h3 style="color: #9b59b6;">📜 Archivio Storico</h3>
                <p>Monitoraggio continuo delle performance nel tempo. 
                Confronta i risultati attuali con i dati storici salvati nel <b>Database Criptato</b>.</p>
            </div>
        """, unsafe_allow_html=True)

    # Footer Informativo
    st.markdown("---")
    st.info("💡 **Consiglio per il Manager:** Inizia dalla sezione 'War Room' caricando l'ultimo report operativo in formato CSV o Excel per ricevere la prima diagnosi AI.")

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
#   PAGINA 3: WAR ROOM STRATEGICA (VERSIONE CORRETTA)
# ==========================================
elif scelta == "📊 War Room Strategica":
    st.markdown(
        f"""
        <div class='warroom-header'>
            <h1>🚀 War Room Strategica</h1>
            <p style='color: white !important;'>
                Analisi quantitativa oraria $H_{{(prod)}}$ e solidità in tempo reale per: 
                <strong style='color: white !important;'>{azienda}</strong>
            </p>
        </div>
        """,
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

        with st.status("🔄 Protocollo Analitico RGD-Alpha in corso...") as status:
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
                    weights=(0.7, 0.3),
                )
                kpi_reali = db.calcola_e_salva_kpi_correnti(user_id)
                
                status.update(
                    label="✅ Analisi Quantitativa Completata!",
                    state="complete",
                )

                # --- 📊 ANALISI TECNICA MOMENTUM (Correttamente Allineato) ---
                with st.expander("📊 Analisi Tecnica: Accelerazione Inefficienze (Algoritmo EMA)"):
                    st.info("Questo grafico evidenzia la velocità di propagazione dei rischi.")
                    df_p = pd.DataFrame(report_analisi)
                    fig = px.bar(
                        df_p,
                        x="asset",
                        y="momentum_score",
                        color="stato",
                        color_discrete_map={"CRITICO": "#ff5f56", "ATTENZIONE": "#ffbd2e", "OTTIMALE": "#27c93f"},
                        template="plotly_white", 
                        title="Dettaglio Momentum per Reparto"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # --- CALCOLI FINALI E DASHBOARD ---
                ore_totale = sum([a.get("ore_produttive_effettive", 0) for a in report_analisi])
                rischio_val = kpi_reali.get("rischio_medio", 0)
                trend_testo = kpi_reali.get("trend", "Stabile")

                st.markdown("### 📊 Risultati Intelligence Report")
                c1, c2, c3, c4 = st.columns(4)
                col_r = "#e74c3c" if rischio_val > 7 else "#f39c12" if rischio_val > 4 else "#27ae60"

                c1.markdown(f'<div class="metric-card"><h3>Solidità</h3><div class="value">{kpi_reali.get("solidita")}%</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-card" style="border-top-color:{col_r}"><h3>Rischio</h3><div class="value" style="color:{col_r}">{rischio_val}/10</div></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-card"><h3>Trend AI</h3><div class="value" style="font-size:1.2rem">{trend_testo}</div></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="metric-card"><h3>Ore Analizzate</h3><div class="value">{int(ore_totale)} h</div></div>', unsafe_allow_html=True)

                # --- CALCOLI FINALI ---
                ore_totale = sum([a.get("ore_produttive_effettive", 0) for a in report_analisi])
                rischio_val = kpi_reali.get("rischio_medio", 0)
                trend_testo = kpi_reali.get("trend", "Stabile")

                # --- DASHBOARD KPI EXECUTIVE (Orizzontale) ---
                st.markdown("### 📊 Risultati Intelligence Report")
                c1, c2, c3, c4 = st.columns(4)
                
                # Colore dinamico per il rischio
                col_r = "#e74c3c" if rischio_val > 7 else "#f39c12" if rischio_val > 4 else "#27ae60"

                c1.markdown(f'<div class="metric-card"><h3>Solidità</h3><div class="value">{kpi_reali.get("solidita")}%</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-card" style="border-top-color:{col_r}"><h3>Rischio</h3><div class="value" style="color:{col_r}">{rischio_val}/10</div></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-card"><h3>Trend AI</h3><div class="value" style="font-size:1.2rem">{trend_testo}</div></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="metric-card"><h3>Ore Analizzate</h3><div class="value">{int(ore_totale)} h</div></div>', unsafe_allow_html=True)

                # --- NARRATIVA IA (Opzionale, sotto le card) ---
                # Qui può seguire il tuo codice per la diagnostica con Groq

                # Aggiornamento Dashboard con Risultati Reali
                st.markdown("### 📊 Risultati Elaborazione Corrente")

                
                # ==========================================
                # MODULO 2: RISULTATI CON TREND AUTO-ADATTIVO
                # ==========================================
                st.markdown("### 📊 Intelligence Report: Analisi Strategica")
                
                # Usiamo le card potenziate per mostrare il Trend (Modulo 2)
                c1, c2, c3, c4 = st.columns(4)

                rischio_val = kpi_reali.get("rischio_medio", 0)
                trend_testo = kpi_reali.get("trend", "Stabile")
                ore_totale = sum([a.get("ore_produttive_effettive", 0) for a in report_analisi])
                
                # Colore dinamico basato sul rischio
                col_r = "#e74c3c" if rischio_val > 7 else "#f39c12" if rischio_val > 4 else "#27ae60"
                
                # Card 1: Solidità con variazione
                c1.markdown(
                    f"<div class='metric-card'><h3>Solidità</h3><div class='value'>{kpi_reali.get('solidita', 0)}%</div><small>Trend: {trend_testo}</small></div>",
                    unsafe_allow_html=True,
                )
                # Card 2: Rischio con colore dinamico
                c2.markdown(
                    f"<div class='metric-card' style='border-top-color:{col_r};'><h3>Rischio</h3><div class='value' style='color:{col_r};'>{rischio_val}/10</div></div>",
                    unsafe_allow_html=True,
                )
                # Card 3: Trend
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

                # --- 📊 ANALISI TECNICA MOMENTUM (Modulo di Approfondimento) ---
                with st.expander("📊 Analisi Tecnica: Accelerazione Inefficienze (Algoritmo EMA)"):
                    st.info("Questo grafico evidenzia la velocità di propagazione dei rischi.")
                    df_p = pd.DataFrame(report_analisi)
                    fig = px.bar(
                        df_p,
                        x="asset",
                        y="momentum_score",
                        color="stato",
                        color_discrete_map={"CRITICO": "#ff5f56", "ATTENZIONE": "#ffbd2e", "OTTIMALE": "#27c93f"},
                        template="plotly_white", 
                        title="Dettaglio Momentum per Reparto"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # --- 🧠 DIAGNOSTICA STRATEGICA RGD + IA (Il Cuore Decisionale) ---
                st.subheader("🧠 Diagnostica Strategica RGD + IA")
                api_key = os.getenv("GROQ_API_KEY")

                if not api_key:
                    st.warning("⚠️ Configura GROQ_API_KEY su Render per attivare la Diagnostica.")
                else:
                    client = Groq(api_key=api_key)
                    media_momentum = round(df_p['momentum_score'].mean(), 2) if 'df_p' in locals() else 0
                    
                    settore_scelto = st.selectbox(
                        "Seleziona il settore operativo per una diagnosi mirata:",
                        ["Marketing", "Logistica", "Produzione", "Servizi", "Retail"],
                        key="settore_ia_unico_exec"
                    )

                    if st.button("🚀 ESEGUI ANALISI STRATEGICA PRESCRITTIVA"):
                        with st.spinner("L'AI sta elaborando la strategia..."):
                            try:
                                prompt_config = f"""
                                Sei un Senior Business Consultant esperto in Digital Twin per l'azienda {azienda} (Settore: {settore_scelto}).
                                DATI CORRENTI:
                                - Solidità: {kpi_reali.get('solidita', 0)}% (Trend: {trend_testo})
                                - Rischio: {rischio_val}/10 | Momentum Medio: {media_momentum}
                                - Ore lavorate: {int(ore_totale)}

                                COMPITO:
                                Rispondi con un tono Executive seguendo questo schema:
                                1. DIAGNOSI NUMERICA: Perché il trend è {trend_testo}.
                                2. SOGLIE DI SETTORE: Compara con il settore {settore_scelto}.
                                3. PIANO D'AZIONE (PRESCRIPTIVE): 3 AZIONI PRATICHE immediate.
                                4. ALLERTA 'DASHBOARD FATIGUE': Rischio se non si agisce in 7gg.
                                5. CONCLUSIONE: Una frase definitiva sulla resilienza.
                                """

                                chat_completion = client.chat.completions.create(
                                    messages=[
                                        {"role": "system", "content": "Sei un CSO virtuale. Dai ordini esecutivi."},
                                        {"role": "user", "content": prompt_config},
                                    ],
                                    model="llama-3.3-70b-versatile",
                                )
                                risposta_testo = chat_completion.choices[0].message.content
                                st.markdown(
                                    f"""
                                    <div class="ai-reasoning">
                                        <h4 style='color:#d4af37; border-bottom: 1px solid #d4af37; padding-bottom:10px;'>📋 RESOCONTO ESECUTIVO AI</h4>
                                        <div style='color:#e2e8f0; font-size: 1rem; line-height: 1.6;'>
                                            {risposta_testo.replace('1.', '<br><b>1.</b>').replace('2.', '<br><b>2.</b>').replace('3.', '<br><b>3.</b>').replace('4.', '<br><b>4.</b>').replace('5.', '<br><b>5.</b>')}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            except Exception as e:
                                st.error(f"Errore tecnico nel motore IA: {e}")

                # --- 📝 PIANO D'AZIONE OPERATIVO INTELLIGENTE (Modulo Reparti) ---
                st.subheader("📝 Piano d'Azione Operativo (Priorità)")
                report_ordinato = sorted(report_analisi, key=lambda x: x.get('rischio', 0), reverse=True)

                for asset in report_ordinato:
                    r = asset.get("rischio", 0)
                    m = asset.get("momentum_score", 0)
                    nome = asset.get('asset', 'Reparto Non Specificato')
                    if r > 7 and m > 2:
                        box_style, label, consiglio = "kpi-box-critical", "🚨 EMERGENZA", "Bloccare le attività e avviare revisione."
                    elif r > 5 or m > 1.5:
                        box_style, label, consiglio = "kpi-box", "⚠️ ATTENZIONE", "Incrementare il monitoraggio."
                    else:
                        box_style, label, consiglio = "kpi-box", "✅ NOMINALE", "Mantenere gli standard attuali."

                    st.markdown(f"""
                        <div class="{box_style}" style="border-left: 10px solid {'#dc3545' if '🚨' in label else '#007BFF'};">
                            <span style="float: right; font-size: 0.8rem; background: #eee; padding: 2px 8px; border-radius: 10px; color: #333;">{label}</span>
                            <b style="font-size: 1.1rem; color: #102a43;">{nome}</b>
                            <br><small>Rischio: <b>{r}/10</b> | Accelerazione: <b>{m}</b></small>
                            <div style="margin-top: 10px; padding: 10px; background: rgba(255,255,255,0.5); border-radius: 5px;">
                                🎯 <b>LOGICA AI:</b> {consiglio}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

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
            df_logs = db.recupera_log_caricamenti_admin()
            if not df_logs.empty:
                df_logs = df_logs[df_logs["azienda"] == azienda]

        if not df_logs.empty:
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
        else:
            st.warning("Nessun caricamento trovato in archivio.")
    except Exception as e:
        st.error(f"Errore recupero archivio: {e}")