"""
Matrix-style autonomous agent loop for UnifiedAi.

Flow:
1) Parse direct JSON action if user provided one
2) Otherwise ask model for JSON plan
3) Validate actions through Guardian
4) Execute allowed actions as tools
5) Feed observations back into loop until done or step budget is reached
"""

import json
import re
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional

from app.core.brain_thinker import brain
from app.core.external_knowledge import external_knowledge
from app.core.guardian import validate_action
from app.core.dino_buddy_creed import inject_creed, should_apply_creed, get_creed_hash


@dataclass
class AgentTrace:
    step: int
    action: str
    params: Dict[str, Any]
    allowed: bool
    reason: str
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class AgentResult:
    response: str
    steps: int
    actions: List[str] = field(default_factory=list)
    pending_approvals: List[Dict[str, Any]] = field(default_factory=list)
    trace: List[Dict[str, Any]] = field(default_factory=list)
    creed_applied: bool = False
    creed_hash: str = ""


def _extract_json_object(raw: str) -> Optional[Dict[str, Any]]:
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


def _agent_system_prompt(intelligence_level: str, allow_external_tools: bool) -> str:
    tool_list = [
        "final",
        "refine",
        "quick_think",
        "deep_think",
        "memory_stats",
        "memory_patterns",
    ]
    if allow_external_tools:
        tool_list.extend(["wikipedia_search", "arxiv_search"])

    return f"""You are Matrix Agent inside UnifiedAi.
Return STRICT JSON only:
{{
  "thinking": "brief internal reasoning",
  "done": false,
  "response": "draft or final response for user",
  "actions": [{{"action":"tool_name","params":{{}}}}]
}}

Rules:
- Be concise and useful.
- Use tools only when they materially improve quality.
- Never invent tool results.
- If answer is ready, set done=true and actions=[].
- Intelligence level: {intelligence_level}
- Allowed actions: {", ".join(tool_list)}
"""


async def _execute_action(action: str, params: Dict[str, Any], allow_external_tools: bool) -> Dict[str, Any]:
    if action == "final":
        return {"ok": True, "action": "final"}
    if action == "refine":
        draft = str(params.get("draft", "")).strip()
        prompt = draft or "Improve the last response for clarity and usefulness."
        refined = await brain.quick_think(prompt)
        return {"ok": True, "action": "refine", "response": refined}
    if action == "quick_think":
        question = str(params.get("question", "")).strip()
        answer = await brain.quick_think(question)
        return {"ok": True, "action": "quick_think", "answer": answer}
    if action == "deep_think":
        question = str(params.get("question", "")).strip()
        session = await brain.think_deep(question, use_memory=True, use_emotional_intelligence=True)
        result = session.to_dict()
        return {
            "ok": True,
            "action": "deep_think",
            "answer": result.get("final_answer", ""),
            "confidence": result.get("confidence", 0.0),
            "iterations": result.get("iterations", 1),
        }
    if action == "wikipedia_search":
        if not allow_external_tools:
            return {"ok": False, "error": "External tools disabled"}
        query = str(params.get("query", "")).strip()
        article = await external_knowledge.search_wikipedia(query)
        if not article:
            return {"ok": True, "action": "wikipedia_search", "result": "No article found"}
        return {
            "ok": True,
            "action": "wikipedia_search",
            "title": article.title,
            "summary": article.summary[:1200],
            "url": article.url,
            "related_topics": article.related_topics[:5],
        }
    if action == "arxiv_search":
        if not allow_external_tools:
            return {"ok": False, "error": "External tools disabled"}
        query = str(params.get("query", "")).strip()
        papers = await external_knowledge.search_arxiv(query, max_results=3)
        return {
            "ok": True,
            "action": "arxiv_search",
            "papers": [
                {
                    "title": p.title,
                    "authors": p.authors[:3],
                    "abstract": p.abstract[:500],
                    "published": p.published,
                    "pdf_url": p.pdf_url,
                }
                for p in papers
            ],
        }
    if action == "memory_stats":
        return {"ok": True, "action": "memory_stats", "stats": brain.memory.get_stats()}
    if action == "memory_patterns":
        pattern_type = params.get("pattern_type")
        value = str(pattern_type).strip() if pattern_type else None
        return {
            "ok": True,
            "action": "memory_patterns",
            "patterns": brain.memory.get_learned_patterns(value),
        }
    return {"ok": False, "error": f"Unknown action: {action}"}


class MatrixAgent:
    async def run(
        self,
        message: str,
        history: List[Dict[str, str]],
        safety_mode: str = "smart",
        intelligence_level: str = "smart",
        max_steps: int = 4,
        allow_external_tools: bool = True,
        auto_execute: bool = False,
        persona: str = "UnifiedAi",
        force_creed: bool = False,
    ) -> AgentResult:
        max_steps = max(1, min(max_steps, 8))
        trace: List[AgentTrace] = []
        pending_approvals: List[Dict[str, Any]] = []
        actions_taken: List[str] = []
        final_response = ""

        # Matrix buddy behavior: direct JSON action fast path.
        direct_json = _extract_json_object(message)
        if direct_json and isinstance(direct_json.get("action"), str):
            action = str(direct_json.get("action", "")).strip().lower()
            params = direct_json.get("params") if isinstance(direct_json.get("params"), dict) else {}
            verdict = validate_action(action, params, safety_mode=safety_mode)
            if not verdict.allowed:
                trace.append(
                    AgentTrace(
                        step=1,
                        action=action,
                        params=params,
                        allowed=False,
                        reason=verdict.reason,
                        error=verdict.reason,
                    )
                )
                return AgentResult(
                    response=f"Blocked by Guardian: {verdict.reason}",
                    steps=1,
                    actions=[],
                    pending_approvals=[],
                    trace=[asdict(t) for t in trace],
                    creed_applied=False,
                    creed_hash=get_creed_hash(),
                )

            if verdict.requires_confirmation and not auto_execute:
                pending_approvals.append(
                    {
                        "action": action,
                        "params": verdict.sanitized_params,
                        "reason": "Confirmation required by safety mode",
                    }
                )
                return AgentResult(
                    response="Action is valid but requires confirmation.",
                    steps=1,
                    actions=[],
                    pending_approvals=pending_approvals,
                    trace=[],
                    creed_applied=False,
                    creed_hash=get_creed_hash(),
                )

            result = await _execute_action(action, verdict.sanitized_params, allow_external_tools)
            trace.append(
                AgentTrace(
                    step=1,
                    action=action,
                    params=verdict.sanitized_params,
                    allowed=True,
                    reason=verdict.reason,
                    result=result,
                    error=None if result.get("ok") else result.get("error", "Tool failed"),
                )
            )
            response = result.get("answer") or result.get("response") or f"Executed action: {action}"
            return AgentResult(
                response=str(response),
                steps=1,
                actions=[action],
                pending_approvals=[],
                trace=[asdict(t) for t in trace],
                creed_applied=False,
                creed_hash=get_creed_hash(),
            )

        working_history = history[-10:] if history else []
        current_user_message = message
        creed_applied = should_apply_creed(persona=persona, force=force_creed)

        for step in range(1, max_steps + 1):
            history_text = "\n".join(
                f"{m.get('role', 'user')}: {m.get('content', '')[:1000]}" for m in working_history[-8:]
            )

            planner_system = _agent_system_prompt(intelligence_level, allow_external_tools)
            if creed_applied:
                planner_system = inject_creed(planner_system)

            planner_prompt = f"""User message:
{current_user_message}

Recent conversation:
{history_text}

Decide next best step."""

            raw = await brain._call_ollama(planner_prompt, planner_system)
            plan = _extract_json_object(raw) or {}

            final_response = str(plan.get("response", "")).strip() or final_response
            done = bool(plan.get("done", False))

            actions = plan.get("actions", [])
            if not isinstance(actions, list):
                actions = []

            if done and not actions:
                return AgentResult(
                    response=final_response or "Done.",
                    steps=step,
                    actions=actions_taken,
                    pending_approvals=pending_approvals,
                    trace=[asdict(t) for t in trace],
                    creed_applied=creed_applied,
                    creed_hash=get_creed_hash(),
                )

            if not actions:
                return AgentResult(
                    response=final_response or raw,
                    steps=step,
                    actions=actions_taken,
                    pending_approvals=pending_approvals,
                    trace=[asdict(t) for t in trace],
                    creed_applied=creed_applied,
                    creed_hash=get_creed_hash(),
                )

            for action_item in actions[:3]:
                if not isinstance(action_item, dict):
                    continue

                action = str(action_item.get("action", "")).strip().lower()
                params = action_item.get("params") if isinstance(action_item.get("params"), dict) else {}
                verdict = validate_action(action, params, safety_mode=safety_mode)

                if not verdict.allowed:
                    trace.append(
                        AgentTrace(
                            step=step,
                            action=action,
                            params=params,
                            allowed=False,
                            reason=verdict.reason,
                            error=verdict.reason,
                        )
                    )
                    continue

                if verdict.requires_confirmation and not auto_execute:
                    pending_approvals.append(
                        {
                            "action": action,
                            "params": verdict.sanitized_params,
                            "reason": "Confirmation required by safety mode",
                        }
                    )
                    trace.append(
                        AgentTrace(
                            step=step,
                            action=action,
                            params=verdict.sanitized_params,
                            allowed=True,
                            reason=verdict.reason,
                            error="Pending confirmation",
                        )
                    )
                    continue

                tool_result = await _execute_action(action, verdict.sanitized_params, allow_external_tools)
                tool_error = None if tool_result.get("ok") else tool_result.get("error", "Tool failed")

                trace.append(
                    AgentTrace(
                        step=step,
                        action=action,
                        params=verdict.sanitized_params,
                        allowed=True,
                        reason=verdict.reason,
                        result=tool_result,
                        error=tool_error,
                    )
                )
                actions_taken.append(action)

                working_history.append({"role": "assistant", "content": final_response or ""})
                working_history.append(
                    {
                        "role": "system",
                        "content": f"Tool result ({action}): {json.dumps(tool_result, default=str)[:2000]}",
                    }
                )

                if action == "final":
                    return AgentResult(
                        response=final_response or "Done.",
                        steps=step,
                        actions=actions_taken,
                        pending_approvals=pending_approvals,
                        trace=[asdict(t) for t in trace],
                        creed_applied=creed_applied,
                        creed_hash=get_creed_hash(),
                    )

            current_user_message = (
                "Continue from tool results. Improve final response and decide if another action is needed."
            )

        return AgentResult(
            response=final_response or "Completed max steps. Provide more specific instructions for deeper execution.",
            steps=max_steps,
            actions=actions_taken,
            pending_approvals=pending_approvals,
            trace=[asdict(t) for t in trace],
            creed_applied=creed_applied,
            creed_hash=get_creed_hash(),
        )


matrix_agent = MatrixAgent()
