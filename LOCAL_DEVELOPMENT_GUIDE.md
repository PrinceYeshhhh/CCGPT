# 🏠 CustomerCareGPT Local Development Guide

This guide helps you set up and run CustomerCareGPT locally for development and testing.

## 🎯 Architecture

- **Frontend**: Cloud (Vercel) - https://customercaregpt-frontend.vercel.app
- **Backend**: Local (Docker) - http://localhost:8000
- **Database**: Local SQLite - `./dev.db`
- **Redis**: Local Docker - `localhost:6379`
- **ChromaDB**: Local Docker - `http://localhost:8001`

## 🚀 Quick Start

### Prerequisites

1. **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop/)
2. **Python 3.8+** (for testing scripts)
3. **Git** (if not already installed)

### 1. Start Local Services

**Windows:**
```bash
start_local.bat
```

**Linux/Mac:**
```bash
./start_local.sh
```

**Manual:**
```bash
docker-compose -f docker-compose.local.yml up -d
```

### 2. Test the Setup

```bash
python test_local.py
```

### 3. Access the Application

- **Frontend (Cloud)**: https://customercaregpt-frontend.vercel.app
- **Backend API (Local)**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔧 Configuration

### Backend Configuration

The backend uses these local configurations:

```bash
# Database
DATABASE_URL=sqlite:///./dev.db

# Redis
REDIS_URL=redis://localhost:6379

# ChromaDB
CHROMA_URL=http://localhost:8001

# CORS (allows cloud frontend)
CORS_ORIGINS=https://customercaregpt-frontend.vercel.app,http://localhost:3000

# URLs
PUBLIC_BASE_URL=http://localhost:8000
API_BASE_URL=http://localhost:8000
```

### Environment Variables

Copy the local environment template:

```bash
# Backend
cp backend/local.env backend/.env

# Frontend (if needed for local testing)
cp frontend/local.env frontend/.env.local
```

## 🧪 Testing

### Run All Tests

```bash
python test_local.py
```

### Test Individual Components

```bash
# Test backend health
curl http://localhost:8000/health

# Test API documentation
curl http://localhost:8000/docs

# Test CORS
curl -H "Origin: https://customercaregpt-frontend.vercel.app" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     http://localhost:8000/api/v1/auth/login
```

### Test with Frontend

1. Open https://customercaregpt-frontend.vercel.app
2. The frontend will automatically connect to your local backend
3. Test all features: registration, login, document upload, chat, etc.

## 📊 Monitoring

### View Logs

```bash
# All services
docker-compose -f docker-compose.local.yml logs -f

# Backend only
docker-compose -f docker-compose.local.yml logs -f backend

# Redis only
docker-compose -f docker-compose.local.yml logs -f redis

# ChromaDB only
docker-compose -f docker-compose.local.yml logs -f chromadb
```

### Debug Endpoints

- **Health Check**: http://localhost:8000/health
- **Debug Health**: http://localhost:8000/debug/health
- **Connectivity Test**: http://localhost:8000/debug/test-connectivity
- **Recent Errors**: http://localhost:8000/debug/errors

## 🛠️ Development

### Backend Development

1. **Edit Code**: Modify files in `backend/` directory
2. **Auto-reload**: Backend automatically reloads on file changes
3. **Database**: SQLite database is stored in `./dev.db`
4. **Uploads**: Files are stored in `./uploads/`

### Database Management

```bash
# Access SQLite database
sqlite3 dev.db

# Run migrations (if needed)
cd backend
alembic upgrade head
```

### Adding Dependencies

1. **Backend**: Add to `backend/requirements.txt`
2. **Rebuild**: `docker-compose -f docker-compose.local.yml build backend`
3. **Restart**: `docker-compose -f docker-compose.local.yml restart backend`

## 🐛 Troubleshooting

### Common Issues

#### Backend Won't Start

```bash
# Check logs
docker-compose -f docker-compose.local.yml logs backend

# Common fixes
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d
```

#### CORS Errors

The backend is configured to allow requests from:
- https://customercaregpt-frontend.vercel.app
- http://localhost:3000
- http://localhost:5173

If you see CORS errors, check the `CORS_ORIGINS` setting in `backend/app/core/config.py`.

#### Database Issues

```bash
# Reset database
rm dev.db
docker-compose -f docker-compose.local.yml restart backend
```

#### Port Conflicts

If ports 8000, 6379, or 8001 are in use:

1. **Stop conflicting services**
2. **Or modify ports in `docker-compose.local.yml`**

### Debug Mode

Enable debug mode for more detailed logs:

```bash
# In docker-compose.local.yml
environment:
  - DEBUG=true
  - LOG_LEVEL=DEBUG
```

## 🚀 Deployment

Once local development is complete:

1. **Test everything locally**
2. **Commit your changes**
3. **Deploy to cloud** using the existing cloud deployment scripts

## 📁 File Structure

```
CustomerCareGPT/
├── backend/                 # Backend code
│   ├── local.env           # Local environment template
│   └── .env               # Local environment (copy from local.env)
├── frontend/               # Frontend code (cloud)
├── docker-compose.local.yml # Local Docker setup
├── start_local.bat        # Windows startup script
├── start_local.sh         # Linux/Mac startup script
├── test_local.py          # Local testing script
└── LOCAL_DEVELOPMENT_GUIDE.md # This guide
```

## 🔗 Useful Commands

```bash
# Start services
docker-compose -f docker-compose.local.yml up -d

# Stop services
docker-compose -f docker-compose.local.yml down

# View logs
docker-compose -f docker-compose.local.yml logs -f

# Restart backend
docker-compose -f docker-compose.local.yml restart backend

# Rebuild backend
docker-compose -f docker-compose.local.yml build backend

# Test setup
python test_local.py

# Access backend shell
docker-compose -f docker-compose.local.yml exec backend bash

# Access Redis CLI
docker-compose -f docker-compose.local.yml exec redis redis-cli
```

## 🎉 Success!

You now have a complete local development environment where:
- ✅ Frontend runs in the cloud (Vercel)
- ✅ Backend runs locally (Docker)
- ✅ All services are connected and working
- ✅ You can develop and test locally
- ✅ Ready for cloud deployment when complete

Happy coding! 🚀
