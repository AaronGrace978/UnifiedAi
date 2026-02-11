"""
Auto-Discovery API Endpoints
Autonomous exploration and dream mode
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.auto_discovery import auto_discovery

router = APIRouter(prefix="/api/discovery", tags=["Auto-Discovery"])


class StartDiscoveryRequest(BaseModel):
    mode: str = "dream"  # dream, focused, exploratory
    seed_topics: Optional[List[str]] = None
    num_threads: int = 3
    max_depth: int = 5


@router.post("/start")
async def start_discovery(request: StartDiscoveryRequest) -> Dict[str, Any]:
    """Start an auto-discovery session"""
    try:
        session = await auto_discovery.start_discovery(
            mode=request.mode,
            seed_topics=request.seed_topics,
            num_threads=request.num_threads,
            max_depth=request.max_depth
        )
        
        return {
            "session_id": session.id,
            "mode": session.mode,
            "threads": [
                {
                    "id": t.id,
                    "seed_topic": t.seed_topic
                }
                for t in session.threads
            ],
            "status": "started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/step")
async def run_step(session_id: str) -> Dict[str, Any]:
    """Run one step of discovery"""
    try:
        result = await auto_discovery.run_discovery_step(session_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/summary")
async def get_session_summary(session_id: str) -> Dict[str, Any]:
    """Get summary of a discovery session"""
    try:
        summary = auto_discovery.get_session_summary(session_id)
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/insights")
async def get_session_insights(session_id: str) -> Dict[str, Any]:
    """Get all insights from a discovery session"""
    try:
        insights = auto_discovery.get_all_insights(session_id)
        return {
            "session_id": session_id,
            "insights": insights,
            "count": len(insights)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions() -> Dict[str, Any]:
    """List all discovery sessions"""
    try:
        sessions = auto_discovery.list_sessions()
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_discovery() -> Dict[str, Any]:
    """Stop continuous discovery"""
    try:
        auto_discovery.stop_discovery()
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

