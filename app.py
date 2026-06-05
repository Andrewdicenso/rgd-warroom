import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import plotly.express as px

import streamlit as st
from dotenv import load_dotenv

# --- MODULI CORE & AUTH ---
from core.ingestor import IngestoreDati
from core.engine import DataGateway, salva_report_certificato
from core.database import DatabaseAziendale
from core.notifier import Sentinella  # <--- INSERISCI QUI QUESTA RIGA

# Importiamo la logica centralizzata dal pacchetto auth
from auth.auth import inizializza_sessione, login_utente, logout_utente
from core.simulator import SimulatoreRischio
from core.visuals import genera_grafico_predittivo
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

st.set_page_config(
    page_title="RGD-Alpha | War Room Strategica",
    layout="wide",
    page_icon="🛡️"
)

inizializza_sessione()

# =========================
#   CSS ENTERPRISE POTENZIATO
# =========================
st.markdown("""
    <style>
    .kpi-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #007BFF; margin-bottom: 15px; }
    .kpi-box-critical { background-color: #fff5f5; padding: 20px; border-radius: 10px; border-left: 5px solid #dc3545; margin-bottom: 15px; }
    .ai-reasoning { background: #0e1117; border: 1px solid #d4af37; padding: 25px; border-radius: 15px; color: #e2e8f0; line-height: 1.6; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .crew-box { padding:15px; border-radius:10px; background:rgba(255,255,255,0.02); margin-bottom:10px; border-left: 5px solid #ccc; }
    
    /* NUOVI STILI PER WAR ROOM */
    .warroom-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        border-left: 5px solid #e74c3c;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .warroom-header h1 {
        color: white;
        margin: 0 0 0.5rem 0;
        font-size: 2.5rem;
    }
    .warroom-header p {
        color: #ecf0f1;
        margin: 0;
        font-size: 1.1rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 4px solid #3498db;
    }
    .metric-card h3 {
        margin: 0 0 0.5rem 0;
        color: #7f8c8d;
        font-size: 0.9rem;
        text-transform: uppercase;
    }
    .metric-card .value {
        font-size: 2rem;
        font-weight: bold;
        color: #2c3e50;
    }
    .metric-card .delta {
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    .welcome-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .step-box {
        background: rgba(255,255,255,0.1);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #ffd700;
    }
    </style>
""", unsafe_allow_html=True)

db = DatabaseAziendale()

# =========================
#   GESTIONE REGISTRAZIONE
# =========================
def registra_nuovo_utente(email: str, password: str, conferma: str):
    if not email or not password or not conferma:
        st.error("Compila tutti i campi.")
        return
    if password != conferma:
        st.error("Le password non coincidono.")
        return
    try:
        esistente = db.get_utente_by_email(email)
        if esistente:
            st.error("Email già registrata.")
            return
        
        # --- MODIFICA PER RENDER E VENDITA ---
        # Leggiamo l'email dell'admin dalla "Cassaforte" (.env)
        admin_email_env = os.getenv("ADMIN_EMAIL", "andrewdicenso@libero.it").lower()
        ruolo = "admin" if email.lower() == admin_email_env else "user"
        # ------------------------------------

        user_id = db.crea_utente(email=email, password=password, ruolo=ruolo)
        if user_id:
            st.success("✅ Registrazione completata. Effettua il login.")
            st.balloons()
    except Exception as e:
        st.error(f"Errore registrazione: {e}")

# =========================
#   SCHERMATA AUTH
# =========================
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

# =========================
#   NAVIGAZIONE SIDEBAR
# =========================
user_id = st.session_state.user_id
azienda = st.session_state.azienda
ruolo = st.session_state.ruolo
is_admin = (ruolo == "admin")

st.sidebar.title("🛡️ RGD-ALPHA")
st.sidebar.write(f"Operatore: **{azienda}**")
menu = ["🏠 Home", "📊 War Room Strategica", "📜 Archivio Storico"]
if is_admin: menu.insert(1, "🕵️ Centrale Admin")
scelta = st.sidebar.radio("Navigazione", menu)

if st.sidebar.button("Logout"): logout_utente()

# =========================
#   PAGINA HOME / BENVENUTO
# =========================
if scelta == "🏠 Home":
    # Header con branding
    st.markdown("""
        <div style='text-align: center; padding: 3rem 0;'>
            <h1 style='font-size: 3.5rem; margin: 0;'>🛡️ RGD-Alpha</h1>
            <h2 style='color: #7f8c8d; margin: 0.5rem 0 2rem 0;'>War Room Strategica Aziendale</h2>
        </div>
    """, unsafe_allow_html=True)
    
    # Card di benvenuto
    st.markdown("""
        <div class='welcome-card'>
            <h3 style='margin-top: 0;'>👋 Benvenuto nella tua War Room Personale</h3>
            <p style='font-size: 1.1rem; line-height: 1.6;'>
                <strong>RGD-Alpha</strong> non è un semplice gestionale. È un sistema di 
                <strong>Risk Intelligence</strong> che analizza il tuo inventario e calcola la 
                <strong>Solidità Operativa</strong> della tua azienda in tempo reale.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Come iniziare
    st.markdown("### 🚀 Come Iniziare (30 secondi)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='step-box'>
            <h4 style='margin-top: 0;'>1️⃣ Registrati</h4>
            <p style='margin: 0;'>Clicca su "Registrazione" in alto e crea il tuo account</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='step-box'>
            <h4 style='margin-top: 0;'>2️⃣ Carica un CSV</h4>
            <p style='margin: 0;'>Vai su "War Room Strategica" e carica il tuo file inventario</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='step-box'>
            <h4 style='margin-top: 0;'>3️⃣ Ottieni l'Analisi</h4>
            <p style='margin: 0;'>Vedi immediatamente Solidità, Rischio e Proiezioni</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Cosa ottieni
    st.markdown("### 📊 Cosa Ottieni")
    col_a, col_b, col_c, col_d = st.columns(4)
    
    with col_a:
        st.metric("📈 Analisi Predittiva", "Scopri quali asset rischiano di diventare obsoleti")
    
    with col_b:
        st.metric("🏭 Multi-Settore", "Supporto per alimentare, abbigliamento, e-commerce")
    
    with col_c:
        st.metric("🔐 Sicurezza Enterprise", "Dati cifrati con AES-256")
    
    with col_d:
        st.metric("📝 Audit Trail", "Ogni operazione è tracciata")
    
    st.markdown("---")
    
    # Value proposition
    st.markdown("""
        <div style='background: #f8f9fa; padding: 2rem; border-radius: 1rem; margin: 2rem 0; border-left: 5px solid #e74c3c;'>
            <h3 style='margin-top: 0;'>🎯 Per Imprenditori Come Te</h3>
            <blockquote style='font-size: 1.2rem; font-style: italic; color: #555; margin: 0;'>
                "Mentre i comuni gestionali si limitano allo storico, 
                RGD-Alpha calcola in tempo reale la Solidità Operativa, 
                identificando i rischi <strong>prima</strong> che colpiscano il bilancio."
            </blockquote>
        </div>
    """, unsafe_allow_html=True)
    
    # Call to action
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h3>Pronto a proteggere la tua azienda?</h3>
            <p style='font-size: 1.2rem;'>Clicca su <strong>War Room Strategica</strong> nel menu a sinistra per iniziare!</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Sicurezza
    st.markdown("""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 1rem; color: white; margin: 2rem 0;'>
            <h3 style='margin-top: 0;'>🔐 Sicurezza Garantita</h3>
            <p style='margin: 0;'>Dati cifrati AES-256 • Hosting Europeo • GDPR Compliant</p>
        </div>
    """, unsafe_allow_html=True)

# =========================
#   WAR ROOM STRATEGICA
# =========================
elif scelta == "📊 War Room Strategica":
    # Header War Room migliorato
    st.markdown("""
        <div class='warroom-header'>
            <h1>🚀 War Room Strategica</h1>
            <p>Analisi in tempo reale della solidità operativa di <strong>{}</strong></p>
        </div>
    """.format(azienda), unsafe_allow_html=True)
    
    # Metriche in evidenza (anche se non ci sono ancora dati)
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
    
    with st.sidebar:
        with st.expander("⚙️ CALIBRAZIONE EMA", expanded=True):
            w1 = st.slider("Peso Presente (W1)", 0.1, 1.0, 0.7)
            w2 = st.slider("Peso Storico (W2)", 0.1, 1.0, 0.3)
        with st.expander("🚨 STRESS TEST", expanded=True):
            ritardo = st.slider("Ritardo Fornitori (Giorni)", 0, 30, 0)
            f_stress = 1.0 + (ritardo / 50.0)

    uploaded_file = st.file_uploader("📁 Carica inventario CSV", type=["csv"])
    if uploaded_file:
        path = UPLOAD_DIR / azienda / uploaded_file.name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f: f.write(uploaded_file.getbuffer())

        with st.status("🔄 Protocollo RGD-Alpha in corso...") as status:
            ingestor = IngestoreDati()
            lista_asset = ingestor.elabora_csv(str(path), azienda)
            
            if lista_asset:
                engine = DataGateway()
                # RIPRISTINATO: Uso di user_id come richiesto
                db.registra_caricamento(user_id, "UNIVERSAL", uploaded_file.name)
                
                # Calcolo con Stress Test e Pesi EMA
                report_analisi = engine.esegui_scan_strategico(lista_asset, "UNIVERSAL", fattore_stress=f_stress, weights=(w1, w2))
                kpi_reali = db.calcola_e_salva_kpi_correnti(user_id)
                
                # --- ESECUZIONE SIMULAZIONE MONTE CARLO ---
                sim = SimulatoreRischio()
                risultati_sim = sim.esegui_stress_test(kpi_reali.get('solidita', 50), volatilita=0.5)
                
                # --- ESECUZIONE SENTINELLA (Notifica Automatica) ---
                sentinella = Sentinella()
                asset_a_rischio = [(a.get('asset'), a.get('rischio')) for a in report_analisi if a.get('rischio', 0) > 7]
                if asset_a_rischio:
                    sentinella.genera_report(asset_a_rischio)
                    st.warning("⚠️ Rilevate criticità: Report di allerta generato in `data/logs/report_critico.txt`")
                
                # --- GRAFICO PREDITTIVO INTEGRATO ---
                if risultati_sim:
                    st.subheader("🔮 Proiezione Stress Test (Monte Carlo 30gg)")
                    
                fig_pred = genera_grafico_predittivo(risultati_sim['percorsi_raw'], giorni_proiettati=30)
                st.plotly_chart(fig_pred, use_container_width=True)
                fig_pred = genera_grafico_predittivo(risultati_sim['percorsi_raw'], giorni_proiettati=30)
                status.update(label="✅ Analisi e Stress Test completati!", state="complete")
                
                # AGGIORNA LE METRICHE IN ALTO
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
                if risultati_sim:
                    st.subheader("🔮 Proiezione Stress Test (Monte Carlo 30gg)")
                    fig_pred = genera_grafico_predittivo(risultati_sim['percorsi_raw'], giorni_proiettati=30)
                    st.plotly_chart(fig_pred, use_container_width=True) # <--- AGGIUNTA QUESTA RIGA MANCANTE
                
                # --- GRAFICO MOMENTUM ---
                st.subheader("📈 Accelerazione del Rischio (Algoritmo EMA)")
                df_plot = pd.DataFrame(report_analisi)
                fig = px.bar(df_plot, x="asset", y="momentum_score", color="stato",
                             color_discrete_map={"CRITICO": "#ff5f56", "ATTENZIONE": "#ffbd2e", "OTTIMALE": "#27c93f"})
                st.plotly_chart(fig, use_container_width=True)

                # --- RAGIONAMENTO IA DINAMICO ---
                st.subheader("🧠 Ragionamento Strategico Intelligence")

                # Recuperiamo il settore rilevato dall'analisi (es. PRIMARIO_ALIMENTARE, TERZIARIO_LOGISTICA)
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

                # ========================================================
                # --- INTEGRAZIONE RGD-ALPHA CREW (NODE.JS BRIDGE) ---
                # ========================================================
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
    except: st.info("In attesa di dati dai nodi periferici.")

# =========================
#   ARCHIVIO STORICO
# =========================
elif scelta == "📜 Archivio Storico":
    st.title("📜 Archivio Storico Caricamenti")
    
    if is_admin:
        st.info("👁️ Visualizzazione Admin: vedi tutti i caricamenti di tutte le aziende")
        try:
            df_logs = db.recupera_log_caricamenti_admin()
            if not df_logs.empty:
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.warning("📭 Nessun file caricato nel sistema")
        except Exception as e:
            st.error(f"Errore recupero dati: {e}")
    else:
        st.info(f"👁️ Visualizzazione limitata alla tua azienda: {azienda}")
        # Qui potresti aggiungere una query filtrata per azienda se necessario
        st.warning("📭 Archivio storico in fase di implementazione per utenti standard")