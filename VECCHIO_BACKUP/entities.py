import logging
from datetime import datetime

logger = logging.getLogger("RGD-Alpha.Entities")

class AssetStrategico:
    """
    CLASSE UNIVERSALE RGD-ALPHA:
    Adatta a qualsiasi documento aziendale.
    """
    def __init__(self, id=None, nome="Generico", rischio=0.0, company_id="GENERIC_CORP", **kwargs):
        self.id = id
        self.nome = nome
        self.rischio = float(rischio) if rischio is not None else 0.0
        self.company_id = company_id
        self.data_rilevazione = kwargs.get('data', datetime.now().strftime("%Y-%m-%d"))

        # Salva automaticamente tutte le colonne extra
        self.dati_extra = kwargs

        # KPI predittivi
        self.analisi_predittiva = {}

    def genera_kpi_strategici(self):
        voto_rischio = float(self.rischio)

        if voto_rischio > 7:
            conclusione = "CRITICO: Richiede intervento immediato del management."
            previsione = "Rischio di interruzione operativa entro 30 giorni."
        elif voto_rischio < 3:
            conclusione = "SICURO: Asset stabile."
            previsione = "Continuità garantita a lungo termine."
        else:
            conclusione = "MONITORAGGIO: Parametri nella norma."
            previsione = "Stabilità prevista per il prossimo trimestre."

        self.analisi_predittiva = {
            "stato": conclusione,
            "proiezione": previsione,
            "kpi_id": self.id
        }
        return self.analisi_predittiva


class AssetDiMercato(AssetStrategico):
    """LOGISTICA & MAGAZZINO"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.quantita = kwargs.get('quantita', kwargs.get('Quantita', kwargs.get('Pezzi', 0)))
        self.sku = kwargs.get('Codice_SKU', kwargs.get('SKU', 'N/D'))
        self.ubicazione = kwargs.get('Ubicazione', 'Magazzino Centrale')


class AssetDiValore(AssetStrategico):
    """FINANCE & CONTABILITÀ"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prezzo = kwargs.get('prezzo', kwargs.get('Importo', kwargs.get('Costo_Unitario', 0.0)))
        self.stato_pagamento = kwargs.get('stato', kwargs.get('Stato_Qualita', kwargs.get('Condizione', 'In attesa')))
        self.valuta = kwargs.get('Valuta', 'EUR')


class AssetDiRelazione(AssetStrategico):
    """CRM & RELAZIONI COMMERCIALI"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.partner = kwargs.get('Fornitore_Origine', kwargs.get('Cliente', kwargs.get('Ragione_Sociale', 'Privato')))
        self.livello_servizio = kwargs.get('livello_servizio', 5.0)
