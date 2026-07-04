import numpy as np
import pandas as pd
import logging

logger = logging.getLogger("RGD-Alpha.Simulator")

class SimulatoreRischio:
    def __init__(self, iterazioni=1000):
        self.iterazioni = iterazioni

    def esegui_stress_test(self, valore_attuale, volatilita, giorni_proiettati=30):
        """
        Simulazione Monte Carlo per prevedere l'andamento del rischio.
        """
        try:
            # Generiamo 1000 possibili percorsi futuri basati sulla volatilità attuale
            # Usiamo una distribuzione normale per le variazioni giornaliere
            rendimenti_simulati = np.random.normal(0, volatilita, (giorni_proiettati, self.iterazioni))
            percorsi_rischio = valore_attuale + rendimenti_simulati.cumsum(axis=0)

            # Analisi dei risultati
            stato_finale = percorsi_rischio[-1, :]
            prob_fallimento = (stato_finale > 9.0).mean() * 100  # Rischio sopra 9 è 'fallimento'
            
            # Calcolo Data di Sopravvivenza (punto di rottura medio)
            giorni_sopravvivenza = giorni_proiettati
            for g in range(giorni_proiettati):
                if (percorsi_rischio[g, :] > 8.5).mean() > 0.5:
                    giorni_sopravvivenza = g
                    break

            return {
                "probabilita_crisi": round(prob_fallimento, 2),
                "giorni_sopravvivenza_stimati": giorni_sopravvivenza,
                "rischio_max_previsto": round(np.max(stato_finale), 2)
            }
        except Exception as e:
            logger.error(f"Errore simulazione: {e}")
            return None
