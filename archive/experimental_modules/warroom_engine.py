# FILE: core/experimental_modules/warroom_engine.py
# SCOPO: Motore di classificazione autonomo per il modulo WarRoom (PESO, QUANTITÀ, TEMPO)

import pandas as pd

CONFIG_MACRO_CATEGORIE = {
    "PESO": {
        "unita": [
            "kg",
            "chili",
            "tonnellate",
            "litri",
            "metri cubi",
            "mc",
            "massa",
            "volume",
        ],
        "info_calcolo": "Calcolo basato su Massa e Volume di merci sfuse o liquidi.",
    },
    "QUANTITA": {
        "unita": ["pezzi", "unita", "lotti", "confezioni", "scatole", "numero", "sku"],
        "info_calcolo": "Calcolo rigoroso a unità o conteggio pezzi a inventario.",
    },
    "TEMPO_SERVIZIO": {
        "unita": [
            "ore",
            "ore lavoro",
            "visualizzazioni",
            "transazioni",
            "tratte",
            "chilometri",
            "giorni",
            "abbonamenti",
        ],
        "info_calcolo": "Calcolo basato su prestazioni orarie, servizi erogati o tempo di utilizzo.",
    },
}


def analizza_file_tabellare(file_caricato):
    """
    Legge l'anteprima di un file Excel o CSV caricato dall'utente
    ed estrae i nomi delle colonne per capire il contesto aziendale.
    """
    try:
        nome_file = file_caricato.name.lower()

        if nome_file.endswith(".csv"):
            df = pd.read_csv(file_caricato, nrows=3)
        elif nome_file.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_caricato, nrows=3)
        else:
            return None, "Formato file non supportato. Carica un Excel o un CSV."

        # Uniamo i nomi delle colonne in un'unica stringa di testo da analizzare
        testo_da_analizzare = " ".join(df.columns.astype(str)).lower()
        return testo_da_analizzare, None

    except Exception as e:
        return None, f"Errore di lettura del file: {str(e)}"


def assegna_categoria_warroom(file_caricato):
    """
    Funzione principale richiamata da Streamlit.
    Riceve il file, analizza le colonne e assegna la macro-categoria adeguata.
    """
    testo_colonne, errore = analizza_file_tabellare(file_caricato)

    if errore:
        return {"errore": errore}

    # Scansione delle keyword per determinare la categoria
    for categoria, configurazione in CONFIG_MACRO_CATEGORIE.items():
        if any(parola in testo_colonne for parola in configurazione["unita"]):
            return {
                "categoria": categoria,
                "dettaglio": configurazione["info_calcolo"],
                "successo": True,
            }

    # Assegnazione di default se non trova corrispondenze specifiche nelle colonne
    return {
        "categoria": "QUANTITA",
        "dettaglio": "Categoria assegnata automaticamente (Default a Pezzi/Unità).",
        "successo": True,
    }
