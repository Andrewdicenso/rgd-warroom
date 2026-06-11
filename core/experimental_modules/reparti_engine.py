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
    st.subheader("🏢 Seleziona Dipartimento")
    aree = list(STRUTTURA_AZIENDALE.keys())
    

    # Selezione singola dell'area (Più chiara per l'utente)
    area_scelta = st.selectbox(
        "Dipartimento:", 
        aree,
        help="L'area scelta cambierà i parametri di calcolo del rischio."
    )
    
    info_area = STRUTTURA_AZIENDALE[area_scelta]
    st.info(f"📍 **Area Attiva:** {area_scelta}\n\n🎯 **Focus:** {info_area['descrizione']}")
    
    return {
        "Dipartimento": area_scelta,
        "config": info_area
    }

def genera_percorso_salvataggio(base_dir, azienda, area_focus, nome_file):
    """
    Genera un percorso sicuro e compatibile con Render per salvare i file.
    Esempio finale:
    /tmp/rgd_uploads/AZ-1/Production_And_Logistic/file.csv
    """

    # Pulizia nomi per compatibilità Linux/Render
    azienda_pulita = str(azienda).replace(" ", "_").replace("&", "And")
    area_pulita = str(area_focus).replace(" ", "_").replace("&", "And")

    # Costruzione percorso
    percorso = Path(base_dir) / azienda_pulita / area_pulita

    # Creazione cartelle (Render non le crea da solo)
    percorso.mkdir(parents=True, exist_ok=True)

    # Percorso finale completo
    return percorso / nome_file


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