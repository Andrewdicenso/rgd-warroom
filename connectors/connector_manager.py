import shutil
import os
import logging

logger = logging.getLogger("RGD-Alpha.Connector")

class LocalSyncConnector:
    """
    Gestore della sincronizzazione dati aziendali.
    Assicura che il trasferimento avvenga in modo tracciabile e sicuro.
    """
    def __init__(self, files_to_sync):
        self.files_to_sync = files_to_sync

    def sync_dati(self) -> bool:
        """Copia i file dalla sorgente locale alla destinazione aziendale con audit trail."""
        success_count = 0
        try:
            for item in self.files_to_sync:
                source = item.get('remote')
                destination = item.get('local')
                
                if not source or not destination:
                    logger.warning("Elemento di sincronizzazione incompleto saltato.")
                    continue

                os.makedirs(os.path.dirname(destination), exist_ok=True)
                
                if os.path.exists(source):
                    shutil.copy2(source, destination)
                    logger.info(f"Sincronizzazione completata: {os.path.basename(source)} -> {destination}")
                    success_count += 1
                else:
                    logger.error(f"Errore di sincronizzazione: File sorgente non trovato {source}")
            
            return success_count > 0
        
        except Exception as e:
            logger.critical(f"Fallimento critico durante la sincronizzazione: {e}")
            return False
