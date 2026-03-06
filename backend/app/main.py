"""
Main Application Entry Point — Ghost Operators Advanced NIDS.

Integrates:
  - FastAPI framework
  - WebSocket Manager for real-time alerts
  - Orchestrator lifecycle management
  - Database connection handling
  - Middleware (CORS, Security, Exceptions)
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.auth import router as auth_router
from app.core.orchestrator import NIDSOrchestrator
from app.core.ws_manager import ws_manager
from app.db.database import db_manager
from app.utils.config import settings
from app.utils.security import SecurityMiddleware
from app.models.schemas import SnifferConfig, MLModelConfig, IPSConfig

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("nids")
    
orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the FastAPI application."""
    global orchestrator

    await db_manager.connect()
    
    try:
        sniffer_cfg = SnifferConfig(interface=settings.INTERFACE)
        ml_cfg = MLModelConfig(model_path=settings.MODEL_PATH, confidence_threshold=settings.CONFIDENCE_THRESHOLD)
        ips_cfg = IPSConfig(enabled=settings.IPS_ENABLED, auto_block=settings.IPS_AUTO_BLOCK)
        
        orchestrator = NIDSOrchestrator(
            sniffer_cfg, 
            ml_cfg, 
            ips_cfg,
            ws_broadcast=ws_manager.broadcast_sync
        )
        logger.info("NIDS Orchestrator initialized")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")

    ws_manager.set_loop(asyncio.get_event_loop())
    
    yield
    
    if orchestrator:
        orchestrator.stop()
    await db_manager.disconnect()
    logger.info("NIDS application shutdown")

app = FastAPI(
    title="Ghost Operators NIDS",
    description="Advanced Network Intrusion Detection & Prevention System",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, tags=["Authentication"])
app.include_router(api_router)

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)

@app.get("/")
async def root():
    return {
        "app": "Ghost Operators Advanced NIDS",
        "version": "2.0.0",
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host=settings.API_HOST, 
        port=settings.API_PORT, 
        reload=settings.API_RELOAD
    )
