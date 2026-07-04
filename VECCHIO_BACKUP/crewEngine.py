# core/crewEngine.py
import json
import os
import pandas as pd

# INDIRIZZAMENTO SICURO: Recupero dinamico del percorso per evitare errori di avvio da main.py o dalle pagine interne
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, 'crewEngine.json')

try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        rgd_config = json.load(f)
except Exception as e:
    print(f"❌ Errore critico nel caricamento di crewEngine.json: {e}")
    rgd_config = {}

def esegui_analisi_evolutiva(azienda_id, dati_file_completo, contesto_rilevato, storico_completo=None):
    """
    CORE ENGINE - PROTOCOLLO RGD-ALPHA
    Analizza olisticamente l'intero file caricato (DataFrame), esegue controlli incrociati 
    tra i reparti e formula la strategia predittiva di marketing e l'Indice di Solidità.
    """
    try:
        nome_progetto = rgd_config.get("nome_progetto", "Protocollo RGD-Alpha")
        print(f"🤖 [{nome_progetto} AI]: Avvio scansione olistica sul file completo di {contesto_rilevato}")

        # Inizializzazione della salute dei 4 reparti aziendali (Base 100)
        salute = {
            "CONTABILITÀ": 100, 
            "MAGAZZINO": 100, 
            "FORNITORI": 100, 
            "VENDITE": 100
        }
        report_diagnostico = ""
        azioni_di_rimedio_marketing = "Nessuna azione richiesta: i parametri aziendali sono stabili."

        # Conversione dei dati in DataFrame Pandas (gestione olistica dell'intero foglio)
        df_attuale = pd.DataFrame(dati_file_completo)
        df_storico = pd.DataFrame(storico_completo) if storico_completo is not None else pd.DataFrame()

        if df_attuale.empty:
            return {
                "successo": False,
                "messaggio": "Il documento caricato non contiene dati validi per l'analisi."
            }

        # --- PILASTRO 1: CONTABILITÀ ---
        if contesto_rilevato == 'CONTABILITÀ':
            regole_contabili = rgd_config["mappatura_4_pilastri"]["CONTABILITÀ"]
            
            # Calcolo olistico delle entrate totali del file attuale
            incassi_attuali = df_attuale["incassi"].sum() if "incassi" in df_attuale.columns else 0
            
            # Estrazione e calcolo della media storica dai dati del database
            if not df_storico.empty and "contesto" in df_storico.columns and "incassi" in df_storico.columns:
                df_storico_contabile = df_storico[df_storico["contesto"] == 'CONTABILITÀ']
                media_storica = df_storico_contabile["incassi"].mean() if not df_storico_contabile.empty else incassi_attuali
            else:
                media_storica = incassi_attuali

            # Analisi predittiva della flessione basata sulla tolleranza definita nel JSON
            if incassi_attuali < (media_storica * regole_contabili["tolleranza_flessione_ricavi"]):
                salute["CONTABILITÀ"] = round((incassi_attuali / media_storica) * 100) if media_storica > 0 else 100
                salute["CONTABILITÀ"] = min(salute["CONTABILITÀ"], 100)
                
                report_diagnostico += f"🛑 WAR ROOM: Rilevato calo degli incassi del {100 - salute['CONTABILITÀ']}% rispetto allo storico precedente.\n"

                # INTERROGAZIONE INCROCIATA CON IL MAGAZZINO
                if "MAGAZZINO" in regole_contabili["reparti_da_interrogare_su_anomalia"]:
                    regole_magazzino = rgd_config["mappatura_4_pilastri"]["MAGAZZINO"]
                    
                    if not df_storico.empty and "contesto" in df_storico.columns and "giorni_stoccaggio" in df_storico.columns:
                        df_magazzino_storico = df_storico[df_storico["contesto"] == 'MAGAZZINO']
                        merci_bloccate = df_magazzino_storico[df_magazzino_storico["giorni_stoccaggio"] > regole_magazzino["limite_giorni_giacenza_critica"]]
                        
                        if not merci_bloccate.empty:
                            report_diagnostico += f"👉 CAUSA INDIVIDUATA (Magazzino): Il crollo dei flussi è legato a merci in giacenza da oltre {regole_magazzino['limite_giorni_giacenza_critica']} giorni.\n"
                            canali_marketing = rgd_config["motore_prescrittivo_marketing"]["canali_azione_veloce"]
                            azioni_di_rimedio_marketing = f"🔥 DIRETTIVA MARKETING ATTIVATA [{canali_marketing[0]}]: Strutturare una campagna promozionale flash sale combinando le giacenze critiche in pacchetti bundle per sbloccare la cassa."

        # --- PILASTRO 2: MAGAZZINO ---
        elif contesto_rilevato == 'MAGAZZINO':
            regole_magazzino = rgd_config["mappatura_4_pilastri"]["MAGAZZINO"]
            
            if "quantita" in df_attuale.columns and "costo_unitario" in df_attuale.columns:
                valore_immobilizzato = (df_attuale["quantita"] * df_attuale["costo_unitario"]).sum()
            else:
                valore_immobilizzato = 0

            if valore_immobilizzato > regole_magazzino["soglia_valore_sovraccarico_euro"]:
                salute["MAGAZZINO"] = 50
                report_diagnostico += f"⚠️ WAR ROOM: Rilevato sovraccarico monetario in Magazzino. Valore totale immobilizzato ({valore_immobilizzato}€) oltre la soglia di sicurezza aziendale.\n"
                canali_marketing = rgd_config["motore_prescrittivo_marketing"]["canali_azione_veloce"]
                azioni_di_rimedio_marketing = f"🔥 DIRETTIVA MARKETING ATTIVATA [{canali_marketing[1]}]: Implementare logiche di cross-selling offrendo i prodotti in esubero come omaggio o incentivo per ordini che superano un carrello minimo d'acquisto."

        # --- CALCOLO DELL'INDICE DI SOLIDITÀ OPERATIVA ---
        # Estrazione pesi dinamici dall'algoritmo del JSON
        pesi = rgd_config["motore_prescrittivo_marketing"]["algoritmo_solidita"]["pesi"]
        punteggio_base = (
            (salute["CONTABILITÀ"] * pesi["contabilita"]) +
            (salute["MAGAZZINO"] * pesi["magazzino"]) +
            (salute["FORNITORI"] * pesi["fornitori"]) +
            (salute["VENDITE"] * pesi["vendite"])
        )
        
        indice_solidita = min(max(round(punteggio_base), 0), 100)

        # Definizione dello stato semaforico visivo
        stato_semaforo = 'VERDE'
        if indice_solidita < 85 and indice_solidita >= 60:
            stato_semaforo = 'GIALLO'
        elif indice_solidita < 60:
            stato_semaforo = 'ROSSO'

        # --- COMPILAZIONE DEL REPORT CERTIFICATO WAR ROOM ---
        return {
            "successo": True,
            "progetto": nome_progetto,
            "indice_solidita_operativa": indice_solidita,
            "stato": stato_semaforo,
            "diagnostica": report_diagnostico if report_diagnostico else "Tutti i reparti analizzati sono in perfetto equilibrio operativo.",
            "soluzione_ritrovata": azioni_di_rimedio_marketing,
            "impatto_futuro_stimato": "Rischio erosione e contrazione della liquidità di cassa entro 30 giorni se non viene applicata la direttiva di marketing prescritta." if indice_solidita < 85 else "I flussi finanziari e operativi stimati sul lungo termine non mostrano criticità latenti."
        }

    except Exception as err:
        print(f"❌ Errore operativo nel modulo crewEngine: {err}")
        return {
            "successo": False,
            "messaggio": f"Errore interno di calcolo nell'engine: {str(err)}"
        }
        