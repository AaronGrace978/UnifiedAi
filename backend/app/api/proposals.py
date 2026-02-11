"""
Research Proposals API Endpoints
Generate and manage research proposals from insights
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.research_proposals import research_generator, ProposalStatus

router = APIRouter(prefix="/api/proposals", tags=["Research Proposals"])


class GenerateProposalRequest(BaseModel):
    insight_id: str
    insight_content: str
    domains: List[str]
    novelty_score: float
    testability_score: float
    key_concepts: Optional[List[str]] = None


class UpdateStatusRequest(BaseModel):
    status: str  # draft, in_review, approved, in_progress, completed, archived


@router.post("/generate")
async def generate_proposal(request: GenerateProposalRequest) -> Dict[str, Any]:
    """Generate a research proposal from an insight"""
    try:
        proposal = research_generator.generate_proposal(
            insight_id=request.insight_id,
            insight_content=request.insight_content,
            domains=request.domains,
            novelty_score=request.novelty_score,
            testability_score=request.testability_score,
            key_concepts=request.key_concepts
        )
        return proposal.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_proposals(status: Optional[str] = None) -> Dict[str, Any]:
    """List all proposals, optionally filtered by status"""
    try:
        status_enum = None
        if status:
            try:
                status_enum = ProposalStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        proposals = research_generator.list_proposals(status_enum)
        return {
            "proposals": proposals,
            "count": len(proposals)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proposal_id}")
async def get_proposal(proposal_id: str) -> Dict[str, Any]:
    """Get a specific proposal by ID"""
    try:
        proposal = research_generator.get_proposal(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        return proposal.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{proposal_id}/status")
async def update_proposal_status(proposal_id: str, request: UpdateStatusRequest) -> Dict[str, Any]:
    """Update proposal status"""
    try:
        try:
            new_status = ProposalStatus(request.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")
        
        success = research_generator.update_status(proposal_id, new_status)
        if not success:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        return {
            "id": proposal_id,
            "status": request.status,
            "updated": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proposal_id}/export/markdown")
async def export_proposal_markdown(proposal_id: str):
    """Export proposal as Markdown document"""
    try:
        markdown = research_generator.export_proposal_markdown(proposal_id)
        if not markdown:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        return PlainTextResponse(
            content=markdown,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={proposal_id}.md"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

