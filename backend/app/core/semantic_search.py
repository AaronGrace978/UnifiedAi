"""
Semantic Search Engine
Vector-based semantic search for insights using sentence transformers.

Falls back to keyword search if sentence-transformers not available.
"""

import sqlite3
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SentenceTransformer = None


@dataclass
class SearchResult:
    """A semantic search result"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    match_type: str = "semantic"  # "semantic" or "keyword"


class SemanticSearchEngine:
    """
    Semantic search using sentence embeddings.
    
    Uses sentence-transformers for embedding generation and cosine similarity
    for retrieval. Falls back to keyword matching if dependencies unavailable.
    """
    
    def __init__(self, db_path: Optional[str] = None, model_name: str = "all-MiniLM-L6-v2"):
        if not db_path:
            import os
            from pathlib import Path
            explicit = (os.getenv("UNIFIEDAI_DATA_DIR") or "").strip()
            if explicit:
                base = Path(explicit)
            else:
                appdata = os.getenv("APPDATA")
                base = Path(appdata) / "unifiedai" / "backend" if appdata else Path.home() / ".unifiedai" / "backend"
            base.mkdir(parents=True, exist_ok=True)
            db_path = str(base / "semantic_index.db")
        self.db_path = db_path
        self.model_name = model_name
        self.model = None
        self.embedding_dim = 384  # Default for MiniLM
        
        # Initialize embedding model if available
        if EMBEDDINGS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
                print(f"[OK] Semantic search initialized with {model_name}")
            except Exception as e:
                print(f"[WARNING] Could not load embedding model: {e}")
                self.model = None
        else:
            print("[WARNING] sentence-transformers not available, using keyword fallback")
        
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for vector storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding BLOB,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index for faster retrieval
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_created 
            ON documents(created_at DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def _embed(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for text"""
        if self.model is None:
            return None
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            print(f"Embedding error: {e}")
            return None
    
    def _embed_batch(self, texts: List[str]) -> Optional[np.ndarray]:
        """Generate embeddings for multiple texts"""
        if self.model is None:
            return None
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            print(f"Batch embedding error: {e}")
            return None
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def index_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Index a document for semantic search.
        
        Args:
            doc_id: Unique document identifier
            content: Document content to index
            metadata: Optional metadata dictionary
            
        Returns:
            True if indexed successfully
        """
        # Generate embedding
        embedding = self._embed(content)
        embedding_blob = embedding.tobytes() if embedding is not None else None
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO documents (id, content, embedding, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            doc_id,
            content,
            embedding_blob,
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        conn.close()
        
        return True
    
    def index_batch(self, documents: List[Dict[str, Any]]) -> int:
        """
        Index multiple documents at once.
        
        Args:
            documents: List of dicts with 'id', 'content', and optional 'metadata'
            
        Returns:
            Number of documents indexed
        """
        if not documents:
            return 0
        
        # Generate embeddings in batch
        contents = [doc['content'] for doc in documents]
        embeddings = self._embed_batch(contents)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for i, doc in enumerate(documents):
            embedding_blob = None
            if embeddings is not None:
                embedding_blob = embeddings[i].tobytes()
            
            cursor.execute("""
                INSERT OR REPLACE INTO documents (id, content, embedding, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                doc['id'],
                doc['content'],
                embedding_blob,
                json.dumps(doc.get('metadata')) if doc.get('metadata') else None
            ))
        
        conn.commit()
        conn.close()
        
        return len(documents)
    
    def search(self, query: str, limit: int = 10, min_score: float = 0.3) -> List[SearchResult]:
        """
        Search for documents similar to the query.
        
        Args:
            query: Search query
            limit: Maximum results to return
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of SearchResult objects
        """
        # Try semantic search first
        if self.model is not None:
            results = self._semantic_search(query, limit, min_score)
            if results:
                return results
        
        # Fall back to keyword search
        return self._keyword_search(query, limit)
    
    def _semantic_search(self, query: str, limit: int, min_score: float) -> List[SearchResult]:
        """Perform semantic search using embeddings"""
        query_embedding = self._embed(query)
        if query_embedding is None:
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all documents with embeddings
        cursor.execute("SELECT id, content, embedding, metadata FROM documents WHERE embedding IS NOT NULL")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return []
        
        # Calculate similarities
        results = []
        for row in rows:
            doc_id, content, embedding_blob, metadata_str = row
            doc_embedding = np.frombuffer(embedding_blob, dtype=np.float32)
            
            # Ensure dimensions match
            if len(doc_embedding) != len(query_embedding):
                continue
            
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            
            if similarity >= min_score:
                metadata = json.loads(metadata_str) if metadata_str else {}
                results.append(SearchResult(
                    id=doc_id,
                    content=content,
                    score=similarity,
                    metadata=metadata,
                    match_type="semantic"
                ))
        
        # Sort by score and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    def _keyword_search(self, query: str, limit: int) -> List[SearchResult]:
        """Fallback keyword search"""
        # Extract keywords
        keywords = [w.lower() for w in re.findall(r'\b\w+\b', query) if len(w) > 2]
        
        if not keywords:
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build LIKE query for each keyword
        conditions = " OR ".join(["LOWER(content) LIKE ?" for _ in keywords])
        params = [f"%{kw}%" for kw in keywords]
        
        cursor.execute(f"""
            SELECT id, content, metadata FROM documents 
            WHERE {conditions}
            LIMIT ?
        """, params + [limit * 2])  # Get extra for scoring
        
        rows = cursor.fetchall()
        conn.close()
        
        # Score by keyword matches
        results = []
        for doc_id, content, metadata_str in rows:
            content_lower = content.lower()
            matches = sum(1 for kw in keywords if kw in content_lower)
            score = matches / len(keywords)
            
            if score > 0:
                metadata = json.loads(metadata_str) if metadata_str else {}
                results.append(SearchResult(
                    id=doc_id,
                    content=content,
                    score=score,
                    metadata=metadata,
                    match_type="keyword"
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    def find_similar(self, doc_id: str, limit: int = 5) -> List[SearchResult]:
        """
        Find documents similar to a given document.
        
        Args:
            doc_id: ID of the document to find similar documents for
            limit: Maximum results
            
        Returns:
            List of similar documents
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT content, embedding FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return []
        
        content, embedding_blob = row
        
        if embedding_blob and self.model:
            # Use the stored embedding for similarity search
            query_embedding = np.frombuffer(embedding_blob, dtype=np.float32)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, content, embedding, metadata FROM documents 
                WHERE id != ? AND embedding IS NOT NULL
            """, (doc_id,))
            rows = cursor.fetchall()
            conn.close()
            
            results = []
            for row in rows:
                other_id, other_content, other_embedding_blob, metadata_str = row
                other_embedding = np.frombuffer(other_embedding_blob, dtype=np.float32)
                
                if len(other_embedding) != len(query_embedding):
                    continue
                
                similarity = self._cosine_similarity(query_embedding, other_embedding)
                metadata = json.loads(metadata_str) if metadata_str else {}
                
                results.append(SearchResult(
                    id=other_id,
                    content=other_content,
                    score=similarity,
                    metadata=metadata,
                    match_type="semantic"
                ))
            
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]
        
        # Fallback: use content for keyword search
        return self._keyword_search(content[:200], limit)
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, content, metadata, created_at FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "id": row[0],
            "content": row[1],
            "metadata": json.loads(row[2]) if row[2] else {},
            "created_at": row[3]
        }
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the index"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM documents WHERE embedding IS NOT NULL")
        with_embeddings = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_documents": total,
            "documents_with_embeddings": with_embeddings,
            "embedding_model": self.model_name if self.model else "none",
            "embedding_dimension": self.embedding_dim if self.model else 0,
            "semantic_search_available": self.model is not None
        }


# Global instance
semantic_search = SemanticSearchEngine()

