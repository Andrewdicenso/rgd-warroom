import streamlit as st
from pathlib import Path

# ==============================================================================
# CONFIGURAZIONE ENTERPRISE: LE 4 MACRO-AREE FOCUS
# ==============================================================================
# Ogni area ha la sua soglia di rischio critica e il suo moltiplicatore di impatto
STRUTTURA_AZIENDALE = {
    "Administration & Finance": {
        "soglia": 6.5, 
        "moltiplicatore": 1.1,
        "descrizione": "Flussi finanziari, bilancio e liquidità."
    },
    "Production & Logistic": {
        "soglia": 7.5, 
        "moltiplicatore": 1.3,
        "descrizione": "Magazzino, produzione e catena di fornitura."
    },
    "Sales & Marketing": {
        "soglia": 7.0, 
        "moltiplicatore": 1.0,
        "descrizione": "Vendite, marketing e gestione clienti."
    },
    "Human Resources & Facilities": {
        "soglia": 8.0, 
        "moltiplicatore": 1.2,
        "descrizione": "Personale, infrastrutture e conformità."
    }
}

def mostra_interfaccia_4_aree():
    """
    Genera l'interfaccia visiva pulita per la War Room.
    Sostituisce i vecchi menu doppi con una selezione singola professionale.
    """
    st.subheader("🏢 Area Focus dell'Analisi")
    aree = list(STRUTTURA_AZIENDALE.keys())
    
    # Selezione singola dell'area (Più chiara per l'utente)
    area_scelta = st.selectbox(
        "Seleziona il Reparto / Area Focus per calibrare l'algoritmo Alpha:", 
        aree,
        help="L'area scelta cambierà i parametri di calcolo del rischio."
    )
    
    info_area = STRUTTURA_AZIENDALE[area_scelta]
    st.info(f"📍 **Area Attiva:** {area_scelta}\n\n🎯 **Focus:** {info_area['descrizione']}")
    
    return {
        "macro_area": area_scelta,
        "reparto": area_scelta, # In questa versione semplificata coincidono
        "config": info_area
    }

def genera_percorso_salvataggio(base_dir, azienda, area_focus, nome_file):
    """
    Genera il percorso sicuro per il salvataggio ad albero.
    Esempio: data/uploads/AZ-1/Production_And_Logistic/file.csv
    """
    # Pulizia nomi per compatibilità Linux/Render
    area_pulita = str(area_focus).replace(" ", "_").replace("&", "And")
    percorso = Path(base_dir) / str(azienda) / area_pulita / nome_file
    return percorso

def analizza_e_configura_motore(area_focus):
    """
    Restituisce la configurazione di rischio specifica per l'area scelta.
    Questa funzione sostituisce la vecchia logica di engine_settori.py.
    """
    config = STRUTTURA_AZIENDALE.get(area_focus, {"soglia": 7.0, "moltiplicatore": 1.0})
    return {
        "settore": area_focus,
        "soglia": config["soglia"],
        "moltiplicatore": config["moltiplicatore"]
    }