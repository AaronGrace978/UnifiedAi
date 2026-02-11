"""
Meta-Intelligence API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.core.meta_intelligence import MetaIntelligenceOrchestrator

router = APIRouter()
meta_intelligence = MetaIntelligenceOrchestrator()

# Pydantic models
class TechnologyDesignRequest(BaseModel):
    technology: str
    parameters: dict = {}

class SimulationRequest(BaseModel):
    system: str
    equations: dict
    variables: dict

class HypothesisRequest(BaseModel):
    domain: str
    observations: List[str]

@router.post("/design")
def design_breakthrough(request: TechnologyDesignRequest):
    """Design a breakthrough technology using meta-intelligence"""
    result = meta_intelligence.design_breakthrough(
        request.technology,
        request.parameters
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.post("/simulate")
def simulate_physics(request: SimulationRequest):
    """Simulate a physics system"""
    result = meta_intelligence.simulate_physics(
        request.system,
        request.equations,
        request.variables
    )
    return result

@router.post("/hypothesis")
def generate_hypothesis(request: HypothesisRequest):
    """Generate scientific hypotheses"""
    return meta_intelligence.generate_hypothesis(
        request.domain,
        request.observations
    )

@router.get("/projects")
def get_active_projects():
    """Get all active breakthrough technology projects"""
    return {
        "projects": meta_intelligence.get_active_projects(),
        "total": len(meta_intelligence.active_projects)
    }

@router.get("/frameworks")
def get_available_frameworks():
    """Get all available breakthrough technology frameworks"""
    return {
        "frameworks": list(meta_intelligence.breakthrough_frameworks.keys()),
        "count": len(meta_intelligence.breakthrough_frameworks)
    }

