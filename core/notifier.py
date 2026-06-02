import datetime
import os

class Sentinella:
    def __init__(self, log_dir="data/logs", filename="report_critico.txt"):
        self.log_path = os.path.join(log_dir, filename)
        # Assicura che la cartella esista
        os.makedirs(log_dir, exist_ok=True)

    def genera_report(self, asset_critici):
        """Scrive un report formattato su file se trova criticità."""
        if not asset_critici:
            return

        with open(self.log_path, "a") as f:
            f.write(f"\n--- REPORT CRITICO: {datetime.datetime.now()} ---\n")
            for nome, rischio in asset_critici:
                f.write(f"ALLERTA: L'asset '{nome}' presenta un rischio critico di {rischio}.\n")
        
        print(f"SENTINELLA: Report generato in {self.log_path}")