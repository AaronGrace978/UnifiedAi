"""
Breakthrough Technology API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.core.breakthrough_tech import BreakthroughTechnology, TechnologyType

router = APIRouter()
tech_framework = BreakthroughTechnology()

@router.get("/technologies")
def list_technologies(tech_type: Optional[str] = None):
    """List all breakthrough technologies"""
    if tech_type:
        try:
            tech_enum = TechnologyType(tech_type)
            return tech_framework.list_technologies(tech_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid technology type. Valid types: {[t.value for t in TechnologyType]}"
            )
    
    return tech_framework.list_technologies()

@router.get("/technologies/{tech_id}")
def get_technology(tech_id: str):
    """Get a specific breakthrough technology"""
    tech = tech_framework.get_technology(tech_id)
    if not tech:
        raise HTTPException(status_code=404, detail=f"Technology '{tech_id}' not found")
    
    # Convert enum to value for JSON serialization
    result = {**tech, "type": tech["type"].value}
    return result

@router.get("/technologies/{tech_id}/roadmap")
def get_research_roadmap(tech_id: str):
    """Get research roadmap for a technology"""
    roadmap = tech_framework.get_research_roadmap(tech_id)
    
    if "error" in roadmap:
        raise HTTPException(status_code=404, detail=roadmap["error"])
    
    return roadmap

