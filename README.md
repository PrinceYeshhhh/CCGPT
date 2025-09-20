# CustomerCareGPT

An intelligent, scalable digital SaaS product designed to automate customer support for small businesses with minimal effort.

## Features

- **Secure Authentication**: JWT-based authentication with refresh tokens
- **User Management**: Complete user registration, login, and profile management
- **File Upload & Processing**: Upload FAQs in PDF, DOCX, or CSV format
- **AI-Powered Responses**: Powered by Google Gemini API with RAG (Retrieval-Augmented Generation)
- **Embeddable Chat Widget**: Lightweight JavaScript widget for easy website integration
- **Admin Dashboard**: Clean interface for file management and analytics
- **Multi-tenant Architecture**: Support for multiple businesses
- **White Label Ready**: Perfect for agencies and resellers

## Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **ChromaDB**: Vector database for embeddings storage
- **Google Gemini API**: AI model for generating responses
- **PostgreSQL**: Relational database for user data and metadata
- **Redis**: Caching and session management

### Frontend
- **React**: Admin dashboard and management interface
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Modern, responsive styling
- **Vite**: Fast build tool and development server

### Infrastructure
- **Docker**: Containerization
- **Nginx**: Reverse proxy and static file serving
- **AWS/GCP**: Cloud deployment ready

## Project Structure

```
CustomerCareGPT/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React admin dashboard
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── utils/          # Utility functions
│   ├── package.json
│   └── Dockerfile
├── widget/                 # Embeddable chat widget
│   ├── src/
│   └── dist/
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CustomerCareGPT
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your actual values
   ```

3. **Required Environment Variables**
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `JWT_SECRET`: Secret key for JWT tokens (use a strong, random string)
   - `DATABASE_URL`: PostgreSQL connection string
   - `REDIS_URL`: Redis connection string
   - `CHROMA_URL`: ChromaDB connection string
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT access token expiration (default: 60)
   - `REFRESH_TOKEN_EXPIRE_DAYS`: JWT refresh token expiration (default: 7)

### Development

#### Option 1: Docker Compose (Recommended)
```bash
# Start all services
make dev
# or
docker-compose up --build

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

#### Option 2: Local Development
```bash
# Install dependencies
make install

# Start backend
make dev-backend

# Start frontend (in another terminal)
make dev-frontend
```

### Production

```bash
# Build and start production services
make prod

# Stop production services
make prod-down
```

### Available Services

- **Frontend**: http://localhost:5173 (React + Vite)
- **Backend API**: http://localhost:8000 (FastAPI)
- **API Documentation**: http://localhost:8000/api/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **ChromaDB**: localhost:8001

### Database Management

```bash
# Run migrations
make db-migrate

# Create new migration
make db-revision message="your migration message"
```

### Authentication

The application includes a complete authentication system:

- **JWT-based authentication** with access and refresh tokens
- **Secure password hashing** using bcrypt
- **Token refresh** mechanism for seamless user experience
- **Protected routes** that require authentication
- **User registration and login** with form validation

#### Authentication Endpoints

- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login with email and password
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/logout` - Logout user

#### Frontend Authentication

- **Login Page** (`/login`) - User login form
- **Register Page** (`/register`) - User registration form
- **Protected Routes** - All dashboard pages require authentication
- **Automatic Token Refresh** - Tokens are refreshed automatically
- **Logout Functionality** - Secure logout with token cleanup

### File Upload & Processing

The application includes a robust file processing pipeline:

- **Multi-format support**: PDF, DOCX, CSV, XLSX files
- **Background processing** with Redis Queue (RQ)
- **Text extraction** and intelligent chunking
- **Workspace-scoped** document management
- **Configurable storage** (local filesystem or S3)

#### File Processing Pipeline

1. **Upload**: Files are validated and stored securely
2. **Background Processing**: Text extraction and chunking happen asynchronously
3. **Chunking**: Text is split into 400-700 token chunks with overlap
4. **Storage**: Chunks are stored in the database with metadata
5. **Embedding**: Chunks are queued for vector embedding (future step)

#### File Upload Endpoints

- `POST /api/v1/documents/upload` - Upload a document
- `GET /api/v1/documents/` - List user's documents
- `GET /api/v1/documents/{document_id}` - Get document details
- `GET /api/v1/documents/{document_id}/chunks` - Get document chunks
- `DELETE /api/v1/documents/{document_id}` - Soft delete document
- `GET /api/v1/documents/jobs/{job_id}` - Check processing job status

#### Running the Background Worker

```bash
# Start Redis server
redis-server

# Start the worker (in a separate terminal)
cd backend
python worker.py

# Or using RQ directly
rq worker -u $REDIS_URL ingest
```

#### File Upload Example

```bash
# Upload a PDF file
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@sample.pdf"

# Response
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "job_id": "abc123",
  "status": "uploaded",
  "message": "Document uploaded successfully"
}

# Check job status
curl -X GET "http://localhost:8000/api/v1/documents/jobs/abc123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get document chunks
curl -X GET "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/chunks" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Development Commands

```bash
# View logs
make logs

# Run tests
make test

# Run linting
make lint

# Clean up
make clean
```

## Production Deployment

### Production Readiness Features

- **Structured Logging**: JSON-formatted logs with request tracing
- **Health Checks**: `/health` and `/ready` endpoints for Kubernetes probes
- **Metrics**: Prometheus metrics for monitoring and alerting
- **Rate Limiting**: Redis-backed rate limiting with configurable limits
- **Caching**: Multi-layer caching for improved performance
- **Security**: Comprehensive security hardening and RBAC
- **Scaling**: Horizontal pod autoscaling and worker scaling
- **Backup**: Automated backup strategies for all data stores
- **Monitoring**: Full observability stack with Grafana dashboards

### Quick Production Setup

```bash
# 1. Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# 2. Deploy with Kubernetes
kubectl apply -f k8s/

# 3. Check deployment status
kubectl get pods
kubectl get services
```

### Production Checklist

- [ ] All secrets stored in Kubernetes secrets or external secret manager
- [ ] Database backups scheduled and tested
- [ ] ChromaDB backup strategy implemented
- [ ] Monitoring and alerting configured
- [ ] Log aggregation set up
- [ ] SSL/TLS certificates configured
- [ ] Network policies applied
- [ ] Pod security policies configured
- [ ] RBAC properly configured
- [ ] Resource limits and requests set
- [ ] HPA configured for auto-scaling
- [ ] Health checks configured
- [ ] Rate limiting enabled
- [ ] Caching layer configured
- [ ] CDN configured for static assets

### Monitoring & Observability

- **Health Checks**: `GET /health` (liveness), `GET /ready` (readiness)
- **Metrics**: `GET /metrics` (Prometheus format)
- **Logs**: Structured JSON logs with request tracing
- **Alerts**: Configurable alerts for error rates, resource usage, and downtime

### Scaling

- **Backend API**: 3-10 replicas with CPU/memory-based autoscaling
- **Workers**: 2-5 replicas with queue-length-based autoscaling
- **Database**: Read replicas and connection pooling
- **Cache**: Redis cluster mode for high availability

### Security

- **Network Policies**: Restrictive pod-to-pod communication
- **Pod Security Policies**: Non-root containers with minimal privileges
- **RBAC**: Role-based access control for Kubernetes resources
- **Secrets Management**: External secret management integration
- **TLS**: End-to-end encryption with automatic certificate management

For detailed production deployment instructions, see [Production README](docs/PRODUCTION_README.md).

## Testing

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.yml up -d
pytest tests/integration/ -v
```

### Test Coverage

- **Unit Tests**: Core business logic and utilities
- **Integration Tests**: API endpoints and database interactions
- **End-to-End Tests**: Complete user workflows
- **Performance Tests**: Load testing and benchmarking

## CI/CD Pipeline

The project includes a comprehensive CI/CD pipeline with:

- **Automated Testing**: Linting, type checking, and unit tests
- **Security Scanning**: Vulnerability scanning with Trivy
- **Docker Builds**: Multi-stage builds for production optimization
- **Deployment**: Automated deployment to staging and production
- **Monitoring**: Health checks and rollback capabilities

See `.github/workflows/ci.yml` for the complete pipeline configuration.

## License

Proprietary - All rights reserved
