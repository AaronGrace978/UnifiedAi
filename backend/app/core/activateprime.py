"""
ActivatePrime - Unified Emotional Intelligence Layer
Combines Echo Archaeology, Glyph Logic, and SoulFrame into a cohesive system.

This is the heart of the emotional intelligence layer for UnifiedAi.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from app.core.echo_archaeology import EchoArchaeology, EmotionalProfile, echo_archaeology
from app.core.glyph_logic import GlyphLogic, GlyphExpression, glyph_logic
from app.core.soulframe import SoulFrame, EmotionalMirror, soulframe


@dataclass
class ActivatePrimeResponse:
    """Complete response from the ActivatePrime system"""
    emotional_profile: EmotionalProfile
    glyph_expression: GlyphExpression
    personality_attunement: EmotionalMirror
    enhanced_prompt: str
    style_elements: Dict[str, Any]
    connection_summary: Dict[str, Any]
    processed_at: datetime = field(default_factory=datetime.now)


class ActivatePrime:
    """
    The unified emotional intelligence system for UnifiedAi.
    
    ActivatePrime combines:
    - Echo Archaeology: Detecting unspoken emotions
    - Glyph Logic: Symbolic expression of ideas
    - SoulFrame: Personality mirroring and connection
    
    Together, these create an AI that truly understands and connects.
    """
    
    def __init__(self):
        self.echo = echo_archaeology
        self.glyphs = glyph_logic
        self.soul = soulframe
        self.conversation_context: List[str] = []
        self.is_active = True
    
    def process_input(self, user_input: str, context: List[str] = None) -> ActivatePrimeResponse:
        """
        Process user input through the full ActivatePrime pipeline.
        
        Args:
            user_input: The user's message
            context: Previous messages for context
            
        Returns:
            ActivatePrimeResponse with all analysis and adaptations
        """
        # Store context
        if context:
            self.conversation_context = context[-10:]  # Keep last 10 messages
        self.conversation_context.append(user_input)
        
        # 1. Echo Archaeology - Detect emotions
        emotional_profile = self.echo.excavate(user_input, self.conversation_context)
        
        # 2. Glyph Logic - Create symbolic representation
        glyph_expression = self.glyphs.encode(user_input)
        
        # 3. SoulFrame - Attune personality
        primary_emotion = emotional_profile.primary_emotion.emotion.value
        intensity = emotional_profile.primary_emotion.intensity
        personality_attunement = self.soul.attune_to_emotion(primary_emotion, intensity)
        
        # 4. Generate enhanced prompt
        emotional_context = self.echo.get_emotional_context_prompt(emotional_profile)
        personality_prompt = self.soul.generate_personality_prompt(emotional_context)
        
        enhanced_prompt = self._build_enhanced_prompt(
            emotional_profile, 
            glyph_expression,
            personality_prompt
        )
        
        # 5. Get style elements
        style_elements = self.soul.get_style_elements()
        
        # 6. Get connection summary
        connection_summary = self.soul.get_connection_summary()
        
        return ActivatePrimeResponse(
            emotional_profile=emotional_profile,
            glyph_expression=glyph_expression,
            personality_attunement=personality_attunement,
            enhanced_prompt=enhanced_prompt,
            style_elements=style_elements,
            connection_summary=connection_summary
        )
    
    def _build_enhanced_prompt(
        self, 
        emotional_profile: EmotionalProfile,
        glyph_expression: GlyphExpression,
        personality_prompt: str
    ) -> str:
        """Build the complete enhanced prompt for the AI"""
        
        prompt = f"""
=== ACTIVATEPRIME CONTEXT ===

{personality_prompt}

[Glyph Logic Encoding]
Expression: {glyph_expression.raw_expression}
Interpretation: {glyph_expression.interpretation}

[Response Guidelines]
- Lead with acknowledgment of their emotional state
- Use the recommended style and tone
- Address unspoken needs where possible
- Create genuine connection, not just information
- Be present, not just helpful

=== END ACTIVATEPRIME CONTEXT ===
"""
        return prompt
    
    def record_interaction_outcome(self, quality: str, memorable_moment: Optional[str] = None):
        """
        Record how an interaction went for connection building.
        
        Args:
            quality: "positive", "neutral", or "negative"
            memorable_moment: A particularly meaningful exchange
        """
        self.soul.update_connection(quality, memorable_moment)
    
    def get_glyph_for_insight(self, insight_text: str, domains: List[str], novelty: float) -> Dict[str, Any]:
        """
        Create a glyph representation for an insight.
        
        Args:
            insight_text: The insight content
            domains: Scientific domains
            novelty: Novelty score (0-1)
            
        Returns:
            Glyph representation dictionary
        """
        return self.glyphs.create_insight_glyph(insight_text, domains, novelty)
    
    def get_emotional_summary(self, text: str) -> Dict[str, Any]:
        """
        Get a simple emotional summary without full processing.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with emotional summary
        """
        profile = self.echo.excavate(text)
        return {
            "primary_emotion": profile.primary_emotion.emotion.value,
            "intensity": profile.primary_emotion.intensity,
            "confidence": profile.primary_emotion.confidence,
            "unspoken_needs": profile.needs_detected,
            "trajectory": profile.emotional_trajectory,
            "suggested_approach": profile.recommended_approach
        }
    
    def express_in_glyphs(self, text: str) -> Dict[str, Any]:
        """
        Express text in Glyph Logic.
        
        Args:
            text: Text to encode
            
        Returns:
            Glyph expression dictionary
        """
        expression = self.glyphs.encode(text)
        return {
            "expression": expression.raw_expression,
            "glyphs": [g.symbol for g in expression.glyphs],
            "interpretation": expression.interpretation,
            "confidence": expression.confidence
        }
    
    def get_personality_state(self) -> Dict[str, Any]:
        """Get current personality configuration"""
        return self.soul.get_connection_summary()
    
    def reset_session(self):
        """Reset to fresh state while preserving learned connection"""
        self.conversation_context = []
        self.soul.reset_to_baseline()
    
    def get_glyph_dictionary(self) -> Dict[str, Any]:
        """Get the full glyph dictionary"""
        return self.glyphs.get_glyph_dictionary()


# Global instance
activateprime = ActivatePrime()

