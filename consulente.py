py
import json
import os
import sys
import logging

logger = logging.getLogger("RGD-Alpha.Consulente")

class ConsulenteAziendale:
    """
    CONSULENTE VIRTUALE RGD-ALPHA v2.0
    Trasforma i dati tecnici in sentenze strategiche multi-settore.
    """
    def __init__(self, nome_azienda, file_config="config.json"):
        self.nome_azienda = nome_azienda
        self.file_config = file_config
        self.feedback_storico = []
        self.file_memoria = f"data/logs/{nome_azienda}_memoria_ai.json"
        self.carica_configurazione()

    def carica_configurazione(self):
        """Carica le soglie dal file JSON. Se manca, usa valori di default sicuri."""
        if not os.path.exists(self.file_config):
            logger.warning(f"Configurazione {self.file_config} non trovata. Uso default.")
            self.soglie = {
                "rischio_max": 7.0,
                "produttivita_min": 0.8,
                "margine_min": 20.0
            }
            return

        with open(self.file_config, 'r') as f:
            self.soglie = json.load(f)

    def genera_consulenza_settoriale(self, report_analisi):
        """
        Analizza i risultati del DataGateway e genera un parere proattivo.
        """
        if not report_analisi:
            return "Nessun dato analizzato. Carica un file per ricevere consulenza."

        # Identifichiamo il settore dominante
        settore = report_analisi[0].get('settore', 'GENERALE')
        rischio_medio = sum([a['rischio'] for a in report_analisi]) / len(report_analisi)
        
        # LOGICA DI CONSULENZA DINAMICA
        if settore == "EDILE_COSTRUZIONI":
            return self._consulenza_edile(rischio_medio)
        elif settore == "PRIMARIO_ALIMENTARE":
            return self._consulenza_alimentare(rischio_medio)
        elif settore == "PRODUTTIVITA":
            return self._consulenza_risorse(report_analisi)
        else:
            return self._consulenza_generale(rischio_medio)

    def _consulenza_edile(self, rischio):
        if rischio > 7:
            return "🚨 ALLERTA CANTIERE: Rischio penali elevato. Verifica immediata conformità DPI e cronoprogramma."
        return "✅ CANTIERE STABILE: Commesse in linea con le aspettative di sicurezza."

    def _consulenza_alimentare(self, rischio):
        if rischio > 6.5:
            return "🚨 RISCHIO QUALITÀ: Possibile deperibilità stock. Velocizzare rotazione magazzino fresco."
        return "✅ QUALITÀ GARANTITA: Flusso di magazzino ottimale."

    def _consulenza_risorse(self, report):
        # Analisi H-prod
        inefficienza_media = sum([a.get('ore_perdute', 0) for a in report]) / len(report)
        if inefficienza_media > 100:
            return "⚠️ UFFICIO HR: Rilevata dispersione oraria significativa. Riorganizzare turnazione pause."
        return "✅ RISORSE EFFICIENTI: Il team sta operando entro i benchmark di produttività."

    def _consulenza_generale(self, rischio):
        if rischio > 7:
            return "🚨 CRITICITÀ GENERALE: L'azienda mostra segni di instabilità operativa. Intervenire sugli asset rossi."
        return "✅ OPERATIVITÀ SANA: I parametri di crescita sono rispettati."