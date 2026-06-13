import pandas as pd
import os
import logging
import io
from core.secure_vault import SecureVault
from core.entities import AssetDiMercato, AssetDiValore, AssetDiRisorsa, AssetStrategico
from core.database import DatabaseAziendale

logger = logging.getLogger("RGD-Alpha.Ingestor")

class IngestoreDati:
    def __init__(self, key_path="core/security/vault.key"):
        self.vault = SecureVault(key_path=key_path)
        self.db = DatabaseAziendale()
        
        self.mappa_sinonimi = {
            'quantita': ['quantita', 'pezzi', 'qta', 'stock', 'unita', 'giacenza', 'rimanenza', 'output_totale', 'amount', 'quantity'],
            'valore': ['prezzo', 'importo', 'lordo', 'valore', 'costo', 'ammontare', 'prezzo_acquisto', 'valore_extra', 'price', 'value'],
            'rischio': ['rischio', 'impatto', 'criticita', 'priorita', 'risk', 'pericolo', 'urgenza'],
            'ore': ['ore', 'tempo', 'durata', 'h', 'lavorato', 'ore_effettive', 'hours'],
            'inefficienze': ['ferie', 'festivita', 'assenze', 'permessi', 'ritardi', 'micropause', 'idle']
        }

    def _pulisce_intestazioni(self, df):
        """Standardizzazione universale delle colonne."""
        def clean_col(c):
            return str(c).strip().lower().replace(' ', '_').replace('à', 'a').replace('ò', 'o').replace('è', 'e').replace('é', 'e').replace('ù', 'u')
        
        df.columns = [clean_col(c) for c in df.columns]
        return df

    def _leggi_file_universale(self, file_path):
        """Tenta di leggere il file gestendo separatori e encoding europei."""
        estensione = os.path.splitext(file_path)[1].lower()
        
        if estensione in ['.xls', '.xlsx']:
            return pd.read_excel(file_path)
        
        if estensione == '.csv':
            # Prova i separatori più comuni (Italia/EU usa ';', USA/UK usa ',')
            for sep in [',', ';', '\t', '|']:
                try:
                    df = pd.read_csv(file_path, sep=sep, encoding='utf-8-sig', on_bad_lines='skip')
                    if len(df.columns) > 1: # Se ha trovato più di una colonna, il separatore è quello giusto
                        return df
                except:
                    continue
            
            # Fallback finale con rilevamento automatico
            try:
                return pd.read_csv(file_path, sep=None, engine='python', encoding='latin-1')
            except Exception as e:
                logger.error(f"Impossibile leggere il CSV: {e}")
                return pd.DataFrame()
        
        return pd.DataFrame()

    def elabora_file(self, file_path, company_id):
        asset_list = []
        df = self._leggi_file_universale(file_path)

        if df.empty:
            logger.error("File vuoto o formato non supportato.")
            return asset_list

        # Pulizia intestazioni
        df = self._pulisce_intestazioni(df)

        # RILEVAMENTO SETTORE (Migliorato: non blocca più se non riconosce nulla)
        settore_nome, ClasseAsset = self._auto_rilevamento_settore(df.columns)
        self.db.registra_caricamento(company_id, f"Analisi {settore_nome}", os.path.basename(file_path))

        for _, row in df.iterrows():
            try:
                # Creiamo un dizionario di base con i dati della riga
                dati_riga = row.to_dict()
                
                # MAPPATURA INTELLIGENTE: Se la colonna 'nome' non esiste, cerchiamo sinonimi o usiamo la prima colonna disponibile
                dati_riga['nome'] = self._estrai_nome(row)
                dati_riga['rischio'] = self._valida_numerico(self._estrai_dato(row, 'rischio', 5.0))
                dati_riga['valore_extra'] = self._valida_numerico(self._estrai_dato(row, 'valore', 0.0))
                dati_riga['company_id'] = company_id
                dati_riga['output_totale'] = self._valida_numerico(self._estrai_dato(row, 'quantita', 0))

                # Gestione inefficienze
                for ineff in self.mappa_sinonimi['inefficienze']:
                    dati_riga[ineff] = self._valida_numerico(row.get(ineff, 0))

                # Creazione Asset dinamica
                nuovo_asset = ClasseAsset(**dati_riga)
                asset_list.append(nuovo_asset)
            except Exception as e:
                logger.debug(f"Riga saltata, ma il processo continua: {e}")

        return asset_list

    def _auto_rilevamento_settore(self, colonne):
        col = set(colonne)
        # Logica di rilevamento... (mantenuta quella esistente ma con fallback su General)
        if any(k in col for k in ['cantiere', 'commessa', 'ponteggio']): return "EDILE", AssetStrategico
        if any(k in col for k in ['collezione', 'taglia', 'stagione']): return "FASHION", AssetDiMercato
        if any(k in col for k in ['fattura', 'lordo', 'partita_iva']): return "FINANCE", AssetDiValore
        if any(k in col for k in ['magazzino', 'vettore', 'stock']): return "LOGISTICS", AssetDiMercato
        return "GENERAL", AssetStrategico

    def _estrai_nome(self, row):
        # Cerca i sinonimi di nome, se non trova nulla prende il valore della prima cella
        for k in ['nome', 'prodotto', 'asset', 'descrizione', 'cantiere', 'cliente', 'fornitore', 'item']:
            if k in row and not pd.isna(row[k]):
                return str(row[k])
        return f"Asset_{datetime.now().strftime('%H%M%S')}" # Nome autogenerato per non bloccare mai

    def _estrai_dato(self, row, categoria_chiave, default=0):
        for sinonimo in self.mappa_sinonimi.get(categoria_chiave, []):
            if sinonimo in row and not pd.isna(row[sinonimo]):
                return row[sinonimo]
        return default

    def _valida_numerico(self, val):
        if pd.isna(val): return 0.0
        try:
            return float(str(val).replace(',', '.'))
        except:
            return 0.0