"""
Ensemble Thinking API Endpoints
Multi-model reasoning for robust answers
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.ensemble_thinker import ensemble_thinker

router = APIRouter(prefix="/api/ensemble", tags=["Ensemble Thinking"])


class EnsembleThinkRequest(BaseModel):
    question: str
    models: Optional[List[str]] = None
    synthesis_model: Optional[str] = None


class DebateRequest(BaseModel):
    topic: str
    rounds: int = 2
    models: Optional[List[str]] = None


@router.get("/models")
async def list_available_models() -> Dict[str, Any]:
    """List available models for ensemble thinking"""
    try:
        models = await ensemble_thinker.list_available_models()
        return {
            "models": models,
            "count": len(models),
            "preferred": ensemble_thinker.preferred_models
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/think")
async def ensemble_think(request: EnsembleThinkRequest) -> Dict[str, Any]:
    """
    Think about a question using multiple models in parallel.
    
    Each model provides its perspective, then the responses are
    synthesized into a coherent answer with agreement analysis.
    """
    try:
        result = await ensemble_thinker.think_ensemble(
            question=request.question,
            models=request.models,
            synthesis_model=request.synthesis_model
        )
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debate")
async def debate_topic(request: DebateRequest) -> Dict[str, Any]:
    """
    Have models debate a topic through multiple rounds.
    
    Two models take positions and exchange rebuttals,
    with a final synthesis of the debate.
    """
    try:
        result = await ensemble_thinker.debate(
            topic=request.topic,
            rounds=request.rounds,
            models=request.models
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

