import os
import logging
from typing import Any, Dict, Optional
from .base_model import AIModelInterface

logger = logging.getLogger(__name__)

class GroqAIProvider(AIModelInterface):
    """
    Implementazione del provider AI per RGD-Alpha.
    Supporta Google Gemini (e in fallback Groq se configurato).
    """

    def __init__(self):
        super().__init__()
        # Recupera prima la chiave Gemini, altrimenti prova Groq
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY")
        self.client = None
        self.model_name = "gemini-2.5-flash"

        if not self.api_key:
            logger.warning("⚠️ Nessuna API Key (Gemini/Groq) trovata nel .env. Modalità Fallback attiva.")
        else:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("✅ Client Google Gemini inizializzato con successo.")
            except Exception as e:
                logger.error(f"❌ Errore nell'inizializzazione del client Gemini: {e}")
                self.client = None

    def analyze(self, data: Dict[str, Any]) -> Optional[str]:
        """Analizza i dati tecnici e genera un insight di business."""
        if not self.client:
            return "Analisi AI non disponibile (Modalità offline/deterministica)."

        try:
            prompt = (
                "Sei il motore di intelligenza artificiale di RGD-Alpha, consulente B2B esperto in Risk Management.\n"
                f"Analizza questi dati di business e identifica inefficienze o sprechi: {data}"
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            if hasattr(self, "log_ai_error"):
                self.log_ai_error("GEMINI_ANALYSIS_ERROR", str(e))
            else:
                logger.error(f"GEMINI_ANALYSIS_ERROR: {e}")
            return None

    def generate_advice(self, context: str) -> Optional[str]:
        """Genera un consiglio operativo semplice e scorrevole per la War Room."""
        if not self.client:
            return None  # Ritorna None per attivare il consiglio deterministico senza blocchi

        try:
            prompt = (
                "Agisci come un consulente aziendale esperto per PMI italiane. "
                "Sii sintetico, diretto e usa un linguaggio chiaro. "
                f"Dai un consiglio operativo su come recuperare margini e mitigare i rischi basandoti su: {context}"
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            if hasattr(self, "log_ai_error"):
                self.log_ai_error("GEMINI_ADVICE_ERROR", str(e))
            else:
                logger.error(f"GEMINI_ADVICE_ERROR: {e}")
            return None


# Alias per mantenere la retrocompatibilità se altri moduli usano GroqProvider
GroqProvider = GroqAIProvider