import warnings
warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*")
"""
Embeddings service for generating and managing text embeddings using sentence-transformers
"""

import asyncio
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import os
from sentence_transformers import SentenceTransformer
import structlog
from functools import lru_cache

from app.core.config import settings
from app.exceptions import EmbeddingError, ConfigurationError

logger = structlog.get_logger()


class EmbeddingsService:
    """Service for generating and managing text embeddings"""
    
    def __init__(self):
        self.model = None
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.embedding_dimension = settings.EMBEDDING_DIMENSION
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self.cache_size = settings.EMBEDDING_CACHE_SIZE
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the sentence transformer model (singleton pattern).
        In testing, use a lightweight fake model to avoid network downloads.
        """
        # Lightweight fake for tests to avoid huggingface downloads
        if os.getenv("TESTING"):
            class _FakeSTModel:
                def __init__(self, dimension: int):
                    self._dimension = dimension
                def get_sentence_embedding_dimension(self) -> int:
                    return self._dimension
                def encode(self, texts, options=None):
                    if isinstance(texts, str):
                        texts = [texts]
                    # Deterministic pseudo-embeddings based on hash
                    embeddings = []
                    for t in texts:
                        h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
                        rng = np.random.default_rng(h % (2**32))
                        vec = rng.random(self._dimension, dtype=np.float32)
                        # Normalize to unit length to mimic ST behavior
                        norm = np.linalg.norm(vec) or 1.0
                        embeddings.append(vec / norm)
                    return np.stack(embeddings)
            self.model = _FakeSTModel(self.embedding_dimension)
            logger.info("Using fake sentence transformer model in TESTING mode", dimension=self.embedding_dimension)
            return

        try:
            logger.info("Loading sentence transformer model", model=self.model_name)
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            logger.info(
                "Sentence transformer model loaded successfully",
                model=self.model_name,
                dimension=self.embedding_dimension
            )
        except Exception as e:
            logger.error("Failed to load sentence transformer model", error=str(e))
            raise EmbeddingError(
                message="Failed to initialize embedding model",
                details={"model_name": self.model_name, "error": str(e)}
            )
    
    @lru_cache(maxsize=1)
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information for metadata storage"""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dimension,
            "model_type": "sentence-transformers"
        }
    
    async def generate_embeddings(
        self, 
        texts: List[str], 
        batch_size: Optional[int] = None
    ) -> List[List[float]]:
        """Generate embeddings for a list of texts with batching"""
        try:
            if not texts:
                return []
            
            logger.info(
                "Generating embeddings",
                text_count=len(texts),
                batch_size=batch_size
            )
            
            # Use configured batch size if not provided
            if batch_size is None:
                batch_size = self.batch_size
            
            # Process in batches for efficiency
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # Generate embeddings for this batch
                batch_embeddings = await self._generate_batch_embeddings(batch_texts)
                all_embeddings.extend(batch_embeddings)
                
                # Small delay to prevent overwhelming the system
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.01)
            
            logger.info(
                "Embeddings generated successfully",
                total_embeddings=len(all_embeddings),
                dimension=len(all_embeddings[0]) if all_embeddings else 0
            )
            
            return all_embeddings
            
        except Exception as e:
            logger.error("Failed to generate embeddings", error=str(e))
            raise
    
    async def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a single batch of texts"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                self.model.encode, 
                texts, 
                {"normalize_embeddings": True}
            )
            
            # Convert numpy arrays to lists
            return [embedding.tolist() for embedding in embeddings]
            
        except Exception as e:
            logger.error("Failed to generate batch embeddings", error=str(e))
            raise EmbeddingError(
                message="Failed to generate embeddings",
                details={"texts_count": len(texts), "error": str(e)}
            )
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            embeddings = await self.generate_embeddings([text], batch_size=1)
            return embeddings[0] if embeddings else []
        except Exception as e:
            logger.error("Failed to generate single embedding", error=str(e))
            raise EmbeddingError(
                message="Failed to generate single embedding",
                details={"text": text[:100], "error": str(e)}
            )

    # --- Backwards-compatible helpers expected by some tests/mocks ---
    async def embed_text(self, text: str) -> List[float]:
        """Alias used by tests: returns a single embedding for the provided text."""
        return await self.generate_single_embedding(text)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Alias used by tests: returns embeddings for multiple texts."""
        return await self.generate_embeddings(texts)
    
    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension for this model"""
        return self.embedding_dimension
    
    def get_model_name(self) -> str:
        """Get the model name"""
        return self.model_name
    
    async def embed_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        workspace_id: str,
        document_id: int
    ) -> List[Dict[str, Any]]:
        """Embed a list of document chunks with metadata"""
        try:
            if not chunks:
                return []
            
            # Extract text content
            texts = [chunk["content"] for chunk in chunks]
            
            # Generate embeddings
            embeddings = await self.generate_embeddings(texts)
            
            # Prepare embedded chunks with metadata
            embedded_chunks = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                embedded_chunk = {
                    "chunk_id": f"ws_{workspace_id}_doc_{document_id}_chunk_{chunk['index']}",
                    "document_id": document_id,
                    "workspace_id": workspace_id,
                    "text": chunk["content"],
                    "chunk_index": chunk["index"],
                    "embedding": embedding,
                    "metadata": {
                        "document_id": document_id,
                        "workspace_id": workspace_id,
                        "chunk_index": chunk["index"],
                        "word_count": chunk.get("word_count", 0),
                        "section_title": chunk.get("section_title", ""),
                        "page_number": chunk.get("page_number"),
                        "content_hash": chunk["hash"],
                        "embedding_model": self.model_name,
                        "embedding_dimension": self.embedding_dimension
                    }
                }
                embedded_chunks.append(embedded_chunk)
            
            logger.info(
                "Chunks embedded successfully",
                workspace_id=workspace_id,
                document_id=document_id,
                chunks_count=len(embedded_chunks)
            )
            
            return embedded_chunks
            
        except Exception as e:
            logger.error(
                "Failed to embed chunks",
                error=str(e),
                workspace_id=workspace_id,
                document_id=document_id
            )
            raise
    
    def calculate_text_hash(self, text: str) -> str:
        """Calculate hash for text content"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    async def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate that an embedding has the correct dimension"""
        return len(embedding) == self.embedding_dimension
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding service"""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dimension,
            "model_loaded": self.model is not None
        }


# Global instance (singleton)
embeddings_service = EmbeddingsService()

