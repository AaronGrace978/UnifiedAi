"""
Coordinator for directed multi-agent responses.

Goal:
- Multiple internal agents contribute.
- A single director produces one user-facing answer.
- Keep context and intermediate outputs budgeted for cost control.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json
import re

from app.config import settings
from app.core.brain_thinker import brain
from app.core.external_knowledge import external_knowledge
from app.core.talk_to_me_pipeline import talk_to_me
from app.core.memory import memory as unified_memory


def _clip(text: str, max_chars: int) -> str:
    value = (text or "").strip()
    if len(value) <= max_chars:
        return value
    if max_chars <= 3:
        return value[:max_chars]
    return value[: max_chars - 3].rstrip() + "..."


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


def _compress_history(history: List[Dict[str, str]], max_chars: int) -> str:
    lines: List[str] = []
    chars = 0
    dropped = 0
    for msg in reversed(history):
        role = "User" if msg.get("role") == "user" else "UnifiedAi"
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        line = f"{role}: {content}"
        line_cost = len(line) + 1
        if chars + line_cost > max_chars:
            dropped += 1
            continue
        lines.append(line)
        chars += line_cost
    lines.reverse()
    if not lines:
        return "(No prior messages)"
    if dropped > 0:
        return f"(Older turns compressed: {dropped})\n" + "\n".join(lines)
    return "\n".join(lines)


@dataclass
class CoordinatorResult:
    response: str
    participants: List[str]
    used_research: bool
    compressed_history: bool
    notes: List[str]


class ConversationCoordinator:
    def __init__(self) -> None:
        self.max_history_chars = settings.COORDINATOR_MAX_HISTORY_CHARS
        self.max_agent_output_chars = settings.COORDINATOR_MAX_AGENT_OUTPUT_CHARS
        self.max_reply_chars = settings.COORDINATOR_MAX_REPLY_CHARS

    async def _decide_research(self, user_message: str) -> Dict[str, Any]:
        system = """You decide if an assistant needs external factual lookup.
Return only JSON with:
- research (boolean)
- query (string)
Rules:
- Use research=true only when objective external facts would improve quality.
- For emotional support, writing help, or opinion requests, use false.
No markdown."""
        prompt = f"User message:\n{user_message}"
        raw = await brain._call_ollama(prompt, system)
        parsed = _extract_json_object(raw) or {}
        research = bool(parsed.get("research", False))
        query = str(parsed.get("query", user_message)).strip() or user_message
        return {"research": research, "query": query}

    async def _run_research(self, query: str) -> str:
        article = await external_knowledge.search_wikipedia(query)
        if not article:
            return "Research agent found no reliable external context."
        summary = _clip(article.summary, self.max_agent_output_chars)
        return f"Title: {article.title}\nSummary: {summary}\nURL: {article.url}"

    async def respond(
        self,
        user_message: str,
        history: List[Dict[str, str]],
        allow_external_tools: bool = True,
        conversation_id: str = "",
    ) -> CoordinatorResult:
        history_text = _compress_history(history, self.max_history_chars)
        compressed = len("\n".join(f"{m.get('role')}: {m.get('content')}" for m in history)) > len(history_text)

        # ---- Memory: retrieve persistent context ----
        mem_ctx = unified_memory.build_context(user_message, conversation_id)
        memory_block = mem_ctx.summary if mem_ctx.summary else ""

        # Agent 1: Conversational pipeline tuned to user context.
        conversational = await talk_to_me(
            user_message=user_message,
            history=history,
            context_char_budget=self.max_history_chars,
            conversation_id=conversation_id,
        )
        conversational_text = _clip(conversational.response, self.max_agent_output_chars)

        # Agent 2: Independent analyst for alternative perspective.
        analyst_prompt = (
            f"Conversation context:\n{history_text}\n\n"
        )
        if memory_block:
            analyst_prompt += f"{memory_block}\n\n"
        analyst_prompt += (
            f"User message:\n{user_message}\n\n"
            "Provide a concise direct answer with key points. Do not roleplay."
        )
        analyst_text = await brain.quick_think(analyst_prompt)
        analyst_text = _clip(analyst_text, self.max_agent_output_chars)

        participants = ["converser", "analyst"]
        research_text = ""
        used_research = False
        notes: List[str] = []

        if allow_external_tools:
            decision = await self._decide_research(user_message)
            if decision.get("research"):
                used_research = True
                participants.append("researcher")
                research_query = str(decision.get("query") or user_message).strip()
                notes.append(f"research_query={_clip(research_query, 140)}")
                research_text = await self._run_research(research_query)
                research_text = _clip(research_text, self.max_agent_output_chars)

        # Director synthesis: one voice, targeted to user, memory-aware.
        director_system = """You are the Director agent.
You receive internal agent outputs and produce ONE final answer to the user.
Rules:
- Prioritize directly helping the user now.
- Keep a coherent single voice.
- Resolve conflicts between internal outputs.
- If research is included, use it carefully and avoid over-claiming.
- If memory context shows relevant past conversations or user preferences, reference them naturally.
- Keep a friendly, calm, plain-language tone.
- Avoid dramatic formatting, decorative symbols, or performative roleplay unless the user asks.
- No mention of "internal agents" or chain-of-thought."""
        director_prompt = (
            f"User message:\n{user_message}\n\n"
            f"Conversation context:\n{history_text}\n\n"
        )
        if memory_block:
            director_prompt += f"{memory_block}\n\n"
        director_prompt += (
            f"[Converser output]\n{conversational_text}\n\n"
            f"[Analyst output]\n{analyst_text}\n\n"
            f"[Research output]\n{research_text or 'Not used'}\n\n"
            "Write the best final reply for the user."
        )
        final = await brain._call_ollama(director_prompt, director_system)
        final = _clip(final, self.max_reply_chars)

        return CoordinatorResult(
            response=final,
            participants=participants,
            used_research=used_research,
            compressed_history=compressed,
            notes=notes,
        )


coordinator = ConversationCoordinator()
