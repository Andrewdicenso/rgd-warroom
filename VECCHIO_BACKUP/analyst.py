import pandas as pd
import logging
import numpy as np

from core.database import DatabaseAziendale

logger = logging.getLogger("RGD-Alpha.Analyst")

class AnalistaRischio:
    """
    Modulo di Intelligence Predittiva: implementa Regressione Lineare e 
    analisi della Volatilità Storica applicata alle ore produttive reali H(prod).
    Lavora direttamente con DatabaseAziendale, che gestisce cifratura/decifratura.
    """
    def __init__(self, db: DatabaseAziendale):
        self.db = db
        self.soglia_critica = 7.0 
        self.soglia_warning = 5.0

    def _calcola_proiezione_lineare(self, serie_rischio):
        """
        Utilizza i minimi quadrati per calcolare la pendenza (slope) del trend.
        Permette di prevedere se il rischio di inefficienza oraria salirà o scenderà.
        """
        n = len(serie_rischio)
        if n < 2:
            return 0
        x = np.arange(n)
        y = serie_rischio
        m = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x ** 2) - (np.sum(x) ** 2))
        return m

    def calcola_trend_predittivo(self, nome_asset, company_id) -> dict:
        """
        Analisi Ingegneristica: Sincronizzata con lo storico 'asset_logs' e i KPI orari.
        Calcola Momentum, Volatilità e Proiezione Futura dell'efficienza della risorsa.
        Usa DatabaseAziendale per lavorare su dati già decifrati.
        """
        try:
            # Recupera tutti gli asset per l'azienda (company_id gestito in chiaro dal DB)
            df_all = self.db.recupera_asset_per_azienda(company_id)

            if df_all.empty:
                return {
                    "status": "Inizializzazione",
                    "valore_attuale": 0.0,
                    "valutazione_strategica": "RACCOLTA DATI",
                    "azione": "Nessun dato storico disponibile per questo asset."
                }

            # Filtra solo l'asset/reparto richiesto
            df = df_all[df_all['nome'] == nome_asset].copy()
            if df.empty:
                return {
                    "status": "Inizializzazione",
                    "valore_attuale": 0.0,
                    "valutazione_strategica": "RACCOLTA DATI",
                    "azione": "Nessun dato storico disponibile per questo asset."
                }

            # Ordine cronologico e limitazione agli ultimi 15 campionamenti
            df = df.sort_values('timestamp')
            df = df.tail(15)

            rischi = df['rischio'].values
            if len(rischi) == 0:
                return {
                    "status": "Inizializzazione",
                    "valore_attuale": 0.0,
                    "valutazione_strategica": "RACCOLTA DATI",
                    "azione": "Nessun dato storico disponibile per questo asset."
                }

            if len(rischi) < 2:
                return {
                    "status": "Inizializzazione",
                    "valore_attuale": float(rischi[-1]),
                    "valutazione_strategica": "RACCOLTA DATI",
                    "azione": "Dati insufficienti per proiezione statistica oraria."
                }

            ultimo = rischi[-1]
            precedente = rischi[-2]

            # 1. Indicatori di Velocità dello slittamento orario
            delta = ultimo - precedente
            pendenza = self._calcola_proiezione_lineare(rischi)

            # 2. Analisi Volatilità delle ore produttive (Deviazione Standard)
            volatilita = np.std(rischi)

            # 3. Momentum (Variazione percentuale del posizionamento di rischio)
            momentum_perc = ((ultimo - rischi[0]) / rischi[0] * 100) if rischi[0] != 0 else 0

            predizione = {
                "status": "Successo",
                "valore_attuale": round(float(ultimo), 2),
                "delta_immediato": round(float(delta), 2),
                "momentum_percentuale": f"{momentum_perc:+.2f}%",
                "indice_volatilita": round(float(volatilita), 2),
                "pendenza_trend": round(float(pendenza), 3),
                "alert_critico": float(ultimo) > self.soglia_critica
            }

            # --- LOGICA DI INTELLIGENCE PREDITTIVA ALLINEATA AD H(prod) ---
            if pendenza > 0.3 or (ultimo > self.soglia_critica and delta > 0):
                predizione["valutazione_strategica"] = "INSTABILITÀ ACCELERATA"
                predizione["azione"] = "CRITICO: Accumulo esponenziale di ore perse. Rischio blocco supply chain o scadenze."
            elif pendenza < -0.1 and ultimo < self.soglia_warning:
                predizione["valutazione_strategica"] = "RECUPERO STRUTTURALE"
                predizione["azione"] = "EFFICIENTE: Ottimizzazione dei tempi e stabilizzazione delle ore reali H(prod)."
            elif volatilita > 1.2:
                predizione["valutazione_strategica"] = "VOLATILITÀ ELEVATA"
                predizione["azione"] = "ATTENZIONE: Alternanza critica tra picchi produttivi e micropause anomale. Monitorare carichi."
            else:
                predizione["valutazione_strategica"] = "STABILITÀ OPERATIVA"
                predizione["azione"] = "MANTENIMENTO: Andamento orario stabile e in linea con la pianificazione."

            return predizione

        except Exception as e:
            logger.error(f"❌ Errore Analista predittivo su {nome_asset}: {e}")
            return {
                "status": "Errore", 
                "valore_attuale": 0.0, 
                "valutazione_strategica": "FALLIMENTO CALCOLO",
                "azione": "Verificare consistenza dei dati e integrità del database."
            }