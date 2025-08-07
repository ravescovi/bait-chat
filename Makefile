# Makefile for bAIt-Chat development

# Variables
PYTHON := python3
PIP := pip
PROJECT_NAME := bait-chat
BACKEND_DIR := backend
UI_DIR := ui
TESTS_DIR := tests

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

.PHONY: help install install-dev test test-unit test-integration lint format type-check clean run-backend run-frontend run-dev docker-build docker-up docker-down logs setup

# Default target
help: ## Show this help message
	@echo "$(GREEN)bAIt-Chat Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

# Installation
install: ## Install production dependencies
	@echo "$(GREEN)Installing production dependencies...$(NC)"
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	@echo "$(GREEN)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-asyncio black isort flake8 mypy jupyter

# Setup
setup: ## Complete project setup
	@echo "$(GREEN)Setting up bAIt-Chat development environment...$(NC)"
	cp .env.example .env
	mkdir -p logs vector_db knowledge_base/{bits_devices,plans,documentation}
	$(MAKE) install-dev
	@echo "$(GREEN)Setup complete! Edit .env file with your configuration.$(NC)"

# Code Quality
lint: ## Run linting checks
	@echo "$(GREEN)Running linting checks...$(NC)"
	flake8 $(BACKEND_DIR) $(UI_DIR) $(TESTS_DIR) --max-line-length=100 --ignore=E203,W503
	@echo "$(GREEN)Linting complete$(NC)"

format: ## Format code with black and isort
	@echo "$(GREEN)Formatting code...$(NC)"
	black $(BACKEND_DIR) $(UI_DIR) $(TESTS_DIR) --line-length=100
	isort $(BACKEND_DIR) $(UI_DIR) $(TESTS_DIR) --profile=black
	@echo "$(GREEN)Code formatting complete$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(GREEN)Running type checks...$(NC)"
	mypy $(BACKEND_DIR) --ignore-missing-imports --disable-error-code=import
	@echo "$(GREEN)Type checking complete$(NC)"

# Testing
test: ## Run all tests
	@echo "$(GREEN)Running all tests...$(NC)"
	PYTHONPATH=. pytest $(TESTS_DIR) -v --tb=short
	@echo "$(GREEN)All tests complete$(NC)"

test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	PYTHONPATH=. pytest $(TESTS_DIR) -v --tb=short -m "not integration and not slow"

test-integration: ## Run integration tests
	@echo "$(GREEN)Running integration tests...$(NC)"
	PYTHONPATH=. pytest $(TESTS_DIR) -v --tb=short -m "integration"

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	PYTHONPATH=. pytest $(TESTS_DIR) --cov=$(BACKEND_DIR) --cov-report=html --cov-report=term

# Development servers
run-backend: ## Run FastAPI backend in development mode
	@echo "$(GREEN)Starting FastAPI backend...$(NC)"
	cd $(BACKEND_DIR) && uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-frontend: ## Run Streamlit frontend
	@echo "$(GREEN)Starting Streamlit frontend...$(NC)"
	streamlit run $(UI_DIR)/streamlit_app.py --server.port 8501

run-dev: ## Run both backend and frontend (requires tmux)
	@echo "$(GREEN)Starting development environment...$(NC)"
	@if command -v tmux >/dev/null 2>&1; then \
		tmux new-session -d -s $(PROJECT_NAME) 'make run-backend'; \
		tmux split-window -h 'make run-frontend'; \
		tmux attach-session -t $(PROJECT_NAME); \
	else \
		echo "$(RED)tmux is required to run both services. Install tmux or run services separately.$(NC)"; \
		echo "Run 'make run-backend' and 'make run-frontend' in separate terminals."; \
	fi

# Docker commands
docker-build: ## Build Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	docker-compose build

docker-up: ## Start all services with Docker Compose
	@echo "$(GREEN)Starting Docker services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started. Access:$(NC)"
	@echo "  Backend API: http://localhost:8000"
	@echo "  Frontend UI: http://localhost:8501"
	@echo "  API Docs: http://localhost:8000/api/docs"

docker-dev: ## Start development environment with Docker
	@echo "$(GREEN)Starting development environment...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.override.yml up

docker-local-llm: ## Start with local LLM (Ollama)
	@echo "$(GREEN)Starting with local LLM support...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.local-llm.yml up -d
	@echo "$(GREEN)Services started with Ollama. Initializing models...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.local-llm.yml --profile init up ollama-init

docker-gpu: ## Start with GPU-enabled local LLM
	@echo "$(GREEN)Starting with GPU-enabled local LLM...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.local-llm.yml --profile gpu up -d

docker-down: ## Stop all Docker services
	@echo "$(GREEN)Stopping Docker services...$(NC)"
	docker-compose down

docker-clean: ## Clean up Docker images and volumes
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	docker-compose down -v --rmi local
	docker system prune -f

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs only
	docker-compose logs -f backend

logs-frontend: ## View frontend logs only
	docker-compose logs -f frontend

# Database and knowledge base
init-kb: ## Initialize knowledge base with sample data
	@echo "$(GREEN)Initializing knowledge base...$(NC)"
	mkdir -p knowledge_base/{bits_devices,plans,documentation}
	$(MAKE) create-sample-data
	@echo "$(GREEN)Knowledge base initialized$(NC)"

create-sample-data: ## Create sample data files
	@echo "Creating sample device definitions..."
	@cat > knowledge_base/bits_devices/example_devices.json << 'EOF'
{
  "motors": {
    "motor_x": {
      "type": "EpicsMotor",
      "description": "Sample X position motor",
      "units": "mm",
      "limits": [-10, 10],
      "precision": 0.001
    },
    "motor_y": {
      "type": "EpicsMotor", 
      "description": "Sample Y position motor",
      "units": "mm",
      "limits": [-5, 5],
      "precision": 0.001
    }
  },
  "detectors": {
    "pilatus": {
      "type": "PilatusDetector",
      "description": "Pilatus 300K area detector",
      "pixel_size": "172 μm",
      "dimensions": "487x619 pixels",
      "frame_rate": "20 Hz"
    },
    "i0": {
      "type": "IonChamber",
      "description": "Incident beam monitor",
      "gas": "N2",
      "voltage": "1500V"
    }
  }
}
EOF
	@echo "Creating sample plan documentation..."
	@cat > knowledge_base/plans/standard_plans.md << 'EOF'
# Standard Scan Plans

## scan(detectors, motor, start, stop, num)
Perform a continuous scan by moving a motor from start to stop position while collecting data from detectors at regular intervals.

**Parameters:**
- `detectors`: List of detector objects to read from
- `motor`: Motor object to move
- `start`: Starting position (motor units)
- `stop`: Ending position (motor units)  
- `num`: Number of data points to collect

**Example:**
```python
scan([pilatus, i0], motor_x, 0, 5, 51)
```

## count(detectors, num=1, delay=None)
Take repeated measurements at the current position to improve counting statistics.

**Parameters:**
- `detectors`: List of detector objects
- `num`: Number of measurements (default: 1)
- `delay`: Time between measurements in seconds

**Example:**
```python
count([pilatus, i0], num=10, delay=1.0)
```

## list_scan(detectors, motor, positions)
Scan through a list of specific motor positions.

**Parameters:**
- `detectors`: List of detector objects
- `motor`: Motor object to move
- `positions`: List of positions to visit

**Example:**
```python
list_scan([pilatus], motor_x, [0, 1.5, 3.2, 5.0])
```
EOF

# Maintenance
clean: ## Clean up temporary files
	@echo "$(GREEN)Cleaning up temporary files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache
	@echo "$(GREEN)Cleanup complete$(NC)"

# Deployment
deploy-staging: ## Deploy to staging environment
	@echo "$(GREEN)Deploying to staging...$(NC)"
	# Add staging deployment commands here

deploy-prod: ## Deploy to production
	@echo "$(RED)Production deployment requires manual approval$(NC)"
	@echo "Use: make deploy-prod-confirmed"

deploy-prod-confirmed: ## Deploy to production (confirmed)
	@echo "$(GREEN)Deploying to production...$(NC)"
	# Add production deployment commands here

# Health checks
check-services: ## Check if all services are running
	@echo "$(GREEN)Checking service health...$(NC)"
	@curl -f http://localhost:8000/health >/dev/null 2>&1 && echo "✓ Backend API: Running" || echo "✗ Backend API: Not running"
	@curl -f http://localhost:8501 >/dev/null 2>&1 && echo "✓ Frontend UI: Running" || echo "✗ Frontend UI: Not running"
	@curl -f http://localhost:11434/api/version >/dev/null 2>&1 && echo "✓ Ollama: Running" || echo "✗ Ollama: Not running"

# Local LLM utilities
ollama-status: ## Check Ollama status and list models
	@echo "$(GREEN)Checking Ollama status...$(NC)"
	@curl -s http://localhost:11434/api/version 2>/dev/null || echo "Ollama not running"
	@echo "Available models:"
	@curl -s http://localhost:11434/api/tags 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "No models found"

ollama-pull: ## Pull a model (usage: make ollama-pull MODEL=llama2)
	@echo "$(GREEN)Pulling model: $(MODEL)...$(NC)"
	@curl -X POST http://localhost:11434/api/pull -d '{"name":"$(MODEL)"}' || echo "Failed to pull model"

ollama-models: ## List all available models
	@curl -s http://localhost:11434/api/tags | python3 -m json.tool

test-local-llm: ## Test local LLM functionality
	@echo "$(GREEN)Testing local LLM...$(NC)"
	@curl -X POST http://localhost:8000/explain \
		-H "Content-Type: application/json" \
		-d '{"plan_name": "scan"}' | python3 -m json.tool

# Documentation
docs: ## Generate API documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	@echo "API documentation available at: http://localhost:8000/api/docs"
	@echo "ReDoc documentation at: http://localhost:8000/api/redoc"

# Quick development workflow
quick-check: ## Quick development checks (format, lint, test)
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) test-unit

# Environment info
env-info: ## Show environment information
	@echo "$(GREEN)Environment Information:$(NC)"
	@echo "Python version: $$($(PYTHON) --version)"
	@echo "Pip version: $$($(PIP) --version)"
	@echo "Project directory: $$(pwd)"
	@echo "Backend directory: $(BACKEND_DIR)"
	@echo "UI directory: $(UI_DIR)"
	@echo "Tests directory: $(TESTS_DIR)"

# Initialize everything for new developers
bootstrap: ## Bootstrap complete development environment
	@echo "$(GREEN)Bootstrapping bAIt-Chat development environment...$(NC)"
	$(MAKE) setup
	$(MAKE) init-kb
	$(MAKE) docker-build
	@echo "$(GREEN)Bootstrap complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "1. Edit .env file with your API keys"
	@echo "2. Run 'make docker-up' to start services"
	@echo "3. Access the application at http://localhost:8501"
	@echo "4. API documentation at http://localhost:8000/api/docs"