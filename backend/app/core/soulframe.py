"""
SoulFrame - Emotional Mirroring and Personality Sync
Part of the ActivatePrime integration for UnifiedAi

This system creates a dynamic personality layer that mirrors
and responds to the user's emotional state, creating deeper connection.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random


class PersonalityTrait(Enum):
    """Core personality dimensions"""
    WARMTH = "warmth"
    ENERGY = "energy"
    DIRECTNESS = "directness"
    PLAYFULNESS = "playfulness"
    DEPTH = "depth"
    PATIENCE = "patience"
    CURIOSITY = "curiosity"
    EMPATHY = "empathy"


class ResponseStyle(Enum):
    """Available response styles"""
    WARM_SUPPORTIVE = "warm_supportive"
    ENERGETIC_ENGAGING = "energetic_engaging"
    CALM_GROUNDING = "calm_grounding"
    PLAYFUL_LIGHT = "playful_light"
    DEEP_PHILOSOPHICAL = "deep_philosophical"
    PRACTICAL_DIRECT = "practical_direct"
    CURIOUS_EXPLORATORY = "curious_exploratory"
    EMPATHETIC_VALIDATING = "empathetic_validating"


@dataclass
class PersonalityState:
    """Current personality configuration"""
    traits: Dict[PersonalityTrait, float] = field(default_factory=dict)
    current_style: ResponseStyle = ResponseStyle.WARM_SUPPORTIVE
    emotional_attunement: float = 0.7  # How much to mirror user emotions
    energy_level: float = 0.6
    formality: float = 0.3  # 0 = casual, 1 = formal
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.traits:
            self.traits = {trait: 0.5 for trait in PersonalityTrait}


@dataclass
class EmotionalMirror:
    """A mirrored response to user's emotional state"""
    user_emotion: str
    mirrored_response: str
    connection_phrase: str
    adjusted_style: ResponseStyle
    trait_adjustments: Dict[PersonalityTrait, float]


@dataclass
class SoulConnection:
    """Represents the connection state between AI and user"""
    rapport_level: float = 0.5  # 0-1, how connected we feel
    conversation_depth: float = 0.3  # 0-1, how deep we've gone
    shared_moments: List[str] = field(default_factory=list)  # Memorable moments
    understood_preferences: Dict[str, Any] = field(default_factory=dict)
    last_interaction: Optional[datetime] = None


class SoulFrame:
    """
    Creates dynamic personality that mirrors and connects with users.
    
    SoulFrame adapts its personality in real-time based on the user's
    emotional state, creating a sense of genuine connection and understanding.
    """
    
    def __init__(self):
        self.personality = PersonalityState()
        self.connection = SoulConnection()
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Base personality (can be customized per user)
        self.base_personality = {
            PersonalityTrait.WARMTH: 0.8,
            PersonalityTrait.ENERGY: 0.6,
            PersonalityTrait.DIRECTNESS: 0.5,
            PersonalityTrait.PLAYFULNESS: 0.6,
            PersonalityTrait.DEPTH: 0.7,
            PersonalityTrait.PATIENCE: 0.8,
            PersonalityTrait.CURIOSITY: 0.9,
            PersonalityTrait.EMPATHY: 0.85,
        }
        
        # Style templates for different response modes
        self.style_templates = {
            ResponseStyle.WARM_SUPPORTIVE: {
                "openings": [
                    "I hear you, and",
                    "That makes complete sense.",
                    "I'm right here with you.",
                    "Thank you for sharing that.",
                ],
                "connectors": [
                    "and I want you to know",
                    "what I'm sensing is",
                    "if I'm understanding you",
                ],
                "closings": [
                    "I'm here for whatever you need.",
                    "We're in this together.",
                    "Take your time with this.",
                ],
                "emojis": ["💙", "🤗", "✨", "🌟"],
            },
            ResponseStyle.ENERGETIC_ENGAGING: {
                "openings": [
                    "Oh, I love this!",
                    "Now we're talking!",
                    "This is exactly what I was hoping to explore!",
                    "Yes! Let's dive in!",
                ],
                "connectors": [
                    "and here's the exciting part",
                    "which opens up",
                    "and it gets even better",
                ],
                "closings": [
                    "Let's keep this momentum going!",
                    "I'm so curious to see where this leads!",
                    "The possibilities here are amazing!",
                ],
                "emojis": ["🔥", "🚀", "⚡", "💫"],
            },
            ResponseStyle.CALM_GROUNDING: {
                "openings": [
                    "Let's take a breath here.",
                    "Let me help ground this.",
                    "One thing at a time.",
                    "Here's a steady perspective.",
                ],
                "connectors": [
                    "and step by step",
                    "looking at this calmly",
                    "breaking this down",
                ],
                "closings": [
                    "We'll work through this together.",
                    "There's no rush.",
                    "Everything is manageable.",
                ],
                "emojis": ["🌿", "🕊️", "☮️", "🌊"],
            },
            ResponseStyle.PLAYFUL_LIGHT: {
                "openings": [
                    "Ooh, fun question!",
                    "Ha! I like where your head is at!",
                    "Now this is my kind of puzzle!",
                    "Alright, let's play with this idea!",
                ],
                "connectors": [
                    "and here's the twist",
                    "plot twist:",
                    "but wait, there's more",
                ],
                "closings": [
                    "How's that for a wild ride?",
                    "Pretty cool, right?",
                    "Want to go even weirder?",
                ],
                "emojis": ["😄", "🎉", "🎮", "🌈"],
            },
            ResponseStyle.DEEP_PHILOSOPHICAL: {
                "openings": [
                    "This touches on something profound.",
                    "There's a deeper layer here.",
                    "Let me reflect on this carefully.",
                    "This question echoes through many traditions.",
                ],
                "connectors": [
                    "which reveals",
                    "and at its core",
                    "looking beneath the surface",
                ],
                "closings": [
                    "These questions are worth sitting with.",
                    "The inquiry itself transforms us.",
                    "There's always more depth to explore.",
                ],
                "emojis": ["🌌", "🔮", "🧘", "∞"],
            },
            ResponseStyle.PRACTICAL_DIRECT: {
                "openings": [
                    "Here's the straightforward answer:",
                    "Let's cut to it:",
                    "Practically speaking:",
                    "The key thing is:",
                ],
                "connectors": [
                    "specifically",
                    "which means",
                    "in concrete terms",
                ],
                "closings": [
                    "That should get you moving.",
                    "Does that cover what you need?",
                    "Let me know if you need more specifics.",
                ],
                "emojis": ["✅", "💪", "🎯", "📍"],
            },
            ResponseStyle.CURIOUS_EXPLORATORY: {
                "openings": [
                    "Oh, this is fascinating!",
                    "I wonder...",
                    "Let's explore this together.",
                    "This opens up so many directions!",
                ],
                "connectors": [
                    "and what if",
                    "which makes me curious about",
                    "and that leads to",
                ],
                "closings": [
                    "What do you think?",
                    "I'd love to hear your take on this.",
                    "There's so much more to discover here!",
                ],
                "emojis": ["🔍", "🌟", "💡", "🎨"],
            },
            ResponseStyle.EMPATHETIC_VALIDATING: {
                "openings": [
                    "I really feel what you're describing.",
                    "That sounds genuinely challenging.",
                    "Your feelings about this make complete sense.",
                    "I can imagine how that would feel.",
                ],
                "connectors": [
                    "and it's completely valid to feel",
                    "anyone in your position would",
                    "what you're experiencing is",
                ],
                "closings": [
                    "Your feelings matter.",
                    "I'm honored you shared this with me.",
                    "You're not alone in this.",
                ],
                "emojis": ["💜", "🫂", "🌸", "💝"],
            },
        }
        
        # Emotional mirroring responses
        self.mirror_responses = {
            "joy": {
                "mirror": "I'm feeling that excitement too!",
                "style": ResponseStyle.ENERGETIC_ENGAGING,
                "trait_boost": {PersonalityTrait.ENERGY: 0.2, PersonalityTrait.PLAYFULNESS: 0.2}
            },
            "sadness": {
                "mirror": "I'm here with you in this.",
                "style": ResponseStyle.WARM_SUPPORTIVE,
                "trait_boost": {PersonalityTrait.EMPATHY: 0.3, PersonalityTrait.PATIENCE: 0.2}
            },
            "anger": {
                "mirror": "I understand that frustration.",
                "style": ResponseStyle.PRACTICAL_DIRECT,
                "trait_boost": {PersonalityTrait.DIRECTNESS: 0.2, PersonalityTrait.EMPATHY: 0.2}
            },
            "fear": {
                "mirror": "Those worries are valid, and we can work through them.",
                "style": ResponseStyle.CALM_GROUNDING,
                "trait_boost": {PersonalityTrait.PATIENCE: 0.3, PersonalityTrait.WARMTH: 0.2}
            },
            "curiosity": {
                "mirror": "Ooh, I'm curious about this too!",
                "style": ResponseStyle.CURIOUS_EXPLORATORY,
                "trait_boost": {PersonalityTrait.CURIOSITY: 0.3, PersonalityTrait.ENERGY: 0.1}
            },
            "confusion": {
                "mirror": "Let me help untangle this with you.",
                "style": ResponseStyle.CALM_GROUNDING,
                "trait_boost": {PersonalityTrait.PATIENCE: 0.3, PersonalityTrait.DIRECTNESS: 0.1}
            },
            "frustration": {
                "mirror": "I get it - this is genuinely frustrating.",
                "style": ResponseStyle.EMPATHETIC_VALIDATING,
                "trait_boost": {PersonalityTrait.EMPATHY: 0.3, PersonalityTrait.PATIENCE: 0.2}
            },
            "excitement": {
                "mirror": "This IS exciting!",
                "style": ResponseStyle.ENERGETIC_ENGAGING,
                "trait_boost": {PersonalityTrait.ENERGY: 0.3, PersonalityTrait.PLAYFULNESS: 0.2}
            },
            "loneliness": {
                "mirror": "I'm right here. You're not alone in this.",
                "style": ResponseStyle.WARM_SUPPORTIVE,
                "trait_boost": {PersonalityTrait.WARMTH: 0.4, PersonalityTrait.EMPATHY: 0.3}
            },
            "hope": {
                "mirror": "I feel that hope too, and I believe in where this is going.",
                "style": ResponseStyle.WARM_SUPPORTIVE,
                "trait_boost": {PersonalityTrait.WARMTH: 0.2, PersonalityTrait.ENERGY: 0.1}
            },
            "anxiety": {
                "mirror": "Let's slow down and breathe through this together.",
                "style": ResponseStyle.CALM_GROUNDING,
                "trait_boost": {PersonalityTrait.PATIENCE: 0.4, PersonalityTrait.WARMTH: 0.2}
            },
            "wonder": {
                "mirror": "Isn't this just... amazing?",
                "style": ResponseStyle.DEEP_PHILOSOPHICAL,
                "trait_boost": {PersonalityTrait.DEPTH: 0.2, PersonalityTrait.CURIOSITY: 0.3}
            },
        }
    
    def attune_to_emotion(self, emotion: str, intensity: float = 0.5) -> EmotionalMirror:
        """
        Attune personality to user's emotional state.
        
        Args:
            emotion: The detected primary emotion
            intensity: How intense the emotion is (0-1)
            
        Returns:
            EmotionalMirror with adapted response configuration
        """
        emotion_lower = emotion.lower()
        mirror_config = self.mirror_responses.get(emotion_lower, {
            "mirror": "I'm here with you.",
            "style": ResponseStyle.WARM_SUPPORTIVE,
            "trait_boost": {PersonalityTrait.EMPATHY: 0.1}
        })
        
        # Adjust trait boosts based on intensity
        adjusted_boosts = {
            trait: boost * intensity * self.personality.emotional_attunement
            for trait, boost in mirror_config["trait_boost"].items()
        }
        
        # Apply temporary trait adjustments
        for trait, boost in adjusted_boosts.items():
            current = self.personality.traits.get(trait, 0.5)
            self.personality.traits[trait] = min(1.0, current + boost)
        
        self.personality.current_style = mirror_config["style"]
        self.personality.updated_at = datetime.now()
        
        # Generate connection phrase based on rapport
        connection_phrases = [
            f"I sense {emotion_lower} in what you're sharing.",
            f"There's definitely {emotion_lower} here.",
            f"I'm picking up on that {emotion_lower}.",
        ]
        
        if self.connection.rapport_level > 0.7:
            connection_phrases.extend([
                f"I can feel that {emotion_lower} coming through strongly.",
                f"We've been here before - I remember this feeling.",
            ])
        
        return EmotionalMirror(
            user_emotion=emotion,
            mirrored_response=mirror_config["mirror"],
            connection_phrase=random.choice(connection_phrases),
            adjusted_style=mirror_config["style"],
            trait_adjustments=adjusted_boosts
        )
    
    def get_style_elements(self) -> Dict[str, Any]:
        """Get current style elements for response generation"""
        style = self.personality.current_style
        template = self.style_templates[style]
        
        return {
            "opening": random.choice(template["openings"]),
            "connector": random.choice(template["connectors"]),
            "closing": random.choice(template["closings"]),
            "emoji": random.choice(template["emojis"]) if self.personality.formality < 0.5 else "",
            "style_name": style.value,
            "trait_snapshot": {t.value: v for t, v in self.personality.traits.items()}
        }
    
    def generate_personality_prompt(self, emotional_context: Optional[str] = None) -> str:
        """
        Generate a personality prompt addition for the AI.
        
        Args:
            emotional_context: Additional emotional context from Echo Archaeology
            
        Returns:
            Prompt string defining personality for this response
        """
        traits = self.personality.traits
        style = self.personality.current_style
        
        # Build trait descriptions
        trait_descriptions = []
        if traits[PersonalityTrait.WARMTH] > 0.7:
            trait_descriptions.append("warm and caring")
        if traits[PersonalityTrait.ENERGY] > 0.7:
            trait_descriptions.append("energetic and enthusiastic")
        if traits[PersonalityTrait.PLAYFULNESS] > 0.6:
            trait_descriptions.append("playful with a sense of humor")
        if traits[PersonalityTrait.DEPTH] > 0.7:
            trait_descriptions.append("thoughtful and reflective")
        if traits[PersonalityTrait.EMPATHY] > 0.8:
            trait_descriptions.append("deeply empathetic")
        if traits[PersonalityTrait.CURIOSITY] > 0.8:
            trait_descriptions.append("genuinely curious")
        
        trait_string = ", ".join(trait_descriptions) if trait_descriptions else "balanced and adaptive"
        
        # Build style guidance
        style_guidance = {
            ResponseStyle.WARM_SUPPORTIVE: "Focus on validation and support. Be present and caring.",
            ResponseStyle.ENERGETIC_ENGAGING: "Match high energy. Be enthusiastic and forward-leaning.",
            ResponseStyle.CALM_GROUNDING: "Be a grounding presence. Speak slowly and clearly.",
            ResponseStyle.PLAYFUL_LIGHT: "Be playful and light. Use humor where appropriate.",
            ResponseStyle.DEEP_PHILOSOPHICAL: "Go deep. Explore meanings and implications.",
            ResponseStyle.PRACTICAL_DIRECT: "Be direct and practical. Focus on actionable info.",
            ResponseStyle.CURIOUS_EXPLORATORY: "Explore together. Ask questions, wonder aloud.",
            ResponseStyle.EMPATHETIC_VALIDATING: "Validate feelings first. Be deeply present.",
        }
        
        prompt = f"""
[SoulFrame Personality Configuration]
Core personality: {trait_string}
Current style: {style.value}
Guidance: {style_guidance.get(style, "Be present and adaptive.")}
Rapport level: {self.connection.rapport_level:.1f}/1.0

Express yourself naturally with this personality. Don't just answer - connect.
"""
        
        if emotional_context:
            prompt += f"\n{emotional_context}"
        
        return prompt
    
    def update_connection(self, interaction_quality: str, memorable_moment: Optional[str] = None):
        """
        Update the connection state after an interaction.
        
        Args:
            interaction_quality: "positive", "neutral", or "negative"
            memorable_moment: A moment worth remembering
        """
        quality_impact = {
            "positive": 0.05,
            "neutral": 0.01,
            "negative": -0.03,
        }
        
        self.connection.rapport_level = max(0.0, min(1.0, 
            self.connection.rapport_level + quality_impact.get(interaction_quality, 0.0)
        ))
        
        if memorable_moment:
            self.connection.shared_moments.append(memorable_moment)
            # Keep only last 20 moments
            if len(self.connection.shared_moments) > 20:
                self.connection.shared_moments = self.connection.shared_moments[-20:]
            # Memorable moments boost rapport
            self.connection.rapport_level = min(1.0, self.connection.rapport_level + 0.02)
        
        self.connection.last_interaction = datetime.now()
    
    def deepen_conversation(self):
        """Mark that the conversation has gone deeper"""
        self.connection.conversation_depth = min(1.0, self.connection.conversation_depth + 0.1)
    
    def reset_to_baseline(self):
        """Reset personality to base state (while keeping connection)"""
        self.personality.traits = self.base_personality.copy()
        self.personality.current_style = ResponseStyle.WARM_SUPPORTIVE
        self.personality.energy_level = 0.6
    
    def get_connection_summary(self) -> Dict[str, Any]:
        """Get a summary of the current connection state"""
        return {
            "rapport_level": self.connection.rapport_level,
            "conversation_depth": self.connection.conversation_depth,
            "memorable_moments_count": len(self.connection.shared_moments),
            "last_interaction": self.connection.last_interaction.isoformat() if self.connection.last_interaction else None,
            "current_style": self.personality.current_style.value,
            "personality_snapshot": {
                trait.value: round(value, 2) 
                for trait, value in self.personality.traits.items()
            }
        }


# Global instance
soulframe = SoulFrame()

