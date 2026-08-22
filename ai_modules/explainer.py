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
