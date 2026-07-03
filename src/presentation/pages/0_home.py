"""
Homepage Placeholder - Pagina principale per utenti autenticati.
Nota: In futuro, questa sarà una pagina multi-page di Streamlit.
"""
import streamlit as st
from src.presentation.state import SessionManager


def main():
    """Homepage per utenti autenticati."""
    SessionManager.require_auth()
    
    st.title("🏠 Homepage RGD-Alpha")
    st.subheader(f"Benvenuto, {SessionManager.get_email()}!")
    
    # Placeholder content
    st.info("""
    📊 **Dashboard in Costruzione**
    
    Questa è la homepage dell'applicazione.
    Le sezioni seguenti verranno implementate nella prossima fase:
    
    1. **📈 KPI Dashboard** - Metriche principali
    2. **🚨 Alert Critici** - Asset a rischio
    3. **📁 File Recenti** - Upload dati
    4. **📊 Analisi** - Report personalizzati
    """)


if __name__ == "__main__":
    main()
