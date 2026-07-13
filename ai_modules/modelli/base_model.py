from abc import ABC, abstractmethod
from typing import Any, Dict

class AIModelInterface(ABC):
    """Interfaccia base per tutti i modelli AI del sistema RGD-Alpha."""
    
    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> str:
        """Analizza i dati forniti e restituisce un insight."""
        pass

    @abstractmethod
    def generate_advice(self, context: str) -> str:
        """Genera un consiglio operativo basato sul contesto."""
        pass
    from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

class AIModelInterface(ABC):
    """Interfaccia base potenziata con gestione errori e logging."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> Optional[str]:
        """Analizza i dati e restituisce insight."""
        pass

    @abstractmethod
    def generate_advice(self, context: str) -> Optional[str]:
        """Genera consiglio operativo."""
        pass

    def log_ai_error(self, error_type: str, details: str):
        """Metodo standard per loggare errori di integrazione AI."""
        self.logger.error(f"[{error_type}] {details}")
        # Qui potremmo aggiungere una notifica verso un servizio di monitoraggio