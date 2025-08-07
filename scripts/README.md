# bAIt-Chat Scripts

Convenience scripts for running bAIt-Chat services locally or with Docker.

## Local Development Scripts

### `install-deps.sh`
Install all dependencies for local development.
```bash
./scripts/install-deps.sh
```

### `demo.sh` 
Start the complete demo with all services (Redis, QServer, Backend, Frontend).
```bash
./scripts/demo.sh
```

### Individual Service Scripts

#### `start-backend.sh`
Start only the FastAPI backend server.
```bash
./scripts/start-backend.sh
# Backend available at: http://localhost:8000
```

#### `start-frontend.sh`
Start only the Streamlit frontend.
```bash  
./scripts/start-frontend.sh
# Frontend available at: http://localhost:8501
```

#### `start-qserver.sh`
Start QServer with the test instrument.
```bash
./scripts/start-qserver.sh
# QServer available at: http://localhost:60610
```

#### `stop-qserver.sh`
Stop the QServer gracefully.
```bash
./scripts/stop-qserver.sh
```

## Docker Scripts

### `docker-up.sh`
Start all services using Docker Compose.
```bash
./scripts/docker-up.sh
```

### `docker-down.sh`
Stop all Docker services.
```bash
./scripts/docker-down.sh

# Remove volumes (data will be lost)
./scripts/docker-down.sh -v
```

### `docker-logs.sh`
View logs from Docker services.
```bash
# All services
./scripts/docker-logs.sh

# Specific service
./scripts/docker-logs.sh backend
./scripts/docker-logs.sh frontend
./scripts/docker-logs.sh qserver
./scripts/docker-logs.sh redis
```

## Service URLs

| Service | Local | Docker |
|---------|-------|--------|
| Frontend | http://localhost:8501 | http://localhost:8501 |
| Backend API | http://localhost:8000 | http://localhost:8000 |
| API Docs | http://localhost:8000/docs | http://localhost:8000/docs |
| QServer | http://localhost:60610 | http://localhost:60610 |
| Redis | localhost:6379 | localhost:6379 |

## Prerequisites

### Local Development
- Python 3.8+
- Redis server (`sudo apt install redis-server`)
- Optional: LMStudio for AI features

### Docker
- Docker and Docker Compose
- Optional: LMStudio running on host for AI features

## Environment Configuration

Copy and customize `.env` file:
```bash
cp .env.example .env
# Edit .env with your settings
```

Key settings:
- `LMSTUDIO_BASE_URL`: LMStudio API endpoint
- `QSERVER_URL`: QServer endpoint
- `DEBUG`: Enable debug mode