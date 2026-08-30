from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.nlp_extractor import LegalTacticalNLPExtractor
from core.graph_engine import ConnectiveGraphEngine

app = FastAPI(
    title="NCRB Tactical Criminal Relationship Intelligence API",
    description="Connective Graph Intelligence and Legal-NLP Pipeline for Cybercrime Syndicate Analysis",
    version="2.0.0"
)

# CORS setup for React / Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
nlp_extractor = LegalTacticalNLPExtractor()
graph_engine = ConnectiveGraphEngine()

class FIRTextRequest(BaseModel):
    text: str

class PredictRoleRequest(BaseModel):
    features: Dict[str, Any]

@app.get("/")
def root():
    return {
        "status": "online",
        "engine": "NCRB Connective Graph & Relationship Intelligence Engine",
        "endpoints": [
            "/api/graph-topology",
            "/api/connections/{person_id}",
            "/api/extract-fir",
            "/docs"
        ]
    }

@app.get("/api/graph-topology")
def get_topology(samples: Optional[int] = None):
    """
    Returns full network graph (nodes and relationship edges).
    If 'samples' query parameter is passed, dynamically constructs that slice from dataset.
    """
    if samples is not None and samples > 0:
        graph_engine.build_network_from_csv(max_samples=samples)
        
    data = graph_engine.get_full_topology()
    return {"status": "success", "data": data}

@app.get("/api/connections/{person_id}")
def get_person_relationships(person_id: str):
    """
    Returns immediate 1st-degree operational links, communication routes,
    and modus operandi connections for a target suspect.
    """
    result = graph_engine.get_entity_connections(person_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"status": "success", "data": result}

@app.post("/api/extract-fir")
def extract_fir(payload: FIRTextRequest):
    """
    Parses unstructured FIR/Chargesheet text into statutory flags,
    IMEIs, bank accounts, and judicial milestones.
    """
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text field cannot be empty.")
    
    result = nlp_extractor.process_document(payload.text)
    return {"status": "success", "data": result}