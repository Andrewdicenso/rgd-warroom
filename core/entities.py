import logging
from datetime import datetime

logger = logging.getLogger("RGD-Alpha.Entities")

class AssetStrategico:
    """
    CLASSE MASTER RGD-ALPHA v2.0
    Cuore del sistema di analisi. Gestisce la persistenza e il calcolo dei KPI base.
    """
    def __init__(self, id=None, nome="Generico", rischio=0.0, company_id="GENERIC_CORP", **kwargs):
        self.id = id
        self.nome = nome
        self.rischio = float(rischio)
        self.company_id = company_id
        self.data_rilevazione = kwargs.get('data', datetime.now().strftime("%Y-%m-%d"))
        
        # --- MOTORE EXTRA DATI ---
        self.dati_extra = kwargs 
        self.volatilità_nativa = 0.15 # Volatilità di base
        self.analisi_predittiva = {}

    def genera_kpi_strategici(self):
        voto = self.rischio
        # Logica di prognosi potenziata
        if voto > 8:
            s, p = "COLLASSO", "Rischio immediato di interruzione attività."
        elif voto > 6:
            s, p = "CRITICO", "Peggioramento previsto entro 15 giorni."
        elif voto > 4:
            s, p = "ATTENZIONE", "Stabilità incerta, richiede monitoraggio."
        else:
            s, p = "OTTIMALE", "Asset in salute, crescita costante."

        self.analisi_predittiva = {"stato": s, "proiezione": p, "kpi_id": self.id}
        return self.analisi_predittiva

class AssetDiMercato(AssetStrategico):
    """LOGISTICA, MAGAZZINO, FASHION"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.quantita = kwargs.get('quantita', kwargs.get('Pezzi', 0))
        self.valore_unitario = kwargs.get('valore', kwargs.get('prezzo', 0.0))
        self.volatilità_nativa = 0.25 # Il mercato si muove velocemente

class AssetDiValore(AssetStrategico):
    """FINANCE & CONTABILITÀ"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.importo = kwargs.get('lordo', kwargs.get('prezzo', 0.0))
        self.volatilità_nativa = 0.10 # La finanza è più stabile ma pesante

class AssetDiRisorsa(AssetStrategico):
    """DIPENDENTI E PRODUTTIVITÀ (H-PROD)"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Campi per l'algoritmo delle ore produttive
        self.ore_teoriche = 2080
        self.inefficienze = {
            'ferie': kwargs.get('ferie', 0),
            'ritardi': kwargs.get('ritardi', 0),
            'assenze': kwargs.get('assenze', 0)
        }
        self.volatilità_nativa = 0.05

class AssetSettoreEdile(AssetStrategico):
    """CANTIERE E COMMESSE"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cantiere = kwargs.get('cantiere', 'N/D')
        self.penale_giornaliera = kwargs.get('penale', 0.0)
        self.volatilità_nativa = 0.30 # L'edile ha rischi improvvisi alti