"""
UnifiedAi Persistent Memory System
===================================
Inspired by ActivatePrimeCOMPLETE's layered memory.

Layers:
  1. Episodic  – every conversation turn, timestamped, searchable
  2. Semantic  – distilled facts, user preferences, learned knowledge
  3. Working   – current session scratchpad (expires)
  4. Identity  – personality traits, relationship state, who the user is

No ML. Pure architecture: store → retrieve → inject → act → remember.
"""

import json
import os
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
#  Data classes
# ---------------------------------------------------------------------------

@dataclass
class Episode:
    id: str
    role: str  # "user" or "assistant"
    content: str
    conversation_id: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticFact:
    id: str
    fact_type: str  # "preference", "fact", "pattern", "correction", "identity"
    content: str
    confidence: float
    source_conversation_id: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkingItem:
    id: str
    key: str
    value: str
    conversation_id: str
    priority: int  # 1-10
    expires_at: str
    created_at: str


@dataclass
class IdentityState:
    user_name: str = ""
    relationship_stage: str = "new"  # new, familiar, trusted, close
    interaction_count: int = 0
    first_seen: str = ""
    last_seen: str = ""
    personality_notes: str = ""  # What UnifiedAi has learned about itself in relation to user
    user_traits: Dict[str, Any] = field(default_factory=dict)
    emotional_baseline: str = "neutral"


@dataclass
class MemoryContext:
    """The assembled memory context ready for prompt injection."""
    relevant_episodes: List[Episode]
    relevant_facts: List[SemanticFact]
    working_items: List[WorkingItem]
    identity: IdentityState
    memory_depth_score: float  # 0.0 = no memory, 1.0 = rich memory
    summary: str  # Human-readable summary for injection


# ---------------------------------------------------------------------------
#  Memory Manager
# ---------------------------------------------------------------------------

DB_NAME = "unified_memory.db"


def _default_memory_db_path() -> str:
    explicit = (os.getenv("UNIFIEDAI_DATA_DIR") or "").strip()
    if explicit:
        base = Path(explicit)
    else:
        appdata = os.getenv("APPDATA")
        base = Path(appdata) / "unifiedai" / "backend" if appdata else Path.home() / ".unifiedai" / "backend"
    base.mkdir(parents=True, exist_ok=True)
    return str(base / DB_NAME)


class MemoryManager:
    """
    Unified persistent memory for UnifiedAi.
    Single SQLite database, four logical layers.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = _default_memory_db_path()
        self.db_path = db_path
        db_parent = Path(self.db_path).parent
        db_parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------
    #  Schema
    # ------------------------------------------------------------------

    def _conn(self) -> sqlite3.Connection:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._conn()
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_episodes_conv
            ON episodes(conversation_id)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_episodes_ts
            ON episodes(timestamp DESC)
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS semantic_facts (
                id TEXT PRIMARY KEY,
                fact_type TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                source_conversation_id TEXT,
                timestamp TEXT NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_facts_type
            ON semantic_facts(fact_type)
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS working_memory (
                id TEXT PRIMARY KEY,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                conversation_id TEXT,
                priority INTEGER DEFAULT 5,
                expires_at TEXT,
                created_at TEXT NOT NULL
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS identity (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                user_name TEXT DEFAULT '',
                relationship_stage TEXT DEFAULT 'new',
                interaction_count INTEGER DEFAULT 0,
                first_seen TEXT,
                last_seen TEXT,
                personality_notes TEXT DEFAULT '',
                user_traits TEXT DEFAULT '{}',
                emotional_baseline TEXT DEFAULT 'neutral'
            )
        """)
        # Ensure exactly one identity row
        c.execute("""
            INSERT OR IGNORE INTO identity (id, first_seen, last_seen)
            VALUES (1, ?, ?)
        """, (datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))

        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    #  Episodic Memory
    # ------------------------------------------------------------------

    def store_episode(
        self,
        role: str,
        content: str,
        conversation_id: str,
        metadata: Optional[Dict] = None,
    ) -> Episode:
        ep = Episode(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            conversation_id=conversation_id,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )
        conn = self._conn()
        conn.execute(
            "INSERT INTO episodes (id, role, content, conversation_id, timestamp, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ep.id, ep.role, ep.content, ep.conversation_id, ep.timestamp,
             json.dumps(ep.metadata)),
        )
        conn.commit()
        conn.close()
        return ep

    def get_conversation(self, conversation_id: str) -> List[Episode]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM episodes WHERE conversation_id = ? ORDER BY timestamp",
            (conversation_id,),
        ).fetchall()
        conn.close()
        return [self._row_to_episode(r) for r in rows]

    def search_episodes(self, query: str, limit: int = 10) -> List[Episode]:
        """Keyword search across all episodes (most recent first)."""
        conn = self._conn()
        words = [w.strip() for w in query.lower().split() if len(w.strip()) > 2]
        if not words:
            conn.close()
            return []
        where = " AND ".join(["LOWER(content) LIKE ?"] * len(words))
        params = [f"%{w}%" for w in words]
        params.append(limit)
        rows = conn.execute(
            f"SELECT * FROM episodes WHERE {where} ORDER BY timestamp DESC LIMIT ?",
            params,
        ).fetchall()
        conn.close()
        return [self._row_to_episode(r) for r in rows]

    def get_recent_episodes(self, limit: int = 20) -> List[Episode]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM episodes ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return list(reversed([self._row_to_episode(r) for r in rows]))

    def count_episodes(self) -> int:
        conn = self._conn()
        count = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
        conn.close()
        return count

    # ------------------------------------------------------------------
    #  Semantic Memory
    # ------------------------------------------------------------------

    def store_fact(
        self,
        fact_type: str,
        content: str,
        confidence: float = 0.7,
        source_conversation_id: str = "",
        metadata: Optional[Dict] = None,
    ) -> SemanticFact:
        fact = SemanticFact(
            id=str(uuid.uuid4()),
            fact_type=fact_type,
            content=content,
            confidence=confidence,
            source_conversation_id=source_conversation_id,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )
        conn = self._conn()
        conn.execute(
            "INSERT INTO semantic_facts (id, fact_type, content, confidence, "
            "source_conversation_id, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (fact.id, fact.fact_type, fact.content, fact.confidence,
             fact.source_conversation_id, fact.timestamp, json.dumps(fact.metadata)),
        )
        conn.commit()
        conn.close()
        return fact

    def search_facts(self, query: str, fact_type: Optional[str] = None, limit: int = 8) -> List[SemanticFact]:
        conn = self._conn()
        words = [w.strip() for w in query.lower().split() if len(w.strip()) > 2]
        if not words:
            conn.close()
            return []
        conditions = ["LOWER(content) LIKE ?"] * len(words)
        params: list = [f"%{w}%" for w in words]
        if fact_type:
            conditions.append("fact_type = ?")
            params.append(fact_type)
        where = " AND ".join(conditions)
        params.append(limit)
        rows = conn.execute(
            f"SELECT * FROM semantic_facts WHERE {where} ORDER BY confidence DESC, timestamp DESC LIMIT ?",
            params,
        ).fetchall()
        conn.close()
        return [self._row_to_fact(r) for r in rows]

    def get_all_facts(self, fact_type: Optional[str] = None, limit: int = 50) -> List[SemanticFact]:
        conn = self._conn()
        if fact_type:
            rows = conn.execute(
                "SELECT * FROM semantic_facts WHERE fact_type = ? ORDER BY confidence DESC LIMIT ?",
                (fact_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM semantic_facts ORDER BY confidence DESC LIMIT ?",
                (limit,),
            ).fetchall()
        conn.close()
        return [self._row_to_fact(r) for r in rows]

    def update_fact_confidence(self, fact_id: str, new_confidence: float):
        conn = self._conn()
        conn.execute(
            "UPDATE semantic_facts SET confidence = ?, timestamp = ? WHERE id = ?",
            (new_confidence, datetime.utcnow().isoformat(), fact_id),
        )
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    #  Working Memory
    # ------------------------------------------------------------------

    def set_working(
        self,
        key: str,
        value: str,
        conversation_id: str = "",
        priority: int = 5,
        ttl_minutes: int = 60,
    ) -> WorkingItem:
        item = WorkingItem(
            id=str(uuid.uuid4()),
            key=key,
            value=value,
            conversation_id=conversation_id,
            priority=priority,
            expires_at=(datetime.utcnow() + timedelta(minutes=ttl_minutes)).isoformat(),
            created_at=datetime.utcnow().isoformat(),
        )
        conn = self._conn()
        # Replace existing key for this conversation
        conn.execute(
            "DELETE FROM working_memory WHERE key = ? AND conversation_id = ?",
            (key, conversation_id),
        )
        conn.execute(
            "INSERT INTO working_memory (id, key, value, conversation_id, priority, expires_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (item.id, item.key, item.value, item.conversation_id,
             item.priority, item.expires_at, item.created_at),
        )
        conn.commit()
        conn.close()
        return item

    def get_working(self, conversation_id: str = "") -> List[WorkingItem]:
        now = datetime.utcnow().isoformat()
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM working_memory WHERE conversation_id = ? AND expires_at > ? "
            "ORDER BY priority DESC",
            (conversation_id, now),
        ).fetchall()
        conn.close()
        return [self._row_to_working(r) for r in rows]

    def cleanup_expired(self):
        now = datetime.utcnow().isoformat()
        conn = self._conn()
        conn.execute("DELETE FROM working_memory WHERE expires_at <= ?", (now,))
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    #  Identity
    # ------------------------------------------------------------------

    def get_identity(self) -> IdentityState:
        conn = self._conn()
        row = conn.execute("SELECT * FROM identity WHERE id = 1").fetchone()
        conn.close()
        if not row:
            return IdentityState()
        return IdentityState(
            user_name=row["user_name"] or "",
            relationship_stage=row["relationship_stage"] or "new",
            interaction_count=row["interaction_count"] or 0,
            first_seen=row["first_seen"] or "",
            last_seen=row["last_seen"] or "",
            personality_notes=row["personality_notes"] or "",
            user_traits=json.loads(row["user_traits"] or "{}"),
            emotional_baseline=row["emotional_baseline"] or "neutral",
        )

    def update_identity(self, **kwargs):
        allowed = {
            "user_name", "relationship_stage", "interaction_count",
            "last_seen", "personality_notes", "user_traits", "emotional_baseline",
        }
        sets = []
        params = []
        for k, v in kwargs.items():
            if k not in allowed:
                continue
            if k == "user_traits" and isinstance(v, dict):
                v = json.dumps(v)
            sets.append(f"{k} = ?")
            params.append(v)
        if not sets:
            return
        conn = self._conn()
        conn.execute(f"UPDATE identity SET {', '.join(sets)} WHERE id = 1", params)
        conn.commit()
        conn.close()

    def bump_interaction(self):
        """Increment interaction count + update last_seen + evolve relationship."""
        conn = self._conn()
        conn.execute(
            "UPDATE identity SET interaction_count = interaction_count + 1, "
            "last_seen = ? WHERE id = 1",
            (datetime.utcnow().isoformat(),),
        )
        conn.commit()
        # Evolve relationship stage based on count
        identity = self.get_identity()
        count = identity.interaction_count
        new_stage = identity.relationship_stage
        if count >= 100:
            new_stage = "close"
        elif count >= 30:
            new_stage = "trusted"
        elif count >= 10:
            new_stage = "familiar"
        if new_stage != identity.relationship_stage:
            self.update_identity(relationship_stage=new_stage)
        conn.close()

    # ------------------------------------------------------------------
    #  Memory Context Assembly (the injector)
    # ------------------------------------------------------------------

    def build_context(
        self,
        user_message: str,
        conversation_id: str,
        max_episodes: int = 6,
        max_facts: int = 5,
    ) -> MemoryContext:
        """
        Assemble relevant memory for prompt injection.
        This is the equivalent of ActivatePrime's MemoryContextInjector.
        """
        # 1. Search for relevant past episodes
        relevant_episodes = self.search_episodes(user_message, limit=max_episodes)

        # 2. Search for relevant facts
        relevant_facts = self.search_facts(user_message, limit=max_facts)
        # Always include high-confidence identity facts
        identity_facts = self.get_all_facts(fact_type="identity", limit=3)
        pref_facts = self.get_all_facts(fact_type="preference", limit=3)
        seen_ids = {f.id for f in relevant_facts}
        for f in identity_facts + pref_facts:
            if f.id not in seen_ids and f.confidence >= 0.6:
                relevant_facts.append(f)
                seen_ids.add(f.id)

        # 3. Working memory for current conversation
        working_items = self.get_working(conversation_id)

        # 4. Identity
        identity = self.get_identity()

        # 5. Compute depth score
        episode_count = self.count_episodes()
        fact_count = len(relevant_facts)
        depth = min(1.0, (episode_count / 100) * 0.5 + (fact_count / 10) * 0.3 + (identity.interaction_count / 50) * 0.2)

        # 6. Build human-readable summary
        summary = self._format_memory_summary(
            relevant_episodes, relevant_facts, working_items, identity, depth
        )

        return MemoryContext(
            relevant_episodes=relevant_episodes,
            relevant_facts=relevant_facts,
            working_items=working_items,
            identity=identity,
            memory_depth_score=round(depth, 2),
            summary=summary,
        )

    def _format_memory_summary(
        self,
        episodes: List[Episode],
        facts: List[SemanticFact],
        working: List[WorkingItem],
        identity: IdentityState,
        depth: float,
    ) -> str:
        parts: List[str] = []

        # Identity block
        if identity.user_name:
            parts.append(f"User: {identity.user_name}")
        parts.append(f"Relationship: {identity.relationship_stage} ({identity.interaction_count} interactions)")
        if identity.personality_notes:
            parts.append(f"Notes: {identity.personality_notes}")

        # Facts block
        if facts:
            fact_lines = []
            for f in facts[:5]:
                fact_lines.append(f"- [{f.fact_type}] {f.content}")
            parts.append("Known facts:\n" + "\n".join(fact_lines))

        # Relevant past conversations
        if episodes:
            ep_lines = []
            for ep in episodes[-4:]:
                role_label = "User" if ep.role == "user" else "UnifiedAi"
                snippet = ep.content[:200] + ("..." if len(ep.content) > 200 else "")
                ep_lines.append(f"- {role_label}: {snippet}")
            parts.append("Relevant past conversation:\n" + "\n".join(ep_lines))

        # Working memory
        if working:
            wm_lines = [f"- {w.key}: {w.value}" for w in working[:4]]
            parts.append("Active context:\n" + "\n".join(wm_lines))

        if not parts:
            return ""

        header = f"=== MEMORY CONTEXT (depth: {depth:.0%}) ==="
        footer = "=== END MEMORY CONTEXT ==="
        return header + "\n" + "\n".join(parts) + "\n" + footer

    # ------------------------------------------------------------------
    #  Fact Extraction (no ML — rule-based)
    # ------------------------------------------------------------------

    def extract_and_store_facts(
        self,
        user_message: str,
        assistant_response: str,
        conversation_id: str,
    ):
        """
        Rule-based fact extraction from a conversation turn.
        No ML. Looks for explicit preference/identity/correction signals.
        """
        msg = user_message.lower().strip()
        facts_to_store: List[Tuple[str, str, float]] = []

        # Name detection
        for prefix in ["my name is ", "i'm ", "i am ", "call me "]:
            if msg.startswith(prefix):
                name_candidate = user_message[len(prefix):].strip().split()[0] if user_message[len(prefix):].strip() else ""
                if name_candidate and len(name_candidate) > 1 and name_candidate[0].isupper():
                    facts_to_store.append(("identity", f"User's name is {name_candidate}", 0.9))
                    self.update_identity(user_name=name_candidate)

        # Preference signals
        pref_signals = [
            ("i like ", "preference", 0.8),
            ("i love ", "preference", 0.9),
            ("i hate ", "preference", 0.8),
            ("i prefer ", "preference", 0.85),
            ("i don't like ", "preference", 0.8),
            ("i enjoy ", "preference", 0.8),
            ("i'm interested in ", "preference", 0.75),
            ("my favorite ", "preference", 0.85),
        ]
        for signal, ftype, conf in pref_signals:
            if signal in msg:
                idx = msg.index(signal)
                rest = user_message[idx + len(signal):].strip()
                if rest and len(rest) > 2:
                    fact_text = f"User: {signal.strip()} {rest[:120]}"
                    facts_to_store.append((ftype, fact_text, conf))

        # Correction signals
        correction_signals = ["actually ", "no, ", "that's wrong", "i meant ", "correction:"]
        for signal in correction_signals:
            if msg.startswith(signal) or f" {signal}" in msg:
                facts_to_store.append(("correction", f"User corrected: {user_message[:200]}", 0.85))
                break

        # Occupation / role signals
        role_signals = ["i work as ", "i'm a ", "i am a ", "my job is "]
        for signal in role_signals:
            if signal in msg:
                idx = msg.index(signal)
                rest = user_message[idx + len(signal):].strip()
                if rest and len(rest) > 2:
                    facts_to_store.append(("identity", f"User's role: {rest[:100]}", 0.85))

        for ftype, content, conf in facts_to_store:
            self.store_fact(
                fact_type=ftype,
                content=content,
                confidence=conf,
                source_conversation_id=conversation_id,
            )

    # ------------------------------------------------------------------
    #  Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        conn = self._conn()
        ep_count = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
        fact_count = conn.execute("SELECT COUNT(*) FROM semantic_facts").fetchone()[0]
        wm_count = conn.execute("SELECT COUNT(*) FROM working_memory").fetchone()[0]
        identity = self.get_identity()
        conn.close()
        return {
            "episodes": ep_count,
            "facts": fact_count,
            "working_items": wm_count,
            "interaction_count": identity.interaction_count,
            "relationship_stage": identity.relationship_stage,
            "user_name": identity.user_name,
        }

    # ------------------------------------------------------------------
    #  Row converters
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_episode(row) -> Episode:
        return Episode(
            id=row["id"],
            role=row["role"],
            content=row["content"],
            conversation_id=row["conversation_id"],
            timestamp=row["timestamp"],
            metadata=json.loads(row["metadata"] or "{}"),
        )

    @staticmethod
    def _row_to_fact(row) -> SemanticFact:
        return SemanticFact(
            id=row["id"],
            fact_type=row["fact_type"],
            content=row["content"],
            confidence=row["confidence"],
            source_conversation_id=row["source_conversation_id"] or "",
            timestamp=row["timestamp"],
            metadata=json.loads(row["metadata"] or "{}"),
        )

    @staticmethod
    def _row_to_working(row) -> WorkingItem:
        return WorkingItem(
            id=row["id"],
            key=row["key"],
            value=row["value"],
            conversation_id=row["conversation_id"] or "",
            priority=row["priority"],
            expires_at=row["expires_at"] or "",
            created_at=row["created_at"],
        )


# ---------------------------------------------------------------------------
#  Singleton
# ---------------------------------------------------------------------------

memory = MemoryManager()
