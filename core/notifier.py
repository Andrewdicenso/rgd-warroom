import datetime
import os
import logging

logger = logging.getLogger("RGD-Alpha.Sentinella")


class Sentinella:
    """
    SENTINELLA RGD-ALPHA v2.0
    Sistema di monitoraggio e alerting strategico.
    Genera report certificati e prepara notifiche per il management.
    """

    def __init__(self, log_dir="data/logs", filename="warroom_alerts.log"):
        self.log_path = os.path.join(log_dir, filename)
        os.makedirs(log_dir, exist_ok=True)

    def genera_report_strategico(self, report_analisi, azienda="AZ-1"):
        """
        Analizza i risultati dell'AI e genera un report di intervento immediato.
        """
        asset_critici = [a for a in report_analisi if a["rischio"] > 7.5]

        if not asset_critici:
            return None

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Scrittura su LOG di Sistema (Audit Trail)
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"🛡️ RGD-ALPHA PROTOCOLO ALPHA - {timestamp}\n")
                f.write(f"AZIENDA MONITORATA: {azienda}\n")
                f.write(f"{'='*60}\n")

                for asset in asset_critici:
                    f.write(f"📍 ASSET: {asset['asset']}\n")
                    f.write(
                        f"📊 LIVELLO RISCHIO: {asset['rischio']}/10 (MOMENTUM: {asset['momentum_score']})\n"
                    )
                    f.write(f"🧠 AZIONE RICHIESTA: {asset['consiglio_strategico']}\n")
                    f.write(f"{'-'*30}\n")
        except Exception as e:
            logger.error(f"Fallimento scrittura report Sentinella: {e}")

        # 2. Generazione Messaggio per l'Imprenditore (Pronto per invio)
        messaggio_alert = (
            f"🛡️ *RGD-ALPHA ALERT: {azienda}*\n"
            f"Rilevate {len(asset_critici)} criticità ad alto impatto.\n"
            f"Il Momentum del rischio indica un'accelerazione critica.\n"
            f"Accedi subito alla War Room per il piano di recupero liquidità."
        )

        print(
            f"✅ SENTINELLA: Protocollo di allerta attivato per {len(asset_critici)} asset."
        )
        return messaggio_alert

    def registra_accesso_anomalo(self, email):
        """Monitoraggio sicurezza del Vault."""
        with open(self.log_path, "a") as f:
            f.write(
                f"⚠️ SECURITY: Tentativo di accesso fallito per {email} alle {datetime.datetime.now()}\n"
            )

    def genera_report(self, report_analisi):
        """Alias per compatibilità con app.py"""
        return self.genera_report_strategico(report_analisi)
