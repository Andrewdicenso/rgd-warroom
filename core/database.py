import sqlite3
import datetime
import os
import logging
import pandas as pd
import bcrypt
from core.secure_vault import SecureVault

logger = logging.getLogger("RGD-Alpha.Database")

class DatabaseAziendale:
    def __init__(self, db_folder="data/db", db_name="azienda.db"):
        try:
            os.makedirs(db_folder, exist_ok=True)
            self.db_path = os.path.join(db_folder, db_name)
            self.vault = SecureVault()
            self.crea_tabelle()
            logger.info(f"🛡️ Database RGD-Alpha pronto: {self.db_path}")
        except Exception as e:
            logger.critical(f"❌ Fallimento database: {e}")
            raise

    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def crea_tabelle(self):
        try:
            with self._get_conn() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS utenti (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        ruolo TEXT NOT NULL,
                        azienda TEXT,
                        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS asset_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        company_id TEXT NOT NULL,
                        nome TEXT NOT NULL,
                        tipo TEXT,
                        rischio REAL NOT NULL,
                        momentum TEXT,
                        volatilita REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS log_caricamenti (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        user_id INTEGER, 
                        azienda TEXT, 
                        contesto TEXT, 
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                        nome_file TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Errore creazione schema: {e}")

    def crea_utente(self, email, password, ruolo="user", azienda=None):
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                email_enc = self.vault.encrypt_data(email)
                password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                cursor.execute(
                    "INSERT INTO utenti (email, password_hash, ruolo, azienda) VALUES (?, ?, ?, ?)", 
                    (email_enc, password_hash, ruolo, None)
                )
                user_id = cursor.lastrowid
                if azienda is None:
                    azienda = f"AZ-{user_id}"
                azienda_enc = self.vault.encrypt_data(azienda)
                cursor.execute("UPDATE utenti SET azienda = ? WHERE id = ?", (azienda_enc, user_id))
                conn.commit()
                return user_id
        except Exception as e:
            logger.error(f"Errore creazione utente: {e}")
            raise

    def get_utente_by_email(self, email):
        try:
            with self._get_conn() as conn:
                cursor = conn.execute("SELECT id, email, password_hash, ruolo, azienda FROM utenti")
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
            logger.error(f"Errore get_utente_by_email: {e}")
            return None

    def get_utente_by_id(self, user_id: int):
        try:
            with self._get_conn() as conn:
                cursor = conn.execute("SELECT id, email, password_hash, ruolo, azienda FROM utenti WHERE id = ?", (user_id,))
                row = cursor.fetchone()
            if not row: return None
            email_dec = self.vault.decrypt_data(row[1])
            if isinstance(email_dec, bytes): email_dec = email_dec.decode()
            azienda_dec = self.vault.decrypt_data(row[4]) if row[4] else None
            if isinstance(azienda_dec, bytes): azienda_dec = azienda_dec.decode()
            return {"id": row[0], "email": email_dec, "password_hash": row[2], "ruolo": row[3], "azienda": azienda_dec}
        except Exception as e:
            logger.error(f"Errore get_utente_by_id: {e}")
            return None

    def supervisione_admin_metriche_globali(self):
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT email, ruolo, azienda, data_creazione FROM utenti", conn)
                if df.empty: return df
                def _dec(v):
                    if v is None: return None
                    dec = self.vault.decrypt_data(v)
                    return dec.decode() if isinstance(dec, bytes) else dec
                df["email"] = df["email"].apply(_dec)
                df["azienda"] = df["azienda"].apply(_dec)
                return df
        except Exception as e:
            logger.error(f"Errore Admin: {e}"); return pd.DataFrame()

    def recupera_attivita_globale(self):
        try:
            with self._get_conn() as conn:
                return pd.read_sql_query("SELECT * FROM asset_logs", conn)
        except Exception as e:
            logger.error(f"Errore: {e}"); return pd.DataFrame()

    def recupera_log_caricamenti_admin(self):
        try:
            with self._get_conn() as conn:
                return pd.read_sql_query("SELECT * FROM log_caricamenti", conn)
        except Exception as e:
            logger.error(f"Errore: {e}"); return pd.DataFrame()

    def registra_caricamento(self, user_id, contesto, nome_file):
        try:
            utente = self.get_utente_by_id(user_id)
            if not utente: return
            with self._get_conn() as conn:
                conn.execute("INSERT INTO log_caricamenti (user_id, azienda, contesto, nome_file) VALUES (?, ?, ?, ?)", (user_id, utente["azienda"], contesto, nome_file))
                conn.commit()
        except Exception as e: logger.error(f"Errore caricamento: {e}")

    def salva_asset(self, user_id, nome_asset, rischio, **kwargs):
        try:
            utente = self.get_utente_by_id(user_id)
            if not utente: return
            with self._get_conn() as conn:
                conn.execute("INSERT INTO asset_logs (user_id, company_id, nome, tipo, rischio, momentum, volatilita) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (user_id, utente["azienda"], nome_asset, kwargs.get('tipo'), rischio, kwargs.get('momentum'), kwargs.get('volatilita')))
                conn.commit()
        except Exception as e: logger.error(f"Errore salvataggio asset: {e}")

    def calcola_e_salva_kpi_correnti(self, user_id):
        """
        MODULO 2: Analisi Predittiva Auto-Adattiva.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.execute("SELECT AVG(rischio), COUNT(id) FROM asset_logs WHERE user_id = ? AND timestamp >= datetime('now', '-1 hour')", (user_id,))
                res_recent = cursor.fetchone()
                rischio_recente = res_recent[0] if res_recent[0] is not None else 0
                count_recent = res_recent[1]

                cursor = conn.execute("SELECT AVG(rischio) FROM asset_logs WHERE user_id = ? AND timestamp < datetime('now', '-1 hour') AND timestamp >= datetime('now', '-24 hours')", (user_id,))
                row_storico = cursor.fetchone()
                rischio_storico = row_storico[0] if row_storico and row_storico[0] is not None else rischio_recente

            if count_recent == 0:
                return {"solidita": 100, "impatto_30gg": "N/D", "rischio_medio": 0, "trend": "Stabile", "variazione": 0}

            variazione = round(rischio_recente - rischio_storico, 2)
            solidita = max(min(round(100 - (rischio_recente * 10), 1), 100), 0)

            if variazione > 0.5: trend, impatto = "In Peggioramento", "CRITICO"
            elif variazione < -0.5: trend, impatto = "In Miglioramento", "POSITIVO"
            else: trend, impatto = "Stabile", "STABILE"

            return {
                "solidita": solidita, "rischio_medio": round(rischio_recente, 2), "trend": trend,
                "variazione": variazione, "impatto_30gg": impatto,
                "data_analisi": datetime.datetime.now().strftime("%H:%M")
            }
        except Exception as e:
            logger.error(f"Errore Modulo 2: {e}")
            return {"solidita": 0, "impatto_30gg": "ERRORE", "rischio_medio": 0, "trend": "Errore", "variazione": 0}
