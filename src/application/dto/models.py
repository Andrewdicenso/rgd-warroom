"""
DTOs (Data Transfer Objects) - Application Layer.
Usati per trasferire dati tra layer (non contengono logica di business).
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class AssetDTO:
    """DTO per Asset - used for API responses, UI rendering."""
    id: str
    nome: str
    categoria: str
    rischio_value: float
    rischio_level: str  # CRITICAL, WARNING, SAFE
    momentum_status: str
    momentum_value: float
    volatilita_value: float
    company_id: str
    data_creazione: str
    data_aggiornamento: str
    is_critical: bool
    dati_extra: Dict[str, Any]


@dataclass
class AssetDiMercatoDTO(AssetDTO):
    """DTO per Asset di Logistica."""
    quantita: float = 0.0
    sku: str = ""
    ubicazione: str = ""


@dataclass
class AssetDiValoreDTO(AssetDTO):
    """DTO per Asset di Finanza."""
    prezzo: float = 0.0
    stato_pagamento: str = ""
    valuta: str = "EUR"


@dataclass
class RiskAnalysisDTO:
    """DTO per risultato analisi di rischio."""
    asset_id: str
    asset_nome: str
    rischio_attuale: float
    rischio_proiezione_30gg: float
    rischio_proiezione_60gg: float
    rischio_proiezione_90gg: float
    trend: str  # ACCELERATING, DECELERATING, STABLE
    trend_value: float
    volatilita: float
    consiglio_strategico: str
    urgenza: str  # IMMEDIATE, HIGH, MEDIUM, LOW
    confidenza: float  # 0-1 (confidence score)


@dataclass
class KPIReportDTO:
    """DTO per report KPI."""
    periodo: str  # "2024-03"
    health_score: float  # 0-10
    asset_critici_count: int
    asset_warning_count: int
    cash_flow_previsto: float
    revenue_previsto: float
    margin_percentage: float
    trend_overall: str
    summary: str


@dataclass
class LoginRequestDTO:
    """DTO per richiesta login."""
    email: str
    password: str


@dataclass
class LoginResponseDTO:
    """DTO per risposta login."""
    success: bool
    user_id: str
    email: str
    ruolo: str
    azienda: str
    azienda_id: str
    token: Optional[str] = None
    message: str = ""


@dataclass
class UserDTO:
    """DTO per Utente."""
    id: str
    email: str
    ruolo: str
    azienda_id: Optional[str]
    data_creazione: str
    data_ultimo_login: Optional[str]


@dataclass
class RegistrationRequestDTO:
    """DTO per richiesta registrazione."""
    email: str
    password: str
    confirm_password: str
    azienda_name: Optional[str] = None


@dataclass
class RegistrationResponseDTO:
    """DTO per risposta registrazione."""
    success: bool
    user_id: Optional[str] = None
    message: str = ""


@dataclass
class PasswordResetRequestDTO:
    """DTO per richiesta reset password."""
    email: str


@dataclass
class PasswordResetDTO:
    """DTO per completamento reset password."""
    token: str
    new_password: str
    confirm_password: str


@dataclass
class FileIngestionRequestDTO:
    """DTO per richiesta ingestion file."""
    file_name: str
    file_content: bytes
    file_type: str  # csv, xlsx, etc
    user_id: str
    company_id: str


@dataclass
class FileIngestionResponseDTO:
    """DTO per risposta ingestion file."""
    success: bool
    ingestion_id: str
    rows_processed: int
    rows_valid: int
    rows_rejected: int
    assets_created: int
    assets_updated: int
    errors: List[str]
    warnings: List[str]


@dataclass
class AlertDTO:
    """DTO per Alert."""
    id: str
    severity: str  # CRITICAL, WARNING, INFO
    title: str
    message: str
    asset_id: Optional[str]
    created_at: str
    read: bool


@dataclass
class DashboardDTO:
    """DTO per Dashboard summary."""
    health_score: float
    asset_critici: int
    asset_warning: int
    asset_total: int
    alerts: List[AlertDTO]
    top_risks: List[RiskAnalysisDTO]
    recent_uploads: List[str]
    last_sync: str
