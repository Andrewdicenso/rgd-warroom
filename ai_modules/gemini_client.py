from google import genai
from google.genai import types
from google.genai.errors import APIError
import streamlit as st

# Modello aggiornato e compatibile
DEFAULT_MODEL = "gemini-3.6-flash"

@st.cache_resource
def get_gemini_client() -> genai.Client:
    """Inizializza e mappa in cache il client Gemini usando le Streamlit Secrets."""
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("La chiave GEMINI_API_KEY non è configurata nelle Streamlit Secrets.")
    return genai.Client(api_key=api_key)


def chiedi_a_gemini(
    prompt: str,
    system_instruction: str = None,
    temperature: float = 0.2,
    model: str = DEFAULT_MODEL
) -> str:
    """
    Invia un prompt a Gemini con gestione degli errori enterprise,
    configurabilità di sistema e parametri di generazione controllati.
    """
    try:
        client = get_gemini_client()

        # Configurazione avanzata della generazione
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
        )

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )

        if not response.text:
            return "Attenzione: Nessuna risposta generata dal modello."

        return response.text

    except APIError as e:
        # Gestione specifica degli errori dell'API di Google
        st.error(f"API di Gemini non disponibile (Errore {e.code}): {e.message}")
        return "Si è verificato un errore di comunicazione con il servizio AI. Riprova più tardi."
    except Exception as e:
        # Gestione generica di fallback
        st.error(f"Errore imprevisto nel modulo AI: {str(e)}")
        return "Impossibile completare la richiesta al momento."