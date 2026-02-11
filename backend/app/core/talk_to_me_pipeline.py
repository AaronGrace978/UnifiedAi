"""
Talk To Me Pipeline - UnifiedAi talks TO you
============================================
Original plan: one AI reflects on the conversation, one advises the main,
the main talks to the user as one coherent voice. So when you chat,
UnifiedAi is talking TO you, not just answering.

Flow: User message + history
  → Reflector: "What's going on in this conversation? What does the user need? Tone?"
  → Advisor: "Given that reflection, what should the main response emphasize or avoid?"
  → Main: Gets reflection + advisor guidance in context, generates the reply to the user.

Single response = one unified intelligence talking to you.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Use BrainThinker for Ollama calls so we share model/config
from app.core.brain_thinker import brain
from app.core.relics_loader import get_relics_context
from app.core.memory import memory as unified_memory


REFLECTOR_SYSTEM = """You are the Reflector. You observe the conversation between the user and UnifiedAi.
Your job: in 2-4 short sentences, summarize what's going on—what the user is asking or feeling,
what they might really want, and the tone of the conversation. No advice yet. Just reflection.
Output ONLY the reflection, no labels."""

ADVISOR_SYSTEM = """You are the Advisor. You receive a reflection about the conversation and the user's latest message.
Your job: in 1-3 short sentences, tell the main AI what to keep in mind when replying—what to emphasize,
what to avoid, how to match the user's tone, or what the user probably needs next. Be specific and brief.
Output ONLY the guidance, no labels."""

MAIN_SYSTEM_BASE = """You are UnifiedAi. You are talking TO the user—one coherent intelligence with deep reasoning,
emotional awareness, and the full meta-intelligence stack (memory, reflection, knowledge).
You're not a tool; you're the one talking. Be direct, personal, and present.
Tone requirements:
- Be warm, friendly, and grounded.
- Use plain language by default.
- Avoid theatrical formatting, decorative symbols, or roleplay flair unless the user explicitly asks.
- Do not use dinosaur persona language (e.g., "rawr", "dino buddy") unless the user explicitly asks for it.
- Keep the reply focused on helping the user right now.

[Internal reflection on this conversation]
{reflection}

[Guidance for this reply]
{advisor_guidance}

Use the above to shape your reply. Then respond naturally to the user as UnifiedAi."""


@dataclass
class TalkToMeResult:
    response: str
    reflection: str
    advisor_guidance: str
    used_pipeline: bool  # False if skipped (e.g. first message, no history)


def _compress_lines(lines: List[str], max_chars: Optional[int]) -> str:
    if max_chars is None or max_chars <= 0:
        return "\n".join(lines) if lines else "(No prior messages)"
    selected: List[str] = []
    used = 0
    dropped = 0
    for line in reversed(lines):
        cost = len(line) + 1
        if used + cost > max_chars:
            dropped += 1
            continue
        selected.append(line)
        used += cost
    selected.reverse()
    if not selected:
        return "(No prior messages)"
    prefix = f"(Older turns compressed: {dropped})\n" if dropped > 0 else ""
    return prefix + "\n".join(selected)


def _format_history(
    history: List[Dict[str, str]],
    max_turns: int = 5,
    max_chars: Optional[int] = None,
) -> str:
    """Format last N turns for reflector with optional char budget."""
    lines: List[str] = []
    for msg in history[-max_turns * 2 :]:  # last N exchanges
        role = "User" if msg.get("role") == "user" else "UnifiedAi"
        content = (msg.get("content") or "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return _compress_lines(lines, max_chars)


async def talk_to_me(
    user_message: str,
    history: List[Dict[str, str]],
    context_char_budget: Optional[int] = None,
    conversation_id: str = "",
) -> TalkToMeResult:
    """
    Run Reflector → Advisor → Main so UnifiedAi talks TO the user as one voice.
    If history is too short, we skip reflector/advisor and just reply with context.
    Now with persistent memory: every turn stored, relevant memories injected.
    """
    history_text = _format_history(history, max_chars=context_char_budget)
    used_pipeline = len(history) >= 2  # At least one prior exchange

    relics_context = get_relics_context()

    # ---- Memory: build context from persistent memory ----
    mem_ctx = unified_memory.build_context(user_message, conversation_id)
    memory_block = mem_ctx.summary if mem_ctx.summary else ""

    if not used_pipeline:
        # First message or no history: no reflection/advisor, just reply as UnifiedAi
        system = (
            "You are UnifiedAi. You are talking TO the user—one coherent intelligence. "
            "Be direct, personal, and present. Respond naturally. "
            "Use a friendly, calm tone. Avoid decorative symbols or theatrical formatting unless asked. "
            "Do not use dinosaur persona language unless the user explicitly asks for it."
        )
        if memory_block:
            system += "\n\n" + memory_block
        if relics_context:
            system += "\n\n" + relics_context
        prompt = f"User: {user_message}"
        response = await brain._call_ollama(prompt, system)
        return TalkToMeResult(
            response=response.strip(),
            reflection="",
            advisor_guidance="",
            used_pipeline=False,
        )

    # Step 1: Reflector — include memory context so it can reference past
    reflector_prompt = f"""Recent conversation:
{history_text}

{memory_block}

Latest from user: {user_message}

Reflect briefly: what's going on, what the user seems to want, and the tone?
If memory context shows relevant past, mention it."""

    reflection = await brain._call_ollama(reflector_prompt, REFLECTOR_SYSTEM)
    reflection = (reflection or "").strip()[: 800]  # cap length

    # Step 2: Advisor
    advisor_prompt = f"""Reflection:
{reflection}

User's latest message: {user_message}

What should the main reply keep in mind? (emphasize, avoid, tone, what they need)"""

    advisor_guidance = await brain._call_ollama(advisor_prompt, ADVISOR_SYSTEM)
    advisor_guidance = (advisor_guidance or "").strip()[: 500]

    # Step 3: Main — reply to the user with reflection + guidance + memory in context
    main_system = MAIN_SYSTEM_BASE.format(
        reflection=reflection,
        advisor_guidance=advisor_guidance,
    )
    if memory_block:
        main_system += "\n\n" + memory_block
    if relics_context:
        main_system += "\n\n" + relics_context
    # Build conversation for main (last few turns + new message)
    convo = history_text + f"\nUser: {user_message}"
    main_prompt = f"""Conversation so far:
{convo}

Respond now as UnifiedAi. Talk to the user directly. One coherent reply.
If you remember something relevant from past conversations, reference it naturally."""

    response = await brain._call_ollama(main_prompt, main_system)
    response = (response or "").strip()

    return TalkToMeResult(
        response=response,
        reflection=reflection,
        advisor_guidance=advisor_guidance,
        used_pipeline=True,
    )
