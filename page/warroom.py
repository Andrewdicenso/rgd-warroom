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

    # Sezione Login / Registrazione / Recupero
    tab_log, tab_reg, tab_res = st.tabs(["🔒 Login", "🆕 Registrazione", "🔑 Recupero Password"])

    with tab_log:
        st.text_input("Email Aziendale")
        st.text_input("Password", type="password")
        st.button("Accedi al Sistema")

    with tab_reg:
        st.text_input("Email Aziendale")
        st.text_input("Password", type="password")
        st.button("Registrati")

    with tab_res:
        st.text_input("Email Aziendale")
        st.button("Invia Link di Recupero")

    # 🔹 Mostra upload e analisi SOLO se l'utente è autenticato
    if st.session_state.get("autenticato"):
        st.markdown("### 📁 Carica file CSV o Excel")
        uploaded_file = st.file_uploader("Upload", type=["csv", "xlsx", "xls"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
            st.dataframe(df, use_container_width=True)

            analista = AnalistaRischio(db=DatabaseAziendale())
            risultati = analista.calcola_kpi(df)
            st.json(risultati)
            st.write(spiega_kpi(risultati))

            fig = analista.genera_grafico_solidita(df)
            st.pyplot(fig)
            st.write(spiega_grafico("Grafico Solidità Operativa", df.to_dict()))
