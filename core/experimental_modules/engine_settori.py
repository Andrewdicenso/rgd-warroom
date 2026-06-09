# FILE: experimental_modules/engine_settori.py
# SCOPO: Mappatura intelligente e configurazione dinamica del motore RGD-Alpha

import pandas as pd
import pypdf

SETTORI_CONFIG = {
    "PRIMARIO_ALIMENTARE": {
        "keywords": ["scadenza", "lotto", "haccp", "temperatura", "fresco", "conservazione"],
        "soglia_critica": 6.5,
        "label": "Qualità e Deperibilità",
        "action_plan": "Verificare immediatamente scadenze imminenti e integrità catena del freddo.",
        "moltiplicatore_rischio": 1.3
    },
    "SECONDARIO_MANIFATTURA": {
        "keywords": ["taglia", "materia prima", "produzione", "stock", "pezzi", "semilavorato"],
        "soglia_critica": 7.5,
        "label": "Continuità Produttiva",
        "action_plan": "Monitorare colli di bottiglia in produzione e disponibilità materie prime.",
        "moltiplicatore_rischio": 1.1
    },
    "TERZIARIO_LOGISTICA": {
        "keywords": ["bolla", "ddt", "targa", "consegna", "ritardo", "vettore", "spedizione"],
        "soglia_critica": 8.0,
        "label": "Efficienza Distributiva",
        "action_plan": "Analizzare lead time dei vettori e ottimizzare rotte di distribuzione.",
        "moltiplicatore_rischio": 1.0
    },
    "EDILE_COSTRUZIONI": {
        "keywords": ["cantiere", "commessa", "ponteggio", "cemento", "sicurezza", "dpi", "subappalto"],
        "soglia_critica": 7.0,
        "label": "Sicurezza e Commesse",
        "action_plan": "Revisione immediata scadenze di cantiere e conformità DPI/Sicurezza.",
        "moltiplicatore_rischio": 1.2
    },
    "FASHION_RETAIL": {
        "keywords": ["collezione", "taglia", "colore", "sku", "stagione", "invenduto", "reso"],
        "soglia_critica": 7.8,
        "label": "Rotazione Stagionale",
        "action_plan": "Analisi rapida dell'invenduto stagionale. Pianificare promozioni mirate.",
        "moltiplicatore_rischio": 1.05
    }
}

def analizza_e_configura_motore(lista_colonne):
    """
    Analizza i metadati del file (colonne) eliminando spazi e standardizzando 
    il testo per garantire il riconoscimento del settore, ispezionando anche 
    le chiavi annidate in dati_extra se presenti.
    """
    colonne_pulite = [str(col).strip().lower() for col in lista_colonne]
    
    if "dati_extra" in colonne_pulite:
        colonne_pulite.extend(["scadenza", "lotto", "id_asset"])
    
    colonne_str = " ".join(colonne_pulite)
    
    for settore, config in SETTORI_CONFIG.items():
        if any(key in colonne_str for key in config["keywords"]):
            return {
                "settore": settore,
                "soglia": config["soglia_critica"],
                "descrizione": config["label"],
                "consiglio": config["action_plan"],
                "moltiplicatore": config["moltiplicatore_rischio"]
            }
            
    return {
        "settore": "GENERALE",
        "soglia": 7.0,
        "descrizione": "Analisi Strategica Standard",
        "consiglio": "Monitoraggio periodico dei KPI standard di rischio.",
        "moltiplicatore": 1.0
    }


# =====================================================================
# --- NUOVO MODULO: LOGICA WARROOM (CATEGORIE: PESO, QUANTITÀ, TEMPO) ---
# =====================================================================

CONFIG_MACRO_CATEGORIE = {
    "PESO": {
        "unita": ["kg", "chili", "tonnellate", "litri", "metri cubi", "mc", "massa", "volume"],
        "info_calcolo": "Calcolo basato su Massa e Volume di merci sfuse o liquidi."
    },
    "QUANTITA": {
        "unita": ["pezzi", "unita", "lotti", "confezioni", "scatole", "numero", "sku"],
        "info_calcolo": "Calcolo rigoroso a unità o conteggio pezzi a inventario."
    },
    "TEMPO_SERVIZIO": {
        "unita": ["ore", "ore lavoro", "visualizzazioni", "transazioni", "tratte", "chilometri", "giorni", "abbonamenti"],
        "info_calcolo": "Calcolo basato su prestazioni orarie, servizi erogati o tempo di utilizzo."
    }
}

def estrai_testo_da_file_warroom(file_caricato):
    """
    Estrae in modo sicuro una stringa di testo da file Excel, CSV o PDF 
    senza salvare nulla sul server (elaborazione in memoria).
    """
    try:
        nome_file = file_caricato.name.lower()
        
        if nome_file.endswith('.csv'):
            df = pd.read_csv(file_caricato, nrows=5)
            colonne = ", ".join(df.columns.astype(str))
            anteprima = df.to_string(index=False)
            return f"FILE TABELLARE CSV\nColonne: {colonne}\nDati:\n{anteprima}"
            
        elif nome_file.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_caricato, nrows=5)
            colonne = ", ".join(df.columns.astype(str))
            anteprima = df.to_string(index=False)
            return f"FILE TABELLARE EXCEL\nColonne: {colonne}\nDati:\n{anteprima}"
            
        elif nome_file.endswith('.pdf'):
            lettore = pypdf.PdfReader(file_caricato)
            testo_estratto = ""
            for i in range(min(2, len(lettore.pages))):
                testo_estratto += lettore.pages[i].extract_text() + "\n"
            return f"DOCUMENTO PDF\nContenuto:\n{testo_estratto[:1500]}"
            
    except Exception as e:
        return f"Errore durante l'estrazione del testo: {str(e)}"
    
    return "Formato file non supportato."

def classifica_documento_warroom(testo_estratto):
    """
    Analizza il testo normalizzato. Al momento simula l'analisi semantica 
    in attesa dell'attivazione dell'API Key per l'AI Micro, garantendo 
    che il sistema non vada mai in crash.
    """
    testo_minuscolo = testo_estratto.lower()
    
    # Controllo rapido tramite parole chiave per decidere la categoria in sicurezza
    for categoria, configurazione in CONFIG_MACRO_CATEGORIE.items():
        if any(parola in testo_minuscolo for parola in configurazione["unita"]):
            return {
                "categoria": categoria,
                "dettaglio": configurazione["info_calcolo"],
                "stato_ai": "Simulazione locale attiva"
            }
            
    # Risposta di fallback se il documento è ambiguo
    return {
        "categoria": "QUANTITA",
        "dettaglio": "Categoria assegnata automaticamente (Default a Pezzi/Unità).",
        "stato_ai": "Simulazione locale attiva (Fallback)"
    }