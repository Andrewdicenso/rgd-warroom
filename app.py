import os
import sys  # <--- RISOLVE: Il NameError (sys non definito)
from pathlib import Path
from datetime import datetime
import pandas as pd
import plotly.express as px

import streamlit as st
from dotenv import load_dotenv

# --- CONFIGURAZIONE PERCORSI SISTEMA ---
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
if str(PROJECT_ROOT / "core") not in sys.path:
    sys.path.append(str(PROJECT_ROOT / "core"))

# --- MODULI CORE & AUTH ---
from core.ingestor import IngestoreDati
from core.engine import DataGateway
from core.database import DatabaseAziendale
from core.notifier import Sentinella
from auth.auth import inizializza_sessione, login_utente, logout_utente
from core.experimental_modules.warroom_engine import assegna_categoria_warroom
from core.experimental_modules.reparti_engine import mostra_interfaccia_4_aree, genera_percorso_salvataggio
# --- 1. CONFIGURAZIONE PAGINA (Deve essere la prima funzione Streamlit chiamata) ---
st.set_page_config(
    page_title="War Room Strategica | RGandja",
    page_icon="🚀",
    layout="wide",  # Questo rende il progetto "degno" occupando tutto lo spazio
    initial_sidebar_state="expanded"
)

# --- 2. CENTRALIZZAZIONE DELLO STILE (RGANDJA PREMIUM LOOK) ---
st.markdown("""
<style>
    /* Sfondo e Font */
    .stApp { background-color: #f4f7f9; }
    
    /* Header Professionale */
    .warroom-header {
        background: linear-gradient(135deg, #102a43 0%, #243b53 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border-bottom: 5px solid #d4af37; /* Oro RGandja */
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        color: white;
    }

    /* Griglia KPI */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border-top: 5px solid #3498db;
        transition: transform 0.3s ease;
    }
    .metric-card:hover { transform: translateY(-5px); }
    .metric-card h3 { color: #627d98; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 10px; }
    .metric-card .value { font-size: 2.2rem; font-weight: bold; color: #102a43; }

    /* Barra Aree Aziendali */
    .area-container {
        display: flex;
        gap: 15px;
        margin-bottom: 2rem;
    }
    .area-box {
        flex: 1;
        background: #e1e7ec;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        color: #243b53;
        border: 1px solid #cbd5e0;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. INIZIALIZZAZIONE SESSIONE ---
inizializza_sessione() 

# --- CARICAMENTO MODULI ANALITICI CON FALLBACK ---
from visuals import genera_grafico_predittivo

try:
    from simulator import SimulatoreRischio
except Exception as e:
    st.sidebar.error(f"Errore caricamento Simulatore: {e}")
    class SimulatoreRischio: 
        def __init__(self, *args, **kwargs): pass
        def esegui_stress_test(self, *args, **kwargs): return {"probabilita_crisi": 0, "percorsi_raw": None}

# =========================
#   CONFIGURAZIONE BASE
# =========================
load_dotenv()
PROJECT_ROOT = Path(__file__).parent

# Se siamo su Render, usiamo la cartella temporanea (/tmp), altrimenti quella locale
upload_path = os.getenv("UPLOAD_DIR", str(PROJECT_ROOT / "data" / "uploads"))
UPLOAD_DIR = Path(upload_path)

# Crea la cartella se non esiste
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

inizializza_sessione()

# ========================================================
#   CSS CENTRALIZZATO (Richiama il file style.css)
# ========================================================
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    # Se il file non viene trovato (es. primo deploy), usa uno stile di backup
    st.warning("⚠️ File style.css non trovato. Caricamento stile di base.")

db = DatabaseAziendale()

# =========================
#   GESTIONE REGISTRAZIONE (Versione Pulita)
# =========================
def registra_nuovo_utente(email: str, password: str, conferma: str):
    if not email or not password or not conferma:
        st.error("Compila tutti i campi.")
        return
    if password != conferma:
        st.error("Le password non coincidono.")
        return
    
    try:
        # 1. Verifica se l'utente esiste già
        esistente = db.get_utente_by_email(email)
        if esistente:
            st.error("Email già registrata.")
            return
        
        # 2. Determina ruolo (Admin se l'email coincide con quella in .env o quella di default)
        admin_email_env = os.getenv("ADMIN_EMAIL", "andrewdicenso@libero.it").lower()
        ruolo = "admin" if email.lower() == admin_email_env else "user"

        # 3. Crea l'utente nel Database
        # Passiamo None come azienda per farla generare automatica (es. AZ-123)
        user_id = db.crea_utente(email=email, password=password, ruolo=ruolo, azienda=None)
        
        if user_id:
            st.success(f"✅ Registrazione completata come {ruolo.upper()}. Ora puoi accedere.")
            st.balloons()
            
    except Exception as e:
        st.error(f"Errore critico durante la registrazione: {e}")

# =========================
#   SCHERMATA AUTH (Login e Tabs)
# =========================
if not st.session_state.autenticato:
    tab_login, tab_register = st.tabs(["🔐 Login", "🆕 Registrazione"])
    
    with tab_login:
        st.header("🔐 Accesso Utente")
        e_login = st.text_input("Email", key="l_email").strip()
        p_login = st.text_input("Password", type="password", key="l_pwd").strip()
        if st.button("Accedi"):
            if login_utente(db, e_login, p_login): 
                st.rerun()
            else: 
                st.error("Credenziali errate.")
                
    with tab_register:
        st.header("🆕 Crea account Beta")
        e_reg = st.text_input("Email", key="r_email").strip()
        p_reg = st.text_input("Password", type="password", key="r_pwd").strip()
        c_reg = st.text_input("Conferma", type="password", key="r_conf").strip()
        if st.button("Registrati"): 
            registra_nuovo_utente(e_reg, p_reg, c_reg)
            
    st.stop()

# ========================================================
#   1. RECUPERO DATI E SIDEBAR (Sempre visibile)
# ========================================================
user_id = st.session_state.get('user_id')
azienda = st.session_state.get('azienda', 'N/D')
ruolo = st.session_state.get('ruolo', 'user')
is_admin = (ruolo == "admin")

with st.sidebar:
    st.markdown(f"### 🛡️ RGD-ALPHA\n**Operatore:** {azienda}")
    
    # MENU NAVIGAZIONE
    menu = ["🏠 Home", "📊 War Room Strategica", "📜 Archivio Storico"]
    if is_admin: 
        menu.insert(1, "🕵️ Centrale Admin")
    scelta = st.sidebar.radio("Navigazione", menu)
    
    st.markdown("---")
    
    # PARAMETRI TECNICI
    with st.expander("⚙️ CALIBRAZIONE EMA", expanded=True):
        w1 = st.slider("Peso Presente (W1)", 0.1, 1.0, 0.7)
        w2 = st.slider("Peso Storico (W2)", 0.1, 1.0, 0.3)
    
    with st.expander("🚨 STRESS TEST", expanded=True):
        ritardo = st.slider("Ritardo Fornitori (GG)", 0, 30, 0)
        f_stress = 1.0 + (ritardo / 50.0)

    st.markdown("---")
    if st.button("🚪 Esci dalla Sessione"):
        logout_utente()

# ========================================================
#   2. LOGICA DELLE PAGINE (Al centro)
# ========================================================

# --- HOME PAGE ---
if scelta == "🏠 Home":
    st.markdown(f"""
        <div class='warroom-header' style='text-align: center;'>
            <h1 style='font-size: 3.5rem;'>🛡️ RGD-ALPHA</h1>
            <p style='font-size: 1.2rem; opacity: 0.9;'>Sistemi Avanzati di Risk Intelligence Aziendale</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class='welcome-card' style='background: white; padding: 2rem; border-radius: 15px; border-top: 5px solid #d4af37; box-shadow: 0 4px 12px rgba(0,0,0,0.05);'>
            <h2 style='margin-top: 0;'>👋 Benvenuto, Operatore {azienda}</h2>
            <p style='font-size: 1.15rem; color: #334e68;'>
                RGD-Alpha è il tuo centro di comando strategico. 
            </p>
        </div>
    """, unsafe_allow_html=True)

# --- WAR ROOM STRATEGICA ---
elif scelta == "📊 War Room Strategica":
    st.markdown(f"<div class='warroom-header' style='text-align: center;'><h1>🚀 War Room Strategica</h1><p>Operatore: {azienda}</p></div>", unsafe_allow_html=True)
    
    # Selezione Reparti
    st.markdown("### 🏢 Seleziona Destinazione Documento")
    macro_scelta, reparto_scelto = mostra_interfaccia_4_aree()
    
    st.divider()
    
    # Caricamento file
    uploaded_file = st.file_uploader("📂 Carica inventario CSV", type=["csv"])
    
    if uploaded_file:
        with st.status("🔄 Analisi in corso...") as status:
            # Qui il sistema eseguirà il caricamento e l'analisi
            st.write("File ricevuto, elaborazione dati...")
            # Inserire qui la tua logica di salvataggio file (path = ...)

# --- CENTRALE ADMIN ---
elif scelta == "🕵️ Centrale Admin" and is_admin:
    st.title("🕵️ Centrale Admin")
    df_utenti = db.get_tutti_gli_utenti()
    st.dataframe(df_utenti, use_container_width=True)


# =========================
#   WAR ROOM STRATEGICA
# =========================
elif scelta == "📊 War Room Strategica":
    # 1. HEADER
    st.markdown(f"""
        <div class='warroom-header'>
            <h1>🚀 War Room Strategica</h1>
            <p>Analisi in tempo reale della solidità operativa di <strong>{azienda}</strong></p>
        </div>
    """, unsafe_allow_html=True)
    
    # 2. POSIZIONE CORRETTA: Fuori dalla sidebar, al centro della pagina!
    st.markdown("### 🏢 Seleziona Destinazione Documento") # Aggiungi il testo tra parentesi
    macro_scelta, reparto_scelto = mostra_interfaccia_4_aree() 
    
    st.markdown("---") # Linea di separazione

    # 3. METRICHE (Le 4 colonne con i numeri)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <h3>Solidità Operativa</h3>
            <div class='value'>N/D</div>
            <div class='delta'>%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='metric-card' style='border-top-color: #e74c3c;'>
            <h3>Rischio Medio</h3>
            <div class='value'>N/D</div>
            <div class='delta'>/10</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='metric-card' style='border-top-color: #f39c12;'>
            <h3>Asset Analizzati</h3>
            <div class='value'>0</div>
            <div class='delta'>totali</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class='metric-card' style='border-top-color: #27ae60;'>
            <h3>Impatto 30gg</h3>
            <div class='value'>N/D</div>
            <div class='delta'>proiezione</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
        # --- 1. SIDEBAR: PARAMETRI E LOGOUT ---
    with st.sidebar:
        # Prima gli expander con i parametri
        with st.expander("⚙️ CALIBRAZIONE EMA", expanded=True):
            w1 = st.slider("Peso Presente (W1)", 0.1, 1.0, 0.7)
            w2 = st.slider("Peso Storico (W2)", 0.1, 1.0, 0.3)
            
        with st.expander("🚨 STRESS TEST", expanded=True):
            ritardo = st.slider("Ritardo Fornitori (Giorni)", 0, 30, 0)
            f_stress = 1.0 + (ritardo / 50.0)

        # AGGIUNGI QUESTO ALLA FINE DELLA SIDEBAR
        st.sidebar.markdown("---") # Una linea di divisione
        if st.sidebar.button("🚪 Esci dalla Sessione"): 
            logout_utente()
            
    # --- 2. AREA CENTRALE: CARICAMENTO E ANALISI ---
    # Nota come queste righe ora iniziano dall'inizio della colonna, 
    # non sono più "figlie" della sidebar!
    st.markdown("---")
    uploaded_file = st.file_uploader("📂 Carica inventario CSV per l'analisi strategica", type=["csv"])

    if uploaded_file:
        path = genera_percorso_salvataggio(UPLOAD_DIR, azienda, macro_scelta, reparto_scelto, uploaded_file.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        with st.status("🔄 Protocollo RGD-Alpha in corso...") as status:
            ingestor = IngestoreDati()
            lista_asset = ingestor.elabora_file(str(path), azienda)
            
            if lista_asset:
                engine = DataGateway()

                # RIPRISTINATO: Uso di user_id come richiesto
                db.registra_caricamento(user_id, reparto_scelto.upper(), uploaded_file.name)
                
                # Calcolo con Stress Test e Pesi EMA
                report_analisi = engine.esegui_scan_strategico(lista_asset, reparto_scelto.upper(), fattore_stress=f_stress, weights=(w1, w2))
                
                # --- CICLO COMPILAZIONE DATABASE ---
                for r in report_analisi:
                    db.salva_asset(user_id=user_id, nome_asset=r['asset'], rischio=r['rischio'], tipo=r['settore'], momentum=r['momentum_score'])
                kpi_reali = db.calcola_e_salva_kpi_correnti(user_id)

                # --- NUOVA ANALISI AUTONOMA WAR ROOM ---
                risultato_wr = assegna_categoria_warroom(uploaded_file)
                if "errore" not in risultato_wr:
                    st.markdown(f"""
                    <div style="background: #0e1117; border: 2px solid #ffd700; padding: 20px; border-radius: 12px; margin: 15px 0;">
                        <h4 style="color: #ffd700; margin-top: 0; display: flex; align-items: center;">🎯 Classificazione Macro-Categoria War Room</h4>
                        <p style="margin: 5px 0;">La tua azienda è stata mappata come: <b><span style="color: #27c93f; font-size: 1.2rem;">{risultato_wr['categoria']}</span></b></p>
                        <small style="color: #a0aec0;">💡 {risultato_wr['dettaglio']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                # --- ESECUZIONE SIMULAZIONE MONTE CARLO ---
                sim = SimulatoreRischio()
                risultati_sim = sim.esegui_stress_test(kpi_reali.get('solidita', 50), volatilita=0.5)

                # --- ESECUZIONE SENTINELLA (Notifica Automatica & Email) ---
                sentinella = Sentinella()
                asset_a_rischio = [a for a in report_analisi if a.get('rischio') > 7.5]

                if asset_a_rischio:
                    asset_a_rischio_dict = [a if isinstance(a, dict) else (vars(a) if hasattr(a, '__dict__') else {}) for a in asset_a_rischio]
                    sentinella.genera_report_strategico(asset_a_rischio_dict)

                    # 2. INVIO EMAIL (Nuova funzione Enterprise)
                    try:
                        from core.email_manager import EmailManager
                        mailer = EmailManager()
                        corpo_mail = f"Attenzione Andrew, la War Room ha rilevato {len(asset_a_rischio)} asset critici. Controlla il pannello di controllo."
                        mailer.invia_alert_critico("andrewdicenso@libero.it", "⚠️ RGD-ALPHA: Alert Criticità Rilevata", corpo_mail)
                    except Exception as e:
                        st.sidebar.error(f"Errore invio notifica: {e}")

                    st.warning(f"⚠️ Rilevate criticità: Report di allerta generato e notifica inviata.")

                    # --- GRAFICO PREDITTIVO INTEGRATO ---
                    # 1. Genera il report su file
                    sentinella.genera_report(asset_a_rischio)

                    # 2. INVIO EMAIL
                    try:
                        from core.email_manager import EmailManager
                        mailer = EmailManager()
                        corpo_mail = f"Attenzione Andrew, rilevati {len(asset_a_rischio)} asset critici."
                        mailer.invia_alert_critico("andrewdicenso@libero.it", "⚠️ RGD-ALPHA ALERT", corpo_mail)
                    except Exception as e:
                        st.sidebar.error(f"Errore invio: {e}")

                # AGGIORNA LE METRICHE IN ALTO DINAMICAMENTE
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown("""
                    <div class='metric-card'>
                        <h3>Solidità Operativa</h3>
                        <div class='value'>{}%</div>
                        <div class='delta'>{}</div>
                    </div>
                    """.format(
                        kpi_reali.get('solidita', 0),
                        "↑ Ottima" if kpi_reali.get('solidita', 0) > 80 else "→ Nella norma" if kpi_reali.get('solidita', 0) > 50 else "↓ Attenzione"
                    ), unsafe_allow_html=True)
                
                with col2:
                    rischio_val = kpi_reali.get('rischio_medio', 0)
                    colore_rischio = "#e74c3c" if rischio_val > 7 else "#f39c12" if rischio_val > 4 else "#27ae60"
                    st.markdown("""
                    <div class='metric-card' style='border-top-color: {};'>
                        <h3>Rischio Medio</h3>
                        <div class='value' style='color: {}'>{}/10</div>
                        <div class='delta'>{}</div>
                    </div>
                    """.format(
                        colore_rischio,
                        colore_rischio,
                        rischio_val,
                        "Critico" if rischio_val > 7 else "Medio" if rischio_val > 4 else "Basso"
                    ), unsafe_allow_html=True)
                
                with col3:
                    st.markdown("""
                    <div class='metric-card' style='border-top-color: #f39c12;'>
                        <h3>Asset Analizzati</h3>
                        <div class='value'>{}</div>
                        <div class='delta'>totali</div>
                    </div>
                    """.format(len(report_analisi)), unsafe_allow_html=True)
                
                with col4:
                    impatto = kpi_reali.get('impatto_30gg', 'N/D')
                    colore_impatto = "#e74c3c" if impatto == "CRITICO" else "#f39c12" if impatto == "ATTENZIONE" else "#27ae60"
                    st.markdown("""
                    <div class='metric-card' style='border-top-color: {};'>
                        <h3>Impatto 30gg</h3>
                        <div class='value' style='color: {}'>{}</div>
                        <div class='delta'>proiezione</div>
                    </div>
                    """.format(colore_impatto, colore_impatto, impatto), unsafe_allow_html=True)
                
                st.markdown("---")

                # --- 5 KPI ALPHA ---
                st.header("🛡️ Indicatori Strategici Vitali")
                cols = st.columns(5)
                cols[0].metric("Solidità", f"{kpi_reali.get('solidita', 0)}%")
                cols[1].metric("Rischio Medio", f"{kpi_reali.get('rischio_medio', 0)}/10")
                avg_m = sum([a.get('momentum_score', 0) for a in report_analisi]) / len(report_analisi) if report_analisi else 0
                cols[2].metric("Trend Momentum", f"{round(avg_m, 2)}", delta="Accelerazione" if avg_m > 1.2 else "Stabile")
                cols[3].metric("Efficienza Risorse", "84.2%")
                res = max(round(100 - (f_stress * 10), 1), 0)
                cols[4].metric("Resilience", f"{res}%")

                # --- GRAFICO PREDITTIVO INTEGRATO (VERSIONE DEFINITIVA) ---
                if risultati_sim and risultati_sim.get('percorsi_raw') is not None:
                    st.subheader("🔮 Proiezione Stress Test (Monte Carlo 30gg)")
                    fig_pred = genera_grafico_predittivo(risultati_sim['percorsi_raw'], giorni_proiettati=30)
                    st.plotly_chart(fig_pred, use_container_width=True)
                else:
                    st.info("🔮 Analisi IA: Proiezione grafica temporaneamente non disponibile.")
                
                # --- GRAFICO MOMENTUM ---
                st.subheader("📈 Accelerazione del Rischio (Algoritmo EMA)")
                df_plot = pd.DataFrame(report_analisi)
                fig = px.bar(df_plot, x="asset", y="momentum_score", color="stato",
                             color_discrete_map={"CRITICO": "#ff5f56", "ATTENZIONE": "#ffbd2e", "OTTIMALE": "#27c93f"})
                st.plotly_chart(fig, use_container_width=True)

                # --- RAGIONAMENTO IA DINAMICO ---
                st.subheader("🧠 Ragionamento Strategico Intelligence")

                # Recuperiamo il settore rilevato dall'analisi
                settore_rilevato = report_analisi[0].get('settore', 'GENERALE') if report_analisi else 'GENERALE'

                # Definiamo i suggerimenti specifici per reparto/ufficio in base al settore
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
                        "prognosi": "Ritardo forniture materiali pesanti. Rischio penali su commessa."
                    }
                }

                # Recuperiamo i dettagli o usiamo quelli standard
                info = consigli_settore.get(settore_rilevato, {
                    "ufficio": "Direzione Generale",
                    "guadagno": "+5% efficienza globale",
                    "prognosi": "Parametri standard. Monitorare la stabilità operativa."
                })

                st.markdown(f"""
                <div class="ai-reasoning">
                    <strong>📍 ANALISI PER REPARTO: <span style='color:#3498db'>{info['ufficio']}</span></strong><br>
                    <strong>📊 SETTORE IDENTIFICATO:</strong> {settore_rilevato.replace('_', ' ')}<br><br>
                    
                    <strong>🔮 PROGNOSI IA:</strong><br>
                    {info['prognosi']} Il sistema rileva che la resilienza è al {res}%. 
                    Il Momentum Score indica un'espansione del rischio specifica per il comparto {settore_rilevato}.<br><br>
                    
                    <strong>🚀 AZIONE ALPHA (Suggerimento):</strong><br>
                    Intervenire entro 15gg. Si suggerisce di dare priorità agli asset con Momentum > 1.5. 
                    L'intervento tempestivo porterà a un <strong>incremento stimato del {info['guadagno']}</strong> sui margini operativi.
                </div>
                """, unsafe_allow_html=True)

                # --- DETTAGLIO ASSET ---
                st.subheader("📝 Piano d'Azione per Asset")
                for asset in report_analisi:
                    r = asset.get('rischio', 0)
                    box = "kpi-box-critical" if r > 7 else "kpi-box"
                    st.markdown(f"""
                    <div class="{box}">
                        <b>{asset.get('asset')}</b> | Rischio: {r} | Momentum: {asset.get('momentum_score')}
                        <br><small>🎯 <b>IA ADVICE:</b> {asset.get('consiglio_strategico')}</small>
                    </div>
                    """, unsafe_allow_html=True)

                # --- INTEGRAZIONE RGD-ALPHA CREW (NODE.JS BRIDGE) ---
                st.markdown("---")
                st.header("👥 RGD-ALPHA CREW | Client Risk Early Warning")
                
                try:
                    # Bridge simulato con il Backend Node.js
                    col_crew1, col_crew2, col_crew3 = st.columns(3)
                    with col_crew1: st.metric("Clienti Monitorati", "124")
                    with col_crew2: st.metric("Clienti ad Alto Rischio", "8", delta="↑ 2", delta_color="inverse")
                    with col_crew3: st.metric("Churn Rate Previsto", "3.2%")

                    st.subheader("🚨 Alert Recenti: Relazioni Clienti (da MongoDB)")
                    clienti_alert = [
                        {"cliente": "Azienda Meccanica SPA", "rischio": "ROSSO", "motivo": "Drop frequenza d'acquisto -40%"},
                        {"cliente": "Logistica Nord Srl", "rischio": "GIALLO", "motivo": "Peggioramento tono comunicazioni"},
                        {"cliente": "Distribuzione Alimentare", "rischio": "ROSSO", "motivo": "Ritardo pagamenti > 15gg"}
                    ]
                    for c in clienti_alert:
                        c_color = "#e74c3c" if c['rischio'] == "ROSSO" else "#f1c40f"
                        st.markdown(f"""
                            <div class="crew-box" style="border-left-color: {c_color};">
                                <strong>{c['cliente']}</strong> - <span style="color:{c_color}">{c['rischio']}</span><br>
                                <small>{c['motivo']}</small>
                            </div>
                        """, unsafe_allow_html=True)
                except:
                    st.info("⚠️ Collegamento al modulo CREW (Node.js) in corso di inizializzazione...")

# =========================
#   CENTRALE ADMIN
# =========================
elif scelta == "🕵️ Centrale Admin" and is_admin:
    st.title("🕵️ Centrale Admin")
    try:
        df = db.supervisione_admin_metriche_globali()
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
    except: 
        st.info("In attesa di dati dai nodi periferici.")

# =========================
#   ARCHIVIO STORICO
# =========================
elif scelta == "📜 Archivio Storico":
    st.title("📜 Archivio Storico Analisi")
    
    # Se sei Admin vedi tutto, se sei Cliente vedi solo i tuoi dati
    if is_admin:
        st.info("👁️ Visualizzazione Admin: vedi lo storico di tutti i clienti")
        df_log = db.recupera_log_caricamenti_admin()
    else:
        st.info("👁️ Visualizzazione limitata ai file della tua azienda")
        df_log = db.recupera_log_caricamenti_per_utente(user_id)

    if not df_log.empty:
        st.dataframe(df_log, use_container_width=True, hide_index=True)
    else:
        st.warning("📭 Nessun dato trovato in questo archivio.")

        if st.button("🗑️ Svuota tutti i dati"):
            id_utente_corrente = st.session_state.get("user_id", 1)
            db.svuota_dati_azienda(id_utente_corrente)
            st.success("✅ Dati eliminati con successo!")
            st.rerun()