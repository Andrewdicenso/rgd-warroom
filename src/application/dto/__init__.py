"""DTOs Module."""
from .models import (
    AssetDTO,
    AssetDiMercatoDTO,
    AssetDiValoreDTO,   # <-- Aggiunto qui
    RiskAnalysisDTO,
    KPIReportDTO,
    LoginRequestDTO,
    LoginResponseDTO,
    UserDTO,
    RegistrationRequestDTO,
    RegistrationResponseDTO,
    FileIngestionRequestDTO,
    FileIngestionResponseDTO,
    AlertDTO,
    DashboardDTO
)

__all__ = [
    "AssetDTO",
    "AssetDiMercatoDTO",
    "AssetDiValoreDTO",  # <-- Aggiunto qui
    "RiskAnalysisDTO",
    "KPIReportDTO",
    "LoginRequestDTO",
    "LoginResponseDTO",
    "UserDTO",
    "RegistrationRequestDTO",
    "RegistrationResponseDTO",
    "FileIngestionRequestDTO",
    "FileIngestionResponseDTO",
    "AlertDTO",
    "DashboardDTO"
]