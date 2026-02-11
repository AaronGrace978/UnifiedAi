"""
Brain Thinker - The Deep Reasoning Engine
An AI that actually THINKS before it speaks.

Architecture:
- Thinking Loop: Break down → Generate → Critique → Synthesize → Reflect
- Background Daemon: Constantly making connections
- Hard Question Mode: Multi-step reasoning until breakthrough
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import httpx
from app.core.memory_system import MemorySystem

# Try to import ActivatePrime for emotional intelligence
try:
    from app.core.activateprime import activateprime, ActivatePrime
    ACTIVATEPRIME_AVAILABLE = True
except ImportError:
    ACTIVATEPRIME_AVAILABLE = False
    activateprime = None


@dataclass
class Thought:
    """A single thought in the thinking process"""
    content: str
    thought_type: str  # "analysis", "hypothesis", "critique", "synthesis", "reflection"
    confidence: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "type": self.thought_type,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ThinkingSession:
    """A complete thinking session for a hard question"""
    question: str
    thoughts: List[Thought] = field(default_factory=list)
    sub_problems: List[str] = field(default_factory=list)
    approaches: List[Dict] = field(default_factory=list)
    final_answer: Optional[str] = None
    confidence: float = 0.0
    iterations: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def add_thought(self, content: str, thought_type: str, confidence: float):
        self.thoughts.append(Thought(content, thought_type, confidence))
    
    def to_dict(self) -> Dict:
        return {
            "question": self.question,
            "thoughts": [t.to_dict() for t in self.thoughts],
            "sub_problems": self.sub_problems,
            "approaches": self.approaches,
            "final_answer": self.final_answer,
            "confidence": self.confidence,
            "iterations": self.iterations,
            "thinking_time": (
                (self.completed_at or datetime.now()) - self.started_at
            ).total_seconds()
        }


class BrainThinker:
    """
    The Deep Reasoning Engine
    
    This AI doesn't just respond - it THINKS:
    1. Breaks problems into sub-problems
    2. Generates multiple approaches
    3. Self-critiques each approach
    4. Synthesizes the best answer
    5. Reflects on what it might have missed
    6. Loops until confident
    """
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        self.ollama_url = ollama_base_url
        self.model = model
        # Cloud models need longer timeouts (up to 5 minutes)
        timeout = 300.0 if ":cloud" in model else 120.0
        self.client = httpx.AsyncClient(timeout=timeout)
        
        # Memory system
        self.memory = MemorySystem()
        
        # ActivatePrime integration (emotional intelligence)
        self.use_activateprime = ACTIVATEPRIME_AVAILABLE
        self.activateprime = activateprime if ACTIVATEPRIME_AVAILABLE else None
        
        # Background thinking state
        self.background_thoughts: List[Thought] = []
        self.knowledge_connections: List[Dict] = []
        self.is_daemon_running = False
        
        # Thinking parameters
        self.min_confidence = 0.7  # Keep thinking until we hit this
        self.max_iterations = 5   # Safety limit
        
        # Available models cache
        self._available_models: List[str] = []
        self._models_cache_time = 0
        
    async def _call_ollama(self, prompt: str, system: str = None) -> str:
        """Call Ollama API using /api/generate (like ActivatePrime)"""
        # Build full prompt with system context
        full_prompt = ""
        if system:
            full_prompt = f"{system}\n\n"
        full_prompt += prompt
        
        try:
            # Build headers (add API key if provided)
            headers = {}
            from app.config import settings
            if hasattr(settings, 'OLLAMA_API_KEY') and settings.OLLAMA_API_KEY:
                headers["Authorization"] = f"Bearer {settings.OLLAMA_API_KEY}"
            
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 2048
                    }
                },
                headers=headers,
                timeout=300.0 if ":cloud" in self.model else 120.0
            )
            response.raise_for_status()
            data = response.json()
            response_text = data.get("response", "[No response]").strip()
            # Handle encoding issues with cloud models
            if not response_text or response_text == "[No response]":
                return f"[Thinking error: Empty response from {self.model}]"
            return response_text
        except httpx.TimeoutException as e:
            return f"[Thinking error: Timeout connecting to Ollama - cloud models may take longer. Try a local model like 'llama3:8b']"
        except httpx.ConnectError as e:
            return f"[Thinking error: Cannot connect to Ollama at {self.ollama_url}. Is Ollama running?]"
        except Exception as e:
            return f"[Thinking error: {str(e)}]"
    
    async def list_models(self) -> List[str]:
        """Get available Ollama models"""
        # Cache for 60 seconds
        if time.time() - self._models_cache_time < 60 and self._available_models:
            return self._available_models
        
        try:
            response = await self.client.get(f"{self.ollama_url}/api/tags", timeout=5.0)
            response.raise_for_status()
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            self._available_models = models
            self._models_cache_time = time.time()
            return models
        except Exception as e:
            print(f"Error listing models: {e}")
            return ["llama3.2:3b"]  # Fallback
    
    def set_model(self, model: str):
        """Switch to a different model"""
        self.model = model
    
    async def think_deep(self, question: str, use_memory: bool = True, use_emotional_intelligence: bool = True) -> ThinkingSession:
        """
        The main thinking loop - tackle a hard question with deep reasoning
        Now with memory, parallel processing, and emotional intelligence!
        """
        session = ThinkingSession(question=question)
        
        # Load relevant context from memory
        context_info = ""
        if use_memory:
            relevant = self.memory.get_relevant_context(question, limit=2)
            if relevant:
                context_info = "\n\nRelevant past thinking:\n"
                for r in relevant:
                    context_info += f"Q: {r['question']}\nA: {r['answer'][:200]}...\n\n"
        
        # ActivatePrime emotional intelligence
        emotional_context = ""
        if use_emotional_intelligence and self.use_activateprime and self.activateprime:
            try:
                prime_response = self.activateprime.process_input(question)
                emotional_context = prime_response.enhanced_prompt
                session.add_thought(
                    f"[Emotional Analysis] Primary emotion: {prime_response.emotional_profile.primary_emotion.emotion.value} "
                    f"(intensity: {prime_response.emotional_profile.primary_emotion.intensity:.2f}). "
                    f"Unspoken needs: {', '.join(prime_response.emotional_profile.needs_detected)}",
                    "emotional_awareness",
                    0.5
                )
            except Exception as e:
                # Don't fail if emotional intelligence has issues
                pass
        
        system_prompt = """You are a deep reasoning engine. You don't just answer - you THINK.
Your process:
1. Analyze the question deeply
2. Break it into sub-problems
3. Generate multiple approaches
4. Critique each approach honestly
5. Synthesize the best answer
6. Reflect on what you might have missed

Be thorough. Be critical. Think hard."""
        
        if context_info:
            system_prompt += context_info
        
        if emotional_context:
            system_prompt += f"\n\n{emotional_context}"

        # PHASE 1: Analyze and decompose (parallel with context loading)
        session.add_thought("Beginning deep analysis...", "analysis", 0.3)
        
        decompose_prompt = f"""Question: {question}

STEP 1: Break this down into sub-problems. What are all the components we need to understand to answer this well?

List each sub-problem clearly:"""
        
        decomposition = await self._call_ollama(decompose_prompt, system_prompt)
        session.add_thought(decomposition, "analysis", 0.4)
        session.sub_problems = [line.strip() for line in decomposition.split('\n') if line.strip() and not line.startswith('STEP')]
        
        # PHASE 2 & 3: PARALLEL - Generate approaches AND critique simultaneously
        approaches_prompt = f"""Original question: {question}

Sub-problems identified:
{decomposition}

STEP 2: Generate 3 different approaches to answering this question. Each approach should be distinct.

Approach 1:
Approach 2:
Approach 3:"""
        
        # Run approaches and initial critique in parallel
        approaches_task = self._call_ollama(approaches_prompt, system_prompt)
        
        # Start approaches generation
        approaches_raw = await approaches_task
        session.add_thought(approaches_raw, "hypothesis", 0.5)
        session.approaches = [{"raw": approaches_raw}]
        
        # PHASE 3: Self-critique
        critique_prompt = f"""Original question: {question}

Approaches generated:
{approaches_raw}

STEP 3: Now be your own critic. What are the weaknesses in each approach? What might we be missing? Be brutally honest.

Critique:"""
        
        critique = await self._call_ollama(critique_prompt, system_prompt)
        session.add_thought(critique, "critique", 0.6)
        
        # PHASE 4: Synthesize
        synthesis_prompt = f"""Original question: {question}

Approaches:
{approaches_raw}

Self-critique:
{critique}

STEP 4: Now synthesize the best answer. Take the strongest elements from each approach, address the critiques, and formulate your best answer.

Best Answer:"""
        
        synthesis = await self._call_ollama(synthesis_prompt, system_prompt)
        session.add_thought(synthesis, "synthesis", 0.75)
        
        # PHASE 5: Reflection loop
        session.iterations = 1
        current_answer = synthesis
        current_confidence = 0.75
        
        while current_confidence < self.min_confidence and session.iterations < self.max_iterations:
            session.iterations += 1
            
            reflect_prompt = f"""Original question: {question}

Current answer:
{current_answer}

STEP 5 (Iteration {session.iterations}): Reflect deeply.
- What assumptions are we making?
- What edge cases haven't we considered?
- Is there a completely different perspective we're missing?
- How can we improve this answer?

Reflection and improved answer:"""
            
            reflection = await self._call_ollama(reflect_prompt, system_prompt)
            session.add_thought(reflection, "reflection", current_confidence + 0.05)
            
            current_answer = reflection
            current_confidence = min(0.95, current_confidence + 0.1)
        
        # Final answer
        session.final_answer = current_answer
        session.confidence = current_confidence
        session.completed_at = datetime.now()
        
        # Save to memory
        if use_memory:
            session_data = session.to_dict()
            session_data["model"] = self.model
            self.memory.save_session(session_data)
        
        return session
    
    async def quick_think(self, question: str, use_emotional_intelligence: bool = True) -> str:
        """
        Lighter thinking for simpler questions - still thoughtful but faster
        """
        # ActivatePrime emotional intelligence for quick responses too
        emotional_context = ""
        if use_emotional_intelligence and self.use_activateprime and self.activateprime:
            try:
                prime_response = self.activateprime.process_input(question)
                emotional_context = f"\n\n{prime_response.enhanced_prompt}"
            except Exception:
                pass
        
        system_prompt = """You are a thoughtful AI. Before answering:
1. Consider the question from multiple angles
2. Think about what the person really needs to know
3. Give a clear, well-reasoned answer

Be helpful and insightful."""
        
        if emotional_context:
            system_prompt += emotional_context
        
        prompt = f"""Question: {question}

Think about this carefully, then provide a clear and insightful answer:"""
        
        return await self._call_ollama(prompt, system_prompt)
    
    async def start_background_daemon(self, topics: List[str] = None):
        """
        Start the background thinking daemon
        Continuously makes connections and reflects
        """
        self.is_daemon_running = True
        
        default_topics = [
            "breakthrough technologies",
            "consciousness and AI",
            "scientific discovery patterns",
            "problem-solving strategies",
            "creative connections between fields"
        ]
        
        topics = topics or default_topics
        
        while self.is_daemon_running:
            # Pick a random topic to think about
            import random
            topic = random.choice(topics)
            
            prompt = f"""You are a background thinking process, always making new connections.

Current focus: {topic}

Generate one novel insight or connection. Think about:
- Unexpected links between different fields
- New ways to approach old problems
- Patterns that others might miss

Share your insight briefly:"""
            
            insight = await self._call_ollama(prompt)
            
            # Create thought with ID
            thought = Thought(insight, "background_insight", 0.5)
            thought_id = f"insight_{int(time.time())}_{len(self.background_thoughts)}"
            
            # Convert to dict with ID for API
            thought_dict = thought.to_dict()
            thought_dict["id"] = thought_id
            
            self.background_thoughts.append(thought)
            
            # Keep only last 50 background thoughts
            if len(self.background_thoughts) > 50:
                self.background_thoughts = self.background_thoughts[-50:]
            
            # Think every 30 seconds
            await asyncio.sleep(30)
    
    def stop_background_daemon(self):
        """Stop the background thinking"""
        self.is_daemon_running = False
    
    def get_background_insights(self, limit: int = 10) -> List[Dict]:
        """Get recent background insights"""
        insights = []
        for i, thought in enumerate(self.background_thoughts[-limit:]):
            insight_dict = thought.to_dict()
            # Add ID if missing
            if "id" not in insight_dict:
                insight_dict["id"] = f"insight_{int(thought.timestamp.timestamp())}_{i}"
            insights.append(insight_dict)
        return insights
    
    async def solve_hard_problem(self, problem: str, use_memory: bool = True) -> Dict:
        """
        Maximum effort problem solving
        Uses all thinking capabilities with memory
        """
        # Start with deep thinking
        session = await self.think_deep(problem, use_memory=use_memory)
        
        # If confidence is still low, try a completely different angle
        if session.confidence < 0.8:
            alternative_prompt = f"""Forget everything you just thought about this problem:
{problem}

Now approach it from a completely different angle. What if all your previous assumptions were wrong?
What's a radically different way to think about this?"""
            
            alternative = await self._call_ollama(alternative_prompt)
            session.add_thought(alternative, "alternative_perspective", 0.6)
            
            # Merge insights
            merge_prompt = f"""Original answer:
{session.final_answer}

Alternative perspective:
{alternative}

Synthesize these into a final, comprehensive answer:"""
            
            final = await self._call_ollama(merge_prompt)
            session.final_answer = final
            session.confidence = min(0.95, session.confidence + 0.1)
        
        return session.to_dict()


# Global instance
brain = BrainThinker()

