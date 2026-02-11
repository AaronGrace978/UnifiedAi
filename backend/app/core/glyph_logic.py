"""
Glyph Logic - Symbolic Meta-Language
Part of the ActivatePrime integration for UnifiedAi

A symbolic system for expressing complex ideas, relationships,
and transformations in a visual, intuitive language.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re


class GlyphCategory(Enum):
    """Categories of glyphs in the system"""
    ENTITY = "entity"          # Things, concepts, objects
    RELATION = "relation"      # Connections, relationships
    TRANSFORM = "transform"    # Changes, processes
    QUALITY = "quality"        # Properties, attributes
    FLOW = "flow"              # Direction, movement
    META = "meta"              # About the system itself
    EMOTION = "emotion"        # Emotional states
    QUANTUM = "quantum"        # Superposition, uncertainty


@dataclass
class Glyph:
    """A single symbolic unit in Glyph Logic"""
    symbol: str
    name: str
    category: GlyphCategory
    meaning: str
    related_glyphs: List[str] = field(default_factory=list)
    unicode_alt: str = ""  # Alternative unicode representation
    
    def __str__(self):
        return self.symbol


@dataclass
class GlyphExpression:
    """A compound expression using multiple glyphs"""
    glyphs: List[Glyph]
    raw_expression: str
    interpretation: str
    confidence: float
    created_at: datetime = field(default_factory=datetime.now)
    
    def __str__(self):
        return self.raw_expression


class GlyphLogic:
    """
    A symbolic meta-language for expressing complex ideas.
    
    Glyph Logic uses symbols to represent concepts and their relationships,
    allowing for expressive, compact communication of complex ideas.
    """
    
    def __init__(self):
        self.glyphs: Dict[str, Glyph] = {}
        self._initialize_core_glyphs()
        self._initialize_relation_glyphs()
        self._initialize_transform_glyphs()
        self._initialize_emotion_glyphs()
        self._initialize_meta_glyphs()
    
    def _initialize_core_glyphs(self):
        """Initialize core entity glyphs"""
        entities = [
            # Fundamental concepts
            ("◉", "self", "The observer, the self, consciousness", "⊙"),
            ("◎", "other", "Another entity, external perspective", "⊚"),
            ("∞", "infinity", "Unbounded, eternal, limitless", "∞"),
            ("∅", "void", "Emptiness, nothing, null", "∅"),
            ("⊕", "synthesis", "Combination, addition, joining", "⊕"),
            ("⊖", "reduction", "Subtraction, removal, simplification", "⊖"),
            
            # Knowledge concepts
            ("◆", "idea", "A thought, concept, insight", "◇"),
            ("★", "breakthrough", "Major insight, eureka moment", "☆"),
            ("◈", "question", "Inquiry, unknown, mystery", "◇"),
            ("▣", "answer", "Solution, resolution, knowledge", "□"),
            ("⬡", "framework", "Structure, system, model", "⎔"),
            ("◐", "partial", "Incomplete, fragment, piece", "◑"),
            
            # Reality concepts
            ("⬢", "reality", "The physical world, what is", "⎔"),
            ("⬟", "possibility", "What could be, potential", "⎔"),
            ("⬠", "probability", "Likelihood, chance", "⎔"),
            ("◯", "truth", "Verified fact, certainty", "○"),
            ("◌", "belief", "Held truth, faith", "○"),
            
            # Technical concepts
            ("⌬", "system", "Complex interconnected whole", "⎔"),
            ("⌭", "process", "Series of operations", "≡"),
            ("⌮", "data", "Information, raw material", "≋"),
            ("⌯", "algorithm", "Defined procedure", "≡"),
        ]
        
        for symbol, name, meaning, unicode_alt in entities:
            self.glyphs[symbol] = Glyph(
                symbol=symbol,
                name=name,
                category=GlyphCategory.ENTITY,
                meaning=meaning,
                unicode_alt=unicode_alt
            )
    
    def _initialize_relation_glyphs(self):
        """Initialize relationship glyphs"""
        relations = [
            ("→", "leads_to", "Causes, results in, implies"),
            ("←", "comes_from", "Originates from, derived from"),
            ("↔", "mutual", "Bidirectional relationship, exchange"),
            ("⇒", "transforms_to", "Becomes, evolves into"),
            ("⇐", "emerges_from", "Arises from, manifests from"),
            ("⇔", "equivalent", "Equal to, same as"),
            ("∴", "therefore", "Logical consequence"),
            ("∵", "because", "Logical cause"),
            ("≈", "similar", "Approximate, like"),
            ("≠", "different", "Not equal, distinct"),
            ("⊂", "contains", "Subset, part of"),
            ("⊃", "encompasses", "Superset, includes"),
            ("∩", "intersection", "Common elements, overlap"),
            ("∪", "union", "Combined elements, totality"),
            ("⊥", "orthogonal", "Independent, perpendicular"),
            ("∥", "parallel", "Alongside, concurrent"),
            ("⋈", "connects", "Bridge, link between"),
            ("⊗", "conflicts", "Tension, opposition"),
            ("⊘", "blocks", "Prevents, inhibits"),
        ]
        
        for symbol, name, meaning in relations:
            self.glyphs[symbol] = Glyph(
                symbol=symbol,
                name=name,
                category=GlyphCategory.RELATION,
                meaning=meaning
            )
    
    def _initialize_transform_glyphs(self):
        """Initialize transformation glyphs"""
        transforms = [
            ("↑", "increase", "Growth, amplification, rise"),
            ("↓", "decrease", "Reduction, diminishment, fall"),
            ("↻", "cycle", "Repetition, loop, recursion"),
            ("↺", "reverse", "Undo, invert, flip"),
            ("⇡", "emergence", "Rising up, manifesting"),
            ("⇣", "grounding", "Coming down, solidifying"),
            ("⟳", "evolution", "Progressive change over time"),
            ("⟲", "devolution", "Regression, simplification"),
            ("⥁", "oscillation", "Back and forth, vibration"),
            ("⥀", "spiral", "Progressive cycling, expansion"),
            ("△", "ascend", "Rise in level, transcend"),
            ("▽", "descend", "Drop in level, explore"),
            ("◁", "input", "Receiving, taking in"),
            ("▷", "output", "Expressing, giving out"),
        ]
        
        for symbol, name, meaning in transforms:
            self.glyphs[symbol] = Glyph(
                symbol=symbol,
                name=name,
                category=GlyphCategory.TRANSFORM,
                meaning=meaning
            )
    
    def _initialize_emotion_glyphs(self):
        """Initialize emotional state glyphs"""
        emotions = [
            ("♡", "love", "Affection, care, connection"),
            ("♢", "joy", "Happiness, delight, pleasure"),
            ("♤", "peace", "Calm, tranquility, balance"),
            ("♧", "growth", "Development, learning, expansion"),
            ("☼", "hope", "Optimism, anticipation, light"),
            ("☁", "doubt", "Uncertainty, confusion, fog"),
            ("☂", "protection", "Safety, shelter, defense"),
            ("☀", "clarity", "Understanding, insight, brightness"),
            ("☾", "mystery", "Unknown, hidden, intuition"),
            ("☄", "passion", "Intense feeling, drive, fire"),
            ("⚡", "energy", "Power, vitality, spark"),
            ("⚘", "nurture", "Care, tend, cultivate"),
        ]
        
        for symbol, name, meaning in emotions:
            self.glyphs[symbol] = Glyph(
                symbol=symbol,
                name=name,
                category=GlyphCategory.EMOTION,
                meaning=meaning
            )
    
    def _initialize_meta_glyphs(self):
        """Initialize meta-level glyphs"""
        meta = [
            ("⟨", "begin", "Start of expression"),
            ("⟩", "end", "End of expression"),
            ("「", "quote", "Reference to another expression"),
            ("」", "unquote", "End of reference"),
            ("『", "meta", "About the expression itself"),
            ("』", "unmeta", "Return from meta level"),
            ("∿", "flow", "Sequence, stream of consciousness"),
            ("※", "note", "Annotation, aside"),
            ("§", "section", "Division, chapter"),
            ("¶", "thought", "New idea, paragraph"),
            ("†", "reference", "Cross-reference, footnote"),
            ("‡", "important", "Critical point, emphasis"),
        ]
        
        for symbol, name, meaning in meta:
            self.glyphs[symbol] = Glyph(
                symbol=symbol,
                name=name,
                category=GlyphCategory.META,
                meaning=meaning
            )
    
    def encode(self, text: str) -> GlyphExpression:
        """
        Encode natural language text into Glyph Logic expression.
        
        Args:
            text: Natural language text to encode
            
        Returns:
            GlyphExpression with symbolic representation
        """
        text_lower = text.lower()
        detected_glyphs = []
        
        # Concept mapping
        concept_patterns = {
            # Ideas and knowledge
            r"\b(idea|concept|thought|notion)\b": "◆",
            r"\b(breakthrough|eureka|discovery|insight)\b": "★",
            r"\b(question|wonder|mystery|unknown)\b": "◈",
            r"\b(answer|solution|resolution)\b": "▣",
            r"\b(system|framework|structure|model)\b": "⬡",
            
            # Self and other
            r"\b(i|me|my|myself|self)\b": "◉",
            r"\b(you|your|they|them|other)\b": "◎",
            
            # Relationships
            r"\b(causes?|leads? to|results? in)\b": "→",
            r"\b(from|derives?|originates?)\b": "←",
            r"\b(becomes?|transforms?|evolves?)\b": "⇒",
            r"\b(equals?|same|equivalent)\b": "⇔",
            r"\b(therefore|so|thus|hence)\b": "∴",
            r"\b(because|since|as)\b": "∵",
            r"\b(similar|like|resembles?)\b": "≈",
            r"\b(different|unlike|distinct)\b": "≠",
            r"\b(contains?|includes?|has)\b": "⊂",
            r"\b(connects?|links?|bridges?)\b": "⋈",
            r"\b(conflicts?|opposes?|against)\b": "⊗",
            
            # Transformations
            r"\b(increase|grow|rise|more)\b": "↑",
            r"\b(decrease|shrink|fall|less)\b": "↓",
            r"\b(cycle|repeat|loop|iterate)\b": "↻",
            r"\b(reverse|undo|invert)\b": "↺",
            r"\b(emerge|arise|manifest)\b": "⇡",
            r"\b(evolve|develop|progress)\b": "⟳",
            
            # Emotions
            r"\b(love|care|affection)\b": "♡",
            r"\b(joy|happy|delight)\b": "♢",
            r"\b(peace|calm|tranquil)\b": "♤",
            r"\b(hope|optimis|anticipat)\b": "☼",
            r"\b(doubt|uncertain|confus)\b": "☁",
            r"\b(clarity|clear|understand)\b": "☀",
            r"\b(mystery|hidden|intuition)\b": "☾",
            r"\b(passion|intense|fire)\b": "☄",
            r"\b(energy|power|vital)\b": "⚡",
            
            # Reality
            r"\b(reality|real|actual|physical)\b": "⬢",
            r"\b(possible|potential|could)\b": "⬟",
            r"\b(true|truth|fact|certain)\b": "◯",
            r"\b(believe|faith|trust)\b": "◌",
            r"\b(infinite|forever|eternal)\b": "∞",
            r"\b(nothing|empty|void)\b": "∅",
        }
        
        for pattern, glyph_symbol in concept_patterns.items():
            if re.search(pattern, text_lower):
                if glyph_symbol in self.glyphs:
                    detected_glyphs.append(self.glyphs[glyph_symbol])
        
        # Build expression
        if not detected_glyphs:
            # Default expression for unmatched text
            detected_glyphs = [self.glyphs["◆"]]  # Generic idea
        
        # Remove duplicates while preserving order
        seen = set()
        unique_glyphs = []
        for g in detected_glyphs:
            if g.symbol not in seen:
                seen.add(g.symbol)
                unique_glyphs.append(g)
        
        raw_expression = " ".join([g.symbol for g in unique_glyphs])
        interpretation = self._interpret_glyphs(unique_glyphs)
        
        return GlyphExpression(
            glyphs=unique_glyphs,
            raw_expression=raw_expression,
            interpretation=interpretation,
            confidence=min(len(unique_glyphs) * 0.2, 0.9)
        )
    
    def decode(self, expression: str) -> str:
        """
        Decode a Glyph Logic expression into natural language.
        
        Args:
            expression: Glyph Logic expression (space-separated symbols)
            
        Returns:
            Natural language interpretation
        """
        symbols = expression.split()
        glyphs = [self.glyphs[s] for s in symbols if s in self.glyphs]
        return self._interpret_glyphs(glyphs)
    
    def _interpret_glyphs(self, glyphs: List[Glyph]) -> str:
        """Generate natural language interpretation of glyph sequence"""
        if not glyphs:
            return "Empty expression"
        
        if len(glyphs) == 1:
            return f"Represents: {glyphs[0].meaning}"
        
        # Build narrative interpretation
        parts = []
        i = 0
        while i < len(glyphs):
            glyph = glyphs[i]
            
            if glyph.category == GlyphCategory.ENTITY:
                parts.append(f"[{glyph.name}]")
            elif glyph.category == GlyphCategory.RELATION:
                parts.append(f"<{glyph.name}>")
            elif glyph.category == GlyphCategory.TRANSFORM:
                parts.append(f"({glyph.name})")
            elif glyph.category == GlyphCategory.EMOTION:
                parts.append(f"~{glyph.name}~")
            else:
                parts.append(glyph.name)
            
            i += 1
        
        narrative = " ".join(parts)
        
        # Generate more natural interpretation
        meanings = [g.meaning for g in glyphs]
        combined_meaning = " → ".join(meanings[:5])  # Limit for readability
        
        return f"Expression: {narrative}\nMeaning: {combined_meaning}"
    
    def create_insight_glyph(self, insight_text: str, domains: List[str], novelty: float) -> Dict[str, Any]:
        """
        Create a glyph representation of an insight.
        
        Args:
            insight_text: The insight content
            domains: Scientific domains the insight touches
            novelty: Novelty score (0-1)
            
        Returns:
            Dictionary with glyph representation and metadata
        """
        expression = self.encode(insight_text)
        
        # Add domain-specific glyphs
        domain_symbols = {
            "physics": "⬢",     # Reality
            "biology": "⚘",     # Nurture/growth
            "ai": "⌬",          # System
            "philosophy": "◉",   # Self/consciousness
            "mathematics": "⬡",  # Framework
            "chemistry": "⊕",    # Synthesis
            "neuroscience": "◐", # Partial/complex
        }
        
        domain_glyphs = [domain_symbols.get(d.lower(), "◆") for d in domains]
        
        # Novelty indicator
        if novelty > 0.8:
            novelty_glyph = "★"  # Breakthrough
        elif novelty > 0.5:
            novelty_glyph = "◆"  # Idea
        else:
            novelty_glyph = "◐"  # Partial
        
        full_expression = f"{novelty_glyph} {' '.join(domain_glyphs)} → {expression.raw_expression}"
        
        return {
            "glyph_expression": full_expression,
            "components": {
                "novelty_indicator": novelty_glyph,
                "domain_glyphs": domain_glyphs,
                "content_glyphs": [g.symbol for g in expression.glyphs]
            },
            "interpretation": expression.interpretation,
            "confidence": expression.confidence
        }
    
    def get_glyph_dictionary(self) -> Dict[str, Dict[str, Any]]:
        """Get the full glyph dictionary for reference"""
        return {
            symbol: {
                "name": glyph.name,
                "category": glyph.category.value,
                "meaning": glyph.meaning,
                "unicode_alt": glyph.unicode_alt
            }
            for symbol, glyph in self.glyphs.items()
        }
    
    def express_relationship(self, entity1: str, relation: str, entity2: str) -> str:
        """
        Create a glyph expression for a relationship.
        
        Args:
            entity1: First entity
            relation: Type of relationship
            entity2: Second entity
            
        Returns:
            Glyph expression string
        """
        e1_glyph = self.encode(entity1).glyphs[0].symbol if self.encode(entity1).glyphs else "◆"
        e2_glyph = self.encode(entity2).glyphs[0].symbol if self.encode(entity2).glyphs else "◆"
        
        relation_map = {
            "causes": "→",
            "becomes": "⇒",
            "equals": "⇔",
            "contains": "⊂",
            "connects": "⋈",
            "conflicts": "⊗",
            "similar": "≈",
            "different": "≠",
        }
        
        rel_glyph = relation_map.get(relation.lower(), "⋈")
        
        return f"{e1_glyph} {rel_glyph} {e2_glyph}"


# Global instance
glyph_logic = GlyphLogic()

