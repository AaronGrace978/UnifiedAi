"""
Collaboration API Endpoints
Multi-user workspace and annotation features
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.collaboration import collaboration, UserRole

router = APIRouter(prefix="/api/collaboration", tags=["Collaboration"])


class CreateUserRequest(BaseModel):
    name: str
    email: Optional[str] = None


class CreateWorkspaceRequest(BaseModel):
    name: str
    description: str
    owner_id: str


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "editor"


class AddAnnotationRequest(BaseModel):
    target_id: str
    target_type: str
    author_id: str
    annotation_type: str = "comment"
    content: str
    position: Optional[Dict[str, float]] = None


class ShareItemRequest(BaseModel):
    item_id: str


# User endpoints
@router.post("/users")
async def create_user(request: CreateUserRequest) -> Dict[str, Any]:
    """Create a new user"""
    try:
        user = collaboration.create_user(request.name, request.email)
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar_color": user.avatar_color
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def list_users() -> Dict[str, Any]:
    """List all users"""
    try:
        users = collaboration.list_users()
        return {
            "users": users,
            "count": len(users)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Workspace endpoints
@router.post("/workspaces")
async def create_workspace(request: CreateWorkspaceRequest) -> Dict[str, Any]:
    """Create a new workspace"""
    try:
        workspace = collaboration.create_workspace(
            name=request.name,
            description=request.description,
            owner_id=request.owner_id
        )
        return collaboration.get_workspace(workspace.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}")
async def get_workspace(workspace_id: str) -> Dict[str, Any]:
    """Get workspace details"""
    try:
        workspace = collaboration.get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return workspace
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/workspaces")
async def get_user_workspaces(user_id: str) -> Dict[str, Any]:
    """Get all workspaces for a user"""
    try:
        workspaces = collaboration.get_user_workspaces(user_id)
        return {
            "user_id": user_id,
            "workspaces": workspaces,
            "count": len(workspaces)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspaces/{workspace_id}/members")
async def add_member(workspace_id: str, request: AddMemberRequest) -> Dict[str, Any]:
    """Add a member to a workspace"""
    try:
        try:
            role = UserRole(request.role)
        except ValueError:
            role = UserRole.EDITOR
        
        success = collaboration.add_member(workspace_id, request.user_id, role)
        if not success:
            raise HTTPException(status_code=400, detail="Could not add member")
        
        return {"status": "added", "user_id": request.user_id, "role": role.value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/workspaces/{workspace_id}/members/{user_id}")
async def remove_member(workspace_id: str, user_id: str) -> Dict[str, Any]:
    """Remove a member from a workspace"""
    try:
        success = collaboration.remove_member(workspace_id, user_id)
        if not success:
            raise HTTPException(status_code=400, detail="Could not remove member")
        return {"status": "removed", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Sharing endpoints
@router.post("/workspaces/{workspace_id}/share/insight")
async def share_insight(workspace_id: str, request: ShareItemRequest) -> Dict[str, Any]:
    """Share an insight to a workspace"""
    try:
        success = collaboration.share_insight(workspace_id, request.item_id)
        if not success:
            raise HTTPException(status_code=400, detail="Could not share insight")
        return {"status": "shared", "insight_id": request.item_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspaces/{workspace_id}/share/proposal")
async def share_proposal(workspace_id: str, request: ShareItemRequest) -> Dict[str, Any]:
    """Share a proposal to a workspace"""
    try:
        success = collaboration.share_proposal(workspace_id, request.item_id)
        if not success:
            raise HTTPException(status_code=400, detail="Could not share proposal")
        return {"status": "shared", "proposal_id": request.item_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Annotation endpoints
@router.post("/workspaces/{workspace_id}/annotations")
async def add_annotation(workspace_id: str, request: AddAnnotationRequest) -> Dict[str, Any]:
    """Add an annotation"""
    try:
        annotation = collaboration.add_annotation(
            workspace_id=workspace_id,
            target_id=request.target_id,
            target_type=request.target_type,
            author_id=request.author_id,
            annotation_type=request.annotation_type,
            content=request.content,
            position=request.position
        )
        
        if not annotation:
            raise HTTPException(status_code=400, detail="Could not add annotation")
        
        return {
            "id": annotation.id,
            "target_id": annotation.target_id,
            "type": annotation.annotation_type.value,
            "content": annotation.content
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/annotations")
async def get_annotations(
    workspace_id: str,
    target_id: Optional[str] = None,
    include_resolved: bool = False
) -> Dict[str, Any]:
    """Get annotations for a workspace"""
    try:
        annotations = collaboration.get_annotations(
            workspace_id=workspace_id,
            target_id=target_id,
            include_resolved=include_resolved
        )
        return {
            "annotations": annotations,
            "count": len(annotations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspaces/{workspace_id}/annotations/{annotation_id}/resolve")
async def resolve_annotation(workspace_id: str, annotation_id: str) -> Dict[str, Any]:
    """Resolve an annotation"""
    try:
        success = collaboration.resolve_annotation(workspace_id, annotation_id)
        if not success:
            raise HTTPException(status_code=400, detail="Could not resolve annotation")
        return {"status": "resolved", "annotation_id": annotation_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

