import logging
from core.database import DatabaseAziendale

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("RGD-Alpha.Main")


def avvia_sistema():
    """
    Entry point di test e diagnostica.
    Non avvia Streamlit.
    Non modifica logiche critiche.
    Serve solo per verificare che il database e i moduli core rispondano.
    """
    logger.info("🚀 Avvio diagnostica RGD-Alpha")

    # 1. Inizializzazione database
    try:
        db = DatabaseAziendale()
        logger.info("🗄️ Database inizializzato correttamente.")
    except Exception as e:
        logger.error(f"❌ Errore inizializzazione database: {e}")
        return

    # 2. Verifica admin
    try:
        admin = db.get_utente_by_email("admin@rgandja.com")
        if admin:
            logger.info("👤 Admin rilevato correttamente nel database.")
        else:
            logger.warning("⚠️ Admin NON trovato. Verrà ricreato automaticamente al prossimo avvio.")
    except Exception as e:
        logger.error(f"❌ Errore verifica admin: {e}")

    logger.info("✅ Diagnostica completata. Il sistema è operativo.")


if __name__ == "__main__":
    avvia_sistema()
