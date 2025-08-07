"""
FastAPI backend for bAIt-Chat (Bluesky AI Technician Chat)
Main application entry point with Phase 1 endpoints
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uvicorn

from models import (
    DeviceResponse,
    PlanResponse,
    ScanMetadata,
    ExplainRequest,
    ExplainResponse,
    ErrorResponse
)
from qserver import QServerClient
from databroker import DatabrokerClient
from explain import PlanExplainer
from rag_engine import RAGEngine
from local_llm import local_llm_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/bait_chat.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="bAIt-Chat API",
    description="Bluesky AI Technician Chat - Beamline Control Assistant",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000", "*"],  # Streamlit default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service clients
qserver_client = QServerClient()
databroker_client = DatabrokerClient()
plan_explainer = PlanExplainer()
rag_engine = RAGEngine()

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running and services are available"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "qserver": qserver_client.is_connected(),
            "databroker": databroker_client.is_connected(),
            "rag_engine": rag_engine.is_initialized()
        }
    }
    return health_status

# Phase 1 Endpoints - Informational + RAG

@app.get("/devices", response_model=List[DeviceResponse])
async def get_devices():
    """
    Retrieve available Ophyd devices from BITS
    Returns list of motors, detectors, and other hardware
    """
    try:
        logger.info("Fetching devices from QServer")
        devices = await qserver_client.get_devices()
        
        # Also check RAG for additional device documentation
        device_docs = await rag_engine.search_devices(query="all devices")
        
        # Combine and format response
        return devices
    except Exception as e:
        logger.error(f"Error fetching devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/plans", response_model=List[PlanResponse])
async def get_plans():
    """
    List available QServer scan plans
    Returns plan names, parameters, and descriptions
    """
    try:
        logger.info("Fetching plans from QServer")
        plans = await qserver_client.get_plans()
        
        # Enhance with RAG documentation
        for plan in plans:
            doc = await rag_engine.search_plans(plan['name'])
            if doc:
                plan['enhanced_description'] = doc
        
        return plans
    except Exception as e:
        logger.error(f"Error fetching plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/last_scan", response_model=ScanMetadata)
async def get_last_scan():
    """
    Fetch most recent scan metadata from Databroker
    Returns scan ID, timestamp, plan name, and results summary
    """
    try:
        logger.info("Fetching last scan from Databroker")
        scan_data = await databroker_client.get_last_scan()
        
        if not scan_data:
            raise HTTPException(status_code=404, detail="No scans found")
        
        return scan_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching last scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/explain", response_model=ExplainResponse)
async def explain_plan(request: ExplainRequest):
    """
    Explain a scan plan in plain English
    Translates Python code to human-readable description
    """
    try:
        logger.info(f"Explaining plan: {request.plan_name or 'custom'}")
        
        # Get plan source code if name provided
        if request.plan_name:
            plan_source = await qserver_client.get_plan_source(request.plan_name)
        else:
            plan_source = request.plan_source
        
        if not plan_source:
            raise HTTPException(status_code=400, detail="Plan source code required")
        
        # Generate explanation using LLM
        explanation = await plan_explainer.explain(
            plan_source=plan_source,
            context=request.context
        )
        
        return ExplainResponse(
            plan_name=request.plan_name,
            explanation=explanation,
            timestamp=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search_knowledge_base(query: str, limit: int = 5):
    """
    Search the RAG knowledge base for relevant information
    """
    try:
        logger.info(f"Searching knowledge base: {query}")
        results = await rag_engine.search(query=query, limit=limit)
        return {"query": query, "results": results}
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Placeholder endpoints for Phase 1.5 - QServer Agent Integration

@app.post("/submit_plan")
async def submit_plan(plan: Dict[str, Any]):
    """
    Submit a plan to QServer (Phase 1.5)
    Placeholder for NLP-translated plan submission
    """
    return {
        "status": "not_implemented", 
        "message": "Plan submission will be available in Phase 1.5"
    }

@app.get("/queue")
async def get_queue():
    """
    Get current queue status (Phase 1.5)
    """
    return {
        "status": "not_implemented",
        "message": "Queue management will be available in Phase 1.5"
    }

@app.delete("/queue/clear")
async def clear_queue():
    """
    Clear the queue (Phase 1.5)
    """
    return {
        "status": "not_implemented",
        "message": "Queue management will be available in Phase 1.5"
    }

@app.delete("/queue/item/{item_id}")
async def remove_queue_item(item_id: str):
    """
    Remove specific item from queue (Phase 1.5)
    """
    return {
        "status": "not_implemented",
        "message": "Queue management will be available in Phase 1.5"
    }

@app.post("/re/pause")
async def pause_run_engine():
    """
    Pause RunEngine (Phase 1.5)
    """
    return {
        "status": "not_implemented",
        "message": "RunEngine control will be available in Phase 1.5"
    }

@app.post("/re/resume")
async def resume_run_engine():
    """
    Resume RunEngine (Phase 1.5)
    """
    return {
        "status": "not_implemented",
        "message": "RunEngine control will be available in Phase 1.5"
    }

# Startup and shutdown events

@app.on_event("startup")
async def startup_event():
    """Initialize connections and load knowledge base"""
    logger.info("Starting bAIt-Chat API server")
    
    # Initialize connections
    await qserver_client.connect()
    await databroker_client.connect()
    await rag_engine.initialize()
    
    # Initialize local LLM service if configured
    if settings.LLM_PROVIDER in ["lmstudio", "ollama"]:
        await local_llm_service.initialize()
    
    logger.info("All services initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections"""
    logger.info("Shutting down bAIt-Chat API server")
    
    await qserver_client.disconnect()
    await databroker_client.disconnect()
    await rag_engine.cleanup()
    
    # Cleanup local LLM service
    if settings.LLM_PROVIDER in ["lmstudio", "ollama"]:
        await local_llm_service.cleanup()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )