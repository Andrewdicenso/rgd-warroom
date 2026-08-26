import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, text

from backend.kpi_engine import compute_financial_kpis
from backend.pdf_generator import generate_pdf_report
from core.ingestor import IngestoreDati
from core.notifier import Sentinella

load_dotenv()

app = FastAPI(
    title="RGD War Room API",
    description="Backend Enterprise per Analisi KPI e Monitoraggio Aziendale",
    version="1.0.0",
)

# CORS Corretto: Nessun conflitto tra wildcard e credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")

# Engine SQLAlchemy resiliente con Pool Pre-Ping e Timeout
engine = (
    create_engine(
        DATABASE_URL,
        connect_args={"connect_timeout": 5},
        pool_pre_ping=True,
        pool_recycle=300,
    )
    if DATABASE_URL
    else None
)

sentinella = Sentinella()
ingestor = IngestoreDati()
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


@app.get("/")
def read_root():
    return {"status": "online", "message": "RGD War Room API Operational"}


@app.get("/api/v1/health")
def health_check():
    if not engine:
        return {"health": "warning", "database": "DATABASE_URL non configurato"}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1;"))
            return {"health": "ok", "database": "connected_to_supabase"}
    except Exception as e:
        return {"health": "error", "database_error": str(e)}


@app.post("/api/v1/upload")
def upload_file(client_id: str = Form(...), file: UploadFile = File(...)):
    if not engine:
        raise HTTPException(status_code=500, detail="Database non connesso")

    # Sanificazione del nome file (Anti Path-Traversal)
    safe_filename = Path(file.filename).name
    file_path = DATA_DIR / safe_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with engine.connect() as connection:
            query = text("""
                INSERT INTO file_uploads (client_id, file_name, file_type, status)
                VALUES (:client_id, :file_name, :file_type, 'uploaded')
                RETURNING id, file_name, status;
            """)
            result = connection.execute(
                query,
                {
                    "client_id": client_id,
                    "file_name": safe_filename,
                    "file_type": file.content_type,
                },
            )
            connection.commit()
            row = result.fetchone()

            return {
                "status": "success",
                "message": "File salvato e registrato con successo",
                "file_data": {
                    "file_id": str(row[0]),
                    "file_name": row[1],
                    "status": row[2],
                    "local_path": str(file_path),
                },
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analyze/{file_id}")
def analyze_file(file_id: str):
    if not engine:
        raise HTTPException(status_code=500, detail="Database non connesso")

    try:
        with engine.connect() as connection:
            # 1. Recupera le informazioni sul file (confronto sicuro con ::text)
            query = text(
                "SELECT file_name, client_id FROM file_uploads WHERE id::text = :file_id;"
            )
            result = connection.execute(query, {"file_id": file_id}).fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Record file non trovato")

            file_name, client_id = str(result[0]), str(result[1])
            file_path = DATA_DIR / file_name

            if not file_path.exists():
                raise HTTPException(
                    status_code=404, detail=f"File fisico non trovato in {file_path}"
                )

            # 2. Legge il file ed esegue l'analisi KPI e Risk Score
            df = (
                pd.read_excel(file_path)
                if file_name.endswith((".xlsx", ".xls"))
                else pd.read_csv(file_path)
            )
            kpi_results = compute_financial_kpis(df, company_id=client_id)

            # 3. Controllo Sentinella per alert critici (> 7.5)
            risk_score = kpi_results.get("risk_score", 0.0)
            if risk_score > 7.5:
                momentum = kpi_results.get("trend_momentum", {}).get(
                    "momentum_perc", "0%"
                )
                action_plan = kpi_results.get("ai_strategic_action_plan", [{}])[0].get(
                    "action", "Monitoraggio"
                )

                alert_msg = sentinella.genera_report_strategico(
                    report_analisi=[
                        {
                            "asset": "Reparto Operativo",
                            "rischio": risk_score,
                            "momentum_score": momentum,
                            "consiglio_strategico": action_plan,
                        }
                    ],
                    azienda=client_id,
                )
                kpi_results["alert_sentinella"] = alert_msg

            # 4. Salva l'analisi su Supabase (con casting esplicito a UUID)
            insert_query = text("""
                INSERT INTO analysis_history (client_id, file_id, kpi_results, risk_score)
                VALUES (:client_id::uuid, :file_id::uuid, :kpi_results, :risk_score)
                RETURNING id, created_at;
            """)

            res = connection.execute(
                insert_query,
                {
                    "client_id": client_id,
                    "file_id": file_id,
                    "kpi_results": json.dumps(kpi_results),
                    "risk_score": risk_score,
                },
            )
            connection.commit()
            analysis_row = res.fetchone()

            return {
                "status": "success",
                "message": "Analisi calcolata e registrata su Supabase",
                "analysis_id": str(analysis_row[0]),
                "financial_kpis": kpi_results,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
