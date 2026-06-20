import pandas as pd
import re
import holidays
from datetime import datetime

class DataRefinery:
    def __init__(self, country='IT'):
        self.country = country
        self.it_holidays = holidays.CountryHoliday(country)
        # Firme software note
        self.signatures = {
            'SAP_ALV': r'\|',
            'ORACLE_REP': r'\-{5,}',
            'AS400': r'PAGINA\s+\d+'
        }

    def refine_file(self, uploaded_file):
        """
        IL PROTOCOLLO LINEARE:
        1. Identificazione -> 2. Isolamento -> 3. Mappatura -> 4. Diagnostica
        """
        # --- STAGE 1: Identificazione ---
        # Leggiamo l'inizio del file per capire chi lo ha generato
        header_sample = uploaded_file.getvalue().decode('utf-8', errors='ignore')[:2000]
        detected_system = "Generic"
        for sys, pattern in self.signatures.items():
            if re.search(pattern, header_sample):
                detected_system = sys
                break
        
        # Carichiamo il DataFrame (Shadow Copy)
        uploaded_file.seek(0)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python', on_bad_lines='skip')
        else:
            df = pd.read_excel(uploaded_file)

        # --- STAGE 2: Isolamento (Pulizia Rumore) ---
        # Rimuoviamo righe con troppi nulli (subtotali/header vuoti)
        threshold = len(df.columns) * 0.5
        df_clean = df.dropna(thresh=threshold).copy()
        
        # Eliminiamo righe che contengono parole di sistema
        noise_words = ['TOTAL', 'SUBTOTAL', 'SOMMA', 'REPORT', 'PAGE', 'USER']
        mask = df_clean.apply(lambda row: row.astype(str).str.contains('|'.join(noise_words), case=False).any(), axis=1)
        df_clean = df_clean[~mask]

        # --- STAGE 3: Mappatura & Normalizzazione ---
        # Qui cerchiamo di standardizzare i nomi delle colonne
        # (Da espandere con la tua logica Smart Mapper)
        df_clean.columns = [str(c).strip().upper() for c in df_clean.columns]
        
        # --- STAGE 4: Diagnostica Continuità ---
        anomalies = []
        if 'DATA' in df_clean.columns or 'DATE' in df_clean.columns:
            date_col = 'DATA' if 'DATA' in df_clean.columns else 'DATE'
            df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors='coerce')
            df_clean = df_clean.dropna(subset=[date_col])
            
            all_days = pd.date_range(start=df_clean[date_col].min(), end=df_clean[date_col].max()).date
            present_days = df_clean[date_col].dt.date.unique()
            
            for d in all_days:
                if d not in present_days:
                    if d.weekday() < 5 and d not in self.it_holidays:
                        anomalies.append(d)

        return {
            "data": df_clean,
            "system": detected_system,
            "anomalies": anomalies,
            "status": "Success" if not df_clean.empty else "Empty"
        }