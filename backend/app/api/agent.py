"""
Matrix-style Agent API
"""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.matrix_agent import matrix_agent


router = APIRouter(prefix="/api/agent", tags=["Matrix Agent"])


class AgentMessage(BaseModel):
    role: str
    content: str


class AgentExecuteRequest(BaseModel):
    message: str
    history: List[AgentMessage] = []
    safety_mode: str = Field(default="smart", pattern="^(confirm-all|smart|speed|off)$")
    intelligence_level: str = Field(default="smart", pattern="^(basic|smart|genius)$")
    max_steps: int = Field(default=4, ge=1, le=8)
    allow_external_tools: bool = True
    auto_execute: bool = False
    persona: str = "UnifiedAi"
    force_creed: bool = False


class AgentExecuteResponse(BaseModel):
    response: str
    steps: int
    actions: List[str]
    pending_approvals: List[Dict[str, Any]]
    trace: List[Dict[str, Any]]
    creed_applied: bool
    creed_hash: str


@router.post("/execute", response_model=AgentExecuteResponse)
async def execute_agent(request: AgentExecuteRequest):
    try:
        history = [{"role": m.role, "content": m.content} for m in request.history]
        result = await matrix_agent.run(
            message=request.message,
            history=history,
            safety_mode=request.safety_mode,
            intelligence_level=request.intelligence_level,
            max_steps=request.max_steps,
            allow_external_tools=request.allow_external_tools,
            auto_execute=request.auto_execute,
            persona=request.persona,
            force_creed=request.force_creed,
        )
        return AgentExecuteResponse(
            response=result.response,
            steps=result.steps,
            actions=result.actions,
            pending_approvals=result.pending_approvals,
            trace=result.trace,
            creed_applied=result.creed_applied,
            creed_hash=result.creed_hash,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent execution error: {exc}")


@router.get("/status")
async def get_agent_status():
    return {
        "status": "online",
        "capabilities": [
            "plan-act-observe-loop",
            "guardian-safety-layer",
            "dino-buddy-creed",
            "external-tools-wikipedia-arxiv",
            "memory-introspection",
        ],
    }
