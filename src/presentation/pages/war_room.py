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
                    # ... resto della logica ...
                else:
                    status.update(label="⚠️ Il file è vuoto o non formattato correttamente.", state="error")
                    st.warning("Verifica che il file CSV/Excel contenga dati validi.")
            except Exception as e:
                status.update(label="❌ Errore durante l'elaborazione", state="error")
                st.error(f"Si è verificato un errore tecnico: {str(e)}")
                    
                    # Calcolo Rischio H(prod) tramite il tuo motore di regressione
                    # Recuperiamo lo storico fittizio per ora (List[float])
                    history = [asset.rischio.value] * 5 
                    analisi_dto = analizzatore.analyze_asset_risk(asset, history)
                    
                    # Mostriamo il consiglio strategico generato dal tuo motore
                    st.info(f"🔍 **{asset.nome}**: {analisi_dto.consiglio}")
                
                st.success(f"Totale Asset analizzati e salvati: {len(assets)}")
            else:
                status.update(label="❌ Errore: Formato non riconosciuto", state="error")
                st.error("Il sistema non è riuscito a identificare il settore del file.")

if __name__ == "__main__":
    show()