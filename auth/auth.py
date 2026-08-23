import streamlit as st
import bcrypt
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings

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
        utente = db.get_utente_by_email(email)
        if not utente:
            logger.warning(f"Tentativo di login fallito: email non trovata ({email}).")
            return False

        if not bcrypt.checkpw(
            password.encode("utf-8"), bytes(utente["password_hash"], "utf-8")
        ):
            logger.warning(f"Tentativo di login fallito per {email}: password errata.")
            return False

        st.session_state.autenticato = True
        st.session_state.user_id = utente["id"]
        st.session_state.email = utente["email"]
        st.session_state.azienda = utente["azienda"]

        if utente["email"].lower() == "andrewdicenso@libero.it":
            st.session_state.ruolo = "admin"
        else:
            st.session_state.ruolo = "user"

        logger.info(
            f"Utente {email} autenticato. Admin: {st.session_state.ruolo == 'admin'}"
        )
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


def invia_email_recupero(email_destinatario, link_reset):
    """
    Spedisce il link di reset tramite server SMTP.
    """
    SMTP_SERVER = "smtp.libero.it"
    SMTP_PORT = 465
    SMTP_USER = "andrewdicenso@libero.it"

    # 🔐 Password sicura presa dal file .env tramite config.py
    SMTP_PASSWORD = settings.SMTP_PASSWORD

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = email_destinatario
    msg["Subject"] = "🛡️ Reset Password | RGD-Alpha War Room"

    corpo_mail = f"""
    Hai richiesto il reset della password per il tuo account RGD-Alpha.
    
    Per procedere, clicca sul link sicuro qui sotto:
    {link_reset}
    
    Il link scadrà tra 30 minuti. Se non hai richiesto tu il reset, ignora questa mail.
    """
    msg.attach(MIMEText(corpo_mail, "plain"))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, email_destinatario, msg.as_string())
        logger.info(f"📧 Mail di reset inviata a {email_destinatario}")
        return True
    except Exception as e:
        logger.error(f"❌ Errore invio mail: {e}")
        return False
