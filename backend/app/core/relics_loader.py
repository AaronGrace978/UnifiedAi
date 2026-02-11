"""
ActivatePrimeCOMPLETE Relics Loader
==================================
Gives UnifiedAi read-only access to the ActivatePrimeCOMPLETE data folder (relics)
so it can use that context when talking to you—personality, history, memories.
"""

import os
from pathlib import Path
from typing import List, Optional

from app.config import settings


# Safe extensions for reading (no executables, no huge binaries)
RELIC_EXTENSIONS = {".txt", ".json", ".md", ".log"}
MAX_FILE_SIZE = 512 * 1024  # 512 KB per file
MAX_TOTAL_CHARS = 12000     # total chars to inject so we don't blow context


def get_relics_path() -> Optional[Path]:
    """Return the configured relics path if set and it exists."""
    raw = (getattr(settings, "ACTIVATEPRIME_RELICTS_PATH", None) or "").strip()
    if not raw:
        return None
    p = Path(raw).expanduser().resolve()
    return p if p.is_dir() else None


def _read_file_safe(path: Path) -> Optional[str]:
    try:
        if path.stat().st_size > MAX_FILE_SIZE:
            return None
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except Exception:
        return None


def list_relic_files(base: Path, limit: int = 50) -> List[Path]:
    """List text-like files under base (one level of subdirs)."""
    out: List[Path] = []
    try:
        for item in base.iterdir():
            if item.is_file() and item.suffix.lower() in RELIC_EXTENSIONS:
                out.append(item)
            elif item.is_dir() and len(out) < limit:
                for sub in item.iterdir():
                    if sub.is_file() and sub.suffix.lower() in RELIC_EXTENSIONS:
                        out.append(sub)
                    if len(out) >= limit:
                        break
            if len(out) >= limit:
                break
    except Exception:
        pass
    return out[:limit]


def get_relics_context(max_chars: int = MAX_TOTAL_CHARS) -> str:
    """
    Build a single string of relic content for injection into UnifiedAi context.
    Returns empty string if path not set or no content.
    """
    base = get_relics_path()
    if not base:
        return ""

    files = list_relic_files(base)
    if not files:
        return ""

    parts: List[str] = []
    total = 0
    for path in files:
        if total >= max_chars:
            break
        content = _read_file_safe(path)
        if not content:
            continue
        name = path.name
        # truncate single file if huge
        if len(content) > 4000:
            content = content[:4000] + "\n... [truncated]"
        chunk = f"[{name}]\n{content}\n"
        if total + len(chunk) > max_chars:
            chunk = chunk[: max_chars - total] + "\n... [truncated]"
        parts.append(chunk)
        total += len(chunk)

    if not parts:
        return ""

    return (
        "\n---\n\n[ActivatePrimeCOMPLETE relics - use for context about the user and relationship when relevant]\n\n"
        + "\n".join(parts)
    )


def has_relics() -> bool:
    """True if relics path is set and has at least one readable file."""
    base = get_relics_path()
    if not base:
        return False
    return len(list_relic_files(base, limit=1)) > 0
