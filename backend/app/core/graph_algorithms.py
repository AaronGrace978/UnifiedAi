"""
Advanced Knowledge Graph Algorithms
Community detection, centrality analysis, topic modeling, and trend detection.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import math

# Try to import networkx for graph algorithms
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None


@dataclass
class Community:
    """A detected community of insights"""
    id: str
    name: str
    members: List[str]  # Node IDs
    size: int
    cohesion: float  # Internal connectivity (0-1)
    key_themes: List[str]
    central_node: str  # Most central node in community
    

@dataclass
class CentralityAnalysis:
    """Centrality analysis results for the knowledge graph"""
    degree_centrality: Dict[str, float]  # Connection count
    betweenness_centrality: Dict[str, float]  # Bridge nodes
    closeness_centrality: Dict[str, float]  # Quick reach to others
    pagerank: Dict[str, float]  # Influence/importance
    most_central_nodes: List[Tuple[str, float]]  # Top N central nodes
    hub_nodes: List[str]  # Nodes connecting different parts


@dataclass
class Topic:
    """A discovered topic from insights"""
    id: str
    name: str
    keywords: List[str]
    insight_ids: List[str]
    prevalence: float  # How common (0-1)
    coherence: float  # How well-defined (0-1)


@dataclass
class Trend:
    """A detected trend in insights over time"""
    topic: str
    direction: str  # "increasing", "decreasing", "stable", "emerging"
    change_rate: float  # Rate of change
    time_range: Tuple[datetime, datetime]
    data_points: List[Tuple[datetime, float]]


class KnowledgeGraphAnalyzer:
    """
    Advanced analysis algorithms for the knowledge graph.
    
    Implements:
    - Community detection (Louvain algorithm)
    - Centrality analysis (multiple metrics)
    - Topic modeling (keyword-based)
    - Trend detection (temporal analysis)
    """
    
    def __init__(self):
        self.graph = None
        if NETWORKX_AVAILABLE:
            self.graph = nx.Graph()
    
    def build_graph(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> bool:
        """
        Build the knowledge graph from nodes and edges.
        
        Args:
            nodes: List of node dictionaries with 'id', 'type', 'label', etc.
            edges: List of edge dictionaries with 'source', 'target', 'type', 'strength'
            
        Returns:
            True if graph was built successfully
        """
        if not NETWORKX_AVAILABLE:
            return False
        
        self.graph = nx.Graph()
        
        # Add nodes with attributes
        for node in nodes:
            node_id = node.get('id', str(id(node)))
            self.graph.add_node(node_id, **node)
        
        # Add edges with attributes
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            if source and target:
                weight = edge.get('strength', 1.0)
                self.graph.add_edge(source, target, weight=weight, **edge)
        
        return True
    
    def detect_communities(self, resolution: float = 1.0) -> List[Community]:
        """
        Detect communities using the Louvain algorithm.
        
        Args:
            resolution: Resolution parameter (higher = more communities)
            
        Returns:
            List of detected communities
        """
        if not NETWORKX_AVAILABLE or self.graph is None or len(self.graph.nodes) == 0:
            return []
        
        try:
            # Use Louvain community detection
            from networkx.algorithms.community import louvain_communities
            communities_sets = louvain_communities(self.graph, resolution=resolution, seed=42)
        except ImportError:
            # Fallback to connected components if Louvain not available
            communities_sets = list(nx.connected_components(self.graph))
        
        communities = []
        for i, members in enumerate(communities_sets):
            members_list = list(members)
            
            # Calculate cohesion (internal edge density)
            subgraph = self.graph.subgraph(members)
            if len(members) > 1:
                max_edges = len(members) * (len(members) - 1) / 2
                actual_edges = subgraph.number_of_edges()
                cohesion = actual_edges / max_edges if max_edges > 0 else 0
            else:
                cohesion = 1.0
            
            # Find central node in community
            if len(members) > 0:
                subgraph_centrality = nx.degree_centrality(subgraph)
                central_node = max(subgraph_centrality, key=subgraph_centrality.get)
            else:
                central_node = members_list[0] if members_list else ""
            
            # Extract themes from node labels
            themes = self._extract_themes_from_nodes(members_list)
            
            # Generate community name from themes
            name = f"Community {i+1}"
            if themes:
                name = f"{themes[0].title()} Cluster"
            
            communities.append(Community(
                id=f"community_{i}",
                name=name,
                members=members_list,
                size=len(members),
                cohesion=cohesion,
                key_themes=themes[:5],
                central_node=central_node
            ))
        
        # Sort by size
        communities.sort(key=lambda c: c.size, reverse=True)
        
        return communities
    
    def _extract_themes_from_nodes(self, node_ids: List[str]) -> List[str]:
        """Extract common themes from node labels"""
        if not self.graph:
            return []
        
        # Collect all labels
        labels = []
        for node_id in node_ids:
            if node_id in self.graph.nodes:
                node_data = self.graph.nodes[node_id]
                label = node_data.get('label', '')
                if label:
                    labels.append(label.lower())
                
                # Also include tags and domains
                tags = node_data.get('tags', [])
                labels.extend([t.lower() for t in tags])
                
                domains = node_data.get('domains', [])
                labels.extend([d.lower() for d in domains])
        
        # Count word frequencies
        word_counts = defaultdict(int)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'this', 'that', 'these', 'those'}
        
        for label in labels:
            words = label.split()
            for word in words:
                word = word.strip('.,!?()[]{}":;')
                if len(word) > 3 and word not in stop_words:
                    word_counts[word] += 1
        
        # Return top themes
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:10]]
    
    def analyze_centrality(self, top_n: int = 10) -> CentralityAnalysis:
        """
        Perform comprehensive centrality analysis.
        
        Args:
            top_n: Number of top central nodes to return
            
        Returns:
            CentralityAnalysis with multiple centrality metrics
        """
        if not NETWORKX_AVAILABLE or self.graph is None or len(self.graph.nodes) == 0:
            return CentralityAnalysis(
                degree_centrality={},
                betweenness_centrality={},
                closeness_centrality={},
                pagerank={},
                most_central_nodes=[],
                hub_nodes=[]
            )
        
        # Calculate various centrality metrics
        degree = nx.degree_centrality(self.graph)
        
        # Betweenness (nodes that bridge parts of the graph)
        try:
            betweenness = nx.betweenness_centrality(self.graph)
        except:
            betweenness = {}
        
        # Closeness (how quickly can reach all other nodes)
        try:
            closeness = nx.closeness_centrality(self.graph)
        except:
            closeness = {}
        
        # PageRank (importance based on connections)
        try:
            pagerank = nx.pagerank(self.graph)
        except:
            pagerank = degree  # Fallback to degree
        
        # Find most central nodes (combined score)
        combined_scores = {}
        for node in self.graph.nodes:
            score = (
                degree.get(node, 0) * 0.25 +
                betweenness.get(node, 0) * 0.25 +
                closeness.get(node, 0) * 0.25 +
                pagerank.get(node, 0) * 0.25
            )
            combined_scores[node] = score
        
        most_central = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        # Identify hub nodes (high betweenness = bridges different parts)
        betweenness_threshold = sum(betweenness.values()) / len(betweenness) if betweenness else 0
        hub_nodes = [node for node, score in betweenness.items() if score > betweenness_threshold * 2]
        
        return CentralityAnalysis(
            degree_centrality=degree,
            betweenness_centrality=betweenness,
            closeness_centrality=closeness,
            pagerank=pagerank,
            most_central_nodes=most_central,
            hub_nodes=hub_nodes[:top_n]
        )
    
    def discover_topics(self, num_topics: int = 5) -> List[Topic]:
        """
        Discover topics from insight content.
        
        Uses keyword extraction and clustering to identify topics.
        
        Args:
            num_topics: Target number of topics to discover
            
        Returns:
            List of discovered topics
        """
        if not self.graph or len(self.graph.nodes) == 0:
            return []
        
        # Collect content from insight nodes
        insight_contents = {}
        for node_id in self.graph.nodes:
            node_data = self.graph.nodes[node_id]
            if node_data.get('type') == 'insight':
                content = node_data.get('label', '') + ' '
                content += ' '.join(node_data.get('tags', []))
                content += ' '.join(node_data.get('domains', []))
                insight_contents[node_id] = content.lower()
        
        if not insight_contents:
            return []
        
        # Extract keywords and their document frequencies
        keyword_docs = defaultdict(set)
        doc_keywords = defaultdict(list)
        
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'this', 'that', 'these', 'those', 'which', 'what', 'how', 'why', 'when', 'where', 'could', 'would', 'should', 'might', 'may', 'can'}
        
        for doc_id, content in insight_contents.items():
            words = content.split()
            for word in words:
                word = word.strip('.,!?()[]{}":;')
                if len(word) > 3 and word not in stop_words:
                    keyword_docs[word].add(doc_id)
                    doc_keywords[doc_id].append(word)
        
        # Score keywords by TF-IDF-like measure
        num_docs = len(insight_contents)
        keyword_scores = {}
        for keyword, docs in keyword_docs.items():
            df = len(docs)
            idf = math.log(num_docs / df) if df > 0 else 0
            # Favor keywords that appear in multiple but not all documents
            specificity = 1 - abs(0.3 - df/num_docs)  # Optimal around 30% of docs
            keyword_scores[keyword] = idf * specificity * len(docs)
        
        # Cluster keywords into topics
        top_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)[:num_topics * 5]
        
        # Create topics from top keyword clusters
        topics = []
        used_keywords = set()
        
        for i in range(num_topics):
            # Find seed keyword
            seed = None
            for keyword, score in top_keywords:
                if keyword not in used_keywords:
                    seed = keyword
                    break
            
            if not seed:
                break
            
            # Find related keywords (appear in same documents)
            seed_docs = keyword_docs[seed]
            related = []
            for keyword, docs in keyword_docs.items():
                if keyword != seed and keyword not in used_keywords:
                    overlap = len(docs & seed_docs) / max(len(docs), len(seed_docs))
                    if overlap > 0.3:
                        related.append((keyword, overlap))
            
            related.sort(key=lambda x: x[1], reverse=True)
            topic_keywords = [seed] + [k for k, _ in related[:4]]
            
            for k in topic_keywords:
                used_keywords.add(k)
            
            # Find insights belonging to this topic
            topic_insights = []
            for doc_id, keywords in doc_keywords.items():
                if any(k in keywords for k in topic_keywords):
                    topic_insights.append(doc_id)
            
            # Calculate metrics
            prevalence = len(topic_insights) / num_docs if num_docs > 0 else 0
            coherence = len(seed_docs & set(topic_insights)) / len(topic_insights) if topic_insights else 0
            
            topics.append(Topic(
                id=f"topic_{i}",
                name=seed.title(),
                keywords=topic_keywords,
                insight_ids=topic_insights,
                prevalence=prevalence,
                coherence=coherence
            ))
        
        # Sort by prevalence
        topics.sort(key=lambda t: t.prevalence, reverse=True)
        
        return topics
    
    def detect_trends(self, time_window_days: int = 30) -> List[Trend]:
        """
        Detect trends in topics over time.
        
        Args:
            time_window_days: Time window for trend analysis
            
        Returns:
            List of detected trends
        """
        if not self.graph or len(self.graph.nodes) == 0:
            return []
        
        # Collect timestamps from insights
        timestamped_topics = defaultdict(list)
        
        for node_id in self.graph.nodes:
            node_data = self.graph.nodes[node_id]
            if node_data.get('type') == 'insight':
                timestamp_str = node_data.get('timestamp')
                if timestamp_str:
                    try:
                        if isinstance(timestamp_str, datetime):
                            timestamp = timestamp_str
                        else:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        
                        # Get domains/tags as topics
                        topics = node_data.get('domains', []) + node_data.get('tags', [])
                        for topic in topics:
                            timestamped_topics[topic].append(timestamp)
                    except:
                        continue
        
        if not timestamped_topics:
            return []
        
        trends = []
        now = datetime.now()
        
        for topic, timestamps in timestamped_topics.items():
            if len(timestamps) < 2:
                continue
            
            timestamps.sort()
            
            # Calculate trend direction
            time_range = (timestamps[0], timestamps[-1])
            duration_days = (timestamps[-1] - timestamps[0]).days
            
            if duration_days == 0:
                continue
            
            # Split into halves and compare
            mid_point = len(timestamps) // 2
            first_half = len(timestamps[:mid_point])
            second_half = len(timestamps[mid_point:])
            
            # Calculate change rate
            if first_half > 0:
                change_rate = (second_half - first_half) / first_half
            else:
                change_rate = 1.0 if second_half > 0 else 0.0
            
            # Determine direction
            if change_rate > 0.3:
                direction = "increasing"
            elif change_rate < -0.3:
                direction = "decreasing"
            elif len(timestamps) < 3 and (now - timestamps[-1]).days < time_window_days:
                direction = "emerging"
            else:
                direction = "stable"
            
            # Create data points (daily counts)
            daily_counts = defaultdict(int)
            for ts in timestamps:
                day = ts.date()
                daily_counts[day] += 1
            
            data_points = [(datetime.combine(d, datetime.min.time()), c) for d, c in sorted(daily_counts.items())]
            
            trends.append(Trend(
                topic=topic,
                direction=direction,
                change_rate=change_rate,
                time_range=time_range,
                data_points=data_points
            ))
        
        # Sort by absolute change rate
        trends.sort(key=lambda t: abs(t.change_rate), reverse=True)
        
        return trends
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the knowledge graph"""
        if not NETWORKX_AVAILABLE or self.graph is None:
            return {
                "networkx_available": NETWORKX_AVAILABLE,
                "graph_built": False
            }
        
        stats = {
            "networkx_available": True,
            "graph_built": True,
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0,
            "is_connected": nx.is_connected(self.graph) if self.graph.number_of_nodes() > 0 else False,
            "num_components": nx.number_connected_components(self.graph) if self.graph.number_of_nodes() > 0 else 0,
        }
        
        # Node type breakdown
        type_counts = defaultdict(int)
        for node_id in self.graph.nodes:
            node_type = self.graph.nodes[node_id].get('type', 'unknown')
            type_counts[node_type] += 1
        stats["node_types"] = dict(type_counts)
        
        return stats
    
    def find_shortest_path(self, source: str, target: str) -> List[str]:
        """Find shortest path between two nodes"""
        if not NETWORKX_AVAILABLE or self.graph is None:
            return []
        
        if source not in self.graph.nodes or target not in self.graph.nodes:
            return []
        
        try:
            path = nx.shortest_path(self.graph, source, target)
            return path
        except nx.NetworkXNoPath:
            return []
    
    def get_neighborhood(self, node_id: str, depth: int = 1) -> Dict[str, Any]:
        """Get the neighborhood of a node up to a certain depth"""
        if not NETWORKX_AVAILABLE or self.graph is None:
            return {"nodes": [], "edges": []}
        
        if node_id not in self.graph.nodes:
            return {"nodes": [], "edges": []}
        
        # Get neighbors up to depth
        neighborhood = {node_id}
        current_layer = {node_id}
        
        for _ in range(depth):
            next_layer = set()
            for node in current_layer:
                neighbors = set(self.graph.neighbors(node))
                next_layer.update(neighbors)
            neighborhood.update(next_layer)
            current_layer = next_layer
        
        # Extract subgraph
        subgraph = self.graph.subgraph(neighborhood)
        
        nodes = [
            {"id": n, **self.graph.nodes[n]}
            for n in subgraph.nodes
        ]
        
        edges = [
            {"source": u, "target": v, **self.graph.edges[u, v]}
            for u, v in subgraph.edges
        ]
        
        return {"nodes": nodes, "edges": edges}


# Global instance
graph_analyzer = KnowledgeGraphAnalyzer()

