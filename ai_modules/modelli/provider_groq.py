import os
from typing import Any, Dict, Optional
from groq import Groq
from .base_model import AIModelInterface

class GroqAIProvider(AIModelInterface):
    """Implementazione del provider per Groq AI."""

    def __init__(self):
        super().__init__()
        # Assicurati di avere GROQ_API_KEY nel tuo file .env
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model_name = "llama3-70b-8192" # Modello di default ottimizzato

    def analyze(self, data: Dict[str, Any]) -> Optional[str]:
        """Analizza i dati tecnici e genera un insight di business."""
        try:
            prompt = f"Analizza questi dati di business e identifica inefficienze o sprechi: {data}"
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            self.log_ai_error("GROQ_ANALYSIS_ERROR", str(e))
            return None

    def generate_advice(self, context: str) -> Optional[str]:
        """Genera un consiglio operativo semplice e scorrevole per la War Room."""
        try:
            prompt = f"Agisci come un consulente aziendale esperto. Sii sintetico, diretto e usa un linguaggio semplice. Dai un consiglio su come recuperare margini basandoti su: {context}"
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            self.log_ai_error("GROQ_ADVICE_ERROR", str(e))
            return None