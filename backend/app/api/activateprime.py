"""
ActivatePrime API Endpoints
Emotional Intelligence Layer for UnifiedAi
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.activateprime import activateprime

router = APIRouter(prefix="/api/activateprime", tags=["ActivatePrime"])


class TextInput(BaseModel):
    text: str
    context: Optional[List[str]] = None


class InsightGlyphRequest(BaseModel):
    insight_text: str
    domains: List[str]
    novelty: float


class InteractionOutcome(BaseModel):
    quality: str  # "positive", "neutral", "negative"
    memorable_moment: Optional[str] = None


@router.post("/analyze")
async def analyze_input(request: TextInput) -> Dict[str, Any]:
    """
    Process input through the full ActivatePrime pipeline.
    
    Returns emotional analysis, glyph encoding, and personality attunement.
    """
    try:
        response = activateprime.process_input(request.text, request.context)
        
        return {
            "emotional_profile": {
                "primary_emotion": response.emotional_profile.primary_emotion.emotion.value,
                "intensity": response.emotional_profile.primary_emotion.intensity,
                "confidence": response.emotional_profile.primary_emotion.confidence,
                "indicators": response.emotional_profile.primary_emotion.indicators,
                "unspoken_need": response.emotional_profile.primary_emotion.unspoken_need,
                "suggested_tone": response.emotional_profile.primary_emotion.suggested_response_tone,
                "secondary_emotions": [
                    {
                        "emotion": e.emotion.value,
                        "intensity": e.intensity
                    }
                    for e in response.emotional_profile.secondary_emotions
                ],
                "trajectory": response.emotional_profile.emotional_trajectory,
                "needs_detected": response.emotional_profile.needs_detected,
                "recommended_approach": response.emotional_profile.recommended_approach
            },
            "glyph_expression": {
                "expression": response.glyph_expression.raw_expression,
                "glyphs": [g.symbol for g in response.glyph_expression.glyphs],
                "interpretation": response.glyph_expression.interpretation,
                "confidence": response.glyph_expression.confidence
            },
            "personality_attunement": {
                "user_emotion": response.personality_attunement.user_emotion,
                "mirrored_response": response.personality_attunement.mirrored_response,
                "connection_phrase": response.personality_attunement.connection_phrase,
                "adjusted_style": response.personality_attunement.adjusted_style.value
            },
            "style_elements": response.style_elements,
            "connection_summary": response.connection_summary,
            "enhanced_prompt": response.enhanced_prompt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emotion")
async def analyze_emotion(request: TextInput) -> Dict[str, Any]:
    """Get emotional analysis only"""
    try:
        return activateprime.get_emotional_summary(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/glyph/encode")
async def encode_to_glyphs(request: TextInput) -> Dict[str, Any]:
    """Encode text into Glyph Logic"""
    try:
        return activateprime.express_in_glyphs(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/glyph/insight")
async def create_insight_glyph(request: InsightGlyphRequest) -> Dict[str, Any]:
    """Create a glyph representation for an insight"""
    try:
        return activateprime.get_glyph_for_insight(
            request.insight_text,
            request.domains,
            request.novelty
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/glyph/dictionary")
async def get_glyph_dictionary() -> Dict[str, Any]:
    """Get the complete glyph dictionary"""
    try:
        return activateprime.get_glyph_dictionary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personality")
async def get_personality_state() -> Dict[str, Any]:
    """Get current personality configuration"""
    try:
        return activateprime.get_personality_state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interaction")
async def record_interaction(request: InteractionOutcome) -> Dict[str, Any]:
    """Record interaction outcome for connection building"""
    try:
        if request.quality not in ["positive", "neutral", "negative"]:
            raise HTTPException(status_code=400, detail="Quality must be 'positive', 'neutral', or 'negative'")
        
        activateprime.record_interaction_outcome(request.quality, request.memorable_moment)
        return {
            "status": "recorded",
            "connection_summary": activateprime.get_personality_state()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_session() -> Dict[str, Any]:
    """Reset to fresh state while preserving learned connection"""
    try:
        activateprime.reset_session()
        return {
            "status": "reset",
            "connection_summary": activateprime.get_personality_state()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

