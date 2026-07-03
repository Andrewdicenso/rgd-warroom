"""
Asset Service - Use Case: Gestione Asset.
"""
from typing import Optional, List
from src.domain import Asset, AssetCategory, RiscoScore, Azienda
from src.application.services.base_service import BaseService
from src.application.mappers import AssetMapper
from src.application.dto import AssetDTO


class AssetService(BaseService):
    """
    Servizio per la gestione degli asset.
    Orchiestra operazioni su asset (crea, legge, aggiorna, elimina).
    
    NOTA: In produzione, userà un AssetRepository per persistenza.
    Per ora, usa in-memory storage per demo.
    """
    
    def __init__(self):
        """Inizializza AssetService."""
        super().__init__("AssetService")
        self._assets_store: dict = {}  # In-memory storage (demo only)
    
    def create_asset(
        self,
        nome: str,
        company_id: str,
        categoria: AssetCategory,
        rischio_value: float = 0.0,
        **dati_extra
    ) -> AssetDTO:
        """
        Crea un nuovo asset.
        
        Args:
            nome: Nome asset
            company_id: ID azienda (multi-tenant)
            categoria: Categoria asset
            rischio_value: Punteggio rischio iniziale
            **dati_extra: Dati aggiuntivi
            
        Returns:
            AssetDTO creato
            
        Raises:
            ValueError: Se dati non validi
        """
        self.log_info(f"Creating asset: {nome} for company {company_id}")
        
        try:
            # Crea domain entity
            asset = Asset(
                nome=nome,
                company_id=company_id,
                categoria=categoria,
                rischio=RiscoScore(rischio_value),
                dati_extra=dati_extra
            )
            
            # Salva in store (demo)
            self._assets_store[asset.id] = asset
            
            # Converte a DTO
            dto = AssetMapper.to_dto(asset)
            self.log_info(f"Asset created: {asset.id}")
            
            return dto
            
        except Exception as e:
            self.log_error(f"Error creating asset {nome}", e)
            raise
    
    def get_asset(self, asset_id: str, company_id: str) -> Optional[AssetDTO]:
        """
        Recupera un asset per ID (filtrato per company).
        
        Args:
            asset_id: ID asset
            company_id: ID azienda (multi-tenant check)
            
        Returns:
            AssetDTO o None se non trovato
        """
        self.log_debug(f"Getting asset {asset_id}")
        
        asset = self._assets_store.get(asset_id)
        if not asset:
            return None
        
        # Multi-tenant: verifica che l'asset appartiene alla company
        if asset.company_id != company_id:
            self.log_warning(f"Unauthorized access attempt to asset {asset_id}")
            return None
        
        return AssetMapper.to_dto(asset)
    
    def list_assets(self, company_id: str) -> List[AssetDTO]:
        """
        Lista tutti gli asset di una company.
        
        Args:
            company_id: ID azienda
            
        Returns:
            Lista AssetDTO
        """
        self.log_info(f"Listing assets for company {company_id}")
        
        company_assets = [
            a for a in self._assets_store.values()
            if a.company_id == company_id
        ]
        
        return AssetMapper.to_dtos(company_assets)
    
    def update_asset_risk(
        self,
        asset_id: str,
        company_id: str,
        new_risk_value: float
    ) -> AssetDTO:
        """
        Aggiorna il rischio di un asset.
        
        Args:
            asset_id: ID asset
            company_id: ID azienda
            new_risk_value: Nuovo valore rischio
            
        Returns:
            AssetDTO aggiornato
            
        Raises:
            ValueError: Se asset non trovato o dato non valido
        """
        self.log_info(f"Updating risk for asset {asset_id}: {new_risk_value}")
        
        asset = self._assets_store.get(asset_id)
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")
        
        if asset.company_id != company_id:
            raise ValueError(f"Unauthorized access to asset {asset_id}")
        
        # Aggiorna rischio
        asset.aggiorna_rischio(new_risk_value)
        
        return AssetMapper.to_dto(asset)
    
    def get_critical_assets(self, company_id: str) -> List[AssetDTO]:
        """
        Recupera asset critici di una company.
        
        Args:
            company_id: ID azienda
            
        Returns:
            Lista AssetDTO critici
        """
        self.log_info(f"Getting critical assets for {company_id}")
        
        all_assets = self.list_assets(company_id)
        critical = [a for a in all_assets if a.is_critical]
        
        return critical
