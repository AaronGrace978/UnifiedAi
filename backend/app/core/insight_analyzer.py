"""
Insight Analyzer - Categorizes, tags, and connects insights
Part of the enhanced UnifiedAi meta-intelligence system
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

# Try to import semantic search for better connection finding
try:
    from app.core.semantic_search import semantic_search, EMBEDDINGS_AVAILABLE
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False
    semantic_search = None


@dataclass
class InsightConnection:
    """Connection between two insights"""
    insight_id_1: str
    insight_id_2: str
    connection_type: str  # "similar", "opposite", "builds_on", "contradicts", "extends"
    strength: float  # 0.0 to 1.0
    shared_concepts: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class InsightTag:
    """Tag for categorizing insights"""
    name: str
    category: str  # "biology", "physics", "ai", "philosophy", "technology", etc.
    confidence: float = 0.5


@dataclass
class AnalyzedInsight:
    """Enhanced insight with analysis"""
    original_insight: Dict[str, Any]
    tags: List[InsightTag] = field(default_factory=list)
    key_concepts: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)  # Fields this connects
    novelty_score: float = 0.5  # How novel/unique this insight is
    testability: float = 0.5  # How testable/actionable
    connections: List[InsightConnection] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.now)


class InsightAnalyzer:
    """
    Analyzes insights to:
    - Extract key concepts and domains
    - Tag and categorize
    - Find connections between insights
    - Assess novelty and testability
    """
    
    def __init__(self):
        self.domain_keywords = {
            "biology": ["biological", "organism", "cell", "DNA", "evolution", "neural", "synapse", "protein", "genetic", "species"],
            "physics": ["quantum", "particle", "energy", "wave", "field", "entropy", "thermodynamic", "relativity", "spacetime"],
            "ai": ["neural network", "machine learning", "algorithm", "model", "training", "intelligence", "computation"],
            "philosophy": ["consciousness", "mind", "reality", "existence", "meaning", "truth", "knowledge", "perception"],
            "technology": ["system", "architecture", "design", "implementation", "breakthrough", "innovation"],
            "mathematics": ["equation", "formula", "theorem", "proof", "calculation", "mathematical", "algorithm"],
            "chemistry": ["molecular", "chemical", "reaction", "compound", "element", "bond"],
            "neuroscience": ["brain", "neuron", "synapse", "cognitive", "memory", "learning", "neural"]
        }
        
        self.connection_indicators = {
            "builds_on": ["extends", "builds on", "based on", "follows from", "derived from"],
            "contradicts": ["contradicts", "opposes", "challenges", "refutes", "disagrees with"],
            "similar": ["similar", "like", "analogous", "comparable", "resembles"],
            "extends": ["extends", "expands", "generalizes", "broadens", "deepens"]
        }
    
    def analyze_insight(self, insight: Dict[str, Any]) -> AnalyzedInsight:
        """Analyze a single insight"""
        content = insight.get("content", "").lower()
        
        # Extract domains
        domains = self._extract_domains(content)
        
        # Extract key concepts (capitalized terms, technical terms)
        key_concepts = self._extract_concepts(content)
        
        # Generate tags
        tags = self._generate_tags(content, domains)
        
        # Assess novelty (simple heuristic: length + unique terms)
        novelty_score = self._assess_novelty(content, key_concepts)
        
        # Assess testability (look for testable predictions, experiments)
        testability = self._assess_testability(content)
        
        return AnalyzedInsight(
            original_insight=insight,
            tags=tags,
            key_concepts=key_concepts,
            domains=domains,
            novelty_score=novelty_score,
            testability=testability
        )
    
    def _extract_domains(self, content: str) -> List[str]:
        """Extract which scientific domains this insight connects"""
        domains = []
        for domain, keywords in self.domain_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in content)
            if matches >= 2:  # At least 2 keyword matches
                domains.append(domain)
        return domains
    
    def _extract_concepts(self, content: str) -> List[str]:
        """Extract key concepts from insight"""
        # Look for capitalized terms (likely proper nouns/concepts)
        concepts = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        
        # Also look for quoted terms
        quoted = re.findall(r'"([^"]+)"', content)
        concepts.extend(quoted)
        
        # Technical terms (common patterns)
        technical = re.findall(r'\b(?:quantum|neural|algorithm|system|mechanism|principle|theory|model|framework)\b', content, re.IGNORECASE)
        concepts.extend(technical)
        
        # Remove duplicates and common words
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        concepts = [c for c in concepts if c.lower() not in common_words and len(c) > 2]
        
        return list(set(concepts))[:10]  # Top 10 unique concepts
    
    def _generate_tags(self, content: str, domains: List[str]) -> List[InsightTag]:
        """Generate tags for the insight"""
        tags = []
        
        # Domain tags
        for domain in domains:
            tags.append(InsightTag(name=domain, category="domain", confidence=0.8))
        
        # Type tags
        if "breakthrough" in content or "revolutionary" in content:
            tags.append(InsightTag(name="breakthrough", category="type", confidence=0.7))
        
        if "novel" in content or "new" in content or "unexpected" in content:
            tags.append(InsightTag(name="novel", category="type", confidence=0.6))
        
        if "testable" in content or "experiment" in content or "prediction" in content:
            tags.append(InsightTag(name="testable", category="type", confidence=0.7))
        
        if "connection" in content or "link" in content or "bridge" in content:
            tags.append(InsightTag(name="cross-domain", category="type", confidence=0.6))
        
        return tags
    
    def _assess_novelty(self, content: str, concepts: List[str]) -> float:
        """Assess how novel/unique this insight is"""
        # Longer insights with more unique concepts tend to be more novel
        length_score = min(len(content) / 1000, 1.0)  # Normalize to 0-1
        concept_score = min(len(concepts) / 10, 1.0)
        
        # Check for novelty indicators
        novelty_words = ["novel", "unexpected", "surprising", "breakthrough", "revolutionary", "new", "first", "never"]
        novelty_indicators = sum(1 for word in novelty_words if word in content)
        indicator_score = min(novelty_indicators / 3, 1.0)
        
        return (length_score * 0.3 + concept_score * 0.3 + indicator_score * 0.4)
    
    def _assess_testability(self, content: str) -> float:
        """Assess how testable/actionable this insight is"""
        testable_indicators = [
            "testable", "experiment", "prediction", "hypothesis", "test", "verify",
            "validate", "measure", "observe", "design", "implement", "build"
        ]
        
        matches = sum(1 for indicator in testable_indicators if indicator in content)
        return min(matches / 5, 1.0)  # Normalize to 0-1
    
    def find_connections(self, insight1: AnalyzedInsight, insight2: AnalyzedInsight) -> Optional[InsightConnection]:
        """Find connections between two insights"""
        # Check shared concepts
        shared = set(insight1.key_concepts) & set(insight2.key_concepts)
        shared_domains = set(insight1.domains) & set(insight2.domains)
        
        if not shared and not shared_domains:
            return None
        
        # Calculate connection strength
        concept_overlap = len(shared) / max(len(insight1.key_concepts), len(insight2.key_concepts), 1)
        domain_overlap = len(shared_domains) / max(len(insight1.domains), len(insight2.domains), 1)
        strength = (concept_overlap * 0.6 + domain_overlap * 0.4)
        
        # Determine connection type (simple heuristic)
        content1 = insight1.original_insight.get("content", "").lower()
        content2 = insight2.original_insight.get("content", "").lower()
        
        connection_type = "similar"  # Default
        for conn_type, indicators in self.connection_indicators.items():
            if any(indicator in content1 or indicator in content2 for indicator in indicators):
                connection_type = conn_type
                break
        
        return InsightConnection(
            insight_id_1=insight1.original_insight.get("id", ""),
            insight_id_2=insight2.original_insight.get("id", ""),
            connection_type=connection_type,
            strength=strength,
            shared_concepts=list(shared)
        )
    
    def analyze_insight_batch(self, insights: List[Dict[str, Any]]) -> List[AnalyzedInsight]:
        """Analyze a batch of insights and find connections"""
        analyzed = [self.analyze_insight(insight) for insight in insights]
        
        # Find connections between insights
        for i, insight1 in enumerate(analyzed):
            for insight2 in analyzed[i+1:]:
                connection = self.find_connections(insight1, insight2)
                if connection and connection.strength > 0.2:  # Threshold
                    insight1.connections.append(connection)
                    insight2.connections.append(connection)
        
        return analyzed
    
    def generate_knowledge_graph(self, analyzed_insights: List[AnalyzedInsight]) -> Dict[str, Any]:
        """Generate a knowledge graph structure from analyzed insights"""
        nodes = []
        edges = []
        
        for insight in analyzed_insights:
            # Create node for insight
            node_id = insight.original_insight.get("id", f"insight_{len(nodes)}")
            
            # Handle timestamp conversion
            timestamp = insight.original_insight.get("timestamp", "")
            if hasattr(timestamp, 'isoformat'):
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = str(timestamp) if timestamp else ""
            
            nodes.append({
                "id": node_id,
                "label": insight.original_insight.get("content", "")[:100] + "...",
                "type": "insight",
                "domains": insight.domains,
                "tags": [tag.name for tag in insight.tags],
                "novelty": insight.novelty_score,
                "testability": insight.testability,
                "timestamp": timestamp_str
            })
            
            # Create edges for connections
            for connection in insight.connections:
                edges.append({
                    "source": connection.insight_id_1,
                    "target": connection.insight_id_2,
                    "type": connection.connection_type,
                    "strength": connection.strength,
                    "shared_concepts": connection.shared_concepts
                })
        
        # Create domain nodes
        all_domains = set()
        for insight in analyzed_insights:
            all_domains.update(insight.domains)
        
        for domain in all_domains:
            nodes.append({
                "id": f"domain_{domain}",
                "label": domain.title(),
                "type": "domain",
                "category": "domain"
            })
            
            # Connect insights to domains
            for insight in analyzed_insights:
                if domain in insight.domains:
                    node_id = insight.original_insight.get("id", f"insight_{len(nodes)}")
                    edges.append({
                        "source": node_id,
                        "target": f"domain_{domain}",
                        "type": "belongs_to",
                        "strength": 0.5
                    })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_insights": len([n for n in nodes if n["type"] == "insight"]),
                "total_domains": len([n for n in nodes if n["type"] == "domain"]),
                "total_connections": len(edges)
            }
        }


    def index_insight_for_search(self, analyzed_insight: AnalyzedInsight) -> bool:
        """
        Index an analyzed insight for semantic search.
        
        Args:
            analyzed_insight: The analyzed insight to index
            
        Returns:
            True if indexed successfully
        """
        if not SEMANTIC_SEARCH_AVAILABLE or semantic_search is None:
            return False
        
        insight = analyzed_insight.original_insight
        
        metadata = {
            "domains": analyzed_insight.domains,
            "tags": [tag.name for tag in analyzed_insight.tags],
            "novelty_score": analyzed_insight.novelty_score,
            "testability": analyzed_insight.testability,
            "key_concepts": analyzed_insight.key_concepts,
            "analyzed_at": analyzed_insight.analyzed_at.isoformat()
        }
        
        return semantic_search.index_document(
            doc_id=insight.get("id", f"insight_{id(insight)}"),
            content=insight.get("content", ""),
            metadata=metadata
        )
    
    def find_similar_insights(self, insight_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find insights similar to a given insight using semantic search.
        
        Args:
            insight_id: ID of the insight to find similar insights for
            limit: Maximum number of similar insights to return
            
        Returns:
            List of similar insights with similarity scores
        """
        if not SEMANTIC_SEARCH_AVAILABLE or semantic_search is None:
            return []
        
        results = semantic_search.find_similar(insight_id, limit=limit)
        
        return [
            {
                "id": r.id,
                "content": r.content,
                "similarity_score": r.score,
                "match_type": r.match_type,
                "metadata": r.metadata
            }
            for r in results
        ]
    
    def semantic_search_insights(self, query: str, limit: int = 10, min_score: float = 0.3) -> List[Dict[str, Any]]:
        """
        Search insights using semantic similarity.
        
        Args:
            query: Search query
            limit: Maximum results to return
            min_score: Minimum similarity threshold
            
        Returns:
            List of matching insights with scores
        """
        if not SEMANTIC_SEARCH_AVAILABLE or semantic_search is None:
            return []
        
        results = semantic_search.search(query, limit=limit, min_score=min_score)
        
        return [
            {
                "id": r.id,
                "content": r.content,
                "score": r.score,
                "match_type": r.match_type,
                "metadata": r.metadata
            }
            for r in results
        ]


# Global instance
insight_analyzer = InsightAnalyzer()

