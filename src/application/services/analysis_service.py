"""
Analysis Service - Use Case: Analisi Predittiva del Rischio.
"""
import numpy as np
from typing import List
from src.domain import Asset, MomentumStatus
from src.application.services.base_service import BaseService
from src.application.mappers import RiskAnalysisMapper
from src.application.dto import RiskAnalysisDTO


class AnalysisService(BaseService):
    """
    Servizio per analisi predittiva del rischio.
    Calcola trend, momentum, volatilità e proiezioni future.
    """
    
    def __init__(self, kpi_repo=None):
        """Inizializza AnalysisService con il repository KPI."""
        super().__init__("AnalysisService")
        self.kpi_repo = kpi_repo

    def calculate_strategic_kpis(self, assets: list):
        """
        Applica il motore matematico originale RGD-Alpha per KPI globali.
        """
        if not assets:
            return {"rischio_medio": 0.0, "solidita": 100.0, "impatto_30gg": 0.0}

        # Estrazione dati dagli oggetti Asset
        tot_rischio = sum(asset.rischio.value if hasattr(asset.rischio, 'value') else asset.rischio for asset in assets)
        # Nota: Usiamo 0.5 come volatilità di default se non presente
        tot_volatilità = sum(getattr(asset, 'volatilita', 0.5) for asset in assets)
        conteggio = len(assets)

        # 1. Rischio Medio (La tua formula originale)
        rischio_medio = round(tot_rischio / conteggio, 2)
        
        # 2. Solidità Operativa (La tua formula originale: inversa del rischio)
        solidita = round(max(0.0, min(100.0, 100.0 - (rischio_medio * 9.5))), 1)
        
        # 3. Impatto Proiettato a 30gg (La tua formula originale)
        impatto_30gg = round((tot_volatilità / conteggio) * rischio_medio * 1.5, 2)

        return {
            "rischio_medio": rischio_medio,
            "solidita": solidita,
            "impatto_30gg": impatto_30gg
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
        current_risk = asset.rischio.value
        risk_30gg = self._project_risk(current_risk, trend_value, 1)
        risk_60gg = self._project_risk(current_risk, trend_value, 2)
        risk_90gg = self._project_risk(current_risk, trend_value, 3)
        
        # Genera consiglio strategico
        consiglio = self._generate_advice(asset, trend, risk_90gg)
        
        # Determina urgenza
        urgenza = self._determine_urgency(asset.rischio.value, risk_90gg)
        
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
        return max(0.0, min(10.0, projected))
    
    def _generate_advice(self, asset: Asset, trend: str, risk_90gg: float) -> str:
        """Genera consiglio strategico basato su analisi."""
        if asset.is_critical:
            return f"AZIONE IMMEDIATA: {asset.nome} è critico (rischio {asset.rischio.value:.1f}/10). Intervento management richiesto NOW."
        
        if trend == MomentumStatus.ACCELERATING.value:
            if risk_90gg >= 7.5:
                return f"ATTENZIONE: {asset.nome} sta accelerando verso critico. Planificare intervento nei prossimi 30gg."
            else:
                return f"MONITORAGGIO: {asset.nome} trend negativo. Mantieni sotto controllo."
        
        if risk_90gg >= 5.0:
            return f"PRECAUZIONE: {asset.nome} probabilmente salirà a {risk_90gg:.1f}/10 tra 90gg. Pianificare azione."
        
        return f"STABILE: {asset.nome} mantiene trend positivo. Continua monitoraggio."
    
    def _determine_urgency(self, current_risk: float, future_risk: float) -> str:
        """Determina il livello di urgenza."""
        if current_risk >= 7.5:
            return "IMMEDIATE"
        
        if future_risk >= 7.5 and (future_risk - current_risk) > 1.0:
            return "HIGH"
        
        if current_risk >= 5.0 or future_risk >= 6.0:
            return "MEDIUM"
        
        return "LOW"
