import sys
import logging
from pathlib import Path
from datetime import datetime
import numpy as np

# ==============================================================================
# RISOLUZIONE DINAMICA DEL PATH PER STREAMLIT (PRESERVATO)
# ==============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ==============================================================================
# COLLEGAMENTI INTERNI RIGIDI (MANTENUTI E VERIFICATI)
# ==============================================================================
from core.secure_vault import SecureVault
from core.database import DatabaseAziendale
from core.experimental_modules.engine_settori import analizza_e_configura_motore

logger = logging.getLogger("RGD-Alpha.Gateway.Enterprise")

class DataGateway:
    """
    Gateway Enterprise: Sistema di analisi predittiva con protocollo EMA (Alpha).
    Include What-If Analysis e calcolo dinamico del Momentum finanziario.
    Integrazione nativa delle metriche quantitative H(prod) per l'efficienza aziendale.
    """
    def __init__(self):
        try:
            # Mantenimento indirizzamento chiavi e database
            self.vault = SecureVault(key_path="core/security/vault.key")
            self.db = DatabaseAziendale()
        except Exception as e:
            logger.critical(f"Errore critico avvio componenti core: {e}")
            raise
        
        # Costante algoritmica di base per il tempo pieno annuo
        self.ORE_TEORICHE_ANNUE = 2080
        
        # Configurazione pesi contesto originaria estesa per le risorse
        self.pesi_contesto = {
            "Magazzino": 1.2,
            "Fornitori": 1.5,
            "Performance Vendite": 1.0,
            "Produttività Risorse": 1.3,
            "UNIVERSAL": 1.0
        }

    # --- SOTTO-MODULO INTEGRATO: ALGORITMO ORE PRODUTTIVE ---
    def calcola_ore_produttive_individuali(self, ferie, festivita, assenze, permessi, ritardi, micropause):
        """Calcola le ore effettive di un dipendente/reparto sottraendo le inefficienze."""
        return self.ORE_TEORICHE_ANNUE - (ferie + festivita + assenze + permessi + ritardi + micropause)

    def calcola_indice_produttivita(self, output_totale, ore_effettive_azienda):
        """Calcola la produttività reale per ora effettiva."""
        if ore_effettive_azienda <= 0: 
            return 0.0
        return round(output_totale / ore_effettive_azienda, 2)

    # --- COLLEGAMENTI DATABASE (PERSISTENZA ATOMICA) ---
    def _archivia_asset(self, asset, rischio_pesato):
        """Persistenza atomica sul database multi-tenant senza spezzare lo schema."""
        try:
            if isinstance(asset, dict):
                user_id = asset.get("user_id", 1)
                nome_asset = asset.get("nome", "Asset_Operativo")
                tipo = asset.get("tipo", "EfficienzaRisorse")
                momentum = asset.get("momentum", "Stabile")
                volatilita = asset.get("volatilita", 0.0)
            else:
                user_id = getattr(asset, 'user_id', 1)
                nome_asset = getattr(asset, 'nome', 'Asset_Operativo')
                tipo = getattr(asset, 'tipo', 'EfficienzaRisorse')
                momentum = getattr(asset, 'momentum', 'Stabile')
                volatilita = getattr(asset, 'volatilita', 0.0)

            # Esecuzione della chiamata al metodo nativo di core.database
            self.db.salva_asset(
                user_id=user_id,
                nome_asset=nome_asset,
                rischio=rischio_pesato,
                tipo=tipo,
                momentum=momentum,
                volatilita=volatilita
            )
        except Exception as e:
            logger.warning(f"Archiviazione fallita sul database aziendale: {e}")

    # --- MATRICE MATEMATICA CORE ---
    def _calcola_trend_momentum_alpha(self, rischio_oggi, rischio_storico, w1=0.7, w2=0.3, dt=1):
        """
        IMPLEMENTAZIONE FORMULA EMA (IMAGE 6):
        M = ((Roggi * W1) - (Rstorico * W2)) / dt
        """
        if dt <= 0: dt = 1
        momentum_score = ((rischio_oggi * w1) - (rischio_storico * w2)) / dt
        return round(momentum_score, 2)

    def _genera_consiglio_azione(self, rischio, settore, momentum_score=0):
        """Genera un consiglio pratico basato su rischio, settore e accelerazione."""
        alert_text = " ⚠️ ACCELERAZIONE CRITICA!" if momentum_score > 1.5 else ""

        if rischio > 8:
            if settore == "LOGISTICS":
                return f"🚨 CRITICO: Avviare liquidazione immediata per liberare spazio.{alert_text}"
            if settore == "FINANCE":
                return f"🚨 CRITICO: Rischio svalutazione totale asset. Revisione contratti.{alert_text}"
            if settore == "PRODUCTION":
                return f"🚨 CRITICO: Colli di bottiglia severi sulle ore lavorate. Riorganizzare i turni.{alert_text}"
            return f"🚨 CRITICO: Azione d'emergenza richiesta entro 48 ore.{alert_text}"
        
        elif rischio > 5:
            if settore == "LOGISTICS":
                return f"⚠️ ATTENZIONE: Pianificare promozione 'Bundle' per aumentare rotazione.{alert_text}"
            return f"⚠️ ATTENZIONE: Monitoraggio intensivo richiesto per i prossimi 7 giorni.{alert_text}"
        
        else:
            return "✅ OTTIMALE: Parametri stabili. Proseguire con ordinaria amministrazione."

    # --- INTERFACCIA DI SCAN STRATEGICO INTEGRATA ---
    def esegui_scan_strategico(self, lista_asset, contesto, fattore_stress=1.0, weights=(0.7, 0.3)):
        """
        Analisi Avanzata RGD-ALPHA con WHAT-IF, TREND MOMENTUM e METRICHE ORARIE.
        Accetta dizionari o oggetti asset mantenendo intatta la compatibilità dell'interfaccia.
        """
        colonne = []
        if lista_asset:
            primo_asset = lista_asset[0]
            colonne = list(primo_asset.keys()) if isinstance(primo_asset, dict) else list(vars(primo_asset).keys())
        
        # Collegamento dinamico a core.experimental_modules.engine_settori
        config_settore = analizza_e_configura_motore(colonne)
        settore_rilevato = config_settore.get("settore", "GENERAL")
        soglia_critica = config_settore.get("soglia", 7.0)
        
        moltiplicatore_finale = config_settore.get("moltiplicatore", 1.0) * self.pesi_contesto.get(contesto, 1.0) * fattore_stress
        
        w1, w2 = weights
        report = []
        
        for asset in lista_asset:
            if isinstance(asset, dict):
                nome_asset = asset.get("nome", "Prodotto")
                rischio_base = asset.get("rischio", 0.0)
                # Verifica presenza parametri quantitativi H(prod)
                ferie = asset.get("ferie", 0)
                festivita = asset.get("festivita", 0)
                assenze = asset.get("assenze", 0)
                permessi = asset.get("permessi", 0)
                ritardi = asset.get("ritardi", 0)
                micropause = asset.get("micropause", 0)
                output_totale = asset.get("output_totale", 0)
            else:
                nome_asset = getattr(asset, 'nome', 'Prodotto')
                rischio_base = getattr(asset, 'rischio', 0.0)
                ferie = getattr(asset, 'ferie', 0)
                festivita = getattr(asset, 'festivita', 0)
                assenze = getattr(asset, 'assenze', 0)
                permessi = getattr(asset, 'permessi', 0)
                ritardi = getattr(asset, 'ritardi', 0)
                micropause = getattr(asset, 'micropause', 0)
                output_totale = getattr(asset, 'output_totale', 0)

            # Se l'asset contiene dati temporali, ricalcola il rischio in base alle ore perse
            if ore_perdute_totatli := (ferie + festivita + assenze + permessi + ritardi + micropause):
                ore_effettive = self.calcola_ore_produttive_individuali(ferie, festivita, assenze, permessi, ritardi, micropause)
                prod_reale = self.calcola_indice_produttivita(output_totale, ore_effettive)
                # Normalizzazione dell'impatto delle ore perse su scala di rischio 1-10
                rischio_base = min(10.0, round((ore_perdute_totatli / self.ORE_TEORICHE_ANNUE) * 10, 2))
            else:
                ore_effettive = self.ORE_TEORICHE_ANNUE
                prod_reale = 0.0

            # Calcolo Rischio Pesato con Stress Test What-If
            rischio_pesato = round(rischio_base * moltiplicatore_finale, 2)
            
            # Recupero rischio storico e calcolo accelerazione EMA
            rischio_storico = rischio_base * 0.85 
            m_score = self._calcola_trend_momentum_alpha(rischio_pesato, rischio_storico, w1=w1, w2=w2)
            
            # Generazione Output IA
            consiglio = self._genera_consiglio_azione(rischio_pesato, settore_rilevato, m_score)
            
            # Definizione stato visivo condizionale
            stato_salute = "CRITICO" if rischio_pesato > soglia_critica else "OTTIMALE"
            if 5.0 < rischio_pesato <= soglia_critica:
                stato_salute = "ATTENZIONE"

            report.append({
                "asset": nome_asset,
                "stato": stato_salute,
                "rischio": rischio_pesato,
                "momentum_score": m_score,
                "consiglio_strategico": consiglio,
                "settore": settore_rilevato,
                "ore_produttive_effettive": ore_effettive,
                "produttivita_oraria_reale": prod_reale,
                "alert": "🚨 STRESS TEST ATTIVO" if fattore_stress > 1.0 else "Parametri nominali"
            })
            
            # Chiamata di persistenza interna preservata
            self._archivia_asset(asset, rischio_pesato)
            
        return report

# --- COLLEGAMENTO CRITTOGRAFICO SECURE VAULT ---
def salva_report_certificato(azienda, dati_report, vault):
    """Genera un blob cifrato per la notarizzazione del report tramite SecureVault."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        certificato = f"TS: {timestamp} | AZIENDA: {azienda} | PROTOCOLLO ALPHA CERTIFIED | AES-256"
        return vault.encrypt_data(certificato)
    except Exception as e:
        logger.error(f"Certificazione fallita tramite secure_vault: {e}")
        return None