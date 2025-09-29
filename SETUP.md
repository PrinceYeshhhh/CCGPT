# CustomerCareGPT Setup Guide

This guide will help you set up and run CustomerCareGPT on your local machine or production server.

## Prerequisites

- Docker and Docker Compose
- Git
- A Google Gemini API key

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd CustomerCareGPT
```

### 2. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/customercaregpt
REDIS_URL=redis://redis:6379

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here

# Environment
ENVIRONMENT=development

# Frontend Configuration
REACT_APP_API_URL=https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1

# File Upload Settings
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=pdf,docx,csv

# Vector Database Settings
CHROMA_PERSIST_DIRECTORY=./chroma_db

# CORS Settings
CORS_ORIGINS=https://customercaregpt-frontend.vercel.app,https://customercaregpt-frontend-git-main.vercel.app
```

### 3. Get a Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and add it to your `.env` file

### 4. Generate a Secret Key

Generate a secure secret key for JWT tokens:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add this to your `.env` file as `SECRET_KEY`.

### 5. Run with Docker Compose

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis cache
- FastAPI backend
- React frontend
- Nginx reverse proxy

### 6. Access the Application

- **Admin Dashboard**: https://customercaregpt-frontend.vercel.app
- **API Documentation**: https://customercaregpt-backend-xxxxx-uc.a.run.app/api/docs
- **Health Check**: https://customercaregpt-backend-xxxxx-uc.a.run.app/health

## Development Setup

If you want to run the services individually for development:

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

## Production Deployment

### 1. Environment Configuration

Update your `.env` file for production:

```env
ENVIRONMENT=production
REACT_APP_API_URL=https://your-domain.com
CORS_ORIGINS=https://your-domain.com
```

### 2. SSL Configuration

For production, you'll need SSL certificates. Place them in the `ssl/` directory:

```
ssl/
├── cert.pem
└── key.pem
```

Update `nginx.conf` to use HTTPS:

```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... rest of configuration
}
```

### 3. Database Migration

Run database migrations:

```bash
docker-compose exec backend alembic upgrade head
```

### 4. Deploy

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Usage

### 1. Create an Account

1. Go to https://customercaregpt-frontend.vercel.app
2. Click "Create account"
3. Fill in your details
4. Sign in

### 2. Upload Documents

1. Go to the Documents page
2. Drag and drop PDF, DOCX, or CSV files
3. Wait for processing to complete

### 3. Create Embed Code

1. Go to the Embed Codes page
2. Click "Create Embed Code"
3. Configure your widget settings
4. Copy the embed code

### 4. Embed on Your Website

Add the embed code to your website:

```html
<script>
  window.CustomerCareGPTConfig = {
    codeId: 'your-embed-code-id',
    title: 'Customer Support',
    primaryColor: '#007bff'
  };
</script>
<script src="https://customercaregpt-backend-xxxxx-uc.a.run.app/widget/widget.js"></script>
```

## API Usage

### Authentication

All API endpoints require authentication. Include the JWT token in the Authorization header:

```bash
curl -H "Authorization: Bearer your-jwt-token" \
     https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1/documents/
```

### Upload Document

```bash
curl -X POST \
     -H "Authorization: Bearer your-jwt-token" \
     -F "file=@document.pdf" \
     -F "title=My Document" \
     https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1/documents/upload
```

### Send Chat Message

```bash
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello, how can I help you?"}' \
     https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1/chat/message
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running
   - Check DATABASE_URL in .env

2. **Gemini API Error**
   - Verify your API key is correct
   - Check API quota limits

3. **File Upload Fails**
   - Check file size limits
   - Ensure file type is supported

4. **Widget Not Loading**
   - Check CORS settings
   - Verify embed code ID

### Logs

View logs for each service:

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
```

### Reset Database

To reset the database:

```bash
docker-compose down -v
docker-compose up -d
```

## Security Considerations

1. **Change Default Passwords**: Update database passwords in production
2. **Use HTTPS**: Always use SSL in production
3. **API Rate Limiting**: Configure appropriate rate limits
4. **File Upload Security**: Validate file types and sizes
5. **CORS Configuration**: Restrict CORS origins in production

## Monitoring

### Health Checks

- Backend: https://customercaregpt-backend-xxxxx-uc.a.run.app/health
- Frontend: https://customercaregpt-frontend.vercel.app
- Database: Check container status

### Metrics

Monitor these key metrics:
- Response times
- Error rates
- File processing success rate
- Chat session duration
- API usage

## Support

For issues and questions:
1. Check the logs
2. Review this documentation
3. Check the API documentation at `/api/docs`
4. Create an issue in the repository

## License

Proprietary - All rights reserved
