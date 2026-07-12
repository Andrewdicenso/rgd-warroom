import streamlit as st
from src.presentation.state.session_manager import SessionManager
from src.config.di_container import DIContainer

# 1. Protezione Sicurezza: Blocca l'accesso se non autenticato
SessionManager.require_auth()

def show():
    st.title("📊 War Room Strategica")
    st.subheader(f"Asset Intelligence per: {SessionManager.get_azienda()}")

    # Recupero Servizi dal Container
    container = DIContainer()
    ingestore = container.get_ingestion_service()
    # Usiamo AssetService invece del repository direttamente
    asset_service = container.get_asset_service()
    analizzatore = container.get_analysis_service()

    # --- ZONA CARICAMENTO ---
    uploaded_file = st.file_uploader("Carica Dataset Operativo (Excel/CSV)", type=["xlsx", "csv"])

    if uploaded_file:
        with st.status("🚀 Protocollo Analitico RGD in corso...", expanded=True) as status:
            # A. Ingestione Dati
            assets = ingestore.process_file(uploaded_file, SessionManager.get_user_id())
            
            # File: /opt/render/project/src/src/presentation/pages/war_room.py
# Sostituisci la sezione "A. Ingestione Dati" (intorno alla riga 25) con questa:

    if uploaded_file:
        with st.status("🚀 Protocollo Analitico RGD in corso...", expanded=True) as status:
                    try:
                        # A. Ingestione Dati
                        assets = ingestore.process_file(uploaded_file, SessionManager.get_user_id())
                    
                        if assets:
                            status.update(label="✅ Ingestione Completata. Avvio Analisi...", state="complete")
                            
                            # B. Analisi per ogni asset trovato
                            for asset in assets:
                                # Calcolo Rischio H(prod)
                                history = [asset.rischio.value] * 5
                                analisi_dto = analizzatore.analyze_asset_risk(asset, history)
                                
                                # Mostriamo il consiglio strategico
                                st.info(f"🔍 **{asset.nome}**: {analisi_dto.consiglio}")
                            
                            st.success(f"Totale Asset analizzati e salvati: {len(assets)}")
                        else:
                            status.update(label="⚠️ Nessun dato rilevato", state="error")
                            st.warning("Il file caricato sembra vuoto o non formattato correttamente.")

                    except Exception as e:
                        status.update(label="❌ Errore durante l'elaborazione", state="error")
                        st.error(f"Si è verificato un errore tecnico: {str(e)}")

# Assicurati che queste ultime righe siano all'inizio della colonna (senza spazi)
if __name__ == "__main__":
    show()