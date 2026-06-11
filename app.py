import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

# --- 1. CONFIGURAZIONE PERCORSI E AMBIENTE ---
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
    st.sidebar.error(f"Errore caricamento Simulatore: {e}")
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

# --- 3. INIZIALIZZAZIONE SESSIONE E DATABASE ---
inizializza_sessione() 
db = DatabaseAziendale()

upload_path = os.getenv("UPLOAD_DIR", str(PROJECT_ROOT / "data" / "uploads"))
UPLOAD_DIR = Path(upload_path)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- 4. STILE CSS RGANDJA PREMIUM (UNIFICATO) ---
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
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
            border-top: 5px solid #3498db; transition: transform 0.3s ease;
        }
        .metric-card:hover { transform: translateY(-5px); }
        .metric-card h3 { color: #627d98; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 10px; }
        .metric-card .value { font-size: 2.2rem; font-weight: bold; color: #102a43; }
        .welcome-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem; border-radius: 1rem; color: white; margin: 2rem 0;
        }
        .step-box { background: white; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #3498db; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGICA REGISTRAZIONE PULITA ---
def registra_nuovo_utente(email: str, password: str, conferma: str):
    if not email or not password or not conferma:
        st.error("Compila tutti i campi richiesti.")
        return
    if password != conferma:
        st.error("Le password inserite non coincidono.")
        return
    try:
        if db.get_utente_by_email(email):
            st.error("Questa email è già registrata nei nostri sistemi.")
            return
        
        admin_email_env = os.getenv("ADMIN_EMAIL", "andrewdicenso@libero.it").lower()
        ruolo = "admin" if email.lower() == admin_email_env else "user"

        user_id = db.crea_utente(email=email, password=password, ruolo=ruolo, azienda=None)
        if user_id:
            st.success(f"✅ Registrazione completata come {ruolo.upper()}. Ora puoi effettuare l'accesso.")
            st.balloons()
    except Exception as e:
        st.error(f"Errore tecnico durante la registrazione: {e}")

# --- 6. SCHERMATA DI AUTENTICAZIONE ---
if not st.session_state.autenticato:
    tab_login, tab_register = st.tabs(["🔐 Login", "🆕 Registrazione"])
    with tab_login:
        st.title("🔐 Accesso Utente")
        e_login = st.text_input("Email", key="l_email").strip()
        p_login = st.text_input("Password", type="password", key="l_pwd").strip()
        if st.button("Accedi"):
            if login_utente(db, e_login, p_login): 
                st.rerun()
            else: 
                st.error("Credenziali errate.")
    with tab_register:
        st.title("🆕 Crea account Beta")
        e_reg = st.text_input("Email", key="r_email").strip()
        p_reg = st.text_input("Password", type="password", key="r_pwd").strip()
        c_reg = st.text_input("Conferma Password", type="password", key="r_conf").strip()
        if st.button("Registrati"): 
            registra_nuovo_utente(e_reg, p_reg, c_reg)
    st.stop()

# --- 7. CONFIGURAZIONE NAVIGAZIONE SIDEBAR ---
user_id = st.session_state.user_id
azienda = st.session_state.azienda
ruolo = st.session_state.ruolo
is_admin = (ruolo == "admin")

st.sidebar.title("🛡️ RGD-ALPHA")
st.sidebar.write(f"Operatore: **{azienda}**")
menu = ["🏠 Home", "📊 War Room Strategica", "📜 Archivio Storico"]
if is_admin: 
    menu.insert(1, "🕵️ Centrale Admin")
scelta = st.sidebar.radio("Navigazione", menu)

if st.sidebar.button("Logout"): 
    logout_utente()

# ==========================================
# 🏠 SEZIONE 1: HOME PAGE
# ==========================================
if scelta == "🏠 Home":
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='font-size: 3.5rem; margin: 0;'>🛡️ RGD-Alpha</h1>
            <h2 style='color: #7f8c8d; margin: 0.5rem 0 2rem 0;'>War Room Strategica Aziendale</h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class='welcome-card'>
            <h3 style='margin-top: 0;'>👋 Benvenuto nella tua War Room Personale</h3>
            <p style='font-size: 1.1rem; line-height: 1.6;'>
                <strong>RGD-Alpha</strong> è un sistema avanzato di 
                <strong>Risk Intelligence</strong> che analizza l'inventario operativo e calcola la 
                <strong>Solidità Strutturale</strong> del tuo ecosistema aziendale in tempo reale.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🚀 Come Iniziare (30 secondi)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='step-box'><h4>1️⃣ Imposta i Parametri</h4><p>Regola i pesi dell'algoritmo EMA e i giorni di stress dal menu laterale.</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='step-box'><h4>2️⃣ Carica un Dataset</h4><p>Vai su 'War Room Strategica', seleziona il reparto e trascina il tuo file.</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='step-box'><h4>3️⃣ Valuta le Criticità</h4><p>Ottieni immediatamente l'analisi di stabilità Monte Carlo e i suggerimenti predittivi.</p></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📊 Funzionalità Integrate")
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.markdown("##### 📈 Analisi Predittiva")
        st.small("Simulazioni probabilistiche basate su motori stocastici a 30 giorni.")
    with col_b:
        st.markdown("##### 🏭 Bilanciamento Multi-Settore")
        st.small("Algoritmi ricalibrati automaticamente per comparti specifici.")
    with col_c:
        st.markdown("##### 🔐 Sicurezza Asset")
        st.small("Flussi informativi protetti, conformità e segregazione dei database.")
    with col_d:
        st.markdown("##### 📝 Tracciamento Log")
        st.small("Audit log completo dei caricamenti storici per finalità ispettive.")

# ==========================================
# 📊 SEZIONE 2: WAR ROOM STRATEGICA
# ==========================================
elif scelta == "📊 War Room Strategica":
    st.markdown(f"<div class='warroom-header'><h1>🚀 War Room Strategica</h1><p>Analisi in tempo reale della solidità operativa di <strong>{azienda}</strong></p></div>", unsafe_allow_html=True)

    with st.expander("📋 GUIDA: Selezione Reparto / Area Focus", expanded=False):
        st.markdown("""
        Seleziona il **Dipartimento** corretto per calibrare i parametri interni dell'algoritmo RGD-Alfa:
        1. **Administration & Finance**
        2. **Production & Logistic**
        3. **Sales & Marketing**
        4. **Human Resources & Facilities**
        """)

    st.markdown("---")

    # Selezione Struttura Dipartimentale (Unica ed evitanti conflitti di duplicazione)
    struttura = mostra_interfaccia_4_aree()
    reparto_scelto = struttura['Dipartimento']

    st.subheader(f"📂 Analisi di Rischio Alpha: {reparto_scelto}")
    uploaded_file = st.file_uploader(f"Trascina qui il file Excel/CSV relativo a: {reparto_scelto}", type=["csv", "xlsx"], key="warroom_uploader")

    # Controlli di calibrazione e Stress Test in Sidebar
    with st.sidebar:
        with st.expander("⚙️ CALIBRAZIONE EMA", expanded=True):
            w1 = st.slider("Peso Presente (W1)", 0.1, 1.0, 0.7)
            w2 = st.slider("Peso Storico (W2)", 0.1, 1.0, 0.3)
        with st.expander("🚨 STRESS TEST", expanded=True):
            ritardo = st.slider("Ritardo Fornitori (Giorni)", 0, 30, 0)
            f_stress = 1.0 + (ritardo / 50.0)

    # Variabili di stato dell'elaborazione per evitare NameError fuori dai blocchi condizionali
    report_analisi = None
    risultati_sim = None
    risultato_wr = None

    if uploaded_file:
        path = genera_percorso_salvataggio(UPLOAD_DIR, azienda, reparto_scelto, uploaded_file.name)
        
        # Prima di aprire il file, assicuriamoci che la cartella esista
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())

            
        with st.status("🔄 Protocollo RGD-Alpha in corso...") as status:
            ingestor = IngestoreDati()
            lista_asset = ingestor.elabora_file(str(path), azienda)
            
            if lista_asset:
                engine = DataGateway()
                db.registra_caricamento(user_id, reparto_scelto.upper(), uploaded_file.name)
                
                report_analisi = engine.esegui_scan_strategico(lista_asset, reparto_scelto.upper(), fattore_stress=f_stress, weights=(w1, w2))
                
                for r in report_analisi:
                    db.salva_asset(user_id=user_id, nome_asset=r['asset'], rischio=r['rischio'], tipo=r['settore'], momentum=r['momentum_score'])
                
                kpi_reali = db.calcola_e_salva_kpi_correnti(user_id)
                
                # Classificazione Macro-Categoria
                risultato_wr = assegna_categoria_warroom(uploaded_file)
                
                # Simulazione Monte Carlo
                sim = SimulatoreRischio()
                risultati_sim = sim.esegui_stress_test(kpi_reali.get('solidita', 50), volatilita=0.5)
                
                # Sistema di notifica Sentinella
                sentinella = Sentinella()
                asset_a_rischio = [a for a in report_analisi if a.get('rischio', 0) > 7.5]
                
                if asset_a_rischio:
                    asset_a_rischio_dict = [a if isinstance(a, dict) else (vars(a) if hasattr(a, '__dict__') else {}) for a in asset_a_rischio]
                    sentinella.genera_report_strategico(asset_a_rischio_dict)
                    sentinella.genera_report(asset_a_rischio)
                    
                    try:
                        from core.email_manager import EmailManager
                        mailer = EmailManager()
                        corpo_mail = f"Attenzione, la War Room RGD-ALPHA ha rilevato {len(asset_a_rischio)} asset critici nel comparto {reparto_scelto}."
                        mailer.invia_alert_critico("andrewdicenso@libero.it", "⚠️ RGD-ALPHA: Alert Criticità Rilevata", corpo_mail)
                    except Exception as e:
                        st.sidebar.error(f"Errore invio notifica email: {e}")
                
                status.update(label="✅ Elaborazione completata con successo!", state="complete")
            else:
                status.update(label="❌ Errore: Dataset caricato non valido.", state="error")
                st.error("Il file inserito non ha superato i controlli di integrità dell'ingestore.")

    # --- RENDERING DEGLI OUTPUT (FUORI DAL BLOCCO STATUS PER PRESERVARE IL LAYOUT WIDE) ---
    kpi_reali = db.calcola_e_salva_kpi_correnti(user_id)

    # 1. Dashboard KPI Principali
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <h3>Solidità Operativa</h3>
            <div class='value'>{kpi_reali.get('solidita', 0)}%</div>
            <div style='color:gray; font-size:0.8rem;'>{"↑ Ottima" if kpi_reali.get('solidita', 0) > 80 else "→ Nella norma" if kpi_reali.get('solidita', 0) > 50 else "↓ Attenzione"}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        rischio_val = kpi_reali.get('rischio_medio', 0)
        colore_rischio = "#e74c3c" if rischio_val > 7 else "#f39c12" if rischio_val > 4 else "#27ae60"
        st.markdown(f"""
        <div class='metric-card' style='border-top-color: {colore_rischio};'>
            <h3>Rischio Medio</h3>
            <div class='value' style='color: {colore_rischio};'>{rischio_val}/10</div>
            <div style='color:gray; font-size:0.8rem;'>{"Critico" if rischio_val > 7 else "Medio" if rischio_val > 4 else "Basso"}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        tot_asset = len(report_analisi) if report_analisi else len(db.recupera_attivita_globale())
        st.markdown(f"""
        <div class='metric-card' style='border-top-color: #f39c12;'>
            <h3>Asset Analizzati</h3>
            <div class='value'>{tot_asset}</div>
            <div style='color:gray; font-size:0.8rem;'>Nodi attivi</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        impatto = kpi_reali.get('impatto_30gg', 'N/D')
        colore_impatto = "#e74c3c" if impatto == "CRITICO" else "#f39c12" if impatto == "ATTENZIONE" else "#27ae60"
        st.markdown(f"""
        <div class='metric-card' style='border-top-color: {colore_impatto};'>
            <h3>Impatto 30gg</h3>
            <div class='value' style='color: {colore_impatto};'>{impatto}</div>
            <div style='color:gray; font-size:0.8rem;'>Proiezione flussi</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    if report_analisi:
        if risultato_wr and "errore" not in risultato_wr:
            st.markdown(f"""
            <div style="background: #0e1117; border: 2px solid #ffd700; padding: 20px; border-radius: 12px; margin: 15px 0;">
                <h4 style="color: #ffd700; margin-top: 0;">🎯 Classificazione Macro-Categoria War Room</h4>
                <p style="margin: 5px 0; color: white;">La tua azienda è stata mappata come: <b><span style="color: #27c93f; font-size: 1.2rem;">{risultato_wr['categoria']}</span></b></p>
                <small style="color: #a0aec0;">💡 {risultato_wr['dettaglio']}</small>
            </div>
            """, unsafe_allow_html=True)

        # Indicatori Strategici Vitali
        st.header("🛡️ Indicatori Strategici Vitali")
        cols = st.columns(5)
        cols[0].metric("Solidità", f"{kpi_reali.get('solidita', 0)}%")
        cols[1].metric("Rischio Medio", f"{kpi_reali.get('rischio_medio', 0)}/10")
        avg_m = sum([a.get('momentum_score', 0) for a in report_analisi]) / len(report_analisi) if report_analisi else 0
        cols[2].metric("Trend Momentum", f"{round(avg_m, 2)}", delta="Accelerazione" if avg_m > 1.2 else "Stabile")
        cols[3].metric("Efficienza Risorse", "84.2%")
        res = max(round(100 - (f_stress * 10), 1), 0)
        cols[4].metric("Resilience", f"{res}%")

        # Sezione Grafici
        if risultati_sim and risultati_sim.get('percorsi_raw') is not None:
            st.subheader("🔮 Proiezione Stress Test (Monte Carlo 30gg)")
            fig_pred = genera_grafico_predittivo(risultati_sim['percorsi_raw'], giorni_proiettati=30)
            st.plotly_chart(fig_pred, use_container_width=True)
        else:
            st.info("🔮 Analisi IA: Esegui un caricamento valido per calcolare le proiezioni predittive stocastiche.")
        
        st.subheader("📈 Accelerazione del Rischio (Algoritmo EMA)")
        df_plot = pd.DataFrame(report_analisi)
        fig = px.bar(df_plot, x="asset", y="momentum_score", color="stato",
                     color_discrete_map={"CRITICO": "#ff5f56", "ATTENZIONE": "#ffbd2e", "OTTIMALE": "#27c93f"})
        st.plotly_chart(fig, use_container_width=True)

        # Ragionamento IA Dinamico Completato
        st.subheader("🧠 Ragionamento Strategico Intelligence")
        settore_rilevato = report_analisi[0].get('settore', 'GENERALE') if report_analisi else 'GENERALE'

        consigli_settore = {
            "PRIMARIO_ALIMENTARE": {
                "ufficio": "Qualità e Logistica",
                "guadagno": "+15% riduzione sprechi",
                "prognosi": "Rischio deperibilità elevato. La velocità di rotazione è vitale."
            },
            "SECONDARIO_MANIFATTURA": {
                "ufficio": "Produzione e Acquisti",
                "guadagno": "+12% ottimizzazione stock",
                "prognosi": "Rallentamento flussi rilevato. Possibile fermo macchina tra 10gg."
            },
            "TERZIARIO_LOGISTICA": {
                "ufficio": "Ufficio Spedizioni / Traffico",
                "guadagno": "+20% efficienza consegne",
                "prognosi": "Collo di bottiglia nei vettori. Saturazione magazzino imminente."
            },
            "EDILE": {
                "ufficio": "Capocantiere / Approvvigionamento",
                "guadagno": "+10% gestione materiali",
                "prognosi": "Fluttuazione dei prezzi delle materie prime rilevata. Stringere i contratti di fornitura."
            },
            "GENERALE": {
                "ufficio": "Ufficio Operation / Management",
                "guadagno": "+10% efficienza standard",
                "prognosi": "Nessuna anomalia strutturale critica rilevata. Continuare il monitoraggio ordinario."
            }
        }

        dettaglio_consiglio = consigli_settore.get(settore_rilevato, consigli_settore["GENERALE"])
        st.success(f"**Ufficio di Riferimento:** {dettaglio_consiglio['ufficio']} | **Ottimizzazione Attesa:** {dettaglio_consiglio['guadagno']}")
        st.markdown(f"> **Prognosi Strategica RGD:** {dettaglio_consiglio['prognosi']}")

# ==========================================
# 🕵️ SEZIONE 3: CENTRALE ADMIN
# ==========================================
elif scelta == "🕵️ Centrale Admin":
    st.title("🕵️ Centrale Admin")
    st.dataframe(db.supervisione_admin_metriche_globali(), use_container_width=True)

# ==========================================
# 📜 SEZIONE 4: ARCHIVIO STORICO
# ==========================================
elif scelta == "📜 Archivio Storico":
    st.title("📜 Archivio Storico")
    df_log = db.recupera_log_caricamenti_admin()
    
    if not df_log.empty:
        st.dataframe(df_log, use_container_width=True, hide_index=True)
        
        # Risolto il paradosso logico: il pulsante compare solo se l'archivio ha dei log da svuotare
        if st.button("🗑️ Svuota tutti i dati"):
            db.svuota_tabelle_totale()
            st.success("Tutti i log storici e gli asset sono stati rimossi dal database.")
            st.rerun()
    else:
        st.warning("📭 Nessun dato trovato in questo archivio storico.")