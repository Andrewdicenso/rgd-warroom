import pandas as pd
import numpy as np
from typing import List
from src.application.services.base_service import BaseService
from src.application.strategies.mapping_strategy import AttentionMappingStrategy
from src.domain.entities import Asset, crea_asset_dal_dizionario
from src.domain.constants import SINONIMI_MAPPING, SAP_FIELD_MAPPING

class IngestionService(BaseService):
    def __init__(self):
        super().__init__("IngestionService")
        self.strategy = AttentionMappingStrategy()

    def _smart_repair_logic(self, bad_line):
        """Logica di riparazione per righe malformate."""
        fixed_line = bad_line[:2] + [" ".join(bad_line[2:])]
        return fixed_line

    def log_ingestion_error(self, error_type: str, details: str):
        """Standardizzazione del logging errori per il motore di ingestione."""
        self.log_error(f"[{error_type}] {details}")

    def process_file(self, file_content, company_id: str) -> List[Asset]:
        """Esegue l'intero protocollo di ingestione RGD-Alpha Enterprise."""
        self.log_info("Avvio Motore di Ingestione Adattivo RGD-Alpha.")

        # 1. Parsing Flessibile con protezione memoria
        try:
            # Prova a leggere come Excel
            df = pd.read_excel(file_content)
        except Exception:
            # Se fallisce, riprova come CSV con protezione RAM
            try:
                file_content.seek(0)
                df = pd.read_csv(
                    file_content, 
                    sep=None, 
                    engine='python', 
                    on_bad_lines=self._smart_repair_logic, 
                    dtype=str,
                    encoding_errors='replace'
                )
            except Exception as e:
                self.log_ingestion_error("CRITICAL_PARSING_FAILURE", str(e))
                return []

        if df.empty:
            self.log_ingestion_error("EMPTY_FILE", "Il file caricato non contiene dati validi.")
            return []

        # 2. Ottimizzazione Memoria e Pulizia
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df = df.dropna(how='all')
        
        numeric_cols = ['rischio', 'quantita', 'prezzo', 'livello_servizio']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('float32')

        # 3. Identificazione Reparto
        settore = self.strategy.identify_sector(df.columns)
        self.log_info(f"Settore rilevato: {settore.value}")

        # 4. Normalizzazione e Creazione Asset
        assets = []
        for _, row in df.iterrows():
            try:
                normalizzato = self._mappa_campi(row.to_dict())
                normalizzato['company_id'] = company_id
                asset = crea_asset_dal_dizionario(normalizzato, settore)
                assets.append(asset)
            except Exception as e:
                self.log_ingestion_error("ASSET_CREATION_FAILURE", f"Riga ignorata causa errore: {e}")

        return assets

    def _mappa_campi(self, raw_data: dict) -> dict:
        """Applica il dizionario di traduzione SAP e Sinonimi."""
        pulito = {}
        for target, sinonimi in SINONIMI_MAPPING.items():
            for key, val in raw_data.items():
                if str(key).lower() in sinonimi:
                    pulito[target] = val
                    break
        pulito['dati_extra'] = raw_data
        return pulito