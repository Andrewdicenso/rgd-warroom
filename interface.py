import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import os
import sys

# --- RISOLUZIONE DINAMICA DEL PATH PER MODULI CORE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- COLLEGAMENTI INTERNI PRESERVATI E INTEGRATI ---
from core.engine import DataGateway

# --- CONFIGURAZIONE PERCORSI E DATABASE ---
DB_PATH = os.path.join(BASE_DIR, "data", "db", "azienda.db")

st.set_page_config(page_title="RGandja Alpha - Intelligence Dashboard", layout="wide")

st.title("🚀 RGandja Alpha: Business Intelligence Proattiva")
st.sidebar.header("Impostazioni Analisi")

# Inizializzazione Gateway Enterprise Unificato
gateway = DataGateway()
COMPANY_ID = "AZ-TEST-01"

def get_assets():
    """Recupera la lista degli asset/reparti unici dal database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = f"SELECT DISTINCT nome FROM asset_logs WHERE company_id = '{COMPANY_ID}'"
        df = pd.read_sql(query, conn)
        conn.close()
        return df['nome'].tolist()
    except Exception as e:
        st.error(f"Errore tecnico nel database: {e}")
        return []

assets = get_assets()

if not assets:
    st.warning("⚠️ Nessun dato trovato nel database.")
    st.info(f"Esegui prima: 'python main.py' per popolare il database in: {DB_PATH}")
    st.stop()

selected_asset = st.sidebar.selectbox("Seleziona Reparto / Asset da monitorare", assets)

# Parametri What-If avanzati inseriti nella Sidebar per calibrazione EMA
st.sidebar.markdown("---")
st.sidebar.subheader("Calibrazione Protocollo EMA")
w1 = st.sidebar.slider("Peso Rischio Corrente (W1)", 0.1, 1.0, 0.7, 0.1)
w2 = st.sidebar.slider("Peso Rischio Storico (W2)", 0.1, 1.0, 0.3, 0.1)
fattore_stress = st.sidebar.slider("Fattore Stress Test (What-If)", 1.0, 2.0, 1.0, 0.1)

if selected_asset:
    # 1. RECUPERO RECORD STORICO RECENTE
    try:
        conn = sqlite3.connect(DB_PATH)
        # Estraiamo l'ultimo log registrato per recuperare i parametri quantitativi
        query_last = f"""
            SELECT nome, rischio, 
                   COALESCE(ferie, 0) as ferie, COALESCE(festivita, 0) as festivita, 
                   COALESCE(assenze, 0) as assenze, COALESCE(permessi, 0) as permessi, 
                   COALESCE(ritardi, 0) as ritardi, COALESCE(micropause, 0) as micropause, 
                   COALESCE(output_totale, 0) as output_totale
            FROM asset_logs 
            WHERE nome='{selected_asset}' AND company_id='{COMPANY_ID}'
            ORDER BY timestamp DESC LIMIT 1
        """
        df_last = pd.read_sql(query_last, conn)
        conn.close()
    except Exception as e:
        st.error(f"Errore recupero log quantitativi: {e}")
        df_last = pd.DataFrame()

    if df_last.empty:
        st.info(f"ℹ️ L'asset '{selected_asset}' è in fase di inizializzazione. Dati insufficienti.")
    else:
        # Conversione record in dizionario compatibile per engine.py
        asset_data = df_last.to_dict(orient='records')[0]
        
        # Esecuzione Scan Strategico Predittivo tramite il Gateway Enterprise unificato
        risultato_scan = gateway.esegui_scan_strategico(
            lista_asset=[asset_data], 
            contesto="Produttività Risorse", 
            fattore_stress=fattore_stress, 
            weights=(w1, w2)
        )
        
        report = risultato_scan[0]

        # 2. METRICHE PRINCIPALI (KPI ROW)
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Indice Rischio Pesato", f"{report['rischio']}/10")
        col2.metric("Trend Momentum Score", f"{report['momentum_score']}")
        col3.metric("Ore Produttive Reali", f"{int(report['ore_produttive_effettive'])} h")
        col4.metric("Produttività Oraria Reale", f"{report['produttivita_oraria_reale']}")

        st.markdown("---")

        # 3. GRAFICI (DATA VISUALIZATION ROW)
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("📈 Andamento Storico Rischio")
            conn = sqlite3.connect(DB_PATH)
            query_hist = f"SELECT timestamp, rischio FROM asset_logs WHERE nome='{selected_asset}' ORDER BY timestamp DESC LIMIT 25"
            df_hist = pd.read_sql(query_hist, conn).sort_values('timestamp')
            conn.close()
            
            fig_hist = px.line(df_hist, x='timestamp', y='rischio', markers=True, 
                               range_y=[0, 10], title=f"Evoluzione Temporale Rischio: {selected_asset}",
                               color_discrete_sequence=['#00CC96'])
            st.plotly_chart(fig_hist, use_container_width=True)

        with col_right:
            st.subheader("🔮 Indicatore di Allerta Precoce")
            # Adattamento tachimetro (Gauge Chart) sull'indice di rischio pesato corrente
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = report['rischio'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [0, 10], 'tickwidth': 1},
                    'bar': {'color': "#1f77b4"},
                    'steps': [
                        {'range': [0, 4], 'color': "#00CC96"},
                        {'range': [4, 7], 'color': "#FFAA00"},
                        {'range': [7, 10], 'color': "#FF4B4B"}]
                }
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)

        # 4. INTELLIGENCE OUTPUT (STRATEGY ROW)
        st.markdown("---")
        st.subheader("💡 Valutazione Strategica e Diagnostica")
        
        c_strat, c_act = st.columns(2)
        with c_strat:
            st.info(f"**Contesto Rilevato**: Settore Operativo {report['settore']} | Stato: {report['stato']}")
        with c_act:
            st.warning(f"**Azione Consigliata**: {report['consiglio_strategico']}")

        if report['stato'] == "CRITICO" or report['rischio'] > 7.0:
            st.error(f"🚨 ALERT OPERATIVO: Inefficienze critiche rilevate per {selected_asset}. Stato Stress Test: {report['alert']}")