import warnings
warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*")
"""
Enhanced embeddings service with multiple models and advanced features
"""

import asyncio
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import structlog
from functools import lru_cache
from enum import Enum
import json

# Enhanced embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# OpenAI embeddings (optional)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Hugging Face transformers (optional)
try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from app.core.config import settings

logger = structlog.get_logger()


class EmbeddingModel(Enum):
    """Available embedding models"""
    SENTENCE_TRANSFORMER_SMALL = "all-MiniLM-L6-v2"  # 384 dims, fast
    SENTENCE_TRANSFORMER_MEDIUM = "all-mpnet-base-v2"  # 768 dims, balanced
    SENTENCE_TRANSFORMER_LARGE = "all-MiniLM-L12-v2"  # 384 dims, better quality
    SENTENCE_TRANSFORMER_MULTILINGUAL = "paraphrase-multilingual-MiniLM-L12-v2"  # 384 dims, multilingual
    OPENAI_ADA = "text-embedding-ada-002"  # 1536 dims, OpenAI
    HUGGINGFACE_MULTILINGUAL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class EnhancedEmbeddingsService:
    """Enhanced embeddings service with multiple models and advanced features"""
    
    def __init__(self, 
                 model_name: str = "all-mpnet-base-v2",
                 cache_size: int = 1000,
                 batch_size: int = 32):
        self.model_name = model_name
        self.cache_size = cache_size
        self.batch_size = batch_size
        self.model = None
        self.tokenizer = None
        self.embedding_dimension = 768  # Default
        self.model_type = "sentence_transformers"
        
        # Cache for embeddings
        self._embedding_cache = {}
        
        # Initialize model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model"""
        try:
            # In testing, short-circuit to a lightweight fake model to avoid downloads
            if settings.ENVIRONMENT.lower() in ("testing", "test") or (str(getattr(settings, "DEBUG", False)).lower() == "true" and getattr(settings, "TESTING", False)):
                self._initialize_fallback_model()
                logger.info("Using fake sentence transformer model in TESTING mode", dimension=self.embedding_dimension)
                return
            if self.model_name.startswith("text-embedding-ada-002"):
                self._initialize_openai_model()
            elif self.model_name.startswith("sentence-transformers/"):
                self._initialize_huggingface_model()
            else:
                self._initialize_sentence_transformer_model()
                
            logger.info(
                "Enhanced embeddings service initialized",
                model=self.model_name,
                dimension=self.embedding_dimension,
                type=self.model_type
            )
        except Exception as e:
            logger.error("Failed to initialize embeddings model", error=str(e))
            # Fallback to basic model
            self._initialize_fallback_model()
    
    def _initialize_sentence_transformer_model(self):
        """Initialize SentenceTransformer model"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers not available")
        
        logger.info("Loading SentenceTransformer model", model=self.model_name)
        self.model = SentenceTransformer(self.model_name)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
        self.model_type = "sentence_transformers"
    
    def _initialize_openai_model(self):
        """Initialize OpenAI embeddings model"""
        if not OPENAI_AVAILABLE:
            raise ImportError("openai not available")
        
        self.model_name = "text-embedding-ada-002"
        self.embedding_dimension = 1536
        self.model_type = "openai"
        logger.info("OpenAI embeddings model initialized")
    
    def _initialize_huggingface_model(self):
        """Initialize Hugging Face transformers model"""
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers not available")
        
        logger.info("Loading Hugging Face model", model=self.model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.embedding_dimension = self.model.config.hidden_size
        self.model_type = "huggingface"
    
    def _initialize_fallback_model(self):
        """Initialize fallback model"""
        logger.warning("Using fallback embeddings model")
        self.model_name = "all-MiniLM-L6-v2"
        self.embedding_dimension = 384
        self.model_type = "fallback"
    
    @lru_cache(maxsize=1)
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dimension,
            "model_type": self.model_type,
            "cache_size": self.cache_size,
            "batch_size": self.batch_size
        }
    
    async def generate_embeddings(
        self, 
        texts: List[str], 
        batch_size: Optional[int] = None,
        normalize: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            normalize: Whether to normalize embeddings
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        batch_size = batch_size or self.batch_size
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = await self._generate_batch_embeddings(batch_texts, normalize)
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    async def generate_single_embedding(
        self, 
        text: str,
        normalize: bool = True
    ) -> List[float]:
        """Generate embedding for a single text"""
        # Check cache first
        cache_key = self._get_cache_key(text, normalize)
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        embeddings = await self.generate_embeddings([text], normalize=normalize)
        embedding = embeddings[0] if embeddings else []
        
        # Cache the result
        if len(self._embedding_cache) < self.cache_size:
            self._embedding_cache[cache_key] = embedding
        
        return embedding
    
    async def _generate_batch_embeddings(
        self, 
        texts: List[str],
        normalize: bool = True
    ) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        try:
            if self.model_type == "openai":
                return await self._generate_openai_embeddings(texts)
            elif self.model_type == "huggingface":
                return await self._generate_huggingface_embeddings(texts, normalize)
            else:  # sentence_transformers or fallback
                return await self._generate_sentence_transformer_embeddings(texts, normalize)
        except Exception as e:
            logger.error("Batch embedding generation failed", error=str(e))
            # Return zero embeddings as fallback
            return [[0.0] * self.embedding_dimension for _ in texts]
    
    async def _generate_sentence_transformer_embeddings(
        self, 
        texts: List[str],
        normalize: bool = True
    ) -> List[List[float]]:
        """Generate embeddings using SentenceTransformer"""
        if not self.model:
            # Fallback to basic model
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.embedding_dimension = 384
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, 
            lambda: self.model.encode(texts, normalize_embeddings=normalize)
        )
        
        return embeddings.tolist()
    
    async def _generate_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI not available")
        
        try:
            response = await openai.Embedding.acreate(
                input=texts,
                model=self.model_name
            )
            
            embeddings = [item["embedding"] for item in response["data"]]
            return embeddings
        except Exception as e:
            logger.error("OpenAI embedding generation failed", error=str(e))
            raise
    
    async def _generate_huggingface_embeddings(
        self, 
        texts: List[str],
        normalize: bool = True
    ) -> List[List[float]]:
        """Generate embeddings using Hugging Face transformers"""
        if not self.model or not self.tokenizer:
            raise ValueError("Hugging Face model not initialized")
        
        # Tokenize texts
        inputs = self.tokenizer(
            texts, 
            padding=True, 
            truncation=True, 
            return_tensors="pt",
            max_length=512
        )
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use mean pooling of last hidden state
            embeddings = outputs.last_hidden_state.mean(dim=1)
            
            if normalize:
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        
        return embeddings.tolist()
    
    def _get_cache_key(self, text: str, normalize: bool) -> str:
        """Generate cache key for text"""
        content = f"{text}:{normalize}:{self.model_name}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def compute_similarity(
        self, 
        text1: str, 
        text2: str
    ) -> float:
        """Compute cosine similarity between two texts"""
        emb1 = await self.generate_single_embedding(text1)
        emb2 = await self.generate_single_embedding(text2)
        
        return self._cosine_similarity(emb1, emb2)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def find_most_similar(
        self, 
        query_text: str, 
        candidate_texts: List[str],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find most similar texts to query"""
        query_embedding = await self.generate_single_embedding(query_text)
        candidate_embeddings = await self.generate_embeddings(candidate_texts)
        
        similarities = []
        for i, candidate_emb in enumerate(candidate_embeddings):
            similarity = self._cosine_similarity(query_embedding, candidate_emb)
            similarities.append((candidate_texts[i], similarity))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    async def cluster_embeddings(
        self, 
        texts: List[str],
        n_clusters: int = 5
    ) -> List[int]:
        """Cluster texts based on their embeddings"""
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            logger.warning("scikit-learn not available for clustering")
            return [0] * len(texts)
        
        embeddings = await self.generate_embeddings(texts)
        
        if len(embeddings) < n_clusters:
            return list(range(len(embeddings)))
        
        # Normalize embeddings
        scaler = StandardScaler()
        normalized_embeddings = scaler.fit_transform(embeddings)
        
        # Perform K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(normalized_embeddings)
        
        return cluster_labels.tolist()
    
    def clear_cache(self):
        """Clear the embedding cache"""
        self._embedding_cache.clear()
        logger.info("Embedding cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._embedding_cache),
            "max_cache_size": self.cache_size,
            "cache_hit_ratio": "N/A"  # Would need to track hits/misses
        }


# Global instances for different models
enhanced_embeddings_service = EnhancedEmbeddingsService(
    model_name="all-mpnet-base-v2",  # Better quality model
    cache_size=2000,
    batch_size=64
)

# Multilingual model for international content
multilingual_embeddings_service = EnhancedEmbeddingsService(
    model_name="paraphrase-multilingual-MiniLM-L12-v2",
    cache_size=1000,
    batch_size=32
)

# Fast model for real-time applications
fast_embeddings_service = EnhancedEmbeddingsService(
    model_name="all-MiniLM-L6-v2",
    cache_size=5000,
    batch_size=128
)
