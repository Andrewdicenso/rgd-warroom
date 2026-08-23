from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Config
    APP_MODE: str = "development"
    DEBUG: bool = True
    ADMIN_EMAIL: str
    SECRET_KEY: str
    DEFAULT_ADMIN_PASSWORD: str

    # Paths
    SRC_DIR: str = "src"
    UPLOAD_DIR: str = "data/uploads"

    # Security
    vault_key_path: str = "core/security/vault.key"
    db_password: str

    # SMTP
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    DATABASE_URL: str

    # Gemini
    GEMINI_API_KEY: str

    # Carica automaticamente dal file .env
    model_config = SettingsConfigDict(env_file=".env")


# Istanza da importare nel resto dell'app
settings = Settings()
