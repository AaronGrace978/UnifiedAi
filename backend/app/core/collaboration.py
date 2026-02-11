"""
Collaboration System
Multi-user collaboration features for UnifiedAi.

Provides shared workspaces, annotations, and real-time collaboration.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json


class UserRole(Enum):
    """User roles in a workspace"""
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class AnnotationType(Enum):
    """Types of annotations"""
    COMMENT = "comment"
    HIGHLIGHT = "highlight"
    QUESTION = "question"
    SUGGESTION = "suggestion"
    APPROVAL = "approval"


@dataclass
class User:
    """A collaborating user"""
    id: str
    name: str
    email: Optional[str] = None
    avatar_color: str = "#9B59B6"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Annotation:
    """An annotation on an insight or proposal"""
    id: str
    target_id: str  # ID of insight/proposal being annotated
    target_type: str  # "insight", "proposal", "graph_node"
    author_id: str
    annotation_type: AnnotationType
    content: str
    position: Optional[Dict[str, float]] = None  # For spatial annotations
    created_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False


@dataclass
class Workspace:
    """A collaborative workspace"""
    id: str
    name: str
    description: str
    owner_id: str
    members: Dict[str, UserRole] = field(default_factory=dict)
    shared_insights: List[str] = field(default_factory=list)
    shared_proposals: List[str] = field(default_factory=list)
    annotations: List[Annotation] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class CollaborationSystem:
    """
    Multi-user collaboration for UnifiedAi.
    
    Provides:
    - Shared workspaces
    - Insight and proposal sharing
    - Annotations and comments
    - User management
    """
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.workspaces: Dict[str, Workspace] = {}
        self.user_workspaces: Dict[str, List[str]] = {}  # user_id -> workspace_ids
    
    def create_user(self, name: str, email: str = None) -> User:
        """Create a new user"""
        user_id = str(uuid.uuid4())[:8]
        
        # Generate avatar color
        colors = ["#9B59B6", "#3498DB", "#E74C3C", "#2ECC71", "#F1C40F", "#1ABC9C"]
        color = colors[len(self.users) % len(colors)]
        
        user = User(
            id=user_id,
            name=name,
            email=email,
            avatar_color=color
        )
        
        self.users[user_id] = user
        self.user_workspaces[user_id] = []
        
        return user
    
    def create_workspace(
        self,
        name: str,
        description: str,
        owner_id: str
    ) -> Workspace:
        """Create a new collaborative workspace"""
        if owner_id not in self.users:
            raise ValueError("Owner not found")
        
        workspace_id = str(uuid.uuid4())[:8]
        
        workspace = Workspace(
            id=workspace_id,
            name=name,
            description=description,
            owner_id=owner_id,
            members={owner_id: UserRole.OWNER}
        )
        
        self.workspaces[workspace_id] = workspace
        self.user_workspaces[owner_id].append(workspace_id)
        
        return workspace
    
    def add_member(
        self,
        workspace_id: str,
        user_id: str,
        role: UserRole = UserRole.EDITOR
    ) -> bool:
        """Add a member to a workspace"""
        if workspace_id not in self.workspaces:
            return False
        if user_id not in self.users:
            return False
        
        workspace = self.workspaces[workspace_id]
        workspace.members[user_id] = role
        workspace.updated_at = datetime.now()
        
        if workspace_id not in self.user_workspaces.get(user_id, []):
            if user_id not in self.user_workspaces:
                self.user_workspaces[user_id] = []
            self.user_workspaces[user_id].append(workspace_id)
        
        return True
    
    def remove_member(self, workspace_id: str, user_id: str) -> bool:
        """Remove a member from a workspace"""
        if workspace_id not in self.workspaces:
            return False
        
        workspace = self.workspaces[workspace_id]
        
        # Can't remove owner
        if workspace.owner_id == user_id:
            return False
        
        if user_id in workspace.members:
            del workspace.members[user_id]
            workspace.updated_at = datetime.now()
            
            if workspace_id in self.user_workspaces.get(user_id, []):
                self.user_workspaces[user_id].remove(workspace_id)
            
            return True
        
        return False
    
    def share_insight(self, workspace_id: str, insight_id: str) -> bool:
        """Share an insight to a workspace"""
        if workspace_id not in self.workspaces:
            return False
        
        workspace = self.workspaces[workspace_id]
        
        if insight_id not in workspace.shared_insights:
            workspace.shared_insights.append(insight_id)
            workspace.updated_at = datetime.now()
        
        return True
    
    def share_proposal(self, workspace_id: str, proposal_id: str) -> bool:
        """Share a proposal to a workspace"""
        if workspace_id not in self.workspaces:
            return False
        
        workspace = self.workspaces[workspace_id]
        
        if proposal_id not in workspace.shared_proposals:
            workspace.shared_proposals.append(proposal_id)
            workspace.updated_at = datetime.now()
        
        return True
    
    def add_annotation(
        self,
        workspace_id: str,
        target_id: str,
        target_type: str,
        author_id: str,
        annotation_type: str,
        content: str,
        position: Dict[str, float] = None
    ) -> Optional[Annotation]:
        """Add an annotation to an insight or proposal"""
        if workspace_id not in self.workspaces:
            return None
        if author_id not in self.users:
            return None
        
        workspace = self.workspaces[workspace_id]
        
        # Check if user has permission
        if author_id not in workspace.members:
            return None
        
        role = workspace.members[author_id]
        if role == UserRole.VIEWER:
            return None  # Viewers can't annotate
        
        try:
            ann_type = AnnotationType(annotation_type)
        except ValueError:
            ann_type = AnnotationType.COMMENT
        
        annotation = Annotation(
            id=str(uuid.uuid4())[:8],
            target_id=target_id,
            target_type=target_type,
            author_id=author_id,
            annotation_type=ann_type,
            content=content,
            position=position
        )
        
        workspace.annotations.append(annotation)
        workspace.updated_at = datetime.now()
        
        return annotation
    
    def resolve_annotation(self, workspace_id: str, annotation_id: str) -> bool:
        """Mark an annotation as resolved"""
        if workspace_id not in self.workspaces:
            return False
        
        workspace = self.workspaces[workspace_id]
        
        for annotation in workspace.annotations:
            if annotation.id == annotation_id:
                annotation.resolved = True
                workspace.updated_at = datetime.now()
                return True
        
        return False
    
    def get_annotations(
        self,
        workspace_id: str,
        target_id: str = None,
        include_resolved: bool = False
    ) -> List[Dict[str, Any]]:
        """Get annotations for a workspace or specific target"""
        if workspace_id not in self.workspaces:
            return []
        
        workspace = self.workspaces[workspace_id]
        annotations = workspace.annotations
        
        if target_id:
            annotations = [a for a in annotations if a.target_id == target_id]
        
        if not include_resolved:
            annotations = [a for a in annotations if not a.resolved]
        
        return [
            {
                "id": a.id,
                "target_id": a.target_id,
                "target_type": a.target_type,
                "author": self.users[a.author_id].name if a.author_id in self.users else "Unknown",
                "author_id": a.author_id,
                "type": a.annotation_type.value,
                "content": a.content,
                "position": a.position,
                "created_at": a.created_at.isoformat(),
                "resolved": a.resolved
            }
            for a in annotations
        ]
    
    def get_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Get workspace details"""
        if workspace_id not in self.workspaces:
            return None
        
        workspace = self.workspaces[workspace_id]
        
        return {
            "id": workspace.id,
            "name": workspace.name,
            "description": workspace.description,
            "owner_id": workspace.owner_id,
            "members": [
                {
                    "user_id": uid,
                    "name": self.users[uid].name if uid in self.users else "Unknown",
                    "role": role.value
                }
                for uid, role in workspace.members.items()
            ],
            "shared_insights_count": len(workspace.shared_insights),
            "shared_proposals_count": len(workspace.shared_proposals),
            "annotations_count": len([a for a in workspace.annotations if not a.resolved]),
            "created_at": workspace.created_at.isoformat(),
            "updated_at": workspace.updated_at.isoformat()
        }
    
    def get_user_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all workspaces for a user"""
        workspace_ids = self.user_workspaces.get(user_id, [])
        
        return [
            self.get_workspace(wid)
            for wid in workspace_ids
            if wid in self.workspaces
        ]
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users"""
        return [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "avatar_color": u.avatar_color,
                "created_at": u.created_at.isoformat()
            }
            for u in self.users.values()
        ]


# Global instance
collaboration = CollaborationSystem()

