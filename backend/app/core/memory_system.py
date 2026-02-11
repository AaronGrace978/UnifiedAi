"""
Memory System for Brain Thinker
Stores and learns from past thinking sessions
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import sqlite3


class MemorySystem:
    """Stores thinking sessions and learns patterns"""
    
    def __init__(self, db_path: str = ""):
        if not db_path:
            explicit = (os.getenv("UNIFIEDAI_DATA_DIR") or "").strip()
            if explicit:
                base = Path(explicit)
            else:
                appdata = os.getenv("APPDATA")
                base = Path(appdata) / "unifiedai" / "backend" if appdata else Path.home() / ".unifiedai" / "backend"
            base.mkdir(parents=True, exist_ok=True)
            db_path = str(base / "brain_memory.db")
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT,
                confidence REAL,
                model TEXT,
                thinking_time REAL,
                iterations INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Thoughts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS thoughts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                content TEXT,
                thought_type TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        
        # Patterns table (learned patterns)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                pattern_data TEXT,
                frequency INTEGER DEFAULT 1,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Context table (for conversation memory)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_session(self, session_data: Dict) -> int:
        """Save a thinking session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (question, answer, confidence, model, thinking_time, iterations)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_data.get("question", ""),
            session_data.get("final_answer", ""),
            session_data.get("confidence", 0.0),
            session_data.get("model", "unknown"),
            session_data.get("thinking_time", 0.0),
            session_data.get("iterations", 0)
        ))
        
        session_id = cursor.lastrowid
        
        # Save thoughts
        for thought in session_data.get("thoughts", []):
            cursor.execute("""
                INSERT INTO thoughts (session_id, content, thought_type, confidence)
                VALUES (?, ?, ?, ?)
            """, (
                session_id,
                thought.get("content", ""),
                thought.get("type", ""),
                thought.get("confidence", 0.0)
            ))
        
        conn.commit()
        conn.close()
        
        # Learn patterns
        self._learn_patterns(session_data)
        
        return session_id
    
    def _learn_patterns(self, session_data: Dict):
        """Extract and learn patterns from session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract question patterns (keywords, topics)
        question = session_data.get("question", "").lower()
        keywords = [w for w in question.split() if len(w) > 4]
        
        for keyword in keywords[:5]:  # Top 5 keywords
            cursor.execute("""
                INSERT OR REPLACE INTO patterns (pattern_type, pattern_data, frequency, last_seen)
                VALUES (?, ?, 
                    COALESCE((SELECT frequency FROM patterns WHERE pattern_type = ? AND pattern_data = ?), 0) + 1,
                    CURRENT_TIMESTAMP)
            """, ("keyword", keyword, "keyword", keyword))
        
        # Learn thinking patterns (which approaches work best)
        for thought in session_data.get("thoughts", []):
            if thought.get("type") == "synthesis" and thought.get("confidence", 0) > 0.8:
                cursor.execute("""
                    INSERT OR REPLACE INTO patterns (pattern_type, pattern_data, frequency, last_seen)
                    VALUES (?, ?, 
                        COALESCE((SELECT frequency FROM patterns WHERE pattern_type = ? AND pattern_data = ?), 0) + 1,
                        CURRENT_TIMESTAMP)
                """, ("high_confidence_approach", "synthesis", "high_confidence_approach", "synthesis"))
        
        conn.commit()
        conn.close()
    
    def get_relevant_context(self, question: str, limit: int = 3) -> List[Dict]:
        """Get relevant past sessions for context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple keyword matching for now
        question_lower = question.lower()
        keywords = [w for w in question_lower.split() if len(w) > 4]
        
        if not keywords:
            conn.close()
            return []
        
        # Find sessions with similar keywords
        placeholders = ",".join(["?"] * len(keywords))
        query = f"""
            SELECT DISTINCT s.* FROM sessions s
            JOIN thoughts t ON s.id = t.session_id
            WHERE LOWER(s.question) LIKE '%{keywords[0]}%'
            ORDER BY s.created_at DESC
            LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "question": row[1],
                "answer": row[2],
                "confidence": row[3],
                "model": row[4],
                "thinking_time": row[5],
                "iterations": row[6],
                "created_at": row[7]
            })
        
        conn.close()
        return results
    
    def get_learned_patterns(self, pattern_type: str = None) -> List[Dict]:
        """Get learned patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if pattern_type:
            cursor.execute("""
                SELECT pattern_type, pattern_data, frequency, last_seen
                FROM patterns
                WHERE pattern_type = ?
                ORDER BY frequency DESC
            """, (pattern_type,))
        else:
            cursor.execute("""
                SELECT pattern_type, pattern_data, frequency, last_seen
                FROM patterns
                ORDER BY frequency DESC
            """)
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "type": row[0],
                "data": row[1],
                "frequency": row[2],
                "last_seen": row[3]
            })
        
        conn.close()
        return results
    
    def save_context(self, key: str, value: str):
        """Save context for conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO context (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        
        conn.commit()
        conn.close()
    
    def get_context(self, key: str) -> Optional[str]:
        """Get saved context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM context WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        conn.close()
        return row[0] if row else None
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(confidence) FROM sessions")
        avg_confidence = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT AVG(thinking_time) FROM sessions")
        avg_time = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT COUNT(*) FROM patterns")
        total_patterns = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_sessions": total_sessions,
            "avg_confidence": round(avg_confidence, 2),
            "avg_thinking_time": round(avg_time, 2),
            "total_patterns": total_patterns
        }

