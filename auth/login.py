import streamlit as st

from auth.auth import inizializza_sessione, login_utente
from core.database import DatabaseAziendale

# Inizializza la sessione Streamlit
inizializza_sessione()

# Configurazione pagina
st.set_page_config(page_title="Login | RGD-Alpha War Room", layout="centered")

st.title("🔐 Accesso Riservato")
st.write("Inserisci le tue credenziali per accedere alla War Room.")

# Inizializzazione database
db = DatabaseAziendale()

# Form di login
with st.form("login_form"):
    email = st.text_input("Email", placeholder="nome@azienda.com")
    password = st.text_input("Password", type="password")
    submit = st.form_submit_button("Accedi")

if submit:
    if login_utente(db, email, password):
        st.success("Accesso effettuato con successo.")
        st.rerun()
    else:
        st.error("Credenziali non valide. Riprova.")

# Se già autenticato → redirect automatico
if st.session_state.autenticato:
    st.info(f"Benvenuto {st.session_state.email}. Reindirizzamento in corso…")
    st.rerun()
