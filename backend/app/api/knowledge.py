"""
External Knowledge API Endpoints
arXiv, Wikipedia, and knowledge enrichment
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.external_knowledge import external_knowledge

router = APIRouter(prefix="/api/knowledge", tags=["External Knowledge"])


class ArxivSearchRequest(BaseModel):
    query: str
    max_results: int = 5
    categories: Optional[List[str]] = None


class WikipediaSearchRequest(BaseModel):
    query: str
    sentences: int = 3


class EnrichInsightRequest(BaseModel):
    insight_content: str
    domains: Optional[List[str]] = None


class CiteClaimRequest(BaseModel):
    claim: str


@router.post("/arxiv/search")
async def search_arxiv(request: ArxivSearchRequest) -> Dict[str, Any]:
    """Search arXiv for relevant papers"""
    try:
        papers = await external_knowledge.search_arxiv(
            query=request.query,
            max_results=request.max_results,
            categories=request.categories
        )
        
        return {
            "query": request.query,
            "papers": [
                {
                    "arxiv_id": p.arxiv_id,
                    "title": p.title,
                    "authors": p.authors,
                    "abstract": p.abstract,
                    "categories": p.categories,
                    "published": p.published,
                    "pdf_url": p.pdf_url
                }
                for p in papers
            ],
            "count": len(papers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wikipedia/search")
async def search_wikipedia(request: WikipediaSearchRequest) -> Dict[str, Any]:
    """Get Wikipedia article summary"""
    try:
        article = await external_knowledge.search_wikipedia(
            query=request.query,
            sentences=request.sentences
        )
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return {
            "title": article.title,
            "summary": article.summary,
            "url": article.url,
            "related_topics": article.related_topics
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enrich")
async def enrich_insight(request: EnrichInsightRequest) -> Dict[str, Any]:
    """Enrich an insight with external knowledge"""
    try:
        enrichment = await external_knowledge.enrich_insight(
            insight_content=request.insight_content,
            domains=request.domains
        )
        return enrichment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cite")
async def cite_for_claim(request: CiteClaimRequest) -> Dict[str, Any]:
    """Find citations to support a claim"""
    try:
        citations = await external_knowledge.cite_for_claim(request.claim)
        return {
            "claim": request.claim,
            "citations": citations,
            "count": len(citations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

