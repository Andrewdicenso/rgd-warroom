"""
Ingestion Service - Orchestrazione del caricamento dati Enterprise.
"""
import pandas as pd
from typing import List
from src.application.services.base_service import BaseService
from src.application.strategies.mapping_strategy import AttentionMappingStrategy
from src.domain.entities import Asset, crea_asset_dal_dizionario
from src.domain.constants import SINONIMI_MAPPING, SAP_FIELD_MAPPING

class IngestionService(BaseService):
    def __init__(self):
        super().__init__("IngestionService")
        self.strategy = AttentionMappingStrategy()

    # File: /opt/render/project/src/src/application/services/ingestion_service.py
# Sostituisci il blocco di lettura (intorno alla riga 24) con questo:

    def process_file(self, file_content, company_id: str) -> List[Asset]:
        """Esegue l'intero protocollo di ingestione RGD-Alpha."""
        self.log_info("Inizio processamento file caricato.")

        # 1. Lettura file (Excel o CSV)
        try:
            # Prova prima come Excel
            df = pd.read_excel(file_content)
        except Exception:
            # Se fallisce, prova come CSV con rilevamento automatico del separatore
            try:
                # Riporta il puntatore all'inizio del file se necessario
                file_content.seek(0)
                # sep=None con engine='python' permette a pandas di indovinare il separatore (virgola, punto e virgola, ecc.)
                df = pd.read_csv(file_content, sep=None, engine='python', on_bad_lines='warn')
            except Exception as e:
                self.log_error(f"Errore critico nella lettura del file: {e}")
                return []

        if df.empty:
            return []

        # 2. Identificazione Reparto tramite Attenzione
        settore = self.strategy.identify_sector(df.columns)
        self.log_info(f"Settore rilevato dal file: {settore.value}")

        # 3. Normalizzazione e Creazione Asset
        assets = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            # Mappiamo i sinonimi (SAP e Standard) sui campi dell'entità
            normalizzato = self._mappa_campi(row_dict)
            normalizzato['company_id'] = company_id
            
            # Creazione tramite la nostra Factory di Dominio
            asset = crea_asset_dal_dizionario(normalizzato, settore)
            assets.append(asset)

        return assets

    def _mappa_campi(self, raw_data: dict) -> dict:
        """Applica il dizionario di traduzione SAP e Sinonimi."""
        pulito = {}
        for target, sinonimi in SINONIMI_MAPPING.items():
            for key, val in raw_data.items():
                if str(key).lower() in sinonimi:
                    pulito[target] = val
                    break
        # Mantieni i dati originali come extra
        pulito['dati_extra'] = raw_data
        return pulito