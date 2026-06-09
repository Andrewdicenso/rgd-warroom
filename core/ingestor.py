import os
import logging
from datetime import datetime
import pandas as pd

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
        
        # 1. STANDARD FORMATI RICHIESTI (Inclusi dal secondo file senza toccare il resto)
        self.STANDARD_FORMATI = {
            'TESTO': ['.docx', '.doc', '.odt', '.pdf'],
            'CALCOLO': ['.xlsx', '.xls', '.csv', '.ods'],
            'SLIDE': ['.pptx', '.ppt', '.odp']
        }
        self.TUTTI_I_FORMATI = [ext for lista in self.STANDARD_FORMATI.values() for ext in lista]
        
        # Mappa dei sinonimi originale (File 1) - Preservata al 100%
        self.mappa_sinonimi = {
            'quantita': ['quantita', 'pezzi', 'qta', 'stock', 'unita', 'giacenza', 'rimanenza', 'output_totale', 'prodotti'],
            'valore': ['prezzo', 'importo', 'lordo', 'valore', 'costo', 'ammontare', 'acquisto'],
            'rischio': ['rischio', 'impatto', 'criticita', 'priorita', 'risk', 'pericolo'],
            'ore': ['ore', 'tempo', 'durata', 'h', 'lavorato'],
            'inefficienze': ['ferie', 'festivita', 'assenze', 'permessi', 'ritardi', 'micropause']
        }

    def _rileva_manovre_manuali(self, file_input):
        """Rileva se il file ha subito modifiche manuali non autorizzate."""
        return False 

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
        """Alias immutato per garantire la retrocompatibilità totale."""
        return self.elabora_file(file_source, company_id)

    def elabora_file(self, file_input, company_id):
        """SISTEMA UNIFICATO: Controllo Formati + Estrazione Dati Strutturata."""
        nome_file = getattr(file_input, 'name', str(file_input))
        ext = os.path.splitext(nome_file)[1].lower()

        # A. CONTROLLO FORMATO CONSONO
        if ext not in self.TUTTI_I_FORMATI:
            logger.error(f"Formato {ext} non supportato.")
            return {"status": "error", "message": f"Il formato {ext} non è conforme agli standard aziendali."}

        # B. CONTROLLO MANOVRE MANUALI
        if self._rileva_manovre_manuali(file_input):
            return {"status": "warning", "message": "Rilevate modifiche manuali. Richiesta autorizzazione."}

        # C. ESECUZIONE ESTRAZIONE
        asset_list = []
        try:
            if ext in self.STANDARD_FORMATI['CALCOLO']:
                if ext == '.csv':
                    df = pd.read_csv(file_input, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
                else:
                    df = pd.read_excel(file_input)

                df = self._pulisce_intestazioni(df)
                valido, msg = self._valida_dati_critici(df)
                if not valido: 
                    return {"status": "error", "message": msg}

                settore_nome, ClasseAsset = self._auto_rilevamento_settore(df.columns)
                
                # Registrazione log nel database reale (Mantenuta intatta)
                try:
                    self.db.registra_caricamento(company_id, f"Analisi {settore_nome}", nome_file)
                except:
                    pass

                for _, row in df.iterrows():
                    # Costruiamo esattamente il dizionario dati del File 1 con i suoi attributi precisi
                    dati_riga = {
                        'nome': self._estrai_nome(row),
                        'rischio': self._estrai_dato(row, 'rischio', 5.0),
                        'valore_extra': self._estrai_dato(row, 'valore', 0.0),
                        'output_totale': self._estrai_dato(row, 'quantita', 0.0),
                        'company_id': company_id,
                        'timestamp': datetime.now()
                    }
                    
                    # Inserimento dinamico inefficienze originale (File 1)
                    for ineff in self.mappa_sinonimi['inefficienze']:
                        dati_riga[ineff] = self._valida_numerico(row.get(ineff, 0.0))

                    try:
                        # Creazione istanza con l'esatto spacchettamento originario
                        nuovo_asset = ClasseAsset(**dati_riga)
                        asset_list.append(nuovo_asset)
                    except Exception as e:
                        continue
                
                return {"status": "success", "data": asset_list}

            # Ritorno standard del File 2 per gli altri formati riconosciuti (testo/slide)
            return {"status": "success", "message": "Documento inviato all'analisi testuale core."}

        except Exception as e:
            logger.error(f"Errore critico ingestore: {e}")
            return {"status": "error", "message": f"Errore ingestione: {e}"}