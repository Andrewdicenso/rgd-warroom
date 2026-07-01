import json
import os
import sys
from core.ingestor import IngestoreDati

class ConsulenteAziendale:
    def __init__(self, nome_azienda, file_config="config.json"):
        self.nome_azienda = nome_azienda
        self.file_config = file_config
        self.feedback_storico = []
        self.file_memoria = f"{nome_azienda}_storico.json"
        
        # Inizializzazione con protezione e disclaimer
        self.mostra_disclaimer()
        self.carica_configurazione()

    def mostra_disclaimer(self):
        print("==========================================================")
        print("CONSULENTE VIRTUALE RGandja - AVVISO DI RESPONSABILITÀ")
        print("==========================================================")
        print("Il Consulente Virtuale analizza i dati in base alle soglie impostate.")
        print("La correttezza dei dati è responsabilità dell'azienda utilizzatrice.")
        print("\nHAI DUBBI SU COME IMPOSTARE LE SOGLIE?")
        print("Non inserire valori casuali. Offriamo un servizio di analisi storica:")
        print("Inviaci i tuoi dati degli ultimi 6 mesi; il nostro team procederà")
        print("a delineare i benchmark reali e personalizzati per la tua azienda.")
        print("==========================================================\n")

    def carica_configurazione(self):
        """Carica le soglie con blocco di sicurezza se il file manca."""
        while not os.path.exists(self.file_config):
            print(f"--- ERRORE: File di configurazione '{self.file_config}' non trovato ---")
            scelta = input("Vuoi reinserire il percorso del file corretto? (s/n): ")
            
            if scelta.lower() == 's':
                nuovo_percorso = input("Inserisci il percorso completo del file: ")
                self.file_config = nuovo_percorso
            else:
                print("Chiusura sistema per motivi di sicurezza.")
                sys.exit()

        with open(self.file_config, 'r') as f:
            config = json.load(f)
            self.soglia_cac = config.get("soglia_cac", 50.0)
            self.soglia_ltv = config.get("soglia_ltv", 200.0)
            self.soglia_burn_rate = config.get("soglia_burn_rate", 10000.0)
            self.soglia_margine = config.get("soglia_margine", 20.0)
            self.soglia_conversione = config.get("soglia_conversione", 2.0)
            print("Configurazione caricata correttamente.")

    def aggiorna_parametro(self, chiave, valore):
        """Consente all'azienda di aggiornare i propri target in autonomia."""
        with open(self.file_config, 'r+') as f:
            config = json.load(f)
            config[chiave] = valore
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()
        self.carica_configurazione()
        print(f"Parametro {chiave} aggiornato a {valore}.")

    def aggiorna_configurazione_da_dict(self, nuovo_dizionario):
        """Aggiorna massivamente le soglie tramite il modulo Premium."""
        with open(self.file_config, 'r+') as f:
            config = json.load(f)
            config.update(nuovo_dizionario) # Aggiorna solo le soglie presenti
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()
        self.carica_configurazione()
        print("Configurazione aggiornata massivamente dal modulo Premium.")

    def avvia_calibrazione_premium(self, cartella_dati="./dati_storici"):
        """Ponte verso l'IngestoreDati per calibrazione automatica."""
        # MODIFICATO: Istanzia IngestoreDati anziché GestoreDati
        gestore = IngestoreDati()
        nuove_soglie = gestore.calcola_soglie_da_storico(cartella_dati)
        self.aggiorna_configurazione_da_dict(nuove_soglie)

    def get_all_kpi(self):
        """Ritorna un dizionario pronto per essere visualizzato nella dashboard."""
        return {
            "cac": self.soglia_cac, 
            "cac_delta": -0.05,
            "ltv": self.soglia_ltv, 
            "ltv_delta": 0.12,
            "churn": 0.024, 
            "churn_delta": -0.001,
            "roi": (self.soglia_margine / 100), 
            "roi_delta": 0.02,
            "eff": 0.85
        }

    # --- Metodi di Analisi ---
    def analizza_cac(self, valore):
        if valore <= (self.soglia_cac * 0.8): stato, consiglio = "ECCELLENTE", "CAC ottimo, puoi scalare."
        elif valore <= self.soglia_cac: stato, consiglio = "SOSTENIBILE", "CAC in linea."
        else: stato, consiglio = "CRITICO", "CAC troppo alto. Rivedi i canali."
        self.ultima_analisi = {"kpi": "CAC", "stato": stato, "consiglio": consiglio}
        return stato, consiglio

    def analizza_ltv(self, valore):
        if valore >= (self.soglia_ltv * 1.2): stato, consiglio = "ECCELLENTE", "LTV molto alto."
        elif valore >= self.soglia_ltv: stato, consiglio = "SOSTENIBILE", "Il valore del cliente è sano."
        else: stato, consiglio = "CRITICO", "LTV basso. Migliora la fidelizzazione."
        self.ultima_analisi = {"kpi": "LTV", "stato": stato, "consiglio": consiglio}
        return stato, consiglio

    def analizza_burn_rate(self, valore):
        if valore <= (self.soglia_burn_rate * 0.7): stato, consiglio = "ECCELLENTE", "Ottima gestione cassa."
        elif valore <= self.soglia_burn_rate: stato, consiglio = "SOSTENIBILE", "Burn rate sotto controllo."
        else: stato, consiglio = "CRITICO", "Stai bruciando cassa troppo velocemente."
        self.ultima_analisi = {"kpi": "BURN_RATE", "stato": stato, "consiglio": consiglio}
        return stato, consiglio

    def analizza_margine_netto(self, valore):
        if valore >= self.soglia_margine: stato, consiglio = "ECCELLENTE", "Margine solido."
        else: stato, consiglio = "CRITICO", "Utile eroso. Controlla i costi."
        self.ultima_analisi = {"kpi": "MARGINE_NETTO", "stato": stato, "consiglio": consiglio}
        return stato, consiglio

    def analizza_tasso_conversione(self, valore):
        if valore >= self.soglia_conversione: stato, consiglio = "ECCELLENTE", "Conversione alta."
        else: stato, consiglio = "CRITICO", "Conversione bassa. Rivedi l'offerta."
        self.ultima_analisi = {"kpi": "TASSO_CONVERSIONE", "stato": stato, "consiglio": consiglio}
        return stato, consiglio

    def registra_feedback(self, utile):
        nuovo_feedback = {"analisi": self.ultima_analisi, "utile": utile}
        self.feedback_storico.append(nuovo_feedback)
        self._salva_su_file()
        return "Grazie per il riscontro." if utile else "Ricevuto, sto imparando."

    def _salva_su_file(self):
        with open(self.file_memoria, 'w') as f:
            json.dump(self.feedback_storico, f, indent=4)