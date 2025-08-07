# bait-chat

"""
PROJECT: bAIt-Chat (Bluesky AI Technician Chat)

DESCRIPTION:
A voice- and text-enabled chatbot assistant for APS beamline control using Bluesky QServer + BITS.
The assistant helps scientists run experiments, manage queues, and understand scan plans using natural language.
It supports optional voice input using Whisper and integrates with Streamlit for UI.

GOALS:
- Retrieve available devices, scan plans, and past scans
- Submit plans to QServer using natural-language instructions
- Query and manage the QServer queue (view, remove, clear, pause/resume)
- Explain Python scan plans in plain scientific language
- Support voice interaction via Whisper (speech-to-text → command routing)

CORE INTERACTIONS:
- "What motors can I use?" → List BITS-defined Ophyd devices
- "What scans are available?" → List QServer plans
- "What was the last scan?" → Show metadata from Databroker
- "Explain this script..." → Translate Python plan to plain English
- "Scan from 0 to 5 mm using Pilatus..." → NLP → Plan Dict → Submit to QServer
- "What's in the queue?" → Show QServer queue state
- "Remove the first item" → Remove item from queue
- "Pause/Resume" → Control RunEngine state

MVP ROADMAP:

PHASE 1 — Informational + RAG:
- Implement `/devices`: return Ophyd devices from BITS
- Implement `/plans`: list QServer plans from RE Manager
- Implement `/last_scan`: fetch most recent scan metadata from Databroker
- Implement `/explain`: summarize plan source code using LLM
- Build RAG system (LangChain + Qdrant/Chroma) with:
  - Device definitions
  - Scan plan templates
  - Beamline documentation

PHASE 1.5 — QServer Agent Integration:
- NLP → plan dict translation for plan types like `scan`, `count`, `list_scan`
- Implement `/submit_plan`: submit translated plan to QServer
- Implement `/queue`: get current queue status
- Implement `/queue/clear` and `/queue/item/remove`
- Implement `/re_pause` and `/re_resume`

PHASE 2 — UI and Live Sync:
- Build Streamlit chatbot UI with status and result display
- Display scan results (metadata, preview images, etc.)
- Add dropdowns/autocomplete for known devices/plans
- Route all commands through LangChain agent tools
- Add optional access control (token, user group, etc.)

VOICE MODE (optional):
- Add Whisper-based speech-to-text pipeline:
  - Browser mic capture (WebRTC or MediaRecorder)
  - Stream to backend
  - Use Whisper (local or remote) for transcription
  - Route to same LangChain agent as text

SECURITY:
- Whitelist plan names (via QServer)
- Log all user actions (input, timestamp, result)
- Validate plan schema using Pydantic
- Optional: user/group permissions if exposed beyond beamline

PROJECT STRUCTURE:

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

TOOLS:
- FastAPI for backend API
- Streamlit for user interface
- LangChain for routing and agent tools
- Whisper for voice input (optional)
- Qdrant or Chroma for vector store
- OpenAI, Claude, or Mistral for LLM backend
- Bluesky stack: QServer, RunEngine, BITS, Databroker

NEXT STEPS:
- [x] Select UI: Streamlit
- [ ] Create NLP plan schema examples
- [ ] Scaffold FastAPI + LangChain agent tools
- [ ] Build basic chatbot loop
- [ ] Integrate Whisper for voice input
"""
