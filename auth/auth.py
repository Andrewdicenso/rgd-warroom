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
        st.session_state.ruolo = "user"
    if "azienda" not in st.session_state:
        st.session_state.azienda = "Sconosciuta"

def login_utente(db, email, password):
    """Verifica le credenziali e assegna il ruolo Admin esclusivamente a te."""
    try:
        # 1️⃣ Recupero utente dal DB (usando la funzione get_utente_by_email corretta)
        utente = db.get_utente_by_email(email)
        if not utente:
            logger.warning(f"Tentativo di login fallito: email non trovata ({email}).")
            return False
        
        # 2️⃣ Verifica password bcrypt
        if not bcrypt.checkpw(password.encode("utf-8"), bytes(utente["password_hash"], "utf-8")):
            logger.warning(f"Tentativo di login fallito per {email}: password errata.")
            return False

        # 3️⃣ Login OK → Blindatura Ruolo Admin
        st.session_state.autenticato = True
        st.session_state.user_id = utente["id"]
        st.session_state.email = utente["email"]
        st.session_state.azienda = utente["azienda"]

        # FORZA ADMIN SOLO PER LA TUA EMAIL
        if utente["email"].lower() == "andrewdicenso@libero.it":
            st.session_state.ruolo = "admin"
        else:
            st.session_state.ruolo = "user"

        logger.info(f"Utente {email} autenticato. Admin: {st.session_state.ruolo == 'admin'}")
        return True

    except Exception as e:
        logger.error(f"Errore durante la fase di login: {e}")
        return False

def logout_utente():
    """Svuota la sessione ed effettua il logout."""
    st.session_state.autenticato = False
    st.session_state.user_id = None
    st.session_state.email = None
    st.session_state.ruolo = "user"
    st.session_state.azienda = "Sconosciuta"
    st.rerun()

def richiede_ruolo(ruolo_richiesto):
    """Verifica autorizzazioni."""
    if not st.session_state.autenticato:
        st.error("Accesso negato. Effettua prima il login.")
        st.stop()
    
    if ruolo_richiesto == "admin" and st.session_state.ruolo != "admin":
        st.error("Area riservata all'amministratore del sistema.")
        st.stop()
