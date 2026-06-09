from ingestor import IngestoreDati

def test_caricamento_legacy():
    ingestore = IngestoreDati()
    
    file_da_caricare = "test_legacy.csv"
    id_azienda_test = "AZ-TEST-01"

    print(f"--- Avvio Importazione Legacy da: {file_da_caricare} ---")
    
    # Eseguiamo l'elaborazione
    import pandas as pd
    import streamlit as st
    try:
        if file_da_caricare.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_da_caricare)
        else:
            df = pd.read_csv(file_da_caricare, sep=None, engine='python')
        if df.empty:
            st.error("⚠️ Il file è vuoto.")
            return
        st.success("✅ File caricato correttamente.")
        # Se il tuo ingestore ha una funzione per elaborare il dataframe usa quella, 
        # altrimenti converti il dataframe in lista per la tua logica successiva:
        lista_asset = df.to_dict('records') 
    except Exception as e:
        st.error(f"❌ Errore nel formato file: {e}")
        return

    # Verifichiamo se la lista contiene qualcosa
    if not lista_asset:
        print("⚠️ Nessun asset creato. Verifica il contenuto del file CSV.")
        return

    print("\n--- Riepilogo Oggetti Creati in Memoria ---")
    for asset in lista_asset:
        # Recupero sicuro degli attributi (usiamo i nomi reali scoperti dai log)
        nome = getattr(asset, 'nome', 'N/D')
        valore = getattr(asset, 'affidabilita', 'N/D')
        rischio = getattr(asset, 'rischio', 'N/D')
        data_effettiva = getattr(asset, 'data_rilevazione', 'Non definita')
        
        print(f"Asset: {nome} | Affidabilità: {valore} | Rischio: {rischio} | Data: {data_effettiva}")

if __name__ == "__main__":
    test_caricamento_legacy()