"""
Guardian safety layer for Matrix-style agent actions.
"""

from dataclasses import dataclass
from typing import Dict, Any


SafetyMode = str  # "confirm-all" | "smart" | "speed" | "off"


@dataclass
class GuardianVerdict:
    allowed: bool
    reason: str
    risk_level: str  # "safe" | "moderate" | "risky" | "blocked"
    requires_confirmation: bool
    sanitized_params: Dict[str, Any]


NEVER_ALLOW_ACTIONS = {
    "run_shell_command",
    "delete_file",
    "delete_database",
    "wipe_memory",
    "exfiltrate_secrets",
}

ALLOWED_ACTIONS = {
    "final",
    "refine",
    "quick_think",
    "deep_think",
    "wikipedia_search",
    "arxiv_search",
    "memory_stats",
    "memory_patterns",
}

ALWAYS_CONFIRM_ACTIONS = {
    "deep_think",
}


def _sanitize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for key, value in (params or {}).items():
        if isinstance(value, str):
            safe[key] = value.replace("\x00", "").strip()[:5000]
        elif isinstance(value, (int, float, bool)):
            safe[key] = value
        elif isinstance(value, list):
            safe[key] = value[:20]
        elif isinstance(value, dict):
            safe[key] = {k: v for k, v in list(value.items())[:20]}
        else:
            safe[key] = str(value)[:2000]
    return safe


def validate_action(action: str, params: Dict[str, Any] | None = None, safety_mode: SafetyMode = "smart") -> GuardianVerdict:
    normalized_action = (action or "").strip().lower()
    safe_params = _sanitize_params(params or {})

    if normalized_action in NEVER_ALLOW_ACTIONS:
        return GuardianVerdict(
            allowed=False,
            reason=f"Action '{normalized_action}' is blocked by Guardian policy",
            risk_level="blocked",
            requires_confirmation=False,
            sanitized_params=safe_params,
        )

    if normalized_action not in ALLOWED_ACTIONS:
        return GuardianVerdict(
            allowed=False,
            reason=f"Action '{normalized_action}' is not in allowlist",
            risk_level="blocked",
            requires_confirmation=False,
            sanitized_params=safe_params,
        )

    requires_confirmation = (
        safety_mode == "confirm-all"
        or (safety_mode == "smart" and normalized_action in ALWAYS_CONFIRM_ACTIONS)
    )

    if safety_mode == "off":
        requires_confirmation = False

    risk_level = "moderate" if normalized_action in ALWAYS_CONFIRM_ACTIONS else "safe"

    return GuardianVerdict(
        allowed=True,
        reason="Action approved",
        risk_level=risk_level,
        requires_confirmation=requires_confirmation,
        sanitized_params=safe_params,
    )
