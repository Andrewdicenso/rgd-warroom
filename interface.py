import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import psycopg2
import os
import sys

# --- CONFIGURAZIONE DATABASE POSTGRESQL (Sorgente Unica) ---
DB_URL = "postgresql://postgres.itqjupaxatvsnwbtbeiv:RGD-Alpha-2025@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"

def get_connection():
    return psycopg2.connect(DB_URL)

# --- RISOLUZIONE PATH E IMPORT CORE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.engine import DataGateway

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="RGandja Alpha - Intelligence Dashboard", layout="wide")

# Inizializzazione Gateway
gateway = DataGateway()
COMPANY_ID = "AZ-TEST-01" # Puoi renderlo dinamico basato sul login

# --- SIDEBAR: NAVIGAZIONE E CENTRALE ADMIN ---
st.sidebar.title("🛡️ Centro Comando")
admin_mode = st.sidebar.checkbox("🕵️ Attiva Centrale Admin")

if admin_mode:
    st.header("🕵️ Centrale Admin - Gestione Clienti VIP")
    try:
        conn = get_connection()
        df_utenti = pd.read_sql("SELECT id, email, is_active, role FROM users ORDER BY id DESC", conn)
        
        st.write("Abilita i nuovi account registrati (es. tua sorella) selezionando 'is_active':")
        edited_df = st.data_editor(
            df_utenti,
            column_config={
                "is_active": st.column_config.CheckboxColumn("ATTIVA", default=False),
                "role": st.column_config.SelectboxColumn("RUOLO", options=["user", "vip", "admin"])
            },
            disabled=["id", "email"],
            hide_index=True,
            key="admin_table"
        )
        
        if st.button("SALVA ATTIVAZIONI"):
            cur = conn.cursor()
            for _, row in edited_df.iterrows():
                cur.execute(
                    "UPDATE users SET is_active = %s, role = %s WHERE id = %s",
                    (row['is_active'], row['role'], row['id'])
                )
            conn.commit()
            cur.close()
            st.success("✅ Database sincronizzato. I clienti ora possono operare.")
            st.balloons()
        conn.close()
    except Exception as e:
        st.error(f"Errore connessione Admin: {e}")
    st.markdown("---")

# --- LOGICA DASHBOARD PRINCIPALE ---
st.title("🚀 RGandja Alpha: Business Intelligence Proattiva")

def get_assets():
    try:
        conn = get_connection()
        query = f"SELECT DISTINCT nome FROM asset_logs WHERE company_id = '{COMPANY_ID}'"
        df = pd.read_sql(query, conn)
        conn.close()
        return df['nome'].tolist()
    except:
        return []

assets = get_assets()

if not assets:
    st.info("👋 Benvenuto. Inizia caricando dei dati nella sezione War Room per popolare la Dashboard.")
    st.stop()

selected_asset = st.sidebar.selectbox("Seleziona Reparto / Asset", assets)

# Parametri What-If Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Calibrazione Protocollo EMA")
w1 = st.sidebar.slider("Peso Rischio Corrente (W1)", 0.1, 1.0, 0.7, 0.1)
w2 = st.sidebar.slider("Peso Rischio Storico (W2)", 0.1, 1.0, 0.3, 0.1)
fattore_stress = st.sidebar.slider("Fattore Stress Test", 1.0, 2.0, 1.0, 0.1)

if selected_asset:
    try:
        conn = get_connection()
        query_last = f"""
            SELECT * FROM asset_logs 
            WHERE nome='{selected_asset}' AND company_id='{COMPANY_ID}'
            ORDER BY timestamp DESC LIMIT 1
        """
        df_last = pd.read_sql(query_last, conn)
        conn.close()
        
        if not df_last.empty:
            asset_data = df_last.to_dict(orient='records')[0]
            
            # Motore Predittivo
            risultato_scan = gateway.esegui_scan_strategico(
                lista_asset=[asset_data], 
                contesto="Produttività Risorse", 
                fattore_stress=fattore_stress, 
                weights=(w1, w2)
            )
            report = risultato_scan[0]

            # Visualizzazione KPI
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Indice Rischio", f"{report['rischio']}/10")
            c2.metric("Momentum Score", report['momentum_score'])
            c3.metric("Ore Produttive", f"{int(report['ore_produttive_effettive'])}h")
            c4.metric("Produttività Oraria", report['produttivita_oraria_reale'])

            # Grafici
            col_l, col_r = st.columns(2)
            with col_l:
                conn = get_connection()
                df_h = pd.read_sql(f"SELECT timestamp, rischio FROM asset_logs WHERE nome='{selected_asset}' LIMIT 25", conn)
                conn.close()
                st.plotly_chart(px.line(df_h, x='timestamp', y='rischio', title="Trend Rischio"), use_container_width=True)
            
            with col_r:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number", value=report['rischio'],
                    gauge={'axis': {'range': [0, 10]}, 'bar': {'color': "darkblue"},
                           'steps': [{'range': [0, 5], 'color': "green"}, {'range': [5, 10], 'color': "red"}]}))
                st.plotly_chart(fig_gauge, use_container_width=True)

            st.info(f"**Azione Consigliata**: {report['consiglio_strategico']}")
    except Exception as e:
        st.error(f"Errore Analisi: {e}")