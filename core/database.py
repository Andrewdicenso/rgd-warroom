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

            # Inizializzazione Vault (Auto-configurato con vault.key)
            self.vault = SecureVault()

            self.crea_tabelle()
            logger.info(f"️ Database RGD-Alpha pronto: {self.db_path}")
        except Exception as e:
            logger.critical(f"❌ Fallimento critico database: {e}")
            raise

    # Connessione centralizzata
    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    # =========================
    #   CREAZIONE TABELLE
    # =========================
    def crea_tabelle(self):
        """Inizializza lo schema garantendo l'integrità dei dati criptati e l'isolamento per utente."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()

                # 1. Tabella Utenti (MASTER)
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

                # 2. Tabella Asset Logs
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

                # 3. Tabella Storico KPI
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

                # 4. Log Caricamenti
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

                conn.commit()
        except Exception as e:
            logger.error(f"❌ Errore creazione schema: {e}")
            raise

    # =========================
    #   UTENTI / AUTENTICAZIONE
    # =========================

    def crea_utente(self, email, password, ruolo="user", azienda=None):
        """
        Crea un nuovo utente.
        La password viene hashata internamente con bcrypt.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()

                email_enc = self.vault.encrypt_data(email)

                # HASH SICURO DELLA PASSWORD
                password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

                # Inserisco utente senza azienda per ottenere l'id
                cursor.execute("""
                    INSERT INTO utenti (email, password_hash, ruolo, azienda)
                    VALUES (?, ?, ?, ?)
                """, (email_enc, password_hash, ruolo, None))
                user_id = cursor.lastrowid

                # Se non è stata passata un'azienda, ne genero una
                if azienda is None:
                    azienda = f"AZ-{user_id}"

                azienda_enc = self.vault.encrypt_data(azienda)

                # Aggiorno l'azienda dell'utente
                cursor.execute("""
                    UPDATE utenti SET azienda = ?
                    WHERE id = ?
                """, (azienda_enc, user_id))

                conn.commit()
                return user_id
        except Exception as e:
            logger.error(f"Errore creazione utente: {e}")
            raise

    def get_utente_by_email(self, email):
        """Recupera un utente decriptando le email nel database per il confronto."""
        try:
            with self._get_conn() as conn:
                # Prendiamo tutti gli utenti per confrontare l'email decriptata
                cursor = conn.execute("SELECT id, email, password_hash, ruolo, azienda FROM utenti")
                rows = cursor.fetchall()

            for row in rows:
                try:
                    # Decriptiamo l'email salvata nel DB per vedere se coincide con quella inserita
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
                    continue # Se un'email non è criptata o è corrotta, passa alla successiva

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
                conn.execute("""
                    INSERT INTO asset_logs (
                        user_id, company_id, nome, tipo, rischio, momentum, volatilita, valore_extra
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
        except Exception as e:
            logger.error(f" Errore salvataggio asset {nome_asset}: {e}")

        # =========================
    #   ASSET / LOGICHE AZIENDALI CORRETTE (ADMIN READY)
    # =========================
    def recupera_asset_per_utente(self, user_id: int):
        """
        LOGICA DI SUPERVISIONE RGD-ALPHA:
        - Se l'utente è ADMIN: estrae TUTTI i dati di TUTTI i clienti (per AI training e supporto).
        - Se l'utente è CLIENTE: isolamento totale, vede solo i propri asset.
        """
        try:
            utente = self.get_utente_by_id(user_id)
            if not utente: return pd.DataFrame()
            
            ruolo = utente.get("ruolo")

            with self._get_conn() as conn:
                if ruolo == "admin":
                    # TU VEDI TUTTO: Nessun filtro WHERE per la supervisione totale
                    query = "SELECT * FROM asset_logs ORDER BY id DESC"
                    params = ()
                else:
                    # IL CLIENTE È ISOLATO: Vede solo i suoi dati personali
                    query = "SELECT * FROM asset_logs WHERE user_id = ? ORDER BY id DESC"
                    params = (user_id,)

                df = pd.read_sql_query(query, conn, params=params)

            if not df.empty:
                # Decriptazione dati per la tua supervisione e addestramento AI
                df['company_id'] = df['company_id'].apply(lambda x: self.vault.decrypt_data(x) if x else "")
                df['nome'] = df['nome'].apply(lambda x: self.vault.decrypt_data(x) if x else "Dato Protetto")
            
            return df
        except Exception as e:
            logger.error(f"Errore supervisione asset: {e}")
            return pd.DataFrame()
            if not utente: return pd.DataFrame()
            
            ruolo = utente.get("ruolo")

            with self._get_conn() as conn:
                if ruolo == "admin":
                    # TU VEDI TUTTO: Nessun filtro WHERE per la supervisione totale
                    query = "SELECT * FROM asset_logs ORDER BY id DESC"
                    params = ()
                else:
                    # IL CLIENTE È ISOLATO: Vede solo i suoi dati personali
                    query = "SELECT * FROM asset_logs WHERE user_id = ? ORDER BY id DESC"
                    params = (user_id,)

                df = pd.read_sql_query(query, conn, params=params)

            if not df.empty:
                # Decriptazione dati per la tua supervisione e addestramento AI
                df['company_id'] = df['company_id'].apply(lambda x: self.vault.decrypt_data(x) if x else "")
                df['nome'] = df['nome'].apply(lambda x: self.vault.decrypt_data(x) if x else "Dato Protetto")
            
            return df
        except Exception as e:
            logger.error(f"Errore supervisione asset: {e}")
            return pd.DataFrame()

    def recupera_asset_per_azienda(self, user_id: int):
        return self.recupera_asset_per_utente(user_id)

    def recupera_attivita_globale(self, solo_admin=False, user_id=None):
        try:
            with self._get_conn() as conn:
                if solo_admin:
                    df = pd.read_sql_query("SELECT * FROM asset_logs ORDER BY id DESC", conn)
                else:
                    return self.recupera_asset_per_utente(user_id)

            if not df.empty:
                df['company_id'] = df['company_id'].apply(lambda x: self.vault.decrypt_data(x) if x else "")
                df['nome'] = df['nome'].apply(lambda x: self.vault.decrypt_data(x) if x else "Dato Protetto")
            return df
        except Exception as e:
            logger.error(f"Errore attivita globale: {e}")
            return pd.DataFrame()

    # ==========================================
    #   CALCOLO MATEMATICO KPI (FIXED FOR ADMIN)
    # ==========================================

    def calcola_e_salva_kpi_correnti(self, user_id: int):
        try:
            utente = self.get_utente_by_id(user_id)
            if not utente: return None
            
            ruolo, azienda = utente.get("ruolo"), utente.get("azienda")

            with self._get_conn() as conn:
                if ruolo == "admin" and azienda:
                    azienda_enc = self.vault.encrypt_data(str(azienda))
                    query = "SELECT rischio, volatilita FROM asset_logs WHERE company_id = ? AND id IN (SELECT MAX(id) FROM asset_logs GROUP BY nome)"
                    params = (azienda_enc,)
                else:
                    query = "SELECT rischio, volatilita FROM asset_logs WHERE user_id = ? AND id IN (SELECT MAX(id) FROM asset_logs GROUP BY nome)"
                    params = (user_id,)
                
                rows = conn.execute(query, params).fetchall()

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
                conn.execute("INSERT INTO storico_kpi (user_id, company_id, kpi_nome, valore) VALUES (?, ?, ?, ?)", (user_id, azienda_enc, kpi_nome, valore))
        except Exception as e: logger.error(f"Errore salva KPI: {e}")

    def recupera_kpi_per_utente(self, user_id: int):
        try:
            utente = self.get_utente_by_id(user_id)
            azienda_enc = self.vault.encrypt_data(str(utente["azienda"]))
            with self._get_conn() as conn:
                if utente["ruolo"] == "admin":
                    df = pd.read_sql_query("SELECT * FROM storico_kpi WHERE company_id = ? ORDER BY data_rilevazione DESC", conn, params=(azienda_enc,))
                else:
                    df = pd.read_sql_query("SELECT * FROM storico_kpi WHERE user_id = ? ORDER BY data_rilevazione DESC", conn, params=(user_id,))
            if not df.empty: df['company_id'] = df['company_id'].apply(self.vault.decrypt_data)
            return df
        except Exception as e: return pd.DataFrame()

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
        except Exception as e: return pd.DataFrame()

    def registra_caricamento(self, user_id: int, contesto: str, nome_file: str):
        try:
            azienda = self.get_azienda_per_utente(user_id)
            az_enc, f_enc = self.vault.encrypt_data(str(azienda)), self.vault.encrypt_data(str(nome_file))
            with self._get_conn() as conn:
                conn.execute("INSERT INTO log_caricamenti (user_id, azienda, contesto, nome_file) VALUES (?, ?, ?, ?)", (user_id, az_enc, contesto, f_enc))
        except Exception as e: logger.error(f"Errore log: {e}")

    def recupera_log_caricamenti_per_utente(self, user_id: int):
        try:
            utente = self.get_utente_by_id(user_id)
            az_enc = self.vault.encrypt_data(str(utente["azienda"]))
            with self._get_conn() as conn:
                if utente["ruolo"] == "admin":
                    df = pd.read_sql_query("SELECT * FROM log_caricamenti WHERE azienda = ? ORDER BY timestamp DESC", conn, params=(az_enc,))
                else:
                    df = pd.read_sql_query("SELECT * FROM log_caricamenti WHERE user_id = ? ORDER BY timestamp DESC", conn, params=(user_id,))
            if not df.empty:
                df["azienda"] = df["azienda"].apply(self.vault.decrypt_data)
                df["nome_file"] = df["nome_file"].apply(self.vault.decrypt_data)
            return df
        except Exception as e: return pd.DataFrame()