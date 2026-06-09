import os
import datetime
import logging
import pandas as pd
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from core.secure_vault import SecureVault

logger = logging.getLogger("RGD-Alpha.Database")

class DatabaseAziendale:
    def __init__(self):
        try:
            self.vault = SecureVault()
            database_url = os.getenv("DATABASE_URL")
            
            if not database_url:
                from pathlib import Path
                db_folder = Path("data/db")
                db_folder.mkdir(parents=True, exist_ok=True)
                database_url = f"sqlite:///{db_folder / 'azienda.db'}"
                logger.info("📁 Usando SQLite locale")
            else:
                # Correzione fondamentale per Render: SQLAlchemy vuole postgresql:// non postgres://
                if database_url.startswith("postgres://"):
                    database_url = database_url.replace("postgres://", "postgresql://", 1)
                logger.info("☁️ Usando PostgreSQL")
            
            if "postgresql" in database_url:
                self.engine = create_engine(
                    database_url, 
                    pool_size=5, 
                    max_overflow=10, 
                    connect_args={"sslmode": "require"}
                )
            else:
                self.engine = create_engine(database_url, connect_args={"check_same_thread": False})
            
            self.crea_tabelle()
        except Exception as e:
            logger.critical(f"❌ Fallimento database: {e}")
            raise

    def _get_conn(self):
        return self.engine.connect()

    def crea_tabelle(self):
        # Rileva automaticamente se siamo su Postgres o SQLite per la chiave primaria
        is_postgres = "postgresql" in self.engine.dialect.name
        pk_type = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
        
        try:
            with self._get_conn() as conn:
                # Creazione tabelle con sintassi adattiva
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS utenti (
                        id {pk_type},
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        ruolo TEXT NOT NULL,
                        azienda TEXT,
                        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS asset_logs (
                        id {pk_type},
                        user_id INTEGER NOT NULL,
                        company_id TEXT NOT NULL,
                        nome TEXT NOT NULL,
                        tipo TEXT,
                        rischio REAL NOT NULL,
                        momentum TEXT,
                        volatilita REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS log_caricamenti (
                        id {pk_type}, 
                        user_id INTEGER, 
                        azienda TEXT, 
                        contesto TEXT, 
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                        nome_file TEXT
                    )
                """))
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Errore schema: {e}")

    def crea_utente(self, email, password, ruolo="user", azienda=None):
        try:
            email_enc = self.vault.encrypt_data(email)
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            with self._get_conn() as conn:
                # Nota: Uso RETURNING id per Postgres, lastrowid è per SQLite
                query = text("INSERT INTO utenti (email, password_hash, ruolo) VALUES (:e, :p, :r) RETURNING id")
                result = conn.execute(query, {"e": email_enc, "p": password_hash, "r": ruolo})
                user_id = result.fetchone()[0]
                
                if azienda is None: azienda = f"AZ-{user_id}"
                azienda_enc = self.vault.encrypt_data(azienda)
                
                conn.execute(text("UPDATE utenti SET azienda = :a WHERE id = :id"), {"a": azienda_enc, "id": user_id})
                conn.commit()
                return user_id
        except Exception as e:
            logger.error(f"Errore creazione utente: {e}")
            return None

    def get_utente_by_email(self, email):
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(text("SELECT id, email, password_hash, ruolo, azienda FROM utenti"))
                rows = cursor.fetchall()
            for row in rows:
                try:
                    email_dec = self.vault.decrypt_data(row[1])
                    if isinstance(email_dec, bytes): email_dec = email_dec.decode()
                    if email_dec.lower() == email.lower():
                        azienda_dec = self.vault.decrypt_data(row[4]) if row[4] else None
                        if isinstance(azienda_dec, bytes): azienda_dec = azienda_dec.decode()
                        return {"id": row[0], "email": email_dec, "password_hash": row[2], "ruolo": row[3], "azienda": azienda_dec}
                except: continue
            return None
        except: return None

    def salva_asset(self, user_id, nome_asset, rischio, **kwargs):
        try:
            # Recupero azienda per l'utente
            utente = self.get_utente_by_id(user_id)
            azienda = utente["azienda"] if utente else "Unknown"
            
            with self._get_conn() as conn:
                conn.execute(text("""
                    INSERT INTO asset_logs (user_id, company_id, nome, tipo, rischio, momentum, volatilita) 
                    VALUES (:u, :c, :n, :t, :r, :m, :v)
                """), {
                    "u": user_id, "c": azienda, "n": nome_asset, 
                    "t": kwargs.get('tipo'), "r": rischio, 
                    "m": kwargs.get('momentum'), "v": kwargs.get('volatilita')
                })
                conn.commit()
        except Exception as e:
            logger.error(f"Errore salvataggio asset: {e}")

    def get_utente_by_id(self, user_id):
        try:
            with self._get_conn() as conn:
                result = conn.execute(text("SELECT id, email, password_hash, ruolo, azienda FROM utenti WHERE id = :id"), {"id": user_id})
                row = result.fetchone()
                if row:
                    email_dec = self.vault.decrypt_data(row[1])
                    if isinstance(email_dec, bytes): email_dec = email_dec.decode()
                    azienda_dec = self.vault.decrypt_data(row[4]) if row[4] else None
                    if isinstance(azienda_dec, bytes): azienda_dec = azienda_dec.decode()
                    return {"id": row[0], "email": email_dec, "password_hash": row[2], "ruolo": row[3], "azienda": azienda_dec}
            return None
        except: return None

    def registra_caricamento(self, user_id, contesto, nome_file):
        try:
            utente = self.get_utente_by_id(user_id)
            azienda = utente["azienda"] if utente else "Unknown"
            with self._get_conn() as conn:
                conn.execute(text("INSERT INTO log_caricamenti (user_id, azienda, contesto, nome_file) VALUES (:u, :a, :c, :f)"), 
                             {"u": user_id, "a": azienda, "c": contesto, "f": nome_file})
                conn.commit()
        except: pass