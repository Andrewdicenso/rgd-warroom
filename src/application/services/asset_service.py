"""
Asset Service - Use Case: Gestione Asset.
"""
from typing import Optional, List
from src.domain import Asset, AssetCategory, RiscoScore
from src.application.services.base_service import BaseService
from src.application.mappers import AssetMapper
from src.application.dto import AssetDTO

class AssetService(BaseService):
    """
    Servizio per la gestione degli asset.
    Orchestra operazioni su asset usando il repository per la persistenza reale.
    """
    
    def __init__(self, asset_repo=None):
        """Inizializza AssetService con il repository (Dependency Injection)."""
        super().__init__("AssetService")
        self.asset_repo = asset_repo
        self._assets_store: dict = {}  # In-memory storage (backup/cache)

    def create_asset(self, asset: Asset) -> AssetDTO:
        """
        Salva un asset (già creato dall'ingestore) nel database.
        Metodo usato dalla War Room.
        """
        self.log_info(f"Saving asset: {asset.nome}")
        try:
            # 1. Persistenza reale tramite Repository
            if self.asset_repo:
                self.asset_repo.create(asset)
            
            # 2. Cache in memoria
            self._assets_store[asset.id] = asset
            
            return AssetMapper.to_dto(asset)
        except Exception as e:
            self.log_error(f"Error saving asset {asset.nome}", e)
            raise

    def get_asset(self, asset_id: str, company_id: str) -> Optional[AssetDTO]:
        """Recupera un asset per ID (filtrato per company)."""
        self.log_debug(f"Getting asset {asset_id}")
        
        # Prova prima nel database reale, altrimenti in memoria
        asset = None
        if self.asset_repo:
            asset = self.asset_repo.read(asset_id)
        
        if not asset:
            asset = self._assets_store.get(asset_id)
            
        if not asset or asset.company_id != company_id:
            return None
        
        return AssetMapper.to_dto(asset)

    def list_assets(self, company_id: str) -> List[AssetDTO]:
        """Lista tutti gli asset di una company."""
        self.log_info(f"Listing assets for company {company_id}")
        
        if self.asset_repo:
            # Recupera dal DB (Repository filtrato per company)
            company_assets = self.asset_repo.list_all() # Da filtrare nel repo o qui
            company_assets = [a for a in company_assets if a.company_id == company_id]
        else:
            company_assets = [a for a in self._assets_store.values() if a.company_id == company_id]
        
        return AssetMapper.to_dtos(company_assets)

    def update_asset_risk(self, asset_id: str, company_id: str, new_risk_value: float) -> AssetDTO:
        """Aggiorna il rischio di un asset."""
        self.log_info(f"Updating risk for asset {asset_id}: {new_risk_value}")
        
        asset = self._assets_store.get(asset_id) # O recupera dal repo
        if not asset or asset.company_id != company_id:
            raise ValueError(f"Asset {asset_id} not found or unauthorized")
        
        asset.aggiorna_rischio(new_risk_value)
        
        if self.asset_repo:
            self.asset_repo.update(asset_id, asset)
            
        return AssetMapper.to_dto(asset)

    def get_critical_assets(self, company_id: str) -> List[AssetDTO]:
        """Recupera asset critici di una company."""
        self.log_info(f"Getting critical assets for {company_id}")
        all_assets = self.list_assets(company_id)
        return [a for a in all_assets if a.is_critical]