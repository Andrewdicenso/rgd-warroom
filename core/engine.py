import sys
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np
import difflib # <-- INDISPENSABILE per la mappatura intelligente

# ==============================================================================
# RISOLUZIONE DINAMICA DEL PATH (Mantenuta intatta)
# ==============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.secure_vault import SecureVault
from core.database import DatabaseAziendale

logger = logging.getLogger("RGD-Alpha.Gateway.Enterprise")

class DataGateway:
    """
    ENGINE RGD-ALPHA ENTERPRISE v2.2
    SISTEMA INTEGRATO: Mappatura Universale + EMA Protocol + What-If Analysis.
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

    # ==========================================================================
    # NUOVA FUNZIONE: SMART MAPPING UNIVERSALE
    # ==========================================================================
    def mappa_colonne_universale(self, df):
        """
        Rileva e rinomina automaticamente le colonne provenienti da qualsiasi ERP/CRM.
        Non interrompe il flusso: se non trova nulla, restituisce il df originale.
        """
        colonne_target = {
            "nome": ["Work Center", "Reparto", "Cantiere", "Asset", "Macchina", "Project", "Account Name", "Name"],
            "rischio": ["Risk", "Criticality", "Priorità", "Livello", "Grado", "Pericolo", "Priority Score", "Rischio"],
            "ore_produttive_effettive": ["Hours", "Ore", "Tempo", "Effort", "Lavorate", "Actual Hours", "h"],
            "tipo": ["Type", "Category", "Categoria", "Genere", "Resource Group", "Tipo"],
            "stato": ["Status", "Stato", "Health", "Fase", "Current State"],
            "timestamp": ["Data", "Date", "Timestamp", "Data Caricamento", "Inizio", "Giorno"]
        }
        colonne_file = list(df.columns)
        mappa_finale = {}

        for target, sinonimi in colonne_target.items():
            for col in colonne_file:
                if col.lower() in [s.lower() for s in sinonimi] or col.lower() == target:
                    mappa_finale[col] = target
                    break
            if target not in mappa_finale.values():
                matches = difflib.get_close_matches(target, colonne_file, n=1, cutoff=0.5)
                if matches: 
                    mappa_finale[matches[0]] = target
        
        return df.rename(columns=mappa_finale)

    # --- ALGORITMI PRODUTTIVITÀ (Invariati) ---
    def calcola_ore_produttive_individuali(self, f, fest, a, p, r, m):
        return self.ORE_TEORICHE_ANNUE - (f + fest + a + p + r + m)

    def calcola_indice_produttivita(self, output, ore_effettive):
        return round(output / ore_effettive, 2) if ore_effettive > 0 else 0.0

    # --- MATRICE MATEMATICA CORE (EMA PROTOCOL - Invariata) ---
    def _calcola_trend_momentum_alpha(self, r_oggi, r_storico, w1=0.7, w2=0.3, dt=1):
        if dt <= 0: 
            dt = 1
        return round(((r_oggi * w1) - (r_storico * w2)) / dt, 2)

    def _calcola_trend_momentum_alpha(self, r_oggi, r_storico, w1=0.7, w2=0.3, dt=1):
        if dt <= 0: 
            dt = 1
        return round(((r_oggi * w1) - (r_storico * w2)) / dt, 2)

    # --- INSERISCI DA QUI ---
    def calcola_volatilita_sistema(self, valori_rischio):
        """
        Rileva instabilità nei dati caricati (Anomalie di Governance).
        """
        if len(valori_rischio) < 2: return 0.0
        return round(np.std(valori_rischio), 2)
    # --- FINO A QUI ---
   
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

    # --- CONFIGURAZIONE SETTORE / SOGLIE (Invariata) ---
    def _analizza_e_configura_motore(self, contesto, colonne):
        contesto_upper = str(contesto).upper()
        if "EDILE" in contesto_upper: 
            return {"settore": "EDILE_COSTRUZIONI", "soglia": 7.5, "moltiplicatore": 1.2}
        if "FASHION" in contesto_upper: 
            return {"settore": "FASHION_RETAIL", "soglia": 7.0, "moltiplicatore": 1.1}
        if "LOGIST" in contesto_upper or "MAGAZZINO" in contesto_upper: 
            return {"settore": "TERZIARIO_LOGISTICA", "soglia": 7.0, "moltiplicatore": 1.3}
        if "ALIMENT" in contesto_upper: 
            return {"settore": "PRIMARIO_ALIMENTARE", "soglia": 6.5, "moltiplicatore": 1.4}
        return {"settore": "GENERAL", "soglia": 7.0, "moltiplicatore": 1.0}

    # --- ANALISI STRATEGICA E WHAT-IF (Logica H(prod) Preservata) ---
    def esegui_scan_strategico(self, lista_asset, contesto, fattore_stress=1.0, weights=(0.7, 0.3)):
        colonne = []
        if lista_asset:
            colonne = list(lista_asset[0].keys()) if isinstance(lista_asset[0], dict) else list(vars(lista_asset[0]).keys())
        
        config = self._analizza_e_configura_motore(contesto, colonne)
        settore_rilevato = config.get("settore", "GENERAL")
        soglia = config.get("soglia", 7.0)
        moltiplicatore = config.get("moltiplicatore", 1.0) * self.pesi_contesto.get(contesto, 1.0) * fattore_stress
        
        report = []
        for asset in lista_asset:
            d = asset if isinstance(asset, dict) else vars(asset)
            nome = d.get("nome", d.get("asset", "Asset")) # Fallback sicuro
            r_base = d.get("rischio", 0.0)
            
                        # Calcolo H(prod) POTENZIATO: Modello di Saturazione Rischio
            voci_perdita = ["ferie", "festivita", "assenze", "permessi", "ritardi", "micropause"]
            ore_p = sum([float(d.get(k, 0)) for k in voci_perdita])
            
            if ore_p > 0:
                rapporto_perdita = ore_p / self.ORE_TEORICHE_ANNUE
                # Funzione di crescita non lineare: il rischio accelera dopo il 15% di ore perse
                r_base = round(10 / (1 + np.exp(-15 * (rapporto_perdita - 0.15))), 2)
            else:
                r_base = d.get("rischio", 1.0) # Fallback se non ci sono ore caricate
            
            r_pesato = round(r_base * moltiplicatore, 2)
            m_score = self._calcola_trend_momentum_alpha(r_pesato, r_base * 0.85, w1=weights[0], w2=weights[1])
            stato = "CRITICO" if r_pesato > soglia else "OTTIMALE" if r_pesato < 5 else "ATTENZIONE"

            report.append({
                "asset": nome,
                "stato": stato,
                "rischio": r_pesato,
                "momentum_score": m_score,
                "consiglio_strategico": self._genera_consiglio_azione(r_pesato, settore_rilevato, m_score),
                "settore": settore_rilevato,
                "alert": "🚨 STRESS TEST ATTIVO" if fattore_stress > 1.0 else "Nominale"
            })
            self._archivia_asset(d, r_pesato, str(m_score))
        return report

    # --- MODULO INTELLIGENCE E ARCHIVIAZIONE (Invariati) ---
    def analizza_giacenze_e_proponi_marketing(self, df):
        proposte = []
        oggi = datetime.now()
        if df is None or df.empty: 
            return proposte
        for _, row in df.iterrows():
            if 'timestamp' not in row or pd.isna(row['timestamp']): 
                continue
            giorni = (oggi - pd.to_datetime(row['timestamp'])).days
            if giorni > 30:
                rischio, valore = row.get('rischio', 0.0), row.get('valore_extra', 0.0)
                sconto = 0.4 if rischio > 7 else 0.2
                proposte.append({
                    "asset": row.get('nome'), 
                    "giorni": giorni, 
                    "recupero_stimato": f"€ {round(valore * (1 - sconto), 2)}", 
                    "consiglio": f"🚨 BLOCCATI {giorni}gg. Applica sconto {int(sconto*100)}%."
                })
        return proposte

    def _archivia_asset(self, d, rischio, momentum_str="Stabile"):
        try:
            self.db.salva_asset(
                user_id=d.get("user_id", 1), 
                nome_asset=d.get("nome"), 
                rischio=rischio, 
                tipo=d.get("tipo", "Enterprise"), 
                momentum=momentum_str, 
                volatilita=0.0
            )
        except Exception as e:
            logger.warning(f"DB Sync fallito: {e}")

    def salva_report_certificato(self, report_data):
        if not report_data: 
            return False
        logger.info("Report salvato con successo (stub).")
        return True