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

py
# ==========================================
#   PAGINA 1: HOME EXECUTIVE
# ==========================================
if scelta == "🏠 Home":
    st.markdown("""
        <div style="text-align: center; padding: 40px 0;">
            <h1 style="color: #d4af37; font-size: 3.5rem; margin-bottom: 10px;">🛡️ RGD-WARROOM ALPHA</h1>
            <p style="font-size: 1.3rem; color: #334e68; font-weight: 500;">
                Il Digital Twin per la Governance Aziendale e il Risk Management Predittivo
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <div class="ai-reasoning" style="height: 280px;">
                <h3 style="color: #3498db;">📊 Intelligence Hub</h3>
                <p>Monitora la <b>Resilience Aziendale</b> con algoritmi EMA di nuova generazione. 
                Isoliamo i trend critici dalle fluttuazioni operative per garantirti una visione cristallina della solidità.</p>
                <div style="margin-top:15px; border-top: 1px solid rgba(212,175,55,0.2); padding-top:10px;">
                    <small style="color: #d4af37;">➔ FOCUS: PREVENZIONE DEL DECLINO OPERATIVO</small>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <div class="ai-reasoning" style="height: 280px; margin-top:20px;">
                <h3 style="color: #e74c3c;">🚨 Scenario Simulation</h3>
                <p>Anticipa il mercato con lo <b>Stress-Test Multivariabile</b>. 
                Simula scenari di crisi e inefficienze per testare la tenuta dei tuoi margini in un ambiente Sandbox sicuro.</p>
                <div style="margin-top:15px; border-top: 1px solid rgba(212,175,55,0.2); padding-top:10px;">
                    <small style="color: #d4af37;">➔ FOCUS: MITIGAZIONE PROATTIVA DEL RISCHIO</small>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="ai-reasoning" style="height: 280px;">
                <h3 style="color: #2ecc71;">🧠 AI Advisory Board</h3>
                <p>Supera la 'Dashboard Fatigue'. Il nostro motore basato su <b>LLM Llama-3.3</b> trasforma i dati complessi 
                in <b>Protocolli Esecutivi</b> chiari e pronti all'azione.</p>
                <div style="margin-top:15px; border-top: 1px solid rgba(212,175,55,0.2); padding-top:10px;">
                    <small style="color: #d4af37;">➔ FOCUS: DECISION-MAKING ASSISTITO DA IA</small>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class="ai-reasoning" style="height: 280px; margin-top:20px;">
                <h3 style="color: #9b59b6;">📜 Governance Audit</h3>
                <p>Mantieni un <b>Audit Trail</b> completo di ogni analisi. 
                Monitora l'evoluzione della tua strategia nel tempo grazie al database criptato ad alta sicurezza.</p>
                <div style="margin-top:15px; border-top: 1px solid rgba(212,175,55,0.2); padding-top:10px;">
                    <small style="color: #d4af37;">➔ FOCUS: COMPLIANCE E TRACCIABILITÀ STORICA</small>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.info("💡 **Executive Insight:** L'80% dei fallimenti aziendali deriva da una cattiva interpretazione dei trend. Inizia caricando i dati operativi nell'Intelligence Hub.")
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
        """
    <div class='warroom-header'>
            <h1>🚀 War Room Strategica</h1            <p style='color: white !important;'>
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
        # 1. SALVATAGGIO FISICO E MAPPATURA INTELLIGENTE
        path_raw = UPLOAD_DIR / azienda / uploaded_file.name
        path_raw.parent.mkdir(parents=True, exist_ok=True)
        with open(path_raw, "wb") as f:
            f.write(uploaded_file.getbuffer())
        with st.status("🔄 Protocollo Analitico RGD-Alpha in corso...") as status:
            # --- MANOVRA SMART MAPPER (Cervello Engine) ---
            engine = DataGateway()
            df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            df_mapped = engine.mappa_colonne_universale(df_raw)
            
            # Salviamo la versione mappata per l'Ingestore
            path_mapped = UPLOAD_DIR / azienda / "temp_mapped.csv"
            df_mapped.to_csv(str(path_mapped), index=False)

        ingestor = IngestoreDati()
        lista_asset = ingestor.elabora_csv(str(path_mapped), azienda)
        if lista_asset:
            db.registra_caricamento(user_id, "WAR_ROOM", uploaded_file.name)
                # 2. ESECUZIONE LOGICA PREDITTIVA
            report_analisi = engine.esegui_scan_strategico(
                lista_asset,
                    "UNIVERSAL",
                fattore_stress=f_stress,
                    weights=(0.7, 0.3)
            )
            kpi_reali = db.calcola_e_salva_kpi_correnti(user_id)
               
            status.update(label="✅ Analisi Quantitativa Completata!", state="complete")
        # --- 📊 ANALISI TECNICA MOMENTUM ---
        with st.expander("📊 Analisi Tecnica: Accelerazione Inefficienze"):
                df_p = pd.DataFrame(report_analisi)
                fig = px.bar(df_p, x="asset", y="momentum_score", color="stato", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
                # --- 3. RISULTATI EXECUTIVE ---
        rischio_val = kpi_reali.get("rischio_medio", 0)
        trend_testo = kpi_reali.get("trend", "Stabile")
        ore_totale = sum([a.get("ore_produttive_effettive", 0) for a in report_analisi])                
        st.markdown("### 📊 Intelligence Report: Analisi Strategica")
        c1, c2, c3, c4 = st.columns(4)
        col_r = "#e74c3c" if rischio_val > 7 else "#f39c12" if rischio_val > 4 else "#27ae60"                
        c1.markdown(f"<div class='metric-card'><h3>Solidità</h3><div class='value'>{kpi_reali.get('solidita')}%</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card' style='border-top-color:{col_r}'><h3>Rischio</h3><div class='value' style='color:{col_r}'>{rischio_val}/10</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><h3>Trend AI</h3><div class='value' style='font-size:1.2rem'>{trend_testo}</div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='metric-card'><h3>Ore Analizzate</h3><div class='value'>{int(ore_totale)} h</div></div>", unsafe_allow_html=True)

        # --- 4. DIAGNOSTICA IA (VERSIONE LUNGA E PROFESSIONALE) ---
        st.subheader("🧠 Diagnostica Strategica RGD + IA")
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
                    client = Groq(api_key=api_key)
                    media_momentum = round(df_p['momentum_score'].mean(), 2)
                    settore_ia = st.selectbox("Seleziona Settore:", ["Marketing", "Logistica", "Produzione", "Retail"], key="settore_ia_exec")
                        
        if st.button("🚀 ESEGUI ANALISI STRATEGICA PRESCRITTIVA"):
                    with st.spinner("L'AI sta elaborando la strategia..."):
                            try:
                                prompt_config = f"""
                                    Sei un Senior Business Consultant (CSO) per l'azienda {azienda} (Settore: {settore_ia}).
                                    DATI: Solidità {kpi_reali.get('solidita')}% | Rischio {rischio_val}/10 | Trend {trend_testo} | Ore {int(ore_totale)}.
                                    COMPITO: Rispondi con tono Executive:
                                    1. DIAGNOSI NUMERICA: Perché il trend è {trend_testo}?
                                    2. SOGLIE: Compara con il settore {settore_ia}.
                                    3. PIANO D'AZIONE: 3 AZIONI PRATICHE immediate.
                                    4. ALLERTA FATIGUE: Rischio se non si agisce in 7gg.
                                """
                                chat = client.chat.completions.create(
                                        messages=[{"role": "system", "content": "Sei un Chief Strategy Officer. Dai ordini esecutivi."},
                                                {"role": "user", "content": prompt_config}],
                                        model="llama-3.3-70b-versatile"
                                )
                                risposta = chat.choices[0].message.content
                                st.markdown(f"""<div class="ai-reasoning"><h4 style='color:#d4af37; border-bottom: 1px solid #d4af37; padding-bottom:10px;'>📋 RESOCONTO ESECUTIVO AI</h4><div style='color:#e2e8f0;'>{risposta.replace('1.', '<br><b>1.</b>').replace('2.', '<br><b>2.</b>').replace('3.', '<br><b>3.</b>').replace('4.', '<br><b>4.</b>')}</div></div>""", unsafe_allow_html=True)
                            except Exception as e:
                                    st.error(f"Errore IA: {e}")
                    # --- 5. PIANO D'AZIONE OPERATIVO INTELLIGENTE (Tieni questo!) ---
        st.subheader("📝 Piano d'Azione Operativo (Priorità)")
        report_ordinato = sorted(report_analisi, key=lambda x: x.get('rischio', 0), reverse=True)
        for asset in report_ordinato:
                        r, m, nome = asset.get("rischio", 0), asset.get("momentum_score", 0), asset.get('asset', 'Reparto Non Specificato')
                        if r > 7 and m > 2: box_style, label, consiglio = "kpi-box-critical", "🚨 EMERGENZA", "Bloccare le attività e avviare revisione immediata."
                        elif r > 5 or m > 1.5: box_style, label, consiglio = "kpi-box", "⚠️ ATTENZIONE", "Incrementare il monitoraggio e ottimizzare i turni."
                        else: box_style, label, consiglio = "kpi-box", "✅ NOMINALE", "Mantenere gli standard attuali. Eseguire controlli di routine."
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
#   PAGINA 4: ARCHIVIO STORICO (VERSIONE EXECUTIVE)
# ==========================================
elif scelta == "📜 Archivio Storico":
    st.title("📜 Archivio Storico Caricamenti")
    
    try:
        # 1. Recupero dati dal database
        df_logs = db.recupera_log_caricamenti_admin()
        
        if df_logs is not None and not df_logs.empty:
            if is_admin:
                st.info("👁️ Vista Admin: Monitoraggio Globale del Sistema")
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.info(f"📁 Registro Analisi Strategiche per: **{azienda}**")
                # FILTRO DI SICUREZZA: Mappatura chirurgica per azienda
                df_filtrato = df_logs[df_logs["azienda"] == azienda]
                
                if not df_filtrato.empty:
                    # Mostriamo i dati in modo elegante
                    st.dataframe(df_filtrato, use_container_width=True, hide_index=True)
                else:
                    st.warning(f"Nessuna operazione registrata per l'azienda {azienda}.")
        else:
            st.warning("L'archivio centrale è attualmente vuoto. Carica un file nella War Room per iniziare.")
            
    except Exception as e:
        st.error(f"❌ Errore critico di sincronizzazione archivio: {e}")
