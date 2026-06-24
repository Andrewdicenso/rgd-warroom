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
        st.session_state.ruolo = "user"   # FIX
    if "azienda" not in st.session_state:
        st.session_state.azienda = "Sconosciuta"  # FIX

def login_utente(db, email, password):
    """
    Verifica le credenziali dell'utente ed effettua il login.
    Ritorna True se il login ha successo, altrimenti False.
    """
    try:
        # 1️⃣ Recupero utente dal DB
        utente = db.get_utente_by_email(email)
        if not utente:
            logger.warning(f"Tentativo di login fallito: email non trovata ({email}).")
            return False
        
        # 2️⃣ Verifica password bcrypt
        if not bcrypt.checkpw(password.encode("utf-8"), bytes(utente["password_hash"], "utf-8")):
            logger.warning(f"Tentativo di login fallito per {email}: password errata.")
            return False

        # 3️⃣ Login OK → aggiorno sessione
        st.session_state.autenticato = True
        st.session_state.user_id = utente["id"]          # UUID
        st.session_state.email = utente["email"]
        st.session_state.ruolo = utente["ruolo"]
        st.session_state.azienda = utente["azienda"]

        logger.info(f"Utente {email} autenticato con successo. Ruolo: {utente['ruolo']}")
        return True

    except Exception as e:
        logger.error(f"Errore durante la fase di login: {e}")
        return False
