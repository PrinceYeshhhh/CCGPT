.PHONY: help dev dev-backend dev-frontend build up down logs clean test lint

# Default target
help:
	@echo "Available commands:"
	@echo "  dev          - Start all services in development mode"
	@echo "  dev-backend  - Start only backend in development mode"
	@echo "  dev-frontend - Start only frontend in development mode"
	@echo "  build        - Build all Docker images"
	@echo "  up           - Start all services with docker-compose"
	@echo "  down         - Stop all services"
	@echo "  logs         - Show logs for all services"
	@echo "  clean        - Clean up containers and volumes"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting"

# Development commands
dev:
	docker-compose up --build

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# Docker commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

# Production commands
prod:
	docker-compose -f docker-compose.prod.yml up --build

prod-down:
	docker-compose -f docker-compose.prod.yml down

# Testing and linting
test:
	cd backend && python -m pytest
	cd frontend && npm test

lint:
	cd backend && python -m flake8 app/
	cd frontend && npm run lint

# Database commands
db-migrate:
	cd backend && alembic upgrade head

db-revision:
	cd backend && alembic revision --autogenerate -m "$(message)"

# Install dependencies
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# Worker commands
worker:
	cd backend && python worker.py

worker-dev:
	cd backend && rq worker -u $$REDIS_URL ingest --verbose

# File processing tests
test-files:
	cd backend && python -m pytest tests/test_file_processing.py -v
