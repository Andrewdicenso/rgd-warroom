import re
from datetime import datetime
from io import BytesIO

import holidays
import pandas as pd


class DataRefinery:
    def __init__(self, country='IT'):
        self.country = country
        self.it_holidays = holidays.CountryHoliday(country)
        # Firme software note ottimizzate
        self.signatures = {
            'SAP_ALV': r'\|',
            'ORACLE_REP': r'\-{5,}',
            'AS400': r'PAGINA\s+\d+|PAGE\s+\d+'
        }

    def refine_file(self, file_input):
        """
        IL PROTOCOLLO LINEARE OTTIMIZZATO:
        1. Identificazione -> 2. Isolamento -> 3. Mappatura -> 4. Diagnostica
        """
        # --- STAGE 0: Normalizzazione Input (Accetta sia stringhe-path che file di Streamlit) ---
        if isinstance(file_input, str):
            with open(file_input, 'rb') as f:
                file_bytes = f.read()
            file_name = file_input
            buffer = BytesIO(file_bytes)
        else:
            file_bytes = file_input.getvalue()
            file_name = file_input.name
            buffer = file_input

        # --- STAGE 1: Identificazione ---
        header_sample = file_bytes.decode('utf-8', errors='ignore')[:2000]
        detected_system = "Generic"
        for sys, pattern in self.signatures.items():
            if re.search(pattern, header_sample):
                detected_system = sys
                break
        
        buffer.seek(0)
        if file_name.endswith('.csv'):
            # --- NUOVA LOGICA DI IDENTIFICAZIONE RIGA ---
            lines = file_bytes.decode('utf-8', errors='ignore').splitlines()
            skip_idx = 0
            for i, line in enumerate(lines):
                if 'DATA' in line.upper() and 'ASSET' in line.upper():
                    skip_idx = i
                    break
            
            buffer.seek(0)
            df = pd.read_csv(buffer, sep=None, engine='python', skiprows=skip_idx, on_bad_lines='skip')
            # ---------------------------------------------
        else:
            df = pd.read_excel(buffer)

        if df.empty:
            return {"data": df, "system": detected_system, "anomalies": [], "status": "Empty"}

        # --- STAGE 2: Isolamento (Pulizia Selettiva del Rumore) ---
        
        # 1. ELIMINAZIONE COLONNE FANTASMA: Rimuove le colonne vuote create dai '|' di SAP
        df = df.loc[:, ~df.columns.str.contains('^Unnamed|^$|^\s*$', case=False, na=False)]
        
        # 2. CALCOLO SOGLIA REALE: Calcola la tolleranza sulle colonne rimaste vere
        threshold = max(1, int(len(df.columns) * 0.5))
        df_clean = df.dropna(thresh=threshold).copy()
        
        # 3. FILTRO RUMORE AVANZATO: Include anche i separatori grafici
        noise_words = ['TOTAL', 'SUBTOTAL', 'SOMMA', 'REPORT', 'PAGE', 'MANDANT']
        
        def is_noise_row(row):
            # Trasforma ogni valore in stringa singolarmente per evitare errori con i numeri (float)
            row_values = [str(val) for val in row.values if val is not None]
            row_str = " ".join(row_values).upper()
            
            # Se la riga è vuota o contiene solo spazi
            if not row_str.strip():
                return True
            # Se la riga contiene i trattini tipici di SAP o parole chiave strutturali
            if '---' in row_str or '- -' in row_str:
                return True
            if any(word in row_str for word in noise_words):
                return True
                
            return False

        # 4. APPLICAZIONE MASCHERA SICURA
        mask = df_clean.apply(is_noise_row, axis=1)
        df_clean = df_clean[~mask]

        # --- STAGE 3: Mappatura & Normalizzazione ---
        df_clean.columns = [str(c).strip().upper() for c in df_clean.columns]
        
        # --- STAGE 4: Diagnostica Continuità ---
        anomalies = []
        date_candidates = [col for col in df_clean.columns if col in ['DATA', 'DATE', 'GIORNO', 'TIMESTAMP']]
        
        if date_candidates:
            date_col = date_candidates[0]
            df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors='coerce')
            df_clean = df_clean.dropna(subset=[date_col])
            
            if not df_clean.empty:
                start_date = df_clean[date_col].min()
                end_date = df_clean[date_col].max()
                
                all_days = pd.date_range(start=start_date, end=end_date).date
                present_days_set = set(df_clean[date_col].dt.date.unique())
                
                for d in all_days:
                    if d not in present_days_set:
                        if d.weekday() < 5 and d not in self.it_holidays:
                            anomalies.append(d.strftime('%Y-%m-%d'))

        return {
            "data": df_clean.reset_index(drop=True),
            "system": detected_system,
            "anomalies": anomalies,
            "status": "Success" if not df_clean.empty else "Empty"
        }