"""
Insights API - Enhanced insight management and visualization
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter()

# Test endpoint to verify router is working
@router.get("/test")
async def test_insights():
    """Test endpoint to verify insights router is loaded"""
    return {"status": "ok", "message": "Insights router is working!"}


# Lazy import to avoid circular dependencies
def get_brain():
    """Lazy import of brain to avoid startup issues"""
    from app.core.brain_thinker import brain
    return brain

def get_analyzer():
    """Lazy import of analyzer to avoid startup issues"""
    from app.core.insight_analyzer import insight_analyzer
    return insight_analyzer


class InsightResponse(BaseModel):
    id: str
    content: str
    timestamp: str
    tags: List[Dict[str, Any]]
    domains: List[str]
    key_concepts: List[str]
    novelty_score: float
    testability: float
    connections: List[Dict[str, Any]]


class KnowledgeGraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    stats: Dict[str, Any]


@router.get("/insights", response_model=List[InsightResponse])
async def get_insights(
    limit: int = Query(50, ge=1, le=500),
    domain: Optional[str] = None,
    tag: Optional[str] = None,
    min_novelty: float = Query(0.0, ge=0.0, le=1.0),
    min_testability: float = Query(0.0, ge=0.0, le=1.0)
):
    """Get analyzed insights with filtering"""
    try:
        brain = get_brain()
        analyzer = get_analyzer()
        
        # Get raw insights
        raw_insights = brain.get_background_insights(limit=limit * 2)
        
        if not raw_insights:
            return []
        
        # Add IDs if missing with proper timestamp handling
        for i, insight in enumerate(raw_insights):
            if "id" not in insight:
                timestamp = insight.get('timestamp', '')
                # Handle datetime objects
                if hasattr(timestamp, 'isoformat'):
                    timestamp_str = timestamp.isoformat().replace(':', '-').replace('.', '-')
                elif isinstance(timestamp, str):
                    timestamp_str = timestamp.replace(':', '-').replace('.', '-')
                else:
                    timestamp_str = str(timestamp).replace(':', '-').replace('.', '-')
                insight["id"] = f"insight_{i}_{timestamp_str}"
        
        # Analyze insights
        analyzed = analyzer.analyze_insight_batch(raw_insights)
        
        # Filter
        filtered = []
        for analysis in analyzed:
            # Domain filter
            if domain and domain not in analysis.domains:
                continue
            
            # Tag filter
            if tag and not any(t.name == tag for t in analysis.tags):
                continue
            
            # Novelty filter
            if analysis.novelty_score < min_novelty:
                continue
            
            # Testability filter
            if analysis.testability < min_testability:
                continue
            
            filtered.append(analysis)
        
        # Limit results
        filtered = filtered[:limit]
        
        # Convert to response format
        responses = []
        for analysis in filtered:
            timestamp = analysis.original_insight.get("timestamp", "")
            if hasattr(timestamp, 'isoformat'):
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = str(timestamp) if timestamp else ""
            
            responses.append(InsightResponse(
                id=analysis.original_insight.get("id", ""),
                content=analysis.original_insight.get("content", ""),
                timestamp=timestamp_str,
                tags=[{"name": t.name, "category": t.category, "confidence": t.confidence} for t in analysis.tags],
                domains=analysis.domains,
                key_concepts=analysis.key_concepts,
                novelty_score=analysis.novelty_score,
                testability=analysis.testability,
                connections=[
                    {
                        "target_id": conn.insight_id_2,
                        "type": conn.connection_type,
                        "strength": conn.strength,
                        "shared_concepts": conn.shared_concepts
                    }
                    for conn in analysis.connections
                ]
            ))
        
        return responses
    except Exception as e:
        import traceback
        print(f"Error in get_insights: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error getting insights: {str(e)}")


@router.get("/knowledge-graph", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(limit: int = Query(100, ge=1, le=500)):
    """Get knowledge graph of insights and their connections"""
    try:
        brain = get_brain()
        analyzer = get_analyzer()
        
        raw_insights = brain.get_background_insights(limit=limit)
        
        # Handle empty insights
        if not raw_insights:
            return KnowledgeGraphResponse(
                nodes=[],
                edges=[],
                stats={
                    "total_insights": 0,
                    "total_domains": 0,
                    "total_connections": 0
                }
            )
        
        # Add IDs with proper timestamp handling
        for i, insight in enumerate(raw_insights):
            if "id" not in insight:
                timestamp = insight.get('timestamp', '')
                # Handle datetime objects
                if hasattr(timestamp, 'isoformat'):
                    timestamp_str = timestamp.isoformat().replace(':', '-').replace('.', '-')
                elif isinstance(timestamp, str):
                    timestamp_str = timestamp.replace(':', '-').replace('.', '-')
                else:
                    timestamp_str = str(timestamp).replace(':', '-').replace('.', '-')
                insight["id"] = f"insight_{i}_{timestamp_str}"
        
        # Analyze and build graph
        analyzed = analyzer.analyze_insight_batch(raw_insights)
        graph = analyzer.generate_knowledge_graph(analyzed)
        
        return KnowledgeGraphResponse(**graph)
    except Exception as e:
        import traceback
        print(f"Error in get_knowledge_graph: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating knowledge graph: {str(e)}")


@router.get("/insights/stats")
async def get_insight_stats():
    """Get statistics about insights"""
    try:
        brain = get_brain()
        analyzer = get_analyzer()
        
        raw_insights = brain.get_background_insights(limit=1000)
        
        if not raw_insights:
            return {
                "total_insights": 0,
                "domains": {},
                "top_tags": {},
                "avg_novelty": 0,
                "avg_testability": 0,
                "total_connections": 0
            }
        
        # Analyze all
        analyzed = analyzer.analyze_insight_batch(raw_insights)
        
        # Calculate stats
        domains_count = {}
        tags_count = {}
        novelty_scores = []
        testability_scores = []
        
        for analysis in analyzed:
            for domain in analysis.domains:
                domains_count[domain] = domains_count.get(domain, 0) + 1
            
            for tag in analysis.tags:
                tags_count[tag.name] = tags_count.get(tag.name, 0) + 1
            
            novelty_scores.append(analysis.novelty_score)
            testability_scores.append(analysis.testability)
        
        return {
            "total_insights": len(analyzed),
            "domains": domains_count,
            "top_tags": dict(sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:10]),
            "avg_novelty": sum(novelty_scores) / len(novelty_scores) if novelty_scores else 0,
            "avg_testability": sum(testability_scores) / len(testability_scores) if testability_scores else 0,
            "total_connections": sum(len(a.connections) for a in analyzed) // 2
        }
    except Exception as e:
        import traceback
        print(f"Error in get_insight_stats: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")
