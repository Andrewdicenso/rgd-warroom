import streamlit as st
import pandas as pd
from core.database import DatabaseAziendale
from core.analyst import AnalistaRischio
from ai_modules.explainer import spiega_kpi, spiega_grafico

def show_warroom(): # Cambiato da main() a show_warroom()
    st.title("📊 War Room Strategica")
    st.markdown("---")

    if st.session_state.get("autenticato"):
        st.markdown("### 📁 Carica file CSV o Excel")
        uploaded_file = st.file_uploader("Upload", type=["csv", "xlsx", "xls"])
        
        if uploaded_file:
            try:
                # ... (tutta la logica di caricamento e analisi che hai già) ...
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.dataframe(df, use_container_width=True)
                analista = AnalistaRischio(db=DatabaseAziendale())
                risultati = analista.calcola_kpi(df)
                st.json(risultati)
                st.write(spiega_kpi(risultati))
                st.pyplot(analista.genera_grafico_solidita(df))
            except Exception as e:
                st.error(f"Errore: {e}")