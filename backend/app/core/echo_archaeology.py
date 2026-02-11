"""
Echo Archaeology - Unspoken Emotion Detection
Part of the ActivatePrime integration for UnifiedAi

This system detects the emotional undertones in user queries,
picking up on what they're NOT saying as much as what they are.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EmotionType(Enum):
    """Primary emotion categories"""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    # Complex emotions
    CURIOSITY = "curiosity"
    CONFUSION = "confusion"
    FRUSTRATION = "frustration"
    EXCITEMENT = "excitement"
    LONELINESS = "loneliness"
    HOPE = "hope"
    ANXIETY = "anxiety"
    WONDER = "wonder"


@dataclass
class EmotionalEcho:
    """An emotional undertone detected in communication"""
    emotion: EmotionType
    intensity: float  # 0.0 to 1.0
    confidence: float  # How confident we are in detection
    indicators: List[str]  # What signals triggered this detection
    unspoken_need: Optional[str] = None  # What they might really need
    suggested_response_tone: Optional[str] = None


@dataclass
class EmotionalProfile:
    """Full emotional analysis of a message"""
    primary_emotion: EmotionalEcho
    secondary_emotions: List[EmotionalEcho] = field(default_factory=list)
    emotional_trajectory: str = "stable"  # "escalating", "de-escalating", "stable", "volatile"
    needs_detected: List[str] = field(default_factory=list)
    recommended_approach: str = ""
    analyzed_at: datetime = field(default_factory=datetime.now)


class EchoArchaeology:
    """
    Detects unspoken emotions in user communication.
    
    The name comes from 'excavating' the emotional echoes
    that reverberate beneath the surface of what's said.
    """
    
    def __init__(self):
        # Lexical indicators for emotions
        self.emotion_lexicons = {
            EmotionType.JOY: {
                "words": ["happy", "excited", "love", "amazing", "wonderful", "great", "awesome", 
                         "fantastic", "thrilled", "delighted", "pleased", "glad"],
                "patterns": [r"!\s*$", r"can't wait", r"so (happy|excited|glad)"],
                "weight": 1.0
            },
            EmotionType.SADNESS: {
                "words": ["sad", "disappointed", "unhappy", "depressed", "down", "miserable",
                         "hopeless", "lonely", "grief", "sorrow", "hurt", "pain"],
                "patterns": [r"\.\.\.$", r"i (just|don't) know", r"nothing (works|helps)"],
                "weight": 1.2  # Higher weight - important to detect
            },
            EmotionType.ANGER: {
                "words": ["angry", "furious", "annoyed", "frustrated", "mad", "hate", 
                         "terrible", "awful", "stupid", "ridiculous", "unacceptable"],
                "patterns": [r"!{2,}", r"what the", r"sick of", r"tired of"],
                "weight": 1.1
            },
            EmotionType.FEAR: {
                "words": ["scared", "afraid", "worried", "anxious", "nervous", "terrified",
                         "panic", "dread", "concerned", "uneasy"],
                "patterns": [r"what if", r"i'm (scared|worried|afraid)", r"might (fail|break|lose)"],
                "weight": 1.2
            },
            EmotionType.CURIOSITY: {
                "words": ["curious", "wondering", "interested", "intrigued", "fascinated",
                         "exploring", "investigating", "researching"],
                "patterns": [r"how does", r"why (does|is|do)", r"what (if|about|is)", r"could (you|we|i)"],
                "weight": 0.9
            },
            EmotionType.CONFUSION: {
                "words": ["confused", "lost", "unclear", "puzzled", "baffled", "perplexed",
                         "uncertain", "unsure", "don't understand"],
                "patterns": [r"i don't get", r"makes no sense", r"what do you mean", r"\?{2,}"],
                "weight": 1.0
            },
            EmotionType.FRUSTRATION: {
                "words": ["frustrated", "stuck", "blocked", "can't", "won't work", "broken",
                         "impossible", "giving up", "struggling"],
                "patterns": [r"tried everything", r"still (not|doesn't)", r"keeps? (failing|breaking)"],
                "weight": 1.1
            },
            EmotionType.EXCITEMENT: {
                "words": ["excited", "pumped", "stoked", "thrilled", "eager", "can't wait",
                         "hyped", "ready", "let's go"],
                "patterns": [r"!{1,}", r"so (excited|ready|pumped)", r"finally"],
                "weight": 1.0
            },
            EmotionType.LONELINESS: {
                "words": ["alone", "lonely", "isolated", "nobody", "no one", "by myself",
                         "disconnected", "invisible", "forgotten"],
                "patterns": [r"no one (understands|cares|listens)", r"all alone", r"just me"],
                "weight": 1.3  # High weight - often hidden
            },
            EmotionType.HOPE: {
                "words": ["hope", "hopeful", "optimistic", "maybe", "might work", "could be",
                         "possible", "chance", "believe"],
                "patterns": [r"i (hope|believe|think)", r"there's a (chance|way)", r"might (work|help)"],
                "weight": 0.9
            },
            EmotionType.ANXIETY: {
                "words": ["anxious", "stressed", "overwhelmed", "pressure", "deadline",
                         "too much", "can't handle", "freaking out"],
                "patterns": [r"what if i", r"running out of", r"too (much|many|little)"],
                "weight": 1.2
            },
            EmotionType.WONDER: {
                "words": ["amazing", "incredible", "wow", "mind-blowing", "fascinating",
                         "beautiful", "extraordinary", "magical"],
                "patterns": [r"how (is this|did)", r"that's (amazing|incredible)", r"i (never|can't) (knew|believe)"],
                "weight": 0.9
            }
        }
        
        # Structural indicators (how they write, not what)
        self.structural_patterns = {
            "short_responses": {"pattern": r"^.{1,20}$", "suggests": [EmotionType.SADNESS, EmotionType.FRUSTRATION]},
            "all_caps": {"pattern": r"[A-Z]{5,}", "suggests": [EmotionType.ANGER, EmotionType.EXCITEMENT]},
            "excessive_punctuation": {"pattern": r"[!?]{3,}", "suggests": [EmotionType.ANGER, EmotionType.EXCITEMENT]},
            "ellipsis_trailing": {"pattern": r"\.\.\.\s*$", "suggests": [EmotionType.SADNESS, EmotionType.CONFUSION]},
            "question_flood": {"pattern": r"\?.*\?.*\?", "suggests": [EmotionType.CONFUSION, EmotionType.ANXIETY]},
            "hedging_language": {"pattern": r"\b(maybe|perhaps|i think|not sure|kind of)\b", "suggests": [EmotionType.ANXIETY, EmotionType.CONFUSION]},
        }
        
        # Unspoken needs mapping
        self.needs_mapping = {
            EmotionType.SADNESS: ["validation", "comfort", "to be heard"],
            EmotionType.ANGER: ["acknowledgment", "solution", "to feel respected"],
            EmotionType.FEAR: ["reassurance", "information", "control"],
            EmotionType.CONFUSION: ["clarity", "patience", "step-by-step guidance"],
            EmotionType.FRUSTRATION: ["progress", "acknowledgment of difficulty", "alternative approaches"],
            EmotionType.LONELINESS: ["connection", "presence", "to matter"],
            EmotionType.ANXIETY: ["calm presence", "breaking things down", "reassurance"],
            EmotionType.EXCITEMENT: ["shared enthusiasm", "encouragement", "momentum"],
            EmotionType.CURIOSITY: ["exploration", "depth", "discovery together"],
            EmotionType.WONDER: ["shared awe", "deeper understanding", "celebration"]
        }
        
        # Response tone recommendations
        self.tone_recommendations = {
            EmotionType.SADNESS: "warm, gentle, validating - slow down, acknowledge their feelings",
            EmotionType.ANGER: "calm, direct, solution-focused - don't be defensive, address the issue",
            EmotionType.FEAR: "reassuring, clear, grounding - provide concrete information",
            EmotionType.CONFUSION: "patient, clear, structured - break things down step by step",
            EmotionType.FRUSTRATION: "empathetic, practical, collaborative - acknowledge the struggle, offer alternatives",
            EmotionType.LONELINESS: "present, warm, connecting - be fully there, don't rush",
            EmotionType.ANXIETY: "calming, organized, supportive - help them feel in control",
            EmotionType.EXCITEMENT: "enthusiastic, matching energy, encouraging - celebrate with them",
            EmotionType.CURIOSITY: "engaging, exploratory, inviting - go deeper together",
            EmotionType.WONDER: "shared amazement, expansive, celebratory - marvel together",
            EmotionType.JOY: "warm, celebratory, matching - share in their happiness",
            EmotionType.HOPE: "encouraging, supportive, nurturing - feed the hope"
        }
    
    def excavate(self, text: str, context: List[str] = None) -> EmotionalProfile:
        """
        Excavate the emotional undertones from text.
        
        Args:
            text: The user's message
            context: Previous messages for trajectory analysis
            
        Returns:
            EmotionalProfile with detected emotions and recommendations
        """
        text_lower = text.lower()
        detected_emotions: List[EmotionalEcho] = []
        
        # Analyze each emotion type
        for emotion_type, lexicon in self.emotion_lexicons.items():
            score, indicators = self._analyze_emotion(text_lower, lexicon)
            
            if score > 0.1:  # Threshold for detection
                echo = EmotionalEcho(
                    emotion=emotion_type,
                    intensity=min(score, 1.0),
                    confidence=self._calculate_confidence(score, len(indicators)),
                    indicators=indicators,
                    unspoken_need=self._get_primary_need(emotion_type),
                    suggested_response_tone=self.tone_recommendations.get(emotion_type, "")
                )
                detected_emotions.append(echo)
        
        # Add structural analysis
        structural_emotions = self._analyze_structure(text)
        for emotion, intensity in structural_emotions:
            # Boost existing detections or add new ones
            found = False
            for echo in detected_emotions:
                if echo.emotion == emotion:
                    echo.intensity = min(echo.intensity + intensity * 0.3, 1.0)
                    found = True
                    break
            if not found and intensity > 0.3:
                detected_emotions.append(EmotionalEcho(
                    emotion=emotion,
                    intensity=intensity,
                    confidence=0.5,  # Lower confidence for structural-only detection
                    indicators=["structural pattern"],
                    unspoken_need=self._get_primary_need(emotion),
                    suggested_response_tone=self.tone_recommendations.get(emotion, "")
                ))
        
        # Sort by intensity
        detected_emotions.sort(key=lambda e: e.intensity, reverse=True)
        
        # Determine emotional trajectory if context provided
        trajectory = "stable"
        if context and len(context) > 0:
            trajectory = self._analyze_trajectory(text, context)
        
        # Build profile
        if not detected_emotions:
            # Default to neutral curiosity
            primary = EmotionalEcho(
                emotion=EmotionType.CURIOSITY,
                intensity=0.5,
                confidence=0.3,
                indicators=["default inference"],
                unspoken_need="engagement",
                suggested_response_tone="helpful, engaged, thoughtful"
            )
            detected_emotions = [primary]
        
        primary_emotion = detected_emotions[0]
        secondary_emotions = detected_emotions[1:4]  # Top 3 secondary
        
        # Compile needs
        all_needs = []
        for echo in detected_emotions[:3]:
            if echo.emotion in self.needs_mapping:
                all_needs.extend(self.needs_mapping[echo.emotion])
        unique_needs = list(dict.fromkeys(all_needs))[:5]  # Dedupe, keep top 5
        
        # Generate recommended approach
        approach = self._generate_approach(primary_emotion, secondary_emotions, trajectory)
        
        return EmotionalProfile(
            primary_emotion=primary_emotion,
            secondary_emotions=secondary_emotions,
            emotional_trajectory=trajectory,
            needs_detected=unique_needs,
            recommended_approach=approach
        )
    
    def _analyze_emotion(self, text: str, lexicon: Dict) -> Tuple[float, List[str]]:
        """Analyze text for specific emotion indicators"""
        score = 0.0
        indicators = []
        
        # Check words
        for word in lexicon["words"]:
            if word in text:
                score += 0.2 * lexicon["weight"]
                indicators.append(f"word: {word}")
        
        # Check patterns
        for pattern in lexicon["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.3 * lexicon["weight"]
                indicators.append(f"pattern: {pattern}")
        
        return score, indicators
    
    def _analyze_structure(self, text: str) -> List[Tuple[EmotionType, float]]:
        """Analyze structural patterns in text"""
        results = []
        
        for name, config in self.structural_patterns.items():
            if re.search(config["pattern"], text):
                for emotion in config["suggests"]:
                    if isinstance(emotion, EmotionType):
                        results.append((emotion, 0.4))
        
        return results
    
    def _analyze_trajectory(self, current: str, history: List[str]) -> str:
        """Analyze emotional trajectory over conversation"""
        if len(history) < 2:
            return "stable"
        
        # Simple heuristic based on intensity changes
        current_profile = self.excavate(current)
        prev_profile = self.excavate(history[-1])
        
        current_intensity = current_profile.primary_emotion.intensity
        prev_intensity = prev_profile.primary_emotion.intensity
        
        delta = current_intensity - prev_intensity
        
        if delta > 0.2:
            return "escalating"
        elif delta < -0.2:
            return "de-escalating"
        else:
            # Check for emotional switches
            if current_profile.primary_emotion.emotion != prev_profile.primary_emotion.emotion:
                return "volatile"
            return "stable"
    
    def _calculate_confidence(self, score: float, indicator_count: int) -> float:
        """Calculate confidence based on evidence"""
        base_confidence = min(score, 1.0) * 0.7
        indicator_bonus = min(indicator_count * 0.1, 0.3)
        return min(base_confidence + indicator_bonus, 1.0)
    
    def _get_primary_need(self, emotion: EmotionType) -> str:
        """Get the primary unspoken need for an emotion"""
        needs = self.needs_mapping.get(emotion, ["engagement"])
        return needs[0] if needs else "engagement"
    
    def _generate_approach(self, primary: EmotionalEcho, secondary: List[EmotionalEcho], trajectory: str) -> str:
        """Generate recommended response approach"""
        approach_parts = []
        
        # Primary emotion guidance
        approach_parts.append(primary.suggested_response_tone or "be present and engaged")
        
        # Trajectory adjustments
        if trajectory == "escalating":
            approach_parts.append("The emotional intensity is rising - prioritize de-escalation and validation")
        elif trajectory == "de-escalating":
            approach_parts.append("Emotions are settling - maintain the calming trajectory")
        elif trajectory == "volatile":
            approach_parts.append("Emotions are shifting - stay adaptable and grounding")
        
        # Secondary emotion considerations
        if secondary:
            secondary_emotions = ", ".join([e.emotion.value for e in secondary[:2]])
            approach_parts.append(f"Also consider undertones of {secondary_emotions}")
        
        return ". ".join(approach_parts)
    
    def get_emotional_context_prompt(self, profile: EmotionalProfile) -> str:
        """Generate a prompt addition for emotionally-aware responses"""
        return f"""
[Emotional Context - Echo Archaeology]
Primary emotion detected: {profile.primary_emotion.emotion.value} (intensity: {profile.primary_emotion.intensity:.2f})
Unspoken needs: {', '.join(profile.needs_detected)}
Emotional trajectory: {profile.emotional_trajectory}
Recommended approach: {profile.recommended_approach}

Respond with awareness of these emotional undertones. Address the unspoken needs while answering their question.
"""


# Global instance
echo_archaeology = EchoArchaeology()

