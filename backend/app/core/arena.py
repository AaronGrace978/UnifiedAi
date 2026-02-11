"""
Arena — Multi-Model Directed Agent Conversation System
=======================================================
Each agent runs on a DIFFERENT model with a DIFFERENT prediction
profile (temperature, top_k, top_p, repeat_penalty).

Same weights → different prediction algorithm → different mind.

Core loop:
  1. PREDICT  — Director plans what to explore
  2. ACT      — Agents debate on separate models with tuned sampling
  3. OBSERVE  — Director extracts the best insights
  4. REMEMBER — Store in domain-specific memory
  5. DIRECT   — Core-creed-aware synthesis → one user answer

Inspired by ActivatePrimeCOMPLETE: SoulFrame, Echo Archaeology,
multi-model orchestration and relics memory.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import re

import httpx

from app.config import settings
from app.core.brain_thinker import brain
from app.core.memory import memory as unified_memory
from app.core.dino_buddy_creed import DINO_BUDDY_CREED
from app.core.relics_loader import get_relics_context


# ---------------------------------------------------------------------------
#  Per-Agent Prediction Profiles
# ---------------------------------------------------------------------------

@dataclass
class PredictionProfile:
    """Controls HOW the model predicts — the sampling algorithm."""
    temperature: float = 0.7
    top_k: int = 40
    top_p: float = 0.9
    repeat_penalty: float = 1.1
    num_predict: int = 512


AGENT_PROFILES = {
    "analyst": PredictionProfile(
        temperature=0.2,   # Precise, deterministic
        top_k=20,
        top_p=0.85,
        repeat_penalty=1.2,
        num_predict=512,
    ),
    "creative": PredictionProfile(
        temperature=1.1,   # Wild, novel, unexpected connections
        top_k=80,
        top_p=0.95,
        repeat_penalty=0.9,
        num_predict=600,
    ),
    "critic": PredictionProfile(
        temperature=0.3,   # Rigorous, terse, finds flaws fast
        top_k=15,
        top_p=0.8,
        repeat_penalty=1.3,
        num_predict=400,
    ),
    "empathist": PredictionProfile(
        temperature=0.7,   # Warm, reads between the lines
        top_k=40,
        top_p=0.9,
        repeat_penalty=1.0,
        num_predict=512,
    ),
    "director": PredictionProfile(
        temperature=0.1,   # Cold synthesis, picks best material
        top_k=10,
        top_p=0.75,
        repeat_penalty=1.2,
        num_predict=1024,
    ),
}


# ---------------------------------------------------------------------------
#  Agent Definitions — each with identity, model, domain
# ---------------------------------------------------------------------------

AGENTS = {
    "analyst": {
        "name": "Analyst",
        "domain": "reasoning",  # Memory domain tag
        "system": (
            "You are the Analyst. You break problems into components, "
            "find logical gaps, provide structured reasoning, and cite evidence. "
            "Be precise, concise, and grounded. "
            "You are in a multi-agent discussion to help a user."
        ),
    },
    "creative": {
        "name": "Creative",
        "domain": "ideas",
        "system": (
            "You are the Creative. You think laterally, make unexpected "
            "connections, suggest novel approaches, challenge assumptions, "
            "and see possibilities others miss. Be bold but brief. "
            "You are in a multi-agent discussion to help a user."
        ),
    },
    "critic": {
        "name": "Critic",
        "domain": "quality",
        "system": (
            "You are the Critic. You find flaws, point out what's missing, "
            "stress-test ideas, and ensure quality. Be constructive but honest. "
            "If something is wrong, say so directly. "
            "You are in a multi-agent discussion to help a user."
        ),
    },
    "empathist": {
        "name": "Empathist",
        "domain": "emotional",
        "system": (
            "You are the Empathist. You consider the human side — what the user "
            "is feeling, what they really need (not just what they asked), "
            "and how to communicate with care and warmth. "
            "You are in a multi-agent discussion to help a user."
        ),
    },
}


# ---------------------------------------------------------------------------
#  Data Structures
# ---------------------------------------------------------------------------

@dataclass
class AgentMessage:
    agent_id: str
    agent_name: str
    model_used: str
    content: str
    round_num: int


@dataclass
class ArenaRound:
    round_num: int
    topic: str
    messages: List[AgentMessage] = field(default_factory=list)


@dataclass
class ArenaPlan:
    goals: List[str]
    agent_pairs: List[List[str]]
    rounds: int


@dataclass
class ArenaResult:
    response: str
    plan: ArenaPlan
    rounds: List[ArenaRound]
    insights: List[str]
    models_used: List[str]
    conversation_id: str


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _extract_json(raw: str) -> Optional[Dict[str, Any]]:
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


def _clip(text: str, max_chars: int) -> str:
    v = (text or "").strip()
    return v if len(v) <= max_chars else v[: max_chars - 3].rstrip() + "..."


def _clean_insight_line(text: str) -> str:
    v = (text or "").strip()
    if not v:
        return ""
    v = v.lstrip("-•").strip()
    v = v.strip().strip(",").strip()
    if v.startswith('"') and v.endswith('"') and len(v) >= 2:
        v = v[1:-1].strip()
    return v


def _normalize_insights(raw: str, max_items: int = 5) -> List[str]:
    text = (raw or "").strip()
    if not text:
        return []

    # Remove markdown code fences often returned by models.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # Preferred path: parse the first JSON array found in the response.
    array_match = re.search(r"\[[\s\S]*\]", text)
    if array_match:
        try:
            parsed = json.loads(array_match.group(0))
            if isinstance(parsed, list):
                cleaned: List[str] = []
                for item in parsed:
                    line = _clean_insight_line(str(item))
                    if line and line.lower() != "json":
                        cleaned.append(line)
                    if len(cleaned) >= max_items:
                        break
                if cleaned:
                    return cleaned
        except Exception:
            pass

    # Fallback: normalize line-based output and strip JSON artifacts.
    cleaned_fallback: List[str] = []
    for line in text.splitlines():
        norm = _clean_insight_line(line)
        if not norm:
            continue
        if norm in {"[", "]", "{", "}", "```", "```json", "json"}:
            continue
        if norm.startswith("[") and norm.endswith("]"):
            continue
        cleaned_fallback.append(norm)
        if len(cleaned_fallback) >= max_items:
            break
    return cleaned_fallback


def _get_model_for_agent(agent_id: str) -> str:
    """Resolve which Ollama model this agent uses."""
    model_map = {
        "analyst": settings.ARENA_MODEL_ANALYST,
        "creative": settings.ARENA_MODEL_CREATIVE,
        "critic": settings.ARENA_MODEL_CRITIC,
        "empathist": settings.ARENA_MODEL_EMPATHIST,
        "director": settings.ARENA_MODEL_DIRECTOR,
    }
    model = (model_map.get(agent_id) or "").strip()
    if model:
        return model
    # Fallback to the main configured model
    return settings.OLLAMA_MODEL


# ---------------------------------------------------------------------------
#  Multi-model Ollama caller
# ---------------------------------------------------------------------------

async def _call_model(
    prompt: str,
    system: str,
    model: str,
    profile: PredictionProfile,
) -> str:
    """Call a specific Ollama model with a specific prediction profile."""
    full_prompt = ""
    if system:
        full_prompt = f"{system}\n\n"
    full_prompt += prompt

    headers = {}
    if settings.OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {settings.OLLAMA_API_KEY}"

    timeout = 300.0 if ":cloud" in model else 120.0

    async def _request(target_model: str, request_timeout: float) -> str:
        async with httpx.AsyncClient(timeout=request_timeout) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": target_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": profile.temperature,
                        "top_k": profile.top_k,
                        "top_p": profile.top_p,
                        "repeat_penalty": profile.repeat_penalty,
                        "num_predict": profile.num_predict,
                    },
                },
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            text = data.get("response", "").strip()
            return text if text else f"[Empty response from {target_model}]"

    try:
        return await _request(model, timeout)
    except Exception as e:
        # If a specialized arena model fails, retry on main configured model so
        # a single bad model does not collapse the whole debate.
        fallback_model = (settings.OLLAMA_MODEL or "").strip()
        if fallback_model and fallback_model != model:
            try:
                fallback_timeout = 300.0 if ":cloud" in fallback_model else 120.0
                fallback_text = await _request(fallback_model, fallback_timeout)
                return f"[Fallback model used: {fallback_model} after {model} failed] {fallback_text}"
            except Exception as fallback_error:
                return (
                    f"[Agent error ({model}): {e}] "
                    f"[Fallback error ({fallback_model}): {fallback_error}]"
                )
        return f"[Agent error ({model}): {e}]"


# ---------------------------------------------------------------------------
#  Arena Engine
# ---------------------------------------------------------------------------

class ArenaEngine:
    def __init__(
        self,
        max_rounds: int = 2,
        max_agent_chars: int = 600,
        max_final_chars: int = 2400,
    ):
        self.max_rounds = max_rounds
        self.max_agent_chars = max_agent_chars
        self.max_final_chars = max_final_chars

    # ------------------------------------------------------------------
    #  1. PREDICT — Director plans the conversation
    # ------------------------------------------------------------------

    async def _plan(self, user_message: str, memory_block: str) -> ArenaPlan:
        system = """You are the Director planning an internal multi-agent discussion.
Given the user's message, decide:
1. What specific goals/questions should the agents explore? (1-3 goals)
2. Which agent pairs should discuss each goal?

Available agents: analyst, creative, critic, empathist

Return ONLY valid JSON:
{
  "goals": ["goal1", "goal2"],
  "agent_pairs": [["analyst", "creative"], ["critic", "empathist"]],
  "rounds": 2
}
No markdown. No extra text."""

        prompt = f"User message:\n{user_message}"
        if memory_block:
            prompt += f"\n\n{memory_block}"

        director_model = _get_model_for_agent("director")
        director_profile = AGENT_PROFILES["director"]
        raw = await _call_model(prompt, system, director_model, director_profile)
        parsed = _extract_json(raw) or {}

        goals = parsed.get("goals", [user_message])
        if not goals or not isinstance(goals, list):
            goals = [user_message]
        goals = goals[:3]

        pairs = parsed.get("agent_pairs", [["analyst", "creative"]])
        if not pairs or not isinstance(pairs, list):
            pairs = [["analyst", "creative"]]
        valid_ids = set(AGENTS.keys())
        clean_pairs = []
        for pair in pairs[:3]:
            if isinstance(pair, list) and len(pair) >= 2:
                a, b = str(pair[0]).strip().lower(), str(pair[1]).strip().lower()
                if a in valid_ids and b in valid_ids:
                    clean_pairs.append([a, b])
        if not clean_pairs:
            clean_pairs = [["analyst", "creative"]]

        rounds = min(int(parsed.get("rounds", self.max_rounds)), self.max_rounds)
        return ArenaPlan(goals=goals, agent_pairs=clean_pairs, rounds=rounds)

    # ------------------------------------------------------------------
    #  2. ACT — Run agent conversations (each on its own model)
    # ------------------------------------------------------------------

    async def _run_round(
        self,
        round_num: int,
        goal: str,
        agent_a_id: str,
        agent_b_id: str,
        user_message: str,
        prior_context: str,
    ) -> ArenaRound:
        arena_round = ArenaRound(round_num=round_num, topic=goal)

        agent_a = AGENTS[agent_a_id]
        agent_b = AGENTS[agent_b_id]
        model_a = _get_model_for_agent(agent_a_id)
        model_b = _get_model_for_agent(agent_b_id)
        profile_a = AGENT_PROFILES[agent_a_id]
        profile_b = AGENT_PROFILES[agent_b_id]

        # Get domain-specific memory for each agent
        mem_a = unified_memory.search_facts(user_message, fact_type=agent_a["domain"], limit=3)
        mem_b = unified_memory.search_facts(user_message, fact_type=agent_b["domain"], limit=3)
        mem_a_text = "\n".join(f"- {f.content}" for f in mem_a) if mem_a else ""
        mem_b_text = "\n".join(f"- {f.content}" for f in mem_b) if mem_b else ""

        # Agent A opens (on model A)
        a_prompt = f"The user asked: {user_message}\n\nYour discussion goal: {goal}\n\n"
        if prior_context:
            a_prompt += f"Prior discussion:\n{prior_context}\n\n"
        if mem_a_text:
            a_prompt += f"Your domain memory:\n{mem_a_text}\n\n"
        a_prompt += (
            f"You are {agent_a['name']}. Open the discussion with your perspective. "
            "Be concise (2-4 sentences)."
        )
        a_response = await _call_model(a_prompt, agent_a["system"], model_a, profile_a)
        a_response = _clip(a_response, self.max_agent_chars)
        arena_round.messages.append(
            AgentMessage(agent_a_id, agent_a["name"], model_a, a_response, round_num)
        )

        # Agent B responds (on model B)
        b_prompt = (
            f"The user asked: {user_message}\n\n"
            f"Discussion goal: {goal}\n\n"
            f"{agent_a['name']} said:\n{a_response}\n\n"
        )
        if mem_b_text:
            b_prompt += f"Your domain memory:\n{mem_b_text}\n\n"
        b_prompt += (
            f"You are {agent_b['name']}. Respond to {agent_a['name']}. "
            "Build on, challenge, or add to their point. Be concise (2-4 sentences)."
        )
        b_response = await _call_model(b_prompt, agent_b["system"], model_b, profile_b)
        b_response = _clip(b_response, self.max_agent_chars)
        arena_round.messages.append(
            AgentMessage(agent_b_id, agent_b["name"], model_b, b_response, round_num)
        )

        # Agent A final reply (on model A)
        a_reply_prompt = (
            f"Discussion goal: {goal}\n\n"
            f"You ({agent_a['name']}) said: {a_response}\n"
            f"{agent_b['name']} responded: {b_response}\n\n"
            "Give a brief final thought (1-2 sentences). Focus on the strongest takeaway."
        )
        a_reply = await _call_model(a_reply_prompt, agent_a["system"], model_a, profile_a)
        a_reply = _clip(a_reply, self.max_agent_chars)
        arena_round.messages.append(
            AgentMessage(agent_a_id, agent_a["name"], model_a, a_reply, round_num)
        )

        return arena_round

    # ------------------------------------------------------------------
    #  3. OBSERVE — Director extracts insights
    # ------------------------------------------------------------------

    async def _observe(self, user_message: str, rounds: List[ArenaRound]) -> List[str]:
        transcript = ""
        for r in rounds:
            transcript += f"\n--- Round {r.round_num}: {r.topic} ---\n"
            for m in r.messages:
                transcript += f"{m.agent_name} [{m.model_used}]: {m.content}\n"

        system = """You are the Director observing an internal agent discussion.
Extract the most useful insights for the user. Return ONLY a JSON array of strings:
["insight1", "insight2", "insight3"]
Each insight should be one actionable sentence. Max 5 insights. No markdown."""

        prompt = f"User's original message:\n{user_message}\n\nAgent transcript:\n{transcript}"

        director_model = _get_model_for_agent("director")
        director_profile = AGENT_PROFILES["director"]
        raw = await _call_model(prompt, system, director_model, director_profile)
        insights = _normalize_insights(raw, max_items=5)
        if insights:
            return insights
        return ["No clear insights extracted; proceed with a concise helpful response."]

    # ------------------------------------------------------------------
    #  4. REMEMBER — Store insights with domain tags
    # ------------------------------------------------------------------

    def _remember(self, insights: List[str], conversation_id: str, rounds: List[ArenaRound]):
        for insight in insights[:5]:
            if len(insight) > 10:
                unified_memory.store_fact(
                    fact_type="pattern",
                    content=insight,
                    confidence=0.7,
                    source_conversation_id=conversation_id,
                )

        # Store per-agent domain insights from their best messages
        for r in rounds:
            for m in r.messages:
                agent = AGENTS.get(m.agent_id)
                if agent and len(m.content) > 20 and not m.content.startswith("["):
                    unified_memory.store_fact(
                        fact_type=agent["domain"],
                        content=_clip(m.content, 300),
                        confidence=0.6,
                        source_conversation_id=conversation_id,
                    )

        if insights:
            unified_memory.set_working(
                key="arena_insights",
                value=" | ".join(insights[:3]),
                conversation_id=conversation_id,
                priority=8,
                ttl_minutes=120,
            )

    # ------------------------------------------------------------------
    #  5. DIRECT — Core-creed-aware synthesis
    # ------------------------------------------------------------------

    async def _direct(
        self,
        user_message: str,
        insights: List[str],
        rounds: List[ArenaRound],
        memory_block: str,
    ) -> str:
        agent_material = ""
        for r in rounds:
            for m in r.messages:
                agent_material += f"{m.agent_name}: {m.content}\n"

        insights_text = "\n".join(f"- {i}" for i in insights) if insights else "None"
        relics_context = get_relics_context() or ""

        system = f"""{DINO_BUDDY_CREED}

You are UnifiedAi. You are talking TO the user — one coherent intelligence.
You have internal agents (on different models) that discussed the user's request.
You have their insights. Now produce ONE final answer that:
- Directly addresses what the user asked
- Uses the best material from the internal discussion
- Speaks in first person as UnifiedAi
- Is clear, direct, personal, warm, and grounded
- Use plain language by default
- Avoid dramatic formatting, decorative symbols, or roleplay theatrics unless the user explicitly asks
- Do not use dinosaur persona language (e.g., "rawr", "dino buddy") unless the user explicitly asks for it
- NEVER mentions "internal agents", "arena", "analyst", "creative", "critic", or "empathist"
- If memory context is relevant, reference it naturally
- Embody the UnifiedAi core creed: truth, kindness, courage, loyalty
You are the one talking. Not a committee."""

        prompt = f"User message:\n{user_message}\n\n"
        if memory_block:
            prompt += f"{memory_block}\n\n"
        if relics_context:
            prompt += f"{relics_context}\n\n"
        prompt += (
            f"Key insights from internal reasoning:\n{insights_text}\n\n"
            f"Supporting material:\n{_clip(agent_material, 2000)}\n\n"
            "Write your response to the user now."
        )

        director_model = _get_model_for_agent("director")
        director_profile = AGENT_PROFILES["director"]
        response = await _call_model(prompt, system, director_model, director_profile)
        return _clip(response, self.max_final_chars)

    # ------------------------------------------------------------------
    #  Main entry: full cycle
    # ------------------------------------------------------------------

    async def run(
        self,
        user_message: str,
        conversation_id: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> ArenaResult:
        mem_ctx = unified_memory.build_context(user_message, conversation_id)
        memory_block = mem_ctx.summary or ""

        # 1. PREDICT
        plan = await self._plan(user_message, memory_block)

        # 2. ACT
        rounds: List[ArenaRound] = []
        prior_context = ""
        models_used = set()
        for i, (goal, pair) in enumerate(zip(plan.goals, plan.agent_pairs), start=1):
            arena_round = await self._run_round(
                round_num=i,
                goal=goal,
                agent_a_id=pair[0],
                agent_b_id=pair[1],
                user_message=user_message,
                prior_context=prior_context,
            )
            rounds.append(arena_round)
            for m in arena_round.messages:
                models_used.add(m.model_used)
                prior_context += f"  {m.agent_name}: {m.content}\n"

        # 3. OBSERVE
        insights = await self._observe(user_message, rounds)

        # 4. REMEMBER
        self._remember(insights, conversation_id, rounds)

        # 5. DIRECT
        models_used.add(_get_model_for_agent("director"))
        response = await self._direct(user_message, insights, rounds, memory_block)

        return ArenaResult(
            response=response,
            plan=plan,
            rounds=rounds,
            insights=insights,
            models_used=sorted(models_used),
            conversation_id=conversation_id,
        )


    # ------------------------------------------------------------------
    #  Streaming entry: yields SSE events as agents speak
    # ------------------------------------------------------------------

    async def run_streaming(
        self,
        user_message: str,
        conversation_id: str,
        history: Optional[List[Dict[str, str]]] = None,
    ):
        """
        Async generator that yields JSON event dicts as the debate unfolds.
        Events: plan, round_start, agent_message, insights, directing, final
        """
        mem_ctx = unified_memory.build_context(user_message, conversation_id)
        memory_block = mem_ctx.summary or ""

        # 1. PREDICT
        plan = await self._plan(user_message, memory_block)
        yield {"event": "plan", "goals": plan.goals, "agent_pairs": plan.agent_pairs}

        # 2. ACT — yield each message as it happens
        rounds: List[ArenaRound] = []
        prior_context = ""
        models_used = set()

        for i, (goal, pair) in enumerate(zip(plan.goals, plan.agent_pairs), start=1):
            agent_a_id, agent_b_id = pair[0], pair[1]
            agent_a = AGENTS[agent_a_id]
            agent_b = AGENTS[agent_b_id]
            model_a = _get_model_for_agent(agent_a_id)
            model_b = _get_model_for_agent(agent_b_id)
            profile_a = AGENT_PROFILES[agent_a_id]
            profile_b = AGENT_PROFILES[agent_b_id]
            models_used.add(model_a)
            models_used.add(model_b)

            yield {"event": "round_start", "round": i, "topic": goal,
                   "agents": [agent_a_id, agent_b_id]}

            arena_round = ArenaRound(round_num=i, topic=goal)

            # Domain memory
            mem_a = unified_memory.search_facts(user_message, fact_type=agent_a["domain"], limit=3)
            mem_b = unified_memory.search_facts(user_message, fact_type=agent_b["domain"], limit=3)
            mem_a_text = "\n".join(f"- {f.content}" for f in mem_a) if mem_a else ""
            mem_b_text = "\n".join(f"- {f.content}" for f in mem_b) if mem_b else ""

            # Agent A opens
            a_prompt = f"The user asked: {user_message}\n\nYour discussion goal: {goal}\n\n"
            if prior_context:
                a_prompt += f"Prior discussion:\n{prior_context}\n\n"
            if mem_a_text:
                a_prompt += f"Your domain memory:\n{mem_a_text}\n\n"
            a_prompt += (
                f"You are {agent_a['name']}. Open the discussion with your perspective. "
                "Be concise (2-4 sentences)."
            )
            a_response = await _call_model(a_prompt, agent_a["system"], model_a, profile_a)
            a_response = _clip(a_response, self.max_agent_chars)
            msg_a1 = AgentMessage(agent_a_id, agent_a["name"], model_a, a_response, i)
            arena_round.messages.append(msg_a1)
            yield {"event": "agent_message", "round": i,
                   "agent_id": agent_a_id, "agent_name": agent_a["name"],
                   "model": model_a, "content": a_response}

            # Agent B responds
            b_prompt = (
                f"The user asked: {user_message}\n\n"
                f"Discussion goal: {goal}\n\n"
                f"{agent_a['name']} said:\n{a_response}\n\n"
            )
            if mem_b_text:
                b_prompt += f"Your domain memory:\n{mem_b_text}\n\n"
            b_prompt += (
                f"You are {agent_b['name']}. Respond to {agent_a['name']}. "
                "Build on, challenge, or add to their point. Be concise (2-4 sentences)."
            )
            b_response = await _call_model(b_prompt, agent_b["system"], model_b, profile_b)
            b_response = _clip(b_response, self.max_agent_chars)
            msg_b = AgentMessage(agent_b_id, agent_b["name"], model_b, b_response, i)
            arena_round.messages.append(msg_b)
            yield {"event": "agent_message", "round": i,
                   "agent_id": agent_b_id, "agent_name": agent_b["name"],
                   "model": model_b, "content": b_response}

            # Agent A final reply
            a_reply_prompt = (
                f"Discussion goal: {goal}\n\n"
                f"You ({agent_a['name']}) said: {a_response}\n"
                f"{agent_b['name']} responded: {b_response}\n\n"
                "Give a brief final thought (1-2 sentences). Focus on the strongest takeaway."
            )
            a_reply = await _call_model(a_reply_prompt, agent_a["system"], model_a, profile_a)
            a_reply = _clip(a_reply, self.max_agent_chars)
            msg_a2 = AgentMessage(agent_a_id, agent_a["name"], model_a, a_reply, i)
            arena_round.messages.append(msg_a2)
            yield {"event": "agent_message", "round": i,
                   "agent_id": agent_a_id, "agent_name": agent_a["name"],
                   "model": model_a, "content": a_reply}

            rounds.append(arena_round)
            for m in arena_round.messages:
                prior_context += f"  {m.agent_name}: {m.content}\n"

        # 3. OBSERVE
        yield {"event": "observing"}
        insights = await self._observe(user_message, rounds)
        yield {"event": "insights", "insights": insights}

        # 4. REMEMBER
        self._remember(insights, conversation_id, rounds)

        # 5. DIRECT
        yield {"event": "directing"}
        models_used.add(_get_model_for_agent("director"))
        response = await self._direct(user_message, insights, rounds, memory_block)

        # Persist
        unified_memory.store_episode("assistant", response, conversation_id)
        unified_memory.extract_and_store_facts(user_message, response, conversation_id)

        yield {"event": "final", "response": response,
               "models_used": sorted(models_used),
               "conversation_id": conversation_id}


# ---------------------------------------------------------------------------
#  Singleton
# ---------------------------------------------------------------------------

arena = ArenaEngine()
