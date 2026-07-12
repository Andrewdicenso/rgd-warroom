"""
Supabase Connection - Gestore Cloud Enterprise RGD-Alpha.
Sostituisce SQLite con persistenza Cloud-Native e Logging professionale.
"""
import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv  # Importa la libreria per leggere il file .env

# Recuperiamo il logger configurato nel tuo sistema
logger = logging.getLogger("RGD-Alpha.Database")

class DatabaseConnection:
    """
    Gestisce la connessione al database Cloud Supabase.
    Utilizza le Environment Variables impostate nel file .env o su Render.
    """
    
    def __init__(self):
        """Inizializza il client Supabase verificando le credenziali."""
        
        # Carica le variabili dal file .env (cerca automaticamente nella root del progetto)
        load_dotenv()
        
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        # Verifica se le variabili sono state caricate correttamente
        if not self.url or not self.key:
            logger.critical("❌ Mancano SUPABASE_URL o SUPABASE_KEY nelle variabili d'ambiente.")
            raise ValueError("Configurazione Supabase incompleta su Render o file .env mancante.")
            
        try:
            # Inizializzazione del client Supabase
            self.client: Client = create_client(self.url, self.key)
            logger.info("🛡️ Connessione Cloud Supabase stabilita con successo.")
        except Exception as e:
            logger.error(f"❌ Fallimento connessione Supabase: {e}")
            raise

    def get_client(self) -> Client:
        """Restituisce il client Supabase per le operazioni dei Repository."""
        return self.client