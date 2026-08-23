import sqlite3
import datetime
import os
import logging
import pandas as pd
import bcrypt
from core.secure_vault import SecureVault

logger = logging.getLogger("RGD-Alpha.Database")


class DatabaseAziendale:
    """
    Architettura di Persistenza Enterprise Criptata RGD-ALPHA.
    Sincronizzato con SecureVault per la cifratura dei dati a riposo.
    Multi-tenant: 1 utente = 1 azienda, isolamento totale dei dati.
    Include funzioni analitiche avanzate per KPI e pannello Admin di supervisione.
    """

    def __init__(self, db_folder="data/db", db_name="azienda.db"):
        try:
            os.makedirs(db_folder, exist_ok=True)
            self.db_path = os.path.join(db_folder, db_name)

            self.vault = SecureVault()

            self.crea_tabelle()
            logger.info(f"🛡️ Database RGD-Alpha (SECURE MODE) pronto: {self.db_path}")
        except Exception as e:
            logger.critical(f"❌ Fallimento critico database: {e}")
            raise

    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    # =========================
    #   CREAZIONE TABELLE
    # =========================
    def crea_tabelle(self):
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS utenti (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        ruolo TEXT NOT NULL,
                        azienda TEXT,
                        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS asset_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        company_id TEXT NOT NULL,
                        nome TEXT NOT NULL,
                        tipo TEXT,
                        rischio REAL NOT NULL,
                        momentum TEXT,
                        volatilita REAL,
                        valore_extra REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES utenti(id)
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS storico_kpi (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        company_id TEXT NOT NULL,
                        kpi_nome TEXT NOT NULL,
                        valore REAL NOT NULL,
                        data_rilevazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES utenti(id)
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS log_caricamenti (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        azienda TEXT,
                        contesto TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        nome_file TEXT,
                        FOREIGN KEY (user_id) REFERENCES utenti(id)
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS password_tokens (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email_enc TEXT NOT NULL,
                        token TEXT NOT NULL,
                        scadenza TIMESTAMP NOT NULL,
                        usato INTEGER DEFAULT 0
                    )
                """)

                conn.commit()
        except Exception as e:
            logger.error(f"❌ Errore creazione schema: {e}")
            raise

    # =========================
    #   UTENTI / AUTENTICAZIONE
    # =========================
    def crea_utente(self, email, password, ruolo="user", azienda=None):
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()

                email_enc = self.vault.encrypt_data(email)
                password_hash = bcrypt.hashpw(
                    password.encode(), bcrypt.gensalt()
                ).decode()

                cursor.execute(
                    """
                    INSERT INTO utenti (email, password_hash, ruolo, azienda)
                    VALUES (?, ?, ?, ?)
                """,
                    (email_enc, password_hash, ruolo, None),
                )
                user_id = cursor.lastrowid

                if azienda is None:
                    azienda = f"AZ-{user_id}"

                azienda_enc = self.vault.encrypt_data(azienda)

                cursor.execute(
                    """
                    UPDATE utenti SET azienda = ?
                    WHERE id = ?
                """,
                    (azienda_enc, user_id),
                )

                conn.commit()
                return user_id
        except Exception as e:
            logger.error(f"Errore creazione utente: {e}")
            raise

    def get_utente_by_email(self, email):
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    "SELECT id, email, password_hash, ruolo, azienda FROM utenti"
                )
                rows = cursor.fetchall()

            for row in rows:
                try:
                    email_dec = self.vault.decrypt_data(row[1])
                    if isinstance(email_dec, bytes):
                        email_dec = email_dec.decode()

                    if email_dec.lower() == email.lower():
                        azienda_dec = (
                            self.vault.decrypt_data(row[4]) if row[4] else None
                        )
                        if isinstance(azienda_dec, bytes):
                            azienda_dec = azienda_dec.decode()

                        return {
                            "id": row[0],
                            "email": email_dec,
                            "password_hash": row[2],
                            "ruolo": row[3],
                            "azienda": azienda_dec,
                        }
                except:
                    continue
            return None
        except Exception as e:
            logger.error(f"Errore recupero utente by email: {e}")
            return None

    def get_utente_by_id(self, user_id: int):
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """
                    SELECT id, email, password_hash, ruolo, azienda
                    FROM utenti WHERE id = ?
                """,
                    (user_id,),
                )
                row = cursor.fetchone()

            if not row:
                return None

            return {
                "id": row[0],
                "email": self.vault.decrypt_data(row[1]),
                "password_hash": row[2],
                "ruolo": row[3],
                "azienda": self.vault.decrypt_data(row[4]) if row[4] else None,
            }
        except Exception as e:
            logger.error(f"Errore recupero utente by id: {e}")
            return None

    def get_tutti_gli_utenti(self):
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT * FROM utenti", conn)

            if df.empty:
                return df

            df["email"] = df["email"].apply(self.vault.decrypt_data)
            df["azienda"] = df["azienda"].apply(self.vault.decrypt_data)
            return df
        except Exception as e:
            logger.error(f"Errore recupero utenti: {e}")
            return pd.DataFrame()

    # =========================
    #   ASSET / LOGICHE AZIENDALI
    # =========================
    def get_azienda_per_utente(self, user_id: int):
        utente = self.get_utente_by_id(user_id)
        if not utente:
            return None
        return utente["azienda"]

    def salva_asset(self, user_id, nome_asset, rischio, **kwargs):
        try:
            azienda = self.get_azienda_per_utente(user_id)
            if azienda is None:
                raise ValueError("Nessuna azienda associata all'utente.")

            company_id_secure = self.vault.encrypt_data(str(azienda))
            nome_secure = self.vault.encrypt_data(str(nome_asset))

            tipo_asset = kwargs.get("tipo", "GenericAsset")
            momentum = kwargs.get("momentum", "Stabile")
            volatilita = kwargs.get("volatilita", 0.0)
            valore_extra = kwargs.get("valore_extra", 0.0)

            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO asset_logs (
                        user_id, company_id, nome, tipo, rischio, momentum, volatilita, valore_extra
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        user_id,
                        company_id_secure,
                        nome_secure,
                        tipo_asset,
                        rischio,
                        momentum,
                        volatilita,
                        valore_extra,
                    ),
                )
        except Exception as e:
            logger.error(f"❌ Errore salvataggio asset {nome_asset}: {e}")

    def recupera_asset_per_utente(self, user_id: int):
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query(
                    "SELECT * FROM asset_logs WHERE user_id = ? ORDER BY id DESC",
                    conn,
                    params=(user_id,),
                )

            if df.empty:
                return df

            df["company_id"] = df["company_id"].apply(self.vault.decrypt_data)
            df["nome"] = df["nome"].apply(self.vault.decrypt_data)
            return df
        except Exception as e:
            logger.error(f"Errore recupero asset per utente: {e}")
            return pd.DataFrame()

    def recupera_asset_per_azienda(self, user_id: int):
        return self.recupera_asset_per_utente(user_id)

    def recupera_attivita_globale(self, solo_admin=False, user_id=None):
        try:
            with self._get_conn() as conn:
                if solo_admin:
                    df = pd.read_sql_query(
                        "SELECT id, user_id, company_id, nome, rischio, timestamp FROM asset_logs ORDER BY id DESC",
                        conn,
                    )
                else:
                    if user_id is None:
                        return pd.DataFrame()
                    df = pd.read_sql_query(
                        "SELECT id, user_id, company_id, nome, rischio, timestamp FROM asset_logs WHERE user_id = ? ORDER BY id DESC",
                        conn,
                        params=(user_id,),
                    )

            if not df.empty:
                df["company_id"] = df["company_id"].apply(self.vault.decrypt_data)
                df["nome"] = df["nome"].apply(self.vault.decrypt_data)

            return df
        except Exception as e:
            logger.error(f"Errore recupero log globali: {e}")
            return pd.DataFrame()

    # ==========================================
    #   CALCOLO MATEMATICO CENTRALIZZATO KPI
    # ==========================================
    def calcola_e_salva_kpi_correnti(self, user_id: int):
        try:
            azienda = self.get_azienda_per_utente(user_id)
            if not azienda:
                return None

            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT rischio, volatilita FROM asset_logs 
                    WHERE id IN (
                        SELECT MAX(id) FROM asset_logs WHERE user_id = ? GROUP BY nome
                    )
                """,
                    (user_id,),
                )
                rows = cursor.fetchall()

            if not rows:
                return {"rischio_medio": 0.0, "solidita": 100.0, "impatto_30gg": 0.0}

            tot_rischio = sum(r[0] for r in rows)
            tot_volatilita = sum(r[1] if r[1] else 0.0 for r in rows)
            conteggio = len(rows)

            rischio_medio = round(tot_rischio / conteggio, 2)
            solidita = round(max(0.0, min(100.0, 100.0 - (rischio_medio * 9.5))), 1)
            impatto_30gg = round((tot_volatilita / conteggio) * rischio_medio * 1.5, 2)

            self.salva_kpi(user_id, "Rischio Medio", rischio_medio)
            self.salva_kpi(user_id, "Solidità Operativa", solidita)
            self.salva_kpi(user_id, "Impatto 30gg", impatto_30gg)

            return {
                "rischio_medio": rischio_medio,
                "solidita": solidita,
                "impatto_30gg": impatto_30gg,
            }
        except Exception as e:
            logger.error(f"❌ Errore nel calcolo centralizzato dei KPI: {e}")
            return {"rischio_medio": 5.0, "solidita": 50.0, "impatto_30gg": 5.0}

    # =========================
    #   KPI HISTORIC ACTIONS
    # =========================
    def salva_kpi(self, user_id: int, kpi_nome: str, valore: float):
        try:
            azienda = self.get_azienda_per_utente(user_id)
            if azienda is None:
                raise ValueError("Nessuna azienda associata all'utente.")

            company_id_secure = self.vault.encrypt_data(str(azienda))

            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO storico_kpi (user_id, company_id, kpi_nome, valore)
                    VALUES (?, ?, ?, ?)
                """,
                    (user_id, company_id_secure, kpi_nome, valore),
                )
        except Exception as e:
            logger.error(f"Errore salvataggio KPI {kpi_nome}: {e}")

    def recupera_kpi_per_utente(self, user_id: int):
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query(
                    "SELECT * FROM storico_kpi WHERE user_id = ? ORDER BY data_rilevazione DESC",
                    conn,
                    params=(user_id,),
                )

            if df.empty:
                return df

            df["company_id"] = df["company_id"].apply(self.vault.decrypt_data)
            return df
        except Exception as e:
            logger.error(f"Errore recupero KPI per utente: {e}")
            return pd.DataFrame()

    # ==========================================
    #   SUPERVISIONE ADMIN
    # ==========================================
    def supervisione_admin_metriche_globali(self):
        try:
            with self._get_conn() as conn:
                df_clienti = pd.read_sql_query(
                    "SELECT id, email, azienda, ruolo FROM utenti WHERE ruolo != 'admin'",
                    conn,
                )
                df_logs = pd.read_sql_query(
                    "SELECT user_id, rischio, volatilita FROM asset_logs", conn
                )
                df_uploads = pd.read_sql_query(
                    "SELECT user_id, COUNT(id) as totale_caricamenti FROM log_caricamenti GROUP BY user_id",
                    conn,
                )

            if df_clienti.empty:
                return pd.DataFrame(
                    columns=[
                        "User ID",
                        "Email Cliente",
                        "Azienda",
                        "Asset Attivi",
                        "Rischio Medio",
                        "File Caricati",
                    ]
                )

            df_clienti["email"] = df_clienti["email"].apply(self.vault.decrypt_data)
            df_clienti["azienda"] = df_clienti["azienda"].apply(self.vault.decrypt_data)

            riepilogo = []
            for _, row in df_clienti.iterrows():
                u_id = row["id"]
                logs_utente = df_logs[df_logs["user_id"] == u_id]
                uploads_utente = df_uploads[df_uploads["user_id"] == u_id]

                asset_attivi = len(logs_utente)
                rischio_medio = (
                    round(logs_utente["rischio"].mean(), 2) if asset_attivi > 0 else 0.0
                )
                file_caricati = (
                    int(uploads_utente["totale_caricamenti"].iloc[0])
                    if not uploads_utente.empty
                    else 0
                )

                riepilogo.append(
                    {
                        "User ID": u_id,
                        "Email Cliente": row["email"],
                        "Azienda": row["azienda"],
                        "Asset Attivi": asset_attivi,
                        "Rischio Medio": rischio_medio,
                        "File Caricati": file_caricati,
                    }
                )

            return pd.DataFrame(riepilogo)
        except Exception as e:
            logger.error(f"❌ Errore durante la supervisione globale dell'Admin: {e}")
            return pd.DataFrame()

    # =========================
    #   LOG CARICAMENTI
    # =========================
    def registra_caricamento(self, user_id: int, contesto: str, nome_file: str):
        try:
            azienda = self.get_azienda_per_utente(user_id)
            if azienda is None:
                raise ValueError("Nessuna azienda associata all'utente.")

            azienda_sec = self.vault.encrypt_data(str(azienda))
            file_sec = self.vault.encrypt_data(str(nome_file))

            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO log_caricamenti (user_id, azienda, contesto, nome_file)
                    VALUES (?, ?, ?, ?)
                """,
                    (user_id, azienda_sec, contesto, file_sec),
                )
        except Exception as e:
            logger.error(f"Errore log admin: {e}")

    def recupera_log_caricamenti_per_utente(self, user_id: int):
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query(
                    "SELECT * FROM log_caricamenti WHERE user_id = ? ORDER BY timestamp DESC",
                    conn,
                    params=(user_id,),
                )

            if df.empty:
                return df

            df["azienda"] = df["azienda"].apply(self.vault.decrypt_data)
            df["nome_file"] = df["nome_file"].apply(self.vault.decrypt_data)
            return df
        except Exception as e:
            logger.error(f"Errore recupero log caricamenti per utente: {e}")
            return pd.DataFrame()

    def recupera_log_caricamenti_admin(self):
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query(
                    "SELECT * FROM log_caricamenti ORDER BY timestamp DESC", conn
                )

            if df.empty:
                return df

            df["azienda"] = df["azienda"].apply(self.vault.decrypt_data)
            df["nome_file"] = df["nome_file"].apply(self.vault.decrypt_data)
            return df
        except Exception as e:
            logger.error(f"Errore recupero log caricamenti admin: {e}")
            return pd.DataFrame()
