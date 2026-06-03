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
            
            # Rileva automaticamente se siamo su Render o locale
            database_url = os.getenv("DATABASE_URL")
            
            if not database_url:
                # Fallback locale per sviluppo
                from pathlib import Path
                db_folder = Path("data/db")
                db_folder.mkdir(parents=True, exist_ok=True)
                database_url = f"sqlite:///{db_folder / 'azienda.db'}"
                logger.info("📁 Usando SQLite locale (sviluppo)")
            else:
                logger.info("☁️ Usando PostgreSQL (produzione Render)")
            
            # Configura connection pool per PostgreSQL
            if database_url.startswith("postgresql"):
                self.engine = create_engine(
                    database_url,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_recycle=1800,
                    connect_args={"sslmode": "require"}
                )
            else:
                self.engine = create_engine(database_url, connect_args={"check_same_thread": False})
            
            self.crea_tabelle()
            logger.info("🛡️ Database RGD-Alpha inizializzato")
            
        except Exception as e:
            logger.critical(f"❌ Fallimento database: {e}")
            raise

    def _get_conn(self):
        return self.engine.connect()

    def crea_tabelle(self):
        try:
            with self._get_conn() as conn:
                # Tabella utenti (compatibile SQLite e PostgreSQL)
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS utenti (
                        id SERIAL PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        ruolo TEXT NOT NULL,
                        azienda TEXT,
                        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Tabella asset_logs
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS asset_logs (
                        id SERIAL PRIMARY KEY,
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
                
                # Tabella log_caricamenti
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS log_caricamenti (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER,
                        azienda TEXT,
                        contesto TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        nome_file TEXT
                    )
                """))
                
                conn.commit()
                logger.info("✅ Tabelle create con successo")
        except Exception as e:
            logger.error(f"❌ Errore creazione schema: {e}")
            raise

    def crea_utente(self, email, password, ruolo="user", azienda=None):
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                email_enc = self.vault.encrypt_data(email)
                password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                cursor.execute(text("INSERT INTO utenti (email, password_hash, ruolo, azienda) VALUES (?, ?, ?, ?)"), 
                             (email_enc, password_hash, ruolo, None))
                user_id = cursor.lastrowid
                if azienda is None: azienda = f"AZ-{user_id}"
                azienda_enc = self.vault.encrypt_data(azienda)
                cursor.execute(text("UPDATE utenti SET azienda = ? WHERE id = ?"), (azienda_enc, user_id))
                conn.commit()
                return user_id
        except Exception as e:
            logger.error(f"Errore creazione utente: {e}")
            raise

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
        except Exception as e:
            return None

    def get_utente_by_id(self, user_id: int):
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(text("SELECT id, email, password_hash, ruolo, azienda FROM utenti WHERE id = ?"), (user_id,))
                row = cursor.fetchone()
            if not row: return None
            email_dec = self.vault.decrypt_data(row[1])
            if isinstance(email_dec, bytes): email_dec = email_dec.decode()
            azienda_dec = self.vault.decrypt_data(row[4]) if row[4] else None
            if isinstance(azienda_dec, bytes): azienda_dec = azienda_dec.decode()
            return {"id": row[0], "email": email_dec, "password_hash": row[2], "ruolo": row[3], "azienda": azienda_dec}
        except: return None

    def supervisione_admin_metriche_globali(self):
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT email, ruolo, azienda, data_creazione FROM utenti", conn)
                if df.empty: return df
                df["email"] = df["email"].apply(lambda x: self.vault.decrypt_data(x).decode() if isinstance(self.vault.decrypt_data(x), bytes) else self.vault.decrypt_data(x))
                df["azienda"] = df["azienda"].apply(lambda x: self.vault.decrypt_data(x).decode() if isinstance(self.vault.decrypt_data(x), bytes) else self.vault.decrypt_data(x))
                return df
        except: return pd.DataFrame()

    def recupera_attivita_globale(self, solo_admin=False):
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT * FROM asset_logs", conn)
                return df
        except: return pd.DataFrame()

    def recupera_log_caricamenti_admin(self):
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT * FROM log_caricamenti", conn)
                return df
        except: return pd.DataFrame()

    def registra_caricamento(self, user_id, contesto, nome_file):
        try:
            azienda = self.get_utente_by_id(user_id)["azienda"]
            with self._get_conn() as conn:
                conn.execute(text("INSERT INTO log_caricamenti (user_id, azienda, contesto, nome_file) VALUES (?, ?, ?, ?)"), 
                             (user_id, azienda, contesto, nome_file))
                conn.commit()
        except: pass

    def salva_asset(self, user_id, nome_asset, rischio, **kwargs):
        try:
            azienda = self.get_utente_by_id(user_id)["azienda"]
            with self._get_conn() as conn:
                conn.execute(text("INSERT INTO asset_logs (user_id, company_id, nome, tipo, rischio, momentum, volatilita) VALUES (?, ?, ?, ?, ?, ?, ?)"),
                             (user_id, azienda, nome_asset, kwargs.get('tipo'), rischio, kwargs.get('momentum'), kwargs.get('volatilita')))
                conn.commit()
        except: pass

    def calcola_e_salva_kpi_correnti(self, user_id):
        """Calcola i KPI reali basandosi sugli asset salvati nel database."""
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(text("""
                    SELECT AVG(rischio) FROM asset_logs 
                    WHERE user_id = ? AND timestamp >= NOW() - INTERVAL '1 hour'
                """), (user_id,))
                rischio_medio = cursor.fetchone()[0]
            
            if rischio_medio is None:
                return {"solidita": 100, "impatto_30gg": "N/D", "rischio_medio": 0}

            solidita = round(100 - (rischio_medio * 10), 1)
            solidita = max(min(solidita, 100), 0)
            
            impatto = "CRITICO" if rischio_medio > 7 else "ATTENZIONE" if rischio_medio > 4 else "STABILE"

            return {
                "solidita": solidita,
                "impatto_30gg": impatto,
                "rischio_medio": round(rischio_medio, 2)
            }
        except:
            return {"solidita": 0, "impatto_30gg": "ERRORE", "rischio_medio": 0}