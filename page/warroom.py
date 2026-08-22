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
        # Aggiunta key univoca per il login
        st.text_input("Email Aziendale", key="login_email")
        st.text_input("Password", type="password", key="login_password")
        st.button("Accedi al Sistema", key="btn_login")

    with tab_reg:
        # Aggiunta key univoca per la registrazione
        st.text_input("Email Aziendale", key="reg_email")
        st.text_input("Password", type="password", key="reg_password")
        st.button("Registrati", key="btn_reg")

    with tab_res:
        # Aggiunta key univoca per il recupero
        st.text_input("Email Aziendale", key="reset_email")
        st.button("Invia Link di Recupero", key="btn_reset")

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