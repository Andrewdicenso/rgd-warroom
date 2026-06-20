import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
import os
import logging
import pandas as pd
import bcrypt
from core.secure_vault import SecureVault

logger = logging.getLogger("RGD-Alpha.Database.Cloud")

class DatabaseAziendale:
    def __init__(self):
        # Usiamo la stringa di connessione fornita
        self.db_url = "postgresql://rgdwarroomdb:vE8bsreVmq54V8M3Nh5pGsiakjYQUycr@dpg-d8fm0cq8qa3s73aeh4e0-a/rgdwarroomdb"
        self.vault = SecureVault()
        self.crea_tabelle()
        logger.info("🛡️ Database Cloud RGD-Alpha (PostgreSQL) Connesso.")

    def _get_conn(self):
        # Connessione al database esterno
        return psycopg2.connect(self.db_url)

    def crea_tabelle(self):
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    # Tabella Utenti (Sintassi PostgreSQL)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS utenti (
                            id SERIAL PRIMARY KEY,
                            email TEXT UNIQUE NOT NULL,
                            password_hash TEXT NOT NULL,
                            ruolo TEXT NOT NULL,
                            azienda TEXT,
                            data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    # Tabella Asset Logs
                    cur.execute("""
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
                    """)
                    # Tabella Log Caricamenti
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS log_caricamenti (
                            id SERIAL PRIMARY KEY, 
                            user_id INTEGER, 
                            azienda TEXT, 
                            contesto TEXT, 
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                            nome_file TEXT
                        )
                    """)
                    # Tabella Log Sicurezza (per reset password e accessi)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS security_logs (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER,
                            azione TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Errore schema Cloud: {e}")

    def crea_utente(self, email, password, ruolo="user", azienda=None):
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    email_enc = self.vault.encrypt_data(email)
                    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                    cur.execute(
                        "INSERT INTO utenti (email, password_hash, ruolo) VALUES (%s, %s, %s) RETURNING id", 
                        (email_enc, password_hash, ruolo)
                    )
                    user_id = cur.fetchone()[0]
                    if azienda is None: azienda = f"AZ-{user_id}"
                    azienda_enc = self.vault.encrypt_data(azienda)
                    cur.execute("UPDATE utenti SET azienda = %s WHERE id = %s", (azienda_enc, user_id))
                    conn.commit()
                    return user_id
        except Exception as e:
            logger.error(f"Errore creazione utente: {e}"); raise

    def get_utente_by_email(self, email):
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, email, password_hash, ruolo, azienda FROM utenti")
                    rows = cur.fetchall()
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
        except Exception as e: return None

    def get_utente_by_id(self, user_id: int):
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, email, password_hash, ruolo, azienda FROM utenti WHERE id = %s", (user_id,))
                    row = cur.fetchone()
            if not row: return None
            email_dec = self.vault.decrypt_data(row[1])
            azienda_dec = self.vault.decrypt_data(row[4]) if row[4] else None
            return {"id": row[0], "email": email_dec.decode() if isinstance(email_dec, bytes) else email_dec, 
                    "password_hash": row[2], "ruolo": row[3], "azienda": azienda_dec.decode() if isinstance(azienda_dec, bytes) else azienda_dec}
        except: return None

    def supervisione_admin_metriche_globali(self):
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT email, ruolo, azienda, data_creazione FROM utenti", conn)
                if df.empty: return df
                def _dec(v):
                    if v is None: return None
                    dec = self.vault.decrypt_data(v)
                    return dec.decode() if isinstance(dec, bytes) else dec
                df["email"] = df["email"].apply(_dec); df["azienda"] = df["azienda"].apply(_dec)
                return df
        except: return pd.DataFrame()

    def recupera_log_caricamenti_admin(self):
        try:
            with self._get_conn() as conn:
                return pd.read_sql_query("SELECT * FROM log_caricamenti ORDER BY timestamp DESC", conn)
        except: return pd.DataFrame()

    def registra_caricamento(self, user_id, contesto, nome_file):
        try:
            utente = self.get_utente_by_id(user_id)
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO log_caricamenti (user_id, azienda, contesto, nome_file) VALUES (%s, %s, %s, %s)", 
                               (user_id, utente["azienda"], contesto, nome_file))
                    conn.commit()
        except Exception as e: logger.error(f"Errore: {e}")

    def salva_asset(self, user_id, nome_asset, rischio, **kwargs):
        try:
            utente = self.get_utente_by_id(user_id)
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO asset_logs (user_id, company_id, nome, tipo, rischio, momentum, volatilita) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                               (user_id, utente["azienda"], nome_asset, kwargs.get('tipo'), rischio, kwargs.get('momentum'), kwargs.get('volatilita')))
                    conn.commit()
        except Exception as e: logger.error(f"Errore: {e}")

    def calcola_e_salva_kpi_correnti(self, user_id):
        """ MODULO 2: Analisi Predittiva con sintassi PostgreSQL """
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    # Presente (Ultima ora)
                    cur.execute("SELECT AVG(rischio), COUNT(id) FROM asset_logs WHERE user_id = %s AND timestamp >= NOW() - INTERVAL '1 hour'", (user_id,))
                    res_recent = cur.fetchone()
                    # Storico (Ultime 24 ore)
                    cur.execute("SELECT AVG(rischio) FROM asset_logs WHERE user_id = %s AND timestamp < NOW() - INTERVAL '1 hour' AND timestamp >= NOW() - INTERVAL '24 hours'", (user_id,))
                    res_hist = cur.fetchone()
                    
            rischio_recente = res_recent[0] if res_recent[0] is not None else 0
            rischio_storico = res_hist[0] if res_hist[0] is not None else rischio_recente

            if res_recent[1] == 0: return {"solidita": 100, "trend": "Stabile", "variazione": 0, "rischio_medio": 0}

            variazione = round(rischio_recente - rischio_storico, 2)
            solidita = max(min(round(100 - (rischio_recente * 10), 1), 100), 0)
            trend = "In Peggioramento" if variazione > 0.5 else "In Miglioramento" if variazione < -0.5 else "Stabile"

            return {"solidita": solidita, "rischio_medio": round(rischio_recente, 2), "trend": trend, "variazione": variazione}
        except Exception as e: logger.error(f"Errore KPI: {e}"); return {"solidita": 0, "trend": "Errore"}

    def recupera_attivita_globale(self):
        """
        Recupera gli ultimi log di sistema combinando caricamenti e attività sugli asset.
        """
        try:
            with self._get_conn() as conn:
                query = """
                    SELECT timestamp, azienda, contesto as attivita, nome_file as dettaglio 
                    FROM log_caricamenti
                    UNION ALL
                    SELECT timestamp, company_id as azienda, 'Salvataggio Asset' as attivita, nome as dettaglio
                    FROM asset_logs
                    ORDER BY timestamp DESC
                    LIMIT 50
                """
                df = pd.read_sql_query(query, conn)
                
                def _dec(v):
                    if v is None: return "N/D"
                    try:
                        dec = self.vault.decrypt_data(v)
                        return dec.decode() if isinstance(dec, bytes) else dec
                    except:
                        return v
                
                if not df.empty and "azienda" in df.columns:
                    df["azienda"] = df["azienda"].apply(_dec)
                
                return df
        except Exception as e:
            logger.error(f"❌ Errore nel recupero attività globale: {e}")
            return pd.DataFrame(columns=["timestamp", "azienda", "attivita", "dettaglio"])

    def reset_password_tracciato(self, email, nuova_password):
        """Reset della password con registrazione dell'evento nei log di sicurezza."""
        try:
            # 1. Troviamo l'utente
            utente = self.get_utente_by_email(email)
            if not utente:
                return False
            
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    # 2. Aggiorniamo la password
                    nuovo_hash = bcrypt.hashpw(nuova_password.encode(), bcrypt.gensalt()).decode()
                    cur.execute(
                        "UPDATE utenti SET password_hash = %s WHERE id = %s",
                        (nuovo_hash, utente["id"])
                    )
                    
                    # 3. REGISTRIAMO LA TRACCIA (Data e Ora sono automatici nel DB)
                    cur.execute(
                        "INSERT INTO security_logs (user_id, azione) VALUES (%s, %s)",
                        (utente["id"], "RESET PASSWORD EFFETTUATO")
                    )
                    
                    conn.commit()
                    logger.info(f"🔐 Sicurezza: Password resettata per utente ID {utente['id']}")
                    return True
        except Exception as e:
            logger.error(f"❌ Errore durante il reset tracciato: {e}")
            return False