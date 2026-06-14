import os
import sys
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# --- 1. OTTIMIZZAZIONE ENVIRONMENT (Singola esecuzione) ---
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

load_dotenv()

# Importazioni raggruppate
from core.ingestor import IngestoreDati
from core.engine import DataGateway
from core.database import DatabaseAziendale
from auth.auth import inizializza_sessione, login_utente, logout_utente
from core.experimental_modules.reparti_engine import mostra_interfaccia_4_aree

# --- 2. CONFIGURAZIONE UI ---
st.set_page_config(page_title="War Room Strategica", layout="wide")

def apply_custom_css():
    """Centralizza lo stile per evitare ripetizioni nel DOM"""
    css_path = PROJECT_ROOT / "style.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.info("File style.css non trovato, carico default.")

apply_custom_css()

# --- 3. BACKEND & SESSIONE ---
inizializza_sessione()
db = DatabaseAziendale()

# --- 4. GESTIONE ACCESSO ---
if not st.session_state.get('autenticato', False):
    # Logica login... (come nel tuo codice)
    st.stop()

# --- 5. LOGICA APPLICATIVA (BACKEND) ---
# Usa st.sidebar per la navigazione
scelta = st.sidebar.radio("Navigazione", ["🏠 Home", "📊 War Room Strategica"])

if scelta == "📊 War Room Strategica":
    # Esempio di pulizia backend
    struttura = mostra_interfaccia_4_aree()
    reparto = struttura['Dipartimento']
    
    uploaded_file = st.file_uploader(f"Carica dati per {reparto}", type=["csv", "xlsx"])
    
    if uploaded_file:
        # Backend: Invece di /tmp/, usa il buffer direttamente
        with st.status("Elaborazione in corso...") as status:
            ingestor = IngestoreDati()
            # Passa il buffer o salva in una cartella di progetto definita
            # lista_asset = ingestor.elabora_file(uploaded_file, st.session_state.azienda)
            status.update(label="Analisi completata!", state="complete")

# ... (Parti iniziali di import e config rimangono uguali)

elif scelta == "📊 War Room Strategica":
    st.markdown(f"<div class='warroom-header'><h1>🚀 War Room Strategica</h1><p>Analisi della solidità di <strong>{azienda}</strong></p></div>", unsafe_allow_html=True)
    
    # 1. PARAMETRI ALGORITMICI (I "Muscoli" del calcolo)
    st.sidebar.subheader("⚙️ Parametri Motore RGD-Alpha")
    f_stress = st.sidebar.slider("Giorni di Stress Test (Monte Carlo)", 7, 90, 30)
    w1 = st.sidebar.slider("Peso Algoritmo EMA (Esponeziale)", 0.0, 1.0, 0.7)
    w2 = 1.0 - w1
    
    # 2. SELEZIONE REPARTO
    struttura = mostra_interfaccia_4_aree()
    reparto_scelto = struttura['Dipartimento']
    
    st.subheader(f"📂 Analisi di Rischio Alpha: {reparto_scelto}")
    uploaded_file = st.file_uploader("Trascina qui il dataset", type=["csv", "xlsx"])
    
    if uploaded_file:
        # Salvataggio temporaneo per l'ingestore
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        with st.status("🔄 Esecuzione Cervelli di Calcolo...") as status:
            try:
                # --- BACKEND STEP 1: Ingestione ---
                ingestor = IngestoreDati()
                lista_asset = ingestor.elabora_file(temp_path, azienda)
                
                if lista_asset:
                    # --- BACKEND STEP 2: Engine di Calcolo Strategico ---
                    engine = DataGateway()
                    # QUI IL FIX: Passiamo correttamente i parametri che causavano l'errore
                    report_analisi = engine.esegui_scan_strategico(
                        lista_asset, 
                        reparto_scelto, # Passato correttamente come area_focus
                        fattore_stress=f_stress, 
                        weights=(w1, w2)
                    )
                    
                    # --- BACKEND STEP 3: Simulatore Monte Carlo ---
                    simulatore = SimulatoreRischio()
                    risultati_sim = simulatore.esegui_stress_test(lista_asset, giorni=f_stress)
                    
                    status.update(label="✅ Calcoli Completati", state="complete")

                    # --- VISUALIZZAZIONE RISULTATI ---
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Solidità Strutturale", f"{report_analisi.get('score', 0)}%")
                    with col_m2:
                        prob_crisi = risultati_sim.get('probabilita_crisi', 0)
                        st.metric("Probabilità Crisi (30gg)", f"{prob_crisi}%", delta=f"{prob_crisi}%", delta_color="inverse")
                    
                    # Grafico Predittivo (Il cervello visivo)
                    fig = genera_grafico_predittivo(risultati_sim['percorsi_raw'], f_stress)
                    st.plotly_chart(fig, use_container_width=True)
                    
            except Exception as e:
                st.error(f"Errore durante l'elaborazione dei cervelli: {e}")
            finally:
                if os.path.exists(temp_path): os.remove(temp_path)