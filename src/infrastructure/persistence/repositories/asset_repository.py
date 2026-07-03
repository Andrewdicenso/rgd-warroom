"""
Asset Repository - Persistence per Asset entities.
"""
from typing import Optional, List
from src.domain import Asset
from .base_repository import BaseRepository


class AssetRepository(BaseRepository[Asset]):
    """
    Repository per Asset.
    
    NOTA: Questa è una implementazione in-memory per demo.
    In produzione, usare SQLAlchemy ORM + database vero.
    """
    
    def __init__(self):
        """Inizializza AssetRepository."""
        super().__init__("Asset")
        self._store: dict = {}  # In-memory storage
    
    def create(self, asset: Asset) -> Asset:
        """Crea e salva un asset."""
        self._store[asset.id] = asset
        self.log_info(f"Asset created: {asset.id}")
        return asset
    
    def read(self, id: str) -> Optional[Asset]:
        """Legge un asset per ID."""
        return self._store.get(id)
    
    def read_by_company(self, company_id: str) -> List[Asset]:
        """Legge tutti gli asset di una company."""
        return [a for a in self._store.values() if a.company_id == company_id]
    
    def update(self, asset: Asset) -> Asset:
        """Aggiorna un asset."""
        if asset.id not in self._store:
            raise ValueError(f"Asset {asset.id} not found")
        self._store[asset.id] = asset
        self.log_info(f"Asset updated: {asset.id}")
        return asset
    
    def delete(self, id: str) -> bool:
        """Cancella un asset."""
        if id in self._store:
            del self._store[id]
            self.log_info(f"Asset deleted: {id}")
            return True
        return False
    
    def list_all(self) -> List[Asset]:
        """Lista tutti gli asset."""
        return list(self._store.values())
    
    def list_critical(self, company_id: str) -> List[Asset]:
        """Lista asset critici di una company."""
        company_assets = self.read_by_company(company_id)
        return [a for a in company_assets if a.is_critical]
