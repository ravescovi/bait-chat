# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

bAIt-Chat (Bluesky AI Technician Chat) is a voice- and text-enabled chatbot assistant for APS beamline control using Bluesky QServer + BITS. The assistant helps scientists run experiments, manage queues, and understand scan plans using natural language.

## Architecture

### Core Components

1. **Backend (FastAPI)** - Handles all API requests and integrations
   - QServer interaction for plan submission and queue management
   - Databroker integration for scan metadata retrieval
   - RAG engine for knowledge retrieval
   - Plan explanation using LLM

2. **UI Layer (Streamlit)** - Chat interface with optional voice input
   - Voice capture via browser (WebRTC/MediaRecorder)
   - Whisper integration for speech-to-text
   - Real-time status and result display

3. **Knowledge Base** - RAG system using LangChain + vector store
   - BITS device definitions
   - Scan plan templates
   - Beamline documentation

4. **Integration Layer** - Bluesky stack components
   - QServer for plan execution
   - RunEngine for scan control
   - BITS for device definitions
   - Databroker for metadata storage

## Development Setup

### Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (when requirements.txt exists)
pip install -r requirements.txt
```

### Local LLM Setup (Optional)
For privacy and offline operation, you can use local LLM models:

```bash
# Option 1: Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama run llama2

# Option 2: LMStudio
# Download from https://lmstudio.ai/ and follow GUI instructions

# Configure for local models
export LLM_PROVIDER=ollama  # or lmstudio
export LOCAL_MODEL_NAME=llama2
```

See [docs/LOCAL_MODELS.md](docs/LOCAL_MODELS.md) for detailed setup instructions.

### Run the Application
```bash
# Start FastAPI backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start Streamlit UI (in separate terminal)
cd ui
streamlit run streamlit_app.py
```

### Testing
```bash
# Run unit tests (when implemented)
pytest tests/

# Test individual endpoints
curl http://localhost:8000/devices
curl http://localhost:8000/plans
```

## Key API Endpoints

### Information Retrieval
- `/devices` - List available Ophyd devices from BITS
- `/plans` - List available QServer scan plans
- `/last_scan` - Get most recent scan metadata from Databroker
- `/explain` - Explain a scan plan in plain language

### Queue Management  
- `/submit_plan` - Submit a plan to QServer
- `/queue` - Get current queue status
- `/queue/clear` - Clear the queue
- `/queue/item/remove` - Remove specific queue item
- `/re_pause` - Pause RunEngine
- `/re_resume` - Resume RunEngine

## Implementation Phases

### Current Phase: MVP Phase 1 (Informational + RAG)
Focus on read-only operations and knowledge retrieval before implementing control operations.

### Key Implementation Patterns

1. **NLP to Plan Translation**
   - Parse natural language input using LangChain
   - Map to structured plan dictionary
   - Validate against QServer schema
   - Submit via QServer API

2. **Security Considerations**
   - Whitelist allowed plan names
   - Validate all plan parameters with Pydantic
   - Log all actions with timestamps
   - Implement rate limiting

3. **Voice Pipeline (Optional)**
   - Capture audio from browser
   - Stream to backend via WebSocket
   - Process with Whisper (local or API)
   - Route transcription to same agent as text

## Project Structure

```
bait-chat/
├── backend/
│   ├── main.py           # FastAPI app entry point
│   ├── explain.py        # Plan explanation logic
│   ├── qserver.py        # QServer interaction
│   ├── databroker.py     # Scan metadata fetch
│   └── rag_engine.py     # RAG setup and search
├── ui/
│   └── streamlit_app.py  # Chatbot UI with voice input
├── knowledge_base/
│   └── bits_devices/     # BITS .py device files
├── vector_db/
│   └── qdrant/           # Embedding + document index
└── requirements.txt      # Python dependencies
```

## Integration Points

### Bluesky Stack
- **QServer**: HTTP API for plan submission and queue management
- **RunEngine**: Core execution engine for scans
- **BITS**: Beamline configuration and device definitions
- **Databroker**: Metadata and data storage/retrieval

### AI/ML Stack
- **LangChain**: Agent routing and tool orchestration
- **Vector Store**: Qdrant or Chroma for embeddings
- **LLM Backend**: OpenAI, Claude, Mistral, LMStudio, or Ollama
- **Local LLM Support**: LMStudio and Ollama for privacy and offline use
- **Whisper**: Speech-to-text (optional)

## Common Development Tasks

### Adding a New Endpoint
1. Define route in `backend/main.py`
2. Implement logic in appropriate module (`qserver.py`, `databroker.py`, etc.)
3. Add corresponding LangChain tool if needed
4. Update UI to use new endpoint

### Extending RAG Knowledge Base
1. Add documents to `knowledge_base/`
2. Update `rag_engine.py` to process new document types
3. Re-index vector database
4. Test retrieval quality

### Implementing a New Plan Type
1. Add plan schema validation in backend
2. Create NLP mapping rules in agent
3. Test with QServer simulator
4. Add to whitelisted plans