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
    Sistema adattivo con auto-correzione, mappatura multi-settore (Edile, Fashion, Risorse)
    e protezione contro crash da dati sporchi.
    """
    def __init__(self, key_path="core/security/vault.key"):
        self.vault = SecureVault(key_path=key_path)
        self.db = DatabaseAziendale()
        
        # Mappa sinottica estesa per coprire i nuovi domini aziendali
        self.mappa_sinonimi = {
            'quantita': ['quantita', 'pezzi', 'qta', 'stock', 'unita', 'giacenza', 'rimanenza', 'output_totale'],
            'valore': ['prezzo', 'importo', 'lordo', 'valore', 'costo', 'ammontare', 'prezzo_acquisto', 'valore_extra'],
            'rischio': ['rischio', 'impatto', 'criticita', 'priorita', 'risk', 'pericolo', 'urgenza'],
            'ore': ['ore', 'tempo', 'durata', 'h', 'lavorato', 'ore_effettive'],
            'inefficienze': ['ferie', 'festivita', 'assenze', 'permessi', 'ritardi', 'micropause']
        }

    def _pulisce_intestazioni(self, df):
        """Standardizza i nomi delle colonne."""
        df.columns = [
            str(c).strip().lower()
            .replace(' ', '_')
            .replace('à', 'a')
            .replace('ò', 'o')
        ]
        return df

    def _valida_dati_critici(self, df):
        if df.empty:
            return False, "Il file caricato è vuoto."
        
        nomi_possibili = [
            'nome', 'descrizione', 'prodotto', 'asset',
            'sku', 'cantiere', 'cliente', 'fornitore'
        ]
        
        if not any(col in df.columns for col in nomi_possibili):
            return False, "Struttura file non riconosciuta. Manca colonna 'Nome' o 'Prodotto'."
        
        return True, "Validazione superata."

    def _auto_rilevamento_settore(self, colonne):
        col = set(colonne)

        if any(k in col for k in ['cantiere', 'commessa', 'ponteggio', 'cemento', 'sicurezza_dpi']):
            return "EDILE", AssetStrategico
        
        if any(k in col for k in ['collezione', 'taglia', 'colore', 'stagione', 'invenduto']):
            return "FASHION", AssetDiMercato
        
        if any(k in col for k in self.mappa_sinonimi['inefficienze']) or 'dipendente' in col:
            return "PRODUTTIVITA", AssetDiRisorsa 
        
        if any(k in col for k in ['fattura', 'iban', 'lordo', 'partita_iva']):
            return "FINANCE", AssetDiValore
        
        if any(k in col for k in ['bolla', 'ddt', 'magazzino', 'vettore', 'spedizione']):
            return "LOGISTICS", AssetDiMercato
        
        return "GENERAL", AssetStrategico

    def _estrai_dato(self, row, categoria_chiave, default=0):
        for sinonimo in self.mappa_sinonimi.get(categoria_chiave, []):
            if sinonimo in row and not pd.isna(row[sinonimo]):
                return row[sinonimo]
        return default

    def _estrai_nome(self, row):
        for k in ['nome', 'prodotto', 'asset', 'descrizione', 'cantiere', 'cliente', 'fornitore']:
            if k in row:
                return str(row[k])
        return "Asset_Generico"

    def _valida_numerico(self, val):
        try:
            v = str(val).replace(',', '.')
            return float(v)
        except:
            return 0.0

    def elabora_file(self, file_path, company_id):
        asset_list = []

        if not os.path.exists(file_path):
            return asset_list

        try:
            # 1. GESTIONE ESTENSIONE
            estensione = os.path.splitext(file_path)[1].lower()

            if estensione == '.csv':
                try:
                    df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8-sig')
                except:
                    df = pd.read_csv(file_path, sep=None, engine='python', encoding='latin-1')
            
            elif estensione in ['.xls', '.xlsx']:
                df = pd.read_excel(file_path)
            
            else:
                logger.error(f"Formato {estensione} non supportato.")
                return asset_list

            # 🔥 PULIZIA BASE (rimuove BOM, spazi, maiuscole)
            df.columns = [c.strip().lower() for c in df.columns]

            # 2. PROCESSO DI PULIZIA AVANZATA
            df = self._pulisce_intestazioni(df)

            valido, messaggio = self._valida_dati_critici(df)
            if not valido:
                logger.warning(f"Validazione fallita: {messaggio}")
                return asset_list

            # 3. RILEVAMENTO E MAPPATURA
            settore_nome, ClasseAsset = self._auto_rilevamento_settore(df.columns)
            self.db.registra_caricamento(company_id, f"Analisi {settore_nome}", os.path.basename(file_path))

            for _, row in df.iterrows():
                dati_riga = row.to_dict()
                dati_riga['nome'] = self._estrai_nome(row)
                dati_riga['rischio'] = self._valida_numerico(self._estrai_dato(row, 'rischio', 5.0))
                dati_riga['valore_extra'] = self._valida_numerico(self._estrai_dato(row, 'valore', 0.0))
                dati_riga['company_id'] = company_id

                for ineff in self.mappa_sinonimi['inefficienze']:
                    dati_riga[ineff] = self._valida_numerico(row.get(ineff, 0))

                dati_riga['output_totale'] = self._valida_numerico(self._estrai_dato(row, 'quantita', 0))

                try:
                    nuovo_asset = ClasseAsset(**dati_riga)
                    asset_list.append(nuovo_asset)
                except Exception as e:
                    logger.debug(f"Salto riga per incompatibilità: {e}")

        except Exception as e:
            logger.error(f"Errore critico ingestione RGD-Alpha: {e}")

        return asset_list
