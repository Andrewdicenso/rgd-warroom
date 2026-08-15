import streamlit as st
import traceback
from src.presentation.state.session_manager import SessionManager
from src.config.di_container import DIContainer

# 1. Protezione Sicurezza
SessionManager.require_auth()

def show():
    # --- RESET CSS ---
    # Forza la visibilità di tutti gli elementi UI, annullando eventuali stili restrittivi
    st.markdown(
        """
        <style>
            /* Forza il colore del testo e del bordo dell'uploader */
            .stFileUploader label p {
                color: #31333F !important; /* Grigio scuro/Nero */
            }
            section[data-testid="stFileUploader"] {
                border: 1px solid #ff4b4b !important; /* Bordo rosso per individuarlo subito */
                padding: 10px;
                border-radius: 5px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("📊 War Room Strategica")
    st.subheader(f"Asset Intelligence per: {SessionManager.get_azienda()}")
    
    st.divider()

    # --- SEZIONE CARICAMENTO ---
    st.markdown("### 📁 Caricamento Dati Operativi")
    uploaded_file = st.file_uploader(
        "Seleziona un file Excel o CSV per avviare il protocollo di analisi", 
        type=["xlsx", "csv"],
        help="Il sistema accetta file esportati dai principali ERP (SAP, Oracle, AS400)"
    )
    
    st.divider()

    if uploaded_file:
        with st.status("🚀 Protocollo Analitico RGD in corso...", expanded=True) as status:
            try:
                # Recupero Servizi (Dependency Injection)
                container = DIContainer()
                ingestore = container.get_ingestion_service()
                analizzatore = container.get_analysis_service()

                # A. Ingestione Dati
                assets = ingestore.process_file(uploaded_file, SessionManager.get_user_id())
                
                if not assets:
                    status.update(label="⚠️ Nessun dato rilevato", state="error")
                    st.warning("Il file caricato non contiene dati validi per l'analisi.")
                    return

                status.update(label="✅ Ingestione Completata. Avvio Analisi...", state="running")
                
                # B. Analisi e Visualizzazione Risultati
                analizzati_con_successo = 0
                for asset in assets:
                    try:
                        # Calcolo Rischio e AI Insight (History fittizia per il calcolo)
                        history = [asset.rischio.value] * 5
                        analisi_dto = analizzatore.analyze_asset_risk(asset, history)
                        
                        # Recupero insight in modo sicuro (supporta diversi nomi attributo nel DTO)
                        insight_text = getattr(analisi_dto, 'insight', getattr(analisi_dto, 'consiglio', "Analisi non disponibile"))
                        
                        with st.expander(f"🔍 Analisi Asset: {asset.nome}"):
                            col_info, col_risk = st.columns([2, 1])
                            with col_info:
                                st.write(f"**ID Azienda:** `{asset.azienda_id}`")
                                st.info(f"**Consiglio Strategico:**\n{insight_text}")
                            with col_risk:
                                st.metric("Rischio Attuale", f"{asset.rischio.value}/10")
                        
                        analizzati_con_successo += 1
                    except Exception as e:
                        st.error(f"Errore nell'analisi dell'asset {getattr(asset, 'nome', 'Sconosciuto')}: {str(e)}")

                # C. Finalizzazione
                status.update(label="✅ Analisi Completata", state="complete")
                st.success(f"Protocollo terminato: {analizzati_con_successo}/{len(assets)} asset elaborati con successo.")

            except Exception as e:
                status.update(label="❌ Errore Critico di Sistema", state="error")
                st.error(f"### Dettaglio Tecnico: {str(e)}")
                with st.expander("🔍 Analisi del Crash (Debug)"):
                    st.code(traceback.format_exc(), language="python")

if __name__ == "__main__":
    show()