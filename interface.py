import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import psycopg2
import os
import sys
from datetime import datetime

# --- CONFIGURAZIONE DATABASE ---
DB_URL = "postgresql://postgres.itqjupaxatvsnwbtbeiv:RGD-Alpha-2025@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"

def get_connection():
    return psycopg2.connect(DB_URL)

# --- IMPORT MODULI CORE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.engine import DataGateway
from ingestor import IngestoreDati

st.set_page_config(page_title="RGandja Alpha - Intelligence Dashboard", layout="wide")
gateway = DataGateway()
ingestore = IngestoreDati()
COMPANY_ID = "AZ-TEST-01"

# --- SIDEBAR ---
st.sidebar.title("🛡️ Centro Comando")
admin_mode = st.sidebar.checkbox("🕵️ Centrale Admin")
war_room_mode = st.sidebar.checkbox("📊 War Room (Caricamento)")

# 1. LOGICA CENTRALE ADMIN (Gestione Verde/Attivi)
if admin_mode:
    st.header("🕵️ Centrale Admin - Gestione Accessi")
    try:
        conn = get_connection()
        df_utenti = pd.read_sql("SELECT id, email, is_active, role FROM users ORDER BY id DESC", conn)
        def style_attivi(row):
            return ['background-color: #d4edda' if row.is_active else '' for _ in row]
        st.write("Stato Attuale (Verde = Attivo):")
        st.dataframe(df_utenti.style.apply(style_attivi, axis=1), hide_index=True)
        
        edited_df = st.data_editor(df_utenti, column_config={
            "is_active": st.column_config.CheckboxColumn("ATTIVA"),
            "role": st.column_config.SelectboxColumn("RUOLO", options=["user", "vip", "admin"])
        }, disabled=["id", "email"], hide_index=True)

        if st.button("SALVA ATTIVAZIONI"):
            cur = conn.cursor()
            for _, row in edited_df.iterrows():
                cur.execute("UPDATE users SET is_active = %s, role = %s WHERE id = %s", (row['is_active'], row['role'], row['id']))
            conn.commit()
            st.success("✅ Database sincronizzato.")
            st.rerun()
        conn.close()
    except Exception as e:
        st.error(f"Errore Admin: {e}")
    st.markdown("---")

# 2. LOGICA WAR ROOM (I 4 PILASTRI STRATEGICI)
if war_room_mode:
    st.header("📊 War Room: Ingestione Documentale VIP")
    
    # --- SELEZIONE DESTINAZIONE (I 4 PILASTRI) ---
    st.subheader("🏢 Seleziona Destinazione Documento")
    pilastri = [
        "💼 Amministrazione & Controllo",
        "⚙️ Operativa & Logistica",
        "📣 Commerciale & Marketing",
        "👥 Risorse Umane & Servizi"
    ]
    destinazione = st.radio("Il file verrà elaborato per il pilastro:", options=pilastri, horizontal=True)

    file_caricato = st.file_uploader("Trascina qui il documento", type=None)

    if file_caricato:
        risultato = ingestore.elabora_file(file_caricato, COMPANY_ID)
        if risultato['status'] == 'success':
            lista_asset = risultato.get('data')
            if lista_asset:
                conn = get_connection()
                cur = conn.cursor()
                for asset in lista_asset:
                    cur.execute("""
                        INSERT INTO asset_logs (nome, rischio, company_id, timestamp, eliminato, pilastro) 
                        VALUES (%s, %s, %s, %s, False, %s)
                    """, (asset['nome'], asset['rischio'], COMPANY_ID, datetime.now(), destinazione))
                conn.commit()
                conn.close()
                st.success(f"✅ File salvato con successo nel pilastro: {destinazione}")
                st.rerun() 
        elif risultato['status'] == 'warning':
            st.warning(f"⚠️ {risultato['message']}")
        elif risultato['status'] == 'error':
            st.error(f"❌ {risultato['message']}")
    st.markdown("---")

# 3. LOGICA DASHBOARD PRINCIPALE
st.title("🚀 RGandja Alpha: Business Intelligence Proattiva")

def get_assets():
    try:
        conn = get_connection()
        df = pd.read_sql(f"SELECT DISTINCT nome FROM asset_logs WHERE company_id = '{COMPANY_ID}' AND eliminato = False", conn)
        conn.close()
        return df['nome'].tolist()
    except: return []

assets = get_assets()
if not assets:
    st.info("👋 Benvenuto. Usa la War Room per caricare i primi dati.")
    st.stop()

selected_asset = st.sidebar.selectbox("Seleziona Reparto / Asset", assets)

# Parametri Sidebar (EMA/Stress)
st.sidebar.markdown("---")
st.sidebar.subheader("Calibrazione Protocollo EMA")
w1 = st.sidebar.slider("Peso Presente (W1)", 0.1, 1.0, 0.7)
w2 = st.sidebar.slider("Peso Storico (W2)", 0.1, 1.0, 0.3)
fattore_stress = st.sidebar.slider("Fattore Stress", 1.0, 2.0, 1.0)

if selected_asset:
    try:
        conn = get_connection()
        df_last = pd.read_sql(f"SELECT * FROM asset_logs WHERE nome='{selected_asset}' AND company_id='{COMPANY_ID}' AND eliminato = False ORDER BY timestamp DESC LIMIT 1", conn)
        conn.close()
        
        if not df_last.empty:
            asset_data = df_last.to_dict(orient='records')[0]
            report = gateway.esegui_scan_strategico(lista_asset=[asset_data], contesto="Produttività", fattore_stress=fattore_stress, weights=(w1, w2))[0]

            # KPI e Grafici
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Indice Rischio", f"{report['rischio']}/10")
            c2.metric("Momentum", report['momentum_score'])
            c3.metric("Ore Produttive", f"{int(report['ore_produttive_effettive'])}h")
            c4.metric("Produttività Oraria", report['produttivita_oraria_reale'])

            col_l, col_r = st.columns(2)
            with col_l:
                conn = get_connection()
                df_h = pd.read_sql(f"SELECT timestamp, rischio FROM asset_logs WHERE nome='{selected_asset}' AND eliminato = False LIMIT 25", conn)
                conn.close()
                st.plotly_chart(px.line(df_h, x='timestamp', y='rischio', title="Trend Rischio"), use_container_width=True)
            with col_r:
                st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=report['rischio'], gauge={'axis': {'range': [0, 10]}, 'steps': [{'range': [0, 5], 'color': "green"}, {'range': [5, 10], 'color': "red"}]})), use_container_width=True)
            st.info(f"**Azione Consigliata**: {report['consiglio_strategico']}")
    except Exception as e:
        st.error(f"Errore Analisi: {e}")