"""
AR/Holographic Interface API Endpoints
WebXR and spatial computing for UnifiedAi
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Dict, Any

from app.core.ar_interface import ar_interface

router = APIRouter(prefix="/api/ar", tags=["AR/Holographic"])


class CreateSceneRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    layout: str = "sphere"


@router.post("/scene")
async def create_spatial_scene(request: CreateSceneRequest) -> Dict[str, Any]:
    """Create a 3D spatial scene from graph data"""
    try:
        scene = ar_interface.create_spatial_scene(
            nodes=request.nodes,
            edges=request.edges,
            layout=request.layout
        )
        return ar_interface.scene_to_dict(scene)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scene/{scene_id}")
async def get_scene(scene_id: str) -> Dict[str, Any]:
    """Get a spatial scene by ID"""
    try:
        scene = ar_interface.get_scene(scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        return ar_interface.scene_to_dict(scene)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scenes")
async def list_scenes() -> Dict[str, Any]:
    """List all spatial scenes"""
    try:
        scenes = ar_interface.list_scenes()
        return {
            "scenes": scenes,
            "count": len(scenes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_webxr_config() -> Dict[str, Any]:
    """Get WebXR configuration"""
    try:
        return ar_interface.get_webxr_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components")
async def get_aframe_components():
    """Get A-Frame component definitions"""
    try:
        components = ar_interface.get_aframe_components()
        return PlainTextResponse(
            content=components,
            media_type="text/html"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

