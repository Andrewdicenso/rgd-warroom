import streamlit as st
import pandas as pd
from core.database import DatabaseAziendale
from core.analyst import AnalistaRischio
from ai_modules.explainer import spiega_kpi, spiega_grafico

def main():
    st.set_page_config(page_title="War Room Strategica", layout="wide")

    # Sidebar
    with st.sidebar:
        st.image("assets/logo.webp", width=180)
        st.markdown("### ⚙️ Menu Operativo")
        st.button("🏠 Home")
        st.button("📊 Analisi Strategica")
        st.button("📈 Previsioni 30/60/90 giorni")
        st.button("⚠️ Rischi & Allarmi")

    st.title("📊 War Room Strategica")
    st.markdown("---")

    # 🔹 Mostra upload e analisi SOLO se l'utente è autenticato
    # Nota: dovrai implementare la logica di login per impostare questa variabile a True
    if st.session_state.get("autenticato"):
        st.markdown("### 📁 Carica file CSV o Excel")
        uploaded_file = st.file_uploader("Upload", type=["csv", "xlsx", "xls"])
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.dataframe(df, use_container_width=True)

                analista = AnalistaRischio(db=DatabaseAziendale())
                risultati = analista.calcola_kpi(df)
                st.json(risultati)
                st.write(spiega_kpi(risultati))

                fig = analista.genera_grafico_solidita(df)
                st.pyplot(fig)
                st.write(spiega_grafico("Grafico Solidità Operativa", df.to_dict()))
            except Exception as e:
                st.error(f"Errore durante l'elaborazione del file: {e}")

if __name__ == "__main__":
    main()