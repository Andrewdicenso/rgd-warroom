import os
import base64
import time
import json
from email.message import EmailMessage

import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Importiamo il database
from core.database import DatabaseAziendale

# Importiamo il nuovo connettore proattivo
from connectors.connector_manager import SFTPConnector

# Inizializziamo il database
db = DatabaseAziendale()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


def autentica_gmail():
    """Autenticazione Gmail tramite Streamlit Secrets (senza token.pickle)."""
    creds = Credentials(
        None,
        refresh_token=st.secrets["google_api"]["refresh_token"],
        client_id=st.secrets["google_api"]["client_id"],
        client_secret=st.secrets["google_api"]["client_secret"],
        token_uri=st.secrets["google_api"]["token_uri"],
    )
    return build("gmail", "v1", credentials=creds)


def invia_risposta(service, destinatario, oggetto_originale, corpo_richiesta):
    message = EmailMessage()
    risposta = (
        f"Gentile utente,\n\n"
        f"confermiamo di aver ricevuto la Sua richiesta: '{oggetto_originale}'.\n\n"
        f"Dati ricevuti:\n{corpo_richiesta}\n\n"
        f"Il nostro team di supporto la prenderà in carico a breve.\n\n"
        f"Cordiali saluti,\nRGandja Co-Pilota"
    )
    message.set_content(risposta)
    message["To"] = destinatario
    message["From"] = "me"
    message["Subject"] = f"Re: {oggetto_originale}"

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
    print(f"Risposta inviata a {destinatario}")


def leggi_mail(service):
    results = service.users().messages().list(userId="me", q="is:unread").execute()
    messages = results.get("messages", [])

    if not messages:
        return

    for message in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=message["id"], format="full")
            .execute()
        )

        payload = msg["payload"]
        body = ""
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8"
                    )

        headers = msg["payload"]["headers"]
        oggetto = next(
            (h["value"] for h in headers if h["name"] == "Subject"), "Senza Oggetto"
        )
        mittente = next(
            (h["value"] for h in headers if h["name"] == "From"), "Sconosciuto"
        )

        if "Richiedi Accreditamento" in oggetto:
            print(f"Trovata richiesta da {mittente}.")
            nome_azienda = "Sconosciuto"
            if "Azienda:" in body:
                nome_azienda = body.split("Azienda:")[1].split("|")[0].strip()

            db.salva_nuova_richiesta(nome_azienda, mittente)

            invia_risposta(service, mittente, oggetto, body)
            service.users().messages().modify(
                userId="me", id=message["id"], body={"removeLabelIds": ["UNREAD"]}
            ).execute()

        elif "Hai bisogno di un adeguamento?" in oggetto:
            print(f"Trovata richiesta di Adeguamento da {mittente}!")
            service.users().messages().modify(
                userId="me", id=message["id"], body={"removeLabelIds": ["UNREAD"]}
            ).execute()


if __name__ == "__main__":
    print("Avvio Co-Pilota RGandja in modalità monitoraggio...")
    try:
        service = autentica_gmail()

        # Caricamento sicuro delle credenziali e lista file da config.json
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                sftp_conf = config["sftp"]
                files_conf = config["files_to_sync"]
        except FileNotFoundError:
            print("Errore: Il file 'config.json' non è stato trovato.")
            exit()

        # Inizializzazione connettore con la nuova logica flessibile
        sftp_manager = SFTPConnector(
            host=sftp_conf["host"],
            username=sftp_conf["username"],
            password=sftp_conf["password"],
            files_to_sync=files_conf,
        )

        while True:
            print("Esecuzione sincronizzazione dati...")
            sftp_manager.sync_dati()

            leggi_mail(service)

            time.sleep(10)
    except KeyboardInterrupt:
        print("\nMonitoraggio interrotto correttamente.")
    except Exception as e:
        print(f"\nErrore critico: {e}")
