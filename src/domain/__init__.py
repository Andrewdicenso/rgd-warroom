"""
Domain Module - Logica Pura di Business.
Contiene: Entità, Value Objects, Rules, Exceptions.
Zero dipendenze da Infrastructure/Application.
"""

from .entities import (
    Asset,
    AssetDiMercato,
    AssetDiValore,
    AssetDiRelazione,
    Azienda,
    Utente,
    crea_asset_dal_dizionario
)

from .value_objects import (
    RiscoScore,
    Momentum,
    Volatilita,
    PeriodoTemporale
)

from .exceptions import (
    DomainException,
    AssetException,
    RiskException,
    ValidationException,
    InvalidRiscoScoreException,
    InvalidAssetException,
    AssetNotFound
)

from .constants import (
    AssetCategory,
    MomentumStatus,
    RiskLevel,
    PaymentStatus,
    InventoryStatus,
    UserRole,
    SINONIMI_MAPPING,
    SAP_FIELD_MAPPING,
    SETTORE_KEYS
)

__all__ = [
    # Entities
    "Asset",
    "AssetDiMercato",
    "AssetDiValore",
    "AssetDiRelazione",
    "Azienda",
    "Utente",
    "crea_asset_dal_dizionario",
    # Value Objects
    "RiscoScore",
    "Momentum",
    "Volatilita",
    "PeriodoTemporale",
    # Exceptions
    "DomainException",
    "AssetException",
    "RiskException",
    "ValidationException",
    "InvalidRiscoScoreException",
    "InvalidAssetException",
    "AssetNotFound",
    # Constants
    "AssetCategory",
    "MomentumStatus",
    "RiskLevel",
    "PaymentStatus",
    "InventoryStatus",
    "UserRole",
    "SINONIMI_MAPPING",
    "SAP_FIELD_MAPPING",
    "SETTORE_KEYS",
]
