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
        st.session_state.ruolo = None   # Corretto: Nessun ruolo finché non si è loggati
    if "azienda" not in st.session_state:
        st.session_state.azienda = None # Corretto: Nessuna azienda finché non si è loggati

def login_utente(db, email, password):
    """
    Verifica le credenziali dell'utente ed effettua il login direttamente su Supabase.
    Ritorna True se il login ha successo, altrimenti False.
    """
    try:
        # 1️⃣ Recupero utente direttamente dal client Supabase bypassando metodi mancanti
        risposta = db.supabase.table("utenti").select("*").eq("email", email).execute()
        
        if not risposta.data or len(risposta.data) == 0:
            logger.warning(f"Tentativo di login fallito: email non trovata ({email}).")
            return False
            
        utente = risposta.data[0]
        hash_salvato = utente.get("password_hash")
        
        # 2️⃣ Verifica password bcrypt safely
        if not hash_salvato or not bcrypt.checkpw(password.encode("utf-8"), hash_salvato.encode("utf-8")):
            logger.warning(f"Tentativo di login fallito per {email}: password errata.")
            return False

        # 3️⃣ Login OK → aggiorno sessione con i dati reali del DB
        st.session_state.autenticato = True
        st.session_state.user_id = utente.get("id")
        st.session_state.email = utente.get("email")
        st.session_state.ruolo = utente.get("ruolo", "user")
        st.session_state.azienda = utente.get("azienda", "Default")

        logger.info(f"Utente {email} autenticato con successo. Ruolo: {st.session_state.ruolo}")
        return True

    except Exception as e:
        logger.error(f"Errore durante la fase di login: {e}")
        return False

def resetta_password_utente(db, email, nuova_password):
    """
    Aggiorna la password dell'utente direttamente su Supabase.
    Ritorna True se l'operazione ha successo, altrimenti False.
    """
    try:
        bytes_p = nuova_password.encode('utf-8')
        salt = bcrypt.gensalt()
        hash_p = bcrypt.hashpw(bytes_p, salt).decode('utf-8')
        
        risultato = db.supabase.table("utenti").update({"password_hash": hash_p}).eq("email", email).execute()
        
        if risultato.data and len(risultato.data) > 0:
            logger.info(f"Password aggiornata con successo per l'utente: {email}")
            return True
        else:
            logger.warning(f"Impossibile aggiornare la password: email {email} non trovata.")
            return False
    except Exception as e:
        logger.error(f"Errore durante il reset della password: {e}")
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
    """Verifica se l'utente loggato ha il ruolo richiesto."""
    if not st.session_state.autenticato:
        st.error("Accesso negato. Effettua prima il login.")
        st.stop()
    
    # Se richiesto admin e l'utente non lo è (o è il superadmin della tabella utenti)
    if ruolo_richiesto == "admin" and st.session_state.ruolo not in ["admin", "superadmin"]:
        st.error("Area riservata all'amministratore del sistema.")
        st.stop()