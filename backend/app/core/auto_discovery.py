"""
Auto-Discovery Mode
Autonomous exploration and insight generation.

The "Dream Mode" - lets the AI explore topics autonomously,
follow chains of reasoning, and build knowledge trees.
"""

import asyncio
import random
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import httpx


@dataclass
class DiscoveryThread:
    """A thread of autonomous exploration"""
    id: str
    seed_topic: str
    current_focus: str
    insights_generated: List[Dict[str, Any]] = field(default_factory=list)
    depth: int = 0
    max_depth: int = 5
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


@dataclass
class DiscoverySession:
    """A complete discovery session"""
    id: str
    mode: str  # "dream", "focused", "exploratory"
    threads: List[DiscoveryThread] = field(default_factory=list)
    total_insights: int = 0
    interesting_connections: List[Dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None


class AutoDiscovery:
    """
    Autonomous exploration and discovery system.
    
    Modes:
    - Dream Mode: Unconstrained creative exploration
    - Focused Mode: Deep dive into a specific topic
    - Exploratory Mode: Follow interesting connections
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        self.ollama_url = ollama_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)
        
        self.active_sessions: Dict[str, DiscoverySession] = {}
        self.is_running = False
        self.session_counter = 0
        
        # Discovery prompts
        self.dream_prompts = [
            "What unexpected connection exists between {topic} and something completely different?",
            "If {topic} was a metaphor for a universal principle, what would it teach us?",
            "What hidden pattern in {topic} might revolutionize our understanding?",
            "Imagine {topic} from the perspective of a consciousness 1000 years in the future.",
            "What's the most counterintuitive truth about {topic} that most people miss?",
        ]
        
        self.exploration_seeds = [
            "consciousness and computation",
            "emergence in complex systems",
            "the nature of time",
            "quantum mechanics and free will",
            "intelligence across substrates",
            "patterns in mathematics and nature",
            "the origin of complexity",
            "information as fundamental",
            "self-reference and recursion",
            "boundaries between order and chaos"
        ]
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama for generation"""
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 512}
                },
                timeout=120.0
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            return f"[Discovery error: {e}]"
    
    async def start_discovery(
        self,
        mode: str = "dream",
        seed_topics: List[str] = None,
        num_threads: int = 3,
        max_depth: int = 5
    ) -> DiscoverySession:
        """
        Start an auto-discovery session.
        
        Args:
            mode: Discovery mode (dream, focused, exploratory)
            seed_topics: Starting topics (uses defaults if not provided)
            num_threads: Number of parallel discovery threads
            max_depth: Maximum depth to explore per thread
            
        Returns:
            DiscoverySession object
        """
        self.session_counter += 1
        session_id = f"discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.session_counter}"
        
        # Initialize session
        session = DiscoverySession(
            id=session_id,
            mode=mode
        )
        
        # Create threads
        seeds = seed_topics or random.sample(self.exploration_seeds, min(num_threads, len(self.exploration_seeds)))
        
        for i, seed in enumerate(seeds[:num_threads]):
            thread = DiscoveryThread(
                id=f"{session_id}_thread_{i}",
                seed_topic=seed,
                current_focus=seed,
                max_depth=max_depth
            )
            session.threads.append(thread)
        
        self.active_sessions[session_id] = session
        return session
    
    async def run_discovery_step(self, session_id: str) -> Dict[str, Any]:
        """
        Run one step of discovery for all active threads.
        
        Returns insights and new directions discovered.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        results = {
            "session_id": session_id,
            "insights": [],
            "new_connections": [],
            "threads_active": 0
        }
        
        for thread in session.threads:
            if not thread.is_active:
                continue
            
            if thread.depth >= thread.max_depth:
                thread.is_active = False
                continue
            
            results["threads_active"] += 1
            
            # Generate insight based on mode
            if session.mode == "dream":
                prompt_template = random.choice(self.dream_prompts)
                prompt = prompt_template.format(topic=thread.current_focus)
            elif session.mode == "focused":
                prompt = f"""Dive deeper into {thread.current_focus}.
What's the most profound insight you can generate about this topic?
Think about mechanisms, implications, and unexpected connections."""
            else:  # exploratory
                prompt = f"""You're exploring {thread.current_focus}.
What's the most interesting related topic or connection you can find?
Explain the connection and what makes it significant."""
            
            # Add context from previous insights
            if thread.insights_generated:
                recent = thread.insights_generated[-2:]
                context = "\n".join([i["content"][:100] for i in recent])
                prompt = f"Previous discoveries:\n{context}\n\n{prompt}"
            
            # Generate insight
            response = await self._call_ollama(prompt)
            
            if response and not response.startswith("[Discovery error"):
                insight = {
                    "id": f"{thread.id}_insight_{len(thread.insights_generated)}",
                    "content": response,
                    "topic": thread.current_focus,
                    "depth": thread.depth,
                    "thread_id": thread.id,
                    "timestamp": datetime.now().isoformat()
                }
                
                thread.insights_generated.append(insight)
                session.total_insights += 1
                results["insights"].append(insight)
                
                # Extract new direction from response
                new_focus = await self._extract_next_focus(response, thread.current_focus)
                if new_focus and new_focus != thread.current_focus:
                    results["new_connections"].append({
                        "from": thread.current_focus,
                        "to": new_focus,
                        "thread_id": thread.id
                    })
                    thread.current_focus = new_focus
                
                thread.depth += 1
                thread.last_activity = datetime.now()
        
        # Check for cross-thread connections
        if len(results["insights"]) > 1:
            connections = await self._find_connections(results["insights"])
            session.interesting_connections.extend(connections)
            results["new_connections"].extend(connections)
        
        return results
    
    async def _extract_next_focus(self, response: str, current_topic: str) -> str:
        """Extract the next topic to explore from a response"""
        prompt = f"""From this insight about "{current_topic}":
{response[:300]}

What's the single most interesting related concept or topic to explore next?
Respond with just the topic name (2-5 words):"""
        
        next_topic = await self._call_ollama(prompt)
        # Clean up response
        next_topic = next_topic.strip().strip('"').strip("'")
        if len(next_topic) < 50:  # Reasonable length check
            return next_topic
        return current_topic  # Stay on current topic if extraction failed
    
    async def _find_connections(self, insights: List[Dict]) -> List[Dict]:
        """Find connections between insights from different threads"""
        if len(insights) < 2:
            return []
        
        # Simple keyword-based connection finding
        connections = []
        
        for i, insight1 in enumerate(insights):
            for insight2 in insights[i+1:]:
                if insight1.get("thread_id") != insight2.get("thread_id"):
                    # Check for word overlap
                    words1 = set(insight1["content"].lower().split())
                    words2 = set(insight2["content"].lower().split())
                    
                    # Filter common words
                    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "is", "are", "was", "were", "be", "been"}
                    words1 = {w for w in words1 if w not in stop_words and len(w) > 3}
                    words2 = {w for w in words2 if w not in stop_words and len(w) > 3}
                    
                    overlap = words1 & words2
                    if len(overlap) >= 3:
                        connections.append({
                            "insight1_id": insight1["id"],
                            "insight2_id": insight2["id"],
                            "shared_concepts": list(overlap)[:5],
                            "type": "cross_thread"
                        })
        
        return connections
    
    async def run_continuous_discovery(
        self,
        session_id: str,
        max_steps: int = 10,
        delay_seconds: float = 5.0
    ):
        """
        Run continuous discovery until max steps or all threads exhaust.
        
        Yields results after each step.
        """
        self.is_running = True
        steps = 0
        
        while self.is_running and steps < max_steps:
            result = await self.run_discovery_step(session_id)
            
            if result.get("error"):
                break
            
            if result["threads_active"] == 0:
                break
            
            yield result
            
            steps += 1
            await asyncio.sleep(delay_seconds)
        
        # Mark session as ended
        session = self.active_sessions.get(session_id)
        if session:
            session.ended_at = datetime.now()
    
    def stop_discovery(self):
        """Stop continuous discovery"""
        self.is_running = False
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of a discovery session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "id": session.id,
            "mode": session.mode,
            "total_insights": session.total_insights,
            "threads": [
                {
                    "id": t.id,
                    "seed_topic": t.seed_topic,
                    "current_focus": t.current_focus,
                    "depth": t.depth,
                    "insights_count": len(t.insights_generated),
                    "is_active": t.is_active
                }
                for t in session.threads
            ],
            "interesting_connections": len(session.interesting_connections),
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "duration_seconds": (
                (session.ended_at or datetime.now()) - session.started_at
            ).total_seconds()
        }
    
    def get_all_insights(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all insights from a session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return []
        
        all_insights = []
        for thread in session.threads:
            all_insights.extend(thread.insights_generated)
        
        return sorted(all_insights, key=lambda x: x.get("timestamp", ""))
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all discovery sessions"""
        return [
            {
                "id": session.id,
                "mode": session.mode,
                "total_insights": session.total_insights,
                "is_ended": session.ended_at is not None,
                "started_at": session.started_at.isoformat()
            }
            for session in self.active_sessions.values()
        ]


# Global instance
auto_discovery = AutoDiscovery()

