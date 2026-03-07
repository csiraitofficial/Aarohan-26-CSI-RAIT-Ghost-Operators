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
import os
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.routes import router as api_router
from app.api.auth import router as auth_router
from app.core.orchestrator import NIDSOrchestrator
from app.core.ws_manager import ws_manager
from app.db.database import db_manager
from app.utils.config import settings
from app.utils.logging_config import setup_production_logging
from app.utils.security import SecurityMiddleware
from app.models.schemas import SnifferConfig, MLModelConfig, IPSConfig

# Initialize Production Logging
setup_production_logging()
logger = logging.getLogger("nids")

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
    
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
        # Verify and initialize DB state
        from app.api.auth import ADMIN_PASSWORD
        if ADMIN_PASSWORD == "Generate-Secure-P@ssw0rd-123!":
             logger.warning("🛡️ SECURITY ALERT: NIDS is running with hardcoded ADMIN_PASSWORD. Change NIDS_ADMIN_PASSWORD in .env immediately!")

        logger.info("NIDS Orchestrator initialized with Industrial-Grade hardening")
        orchestrator.set_loop(asyncio.get_event_loop())
        orchestrator.start()
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
    description="Production-grade Network Intrusion Detection & Prevention System",
    version="2.0.0",
    lifespan=lifespan
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Handled by SecurityMiddleware below

# CORS Hardware-Grade Configuration
cors_origins = settings.cors_origins_list
allow_all = "*" in cors_origins or settings.CORS_ORIGINS == "*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else cors_origins,
    allow_credentials=not allow_all, 
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityMiddleware)

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
