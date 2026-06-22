import difflib
import pandas as pd
import os
from datetime import datetime
import logging
from core.secure_vault import SecureVault
from core.entities import AssetDiMercato, AssetDiValore, AssetDiRelazione, AssetStrategico
from core.database import DatabaseAziendale

logger = logging.getLogger("RGD-Alpha.Ingestor")

class IngestoreDati:
    """
    INGESTORE UNIVERSALE RGD-ALPHA:
    Sistema adattivo con validazione preventiva per prevenire crash.
    """
    def __init__(self, key_path="core/security/vault.key"):
        self.vault = SecureVault(key_path=key_path)
        self.db = DatabaseAziendale()
        
        # Dizionario esteso per mappare i file reali ai campi del sistema
        self.mappa_sinonimi = {
            'quantita': ['quantita', 'pezzi', 'qta', 'stock', 'unita', 'Quantita', 'Giacenza'],
            'valore': ['prezzo', 'importo', 'lordo', 'valore', 'costo', 'ammontare', 'Costo_Unitario', 'prezzo_acquisto'],
            'rischio': ['rischio', 'impatto', 'criticità', 'priorità', 'Rischio_Logistico', 'Risk_Factor'],
            'stato': ['stato', 'condizione', 'status', 'pagamento', 'disponibilita', 'Stato_Qualita']
        }

    def _valida_dati_critici(self, df):
        """
        DATA VALIDATOR: Controlla se il file ha i requisiti minimi per non rompere il sistema.
        Ritorna (True, message) o (False, error_message).
        """
        if df.empty:
            return False, "Il file caricato è vuoto."
        
        # Cerchiamo se esiste almeno una colonna che assomigli a un 'nome' o 'descrizione'
        nomi_possibili = ['nome', 'descrizione', 'prodotto', 'asset', 'Descrizione_Asset', 'SKU']
        colonne_lower = [c.lower() for c in df.columns]
        nomi_lower = [n.lower() for n in nomi_possibili]

        if not any(n in colonne_lower for n in nomi_lower):
            return False, "Non trovo una colonna 'Nome' o 'Prodotto'. Controlla le intestazioni del file."

        return True, "Validazione superata."

    def _auto_rilevamento_settore(self, colonne):
        """Analizza le intestazioni per capire se è Logistica, Finance o Relazioni."""
        colonne_lower = [str(c).lower() for c in colonne]
        
        if any(term in colonne_lower for term in ['fattura', 'iban', 'lordo', 'costo_unitario']):
            return "FINANCE", AssetDiValore
        if any(term in colonne_lower for term in ['bolla', 'ddt', 'magazzino', 'quantita', 'sku', 'ubicazione', 'giacenza']):
            return "LOGISTICS", AssetDiMercato
        if any(term in colonne_lower for term in ['cliente', 'fornitore', 'crm', 'fornitore_origine']):
            return "RELATIONS", AssetDiRelazione
        
        return "GENERAL", AssetStrategico

    def _estrai_dato(self, row, categoria_chiave, default=0):
        """Cerca il dato usando i sinonimi definiti sopra."""
        for sinonimo in self.mappa_sinonimi.get(categoria_chiave, []):
            val = row.get(sinonimo)
            if val is not None and not pd.isna(val):
                return val
        return default

    def elabora_csv(self, file_path, company_id):
        asset_list = [] 
        
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} non trovato.")
            return asset_list

        try:
            # CONTROLLO ESTENSIONE: CSV o EXCEL?
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            else:
                logger.error(f"Formato file non supportato: {file_path}")
                return asset_list
            
            # --- ESECUZIONE VALIDATORE ---
            valido, messaggio = self._valida_dati_critici(df)
            if not valido:
                logger.warning(f"Validazione fallita per {company_id}: {messaggio}")
                return asset_list

            # Rilevamento automatico del reparto
            settore_nome, ClasseAsset = self._auto_rilevamento_settore(df.columns)

            for _, row in df.iterrows():
                dati_riga = row.to_dict()
                # Normalizzazione campi
                dati_riga['id_asset'] = row.get('ID_Movimento', row.get('id', row.get('ID', 'N/D')))
                dati_riga['nome'] = row.get('Descrizione_Asset', row.get('nome', row.get('prodotto')))

                try:
                    nuovo_asset = ClasseAsset(**dati_riga)
                    if hasattr(nuovo_asset, 'genera_kpi_strategici'):
                        nuovo_asset.genera_kpi_strategici()
                    asset_list.append(nuovo_asset)
                except Exception as e:
                    logger.debug(f"Salto riga per errore formato: {e}")

        except Exception as e:
            logger.error(f"Errore critico durante l'elaborazione del file: {e}")

        return asset_list

        # ... (restante codice invariato)

    def _smart_mapping_colonne(self, df):
        """Usa la logica fuzzy per mappare colonne anche se scritte male."""
        mappa_reale = {}
        colonne_file = df.columns.tolist()
        
        for target, sinonimi in self.mappa_sinonimi.items():
                for col in colonne_file:
                # Corrispondenza esatta o sinonimo
                    if col.lower() in [s.lower() for s in sinonimi]:
                        mappa_reale[target] = col
                    break
            
            # Se ancora non trovata, prova il fuzzy matching (difflib)
                if target not in mappa_reale:
                    matches = difflib.get_close_matches(target, colonne_file, n=1, cutoff=0.6)
                if matches:
                    mappa_reale[target] = matches[0]
        
        return mappa_reale

    def elabora_csv(self, file_path, company_id):
        # ... (caricamento file) ...
        
        # 1. Rileva i "ponti" tra le colonne
        mappa = self._smart_mapping_colonne(df)
        
        # 2. Rilevamento settore
        settore_nome, ClasseAsset = self._auto_rilevamento_settore(df.columns)
        logger.info(f"Settore rilevato: {settore_nome}")

        for _, row in df.iterrows():
            # Estraiamo i dati usando la mappa intelligente
            valore_corrente = row.get(mappa.get('valore'), 0)
            rischio_corrente = row.get(mappa.get('rischio'), 0)
            
            # --- LOGICA PREDIZIONE (L'Anima del sistema) ---
            # Recuperiamo lo storico dal DB per calcolare il Momentum
            storico = self.db.get_ultimo_stato_asset(row.get('nome'), company_id)
            
            momentum = 0
            if storico:
                # Calcoliamo la variazione rispetto a ieri
                momentum = (valore_corrente - storico['valore']) / 1 # dt=1 giorno
            
            # Creazione dell'asset potenziato
            dati_asset = row.to_dict()
            dati_asset['momentum_score'] = momentum
            
            asset_obj = ClasseAsset(**dati_asset)
            # ... salvataggio e aggiunta alla lista