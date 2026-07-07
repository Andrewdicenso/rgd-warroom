"""
KPI Repository - Gestione dello storico rischi su Supabase.
Fornisce i dati per l'analisi predittiva del motore RGD-Alpha.
"""
from typing import List, Optional
from src.infrastructure.persistence.repositories.base_repository import BaseRepository
from src.infrastructure.persistence.db.connection import DatabaseConnection

class KPIRepository(BaseRepository):
    def __init__(self, db: DatabaseConnection):
        # Inizializza la classe base con il nome della tabella
        super().__init__("kpi_history")
        self.supabase = db.get_client()

    def find_history_for_asset(self, asset_id: str, limit: int = 12) -> List[float]:
        """
        Recupera gli ultimi N punteggi di rischio per un asset.
        Necessario per la regressione lineare dell'AnalysisService.
        """
        try:
            response = self.supabase.table("kpi_history") \
                .select("rischio") \
                .eq("asset_id", asset_id) \
                .order("data", desc=True) \
                .limit(limit) \
                .execute()
            
            # Ritorna i valori dal più vecchio al più recente per il calcolo del trend
            return [float(row['rischio']) for row in reversed(response.data)]
        except Exception:
            return []

    def record_kpi(self, asset_id: str, user_id: str, rischio: float) -> bool:
        """Registra un nuovo punto nello storico dei rischi."""
        data = {
            "asset_id": asset_id,
            "user_id": user_id,
            "rischio": rischio
        }
        try:
            response = self.supabase.table("kpi_history").insert(data).execute()
            return len(response.data) > 0
        except Exception:
            return False

    # === IMPLEMENTAZIONE METODI OBBLIGATORI (BaseRepository) ===

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