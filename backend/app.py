import io
import os
from pypdf import PdfReader
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.nlp_extractor import LegalTacticalNLPExtractor
from core.graph_engine import ConnectiveGraphEngine
from core.suspicion_engine import SuspicionScoringEngine
from core.judicial_predictor import JudicialReliefPredictor

# 1. Initialize FastAPI Application
app = FastAPI(
    title="NCRB Tactical Criminal Relationship Intelligence API",
    description="Connective Graph Intelligence, Suspicion Engine & Judicial Risk Predictor",
    version="2.0.0"
)

# 2. Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Initialize Core Analytical Engines
nlp_extractor = LegalTacticalNLPExtractor()
graph_engine = ConnectiveGraphEngine()
suspicion_engine = SuspicionScoringEngine()
judicial_predictor = JudicialReliefPredictor()


class FIRTextRequest(BaseModel):
    text: str


class JudicialCaseRequest(BaseModel):
    custody_duration_days: int = 15
    charge_sheet_filed: int = 0
    account_frozen_indicator: int = 1
    statutory_cert_present: int = 1
    heinous_offense_flag: int = 0
    prior_antecedents_count: int = 0
    flight_risk_indicator: int = 0
    unauthorized_amount_inr: float = 0.0
    recovery_effected_ratio: float = 0.0


@app.get("/")
def root():
    return {
        "status": "online",
        "engine": "NCRB Connective Graph & Relationship Intelligence Engine",
        "endpoints": [
            "/api/graph-topology",
            "/api/connections/{person_id}",
            "/api/extract-fir",
            "/api/analyze-file",
            "/api/predict-judicial-relief",
            "/docs"
        ]
    }


@app.get("/api/graph-topology")
def get_topology(samples: Optional[int] = None):
    """Returns full baseline network graph with nodes, relationship edges, and syndicate cells."""
    if samples is not None and samples > 0:
        graph_engine.build_network_from_csv(max_samples=samples)
        
    data = graph_engine.get_full_topology()
    scored_data = suspicion_engine.score_entire_network(data)
    return {"status": "success", "data": scored_data, "graph_data": scored_data}


@app.get("/api/connections/{person_id}")
def get_person_relationships(person_id: str):
    """Returns 1st-degree operational links and Modus Operandi hops for an accused suspect."""
    result = graph_engine.get_entity_connections(person_id)
    if "error" in result:
        return {
            "status": "success",
            "data": {
                "person_id": person_id,
                "total_connections": 0,
                "relationships": []
            }
        }
    return {"status": "success", "data": result}


@app.post("/api/extract-fir")
def extract_fir(payload: FIRTextRequest):
    """Parses raw text into statutory charges, IMEIs, entities, and builds an ML-scored topology."""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text field cannot be empty.")
    
    # 1. NLP Extraction
    extracted = nlp_extractor.process_document(payload.text)
    
    # 2. Score Topology via Suspicion Engine (Model 1)
    if "graph_data" in extracted and extracted["graph_data"].get("nodes"):
        scored_graph = suspicion_engine.score_entire_network(extracted["graph_data"])
        extracted["graph_data"] = scored_graph

    return {
        "status": "success",
        "data": extracted,
        "graph_data": extracted.get("graph_data", {"nodes": [], "links": []})
    }


@app.post("/api/analyze-file")
def analyze_document(file: UploadFile = File(...)):
    """
    Parses PDF or TXT bytes, extracts tactical entities, generates graph topology,
    and enriches every node through the Suspicion Scoring ML Engine.
    """
    filename = file.filename.lower()
    content = ""

    try:
        raw_bytes = file.file.read()
        
        if filename.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(raw_bytes))
            content = "".join([(page.extract_text() or "") + "\n" for page in reader.pages])
        elif filename.endswith(".txt"):
            content = raw_bytes.decode("utf-8", errors="ignore")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .txt or .pdf files.")

        if not content.strip():
            raise HTTPException(status_code=400, detail="Document contains no readable text.")

        # 1. Extract Entities & Raw Network
        analysis_result = nlp_extractor.process_document(content)
        
        # 2. Enrich through Model 1 (Suspicion Scoring Engine)
        if "graph_data" in analysis_result and analysis_result["graph_data"].get("nodes"):
            scored_graph = suspicion_engine.score_entire_network(analysis_result["graph_data"])
            analysis_result["graph_data"] = scored_graph

        # Returns both data and top-level graph_data for bulletproof frontend compatibility
        return {
            "status": "success",
            "filename": file.filename,
            "data": analysis_result,
            "graph_data": analysis_result.get("graph_data", {"nodes": [], "links": []})
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.post("/api/predict-judicial-relief")
def predict_bail_relief(case_data: JudicialCaseRequest):
    """
    Evaluates accused parameters against Model 2 (Judicial Predictor)
    to predict bail vs custody remand and cite BSA/BNSS compliance milestones.
    """
    try:
        prediction = judicial_predictor.predict_judicial_relief(case_data.model_dump())
        return {"status": "success", "data": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction engine failure: {str(e)}")