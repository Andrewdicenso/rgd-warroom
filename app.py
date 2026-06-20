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
#   CONFIGURAZIONE BASE & UI
# ==========================================
load_dotenv()
DATA_ROOT = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_ROOT / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Impostazione Layout Enterprise
st.set_page_config(
    page_title="RGD-Alpha | War Room Strategica", 
    layout="wide", 
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

# Inizializzazione Sessione (Fondamentale per Auth)
inizializza_sessione()

# ==========================================
#   GESTIONE ESTETICA (CSS ESTERNO)
# ==========================================
def load_css(file_name="style.css"):
    """Carica il design system del progetto."""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ Sistema visivo RGD non caricato. Verifica la presenza di style.css")

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
        
        # Recupero Admin Email (Standard RGD-Alpha)
        admin_email_env = os.getenv("ADMIN_EMAIL", "andrewdicenso@libero.it").lower()
        ruolo = "admin" if email.lower() == admin_email_env else "user"
        
        if db.crea_utente(email=email, password=password, ruolo=ruolo):
            st.success("✅ Registrazione completata. Effettua il login.")
            st.balloons()
    except Exception as e:
        st.error(f"Errore critico durante la registrazione: {e}")

# --- BLOCCO DI ACCESSO (Visualizzato solo se non autenticato) ---
if not st.session_state.autenticato:
    # Aggiungiamo il terzo Tab per il recupero credenziali
    t1, t2, t3 = st.tabs(["🔐 Login", "🆕 Registrazione", "🔄 Recupero Password"])
    
    with t1:
        e = st.text_input("Email Aziendale", key="l_e").strip()
        p = st.text_input("Password", type="password", key="l_p").strip()
        if st.button("Accedi al Sistema"):
            if login_utente(db, e, p):
                st.rerun()
            else:
                st.error("Credenziali non valide. Riprova.")
                
    with t2:
        re = st.text_input("Email per registrazione", key="r_e").strip()
        rp = st.text_input("Scegli Password", type="password", key="r_p").strip()
        rc = st.text_input("Conferma Password", type="password", key="r_c").strip()
        if st.button("Crea Account Enterprise"):
            registra_nuovo_utente(re, rp, rc)

    with t3:
        st.subheader("Reset Credenziali con Tracciamento")
        st.info("Nota: Ogni operazione di reset viene registrata nei log di sicurezza con data e ora.")
        res_e = st.text_input("Inserisci la tua Email", key="res_e").strip()
        res_p = st.text_input("Nuova Password", type="password", key="res_p").strip()
        res_c = st.text_input("Conferma Nuova Password", type="password", key="res_c").strip()
        
        if st.button("Aggiorna Password e Registra Evento"):
            if not res_e or not res_p:
                st.warning("Inserisci email e nuova password.")
            elif res_p != res_c:
                st.error("Le password non coincidono.")
            elif len(res_p) < 8:
                st.error("La password deve essere di almeno 8 caratteri per la sicurezza Enterprise.")
            else:
                # Esecuzione del reset tracciato nel database
                if db.reset_password_tracciato(res_e, res_p):
                    st.success("✅ Password aggiornata con successo!")
                    st.toast("Evento registrato nei log di sicurezza.")
                    st.info("Ora puoi tornare nel tab 'Login' e accedere.")
                else:
                    st.error("Impossibile procedere. Verifica l'email inserita.")
            
    st.stop() # Blocca l'esecuzione finché l'utente non è autenticato

# ==========================================
#   NAVIGAZIONE SIDEBAR EXECUTIVE (VERSIONE BLINDATA)
# ==========================================
# Recupero sicuro: se la sessione scade, evitiamo il crash
user_id = st.session_state.get('user_id', 0)
azienda = st.session_state.get('azienda', 'Operatore Sconosciuto')
ruolo = st.session_state.get('ruolo', 'user')
is_admin = ruolo == "admin"

st.sidebar.title("🛡️ RGD-ALPHA")
st.sidebar.write(f"Operatore: **{azienda}**")

# Menu dinamico
menu = ["🏠 Home", "📊 War Room Strategica", "📜 Archivio Storico"]
if is_admin:
    menu.insert(1, "🕵️ Centrale Admin")

scelta = st.sidebar.radio("Navigazione", menu)

# --- STRESS TEST PULITO ---
st.sidebar.markdown("---")
st.sidebar.subheader("🚨 Simulazione Stress Test")
f_stress = st.sidebar.slider(
    "Moltiplicatore Inefficienze", 
    min_value=1.0, 
    max_value=2.5, 
    value=1.0, 
    step=0.1,
    help="Simula un aumento del rischio operativo globale."
)
st.sidebar.caption("Leva attiva per simulazione scenari di crisi.")

st.sidebar.markdown("---")
if st.sidebar.button("Logout", key="logout_sidebar"):
    logout_utente()


# --- INIZIO BLOCCO TUTELA LEGALE RGANDJA ---
st.sidebar.markdown("---")
with st.sidebar.expander("⚖️ Note Legali & Copyright"):
    st.markdown(f"""
    <div style="font-size: 0.85em; color: #555; line-height: 1.4;">
        <strong>Proprietario Intellettuale:</strong><br>
        [Tuo Nome e Cognome]<br><br>
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
    """, unsafe_allow_html=True)

st.sidebar.caption("© 2024 Rgandja. Tutti i diritti riservati.")
# --- FINE BLOCCO TUTELA LEGALE ---

# ==========================================
# RIGA DI RIFERIMENTO FINALE: (Fine del file)
# ==========================================


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
    st.markdown("""
        <div style="background-color: #1e3c72; padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;">
            <h2 style="margin: 0; color: white;">🕵️ Centrale di Supervisione Admin</h2>
            <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.8);">Monitoraggio globale delle attività di sistema e degli accessi utente.</p>
        </div>
    """, unsafe_allow_html=True)

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
            # Ordiniamo per data se possibile, altrimenti mostriamo l'intero log
            st.dataframe(df_asset_globale, use_container_width=True)
        else:
            st.warning("Nessuna attività registrata negli asset logs.")

    except Exception as e:
        st.error(f"❌ Errore critico nel caricamento del pannello Admin: {e}")

# ==========================================
#   PAGINA 3: WAR ROOM STRATEGICA (OTTIMIZZATA)
# ==========================================
elif scelta == "📊 War Room Strategica":
    st.markdown(
        f"""
        <div class='warroom-header'>
            <h1 style='color: white !important;'>🚀 War Room Strategica</h1>
            <p style='color: white !important;'>
                Analisi quantitativa oraria $H_{{(prod)}}$ e solidità in tempo reale per: 
                <strong style='color: white !important;'>{azienda}</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # 1. Caricamento file dati operativi
    uploaded_file = st.file_uploader(
        "📁 Carica file dati operativi (SAP, Salesforce, Excel Custom)", 
        type=["csv", "xlsx", "xls"]
    )   

    # 2. Esecuzione Pipeline solo in presenza del file
    if uploaded_file:
        # Salvataggio di sicurezza del file RAW caricato dal manager
        path_raw = UPLOAD_DIR / azienda / uploaded_file.name
        path_raw.parent.mkdir(parents=True, exist_ok=True)
        with open(path_raw, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Unico blocco di stato per l'intera pipeline di calcolo e raffinazione
        with st.status("🔄 Protocollo Analitico RGD-Alpha in corso...", expanded=True) as status:
            
            status.write("🔍 Fase 1: Identificazione impronta digitale del software e pulizia...")
            
            # Controlla questo pezzetto dentro app.py:
            status.write("🔍 Fase 1: Identificazione impronta digitale del software e pulizia...")

            # 1. Recuperiamo il paese dell'azienda (con fallback su 'IT')
            paese_calendar = st.session_state.get("paese_azienda", "IT") 

            # 2. Passiamo il paese all'istanza
            refinery = DataRefinery(country=paese_calendar)

            # 3. Eseguiamo il raffinamento passandogli il file
            refined_result = refinery.refine_file(str(path_raw)) 
            df_pulito = refined_result["data"]
            
            # Il motore esegue il raffinamento usando il calendario appena definito
            refined_result = refinery.refine_file(str(path_raw)) 
            df_pulito = refined_result["data"]
            
            if refined_result.get("anomalies"):
                st.warning(f"⚠️ Rilevate anomalie strutturali fango: {len(refined_result['anomalies'])} righe corrette.")

            status.write("🗺️ Fase 2: Smart Mapping delle colonne universali...")
            engine = DataGateway()
            df_mapped = engine.mappa_colonne_universale(df_pulito)
            
            # Salvataggio del file normalizzato pronto per l'ingestione
            path_mapped = UPLOAD_DIR / azienda / "temp_mapped.csv"
            df_mapped.to_csv(str(path_mapped), index=False)

            status.write("📥 Fase 3: Ingestione e calcolo degli asset strategici...")
            ingestor = IngestoreDati()
            lista_asset = ingestor.elabora_csv(str(path_mapped), azienda)

            if lista_asset:
                # Registra l'evento nell'Audit Trail dell'azienda
                db.registra_caricamento(user_id, "WAR_ROOM", uploaded_file.name)
                
                status.write("📈 Fase 4: Calcolo quantitativo predittivo ed elaborazione $H_{(prod)}$...")
                # Esecuzione della logica predittiva con fattore stress attivo dalla sidebar
                report_analisi = engine.esegui_scan_strategico(
                    lista_asset,
                    "UNIVERSAL",
                    fattore_stress=f_stress,
                    weights=(0.7, 0.3)
                )
                
                # Passiamo i dati correnti per calcolare le metriche aggiornate
                kpi_reali = db.calcola_e_salva_kpi_correnti(user_id, report_analisi)
                
                # Creazione sicura del DataFrame per l'analisi dei punteggi e grafici
                df_p = pd.DataFrame(report_analisi)
                
                status.update(label="✅ Protocollo RGD-Alpha Completato con Successo!", state="complete")
            else:
                status.update(label="❌ Errore critico durante l'ingestione dei dati.", state="error")
                st.stop()

        # --- 📊 VISUALIZZAZIONE RISULTATI EXECUTIVE ---
        rischio_val = kpi_reali.get("rischio_medio", 0) if kpi_reali else 0
        trend_testo = kpi_reali.get("trend", "Stabile") if kpi_reali else "N/D"
        solidita_val = kpi_reali.get("solidita", 0) if kpi_reali else 0
        ore_totale = df_p['ore_produttive_effettive'].sum() if not df_p.empty else 0
        
        st.markdown("### 📊 Intelligence Report: Analisi Strategica")
        c1, c2, c3, c4 = st.columns(4)
        col_r = "#e74c3c" if rischio_val > 7 else "#f39c12" if rischio_val > 4 else "#27ae60"
        
        c1.markdown(f"<div class='metric-card'><h3>Solidità</h3><div class='value'>{solidita_val}%</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card' style='border-top-color:{col_r}'><h3>Rischio</h3><div class='value' style='color:{col_r};'>{rischio_val}/10</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><h3>Trend AI</h3><div class='value' style='font-size:1.2rem'>{trend_testo}</div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='metric-card'><h3>Ore Analizzate</h3><div class='value'>{int(ore_totale)} h</div></div>", unsafe_allow_html=True)

        # --- 👀 EXPANDER: ANALISI TECNICA MOMENTUM ---
        with st.expander("📊 Analisi Tecnica: Accelerazione Inefficienze"):
            variazione = kpi_reali.get("variazione_momentum", 0) if kpi_reali else 0
            if variazione == 0:
                st.info("ℹ️ **Nota per il Management:** Questo è il primo rilevamento per l'azienda. Il calcolo della velocità (Momentum) sarà disponibile a partire dal prossimo caricamento dati.")
            else:
                st.metric(label="Variazione Momentum Strategico", value=f"{variazione}%")
            
            # Mostra la tabella dei dati dell'analisi
            st.dataframe(df_p, use_container_width=True, hide_index=True)

        # --- 🧠 DIAGNOSTICA IA ---
        st.subheader("🧠 Diagnostica Strategica RGD + IA")
        api_key = os.getenv("GROQ_API_KEY")
        if api_key and not df_p.empty:
            client = Groq(api_key=api_key)
            media_momentum = round(df_p['momentum_score'].mean(), 2)
            settore_ia = st.selectbox("Seleziona Settore:", ["Marketing", "Logistica", "Produzione", "Retail"], key="settore_ia_exec")
                
            if st.button("🚀 ESEGUI ANALISI STRATEGICA PRESCRITTIVA"):
                with st.spinner("AI al lavoro..."):
                    try:
                        prompt_config = f"Analisi per {azienda} ({settore_ia}). Solidità {solidita_val}% | Rischio {rischio_val}/10 | Trend {trend_testo} | Media Momentum {media_momentum}."
                        chat = client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": "Sei un CSO (Chief Strategy Officer) di alto livello per il sistema Rgandja."},
                                {"role": "user", "content": prompt_config}
                            ],
                            model="llama-3.3-70b-versatile"
                        )
                        st.markdown(f"<div class='ai-reasoning'><h4 style='color:#d4af37'>📋 RESOCONTO ESECUTIVO</h4>{chat.choices[0].message.content}</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Errore IA: {e}")

        # --- 📝 PIANO D'AZIONE OPERATIVO ---
        st.subheader("📝 Piano d'Azione Operativo (Priorità)")
        report_ordinato = sorted(report_analisi, key=lambda x: x.get('rischio', 0), reverse=True)
        for asset in report_ordinato:
            r, m, nome = asset.get("rischio", 0), asset.get("momentum_score", 0), asset.get('asset', 'N/D')
            if r > 7 and m > 2: 
                box_style, label, consiglio = "kpi-box-critical", "🚨 EMERGENZA", "Bloccare attività e mitigare immediatamente il rischio operativo."
            elif r > 5 or m > 1.5: 
                box_style, label, consiglio = "kpi-box", "⚠️ ATTENZIONE", "Incrementare il monitoraggio e isolare le varianze orarie."
            else: 
                box_style, label, consiglio = "kpi-box", "✅ NOMINALE", "Standard mantenuti. Continuare la normale governance."
            
            st.markdown(f"<div class='{box_style}'><b>{nome}</b> | Rischio: {r} | Momentum: {m}<br><small>🎯 {consiglio}</small></div>", unsafe_allow_html=True)
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
