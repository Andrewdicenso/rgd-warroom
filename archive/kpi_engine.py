from typing import Any, Dict, Optional

import pandas as pd

from core.analyst import AnalistaRischio
from core.database import DatabaseAziendale


def compute_financial_kpis(
    df: pd.DataFrame, 
    company_id: str = "DEFAULT_CLIENT",
    asset_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Motore di Calcolo KPI Strategici e Finanziari.
    Normalizza le colonne, calcola la qualità del dato, estrae aggregati monetari 
    ed esegue l'analisi predittiva sul trend storico dell'asset.
    """
    if df.empty:
        return {"error": "Dataframe vuoto", "risk_score": 10.0, "risk_level": "ALTO"}

    df.columns = [str(col).strip().lower() for col in df.columns]
    
    total_rows = int(len(df))
    total_cells = max(int(df.size), 1)
    null_count = int(df.isnull().sum().sum())
    completeness = float(round((1 - null_count / total_cells) * 100, 2))
    
    if not asset_name:
        if any(c in df.columns for c in ['prezzo', 'importo', 'valore', 'netwr']):
            asset_name = "Finanza"
        elif any(c in df.columns for c in ['quantita', 'pezzi', 'menge', 'sku']):
            asset_name = "Magazzino"
        else:
            asset_name = "Generico"

    db_aziendale = DatabaseAziendale()
    analista = AnalistaRischio(db=db_aziendale)
    
    trend_analysis = analista.calcola_trend_predittivo(
        nome_asset=asset_name, 
        company_id=company_id
    )
    
    valore_attuale = trend_analysis.get("valore_attuale")
    if valore_attuale is not None and valore_attuale > 0:
        risk_score = float(valore_attuale)
    else:
        risk_score = float(max(1.0, round((100 - completeness) / 10, 2)))
    
    risk_level = "ALTO" if risk_score > 7.0 else ("MEDIO" if risk_score > 5.0 else "BASSO")

    totale_valore = 0.0
    for col_valore in ['importo', 'valore', 'prezzo', 'netwr', 'dmbtr']:
        if col_valore in df.columns:
            totale_valore = float(pd.to_numeric(df[col_valore], errors='coerce').sum())
            break

    return {
        "asset_analyzed": asset_name,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "completeness_rate": f"{completeness}%",
        "total_records_analyzed": total_rows,
        "monetary_summary": {
            "total_value_detected": round(totale_valore, 2),
            "has_financial_data": totale_valore > 0
        },
        "trend_momentum": {
            "pendenza": trend_analysis.get("pendenza_trend", 0.0),
            "volatilita": trend_analysis.get("indice_volatilita", 0.0),
            "momentum_perc": trend_analysis.get("momentum_percentuale", "0%"),
            "valutazione": trend_analysis.get("valutazione_strategica", "RACCOLTA DATI")
        },
        "ai_strategic_action_plan": [
            {
                "target": f"Ingegneria di Processo ({asset_name})",
                "action": trend_analysis.get("azione", "Monitorare l'andamento delle ore reali e dei flussi."),
                "urgency": "ALTA" if risk_level == "ALTO" else "MEDIA"
            }
        ],
        "summary_metrics": {
            "columns_found": list(df.columns),
            "data_quality_status": "OTTIMALE" if completeness > 90 else "ATTENZIONE"
        }
    }