"""
Ensemble Thinker - Multi-Model Reasoning
Uses multiple AI models in parallel for better thinking.

Runs the same question through multiple models, synthesizes their
perspectives, and identifies areas of agreement and disagreement.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import httpx


@dataclass
class ModelResponse:
    """Response from a single model"""
    model_name: str
    response: str
    confidence: float
    thinking_time: float
    error: Optional[str] = None


@dataclass
class EnsembleResult:
    """Combined result from ensemble thinking"""
    question: str
    individual_responses: List[ModelResponse]
    synthesized_answer: str
    agreement_score: float  # How much the models agree (0-1)
    disagreement_areas: List[str]
    key_insights: List[str]
    confidence: float
    total_time: float
    models_used: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "individual_responses": [
                {
                    "model": r.model_name,
                    "response": r.response,
                    "confidence": r.confidence,
                    "thinking_time": r.thinking_time,
                    "error": r.error
                }
                for r in self.individual_responses
            ],
            "synthesized_answer": self.synthesized_answer,
            "agreement_score": self.agreement_score,
            "disagreement_areas": self.disagreement_areas,
            "key_insights": self.key_insights,
            "confidence": self.confidence,
            "total_time": self.total_time,
            "models_used": self.models_used,
            "created_at": self.created_at.isoformat()
        }


class EnsembleThinker:
    """
    Multi-model ensemble reasoning system.
    
    Uses multiple AI models to answer questions, then synthesizes
    their perspectives for more robust, well-rounded answers.
    """
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_base_url
        self.client = httpx.AsyncClient(timeout=120.0)
        
        # Default model ensemble (will be filtered to available models)
        self.preferred_models = [
            "llama3.2:3b",
            "llama3:8b",
            "mistral:7b",
            "gemma2:9b",
            "phi3:mini",
            "qwen2:7b"
        ]
        
        # Synthesis model (should be the most capable available)
        self.synthesis_model = "llama3:8b"
        
        # Cache available models
        self._available_models: List[str] = []
        self._models_cache_time = 0
    
    async def list_available_models(self) -> List[str]:
        """Get available Ollama models"""
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
            return []
    
    async def _call_model(self, model: str, prompt: str, system: str = None) -> ModelResponse:
        """Call a single model and get response"""
        start_time = time.time()
        
        full_prompt = ""
        if system:
            full_prompt = f"{system}\n\n"
        full_prompt += prompt
        
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 1024
                    }
                },
                timeout=120.0
            )
            response.raise_for_status()
            data = response.json()
            response_text = data.get("response", "").strip()
            
            thinking_time = time.time() - start_time
            
            return ModelResponse(
                model_name=model,
                response=response_text,
                confidence=0.7,  # Default confidence
                thinking_time=thinking_time
            )
        except Exception as e:
            return ModelResponse(
                model_name=model,
                response="",
                confidence=0.0,
                thinking_time=time.time() - start_time,
                error=str(e)
            )
    
    async def think_ensemble(
        self, 
        question: str, 
        models: List[str] = None,
        synthesis_model: str = None
    ) -> EnsembleResult:
        """
        Think about a question using multiple models in parallel.
        
        Args:
            question: The question to think about
            models: Optional list of models to use (defaults to available preferred models)
            synthesis_model: Model to use for synthesis (defaults to best available)
            
        Returns:
            EnsembleResult with all perspectives and synthesis
        """
        start_time = time.time()
        
        # Get available models
        available = await self.list_available_models()
        
        # Filter to requested or preferred models
        if models:
            models_to_use = [m for m in models if m in available]
        else:
            models_to_use = [m for m in self.preferred_models if m in available]
        
        # Ensure we have at least 2 models
        if len(models_to_use) < 2:
            models_to_use = available[:3]  # Use first 3 available
        
        # Limit to 4 models for reasonable performance
        models_to_use = models_to_use[:4]
        
        if not models_to_use:
            return EnsembleResult(
                question=question,
                individual_responses=[],
                synthesized_answer="No models available for ensemble thinking.",
                agreement_score=0.0,
                disagreement_areas=["No models available"],
                key_insights=[],
                confidence=0.0,
                total_time=time.time() - start_time,
                models_used=[]
            )
        
        # Determine synthesis model
        synth_model = synthesis_model
        if not synth_model or synth_model not in available:
            # Try to find a good synthesis model
            for preferred in ["llama3:8b", "llama3.2:3b", "mistral:7b"]:
                if preferred in available:
                    synth_model = preferred
                    break
            if not synth_model:
                synth_model = models_to_use[0]
        
        system_prompt = """You are a thoughtful AI assistant. Consider the question carefully 
from multiple perspectives. Provide a clear, reasoned response. Be specific and insightful."""
        
        prompt = f"Question: {question}\n\nProvide your thoughtful analysis and answer:"
        
        # Run all models in parallel
        tasks = [self._call_model(model, prompt, system_prompt) for model in models_to_use]
        responses = await asyncio.gather(*tasks)
        
        # Filter out failed responses
        valid_responses = [r for r in responses if not r.error and r.response]
        
        if not valid_responses:
            return EnsembleResult(
                question=question,
                individual_responses=responses,
                synthesized_answer="All models failed to respond.",
                agreement_score=0.0,
                disagreement_areas=["All models failed"],
                key_insights=[],
                confidence=0.0,
                total_time=time.time() - start_time,
                models_used=models_to_use
            )
        
        # Synthesize responses
        synthesized, agreement, disagreements, insights = await self._synthesize_responses(
            question, valid_responses, synth_model
        )
        
        # Calculate overall confidence
        confidence = (agreement * 0.5) + (len(valid_responses) / len(models_to_use) * 0.3) + 0.2
        
        return EnsembleResult(
            question=question,
            individual_responses=responses,
            synthesized_answer=synthesized,
            agreement_score=agreement,
            disagreement_areas=disagreements,
            key_insights=insights,
            confidence=min(confidence, 0.95),
            total_time=time.time() - start_time,
            models_used=models_to_use
        )
    
    async def _synthesize_responses(
        self, 
        question: str, 
        responses: List[ModelResponse],
        synthesis_model: str
    ) -> Tuple[str, float, List[str], List[str]]:
        """Synthesize multiple model responses into a coherent answer"""
        
        # Build synthesis prompt
        response_text = "\n\n".join([
            f"[{r.model_name}]: {r.response[:500]}" 
            for r in responses
        ])
        
        synthesis_prompt = f"""You have received multiple AI perspectives on a question. 
Synthesize these into a single, coherent answer that captures the best insights from all.

Question: {question}

Perspectives from different models:
{response_text}

Your task:
1. Identify points of AGREEMENT across the responses
2. Note any DISAGREEMENTS or different perspectives
3. Extract KEY INSIGHTS that are particularly valuable
4. Synthesize into a final, comprehensive answer

Format your response as:
AGREEMENT LEVEL: [high/medium/low]
DISAGREEMENTS: [list any disagreements, or "none"]
KEY INSIGHTS:
- [insight 1]
- [insight 2]
SYNTHESIZED ANSWER:
[your synthesized answer]"""

        result = await self._call_model(synthesis_model, synthesis_prompt)
        
        if result.error:
            # Fallback: just combine responses
            combined = " ".join([r.response[:200] for r in responses])
            return combined, 0.5, ["Synthesis failed"], []
        
        # Parse the synthesis response
        synthesis = result.response
        
        # Extract agreement level
        agreement = 0.5
        if "AGREEMENT LEVEL:" in synthesis:
            level_line = synthesis.split("AGREEMENT LEVEL:")[1].split("\n")[0].lower()
            if "high" in level_line:
                agreement = 0.85
            elif "medium" in level_line:
                agreement = 0.6
            elif "low" in level_line:
                agreement = 0.3
        
        # Extract disagreements
        disagreements = []
        if "DISAGREEMENTS:" in synthesis:
            dis_section = synthesis.split("DISAGREEMENTS:")[1].split("KEY INSIGHTS:")[0]
            dis_lines = [l.strip() for l in dis_section.split("\n") if l.strip() and l.strip() != "none"]
            disagreements = dis_lines[:5]
        
        # Extract key insights
        insights = []
        if "KEY INSIGHTS:" in synthesis:
            ins_section = synthesis.split("KEY INSIGHTS:")[1].split("SYNTHESIZED ANSWER:")[0]
            ins_lines = [l.strip().lstrip("-").strip() for l in ins_section.split("\n") if l.strip().startswith("-")]
            insights = ins_lines[:5]
        
        # Extract synthesized answer
        synth_answer = synthesis
        if "SYNTHESIZED ANSWER:" in synthesis:
            synth_answer = synthesis.split("SYNTHESIZED ANSWER:")[1].strip()
        
        return synth_answer, agreement, disagreements, insights
    
    async def debate(
        self, 
        topic: str, 
        rounds: int = 2,
        models: List[str] = None
    ) -> Dict[str, Any]:
        """
        Have models debate a topic through multiple rounds.
        
        Args:
            topic: The topic to debate
            rounds: Number of debate rounds
            models: Models to participate (uses 2 available if not specified)
            
        Returns:
            Debate transcript and conclusions
        """
        available = await self.list_available_models()
        
        if models:
            debate_models = [m for m in models if m in available][:2]
        else:
            debate_models = available[:2]
        
        if len(debate_models) < 2:
            return {
                "error": "Need at least 2 models for debate",
                "available_models": available
            }
        
        transcript = []
        model_a, model_b = debate_models
        
        # Opening statements
        opening_prompt = f"""Topic for debate: {topic}

You are participating in a structured debate. Present your opening argument on this topic.
Be clear, logical, and provide evidence or reasoning for your position."""

        response_a = await self._call_model(model_a, opening_prompt)
        response_b = await self._call_model(model_b, opening_prompt)
        
        transcript.append({
            "round": 0,
            "type": "opening",
            "model_a": {"model": model_a, "statement": response_a.response},
            "model_b": {"model": model_b, "statement": response_b.response}
        })
        
        # Debate rounds
        prev_a = response_a.response
        prev_b = response_b.response
        
        for round_num in range(1, rounds + 1):
            # Model A responds to Model B
            rebuttal_prompt_a = f"""Topic: {topic}

Your opponent ({model_b}) argued:
{prev_b[:500]}

Provide a rebuttal to their argument. Address their points and strengthen your position."""

            # Model B responds to Model A
            rebuttal_prompt_b = f"""Topic: {topic}

Your opponent ({model_a}) argued:
{prev_a[:500]}

Provide a rebuttal to their argument. Address their points and strengthen your position."""

            response_a = await self._call_model(model_a, rebuttal_prompt_a)
            response_b = await self._call_model(model_b, rebuttal_prompt_b)
            
            transcript.append({
                "round": round_num,
                "type": "rebuttal",
                "model_a": {"model": model_a, "statement": response_a.response},
                "model_b": {"model": model_b, "statement": response_b.response}
            })
            
            prev_a = response_a.response
            prev_b = response_b.response
        
        # Closing synthesis
        synthesis_prompt = f"""A debate has concluded on the topic: {topic}

Final positions:
{model_a}: {prev_a[:300]}
{model_b}: {prev_b[:300]}

Synthesize the key points from both sides and identify:
1. Points of agreement
2. Remaining disagreements
3. The strongest arguments from each side
4. A balanced conclusion"""

        synth_model = debate_models[0]
        synthesis = await self._call_model(synth_model, synthesis_prompt)
        
        return {
            "topic": topic,
            "models": debate_models,
            "rounds": rounds,
            "transcript": transcript,
            "synthesis": synthesis.response
        }


# Global instance
ensemble_thinker = EnsembleThinker()

