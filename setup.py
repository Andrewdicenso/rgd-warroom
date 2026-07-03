"""
Setup script - Configurazione iniziale RGD-Alpha
"""
import os
import sys
from pathlib import Path

# Risolvi percorsi
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def setup_environment():
    """Setup l'ambiente iniziale."""
    print("🚀 RGD-Alpha Setup Iniziato...")
    
    # Crea directory necessarie
    directories = [
        "data/db",
        "data/uploads",
        "data/logs",
        "data/exports",
        "core/security"
    ]
    
    for dir_path in directories:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Creato: {dir_path}")
    
    # Crea .env se non esiste
    env_file = PROJECT_ROOT / ".env"
    env_example = PROJECT_ROOT / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        print("✅ .env creato da .env.example")
    
    # Configura logging
    from src.infrastructure import configure_logging
    configure_logging()
    print("✅ Logging configurato")
    
    # Inizializza services
    from src.application.services import AuthService, AssetService, AnalysisService
    auth_service = AuthService()
    asset_service = AssetService()
    analysis_service = AnalysisService()
    print("✅ Services inizializzati")
    
    print("\n✨ Setup completato con successo!")
    print("\nProssimi step:")
    print("1. Modifica .env con le tue credenziali")
    print("2. Avvia: streamlit run src/presentation/streamlit_app.py")
    print("3. Run test: pytest tests/ -v")


if __name__ == "__main__":
    setup_environment()
