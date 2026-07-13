import streamlit as st
import traceback
from src.presentation.state.session_manager import SessionManager
from src.config.di_container import DIContainer

# 1. Protezione Sicurezza
SessionManager.require_auth()

def show():
    st.title("📊 War Room Strategica")
    st.subheader(f"Asset Intelligence per: {SessionManager.get_azienda()}")

    # Recupero Servizi (Dependency Injection)
    container = DIContainer()
    ingestore = container.get_ingestion_service()
    asset_service = container.get_asset_service()
    analizzatore = container.get_analysis_service()

    uploaded_file = st.file_uploader("Carica Dataset Operativo (Excel/CSV)", type=["xlsx", "csv"])

    if uploaded_file:
        with st.status("🚀 Protocollo Analitico RGD in corso...", expanded=True) as status:
            try:
                # A. Ingestione Dati
                assets = ingestore.process_file(uploaded_file, SessionManager.get_user_id())
                
                if not assets:
                    status.update(label="⚠️ Nessun dato rilevato", state="error")
                    st.warning("Il file caricato non contiene dati validi per l'analisi.")
                    return

                status.update(label="✅ Ingestione Completata. Avvio Analisi...", state="running")
                
                # B. Analisi e Salvataggio
                analizzati_con_successo = 0
                for asset in assets:
                    try:
                        # Calcolo Rischio e AI Insight
                        history = [asset.rischio.value] * 5
                        analisi_dto = analizzatore.analyze_asset_risk(asset, history)
                        
                        # LOGICA PROFESSIONALE: Se il DTO ha 'insight', usa quello. 
                        # Se ha 'consiglio', cambialo qui sotto.
                        insight_text = getattr(analisi_dto, 'insight', getattr(analisi_dto, 'consiglio', "Analisi non disponibile"))
                        
                        with st.expander(f"🔍 Asset: {asset.nome}"):
                            st.write(f"**Stato Rischio:** {asset.rischio.value}")
                            st.info(f"**Consiglio Strategico:** {insight_text}")
                        
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
