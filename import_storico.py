import os
import pandas as pd
from datetime import datetime
from core.ingestor import IngestoreDati
from core.database import DatabaseAziendale

def esegui_importazione_massiva(azienda_id):
    ingestor = IngestoreDati()
    db = DatabaseAziendale()
    
    # Percorso corretto: punta alla cartella che hai creato prima
    cartella_storico = os.path.join("data", "history_import")
    
    if not os.path.exists(cartella_storico):
        print(f"⚠️ Errore: La cartella {cartella_storico} non esiste.")
        return

    # Cerchiamo tutti i file CSV dentro la cartella
    file_presenti = [f for f in os.listdir(cartella_storico) if f.endswith('.csv')]
    
    if not file_presenti:
        print("ℹ️ Cartella vuota: Inserisci i file CSV in data/history_import per iniziare.")
        return

    print(f"🚀 Inizio importazione di {len(file_presenti)} file storici...")

    for nome_file in file_presenti:
        path_completo = os.path.join(cartella_storico, nome_file)
        print(f"📄 Elaborazione del file storico: {nome_file}...")
        
        try:
            # L'ingestore elabora e mappa i dati automaticamente
            lista_asset = ingestor.elabora_csv(path_completo, azienda_id)
            
            # Registriamo l'evento nel database per vederlo nella Centrale Admin
            db.registra_caricamento(azienda_id, "IMPORT_STORICO", nome_file)
            print(f"✅ Successo: {len(lista_asset)} asset caricati correttamente.")
            
        except Exception as e:
            print(f"❌ Errore durante l'import di {nome_file}: {e}")

    print("\n🏆 Operazione completata: Il database ora contiene i dati del passato!")

if __name__ == "__main__":
    # Avviamo l'import per la tua azienda di test
    esegui_importazione_massiva("AZIENDA_001")