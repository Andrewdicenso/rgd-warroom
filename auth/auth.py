import streamlit as st
import bcrypt
import logging

logger = logging.getLogger("RGD-Alpha.Auth")

def inizializza_sessione():
    """Inizializza le variabili dello stato della sessione di Streamlit se non esistono."""
    if "autenticato" not in st.session_state:
        st.session_state.autenticato = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "email" not in st.session_state:
        st.session_state.email = None
    if "ruolo" not in st.session_state:
        st.session_state.ruolo = None
    if "azienda" not in st.session_state:
        st.session_state.azienda = None

def login_utente(db, email, password):
    try:
        # 1. Recupero Robusto: la funzione get_utente_by_email decripta internamente
        utente = db.get_utente_by_email(email)
        
        if not utente:
            return False # Email non trovata o decriptazione fallita
        
        # 2. Verifica password con Bcrypt (gestendo sia stringhe che byte)
        stored_hash = utente["password_hash"]
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
            
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            st.session_state.autenticato = True
            st.session_state.user_id = utente["id"]
            st.session_state.email = utente["email"]
            st.session_state.ruolo = utente["ruolo"]
            st.session_state.azienda = utente["azienda"]
            return True
        return False
    except Exception as e:
        st.error(f"Errore tecnico login: {e}")
        return False

def logout_utente():
    """Svuota la sessione ed effettua il logout dell'utente."""
    st.session_state.autenticato = False
    st.session_state.user_id = None
    st.session_state.email = None
    st.session_state.ruolo = None
    st.session_state.azienda = None
    st.rerun()

def richiede_ruolo(ruolo_richiesto):
    """
    Verifica se l'utente loggato ha il ruolo richiesto.
    Se non è autorizzato, interrompe l'esecuzione della pagina di Streamlit.
    """
    if not st.session_state.autenticato:
        st.error("Accesso negato. Effettua prima il login.")
        st.stop()
    
    if ruolo_richiesto == "admin" and st.session_state.ruolo != "admin":
        st.error("Area riservata all'amministratore del sistema.")
        st.stop()