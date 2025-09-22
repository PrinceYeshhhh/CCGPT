# Production-Grade RAG System Documentation

## 🚀 Overview

The Production-Grade RAG (Retrieval-Augmented Generation) system is a comprehensive, enterprise-ready solution that provides advanced file processing, intelligent chunking, vector search, and AI-powered response generation capabilities.

## 🏗️ Architecture

### Core Components

1. **ProductionFileProcessor** - Advanced file processing with semantic chunking
2. **ProductionVectorService** - High-performance vector search with multiple strategies
3. **ProductionRAGService** - Unified RAG pipeline with advanced capabilities

### Key Features

- **Multi-format Support**: PDF, DOCX, TXT, MD, CSV, XLSX, JSON, HTML
- **Advanced Chunking**: Semantic, hierarchical, adaptive, and fixed-size strategies
- **Hybrid Search**: Vector similarity + BM25 + reranking
- **Multiple Retrieval Modes**: Similarity, hybrid, semantic, multi-query, fusion
- **Response Styles**: Conversational, technical, summarized, detailed, step-by-step
- **Performance Optimization**: Redis caching, parallel processing, async operations
- **Production Monitoring**: Health checks, performance stats, error tracking

## 📁 File Structure

```
backend/app/services/
├── production_rag_system.py      # Core file processing and chunking
├── production_vector_service.py  # Vector search and retrieval
├── production_rag_service.py     # Unified RAG pipeline
└── test_production_rag_system.py # Comprehensive tests

backend/app/api/v1/endpoints/
└── production_rag.py             # API endpoints

backend/
├── requirements.txt              # Updated dependencies
└── PRODUCTION_RAG_SYSTEM.md     # This documentation
```

## 🔧 Installation & Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Initialize NLTK Data

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('wordnet')
```

### 3. Configure Environment Variables

```env
# Vector Database
CHROMA_DB_PATH=./data/chroma_db

# Redis Cache
REDIS_URL=redis://localhost:6379

# Google Gemini
GOOGLE_API_KEY=your_gemini_api_key

# File Upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB
```

## 🚀 Usage

### 1. Basic File Processing

```python
from app.services.production_rag_service import ProductionRAGService, RAGConfig
from app.services.production_rag_system import ChunkingStrategy

# Initialize service
rag_service = ProductionRAGService(db)

# Process a file
result = await rag_service.process_file(
    file_path="document.pdf",
    content_type="application/pdf",
    workspace_id="workspace_123",
    config=RAGConfig(
        chunk_size=1000,
        chunk_overlap=200,
        chunking_strategy=ChunkingStrategy.SEMANTIC
    )
)
```

### 2. Query Processing

```python
# Process a query
response = await rag_service.process_query(
    query="What is the main topic of the document?",
    workspace_id="workspace_123",
    config=RAGConfig(
        search_mode=SearchMode.HYBRID,
        top_k=10,
        response_style=ResponseStyle.TECHNICAL,
        use_reranking=True
    )
)

print(response.answer)
print(response.sources)
```

### 3. API Usage

#### Process File
```bash
curl -X POST "http://localhost:8000/api/v1/production-rag/process-file" \
  -F "file=@document.pdf" \
  -F "workspace_id=workspace_123" \
  -F "chunking_strategy=semantic"
```

#### Query Documents
```bash
curl -X POST "http://localhost:8000/api/v1/production-rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic?",
    "workspace_id": "workspace_123",
    "search_mode": "hybrid",
    "response_style": "technical"
  }'
```

## 🔍 Advanced Features

### 1. Chunking Strategies

#### Semantic Chunking
```python
config = RAGConfig(
    chunking_strategy=ChunkingStrategy.SEMANTIC
)
```
- Groups related content together
- Preserves semantic meaning
- Best for natural language content

#### Hierarchical Chunking
```python
config = RAGConfig(
    chunking_strategy=ChunkingStrategy.HIERARCHICAL
)
```
- Respects document structure
- Maintains section relationships
- Best for structured documents

#### Adaptive Chunking
```python
config = RAGConfig(
    chunking_strategy=ChunkingStrategy.ADAPTIVE
)
```
- Adjusts chunk size based on content type
- Optimizes for different content types
- Best for mixed content

### 2. Search Modes

#### Hybrid Search
```python
config = RAGConfig(
    search_mode=SearchMode.HYBRID
)
```
- Combines vector similarity and BM25
- Best overall performance
- Recommended for most use cases

#### Semantic Search
```python
config = RAGConfig(
    search_mode=SearchMode.SEMANTIC
)
```
- Uses query expansion and reranking
- Best for complex queries
- Higher computational cost

#### Fusion Search
```python
config = RAGConfig(
    search_mode=SearchMode.FUSION
)
```
- Combines multiple search methods
- Best accuracy
- Highest computational cost

### 3. Response Styles

#### Technical Style
```python
config = RAGConfig(
    response_style=ResponseStyle.TECHNICAL
)
```
- Detailed, technical responses
- Includes specific details and examples
- Best for technical documentation

#### Conversational Style
```python
config = RAGConfig(
    response_style=ResponseStyle.CONVERSATIONAL
)
```
- Chat-like, friendly responses
- Natural language flow
- Best for general queries

#### Summarized Style
```python
config = RAGConfig(
    response_style=ResponseStyle.SUMMARIZED
)
```
- Concise, key-point responses
- Focuses on essential information
- Best for quick answers

## 📊 Performance Monitoring

### 1. Health Check

```python
# Check system health
health = await rag_service.health_check()
print(health)
```

### 2. Performance Stats

```python
# Get performance statistics
stats = await rag_service.get_performance_stats()
print(stats)
```

### 3. API Health Check

```bash
curl -X GET "http://localhost:8000/api/v1/production-rag/health"
```

## 🧪 Testing

### Run Tests

```bash
cd backend
python -m pytest test_production_rag_system.py -v
```

### Test Coverage

```bash
python -m pytest test_production_rag_system.py --cov=app.services.production_rag_system --cov=app.services.production_vector_service --cov=app.services.production_rag_service
```

## 🔧 Configuration

### RAG Configuration Options

```python
@dataclass
class RAGConfig:
    # File processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC
    
    # Search configuration
    search_mode: SearchMode = SearchMode.HYBRID
    top_k: int = 10
    similarity_threshold: float = 0.7
    use_reranking: bool = True
    rerank_top_k: int = 5
    
    # Generation configuration
    response_style: ResponseStyle = ResponseStyle.CONVERSATIONAL
    max_context_length: int = 4000
    include_sources: bool = True
    include_citations: bool = True
    stream_response: bool = False
    
    # Performance
    use_cache: bool = True
    parallel_processing: bool = True
```

### Search Configuration Options

```python
@dataclass
class SearchConfig:
    top_k: int = 10
    similarity_threshold: float = 0.7
    search_mode: SearchMode = SearchMode.HYBRID
    use_reranking: bool = True
    rerank_top_k: int = 5
    use_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    boost_important: bool = True
    filter_by_metadata: Optional[Dict[str, Any]] = None
```

## 🚨 Error Handling

### Common Errors

1. **File Processing Errors**
   - Unsupported file type
   - File too large
   - Corrupted file

2. **Search Errors**
   - No results found
   - Vector database unavailable
   - Embedding generation failed

3. **Generation Errors**
   - Gemini API unavailable
   - Context too long
   - Invalid response format

### Error Response Format

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🔒 Security Considerations

### 1. File Upload Security
- File type validation
- File size limits
- Malware scanning (recommended)

### 2. Data Privacy
- Workspace isolation
- Data encryption at rest
- Secure API endpoints

### 3. Access Control
- Authentication required
- Workspace-based access
- Rate limiting

## 📈 Scalability

### 1. Horizontal Scaling
- Stateless service design
- Load balancer ready
- Database connection pooling

### 2. Caching Strategy
- Redis for search results
- Embedding caching
- Response caching

### 3. Performance Optimization
- Async operations
- Parallel processing
- Connection pooling

## 🛠️ Troubleshooting

### Common Issues

1. **ChromaDB Connection Issues**
   ```bash
   # Check ChromaDB status
   curl -X GET "http://localhost:8000/api/v1/production-rag/health"
   ```

2. **Redis Connection Issues**
   ```bash
   # Check Redis status
   redis-cli ping
   ```

3. **Memory Issues**
   - Reduce chunk size
   - Enable parallel processing
   - Use streaming responses

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 API Reference

### Endpoints

- `POST /api/v1/production-rag/process-file` - Process and index file
- `POST /api/v1/production-rag/query` - Query documents
- `POST /api/v1/production-rag/search` - Search documents only
- `GET /api/v1/production-rag/workspace/{workspace_id}/stats` - Get workspace stats
- `GET /api/v1/production-rag/health` - Health check
- `DELETE /api/v1/production-rag/workspace/{workspace_id}` - Delete workspace
- `POST /api/v1/production-rag/workspace/{workspace_id}/batch-process` - Batch process files
- `GET /api/v1/production-rag/workspace/{workspace_id}/documents` - List workspace documents

### Request/Response Schemas

See `app/schemas/rag.py` for detailed schemas.

## 🤝 Contributing

### Development Setup

1. Clone repository
2. Install dependencies
3. Set up environment variables
4. Run tests
5. Start development server

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings
- Write tests

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the test cases
- Contact the development team

---

**Last Updated**: January 2024
**Version**: 1.0.0
**Status**: Production Ready ✅
