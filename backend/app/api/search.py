"""
Semantic Search API Endpoints
Vector-based semantic search for UnifiedAi
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.semantic_search import semantic_search

router = APIRouter(prefix="/api/search", tags=["Semantic Search"])


class IndexDocumentRequest(BaseModel):
    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class IndexBatchRequest(BaseModel):
    documents: List[IndexDocumentRequest]


class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    min_score: float = 0.3


class SimilarRequest(BaseModel):
    doc_id: str
    limit: int = 5


@router.post("/index")
async def index_document(request: IndexDocumentRequest) -> Dict[str, Any]:
    """Index a single document for semantic search"""
    try:
        success = semantic_search.index_document(
            request.id,
            request.content,
            request.metadata
        )
        return {
            "status": "indexed" if success else "failed",
            "id": request.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/batch")
async def index_batch(request: IndexBatchRequest) -> Dict[str, Any]:
    """Index multiple documents at once"""
    try:
        documents = [
            {
                "id": doc.id,
                "content": doc.content,
                "metadata": doc.metadata
            }
            for doc in request.documents
        ]
        count = semantic_search.index_batch(documents)
        return {
            "status": "success",
            "documents_indexed": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def search_documents(request: SearchRequest) -> Dict[str, Any]:
    """Search for documents using semantic similarity"""
    try:
        results = semantic_search.search(
            request.query,
            limit=request.limit,
            min_score=request.min_score
        )
        return {
            "query": request.query,
            "results": [
                {
                    "id": r.id,
                    "content": r.content[:500] + "..." if len(r.content) > 500 else r.content,
                    "score": r.score,
                    "match_type": r.match_type,
                    "metadata": r.metadata
                }
                for r in results
            ],
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similar")
async def find_similar_documents(request: SimilarRequest) -> Dict[str, Any]:
    """Find documents similar to a given document"""
    try:
        results = semantic_search.find_similar(request.doc_id, request.limit)
        return {
            "reference_id": request.doc_id,
            "similar": [
                {
                    "id": r.id,
                    "content": r.content[:500] + "..." if len(r.content) > 500 else r.content,
                    "score": r.score,
                    "match_type": r.match_type,
                    "metadata": r.metadata
                }
                for r in results
            ],
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document/{doc_id}")
async def get_document(doc_id: str) -> Dict[str, Any]:
    """Get a document by ID"""
    try:
        doc = semantic_search.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/document/{doc_id}")
async def delete_document(doc_id: str) -> Dict[str, Any]:
    """Delete a document from the index"""
    try:
        deleted = semantic_search.delete_document(doc_id)
        return {
            "status": "deleted" if deleted else "not_found",
            "id": doc_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Get semantic search statistics"""
    try:
        return semantic_search.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

