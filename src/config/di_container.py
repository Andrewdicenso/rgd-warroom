"""
DI Container - Dependency Injection Container per RGD-Alpha.
Gestisce l'istanziazione delle dependencies in modo centralizzato.
"""
from typing import Dict, Any, Optional
import logging

from .settings import Settings, get_settings


logger = logging.getLogger("RGD-Alpha.DIContainer")


class DIContainer:
    """
    Contenitore di Dipendenze.
    
    Uso:
        container = DIContainer()
        asset_service = container.get_asset_service()
        analysis_service = container.get_analysis_service()
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Inizializza il container.
        
        Args:
            settings: Settings instance (default: get_settings())
        """
        self.settings = settings or get_settings()
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
        
        # Registra settings come singleton
        self._register_singleton("settings", self.settings)
    
    def _register_singleton(self, name: str, instance: Any) -> None:
        """Registra un'istanza singleton."""
        self._singletons[name] = instance
        logger.debug(f"✓ Singleton registered: {name}")
    
    def _register_factory(self, name: str, factory: callable) -> None:
        """Registra una factory function."""
        self._factories[name] = factory
        logger.debug(f"✓ Factory registered: {name}")
    
    def get(self, name: str) -> Any:
        """
        Ottiene una dependency dal container.
        
        Precedenza:
        1. Singletons (istanze già create)
        2. Factories (lazy loading)
        3. Exception se non trovato
        """
        # Prova singleton prima
        if name in self._singletons:
            return self._singletons[name]
        
        # Prova factory (lazy load)
        if name in self._factories:
            instance = self._factories[name]()
            self._singletons[name] = instance  # Cache come singleton
            return instance
        
        raise ValueError(f"❌ Dependency '{name}' not registered in DIContainer")
    
    # ========== EXAMPLE: Service Getters (Implementare quando serve) ==========
    
    def get_asset_service(self):
        """Otiene AssetService (quando implementato)."""
        # from application.services.asset_service import AssetService
        # return AssetService(asset_repo=self.get_asset_repository())
        pass
    
    def get_analysis_service(self):
        """Ottiene AnalysisService (quando implementato)."""
        # from application.services.analysis_service import AnalysisService
        # return AnalysisService(asset_repo=self.get_asset_repository(), ...)
        pass
    
    def get_database(self):
        """Ottiene DatabaseAziendale (when implemented)."""
        # from core.database import DatabaseAziendale
        # return DatabaseAziendale()
        pass


# Global container instance
_container: Optional[DIContainer] = None


def get_di_container() -> DIContainer:
    """Factory per ottenere il global DI container."""
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def reset_di_container() -> None:
    """Reset il container (utile per test)."""
    global _container
    _container = None
