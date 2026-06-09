import pandas as pd
import os
from datetime import datetime
import logging
from core.secure_vault import SecureVault
from core.entities import AssetDiMercato, AssetDiValore, AssetDiRisorsa, AssetStrategico
from core.database import DatabaseAziendale

logger = logging.getLogger("RGD-Alpha.Ingestor")

class IngestoreDati:
    """
    INGESTORE ENTERPRISE RGD-ALPHA v2.0:
    Sistema adattivo con auto-correzione, mappatura multi-settore.
    """
    def __init__(self, key_path="core/security/vault.key"):
        # Gestione sicura del Vault per evitare crash se il file manca in locale
        try:
            self.vault = SecureVault(key_path=key_path)
        except:
            self.vault = None
            logger.warning("Vault non inizializzato: procedo in modalità standard.")
            
        self.db = DatabaseAziendale()
        
        self.mappa_sinonimi = {
            'quantita': ['quantita', 'pezzi', 'qta', 'stock', 'unita', 'giacenza', 'rimanenza', 'output_totale', 'prodotti'],
            'valore': ['prezzo', 'importo', 'lordo', 'valore', 'costo', 'ammontare', 'acquisto'],
            'rischio': ['rischio', 'impatto', 'criticita', 'priorita', 'risk', 'pericolo'],
            'ore': ['ore', 'tempo', 'durata', 'h', 'lavorato'],
            'inefficienze': ['ferie', 'festivita', 'assenze', 'permessi', 'ritardi', 'micropause']
        }

    def _pulisce_intestazioni(self, df):
        """Standardizza i nomi delle colonne eliminando spazi e accenti."""
        df.columns = [
            str(c).strip().lower()
            .replace(' ', '_')
            .replace('à', 'a').replace('è', 'e').replace('é', 'e')
            .replace('ì', 'i').replace('ò', 'o').replace('ù', 'u') 
            for c in df.columns
        ]
        return df

    def _valida_dati_critici(self, df):
        if df.empty: return False, "Il file caricato è vuoto."
        nomi_possibili = ['nome', 'descrizione', 'prodotto', 'asset', 'sku', 'cantiere', 'cliente', 'dipendente']
        if not any(col in df.columns for col in nomi_possibili):
            return False, "Struttura file non riconosciuta: manca una colonna identificativa (es. Nome o Asset)."
        return True, "Validazione superata."

    def _auto_rilevamento_settore(self, colonne):
        col = set(colonne)
        if any(k in col for k in ['cantiere', 'commessa', 'ponteggio', 'sicurezza']):
            return "EDILE", AssetStrategico
        if any(k in col for k in ['collezione', 'taglia', 'stagione']):
            return "FASHION", AssetDiMercato
        if any(k in col for k in self.mappa_sinonimi['inefficienze']) or 'dipendente' in col:
            return "PRODUTTIVITA", AssetDiRisorsa 
        if any(k in col for k in ['fattura', 'iban', 'partita_iva']):
            return "FINANCE", AssetDiValore
        return "GENERAL", AssetStrategico

    def _estrai_dato(self, row, categoria_chiave, default=0.0):
        for sinonimo in self.mappa_sinonimi.get(categoria_chiave, []):
            if sinonimo in row and not pd.isna(row[sinonimo]):
                return self._valida_numerico(row[sinonimo])
        return default

    def _estrai_nome(self, row):
        for k in ['nome', 'prodotto', 'asset', 'descrizione', 'cantiere', 'dipendente']:
            if k in row and not pd.isna(row[k]): return str(row[k])
        return "Asset_Generico"

    def _valida_numerico(self, val):
        if pd.isna(val): return 0.0
        try:
            return float(str(val).replace(',', '.'))
        except:
            return 0.0

    def elabora_csv(self, file_source, company_id):
        """
        Alias per mantenere compatibilità con interface.py e gestire 
        sia oggetti file (Streamlit) che percorsi (Terminal).
        """
        # Se è un oggetto file di Streamlit, usiamo il nome, altrimenti il path
        file_path = getattr(file_source, 'name', str(file_source))
        return self.elabora_file(file_source, company_id)

    def elabora_file(self, file_input, company_id):
        asset_list = []
        try:
            # Rilevamento estensione dinamico
            nome_file = getattr(file_input, 'name', str(file_input))
            ext = os.path.splitext(nome_file)[1].lower()

            if ext == '.csv':
                df = pd.read_csv(file_input, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
            elif ext in ['.xls', '.xlsx']:
                df = pd.read_excel(file_input)
            else:
                return []

            df = self._pulisce_intestazioni(df)
            valido, msg = self._valida_dati_critici(df)
            if not valido: return []

            settore_nome, ClasseAsset = self._auto_rilevamento_settore(df.columns)
            
            # Registrazione log nel database reale
            try:
                self.db.registra_caricamento(company_id, f"Analisi {settore_nome}", nome_file)
            except:
                pass

            for _, row in df.iterrows():
                # Costruiamo il dizionario dati con protezione contro i valori mancanti
                dati_riga = {
                    'nome': self._estrai_nome(row),
                    'rischio': self._estrai_dato(row, 'rischio', 5.0),
                    'valore_extra': self._estrai_dato(row, 'valore', 0.0),
                    'output_totale': self._estrai_dato(row, 'quantita', 0.0),
                    'company_id': company_id,
                    'timestamp': datetime.now()
                }
                
                # Inserimento dinamico inefficienze (evita il crash se la colonna non esiste)
                for ineff in self.mappa_sinonimi['inefficienze']:
                    dati_riga[ineff] = self._valida_numerico(row.get(ineff, 0.0))

                try:
                    # Creazione istanza asset basata sul settore rilevato
                    nuovo_asset = ClasseAsset(**dati_riga)
                    asset_list.append(nuovo_asset)
                except Exception as e:
                    continue

        except Exception as e:
            logger.error(f"Errore critico ingestore: {e}")
        
        return asset_list