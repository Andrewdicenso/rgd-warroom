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
    
    py
    # ========== SERVICE & REPOSITORY GETTERS (Operativi) ==========

    def get_database(self):
        """Restituisce la connessione Supabase persistente."""
        from src.infrastructure.persistence.db.connection import DatabaseConnection
        return self.get("database") if "database" in self._singletons else \
               self._register_singleton("database", DatabaseConnection())

    def get_user_repository(self):
        from src.infrastructure.persistence.repositories.user_repository import UserRepository
        return UserRepository(db=self.get_database())

    def get_asset_repository(self):
        from src.infrastructure.persistence.repositories.asset_repository import AssetRepository
        return AssetRepository(db=self.get_database())

    def get_auth_service(self):
        from src.application.services.auth_service import AuthService
        return AuthService(user_repo=self.get_user_repository())

    def get_analysis_service(self):
        from src.application.services.analysis_service import AnalysisService
        # L'analisi richiede i dati storici (KPI Repository)
        from src.infrastructure.persistence.repositories.kpi_repository import KPIRepository
        kpi_repo = KPIRepository(db=self.get_database())
        return AnalysisService(kpi_repo=kpi_repo)

    def get_ingestion_service(self):
        from src.application.services.ingestion_service import IngestionService
        return IngestionService()