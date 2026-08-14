"""
Analysis Service - Use Case: Analisi Predittiva del Rischio.
"""
import numpy as np
import logging
from typing import List
from src.domain import Asset, MomentumStatus
from src.application.services.base_service import BaseService
from src.application.mappers import RiskAnalysisMapper
from src.application.dto import RiskAnalysisDTO
from ai_modules.modelli.factory import AIFactory

logger = logging.getLogger("RGD-Alpha.AnalysisService")

class AnalysisService(BaseService):
    """
    Servizio per analisi predittiva del rischio.
    Calcola trend, momentum, volatilità e proiezioni future.
    """
    
    def __init__(self, kpi_repo=None):
        """Inizializza AnalysisService con il repository KPI e il provider AI."""
        super().__init__("AnalysisService")
        self.kpi_repo = kpi_repo
        # Inizializziamo il provider AI (Groq di default)
        self.ai_provider = AIFactory.get_provider("groq")

    def calculate_strategic_kpis(self, assets: list):
        """
        Applica il motore matematico originale RGD-Alpha per KPI globali con normalizzazione dell'impatto.
        """
        if not assets:
            return {"rischio_medio": 0.0, "solidita": 100.0, "impatto_30gg": 0.0, "delta_30gg": 0.0}

        # Estrazione dati dagli oggetti Asset
        tot_rischio = sum(asset.rischio.value if hasattr(asset.rischio, 'value') else asset.rischio for asset in assets)
        tot_volatilità = sum(getattr(asset, 'volatilita', 0.5) for asset in assets)
        conteggio = len(assets)

        # 1. Rischio Medio (Formula originale)
        rischio_medio = round(tot_rischio / conteggio, 2)
        
        # 2. Solidità Operativa (Formula originale: inversa del rischio)
        solidita = round(max(0.0, min(100.0, 100.0 - (rischio_medio * 9.5))), 1)
        
        # 3. Impatto Proiettato a 30gg (Miglioria: Normalizzato con Cap a 10.0)
        impatto_grezzo = (tot_volatilità / conteggio) * rischio_medio * 1.5
        impatto_30gg = round(min(10.0, max(0.0, impatto_grezzo)), 2)

        # 4. Delta Rischio stimato a 30 giorni
        delta_30gg = round(impatto_30gg - rischio_medio, 2)

        return {
            "rischio_medio": rischio_medio,
            "solidita": solidita,
            "impatto_30gg": impatto_30gg,
            "delta_30gg": delta_30gg
        }
    
    def analyze_asset_risk(
        self,
        asset: Asset,
        historical_risks: List[float]
    ) -> RiskAnalysisDTO:
        """
        Analizza il rischio di un asset.
        
        Args:
            asset: Asset da analizzare
            historical_risks: Lista di rischi storici (trend)
            
        Returns:
            RiskAnalysisDTO con previsioni
        """
        self.log_info(f"Analyzing risk for asset {asset.id}")
        
        # Calcola trend (regressione lineare)
        trend, trend_value = self._calculate_trend(historical_risks)
        
        # Calcola proiezioni future
        current_risk = asset.rischio.value if hasattr(asset.rischio, 'value') else float(asset.rischio)
        risk_30gg = self._project_risk(current_risk, trend_value, 1)
        risk_60gg = self._project_risk(current_risk, trend_value, 2)
        risk_90gg = self._project_risk(current_risk, trend_value, 3)
        
        # Genera consiglio strategico (AI o Fallback)
        consiglio = self._generate_advice(asset, trend, risk_90gg)
        
        # Determina urgenza
        urgenza = self._determine_urgency(current_risk, risk_90gg)
        
        # Crea DTO
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
            confidenza=0.85
        )
        
        self.log_info(f"Risk analysis complete: {asset.id} → {urgenza}")
        
        return dto
    
    def _calculate_trend(self, risks: List[float]) -> tuple[str, float]:
        """
        Calcola il trend dei rischi storici.
        
        Args:
            risks: Lista di rischi nel tempo
            
        Returns:
            (trend_name, trend_value) dove trend_value è la pendenza
        """
        if len(risks) < 2:
            return MomentumStatus.UNDEFINED.value, 0.0
        
        # Regressione lineare semplice
        x = np.arange(len(risks))
        y = np.array(risks)
        
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
        
        # Classifica trend
        if slope > 0.2:
            trend = MomentumStatus.ACCELERATING.value
        elif slope < -0.2:
            trend = MomentumStatus.DECELERATING.value
        else:
            trend = MomentumStatus.STABLE.value
        
        return trend, float(slope)
    
    def _project_risk(self, current_risk: float, trend_slope: float, months: int) -> float:
        """
        Proietta il rischio futuro basato sul trend.
        
        Args:
            current_risk: Rischio attuale
            trend_slope: Pendenza del trend (da regressione)
            months: Mesi nel futuro
            
        Returns:
            Rischio proiettato (0-10)
        """
        projected = current_risk + (trend_slope * months)
        
        # Clamp tra 0 e 10
        return round(max(0.0, min(10.0, projected)), 2)
    
    def _generate_advice(self, asset: Asset, trend: str, risk_90gg: float) -> str:
        """Genera consiglio strategico potenziato dall'AI con fallback deterministico sicuro."""

        # 1. Proviamo a usare l'AI se il provider è configurato
        if self.ai_provider:
            try:
                current_risk_val = asset.rischio.value if hasattr(asset.rischio, 'value') else asset.rischio
                context_str = (
                    f"Asset: {asset.nome}, Rischio Attuale: {current_risk_val}, "
                    f"Trend: {trend}, Proiezione 90gg: {risk_90gg}. "
                    f"Criticità: {'Sì' if asset.is_critical else 'No'}."
                )
                ai_insight = self.ai_provider.generate_advice(context_str)

                if ai_insight:
                    return ai_insight
            except Exception as e:
                logger.warning(f"AI Provider temporaneamente non disponibile, attivato fallback deterministico: {e}")

        # 2. FALLBACK: Se l'AI fallisce o non è disponibile, usiamo la logica originale
        current_risk_val = asset.rischio.value if hasattr(asset.rischio, 'value') else asset.rischio

        if asset.is_critical:
            return f"AZIONE IMMEDIATA: {asset.nome} è critico (rischio {current_risk_val:.1f}/10). Intervento management richiesto NOW."

        if trend == MomentumStatus.ACCELERATING.value:
            if risk_90gg >= 7.5:
                return f"ATTENZIONE: {asset.nome} sta accelerando verso critico. Pianificare intervento nei prossimi 30gg."
            return f"MONITORAGGIO: {asset.nome} trend negativo. Mantieni sotto controllo."

        if risk_90gg >= 5.0:
            return f"PRECAUZIONE: {asset.nome} probabilmente salirà a {risk_90gg:.1f}/10 tra 90gg. Pianificare azione."

        return f"STABILE: {asset.nome} mantiene trend positivo. Continua monitoraggio."