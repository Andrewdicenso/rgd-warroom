from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

class AIModelInterface(ABC):
    """
    Interfaccia base potenziata per tutti i modelli AI del sistema RGD-Alpha.
    Fornisce la struttura astratta e i metodi standard di logging e gestione errori.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> Optional[str]:
        """Analizza i dati forniti e restituisce un insight di business."""
        pass

    @abstractmethod
    def generate_advice(self, context: str) -> Optional[str]:
        """Genera un consiglio operativo basato sul contesto fornito."""
        pass

    def log_ai_error(self, error_type: str, details: str) -> None:
        """Metodo standard per loggare errori di integrazione AI."""
        self.logger.error(f"[{error_type}] {details}")
        # In futuro: invio notifica automatica verso dashboard o webhook di monitoraggio