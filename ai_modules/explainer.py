from ai_modules.gemini_client import chiedi_a_gemini


def spiega_kpi(kpi: dict) -> str:
    prompt = f"""
Sei un assistente aziendale. Spiega questi KPI in modo semplice, chiaro, diretto,
senza linguaggio tecnico inutile, ma con informazioni complete.

KPI:
{kpi}

Scrivi una spiegazione comprensibile anche per un imprenditore non tecnico.
Evita termini complessi. Vai dritto al punto.
"""
    return chiedi_a_gemini(prompt)


def spiega_grafico(descrizione: str, dati: dict) -> str:
    prompt = f"""
Spiega questo grafico in modo semplice e comprensibile.

Descrizione grafico:
{descrizione}

Dati:
{dati}

Spiega cosa significa, cosa indica, e cosa dovrebbe fare l'imprenditore.
"""
    return chiedi_a_gemini(prompt)


def spiega_war_room_strategica(
    azienda: str,
    settore: str,
    solidita: float,
    rischio: float,
    momentum: float,
    ore: int,
    df_str: str,
) -> str:
    """Genera un report predittivo di livello Enterprise a 30/60/90 giorni tramite Gemini."""
    prompt = f"""
Agisci come un Chief Strategy Officer (CSO) di livello Enterprise.
Analizza i dati operativi per l'azienda {azienda} operante nel settore {settore}.

METRICHE CHIAVE:
- Solidità aziendale: {solidita}%
- Rischio Medio: {rischio}/10
- Momentum di crescita: {momentum}
- Ore Analizzate: {ore}h

DETTAGLIO ASSET E VARIANZE:
{df_str}

OBIETTIVO DEL REPORT:
1. Fornisci un'analisi strategica chiara, discorsiva e comprensibile per il board direttivo.
2. Struttura una sezione dedicata con la **Formula Predettiva a 30, 60 e 90 giorni** basata sui trend attuali e sui fattori di rischio emersi.
3. Mantieni un tono professionale, autorevole e orientato all'azione (prescrittivo).
"""
    return chiedi_a_gemini(prompt)
