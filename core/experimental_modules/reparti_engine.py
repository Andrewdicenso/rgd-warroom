# FILE: core/experimental_modules/reparti_engine.py
# SCOPO: Gestione isolata dei dati e dell'interfaccia grafica a 4 sezioni (Tab) per i reparti

import streamlit as st
from pathlib import Path

def mostra_interfaccia_4_aree():
    """
    Disegna visivamente le 4 macro-aree (Tab) sulla pagina
    e restituisce la Macro-Area e il Reparto scelti dall'utente.
    """
    st.markdown("### 🏢 Seleziona Destinazione Documento")
    
    # Creiamo le 4 grandi sezioni visibili sulla pagina come schede
    tab1, tab2, tab3, tab4 = st.tabs([
        "💼 Amministrazione & Controllo", 
        "⚙️ Operativa & Logistica", 
        "📣 Commerciale & Marketing", 
        "👥 Risorse Umane & Servizi"
    ])
    
    macro_scelta = ""
    reparto_scelto = ""
    
    # --- SEZIONE 1: AMMINISTRAZIONE ---
    with tab1:
        st.markdown("##### Seleziona il reparto amministrativo:")
        reparto_amm = st.radio(
            "Reparti:", ["Amministrazione", "Contabilità e Finanza", "Controllo di Gestione"],
            key="rep_amm", label_visibility="collapsed"
        )
        if reparto_amm:
            macro_scelta = "Area Amministrativa e Controllo"
            reparto_scelto = reparto_amm

    # --- SEZIONE 2: OPERATIVA ---
    with tab2:
        st.markdown("##### Seleziona il reparto operativo:")
        reparto_ope = st.radio(
            "Reparti:", ["Acquisti", "Magazzino e Logistica", "Produzione - Erogazione Servizi", "Ufficio Tecnico - Ricerca e Sviluppo"],
            key="rep_ope", label_visibility="collapsed"
        )
        if reparto_ope:
            macro_scelta = "Area Operativa e Logistica"
            reparto_scelto = reparto_ope

    # --- SEZIONE 3: COMMERCIALE ---
    with tab3:
        st.markdown("##### Seleziona il reparto commerciale:")
        reparto_com = st.radio(
            "Reparti:", ["Marketing", "Vendite - Commerciale", "Customer Care - Assistenza Clienti"],
            key="rep_com", label_visibility="collapsed"
        )
        if reparto_com:
            macro_scelta = "Area Commerciale e Comunicazione"
            reparto_scelto = reparto_com

    # --- SEZIONE 4: RISORSE UMANE ---
    with tab4:
        st.markdown("##### Seleziona il reparto servizi e risorse:")
        reparto_hr = st.radio(
            "Reparti:", ["Risorse Umane (HR)", "Sistemi Informativi (IT)", "Affari Legali e Compliance", "Segreteria e Servizi Generali"],
            key="rep_hr", label_visibility="collapsed"
        )
        if reparto_hr:
            macro_scelta = "Area Risorse Umane e Servizi Generali"
            reparto_scelto = reparto_hr

    st.markdown("---")
    
    if reparto_scelto:
        st.info(f"📍 Il documento verrà archiviato in: **{macro_scelta}** ➔ **{reparto_scelto}**")
        
    # Restituiamo le due scelte ad app.py
    return macro_scelta, reparto_scelto


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