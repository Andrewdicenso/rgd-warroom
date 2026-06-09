import os
import pandas as pd
import streamlit as st
from ingestor import IngestoreDati

# Configurazione per il test in locale senza Streamlit UI attivo
class MockFile:
    """Simula l'oggetto file di Streamlit per il test autonomo."""
    def __init__(self, file_path):
        self.name = os.path.basename(file_path)
        self.path = file_path
    
    def __str__(self):
        return self.name

def elabora_caricamento_vip(file_da_caricare):
    """
    Sistema di Ingestione Intelligente per Documenti, Fogli di Calcolo e PDF.
    Rileva formati non conformi o manomissioni manuali.
    """
    estensione = os.path.splitext(file_da_caricare.name)[1].lower()
    
    # 1. DEFINIZIONE FORMATI AUTORIZZATI
    FORMATI_TESTO = ['.docx', '.doc', '.odt', '.pdf']
    FORMATI_DATI = ['.xlsx', '.xls', '.csv', '.ods']
    FORMATI_SLIDE = ['.pptx', '.ppt', '.odp']
    
    TUTTI_I_FORMATI = FORMATI_TESTO + FORMATI_DATI + FORMATI_SLIDE

    if estensione not in TUTTI_I_FORMATI:
        st.error(f"❌ Formato '{estensione}' non supportato. Carica documenti Standard Microsoft, OpenSource o PDF.")
        return None

    # 2. CONTROLLO INTEGRITÀ (Simulazione rilevamento manomissione manuale)
    scritte_manuali_rilevate = False # Questa variabile verrebbe dal tuo core engine
    
    if scritte_manuali_rilevate:
        st.warning("⚠️ ATTENZIONE: Il sistema ha rilevato modifiche manuali o scritte aggiuntive nel documento.")
        conferma = st.checkbox("Dichiaro di accettare le modifiche manuali rilevate e procedere con l'elaborazione.")
        if not conferma:
            st.info("In attesa di conferma dall'utente per procedere...")
            return None

    # 3. SMISTAMENTO ALL'ENGINE DI ESECUZIONE
    try:
        st.success(f"✅ File '{file_da_caricare.name}' riconosciuto. Avvio estrazione dati...")
        
        # Gestione per i fogli di calcolo e CSV
        if estensione in FORMATI_DATI:
            # Se stiamo usando il file reale di Streamlit passiamo l'oggetto, altrimenti il percorso stringa nel mock
            target_file = getattr(file_da_caricare, 'path', file_da_caricare)
            
            if estensione == '.csv':
                df = pd.read_csv(target_file, sep=None, engine='python')
            else:
                df = pd.read_excel(target_file)
                
            if df.empty:
                st.error("⚠️ Il file è vuoto.")
                return None
                
            return df.to_dict('records')
            
        # Per gli altri formati (PDF, DOCX, PPTX) estendere qui la logica custom
        st.warning(f"ℹ️ Formato {estensione} valido, ma l'estrazione testo non è ancora implementata.")
        return None
        
    except Exception as e:
        st.error(f"❌ Errore durante l'estrazione dati: {e}")
        return None

def test_caricamento_legacy():
    # Inizializzazione (mantenuta per retrocompatibilità)
    ingestore = IngestoreDati() 
    id_azienda_test = "AZ-TEST-01"
    
    # Allineamento: Trasformiamo la stringa in un oggetto compatibile con l'attributo .name
    file_stringa = "test_legacy.csv"
    file_compatibile = MockFile(file_stringa)

    print(f"--- Avvio Importazione Intelligente da: {file_compatibile.name} ---")
    
    # Eseguiamo l'elaborazione tramite il nuovo engine intelligente
    lista_asset = elabora_caricamento_vip(file_compatibile)

    # Verifichiamo se la lista contiene qualcosa
    if not lista_asset:
        print("⚠️ Nessun asset creato. Verifica il contenuto del file o il formato.")
        return

    print("\n--- Riepilogo Oggetti Creati in Memoria ---")
    for asset in lista_asset:
        # CORREZIONE: Essendo dizionari e non oggetti, usiamo .get() al posto di getattr()
        nome = asset.get('nome', 'N/D')
        valore = asset.get('affidabilita', asset.get('valore', 'N/D')) # Fallback se la colonna cambia nome
        rischio = asset.get('rischio', 'N/D')
        data_effettiva = asset.get('data_rilevazione', 'Non definita')
        
        print(f"Asset: {nome} | Affidabilità: {valore} | Rischio: {rischio} | Data: {data_effettiva}")

# --- BLOCCO DI ESECUZIONE (Streamlit UI o Script Locale) ---
if __name__ == "__main__":
    # Se lo script viene lanciato normalmente da terminale esegue il test
    # Se viene lanciato con `streamlit run`, mostra l'interfaccia web
    if st.runtime.exists():
        st.title("Data Ingestion Gateway")
        file_caricato = st.file_uploader("Trascina qui il tuo documento", type=None)
        if file_caricato:
            risultato = elabora_caricamento_vip(file_caricato)
            if risultato:
                st.session_state['dati_pronti'] = True
                st.json(risultato[:3]) # Mostra un'anteprima dei primi 3 record
    else:
        # Esecuzione del test di simulazione offline
        test_caricamento_legacy()