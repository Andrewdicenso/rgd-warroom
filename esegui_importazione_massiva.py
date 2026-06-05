py
import os
from datetime import datetime
from core.ingestor import IngestoreDati
from core.database import DatabaseAziendale

def esegui_importazione_massiva(azienda_id):
    ingestor = IngestoreDati()
    db = DatabaseAziendale()
    
    # Percorso allineato alla struttura data/
    cartella_storico = os.path.join("data", "history_import")
    
    if not os.path.exists(cartella_storico):
        print(f"⚠️ Errore: La cartella {cartella_storico} non esiste.")
        return

    # Estendiamo la ricerca a CSV ed EXCEL (come abbiamo fatto nell'ingestore)
    file_presenti = [f for f in os.listdir(cartella_storico) if f.lower().endswith(('.csv', '.xlsx', '.xls'))]
    
    if not file_presenti:
        print("ℹ️ Nessun file trovato: Carica CSV o Excel in data/history_import.")
        return

    print(f"🚀 RGD-ALPHA: Inizio importazione massiva di {len(file_presenti)} file storici...")

    for nome_file in file_presenti:
        path_completo = os.path.join(cartella_storico, nome_file)
        print(f"📄 Elaborazione asset: {nome_file}...")
        
        try:
            # MODIFICATO: Usiamo 'elabora_file' che è la versione potenziata e sicura
            lista_asset = ingestor.elabora_file(path_completo, azienda_id)
            
            # Registriamo l'evento per la supervisione Admin
            db.registra_caricamento(azienda_id, "MIGRAZIONE_STORICA", nome_file)
            print(f"✅ Successo: {len(lista_asset)} asset migrati nel sistema.")
            
        except Exception as e:
            print(f"❌ Errore critico su {nome_file}: {e}")

    print("\n🏆 MIGRAZIONE COMPLETATA: La War Room ora dispone dello storico dati!")

if __name__ == "__main__":
    # Allineato all'ID che abbiamo visto nella dashboard (AZ-1 o AZ-TEST-01)
    esegui_importazione_massiva("AZ-1")