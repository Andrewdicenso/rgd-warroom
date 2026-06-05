import sys
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np

# ==============================================================================
# RISOLUZIONE DINAMICA DEL PATH
# ==============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.secure_vault import SecureVault
from core.database import DatabaseAziendale
from core.experimental_modules.engine_settori import analizza_e_configura_motore

logger = logging.getLogger("RGD-Alpha.Gateway.Enterprise")

class DataGateway:
    """
    ENGINE RGD-ALPHA ENTERPRISE v2.0
    Sistema di analisi predittiva con protocollo EMA, What-If Analysis,
    calcolo H(prod) e Modulo di Recupero Liquidità (Incoming Forecast).
    """
    def __init__(self):
        try:
            self.vault = SecureVault(key_path="core/security/vault.key")
            self.db = DatabaseAziendale()
        except Exception as e:
            logger.critical(f"Errore critico avvio componenti core: {e}")
            raise
        
        self.ORE_TEORICHE_ANNUE = 2080
        self.pesi_contesto = {
            "Magazzino": 1.2, "Fornitori": 1.5, "Performance Vendite": 1.0,
            "Produttività Risorse": 1.3, "EDILE": 1.4, "FASHION": 1.1, "UNIVERSAL": 1.0
        }

    # --- ALGORITMI PRODUTTIVITÀ ---
    def calcola_ore_produttive_individuali(self, f, fest, a, p, r, m):
        return self.ORE_TEORICHE_ANNUE - (f + fest + a + p + r + m)

    def calcola_indice_produttivita(self, output, ore_effettive):
        return round(output / ore_effettive, 2) if ore_effettive > 0 else 0.0

    # --- MATRICE MATEMATICA CORE (EMA PROTOCOL) ---
    def _calcola_trend_momentum_alpha(self, r_oggi, r_storico, w1=0.7, w2=0.3, dt=1):
        if dt <= 0: dt = 1
        return round(((r_oggi * w1) - (r_storico * w2)) / dt, 2)

    def _genera_consiglio_azione(self, rischio, settore, m_score=0):
        alert = " ⚠️ ACCELERAZIONE CRITICA!" if m_score > 1.5 else ""
        if rischio > 8:
            consigli = {
                "PRIMARIO_ALIMENTARE": "🚨 BLOCCO LOTTI: Rischio sanitario/scadenza. Isolare stock.",
                "EDILE_COSTRUZIONI": "🚨 FERMO CANTIERE: Rischio penali elevato. Verificare subappalti.",
                "TERZIARIO_LOGISTICA": "🚨 LIQUIDAZIONE: Saturazione spazi. Liberare magazzino ora.",
                "FASHION_RETAIL": "🚨 OUTLET IMMEDIATO: Merce fuori stagione. Recuperare capitale."
            }
            return consigli.get(settore, "🚨 EMERGENZA: Azione correttiva richiesta entro 24h.") + alert
        elif rischio > 5:
            return f"⚠️ MONITORAGGIO: Settore {settore} in allerta. Revisione parametri settimanale." + alert
        return "✅ NOMINALE: Proseguire secondo pianificazione."

    # --- ANALISI STRATEGICA E WHAT-IF ---
    def esegui_scan_strategico(self, lista_asset, contesto, fattore_stress=1.0, weights=(0.7, 0.3)):
        colonne = []
        if lista_asset:
            colonne = list(lista_asset[0].keys()) if isinstance(lista_asset[0], dict) else list(vars(lista_asset[0]).keys())
        
        config_settore = analizza_e_configura_motore(colonne)
        settore_rilevato = config_settore.get("settore", "GENERAL")
        soglia = config_settore.get("soglia", 7.0)
        moltiplicatore = config_settore.get("moltiplicatore", 1.0) * self.pesi_contesto.get(contesto, 1.0) * fattore_stress
        
        report = []
        for asset in lista_asset:
            d = asset if isinstance(asset, dict) else vars(asset)
            nome = d.get("nome", "Asset")
            r_base = d.get("rischio", 0.0)
            
            # Integrazione Metriche H(prod)
            ore_p = sum([d.get(k, 0) for k in ["ferie", "festivita", "assenze", "permessi", "ritardi", "micropause"]])
            if ore_p > 0:
                r_base = min(10.0, round((ore_p / self.ORE_TEORICHE_ANNUE) * 10, 2))
            
            r_pesato = round(r_base * moltiplicatore, 2)
            m_score = self._calcola_trend_momentum_alpha(r_pesato, r_base * 0.85, w1=weights[0], w2=weights[1])
            
            report.append({
                "asset": nome,
                "stato": "CRITICO" if r_pesato > soglia else "OTTIMALE" if r_pesato < 5 else "ATTENZIONE",
                "rischio": r_pesato,
                "momentum_score": m_score,
                "consiglio_strategico": self._genera_consiglio_azione(r_pesato, settore_rilevato, m_score),
                "settore": settore_rilevato,
                "alert": "🚨 STRESS TEST ATTIVO" if fattore_stress > 1.0 else "Nominale"
            })
            self._archivia_asset(d, r_pesato)
        return report

    # --- MODULO INTELLIGENCE: RECUPERO LIQUIDITÀ (INCOMING) ---
    def analizza_giacenze_e_proponi_marketing(self, df):
        proposte = []
        oggi = datetime.now()
        if df is None or df.empty: return proposte
            
        for _, row in df.iterrows():
            giorni = (oggi - pd.to_datetime(row['timestamp'])).days
            if giorni > 30:
                rischio = row.get('rischio', 0.0)
                valore = row.get('valore_extra', 0.0)
                sconto = 0.4 if rischio > 7 else 0.2
                recupero = round(valore * (1 - sconto), 2)
                
                proposte.append({
                    "asset": row.get('nome'),
                    "giorni": giorni,
                    "recupero_stimato": f"€ {recupero}",
                    "consiglio": f"🚨 BLOCCATI {giorni}gg. Applica sconto {int(sconto*100)}% per recuperare liquidità."
                })
        return proposte

    def _archivia_asset(self, d, rischio):
        try:
            self.db.salva_asset(
                user_id=d.get("user_id", 1), nome_asset=d.get("nome"),
                rischio=rischio, tipo=d.get("tipo", "Enterprise"),
                momentum=d.get("momentum", "Stabile"), volatilita=d.get("volatilita", 0.0)
            )
        except Exception as e: logger.warning(f"DB Sync fallito: {e}")