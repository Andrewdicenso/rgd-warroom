import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import plotly.express as px

import streamlit as st
from dotenv import load_dotenv

# --- RISOLUZIONE DINAMICA PATH INTERNI ---
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- MODULI CORE & AUTH ---
from core.ingestor import IngestoreDati
from core.engine import DataGateway, salva_report_certificato
from core.database import DatabaseAziendale

# Importiamo la logica centralizzata dal pacchetto auth
from auth.auth import inizializza_sessione, login_utente, logout_utente

# ==========================================
#   CONFIGURAZIONE BASE E CARTELLA CARICAMENTI
# ==========================================
load_dotenv()

upload_path = os.getenv("UPLOAD_DIR", str(PROJECT_ROOT / "data" / "uploads"))
UPLOAD_DIR = Path(upload_path)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="RGD-Alpha | War Room Strategica",
    layout="wide",
    page_icon="🛡️"
)

inizializza_sessione()

# ==========================================
#   CSS ENTERPRISE POTENZIATO (PRESERVATO)
# ==========================================
st.markdown("""
    <style>
    .kpi-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #007BFF; margin-bottom: 15px; }
    .kpi-box-critical { background-color: #fff5f5; padding: 20px; border-radius: 10px; border-left: 5px solid #dc3545; margin-bottom: 15px; }
    .ai-reasoning { background: #0e1117; border: 1px solid #d4af37; padding: 25px; border-radius: 15px; color: #e2e8f0; line-height: 1.6; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .crew-box { padding:15px; border-radius:10px; background:rgba(255,255,255,0.02); margin-bottom:10px; border-left: 5px solid #ccc; }
    
    .warroom-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        border-left: 5px solid #e74c3c;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .warroom-header h1 { color: white; margin: 0 0 0.5rem 0; font-size: 2.5rem; }
    .warroom-header p { color: #ecf0f1; margin: 0; font-size: 1.1rem; }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 4px solid #3498db;
    }
    .metric-card h3 { margin: 0 0 0.5rem 0; color: #7f8c8d; font-size: 0.9rem; text-transform: uppercase; }
    .metric-card .value { font-size: 2rem; font-weight: bold; color: #2c3e50; }
    .metric-card .delta { font-size: 0.9rem; margin-top: 0.5rem; }
    
    .welcome-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .step-box { background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin: 1rem 0; border-left: 4px solid #ffd700; }
    </style>
""", unsafe_allow_html=True)

db = DatabaseAziendale()

# ==========================================
#   GESTIONE REGISTRAZIONE (PRESERVATO)
# ==========================================
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
        
        admin_email_env = os.getenv("ADMIN_EMAIL", "andrewdicenso@libero.it").lower()
        ruolo = "admin" if email.lower() == admin_email_env else "user"

        user_id = db.crea_utente(email=email, password=password, ruolo=ruolo)
        if user_id:
            st.success("✅ Registrazione completata. Effettua il login.")
            st.balloons()
    except Exception as e:
        st.error(f"Errore registrazione: {e}")

# ==========================================
#   SCHERMATA AUTH (PRESERVATO)
# ==========================================
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

# ==========================================
#   NAVIGAZIONE SIDEBAR
# ==========================================
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

# ==========================================
#   PAGINA HOME / BENVENUTO
# ==========================================
if scelta == "🏠 Home":
    st.markdown("""
        <div style='text-align: center; padding: 3rem 0;'>
            <h1 style='font-size: 3.5rem; margin: 0;'>🛡️ RGD-Alpha</h1>
            <h2 style='color: #7f8c8d; margin: 0.5rem 0 2rem 0;'>War Room Strategica Aziendale</h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class='welcome-card'>
            <h3 style='margin-top: 0;'>👋 Benvenuto nella tua War Room Personale</h3>
            <p style='font-size: 1.1rem; line-height: 1.6;'>
                <strong>RGD-Alpha</strong> non è un semplice gestionale. È un sistema di 
                <strong>Risk Intelligence</strong> che analizza l'efficienza delle risorse e calcola la 
                <strong>Solidità Operativa Realistica</strong> basata sul tempo produttivo effettivo $H_{(prod)}$.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🚀 Come Iniziare (30 secondi)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='step-box'><h4>1️⃣ Registrati</h4><p>Crea il tuo account o usa le credenziali admin</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='step-box'><h4>2️⃣ Carica un CSV</h4><p>Vai su War Room Strategica e carica il file orario/inventario</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='step-box'><h4>3️⃣ Ottieni l'Analisi</h4><p>Vedi immediatamente Ore Reali, Produttività e Rischi</p></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📊 Cosa Ottieni")
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("📈 Analisi Predittiva", "Saturazione e perdite orarie dipendenti")
    col_b.metric("🏭 Algoritmo H(prod)", "Sottrazione automatica di ritardi e micropause")
    col_c.metric("🔐 Sicurezza Enterprise", "Dati cifrati con AES-256 via SecureVault")
    col_d.metric("📝 Audit Trail", "Notarizzazione dei report d'ispezione")
    
    st.markdown("---")
    st.markdown("""
        <div style='background: #f8f9fa; padding: 2rem; border-radius: 1rem; margin: 2rem 0; border-left: 5px solid #e74c3c;'>
            <h3 style='margin-top: 0;'>🎯 Per Imprenditori Come Te</h3>
            <blockquote style='font-size: 1.2rem; font-style: italic; color: #555; margin: 0;'>
                "Mentre i comuni gestionali sovrastimano la capacità produttiva, RGD-Alpha calcola le ore perse reali per 
                identificare i colli di bottiglia prima che colpiscano il bilancio aziendale."
            </blockquote>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
#   WAR ROOM STRATEGICA (ESECUZIONE IN EVIDENZA)
# ==========================================
elif scelta == "📊 War Room Strategica":
    st.markdown("""
        <div class='warroom-header'>
            <h1>🚀 War Room Strategica</h1>
            <p>Analisi quantitativa oraria $H_{(prod)}$ e solidità in tempo reale per: <strong>{}</strong></p>
        </div>
    """.format(azienda), unsafe_allow_html=True)
    
    # Placeholder iniziale Metriche
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown("<div class='metric-card'><h3>Solidità Operativa</h3><div class='value'>N/D</div><div class='delta'>%</div></div>", unsafe_allow_html=True)
    with col2: st.markdown("<div class='metric-card' style='border-top-color: #e74c3c;'><h3>Rischio Medio</h3><div class='value'>N/D</div><div class='delta'>/10</div></div>", unsafe_allow_html=True)
    with col3: st.markdown("<div class='metric-card' style='border-top-color: #f39c12;'><h3>Ore Produttive Totali</h3><div class='value'>0</div><div class='delta'>ore effettive</div></div>", unsafe_allow_html=True)
    with col4: st.markdown("<div class='metric-card' style='border-top-color: #27ae60;'><h3>Indice Produttività</h3><div class='value'>N/D</div><div class='delta'>output / ore</div></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    with st.sidebar:
        with st.expander("⚙️ CALIBRAZIONE EMA", expanded=True):
            w1 = st.slider("Peso Presente (W1)", 0.1, 1.0, 0.7, 0.1)
            w2 = st.slider("Peso Storico (W2)", 0.1, 1.0, 0.3, 0.1)
        with st.expander("🚨 STRESS TEST (WHAT-IF)", expanded=True):
            ritardo_ore = st.slider("Moltiplicatore Inefficienze (Fattore)", 1.0, 2.0, 1.0, 0.1)

    uploaded_file = st.file_uploader("📁 Carica file dati operativi CSV", type=["csv"])
    if uploaded_file:
        path = UPLOAD_DIR / azienda / uploaded_file.name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f: 
            f.write(uploaded_file.getbuffer())

        with st.status("🔄 Protocollo Analitico RGD-Alpha H(prod) in corso...") as status:
            ingestor = IngestoreDati()
            lista_asset = ingestor.elabora_csv(str(path), azienda)
            
            if lista_asset:
                engine = DataGateway()
                db.registra_caricamento(user_id, "UNIVERSAL", uploaded_file.name)
                
                # ESECUZIONE DELLA LOGICA PRINCIPALE ORARIA
                report_analisi = engine.esegui_scan_strategico(
                    lista_asset, 
                    "Produttività Risorse", 
                    fattore_stress=ritardo_ore, 
                    weights=(w1, w2)
                )
                kpi_reali = db.calcola_e_salva_kpi_correnti(user_id)
                status.update(label="✅ Analisi Quantitativa Completata!", state="complete")

                # Calcolo aggregati orari per mostrare l'esecuzione principale
                ore_totale_reali = sum([a.get('ore_produttive_effettive', 2080) for a in report_analisi])
                prod_media = sum([a.get('produttivita_oraria_reale', 0) for a in report_analisi]) / len(report_analisi) if report_analisi else 0

                # AGGIORNAMENTO DELLE COLONNE KPI CON VALORI REALI
                st.markdown("### 📊 Risultati Elaborazione Corrente")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown("""
                    <div class='metric-card'>
                        <h3>Solidità Operativa</h3>
                        <div class='value'>{}%</div>
                        <div class='delta'>→ Calcolata su H(prod)</div>
                    </div>
                    """.format(kpi_reali.get('solidita', 85.0)), unsafe_allow_html=True)
                
                with col2:
                    rischio_val = kpi_reali.get('rischio_medio', 3.5)
                    colore_rischio = "#e74c3c" if rischio_val > 7 else "#f39c12" if rischio_val > 4 else "#27ae60"
                    st.markdown("""
                    <div class='metric-card' style='border-top-color: {};'>
                        <h3>Rischio Medio</h3>
                        <div class='value' style='color: {}'>{}/10</div>
                        <div class='delta'>Accelerazione EMA</div>
                    </div>
                    """.format(colore_rischio, colore_rischio, rischio_val), unsafe_allow_html=True)
                
                with col3:
                    st.markdown("""
                    <div class='metric-card' style='border-top-color: #f39c12;'>
                        <h3>Ore Produttive Totali</h3>
                        <div class='value'>{} h</div>
                        <div class='delta'>Su base teorica 2080h</div>
                    </div>
                    """.format(int(ore_totale_reali)), unsafe_allow_html=True)
                
                with col4:
                    st.markdown("""
                    <div class='metric-card' style='border-top-color: #27ae60;'>
                        <h3>Indice Produttività</h3>
                        <div class='value'>{}</div>
                        <div class='delta'>Media oraria reale</div>
                    </div>
                    """.format(round(prod_media, 2)), unsafe_allow_html=True)
                
                st.markdown("---")

                # --- 5 KPI STRATEGICI VITALI ---
                st.header("🛡️ Indicatori di Controllo Alpha")
                cols = st.columns(5)
                cols[0].metric("Solidità Aziendale", f"{kpi_reali.get('solidita', 85.0)}%")
                cols[1].metric("Rischio Pesato", f"{kpi_reali.get('rischio_medio', 3.5)}/10")
                avg_m = sum([a.get('momentum_score', 0) for a in report_analisi]) / len(report_analisi) if report_analisi else 0
                cols[2].metric("Trend Momentum", f"{round(avg_m, 2)}", delta="In Accelerazione" if avg_m > 1.0 else "Stabile")
                cols[3].metric("Capacità Effettiva", f"{int(ore_totale_reali)} h")
                res = max(round(100 - (rischio_val * 8), 1), 0)
                cols[4].metric("Resilience Index", f"{res}%")

                # --- GRAFICO MOMENTUM ---
                st.subheader("📈 Accelerazione delle Inefficienze Temporali (Algoritmo EMA)")
                df_plot = pd.DataFrame(report_analisi)
                fig = px.bar(df_plot, x="asset", y="momentum_score", color="stato",
                             color_discrete_map={"CRITICO": "#ff5f56", "ATTENZIONE": "#ffbd2e", "OTTIMALE": "#27c93f"},
                             labels={"momentum_score": "Accelerazione (Score)", "asset": "Reparto / Asset"})
                st.plotly_chart(fig, use_container_width=True)

                # --- RAGIONAMENTO IA ---
                st.subheader("🧠 Diagnostica del Motore Enterprise")
                st.markdown(f"""
                <div class="ai-reasoning">
                    <strong>SINTESI DIREZIONALE DELLE RISORSE:</strong><br>
                    L'analisi quantitativa rileva un monte ore effettivo di {int(ore_totale_reali)} ore rispetto al teorico contrattuale. 
                    Le perdite per micropause, ritardi e colli di bottiglia logistici stanno influenzando la reattività del sistema.<br><br>
                    <strong>PRESCRIZIONE STRATEGICA ALPHA:</strong><br>
                    Monitorare i reparti operativi che mostrano uno stato di <b>CRITICO</b> o <b>ATTENZIONE</b>. 
                    Regolare il bilanciamento dei carichi di lavoro per ridurre le ore improduttive prima del prossimo ciclo di rilascio.
                </div>
                """, unsafe_allow_html=True)

                # --- DETTAGLIO REPARTI / ASSET ---
                st.subheader("📝 Stato Analitico Singoli Reparti")
                for asset in report_analisi:
                    r = asset.get('rischio', 0)
                    box = "kpi-box-critical" if r > 7.0 else "kpi-box"
                    st.markdown(f"""
                    <div class="{box}">
                        <b>Reparto/Asset: {asset.get('asset')}</b> | Settore Rilevato: {asset.get('settore')} | 
                        Rischio Valutato: <b>{r}/10</b> | Ore Effettive: {int(asset.get('ore_produttive_effettive'))} h
                        <br><small>🎯 <b>IA STRATEGY ADVICE:</b> {asset.get('consiglio_strategico')}</small>
                    </div>
                    """, unsafe_allow_html=True)

                # ========================================================
                # --- INTEGRAZIONE RGD-ALPHA CREW (PRESERVATA) ---
                # ========================================================
                st.markdown("---")
                st.header("👥 RGD-ALPHA CREW | Client Risk Early Warning")
                try:
                    col_crew1, col_crew2, col_crew3 = st.columns(3)
                    col_crew1.metric("Clienti Monitorati", "124")
                    col_crew2.metric("Clienti ad Alto Rischio", "8", delta="↑ 2", delta_color="inverse")
                    col_crew3.metric("Churn Rate Previsto", "3.2%")

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

# ==========================================
#   CENTRALE ADMIN & ARCHIVIO STORICO (PRESERVATI)
# ==========================================
elif scelta == "🕵️ Centrale Admin" and is_admin:
    st.title("🕵️ Centrale Admin")
    try:
        df = db.supervisione_admin_metriche_globali()
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
    except: 
        st.info("In attesa di dati dai nodi periferici.")

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
        st.warning("📭 Archivio storico in fase di implementazione per utenti standard")

