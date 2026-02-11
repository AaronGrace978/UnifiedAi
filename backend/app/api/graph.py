"""
Graph Analysis API Endpoints
Advanced knowledge graph algorithms
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.graph_algorithms import graph_analyzer

router = APIRouter(prefix="/api/graph", tags=["Graph Analysis"])


class BuildGraphRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class PathRequest(BaseModel):
    source: str
    target: str


class NeighborhoodRequest(BaseModel):
    node_id: str
    depth: int = 1


@router.post("/build")
async def build_graph(request: BuildGraphRequest) -> Dict[str, Any]:
    """Build the knowledge graph from nodes and edges"""
    try:
        success = graph_analyzer.build_graph(request.nodes, request.edges)
        stats = graph_analyzer.get_graph_stats()
        return {
            "success": success,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_graph_stats() -> Dict[str, Any]:
    """Get graph statistics"""
    try:
        return graph_analyzer.get_graph_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/communities")
async def detect_communities(resolution: float = 1.0) -> Dict[str, Any]:
    """Detect communities in the knowledge graph"""
    try:
        communities = graph_analyzer.detect_communities(resolution)
        return {
            "communities": [
                {
                    "id": c.id,
                    "name": c.name,
                    "members": c.members,
                    "size": c.size,
                    "cohesion": c.cohesion,
                    "key_themes": c.key_themes,
                    "central_node": c.central_node
                }
                for c in communities
            ],
            "count": len(communities)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/centrality")
async def analyze_centrality(top_n: int = 10) -> Dict[str, Any]:
    """Analyze node centrality in the graph"""
    try:
        analysis = graph_analyzer.analyze_centrality(top_n)
        return {
            "most_central_nodes": [
                {"node_id": node, "score": score}
                for node, score in analysis.most_central_nodes
            ],
            "hub_nodes": analysis.hub_nodes,
            "metrics": {
                "degree_centrality": dict(list(analysis.degree_centrality.items())[:20]),
                "betweenness_centrality": dict(list(analysis.betweenness_centrality.items())[:20]),
                "pagerank": dict(list(analysis.pagerank.items())[:20])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics")
async def discover_topics(num_topics: int = 5) -> Dict[str, Any]:
    """Discover topics from insights"""
    try:
        topics = graph_analyzer.discover_topics(num_topics)
        return {
            "topics": [
                {
                    "id": t.id,
                    "name": t.name,
                    "keywords": t.keywords,
                    "insight_count": len(t.insight_ids),
                    "insight_ids": t.insight_ids[:10],  # Limit for response size
                    "prevalence": t.prevalence,
                    "coherence": t.coherence
                }
                for t in topics
            ],
            "count": len(topics)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def detect_trends(time_window_days: int = 30) -> Dict[str, Any]:
    """Detect trends in topics over time"""
    try:
        trends = graph_analyzer.detect_trends(time_window_days)
        return {
            "trends": [
                {
                    "topic": t.topic,
                    "direction": t.direction,
                    "change_rate": t.change_rate,
                    "time_range": [
                        t.time_range[0].isoformat() if t.time_range[0] else None,
                        t.time_range[1].isoformat() if t.time_range[1] else None
                    ],
                    "data_points_count": len(t.data_points)
                }
                for t in trends
            ],
            "count": len(trends)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/path")
async def find_path(request: PathRequest) -> Dict[str, Any]:
    """Find shortest path between two nodes"""
    try:
        path = graph_analyzer.find_shortest_path(request.source, request.target)
        return {
            "source": request.source,
            "target": request.target,
            "path": path,
            "length": len(path) - 1 if path else -1,
            "found": len(path) > 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/neighborhood")
async def get_neighborhood(request: NeighborhoodRequest) -> Dict[str, Any]:
    """Get the neighborhood of a node"""
    try:
        result = graph_analyzer.get_neighborhood(request.node_id, request.depth)
        return {
            "center": request.node_id,
            "depth": request.depth,
            "nodes": result["nodes"],
            "edges": result["edges"],
            "node_count": len(result["nodes"]),
            "edge_count": len(result["edges"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

