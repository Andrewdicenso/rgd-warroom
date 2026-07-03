"""
Base Service - Classe astratta base per tutti i servizi.
"""
import logging
from abc import ABC


class BaseService(ABC):
    """Base service class con logging comune."""
    
    def __init__(self, service_name: str):
        """
        Inizializza il servizio base.
        
        Args:
            service_name: Nome del servizio (per logging)
        """
        self.logger = logging.getLogger(f"RGD-Alpha.{service_name}")
        self.service_name = service_name
    
    def log_info(self, message: str) -> None:
        """Log info level."""
        self.logger.info(f"[{self.service_name}] {message}")
    
    def log_error(self, message: str, exception: Exception = None) -> None:
        """Log error level."""
        if exception:
            self.logger.error(f"[{self.service_name}] {message}", exc_info=exception)
        else:
            self.logger.error(f"[{self.service_name}] {message}")
    
    def log_warning(self, message: str) -> None:
        """Log warning level."""
        self.logger.warning(f"[{self.service_name}] {message}")
    
    def log_debug(self, message: str) -> None:
        """Log debug level."""
        self.logger.debug(f"[{self.service_name}] {message}")
