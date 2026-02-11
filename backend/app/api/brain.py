"""
Brain Thinker API Endpoints
The interface to the deep reasoning engine
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import json
import re

from app.core.brain_thinker import BrainThinker, brain
from app.core.external_knowledge import external_knowledge
from app.core.coordinator import coordinator
from app.core.arena import arena
from app.core.memory import memory as unified_memory
from app.config import settings
import uuid

router = APIRouter()

# Initialize brain with settings
brain.ollama_url = settings.OLLAMA_BASE_URL
brain.model = settings.OLLAMA_MODEL


class ThinkRequest(BaseModel):
    question: str
    mode: str = "deep"  # "deep", "quick", or "maximum"
    model: Optional[str] = None  # Optional model override
    use_memory: bool = True  # Use memory system


class ThinkResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    thinking_time: float
    iterations: int
    thoughts: List[Dict[str, Any]]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    think_deep: bool = False
    talk_to_me: bool = True  # Use Reflector → Advisor → Main so UnifiedAi talks TO you
    autonomous: bool = True  # Let UnifiedAi run multi-step internal loop
    autonomous_max_steps: int = Field(default=3, ge=1, le=8)
    allow_external_tools: bool = True
    coordinator_mode: Optional[bool] = None  # Default follows COORDINATOR_ENABLED
    arena_mode: bool = False  # Directed multi-agent conversation arena
    conversation_id: Optional[str] = None  # Persistent conversation tracking


class ChatResponse(BaseModel):
    response: str
    thinking_process: Optional[List[Dict]] = None
    confidence: float = 0.0
    talk_to_me_used: bool = False  # True when reflection/advisor pipeline was used
    autonomy_steps: int = 1
    autonomy_actions: Optional[List[str]] = None
    conversation_id: Optional[str] = None  # Echoed back for session continuity
    memory_depth: float = 0.0  # 0.0-1.0 how much memory was used
    arena_debate: Optional[List[Dict]] = None  # Full debate transcript for UI rendering


def _normalize_history(message: str, history: List[ChatMessage]) -> List[Dict[str, str]]:
    """
    Normalize incoming history.
    Frontend currently sends `message` and sometimes already-appended user message in history.
    """
    normalized = [{"role": m.role, "content": m.content} for m in history]
    if (
        normalized
        and normalized[-1].get("role") == "user"
        and (normalized[-1].get("content") or "").strip() == (message or "").strip()
    ):
        normalized = normalized[:-1]
    return normalized


def _extract_json_object(raw: str) -> Optional[Dict[str, Any]]:
    """Parse a JSON object from raw model text, with a light fallback."""
    if not raw:
        return None
    text = raw.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None


async def _decide_autonomy_action(
    original_user_message: str,
    latest_draft: str,
    history: List[Dict[str, str]],
    current_step: int,
    max_steps: int,
    allow_external_tools: bool,
) -> Dict[str, Any]:
    """Ask the model whether to finalize or run one more autonomous action."""
    allowed = (
        "final, refine, wikipedia, arxiv, both"
        if allow_external_tools
        else "final, refine"
    )
    system = """You are an autonomy controller for a chat assistant.
Decide if the assistant should finalize now or do one additional internal action first.
Return ONLY valid JSON object with keys:
- done (boolean)
- action (string; one of allowed actions)
- query (string; optional)
- reason (string; brief)
No markdown. No extra text."""
    history_snippet = "\n".join(
        f"{m.get('role', 'unknown')}: {(m.get('content') or '').strip()}"
        for m in history[-8:]
    )
    prompt = f"""Allowed actions: {allowed}
Current step: {current_step}/{max_steps}

Original user message:
{original_user_message}

Latest draft response:
{latest_draft}

Recent conversation:
{history_snippet}

Rules:
- If the draft already answers the user clearly, choose final with done=true.
- Use wikipedia/arxiv/both only when external facts would materially improve quality.
- Use refine for one more internal rewrite pass without tools.
- If step reached max, choose final.
"""
    decision_raw = await brain._call_ollama(prompt, system)
    decision = _extract_json_object(decision_raw) or {}
    action = str(decision.get("action", "final")).strip().lower()
    done = bool(decision.get("done", action == "final"))
    query = str(decision.get("query", "")).strip()
    reason = str(decision.get("reason", "")).strip()
    valid_actions = {"final", "refine", "wikipedia", "arxiv", "both"}
    if action not in valid_actions:
        action = "final"
        done = True
    if not allow_external_tools and action in {"wikipedia", "arxiv", "both"}:
        action = "refine"
    if current_step >= max_steps:
        action = "final"
        done = True
    return {
        "done": done,
        "action": action,
        "query": query,
        "reason": reason,
    }


def _format_tool_context(tool_name: str, payload: str) -> str:
    return (
        "External context for internal reasoning only.\n"
        f"Tool: {tool_name}\n"
        f"{payload}\n"
        "Use this to improve accuracy, then respond directly to the user."
    )


async def _run_external_action(action: str, query: str) -> Optional[str]:
    """Run one supported external action and return compact context text."""
    try:
        if action == "wikipedia":
            article = await external_knowledge.search_wikipedia(query)
            if not article:
                return "Wikipedia returned no results."
            related = ", ".join(article.related_topics[:5]) if article.related_topics else "None"
            return (
                f"Title: {article.title}\n"
                f"Summary: {article.summary[:1200]}\n"
                f"URL: {article.url}\n"
                f"Related topics: {related}"
            )
        if action == "arxiv":
            papers = await external_knowledge.search_arxiv(query, max_results=3)
            if not papers:
                return "arXiv returned no papers."
            lines = []
            for i, paper in enumerate(papers, start=1):
                lines.append(
                    f"{i}. {paper.title} ({paper.published})\n"
                    f"   Authors: {', '.join(paper.authors[:3])}\n"
                    f"   Abstract: {paper.abstract[:500]}\n"
                    f"   URL: {paper.pdf_url}"
                )
            return "\n".join(lines)
        if action == "both":
            wiki_task = external_knowledge.search_wikipedia(query)
            arxiv_task = external_knowledge.search_arxiv(query, max_results=2)
            article, papers = await asyncio.gather(wiki_task, arxiv_task)
            parts: List[str] = []
            if article:
                parts.append(
                    "Wikipedia:\n"
                    f"- {article.title}\n"
                    f"- {article.summary[:900]}\n"
                    f"- {article.url}"
                )
            if papers:
                papers_text = "\n".join(
                    f"- {p.title} ({p.published}) | {p.pdf_url}" for p in papers
                )
                parts.append(f"arXiv:\n{papers_text}")
            return "\n\n".join(parts) if parts else "No external results."
    except Exception as exc:
        return f"External action failed: {exc}"
    return None


@router.post("/arena/stream")
async def arena_stream(request: ChatRequest):
    """
    SSE streaming endpoint for Arena mode.
    Returns Server-Sent Events as agents debate in real time.
    """
    conv_id = request.conversation_id or str(uuid.uuid4())
    unified_memory.store_episode("user", request.message, conv_id)
    unified_memory.bump_interaction()

    async def event_generator():
        try:
            async for event in arena.run_streaming(
                user_message=request.message,
                conversation_id=conv_id,
                history=[{"role": m.role, "content": m.content} for m in request.history],
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            import traceback
            err = {"event": "error", "message": str(e), "trace": traceback.format_exc(limit=2)}
            yield f"data: {json.dumps(err)}\n\n"
        yield "data: {\"event\": \"done\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/talk", response_model=ChatResponse)
async def talk(request: ChatRequest):
    """
    UnifiedAi talks TO you. Uses Reflector → Advisor → Main so the reply
    is one coherent voice informed by the conversation.
    """
    try:
        from app.core.talk_to_me_pipeline import talk_to_me
        history = [{"role": m.role, "content": m.content} for m in request.history]
        result = await talk_to_me(request.message, history)
        return ChatResponse(
            response=result.response,
            thinking_process=(
                [
                    {"type": "reflection", "content": result.reflection},
                    {"type": "advisor", "content": result.advisor_guidance},
                ]
                if result.used_pipeline and result.reflection
                else None
            ),
            confidence=0.85 if result.used_pipeline else 0.75,
            talk_to_me_used=result.used_pipeline,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Talk error: {str(e)}")


@router.post("/think", response_model=ThinkResponse)
async def think(request: ThinkRequest):
    """
    Submit a question for deep thinking
    
    Modes:
    - quick: Fast but thoughtful response
    - deep: Full thinking loop with critique and reflection
    - maximum: Maximum effort, tries alternative perspectives
    """
    try:
        # Switch model if specified
        if request.model:
            brain.set_model(request.model)
        
        if request.mode == "quick":
            answer = await brain.quick_think(request.question)
            return ThinkResponse(
                question=request.question,
                answer=answer,
                confidence=0.7,
                thinking_time=0,
                iterations=1,
                thoughts=[]
            )
        
        elif request.mode == "maximum":
            result = await brain.solve_hard_problem(request.question, use_memory=request.use_memory)
            return ThinkResponse(
                question=request.question,
                answer=result["final_answer"],
                confidence=result["confidence"],
                thinking_time=result["thinking_time"],
                iterations=result["iterations"],
                thoughts=result["thoughts"]
            )
        
        else:  # deep (default)
            session = await brain.think_deep(request.question, use_memory=request.use_memory)
            result = session.to_dict()
            return ThinkResponse(
                question=request.question,
                answer=result["final_answer"],
                confidence=result["confidence"],
                thinking_time=result["thinking_time"],
                iterations=result["iterations"],
                thoughts=result["thoughts"]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Thinking error: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with UnifiedAi. By default uses "talk to me" pipeline so UnifiedAi
    talks TO you (Reflector → Advisor → Main). Set talk_to_me=False for
    plain quick_think; set think_deep=True for full deep-thinking loop.
    """
    try:
        use_coordinator = (
            settings.COORDINATOR_ENABLED
            if request.coordinator_mode is None
            else bool(request.coordinator_mode)
        )

        # ---- Memory: resolve conversation_id and persist user turn ----
        conv_id = request.conversation_id or str(uuid.uuid4())
        unified_memory.store_episode("user", request.message, conv_id)
        unified_memory.bump_interaction()
        unified_memory.cleanup_expired()

        if request.think_deep:
            session = await brain.think_deep(request.message)
            result = session.to_dict()
            # Persist assistant response
            unified_memory.store_episode("assistant", result["final_answer"], conv_id)
            return ChatResponse(
                response=result["final_answer"],
                thinking_process=result["thoughts"],
                confidence=result["confidence"],
                talk_to_me_used=False,
                autonomy_steps=1,
                autonomy_actions=[],
                conversation_id=conv_id,
                memory_depth=0.0,
            )
        # ---- Arena Mode: directed multi-agent conversation ----
        if request.arena_mode and not request.think_deep:
            arena_result = await arena.run(
                user_message=request.message,
                conversation_id=conv_id,
                history=[{"role": m.role, "content": m.content} for m in request.history],
            )
            # Persist
            unified_memory.store_episode("assistant", arena_result.response, conv_id)
            unified_memory.extract_and_store_facts(
                request.message, arena_result.response, conv_id
            )
            mem_ctx = unified_memory.build_context(request.message, conv_id)

            thinking_process = [
                {
                    "type": "arena_plan",
                    "content": f"goals={arena_result.plan.goals}",
                },
            ]
            for i, r in enumerate(arena_result.rounds):
                agents = ", ".join(set(m.agent_name for m in r.messages))
                thinking_process.append({
                    "type": f"arena_round_{i+1}",
                    "content": f"topic={r.topic} | agents={agents}",
                })
            if arena_result.insights:
                thinking_process.append({
                    "type": "arena_insights",
                    "content": " | ".join(arena_result.insights[:3]),
                })
            if mem_ctx.memory_depth_score > 0:
                thinking_process.append(
                    {"type": "memory", "content": f"depth={mem_ctx.memory_depth_score:.0%}"}
                )

            # Build full debate transcript for frontend visualization
            arena_debate = []
            for r in arena_result.rounds:
                round_data = {
                    "round": r.round_num,
                    "topic": r.topic,
                    "messages": [
                        {
                            "agent_id": m.agent_id,
                            "agent_name": m.agent_name,
                            "model": m.model_used,
                            "content": m.content,
                        }
                        for m in r.messages
                    ],
                }
                arena_debate.append(round_data)

            return ChatResponse(
                response=arena_result.response,
                thinking_process=thinking_process,
                confidence=0.92,
                talk_to_me_used=True,
                autonomy_steps=len(arena_result.rounds),
                autonomy_actions=["arena"],
                conversation_id=conv_id,
                memory_depth=mem_ctx.memory_depth_score,
                arena_debate=arena_debate,
            )

        if request.talk_to_me:
            from app.core.talk_to_me_pipeline import talk_to_me

            # UnifiedAi talks TO you with optional autonomous multi-step loop.
            history = _normalize_history(request.message, request.history)

            if use_coordinator:
                coordinated = await coordinator.respond(
                    user_message=request.message,
                    history=history,
                    allow_external_tools=request.allow_external_tools,
                    conversation_id=conv_id,
                )
                # Persist assistant response + extract facts
                unified_memory.store_episode("assistant", coordinated.response, conv_id)
                unified_memory.extract_and_store_facts(
                    request.message, coordinated.response, conv_id
                )
                mem_ctx = unified_memory.build_context(request.message, conv_id)

                thinking_process = [
                    {
                        "type": "director",
                        "content": f"participants={', '.join(coordinated.participants)}",
                    }
                ]
                if coordinated.used_research:
                    thinking_process.append(
                        {"type": "research", "content": "external context used"}
                    )
                if coordinated.compressed_history:
                    thinking_process.append(
                        {"type": "budget", "content": "history compressed for efficiency"}
                    )
                if mem_ctx.memory_depth_score > 0:
                    thinking_process.append(
                        {"type": "memory", "content": f"depth={mem_ctx.memory_depth_score:.0%}"}
                    )
                for note in coordinated.notes[:2]:
                    thinking_process.append({"type": "note", "content": note})

                return ChatResponse(
                    response=coordinated.response,
                    thinking_process=thinking_process,
                    confidence=0.9,
                    talk_to_me_used=True,
                    autonomy_steps=1,
                    autonomy_actions=["coordinator"],
                    conversation_id=conv_id,
                    memory_depth=mem_ctx.memory_depth_score,
                )

            user_message = request.message
            autonomy_actions: List[str] = []
            final_result = None
            steps = 0

            max_steps = request.autonomous_max_steps if request.autonomous else 1

            for step in range(1, max_steps + 1):
                steps = step
                result = await talk_to_me(user_message, history)
                final_result = result

                # Add this internal turn so subsequent autonomy steps have context.
                history.append({"role": "user", "content": user_message})
                history.append({"role": "assistant", "content": result.response})

                if not request.autonomous:
                    break

                decision = await _decide_autonomy_action(
                    original_user_message=request.message,
                    latest_draft=result.response,
                    history=history,
                    current_step=step,
                    max_steps=max_steps,
                    allow_external_tools=request.allow_external_tools,
                )
                action = decision["action"]
                query = decision["query"] or request.message
                if decision["done"] or action == "final":
                    autonomy_actions.append("final")
                    break
                if action == "refine":
                    autonomy_actions.append("refine")
                    user_message = (
                        "Rewrite and improve your last response for clarity, usefulness, and directness. "
                        "Keep it coherent and grounded in the conversation."
                    )
                    continue

                tool_output = await _run_external_action(action, query)
                autonomy_actions.append(f"{action}({query})")
                if not tool_output:
                    break
                user_message = _format_tool_context(action, tool_output)

            if final_result is None:
                raise RuntimeError("Autonomy loop produced no response")

            thinking_process = (
                [
                    {"type": "reflection", "content": final_result.reflection},
                    {"type": "advisor", "content": final_result.advisor_guidance},
                ]
                if final_result.used_pipeline and final_result.reflection
                else []
            )
            if request.autonomous and autonomy_actions:
                thinking_process.append(
                    {
                        "type": "autonomy",
                        "content": " -> ".join(autonomy_actions),
                    }
                )
            # Persist final response + extract facts
            unified_memory.store_episode("assistant", final_result.response, conv_id)
            unified_memory.extract_and_store_facts(
                request.message, final_result.response, conv_id
            )

            return ChatResponse(
                response=final_result.response,
                thinking_process=thinking_process or None,
                confidence=0.85 if final_result.used_pipeline else 0.75,
                talk_to_me_used=final_result.used_pipeline,
                autonomy_steps=max(steps, 1),
                autonomy_actions=autonomy_actions,
                conversation_id=conv_id,
                memory_depth=0.0,
            )
        # Plain mode: quick_think with history + memory
        mem_ctx = unified_memory.build_context(request.message, conv_id)
        context = ""
        if mem_ctx.summary:
            context += mem_ctx.summary + "\n\n"
        if request.history:
            context += "Previous conversation:\n"
            for msg in request.history[-5:]:
                context += f"{msg.role}: {msg.content}\n"
            context += "\n"
        full_prompt = f"{context}User: {request.message}"
        response = await brain.quick_think(full_prompt)
        # Persist
        unified_memory.store_episode("assistant", response, conv_id)
        unified_memory.extract_and_store_facts(request.message, response, conv_id)
        return ChatResponse(
            response=response,
            thinking_process=None,
            confidence=0.75,
            talk_to_me_used=False,
            autonomy_steps=1,
            autonomy_actions=[],
            conversation_id=conv_id,
            memory_depth=mem_ctx.memory_depth_score,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/daemon/start")
async def start_daemon(background_tasks: BackgroundTasks, topics: List[str] = None):
    """Start the background thinking daemon"""
    if brain.is_daemon_running:
        return {"status": "already_running", "message": "Background thinking is already active"}
    
    background_tasks.add_task(brain.start_background_daemon, topics)
    return {"status": "started", "message": "Background thinking daemon started"}


@router.post("/daemon/stop")
async def stop_daemon():
    """Stop the background thinking daemon"""
    brain.stop_background_daemon()
    return {"status": "stopped", "message": "Background thinking daemon stopped"}


@router.get("/daemon/insights")
async def get_insights(limit: int = 10):
    """Get recent insights from background thinking"""
    insights = brain.get_background_insights(limit)
    return {
        "is_running": brain.is_daemon_running,
        "insights": insights,
        "total_thoughts": len(brain.background_thoughts)
    }


@router.get("/models")
async def list_models():
    """List available Ollama models"""
    models = await brain.list_models()
    return {
        "models": models,
        "current_model": brain.model
    }

@router.post("/models/{model_name}")
async def set_model(model_name: str):
    """Switch to a different model"""
    models = await brain.list_models()
    if model_name not in models:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    brain.set_model(model_name)
    return {"status": "success", "model": model_name}

@router.get("/unified-memory/stats")
async def unified_memory_stats():
    """Get persistent memory system statistics."""
    stats = unified_memory.get_stats()
    identity = unified_memory.get_identity()
    return {
        "stats": stats,
        "identity": {
            "user_name": identity.user_name,
            "relationship_stage": identity.relationship_stage,
            "interaction_count": identity.interaction_count,
            "first_seen": identity.first_seen,
            "last_seen": identity.last_seen,
            "emotional_baseline": identity.emotional_baseline,
        },
    }


@router.get("/unified-memory/facts")
async def unified_memory_facts(fact_type: Optional[str] = None, limit: int = 20):
    """Get stored semantic facts."""
    facts = unified_memory.get_all_facts(fact_type=fact_type, limit=limit)
    return {"facts": [{"id": f.id, "type": f.fact_type, "content": f.content, "confidence": f.confidence, "timestamp": f.timestamp} for f in facts]}


@router.get("/relics/status")
async def relics_status():
    """ActivatePrimeCOMPLETE relics: is path set and are we loading context?"""
    try:
        from app.core.relics_loader import get_relics_path, has_relics, list_relic_files
        from app.config import settings
        path = get_relics_path()
        path_str = str(path) if path else (getattr(settings, "ACTIVATEPRIME_RELICTS_PATH", None) or "")
        active = has_relics()
        files = list_relic_files(path, limit=100) if path else []
        return {
            "path": path_str,
            "active": active,
            "file_count": len(files),
            "hint": "Set ACTIVATEPRIME_RELICTS_PATH in .env to your ActivatePrimeCOMPLETE data folder (e.g. G:\\ActivatePrimeCOMPLETE\\data)"
        }
    except Exception as e:
        return {"path": "", "active": False, "file_count": 0, "error": str(e)}

@router.get("/memory/stats")
async def get_memory_stats():
    """Get memory system statistics"""
    stats = brain.memory.get_stats()
    return stats

@router.get("/memory/patterns")
async def get_patterns(pattern_type: Optional[str] = None):
    """Get learned patterns"""
    patterns = brain.memory.get_learned_patterns(pattern_type)
    return {"patterns": patterns}

@router.get("/status")
async def get_status():
    """Get Brain Thinker status"""
    memory_stats = brain.memory.get_stats()
    return {
        "status": "online",
        "model": brain.model,
        "ollama_url": brain.ollama_url,
        "daemon_running": brain.is_daemon_running,
        "background_thoughts": len(brain.background_thoughts),
        "min_confidence_threshold": brain.min_confidence,
        "max_iterations": brain.max_iterations,
        "memory": memory_stats
    }


@router.get("/export/insights/json")
async def export_insights_json():
    """Export all insights as JSON"""
    from fastapi.responses import Response
    import json
    
    insights = brain.get_background_insights(limit=1000)
    
    if not insights:
        raise HTTPException(status_code=404, detail="No insights to export")
    
    # Convert timestamps to strings
    for insight in insights:
        if "timestamp" in insight and hasattr(insight["timestamp"], "isoformat"):
            insight["timestamp"] = insight["timestamp"].isoformat()
    
    content = json.dumps(insights, indent=2, default=str)
    
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": "attachment; filename=unifiedai_insights.json"
        }
    )


@router.get("/export/insights/txt")
async def export_insights_txt():
    """Export all insights as TXT"""
    from fastapi.responses import Response
    
    insights = brain.get_background_insights(limit=1000)
    
    if not insights:
        raise HTTPException(status_code=404, detail="No insights to export")
    
    lines = ["UnifiedAi - Brain Thinker Insights Export", "=" * 50, ""]
    
    for i, insight in enumerate(insights, 1):
        timestamp = insight.get("timestamp", "Unknown")
        if hasattr(timestamp, "strftime"):
            timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        lines.append(f"Insight #{i}")
        lines.append(f"Time: {timestamp}")
        lines.append(f"Type: {insight.get('type', 'background_insight')}")
        lines.append(f"Confidence: {insight.get('confidence', 0):.0%}")
        lines.append("-" * 30)
        lines.append(insight.get("content", ""))
        lines.append("")
        lines.append("=" * 50)
        lines.append("")
    
    content = "\n".join(lines)
    
    return Response(
        content=content,
        media_type="text/plain",
        headers={
            "Content-Disposition": "attachment; filename=unifiedai_insights.txt"
        }
    )
