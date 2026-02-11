"""
External Knowledge Integration
arXiv, Wikipedia, and other knowledge sources.

Provides access to external knowledge bases for enriching insights.
"""

import asyncio
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


@dataclass
class ArxivPaper:
    """An arXiv paper"""
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published: str
    pdf_url: str
    relevance_score: float = 0.0


@dataclass
class WikipediaArticle:
    """A Wikipedia article summary"""
    title: str
    summary: str
    url: str
    categories: List[str] = field(default_factory=list)
    related_topics: List[str] = field(default_factory=list)


@dataclass
class ExternalReference:
    """A reference from external sources"""
    source: str  # "arxiv", "wikipedia", "semantic_scholar"
    title: str
    content: str
    url: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    retrieved_at: datetime = field(default_factory=datetime.now)


class ExternalKnowledge:
    """
    External knowledge integration for UnifiedAi.
    
    Provides access to:
    - arXiv scientific papers
    - Wikipedia articles
    - Semantic Scholar (future)
    - PubMed (future)
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0) if HTTPX_AVAILABLE else None
        
        # API endpoints
        self.arxiv_api = "http://export.arxiv.org/api/query"
        self.wikipedia_api = "https://en.wikipedia.org/api/rest_v1"
        
        # Cache
        self.cache: Dict[str, ExternalReference] = {}
        self.cache_duration = 3600  # 1 hour
    
    async def search_arxiv(
        self,
        query: str,
        max_results: int = 5,
        categories: List[str] = None
    ) -> List[ArxivPaper]:
        """
        Search arXiv for relevant papers.
        
        Args:
            query: Search query
            max_results: Maximum papers to return
            categories: Filter by arXiv categories (e.g., ["cs.AI", "physics.gen-ph"])
            
        Returns:
            List of ArxivPaper objects
        """
        if not self.client:
            return []
        
        # Build query
        search_query = f"all:{query}"
        if categories:
            cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
            search_query = f"({search_query}) AND ({cat_query})"
        
        try:
            response = await self.client.get(
                self.arxiv_api,
                params={
                    "search_query": search_query,
                    "max_results": max_results,
                    "sortBy": "relevance"
                }
            )
            response.raise_for_status()
            
            # Parse XML response (simplified parsing)
            content = response.text
            papers = []
            
            # Extract entries
            entries = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)
            
            for entry in entries[:max_results]:
                # Extract fields
                title_match = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
                title = title_match.group(1).strip() if title_match else "Unknown"
                
                abstract_match = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
                abstract = abstract_match.group(1).strip() if abstract_match else ""
                
                id_match = re.search(r'<id>http://arxiv.org/abs/(.*?)</id>', entry)
                arxiv_id = id_match.group(1) if id_match else ""
                
                authors = re.findall(r'<name>(.*?)</name>', entry)
                
                categories = re.findall(r'<category term="(.*?)"', entry)
                
                published_match = re.search(r'<published>(.*?)</published>', entry)
                published = published_match.group(1)[:10] if published_match else ""
                
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                
                papers.append(ArxivPaper(
                    arxiv_id=arxiv_id,
                    title=title,
                    authors=authors,
                    abstract=abstract[:500],
                    categories=categories,
                    published=published,
                    pdf_url=pdf_url
                ))
            
            return papers
            
        except Exception as e:
            print(f"arXiv search error: {e}")
            return []
    
    async def search_wikipedia(
        self,
        query: str,
        sentences: int = 3
    ) -> Optional[WikipediaArticle]:
        """
        Get Wikipedia article summary.
        
        Args:
            query: Search term
            sentences: Number of sentences in summary
            
        Returns:
            WikipediaArticle or None
        """
        if not self.client:
            return None
        
        try:
            # Search for article
            encoded_query = quote(query)
            
            response = await self.client.get(
                f"{self.wikipedia_api}/page/summary/{encoded_query}",
                headers={"Accept": "application/json"}
            )
            
            if response.status_code == 404:
                # Try search API
                search_response = await self.client.get(
                    f"https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "opensearch",
                        "search": query,
                        "limit": 1,
                        "format": "json"
                    }
                )
                search_data = search_response.json()
                
                if len(search_data) > 1 and len(search_data[1]) > 0:
                    # Try first result
                    first_result = search_data[1][0]
                    response = await self.client.get(
                        f"{self.wikipedia_api}/page/summary/{quote(first_result)}",
                        headers={"Accept": "application/json"}
                    )
            
            response.raise_for_status()
            data = response.json()
            
            # Get related articles
            related = []
            try:
                related_response = await self.client.get(
                    f"{self.wikipedia_api}/page/related/{encoded_query}",
                    headers={"Accept": "application/json"}
                )
                if related_response.status_code == 200:
                    related_data = related_response.json()
                    related = [p.get("title", "") for p in related_data.get("pages", [])[:5]]
            except:
                pass
            
            return WikipediaArticle(
                title=data.get("title", query),
                summary=data.get("extract", "No summary available."),
                url=data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                categories=[],
                related_topics=related
            )
            
        except Exception as e:
            print(f"Wikipedia search error: {e}")
            return None
    
    async def enrich_insight(
        self,
        insight_content: str,
        domains: List[str] = None
    ) -> Dict[str, Any]:
        """
        Enrich an insight with external knowledge.
        
        Searches for relevant papers and articles based on insight content.
        
        Args:
            insight_content: The insight text
            domains: Scientific domains for better search
            
        Returns:
            Dictionary with external references
        """
        # Extract key terms for search
        key_terms = self._extract_key_terms(insight_content)
        
        if not key_terms:
            return {"papers": [], "articles": [], "message": "Could not extract search terms"}
        
        search_query = " ".join(key_terms[:5])
        
        # Search in parallel
        arxiv_task = self.search_arxiv(search_query, max_results=3)
        wiki_task = self.search_wikipedia(key_terms[0] if key_terms else insight_content[:50])
        
        papers, article = await asyncio.gather(arxiv_task, wiki_task)
        
        return {
            "search_query": search_query,
            "papers": [
                {
                    "arxiv_id": p.arxiv_id,
                    "title": p.title,
                    "authors": p.authors[:3],
                    "abstract": p.abstract[:200] + "...",
                    "pdf_url": p.pdf_url,
                    "published": p.published
                }
                for p in papers
            ],
            "wikipedia": {
                "title": article.title,
                "summary": article.summary,
                "url": article.url,
                "related_topics": article.related_topics
            } if article else None
        }
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text for searching"""
        # Simple extraction - remove common words and keep significant terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'this', 'that', 'these', 'those', 'it', 'its', 'as', 'from', 'which',
            'what', 'how', 'why', 'when', 'where', 'could', 'would', 'should',
            'might', 'may', 'can', 'will', 'has', 'have', 'had', 'do', 'does',
            'did', 'not', 'no', 'yes', 'all', 'any', 'some', 'every', 'each'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Filter and score
        term_freq = {}
        for word in words:
            if word not in stop_words:
                term_freq[word] = term_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_terms = sorted(term_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [term for term, freq in sorted_terms[:10]]
    
    async def cite_for_claim(
        self,
        claim: str
    ) -> List[Dict[str, Any]]:
        """
        Find citations to support a claim.
        
        Args:
            claim: The claim or statement to find support for
            
        Returns:
            List of potential citations
        """
        papers = await self.search_arxiv(claim, max_results=5)
        
        citations = []
        for paper in papers:
            # Simple relevance scoring based on term overlap
            claim_words = set(claim.lower().split())
            title_words = set(paper.title.lower().split())
            abstract_words = set(paper.abstract.lower().split())
            
            title_overlap = len(claim_words & title_words)
            abstract_overlap = len(claim_words & abstract_words)
            
            relevance = (title_overlap * 2 + abstract_overlap) / max(len(claim_words), 1)
            
            citations.append({
                "source": "arXiv",
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "authors": paper.authors,
                "relevance_score": min(relevance, 1.0),
                "citation_text": f"{', '.join(paper.authors[:3])}. \"{paper.title}\". arXiv:{paper.arxiv_id} ({paper.published})"
            })
        
        # Sort by relevance
        citations.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return citations


# Global instance
external_knowledge = ExternalKnowledge()

