"""
KPI Repository - Gestione dello storico rischi su Supabase.
Fornisce i dati per l'analisi predittiva del motore RGD-Alpha.
"""
from typing import List
from src.infrastructure.persistence.repositories.base_repository import BaseRepository
from src.infrastructure.persistence.db.connection import DatabaseConnection

class KPIRepository(BaseRepository):
    def __init__(self, db: DatabaseConnection):
        super().__init__("KPI")
        self.supabase = db.get_client()

    def find_history_for_asset(self, asset_id: str, limit: int = 12) -> List[float]:
        """
        Recupera gli ultimi N punteggi di rischio per un asset.
        Necessario per la regressione lineare dell'AnalysisService.
        """
        response = self.supabase.table("kpi_history") \
            .select("rischio") \
            .eq("asset_id", asset_id) \
            .order("data", desc=True) \
            .limit(limit) \
            .execute()
        
        # Ritorna i valori dal più vecchio al più recente per il calcolo del trend
        return [float(row['rischio']) for row in reversed(response.data)]

    def record_kpi(self, asset_id: str, user_id: str, rischio: float) -> bool:
        """Registra un nuovo punto nello storico dei rischi."""
        data = {
            "asset_id": asset_id,
            "user_id": user_id,
            "rischio": rischio
        }
        response = self.supabase.table("kpi_history").insert(data).execute()
        return len(response.data) > 0
            
    def record_kpi(self, asset_id: str, user_id: str, rischio: float) -> bool:
        """Registra un nuovo punto nello storico dei rischi."""
        data = {
            "asset_id": asset_id,
            "user_id": user_id,
            "rischio": rischio
        }
        response = self.supabase.table("kpi_history").insert(data).execute()
        return len(response.data) > 0

    # === AGGIUNGI QUESTI METODI PER RISOLVERE IL TYPERROR ===

    def create(self, data: dict):
        """Implementazione obbligatoria per BaseRepository"""
        return self.supabase.table("kpi_history").insert(data).execute()

    def read(self, id: str):
        """Implementazione obbligatoria per BaseRepository"""
        return self.supabase.table("kpi_history").select("*").eq("id", id).execute()

    def update(self, id: str, data: dict):
        """Implementazione obbligatoria per BaseRepository"""
        return self.supabase.table("kpi_history").update(data).eq("id", id).execute()

    def delete(self, id: str):
        """Implementazione obbligatoria per BaseRepository"""
        return self.supabase.table("kpi_history").delete().eq("id", id).execute()

    def list_all(self):
        """Implementazione obbligatoria per BaseRepository"""
        return self.supabase.table("kpi_history").select("*").execute()