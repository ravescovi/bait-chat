# bAIt-Chat: AI Assistant for Bluesky Beamline Control

bAIt-Chat is an intelligent AI-powered assistant for synchrotron beamlines using the Bluesky data acquisition framework. It features comprehensive **real-time instrument introspection**, QueueServer integration, and an intuitive chat interface for beamline operations, device control, and intelligent scan planning.

## 🚀 Quick Start

### Option 1: Local Installation
```bash
# Install dependencies and package
./scripts/install-deps.sh

# Start complete demo
./scripts/demo.sh
```

### Option 2: Docker
```bash
# Start all services with Docker
./scripts/docker-up.sh
```

### Option 3: Python Package
```bash
# Install with QServer support
pip install -e .[qserver]

# Start complete demo
bait-chat demo
```

### Access
- **Web Interface**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs

## 💡 Available Scripts

```bash
# Local Development
./scripts/demo.sh              # Full demo with all services
./scripts/start-backend.sh     # Backend only
./scripts/start-frontend.sh    # Frontend only
./scripts/start-qserver.sh     # QServer only

# Docker
./scripts/docker-up.sh         # Start with Docker Compose
./scripts/docker-down.sh       # Stop Docker services
./scripts/docker-logs.sh       # View logs

# CLI Commands
bait-chat demo                 # Full demo with QServer
bait-chat backend              # Backend only
bait-chat frontend             # Frontend only
bait-chat status              # Check services
```

## 📋 Prerequisites

- Python 3.8+
- Redis (for QServer): `sudo apt install redis-server`
- Optional: LMStudio for local AI

## 🔬 Core Features

### 🧠 AI-Powered Chat Interface
- **Natural Language Processing**: Ask questions about devices, plans, and operations
- **Context-Aware Responses**: AI understands your beamline configuration
- **LMStudio Integration**: Local AI with privacy and customization

### 🔍 Real-Time Instrument Introspection
- **Live Device Monitoring**: Real-time positions, limits, and connection status
- **Smart Device Categorization**: Automatic classification (motors, detectors, shutters)
- **Environment Status**: QServer environment monitoring and health checks

### 📊 Intelligent Plan Analysis
- **Comprehensive Plan Discovery**: Analyze all available Bluesky plans
- **Parameter Intelligence**: Type inference, validation rules, and smart suggestions
- **Complexity Assessment**: Automatic difficulty rating (beginner/intermediate/advanced)
- **Smart Recommendations**: Personalized plan suggestions based on available devices
- **Usage Analytics**: Track scan history and identify patterns

### 🎯 Advanced Plan Features
- **Parameter Validation**: Real-time validation with type checking
- **Prerequisites Detection**: Automatic requirement analysis
- **Related Plans Discovery**: Find similar or complementary plans
- **Smart Examples**: Context-aware usage examples with your actual devices
- **Execution Estimates**: Duration and complexity predictions

### 🚀 System Integration
- **QueueServer Integration**: Direct connection to Bluesky QueueServer
- **BITS Test Instrument**: Pre-configured with beamline testing suite
- **Docker Support**: Complete containerized deployment
- **RESTful API**: Full programmatic access with OpenAPI documentation

## 🎛️ User Interface

### 💬 Chat Interface
- Interactive conversation with AI assistant
- Context-aware responses about your specific beamline setup
- Natural language device queries and plan explanations

### 🔬 Instrument Introspection Dashboard
- **📊 Status Tab**: QServer state, environment status, and system health
- **🔧 Devices Tab**: Live device positions, categorization, and detailed inspection
- **📋 Plans Tab**: 
  - **All Plans**: Filterable browser with complexity indicators
  - **Recommendations**: Skill-level based suggestions
  - **Analysis**: Visual analytics and complexity breakdowns
- **📈 History Tab**: Scan history, success rates, and usage patterns

### 🎨 Enhanced Interface Features
- **Smart Filtering**: Filter by complexity, category, device type
- **Color-Coded Complexity**: 🟢 Beginner | 🟡 Intermediate | 🔴 Advanced
- **Real-Time Status Indicators**: Live connection and position monitoring
- **Interactive Parameter Tables**: Type information and validation rules
- **Visual Analytics**: Charts for plan categories and complexity distribution

## 🛠️ Technical Architecture

- **Frontend**: Streamlit with enhanced multi-tab interface
- **Backend**: FastAPI with comprehensive REST API
- **AI Engine**: LMStudio integration with context-aware responses
- **Queue System**: Direct Bluesky QueueServer integration
- **Database**: Redis for session state and caching
- **Containerization**: Docker Compose with health checks

---
**Making beamline control as easy as conversation!** 🔬✨

Transform your synchrotron beamline into an intelligent, AI-assisted research platform.