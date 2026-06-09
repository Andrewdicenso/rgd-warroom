# FILE: core/experimental_modules/reparti_engine.py
# SCOPO: Gestione isolata dei dati e dell'interfaccia grafica a 4 sezioni (Tab) per i reparti

import streamlit as st
from pathlib import Path

def mostra_interfaccia_4_aree():
    """
    Versione VIP: Gestisce solo i 4 Pilastri Strategici.
    Restituisce solo la Macro-Area scelta (Senza sottovoci).
    """
    st.markdown("### 🏢 Seleziona Destinazione Documento")
    
    # Creiamo i 4 grandi pilastri come bottoni orizzontali
    pilastri = [
        "💼 Amministrazione & Controllo", 
        "⚙️ Operativa & Logistica", 
        "📣 Commerciale & Marketing", 
        "👥 Risorse Umane & Servizi"
    ]
    
    # Usiamo un radio button orizzontale per massima pulizia
    macro_scelta = st.radio(
        "Seleziona il pilastro di destinazione:",
        options=pilastri,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    if macro_scelta:
        st.info(f"📍 Destinazione impostata: **{macro_scelta}**")
        
    # Restituiamo la scelta. Reparto scelto è uguale a macro_scelta perché abbiamo tolto le sottovoci.
    return macro_scelta, macro_scelta

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