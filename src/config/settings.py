"""
Settings.py - Configurazione Centralizzata RGD-Alpha
Utilizza Pydantic per validazione e gestione variabili d'ambiente.
"""
import os
from pathlib import Path
from typing import Optional
from functools import lru_cache


class Settings:
    """
    Configurazione Centralizzata - RGD-Alpha Enterprise.
    
    Legge da:
    1. Variabili d'ambiente (.env)
    2. Config JSON legacy
    3. Valori di default sicuri
    """
    
    # ========== PROJECT PATHS ==========
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
    DATA_ROOT: Path = PROJECT_ROOT / "data"
    UPLOAD_DIR: Path = DATA_ROOT / "uploads"
    DB_DIR: Path = DATA_ROOT / "db"
    LOG_DIR: Path = DATA_ROOT / "logs"
    
    # ========== APPLICATION ==========
    APP_NAME: str = "RGD-Alpha"
    APP_VERSION: str = "1.0.0-ALPHA"
    APP_DESCRIPTION: str = "War Room Strategica Aziendale"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # ========== DATABASE ==========
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/db/azienda.db")
    DB_PATH: str = str(DB_DIR / "azienda.db")
    
    # ========== SECURITY ==========
    VAULT_KEY_PATH: str = os.getenv("VAULT_KEY_PATH", "core/security/vault.key")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "andrewdicenso@libero.it")
    DEFAULT_ADMIN_PASSWORD: str = "WarRoom123!"
    
    # ========== PASSWORD HASHING ==========
    BCRYPT_ROUNDS: int = 12
    PASSWORD_MIN_LENGTH: int = 8
    
    # ========== STREAMLIT CONFIG ==========
    ST_PAGE_CONFIG = {
        "page_title": "RGD-Alpha | War Room Strategica",
        "layout": "wide",
        "page_icon": "🛡️",
        "initial_sidebar_state": "expanded"
    }
    
    # ========== RISK THRESHOLDS ==========
    RISK_THRESHOLD_CRITICAL: float = 7.5
    RISK_THRESHOLD_WARNING: float = 5.0
    RISK_THRESHOLD_SAFE: float = 3.0
    
    # ========== BUSINESS METRICS ==========
    SOGLIA_CAC: float = 50.0
    SOGLIA_LTV: float = 200.0
    SOGLIA_BURN_RATE: float = 10000.0
    SOGLIA_MARGINE: float = 20.0
    SOGLIA_CONVERSIONE: float = 2.0
    ORE_TEORICHE_ANNUE: int = 2080
    
    # ========== EMAIL CONFIG ==========
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.libero.it")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 465))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # ========== GOOGLE API ==========
    GMAIL_CLIENT_ID: Optional[str] = os.getenv("GMAIL_CLIENT_ID")
    GMAIL_CLIENT_SECRET: Optional[str] = os.getenv("GMAIL_CLIENT_SECRET")
    GMAIL_REFRESH_TOKEN: Optional[str] = os.getenv("GMAIL_REFRESH_TOKEN")
    
    # ========== GROQ LLM API ==========
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
    
    # ========== LOGGING ==========
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO" if not DEBUG else "DEBUG")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ========== ASSET CATEGORIES (Domain Constants) ==========
    ASSET_CATEGORIES = {
        "FINANCE": "AssetDiValore",
        "LOGISTICS": "AssetDiMercato",
        "RELATIONS": "AssetDiRelazione",
        "GENERAL": "AssetStrategico"
    }
    
    # ========== ERP SYSTEM SIGNATURES ==========
    ERP_SIGNATURES = {
        "SAP": r"\|",
        "ORACLE": r"\-{5,}",
        "AS400": r"PAGINA\s+\d+|PAGE\s+\d+"
    }
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Crea le directory necessarie se non esistono."""
        for dir_path in [cls.DATA_ROOT, cls.UPLOAD_DIR, cls.DB_DIR, cls.LOG_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def to_dict(cls) -> dict:
        """Converte settings a dizionario (excludendo secrets)."""
        return {
            k: v for k, v in cls.__dict__.items()
            if not k.startswith("_") and k.isupper() and not any(
                secret in k.upper() for secret in ["SECRET", "PASSWORD", "TOKEN", "KEY"]
            )
        }


# Singleton - Factory per settings
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Factory function per ottenere l'istanza Settings (singleton).
    Crea le directory necessarie al primo accesso.
    """
    Settings.ensure_directories()
    return Settings()


# Export per convenience
settings = get_settings()
