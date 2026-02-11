"""
Export API Endpoints
Export knowledge graphs, proposals, and reports
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.export_engine import export_engine

router = APIRouter(prefix="/api/export", tags=["Export"])


class GraphExportRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    title: str = "Knowledge Graph"
    width: int = 1200
    height: int = 800


class ProposalExportRequest(BaseModel):
    proposal: Dict[str, Any]


class InsightsExportRequest(BaseModel):
    insights: List[Dict[str, Any]]
    include_metadata: bool = True


class SessionExportRequest(BaseModel):
    session_data: Dict[str, Any]


@router.get("/capabilities")
async def get_capabilities() -> Dict[str, Any]:
    """Get available export capabilities"""
    try:
        return {
            "capabilities": export_engine.get_capabilities()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/graph/png")
async def export_graph_png(request: GraphExportRequest) -> Dict[str, Any]:
    """Export knowledge graph as PNG image"""
    try:
        result = export_engine.export_graph_png(
            nodes=request.nodes,
            edges=request.edges,
            title=request.title,
            width=request.width,
            height=request.height
        )
        
        return {
            "success": result.success,
            "format": result.format,
            "filename": result.filename,
            "data_base64": result.data_base64,
            "mime_type": result.mime_type,
            "size_bytes": result.size_bytes,
            "error": result.error
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proposal/pdf")
async def export_proposal_pdf(request: ProposalExportRequest) -> Dict[str, Any]:
    """Export research proposal as PDF"""
    try:
        result = export_engine.export_proposal_pdf(request.proposal)
        
        return {
            "success": result.success,
            "format": result.format,
            "filename": result.filename,
            "data_base64": result.data_base64,
            "mime_type": result.mime_type,
            "size_bytes": result.size_bytes,
            "error": result.error
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insights/json")
async def export_insights_json(request: InsightsExportRequest) -> Dict[str, Any]:
    """Export insights as formatted JSON"""
    try:
        result = export_engine.export_insights_json(
            insights=request.insights,
            include_metadata=request.include_metadata
        )
        
        return {
            "success": result.success,
            "format": result.format,
            "filename": result.filename,
            "data_base64": result.data_base64,
            "mime_type": result.mime_type,
            "size_bytes": result.size_bytes,
            "error": result.error
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/report")
async def export_session_report(request: SessionExportRequest) -> Dict[str, Any]:
    """Export thinking session as HTML report"""
    try:
        result = export_engine.export_session_report(request.session_data)
        
        return {
            "success": result.success,
            "format": result.format,
            "filename": result.filename,
            "data_base64": result.data_base64,
            "mime_type": result.mime_type,
            "size_bytes": result.size_bytes,
            "error": result.error
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

