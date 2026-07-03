"""
Database Connection - Gestione connessione SQLite (stub).
"""
import sqlite3
import logging
from pathlib import Path
from typing import Optional


logger = logging.getLogger("RGD-Alpha.Database")


class DatabaseConnection:
    """
    Gestisce la connessione al database SQLite.
    
    NOTA: Questa è una versione semplificata.
    In produzione, usare SQLAlchemy per ORM mapping.
    """
    
    def __init__(self, db_path: str = "data/db/azienda.db"):
        """
        Inizializza la connessione al database.
        
        Args:
            db_path: Path al file SQLite
        """
        self.db_path = Path(db_path)
        self._ensure_db_exists()
    
    def _ensure_db_exists(self) -> None:
        """Assicura che il database e le tabelle esistano."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.db_path.exists():
            logger.info(f"Creating database: {self.db_path}")
            self._create_tables()
    
    def _create_tables(self) -> None:
        """Crea le tabelle necessarie."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Tabella Utenti
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utenti (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                ruolo TEXT NOT NULL,
                azienda_id TEXT,
                data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_ultimo_login TIMESTAMP
            )
        """)
        
        # Tabella Asset
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                company_id TEXT NOT NULL,
                categoria TEXT NOT NULL,
                rischio REAL NOT NULL,
                momentum_status TEXT,
                momentum_value REAL,
                volatilita REAL,
                data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_aggiornamento TIMESTAMP,
                dati_extra TEXT
            )
        """)
        
        # Tabella KPI Storico
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kpi_history (
                id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                rischio REAL NOT NULL,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asset_id) REFERENCES asset(id),
                FOREIGN KEY (user_id) REFERENCES utenti(id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database tables created")
    
    def get_connection(self) -> sqlite3.Connection:
        """Ottiene una connessione al database."""
        return sqlite3.connect(str(self.db_path))
    
    def execute_query(self, query: str, params: tuple = ()) -> list:
        """Esegue una query di lettura."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Esegue una query di modifica (INSERT, UPDATE, DELETE)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        return rows_affected
