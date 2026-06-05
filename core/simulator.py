py
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger("RGD-Alpha.Simulator")

class SimulatoreRischio:
    def __init__(self, iterazioni=1000):
        self.iterazioni = iterazioni

    def esegui_stress_test(self, valore_attuale, volatilita, giorni_proiettati=30):
        """
        Simulazione Monte Carlo Avanzata con logica di DRIFT (Tendenza).
        Prevede il 'Punto di Rottura' aziendale sotto stress.
        """
        try:
            # 1. Calcolo del Drift (Tendenza): Se il rischio è già alto (>5), 
            # l'AI assume una tendenza naturale al peggioramento (0.02 al giorno)
            drift = 0.02 if valore_attuale > 5.0 else 0.0
            
            # 2. Generazione variazioni con distribuzione normale pesata
            variazioni = np.random.normal(drift, volatilita, (giorni_proiettati, self.iterazioni))
            
            # 3. Costruzione dei percorsi cumulativi
            percorsi_rischio = valore_attuale + variazioni.cumsum(axis=0)
            
            # Limite fisico del rischio (Scale 0-10)
            percorsi_rischio = np.clip(percorsi_rischio, 0, 10)

            # 4. Analisi dei risultati (Punto di rottura)
            stato_finale = percorsi_rischio[-1, :]
            # Probabilità di superare la soglia di allarme rosso (8.5)
            prob_crisi = (stato_finale > 8.5).mean() * 100 
            
            # 5. Calcolo 'Day Zero' (Quando l'azienda collassa mediamente)
            media_giornaliera = np.mean(percorsi_rischio, axis=1)
            giorni_sopravvivenza = giorni_proiettati
            for g, r in enumerate(media_giornaliera):
                if r > 8.5:
                    giorni_sopravvivenza = g
                    break

            return {
                "probabilita_crisi": round(prob_crisi, 2),
                "giorni_sopravvivenza_stimati": giorni_sopravvivenza,
                "rischio_max_previsto": round(np.max(stato_finale), 2),
                "media_finale": round(np.mean(stato_finale), 2),
                "percorsi_raw": percorsi_rischio
            }
        except Exception as e:
            logger.error(f"Errore simulazione Monte Carlo: {e}")
            return None