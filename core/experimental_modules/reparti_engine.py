import streamlit as st
import os
from pathlib import Path

# Configurazione ad albero delle Macro-Aree e dei relativi Sotto-Reparti
STRUTTURA_AZIENDALE = {
    "Area Amministrativa e Controllo": [
        "Amministrazione", 
        "Contabilità e Finanza", 
        "Controllo di Gestione"
    ],
    "Area Operativa e Logistica": [
        "Acquisti", 
        "Magazzino e Logistica", 
        "Produzione - Erogazione Servizi", 
        "Ufficio Tecnico - Ricerca e Sviluppo"
    ],
    "Area Commerciale e Comunicazione": [
        "Marketing", 
        "Vendite - Commerciale", 
        "Customer Care - Assistenza Clienti"
    ],
    "Area Risorse Umane e Servizi Generali": [
        "Risorse Umane (HR)", 
        "Sistemi Informativi (IT)", 
        "Affari Legali e Compliance", 
        "Segreteria e Servizi Generali"
    ]
}

def ottieni_macro_aree():
    """Restituisce la lista di tutte le Macro-Aree disponibili."""
    return list(STRUTTURA_AZIENDALE.keys())

def ottieni_reparti_per_macro_area(macro_area):
    """Restituisce i reparti associati a una specifica Macro-Area."""
    return STRUTTURA_AZIENDALE.get(macro_area, [])

def genera_percorso_salvataggio(base_dir, azienda, macro_area, reparto, nome_file):
    """
    Genera il percorso sicuro (Path) in cui salvare il file sul server,
    strutturato come: base_dir/azienda/Macro_Area/Sotto_Reparto/nome_file.ext
    """
    # Puliamo i nomi sostituendo gli spazi con underscore per evitare problemi sui server Linux (Render)
    macro_pulita = macro_area.replace(" ", "_").replace("(", "").replace(")", "")
    reparto_pulito = reparto.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
    
    # Costruiamo il percorso ad albero completo
    percorso_completo = Path(base_dir) / azienda / macro_pulita / reparto_pulito / nome_file
    return percorso_completo
    import streamlit as st

def mostra_interfaccia_4_aree():
    """
    Genera l'interfaccia visiva in Streamlit per la selezione 
    della Macro-Area e del relativo Reparto.
    """
    st.subheader("🏢 Selezione Struttura Aziendale")
    
    col1, col2 = st.columns(2)
    
    with col1:
        macro_aree = ottieni_macro_aree()
        macro_scelta = st.selectbox("Seleziona la Macro-Area:", macro_aree)
        
    with col2:
        reparti_disponibili = ottieni_reparti_per_macro_area(macro_scelta)
        reparto_scelto = st.selectbox("Seleziona il Reparto/Ufficio:", reparti_disponibili)
        
    st.info(f"📍 Destinazione analisi: **{macro_scelta}** > **{reparto_scelto}**")
    
    return {
        "macro_area": macro_scelta,
        "reparto": reparto_scelto
    }