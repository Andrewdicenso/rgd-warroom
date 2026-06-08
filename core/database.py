import psycopg2
import datetime
import os
import logging
import pandas as pd
import bcrypt
from core.secure_vault import SecureVault
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("RGD-Alpha.Database")


class DatabaseAziendale:
    """
    Architettura di Persistenza Enterprise Criptata RGD-ALPHA.
    Sincronizzato con SecureVault per la cifratura dei dati a riposo.
    Multi-tenant: 1 utente = 1 azienda, isolamento totale dei dati.
    Collegato esternamente su Supabase (PostgreSQL).
    """

    def __init__(self):
        try:
            # Prendiamo il link magico dal file .env
            self.db_url = os.getenv("DATABASE_URL")
            
            # Inizializzazione Vault (Auto-configurato con vault.key)
            self.vault = SecureVault()

            # Creiamo le tabelle su Supabase se non esistono già
            self.crea_tabelle()
            logger.info("⚡ Database RGD-Alpha su Supabase pronto e connesso!")
        except Exception as e:
            logger.critical(f"❌ Fallimento critico database esterno: {e}")
            raise

    # Connessione centralizzata a Supabase
    def _get_conn(self):
        return psycopg2.connect(self.db_url)

    # =========================
    #   CREAZIONE TABELLE
    # =========================
    def crea_tabelle(self):
        """Inizializza lo schema garantendo l'integrità dei dati criptati e l'isolamento per utente."""
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cursor:

                    # 1. Tabella Utenti (MASTER)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS utenti (
                            id SERIAL PRIMARY KEY,
                            email TEXT UNIQUE NOT NULL,
                            password_hash TEXT NOT NULL,
                            ruolo TEXT NOT NULL,
                            azienda TEXT,
                            data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # 2. Tabella Asset Logs
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS asset_logs (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            company_id TEXT NOT NULL,
                            nome TEXT NOT NULL,
                            tipo TEXT,
                            rischio REAL NOT NULL,
                            momentum TEXT,
                            volatilita REAL,
                            valore_extra REAL,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES utenti(id)
                        )
                    """)

                    # 3. Tabella Storico KPI
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS storico_kpi (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            company_id TEXT NOT NULL,
                            kpi_nome TEXT NOT NULL,
                            valore REAL NOT NULL,
                            data_rilevazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES utenti(id)
                        )
                    """)

                    # 4. Log Caricamenti
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS log_caricamenti (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            azienda TEXT,
                            contesto TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            nome_file TEXT,
                            FOREIGN KEY (user_id) REFERENCES utenti(id)
                        )
                    """)

                    conn.commit()
        except Exception as e:
            logger.error(f"❌ Errore creazione schema su Supabase: {e}")
            raise

    # =========================
    #   UTENTI / AUTENTICAZIONE
    # =========================
    def crea_utente(self, email, password, ruolo="user", azienda=None):
        """Crea un nuovo utente e gestisce l'azienda automatica."""
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cursor:

                    email_enc = self.vault.encrypt_data(email)
                    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

                    if azienda is not None:
                        azienda_enc = self.vault.encrypt_data(azienda)
                        cursor.execute("""
                            INSERT INTO utenti (email, password_hash, ruolo, azienda)
                            VALUES (%s, %s, %s, %s) RETURNING id
                        """, (email_enc, password_hash, ruolo, azienda_enc))
                        user_id = cursor.fetchone()[0]
                        conn.commit()
                        return user_id
                    
                    cursor.execute("""
                        INSERT INTO utenti (email, password_hash, ruolo, azienda)
                        VALUES (%s, %s, %s, %s) RETURNING id
                    """, (email_enc, password_hash, ruolo, None))
                    user_id = cursor.fetchone()[0]

                    azienda_generata = f"AZ-{user_id}"
                    azienda_enc = self.vault.encrypt_data(azienda_generata)

                    cursor.execute("""
                        UPDATE utenti SET azienda = %s
                        WHERE id = %s
                    """, (azienda_enc, user_id))

                    conn.commit()
                    return user_id
        except Exception as e:
            logger.error(f"Errore creazione utente: {e}")
            raise

    def get_utente_by_id(self, user_id: int):
        """Recupera un utente tramite il suo ID decriptandone i dati."""
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, email, password_hash, ruolo, azienda FROM utenti WHERE id = %s", (user_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        return {
                            "id": row[0],
                            "email": self.vault.decrypt_data(row[1]),
                            "password_hash": row[2],
                            "ruolo": row[3],
                            "azienda": self.vault.decrypt_data(row[4]) if row[4] else None
                        }
                return None
        except Exception as e:
            logger.error(f"Errore recupero utente per ID {user_id}: {e}")
            return None

    def get_utente_by_email(self, email):
        """Recupera un utente decriptando le email nel database per il confronto."""
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, email, password_hash, ruolo, azienda FROM utenti")
                    rows = cursor.fetchall()

            for row in rows:
                try:
                    email_decriptata = self.vault.decrypt_data(row[1])
                    if email_decriptata.lower() == email.lower():
                        return {
                            "id": row[0],
                            "email": email_decriptata,
                            "password_hash": row[2],
                            "ruolo": row[3],
                            "azienda": self.vault.decrypt_data(row[4]) if row[4] else None
                        }
                except:
                    continue
            return None
        except Exception as e:
            logger.error(f"Errore recupero utente: {e}")
            return None

    def get_tutti_gli_utenti(self):
        """Ritorna tutti gli utenti (per Admin Panel)."""
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

            tipo_asset = kwargs.get('tipo', 'GenericAsset')
            momentum = kwargs.get('momentum', 'Stabile')
            volatilita = kwargs.get('volatilita', 0.0)
            valore_extra = kwargs.get('valore_extra', 0.0)

            with self._get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO asset_logs (
                            user_id, company_id, nome, tipo, rischio, momentum, volatilita, valore_extra
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_id,
                        company_id_secure,
                        nome_secure,
                        tipo_asset,
                        rischio,
                        momentum,
                        volatilita,
                        valore_extra
                    ))
                conn.commit()
        except Exception as e:
            logger.error(f" Errore salvataggio asset {nome_asset}: {e}")

    def recupera_asset_per_utente(self, user_id: int):
        """Recupera gli asset con logica di supervisione Admin/Cliente."""
        try:
            utente = self.get_utente_by_id(user_id)
            if not utente: 
                return pd.DataFrame()
            
            ruolo = utente.get("ruolo")
            with self._get_conn() as conn:
                if ruolo == "admin":
                    query = "SELECT * FROM asset_logs ORDER BY id DESC"
                    df = pd.read_sql_query(query, conn)
                else:
                    query = "SELECT * FROM asset_logs WHERE user_id = %s ORDER BY id DESC"
                    # Corretto l'invio del parametro come lista [] per PostgreSQL
                    df = pd.read_sql_query(query, conn, params=[user_id])

            if not df.empty:
                df['company_id'] = df['company_id'].apply(lambda x: self.vault.decrypt_data(x) if x else "")
                df['nome'] = df['nome'].apply(lambda x: self.vault.decrypt_data(x) if x else "Dato Protetto")
            return df
        except Exception as e:
            logger.error(f"Errore recupero asset: {e}")
            return pd.DataFrame()

    def svuota_dati_azienda(self, user_id: int) -> bool:
        """Elimina in modo sicuro tutti i dati di analisi di un utente specifico."""
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM asset_logs WHERE user_id = %s", (user_id,))
                    cursor.execute("DELETE FROM storico_kpi WHERE user_id = %s", (user_id,))
                    cursor.execute("DELETE FROM log_caricamenti WHERE user_id = %s", (user_id,))
                conn.commit()
                logger.info(f"🗑️ Hard reset completato per l'utente ID: {user_id}")
                return True
        except Exception as e:
            logger.error(f"❌ Errore durante lo svuotamento dati utente {user_id}: {e}")
            return False

    def elimina_singolo_log_caricamento(self, user_id: int, log_id: int) -> bool:
        """Elimina un singolo file caricato dalla cronologia dell'utente."""
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM log_caricamenti WHERE id = %s AND user_id = %s", (log_id, user_id))
                    row_count = cursor.rowcount
                conn.commit()
                return row_count > 0
        except Exception as e:
            logger.error(f"❌ Errore eliminazione log {log_id}: {e}")
            return False

    # ==========================================
    #   CALCOLO MATEMATICO KPI
    # ==========================================
    def calcola_e_salva_kpi_correnti(self, user_id: int):
        try:
            utente = self.get_utente_by_id(user_id)
            if not utente: return None
            
            ruolo, azienda = utente.get("ruolo"), utente.get("azienda")

            with self._get_conn() as conn:
                with conn.cursor() as cursor:
                    if ruolo == "admin" and azienda:
                        azienda_enc = self.vault.encrypt_data(str(azienda))
                        query = "SELECT rischio, volatilita FROM asset_logs WHERE company_id = %s AND id IN (SELECT MAX(id) FROM asset_logs GROUP BY nome)"
                        params = (azienda_enc,)
                    else:
                        query = "SELECT rischio, volatilita FROM asset_logs WHERE user_id = %s AND id IN (SELECT MAX(id) FROM asset_logs GROUP BY nome)"
                        params = (user_id,)
                    
                    cursor.execute(query, params)
                    rows = cursor.fetchall()

            if not rows: return {"rischio_medio": 0.0, "solidita": 100.0, "impatto_30gg": 0.0}

            rischio_medio = round(sum(r[0] for r in rows) / len(rows), 2)
            solidita = round(max(0.0, min(100.0, 100.0 - (rischio_medio * 9.5))), 1)
            impatto_30gg = round((sum(r[1] or 0.0 for r in rows) / len(rows)) * rischio_medio * 1.5, 2)

            self.salva_kpi(user_id, "Rischio Medio", rischio_medio)
            self.salva_kpi(user_id, "Solidità Operativa", solidita)
            self.salva_kpi(user_id, "Impatto 30gg", impatto_30gg)

            return {"rischio_medio": rischio_medio, "solidita": solidita, "impatto_30gg": impatto_30gg}
        except Exception as e:
            logger.error(f"Errore KPI: {e}")
            return {"rischio_medio": 5.0, "solidita": 50.0, "impatto_30gg": 5.0}

    def salva_kpi(self, user_id: int, kpi_nome: str, valore: float):
        try:
            azienda = self.get_azienda_per_utente(user_id)
            azienda_enc = self.vault.encrypt_data(str(azienda))
            with self._get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO storico_kpi (user_id, company_id, kpi_nome, valore) VALUES (%s, %s, %s, %s)", (user_id, azienda_enc, kpi_nome, valore))
                conn.commit()
        except Exception as e: 
            logger.error(f"Errore salva KPI: {e}")

    def recupera_kpi_per_utente(self, user_id: int):
        try:
            utente = self.get_utente_by_id(user_id)
            azienda_enc = self.vault.encrypt_data(str(utente["azienda"]))
            with self._get_conn() as conn:
                if utente["ruolo"] == "admin":
                    query = "SELECT * FROM storico_kpi WHERE company_id = %s ORDER BY data_rilevazione DESC"
                    df = pd.read_sql_query(query, conn, params=[azienda_enc])
                else:
                    query = "SELECT * FROM storico_kpi WHERE user_id = %s ORDER BY data_rilevazione DESC"
                    df = pd.read_sql_query(query, conn, params=[user_id])
            if not df.empty: 
                df['company_id'] = df['company_id'].apply(self.vault.decrypt_data)
            return df
        except Exception as e: 
            return pd.DataFrame()

    def supervisione_admin_metriche_globali(self):
        """Monitoraggio clienti per Admin."""
        try:
            with self._get_conn() as conn:
                df_clienti = pd.read_sql_query("SELECT id, email, azienda FROM utenti WHERE ruolo != 'admin'", conn)
                df_logs = pd.read_sql_query("SELECT user_id, rischio FROM asset_logs", conn)
            
            if df_clienti.empty: return pd.DataFrame()

            df_clienti["email"] = df_clienti["email"].apply(self.vault.decrypt_data)
            df_clienti["azienda"] = df_clienti["azienda"].apply(self.vault.decrypt_data)

            res = []
            for _, r in df_clienti.iterrows():
                u_logs = df_logs[df_logs["user_id"] == r["id"]]
                res.append({
                    "Email": r["email"],
                    "Azienda": r["azienda"],
                    "Asset": len(u_logs),
                    "Rischio": round(u_logs["rischio"].mean(), 2) if len(u_logs) > 0 else 0.0
                })
            return pd.DataFrame(res)
        except Exception as e: 
            return pd.DataFrame()

    def registra_caricamento(self, user_id: int, contesto: str, nome_file: str):
        try:
            azienda = self.get_azienda_per_utente(user_id)
            az_enc, f_enc = self.vault.encrypt_data(str(azienda)), self.vault.encrypt_data(str(nome_file))
            with self._get_conn() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO log_caricamenti (user_id, azienda, contesto, nome_file) VALUES (%s, %s, %s, %s)", (user_id, az_enc, contesto, f_enc))
                conn.commit()
        except Exception as e: 
            logger.error(f"Errore log: {e}")

    def recupera_log_caricamenti_per_utente(self, user_id: int):
        try:
            utente = self.get_utente_by_id(user_id)
            az_enc = self.vault.encrypt_data(str(utente["azienda"]))
            with self._get_conn() as conn:
                if utente["ruolo"] == "admin":
                    query = "SELECT * FROM log_caricamenti WHERE azienda = %s ORDER BY timestamp DESC"
                    df = pd.read_sql_query(query, conn, params=[az_enc])
                else:
                    query = "SELECT * FROM log_caricamenti WHERE user_id = %s ORDER BY timestamp DESC"
                    df = pd.read_sql_query(query, conn, params=[user_id])
            if not df.empty:
                df["azienda"] = df["azienda"].apply(self.vault.decrypt_data)
                df["nome_file"] = df["nome_file"].apply(self.vault.decrypt_data)
            return df
        except Exception as e:
            return pd.DataFrame()

    def recupera_log_caricamenti_admin(self):
        try:
            with self._get_conn() as conn:
                df = pd.read_sql_query("SELECT * FROM log_caricamenti ORDER BY timestamp DESC", conn)

            if not df.empty:
                df["azienda"] = df["azienda"].apply(lambda x: self.vault.decrypt_data(x) if x else "N/A")
                df["nome_file"] = df["nome_file"].apply(lambda x: self.vault.decrypt_data(x) if x else "N/A")
            return df
        except Exception as e:
            logger.error(f"Errore recupero log caricamenti admin: {e}")
            return pd.DataFrame()