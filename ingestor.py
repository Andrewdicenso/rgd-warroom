import pandas as pd
import os
import logging
import torch
import torch.nn.functional as F
from core.secure_vault import SecureVault
from core.entities import (
    AssetDiMercato,
    AssetDiValore,
    AssetDiRelazione,
    AssetStrategico,
)
from core.database import DatabaseAziendale

logger = logging.getLogger("RGD-Alpha.Ingestor")


class IngestoreDati:
    def __init__(self, key_path="core/security/vault.key"):
        self.vault = SecureVault(key_path=key_path)
        self.db = DatabaseAziendale()

        # 1. DIZIONARIO DI TRADUZIONE SAP
        self.dizionario_sap = {
            "quantita": ["menge", "labst", "vclog"],
            "valore": ["netwr", "dmbtr", "waers", "knumv"],
            "nome": ["matnr", "maktx", "arktx"],
            "id_asset": ["belnr", "vbeln", "aufnr"],
        }

        self.mappa_sinonimi = {
            "quantita": [
                "quantita",
                "pezzi",
                "qta",
                "stock",
                "unita",
                "giacenza",
                "quantity",
                "vol",
                "qty",
            ],
            "valore": [
                "prezzo",
                "importo",
                "lordo",
                "valore",
                "costo",
                "ammontare",
                "costo_unitario",
                "prezzo_acquisto",
                "amount",
                "price",
                "netwr",
            ],
            "rischio": [
                "rischio",
                "impatto",
                "criticita",
                "priorita",
                "rischio_logistico",
                "risk_factor",
                "risk",
                "score",
            ],
            "stato": [
                "stato",
                "condizione",
                "status",
                "pagamento",
                "disponibilita",
                "stato_qualita",
                "level",
            ],
            "id_asset": [
                "codice",
                "id",
                "reference",
                "ref",
                "belnr",
                "matnr",
                "id_asset",
            ],
            "nome": [
                "descrizione",
                "prodotto",
                "materiale",
                "item",
                "nome",
                "asset",
                "maktx",
            ],
        }

        self.settori_keys = {
            "FINANCE": ["fattura", "iban", "lordo", "costo_unitario", "netwr", "dmbtr"],
            "LOGISTICS": [
                "bolla",
                "ddt",
                "magazzino",
                "quantita",
                "sku",
                "matnr",
                "menge",
                "labst",
            ],
            "RELATIONS": ["cliente", "fornitore", "crm", "kunnr", "lifnr"],
        }

        self.classi_valori = {
            "FINANCE": AssetDiValore,
            "LOGISTICS": AssetDiMercato,
            "RELATIONS": AssetDiRelazione,
            "GENERAL": AssetStrategico,
        }

    def _rileva_sorgente_sap(self, colonne):
        colonne_lower = [str(c).lower() for c in colonne]
        punteggio_sap = 0

        for col in colonne_lower:
            for lista_sap in self.dizionario_sap.values():
                if col in lista_sap:
                    punteggio_sap += 1

        if len(colonne_lower) == 0:
            return False

        return (punteggio_sap / len(colonne_lower)) > 0.30

    def _calcola_attenzione_settore(self, colonne_file):
        punteggi_settori = {"FINANCE": 0.0, "LOGISTICS": 0.0, "RELATIONS": 0.0}

        for colonna in colonne_file:
            col_clean = str(colonna).lower()
            for settore, chiavi in self.settori_keys.items():
                for chiave in chiavi:
                    if chiave == col_clean:
                        punteggi_settori[settore] += 2.0
                    elif chiave in col_clean:
                        punteggi_settori[settore] += 1.0

        tensor = torch.tensor([list(punteggi_settori.values())], dtype=torch.float32)
        if tensor.sum() == 0:
            return "GENERAL", self.classi_valori["GENERAL"]

        pesi = F.softmax(tensor, dim=-1).flatten()
        mappa_pesi = dict(zip(punteggi_settori.keys(), pesi.tolist()))

        settore_scelto = max(mappa_pesi, key=mappa_pesi.get)
        if mappa_pesi[settore_scelto] < 0.45:
            return "GENERAL", self.classi_valori["GENERAL"]

        return settore_scelto, self.classi_valori[settore_scelto]

    def _normalizza_riga_intelligente(self, row, is_sap):
        dati_puliti = row.to_dict()
        dizionario_riferimento = self.dizionario_sap if is_sap else self.mappa_sinonimi

        for campo_target, sinonimi in dizionario_riferimento.items():
            for colonna_reale in row.index:
                if str(colonna_reale).lower() in sinonimi:
                    valore = row[colonna_reale]
                    if valore is not None and not pd.isna(valore):
                        dati_puliti[campo_target] = valore
                        break

        dati_puliti["id_asset"] = dati_puliti.get("id_asset", row.get("id", "N/D"))
        dati_puliti["nome"] = dati_puliti.get("nome", row.get("nome", "Asset_Generico"))

        return dati_puliti

    def elabora_csv(self, file_path, company_id):
        asset_list = []
        if not os.path.exists(file_path):
            return asset_list

        try:
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
                df = pd.read_excel(file_path)
            else:
                return asset_list

            if df.empty:
                return asset_list

            is_sap = self._rileva_sorgente_sap(df.columns)
            settore_nome, ClasseAsset = self._calcola_attenzione_settore(df.columns)

            for _, row in df.iterrows():
                dati_normalizzati = self._normalizza_riga_intelligente(row, is_sap)

                try:
                    nuovo_asset = ClasseAsset(**dati_normalizzati)

                    if hasattr(nuovo_asset, "genera_kpi_strategici"):
                        nuovo_asset.genera_kpi_strategici()

                    # Salvataggio storico (opzionale)
                    # self.db.salva_asset(nuovo_asset, company_id)

                    asset_list.append(nuovo_asset)

                except Exception as e:
                    logger.debug(f"Salto riga per errore formato: {e}")

        except Exception as e:
            logger.error(f"Errore critico: {e}")

        return asset_list
