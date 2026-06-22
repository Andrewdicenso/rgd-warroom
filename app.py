import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Importazione dei moduli core RGD-Alpha
from core.database import DatabaseAziendale
from core.engine import DataGateway
from auth.auth import inizializza_sessione, login_utente, logout_utente

# ==============================================================================
# 1. INIZIALIZZAZIONE SISTEMA E SESSIONE
# ==============================================================================
st.set_page_config(page_title="RGD-Alpha War Room", layout="wide", page_icon="🛡️")
inizializza_sessione()

# Connessioni singole e persistenti per evitare sovraccarichi al DB Cloud
if "db" not in st.session_state:
    st.session_state.db = DatabaseAziendale()
if "engine" not in st.session_state:
    st.session_state.engine = DataGateway()

db = st.session_state.db
engine = st.session_state.engine

# ==============================================================================
# 2. SCHERMATA DI LOGIN & RESET (Se l'utente non è autenticato)
# ==============================================================================
if not st.session_state.autenticato:
    st.title("🔒 RGD-Alpha Enterprise — Accesso Protetto")
    
    tab_log, tab_res = st.tabs(["Accedi al Sistema", "Ripristino Credenziali Security"])
    
    with tab_log:
        with st.form("form_login"):
            email_input = st.text_input("Email Aziendale").strip()
            password_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Effettua Login")
            
            if submit_login:
                if email_input and password_input:
                    if login_utente(db, email_input, password_input):
                        st.success("Autenticazione riuscita! Inserimento in corso...")
                        st.rerun()
                    else:
                        st.error("Credenziali errate o utente non autorizzato.")
                else:
                    st.warning("Per favore, compila tutti i campi di accesso.")
                    
    with tab_res:
        with st.form("form_reset"):
            st.subheader("Tracciamento Reset Password")
            email_reset = st.text_input("Inserisci la tua Email di registrazione").strip()
            nuova_pass = st.text_input("Nuova Password Temporanea", type="password")
            submit_reset = st.form_submit_button("Aggiorna Password")
            
            if submit_reset:
                if email_reset and nuova_pass:
                    if db.reset_password_tracciato(email_reset, nuova_pass):
                        st.success("🔒 Reset completato e registrato nei log di sicurezza. Puoi accedere.")
                    else:
                        st.error("Impossibile procedere. Email non trovata nel sistema cloud.")
                else:
                    st.warning("Campi incompleti.")
    st.stop()

# ==============================================================================
# 3. DASHBOARD UTENTE AUTENTICATO (Sidebar Informativa)
# ==============================================================================
st.sidebar.title("🛡️ RGD-Alpha v2.2")
st.sidebar.markdown(f"**Azienda:** `{st.session_state.azienda}`")
st.sidebar.markdown(f"**Utente:** `{st.session_state.email}`")
st.sidebar.markdown(f"**Livello Ruolo:** `{st.session_state.ruolo.upper()}`")

if st.sidebar.button("Log Out Sistema", use_container_width=True):
    logout_utente()

# Menu a Tab Principale
tab_nomi = ["🛡️ War Room & Scan", "📦 Marketing & Giacenze"]
if st.session_state.ruolo == "admin":
    tab_nomi.append("👑 Pannello Controllo Admin")

tabs = st.tabs(tab_nomi)

# ==============================================================================
# TAB 1: WAR ROOM & SCAN STRATEGICO
# ==============================================================================
with tabs[0]:
    st.title("🎯 War Room Strategica")
    
    # --- CONFIGURAZIONE PARAMETRI DI SCAN ---
    with st.expander("⚙️ Configurazione Contesto e Stress Test (What-If)", expanded=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            contesto = st.selectbox(
                "Seleziona il Contesto Operativo:",
                ["Magazzino", "Fornitori", "Performance Vendite", "Produttività Risorse", "EDILE", "FASHION", "UNIVERSAL"]
            )
        with col_c2:
            fattore_stress = st.slider("Fattore di Stress Test (Moltiplicatore Algoritmico)", min_value=1.0, max_value=2.0, value=1.0, step=0.1)

    uploaded_file = st.file_uploader("Carica il tracciato dati (.csv, .xlsx)", type=["csv", "xlsx"])

    if uploaded_file:
        try:
            # Caricamento dinamico dei dati
            if uploaded_file.name.endswith('.csv'):
                df_originale = pd.read_csv(uploaded_file)
            else:
                df_originale = pd.read_excel(uploaded_file)
            
            # Pulizia spazi vuoti sulle intestazioni
            df_pulito = df_originale.copy()
            df_pulito.columns = [str(c).strip() for c in df_pulito.columns]
            
            # Attivazione del motore di Mappatura Universale ERP/CRM
            df_mappato = engine.mappa_colonne_universale(df_pulito)
            
            # Trasformazione in dizionario iniettando l'ID Utente di sessione reale
            lista_asset = []
            for _, row in df_mappato.iterrows():
                asset_dict = row.dropna().to_dict()
                asset_dict["user_id"] = st.session_state.user_id
                lista_asset.append(asset_dict)
            
            # ESECUZIONE SCAN (Formule e protocollo EMA originari intatti)
            with st.spinner("Elaborazione in corso nel motore algoritmico..."):
                report_analisi = engine.esegui_scan_strategico(lista_asset, contesto, fattore_stress=fattore_stress)
            
            # Registrazione caricamento sul Database
            db.registra_caricamento(st.session_state.user_id, contesto, uploaded_file.name)
            
            # Generazione DataFrame finale dell'analisi
            df_report = pd.DataFrame(report_analisi)
            
            # ----------------==================================================
            # LA VERA WAR ROOM: SEZIONE METRICHE COMPLESSIVE ED EVOLUTE
            # ----------------==================================================
            st.markdown("---")
            st.subheader("📊 Stato della War Room Aziendale")
            
            # Conteggi di criticità basati sui risultati reali dell'engine
            critici = len(df_report[df_report["stato"] == "CRITICO"])
            attenzione = len(df_report[df_report["stato"] == "ATTENZIONE"])
            ottimali = len(df_report[df_report["stato"] == "OTTIMALE"])
            rischio_medio_file = round(df_report["rischio"].mean(), 2) if not df_report.empty else 0.0
            
            # Visualizzazione dei Counter della War Room in colonne grafiche
            col_w1, col_w2, col_w3, col_w4 = st.columns(4)
            col_w1.metric("Asset CRITICI (Rischio > 7)", f"🚨 {critici}")
            col_w2.metric("Asset IN ATTENZIONE", f"⚠️ {attenzione}")
            col_w3.metric("Asset OTTIMALI", f"✅ {ottimali}")
            col_w4.metric("Media Rischio Calcolata", f"📊 {rischio_medio_file}")
            
            # Sezione Grafica della War Room: Tabella ad alto impatto visivo
            st.subheader("📋 Output Analisi Dettagliata")
            st.dataframe(df_report, use_container_width=True)
            
            # --- PIANO D'AZIONE OPERATIVO AVANZATO ---
            st.markdown("---")
            st.subheader("🎯 Piano d'Azione Operativo Prioritario")
            st.markdown("_Gli elementi sono ordinati automaticamente dal livello di rischio più alto a quello più basso._")
            
            # Estrazione e ordinamento pulito (evita i KeyError sulle maiuscole)
            df_ordinato = df_report.sort_values(by="rischio", ascending=False)
            
            for _, row in df_ordinato.iterrows():
                r = row.get("rischio", 0.0)
                m = row.get("momentum_score", 0.0)
                nome = row.get("asset", "Asset")
                consiglio = row.get("consiglio_strategico", "")
                
                # Visualizzazione condizionale basata sulle soglie reali
                if r > 7.0:
                    st.error(f"🔴 **{nome}** [Rischio: {r} | Momentum: {m}] — {consiglio}")
                elif r > 5.0:
                    st.warning(f"🟡 **{nome}** [Rischio: {r} | Momentum: {m}] — {consiglio}")
                else:
                    st.success(f"🟢 **{nome}** [Rischio: {r} | Momentum: {m}] — {consiglio}")
                    
        except Exception as e:
            st.error(f"❌ Errore critico di elaborazione: {e}")
            st.info("Verifica la formattazione dei dati interni del file caricato.")
    else:
        st.info("💡 Carica un file valido per popolare la War Room e sbloccare i contatori di rischio.")

# ==============================================================================
# TAB 2: MARKETING & GIACENZE
# ==============================================================================
with tabs[1]:
    st.header("📦 Intelligence Giacenze e Strategie di Recupero")
    st.markdown("Algoritmo di analisi invecchiamento stock per lotti fermi da oltre 30 giorni.")
    
    # Se il file è stato caricato nel primo tab ed esiste il df_mappato in memoria locale
    if uploaded_file and 'df_mappato' in locals():
        if 'timestamp' in df_mappato.columns:
            with st.spinner("Generazione proposte di recupero capitale..."):
                proposte = engine.analizza_giacenze_e_proponi_marketing(df_mappato)
                
            if proposte:
                st.success(f"Rilevate {len(proposte)} opportunità operative di liquidazione stock.")
                df_proposte = pd.DataFrame(proposte)
                st.dataframe(df_proposte, use_container_width=True)
            else:
                st.info("✅ Ottimo stato: nessun elemento risulta bloccato da oltre 30 giorni.")
        else:
            st.warning("⚠️ Funzione disattivata: il file inserito non ha una colonna temporale identificabile come `timestamp`.")
    else:
        st.info("💡 Carica un tracciato dati nel primo Tab per calcolare le giacenze operative.")

# ==============================================================================
# TAB 3: PANNELLO DI CONTROLLO ADMIN (Riservato ed esclusivo)
# ==============================================================================
if st.session_state.ruolo == "admin":
    with tabs[2]:
        st.header("👑 Global System Administrator Dashboard")
        st.markdown("Dati strutturali estratti direttamente dal database relazionale cloud.")
        
        col_kpi1, col_kpi2 = st.columns(2)
        
        with col_kpi1:
            st.subheader("👥 Utenti e Organizzazioni")
            df_utenti = db.supervisione_admin_metriche_globali()
            st.dataframe(df_utenti, use_container_width=True)
            
        with col_kpi2:
            st.subheader("📈 KPI di Carico di Rete Storico")
            # Estrae i dati storici del database per l'utente admin
            kpi = db.calcola_e_salva_kpi_correnti(st.session_state.user_id)
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Solidità Infrastruttura", f"{kpi.get('solidita', 0)} %")
            col_m2.metric("Rischio Medio Storico", f"{kpi.get('rischio_medio', 0)}")
            col_m3.metric("Trend di Sistema", kpi.get('trend', 'N/D'), delta=f"{kpi.get('variazione', 0)}")

        st.markdown("---")
        st.subheader("📜 Log Attività Globale Real-Time (Cloud)")
        df_logs = db.recupera_attivita_globale()
        st.dataframe(df_logs, use_container_width=True)

# ==========================================
#   PAGINA 3: WAR ROOM STRATEGICA (ALLINEATA)
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

    # 2. Esecuzione Pipeline
    if uploaded_file:
        path_raw = UPLOAD_DIR / azienda / uploaded_file.name
        path_raw.parent.mkdir(parents=True, exist_ok=True)
        with open(path_raw, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.status("🔄 Protocollo Analitico RGD-Alpha in corso...", expanded=True) as status:
            # Fase 1: Raffinamento
            status.write("🔍 Fase 1: Identificazione impronta digitale e pulizia...")
            paese_calendar = st.session_state.get("paese_azienda", "IT") 
            refinery = DataRefinery(country=paese_calendar)
            
            refined_result = refinery.refine_file(str(path_raw)) 
            df_pulito = refined_result["data"]
            # Normalizzazione immediata
            df_pulito.columns = [str(c).lower().strip() for c in df_pulito.columns]

            if refined_result.get("anomalies"):
                st.warning(f"⚠️ Rilevate anomalie strutturali: {len(refined_result['anomalies'])} righe corrette.")

            # Fase 2: Mapping
            status.write("🗺️ Fase 2: Smart Mapping delle colonne universali...")
            engine = DataGateway()
            df_mapped = engine.mappa_colonne_universale(df_pulito)
            df_mapped.columns = [str(c).lower().strip() for c in df_mapped.columns]

            # Salvataggio temp
            path_mapped = UPLOAD_DIR / azienda / "temp_mapped.csv"
            df_mapped.to_csv(str(path_mapped), index=False)

            # Fase 3: Ingestione
            status.write("📥 Fase 3: Ingestione e calcolo degli asset strategici...")
            ingestor = IngestoreDati()
            lista_asset = ingestor.elabora_csv(str(path_mapped), azienda)

            if lista_asset:
                db.registra_caricamento(user_id, "WAR_ROOM", uploaded_file.name)
                
                status.write("📈 Fase 4: Calcolo quantitativo predittivo...")
                report_analisi = engine.esegui_scan_strategico(
                    lista_asset,
                    "UNIVERSAL",
                    fattore_stress=f_stress,
                    weights=(0.7, 0.3)
                )
                
                # Sincronizzazione KPI
                db.calcola_e_salva_kpi_correnti(user_id)
                kpi_reali = db.get_kpi_recenti(user_id) if hasattr(db, 'get_kpi_recenti') else {}
                
                # Creazione DataFrame Finale
                df_p = pd.DataFrame(report_analisi)
                df_p.columns = [str(c).lower().strip() for c in df_p.columns]
                
                # Fallback KPI se database vuoto
                if not isinstance(kpi_reali, dict) or not kpi_reali:
                    kpi_reali = {
                        "solidita": 85, 
                        "rischio_medio": round(df_p['risk_factor'].mean() if 'risk_factor' in df_p.columns else 4, 1),
                        "trend": "In Monitoraggio"
                    }
                
                status.update(label="✅ Protocollo RGD-Alpha Completato con Successo!", state="complete")
                
                # --- VISUALIZZAZIONE RISULTATI ---
                # AGGIUNGI QUESTA RIGA QUI SOTTO:
                df_p.columns = [str(c).lower().strip() for c in df_p.columns]

                # Ora i calcoli sotto leggeranno correttamente i dati:
                rischio_val = kpi_reali.get("rischio_medio", 0)
                trend_testo = kpi_reali.get("trend", "Stabile")
                solidita_val = kpi_reali.get("solidita", 0)
                col_ore = [c for c in df_p.columns if 'ore' in c or 'effettive' in c]
                if col_ore:
                    # Prende la prima colonna trovata e somma i valori convertendoli in numeri
                    ore_totale = pd.to_numeric(df_p[col_ore[0]], errors='coerce').sum()
                else:
                    ore_totale = 0
                
                st.markdown("### 📊 Intelligence Report: Analisi Strategica")
                c1, c2, c3, c4 = st.columns(4)
                col_r = "#e74c3c" if rischio_val > 7 else "#f39c12" if rischio_val > 4 else "#27ae60"
                
                c1.markdown(f"<div class='metric-card'><h3>Solidità</h3><div class='value'>{solidita_val}%</div></div>", unsafe_allow_html=True)
                c2.markdown(f"<div class='metric-card' style='border-top-color:{col_r}'><h3>Rischio</h3><div class='value' style='color:{col_r};'>{rischio_val}/10</div></div>", unsafe_allow_html=True)
                c3.markdown(f"<div class='metric-card'><h3>Trend AI</h3><div class='value' style='font-size:1.2rem'>{trend_testo}</div></div>", unsafe_allow_html=True)
                c4.markdown(f"<div class='metric-card'><h3>Ore Analizzate</h3><div class='value'>{int(ore_totale)} h</div></div>", unsafe_allow_html=True)

                with st.expander("📊 Analisi Tecnica: Dettaglio Asset"):
                    st.dataframe(df_p, use_container_width=True, hide_index=True)

                # Diagnostica IA
                st.subheader("🧠 Diagnostica Strategica RGD + IA")
                api_key = os.getenv("GROQ_API_KEY")
                if api_key:
                    from groq import Groq
                    client = Groq(api_key=api_key)
                    media_m = round(df_p['momentum_score'].mean() if 'momentum_score' in df_p.columns else 0, 2)
                    settore_ia = st.selectbox("Seleziona Settore:", ["Marketing", "Logistica", "Produzione", "Retail"])
                        
                    if st.button("🚀 ESEGUI ANALISI STRATEGICA PRESCRITTIVA"):
                        with st.spinner("AI al lavoro..."):
                            try:
                                prompt = f"Analisi per {azienda} ({settore_ia}). Solidità {solidita_val}% | Rischio {rischio_val}/10 | Momentum {media_m}."
                                chat = client.chat.completions.create(
                                    messages=[{"role": "system", "content": "Sei un CSO."}, {"role": "user", "content": prompt}],
                                    model="llama-3.3-70b-versatile"
                                )
                                st.markdown(f"<div class='ai-reasoning'>{chat.choices[0].message.content}</div>", unsafe_allow_html=True)
                            except Exception as e:
                                st.error(f"Errore IA: {e}")
            else:
                # --- MODIFICA DIAGNOSTICA QUI ---
                status.update(label="❌ Errore: Dati non compatibili", state="error")
                st.error(f"L'ingestione di '{uploaded_file.name}' è fallita.")
                # Mostriamo le colonne per capire perché l'inventario non viene letto
                st.info(f"Il sistema ha rilevato queste colonne: {df_pulito.columns.tolist()}")
                st.warning("Assicurati che il file contenga riferimenti a 'data' e 'asset'.")
                st.stop()

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
