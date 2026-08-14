"""
Analysis Service - Use Case: Analisi Predittiva del Rischio.
Orchestra i calcoli matematici dei KPI e l'integrazione con l'AI.
"""

import logging
from typing import List, Tuple
import numpy as np

from ai_modules.modelli.factory import AIFactory
from src.application.dto import RiskAnalysisDTO
from src.application.mappers import RiskAnalysisMapper
from src.application.services.base_service import BaseService
from src.domain import Asset, MomentumStatus

logger = logging.getLogger("RGD-Alpha.AnalysisService")


class AnalysisService(BaseService):
    """
    Servizio per l'analisi predittiva del rischio.
    Calcola trend, momentum, volatilità e proiezioni future.
    """

    def __init__(self, kpi_repo=None):
        """Inizializza AnalysisService con il repository KPI e il provider AI."""
        super().__init__("AnalysisService")
        self.kpi_repo = kpi_repo
        # Inizializziamo il provider AI (Gemini/Groq tramite AIFactory)
        self.ai_provider = AIFactory.get_provider("gemini")

    def calculate_strategic_kpis(self, assets: list) -> dict:
        """
        Applica il motore matematico originale RGD-Alpha per KPI globali 
        con normalizzazione dell'impatto.
        """
        if not assets:
            return {
                "rischio_medio": 0.0,
                "solidita": 100.0,
                "impatto_30gg": 0.0,
                "delta_30gg": 0.0,
            }

        # Estrazione dati dagli oggetti Asset
        tot_rischio = sum(
            asset.rischio.value if hasattr(asset.rischio, "value") else asset.rischio
            for asset in assets
        )
        tot_volatilità = sum(getattr(asset, "volatilita", 0.5) for asset in assets)
        conteggio = len(assets)

        # 1. Rischio Medio
        rischio_medio = round(tot_rischio / conteggio, 2)

        # 2. Solidità Operativa (Inversa del rischio)
        solidita = round(max(0.0, min(100.0, 100.0 - (rischio_medio * 9.5))), 1)

        # 3. Impatto Proiettato a 30gg (Normalizzato con Cap a 10.0)
        impatto_grezzo = (tot_volatilità / conteggio) * rischio_medio * 1.5
        impatto_30gg = round(min(10.0, max(0.0, impatto_grezzo)), 2)

        # 4. Delta Rischio stimato a 30 giorni
        delta_30gg = round(impatto_30gg - rischio_medio, 2)

        return {
            "rischio_medio": rischio_medio,
            "solidita": solidita,
            "impatto_30gg": impatto_30gg,
            "delta_30gg": delta_30gg,
        }

    def analyze_asset_risk(
        self, asset: Asset, historical_risks: List[float]
    ) -> RiskAnalysisDTO:
        """
        Analizza il rischio di un asset e genera le proiezioni temporali.
        """
        self.log_info(f"Analisi rischio avviata per asset: {asset.id}")

        # Calcola trend (regressione lineare)
        trend, trend_value = self._calculate_trend(historical_risks)

        # Calcola proiezioni future
        current_risk = (
            asset.rischio.value
            if hasattr(asset.rischio, "value")
            else float(asset.rischio)
        )
        risk_30gg = self._project_risk(current_risk, trend_value, 1)
        risk_60gg = self._project_risk(current_risk, trend_value, 2)
        risk_90gg = self._project_risk(current_risk, trend_value, 3)

        # Genera consiglio strategico (AI o Fallback)
        consiglio = self._generate_advice(asset, trend, risk_90gg)

        # Determina livello di urgenza
        urgenza = self._determine_urgency(current_risk, risk_90gg)

        # Crea e restituisce DTO tramite Mapper
        dto = RiskAnalysisMapper.to_dto(
            asset=asset,
            rischio_attuale=current_risk,
            rischio_30gg=risk_30gg,
            rischio_60gg=risk_60gg,
            rischio_90gg=risk_90gg,
            trend=trend,
            trend_value=trend_value,
            consiglio=consiglio,
            urgenza=urgenza,
            confidenza=0.95,
        )

        self.log_info(f"Analisi completata per {asset.id} → Urgenza: {urgenza}")
        return dto

    def _calculate_trend(self, risks: List[float]) -> Tuple[str, float]:
        """Calcola il trend dei rischi storici tramite regressione lineare."""
        if len(risks) < 2:
            return MomentumStatus.UNDEFINED.value, 0.0

        x = np.arange(len(risks))
        y = np.array(risks)

        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]

        if slope > 0.2:
            trend = MomentumStatus.ACCELERATING.value
        elif slope < -0.2:
            trend = MomentumStatus.DECELERATING.value
        else:
            trend = MomentumStatus.STABLE.value

        return trend, float(slope)

    def _project_risk(self, current_risk: float, trend_slope: float, months: int) -> float:
        """Proietta il rischio futuro limitandolo tra 0.0 e 10.0."""
        projected = current_risk + (trend_slope * months)
        return round(max(0.0, min(10.0, projected)), 2)

    def _determine_urgency(self, current_risk: float, risk_90gg: float) -> str:
        """Determina il livello di urgenza d'intervento."""
        if current_risk >= 7.5 or risk_90gg >= 8.5:
            return "IMMEDIATE"
        elif current_risk >= 5.0 or risk_90gg >= 6.5:
            return "HIGH"
        elif current_risk >= 3.0 or risk_90gg >= 4.5:
            return "MEDIUM"
        return "LOW"

    def _generate_advice(self, asset: Asset, trend: str, risk_90gg: float) -> str:
        """Genera un consiglio strategico potenziato dall'AI con fallback deterministico."""
        current_risk_val = (
            asset.rischio.value
            if hasattr(asset.rischio, "value")
            else asset.rischio
        )

        # 1. Tentativo con AI Provider
        if self.ai_provider:
            try:
                context_str = (
                    f"Asset: {asset.nome}, Rischio Attuale: {current_risk_val}, "
                    f"Trend: {trend}, Proiezione 90gg: {risk_90gg}. "
                    f"Criticità: {'Sì' if asset.is_critical else 'No'}."
                )
                ai_insight = self.ai_provider.generate_advice(context_str)
                if ai_insight:
                    return ai_insight
            except Exception as e:
                logger.warning(
                    f"AI Provider temporaneamente non disponibile, attivato fallback: {e}"
                )

        # 2. FALLBACK Deterministico
        if asset.is_critical:
            return (
                f"AZIONE IMMEDIATA: {asset.nome} è critico (rischio {current_risk_val:.1f}/10). "
                f"Intervento del management richiesto ORA."
            )

        if trend == MomentumStatus.ACCELERATING.value:
            if risk_90gg >= 7.5:
                return (
                    f"ATTENZIONE: {asset.nome} sta accelerando verso livello critico. "
                    f"Pianificare intervento nei prossimi 30 giorni."
                )
            return f"MONITORAGGIO: {asset.nome} mostra un trend negativo. Mantieni sotto controllo."

        if risk_90gg >= 5.0:
            return (
                f"PRECAUZIONE: {asset.nome} potrebbe salire a {risk_90gg:.1f}/10 tra 90 giorni. "
                f"Pianificare azione preventiva."
            )

        return f"STABILE: {asset.nome} mantiene un trend controllato. Continua il monitoraggio."