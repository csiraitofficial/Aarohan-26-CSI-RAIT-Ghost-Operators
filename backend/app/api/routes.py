"""
API Routes — FastAPI endpoints for the Advanced NIDS.

Comprehensive endpoints for:
  - System control (start/stop)
  - Alert management (query/resolve/export)
  - Traffic analysis (packets/flows)
  - Settings management
  - Health & Metrics
"""

import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from fastapi.responses import FileResponse

from app.models.schemas import (
    SnifferConfig, MLModelConfig, Alert, PacketInfo,
    SystemStatus, StartSnifferRequest, StopSnifferRequest,
    AlertResponse, PacketResponse, StatsResponse, BlockIPRequest,
    AlertSeverity, DetectionType, HealthResponse
)
from app.utils.security import verify_api_key, require_role, UserRole
from app.utils.config import settings

# Orchestrator will be initialized in main.py and stored here
# We use a pattern to access the global orchestrator instance
orchestrator = None

router = APIRouter(prefix="/api/v1")

def get_orchestrator():
    from app.main import orchestrator as global_orch
    if global_orch is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return global_orch

# ============================================================
# System Control
# ============================================================

@router.get("/status", response_model=SystemStatus)
async def get_status(orch=Depends(get_orchestrator)):
    return orch.get_system_status()

@router.post("/start")
async def start_nids(req: Optional[StartSnifferRequest] = None, orch=Depends(get_orchestrator)):
    if req and req.config:
        orch.update_sniffer_config(req.config)
    
    if orch.start():
        return {"status": "success", "message": "NIDS started"}
    else:
        raise HTTPException(status_code=500, detail="Failed to start NIDS")

@router.post("/stop")
async def stop_nids(orch=Depends(get_orchestrator)):
    if orch.stop():
        return {"status": "success", "message": "NIDS stopped"}
    else:
        return {"status": "warning", "message": "NIDS was not running"}

# ============================================================
# Alerts
# ============================================================

@router.get("/alerts", response_model=AlertResponse)
async def get_alerts(
    limit: int = Query(100, le=1000),
    page: int = Query(1, ge=1),
    severity: Optional[AlertSeverity] = None,
    detection_type: Optional[DetectionType] = None,
    source_ip: Optional[str] = None,
    resolved: Optional[bool] = None,
    orch=Depends(get_orchestrator)
):
    all_alerts = orch.get_alerts(
        limit=limit, 
        severity=severity,
        detection_type=detection_type,
        source_ip=source_ip,
        resolved=resolved
    )
    # Pagination in-memory for Phase 1
    start = (page - 1) * limit
    end = start + limit
    return {
        "alerts": all_alerts[start:end],
        "total_count": len(all_alerts),
        "page": page,
        "page_size": limit
    }

@router.get("/alerts/{alert_id}", response_model=Alert)
async def get_alert_details(alert_id: str, orch=Depends(get_orchestrator)):
    alert = orch.alert_manager.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, notes: str = "", orch=Depends(get_orchestrator)):
    if orch.resolve_alert(alert_id, notes):
        return {"status": "success", "message": f"Alert {alert_id} resolved"}
    raise HTTPException(status_code=404, detail="Alert not found")

@router.get("/alerts/export")
async def export_alerts(format: str = "json", orch=Depends(get_orchestrator)):
    export_data = orch.export_alerts(format)
    # Return as file for better UX
    filename = f"nids_alerts_{format}.{format}"
    filepath = f"data/{filename}"
    with open(filepath, "w") as f:
        f.write(export_data)
    return FileResponse(filepath, filename=filename)

# ============================================================
# Traffic Data
# ============================================================

@router.get("/packets", response_model=PacketResponse)
async def get_recent_packets(limit: int = Query(100, le=500), orch=Depends(get_orchestrator)):
    packets = orch.get_recent_packets(limit)
    return {
        "packets": packets,
        "total_count": len(packets),
        "page": 1,
        "page_size": limit
    }

@router.get("/stats", response_model=StatsResponse)
async def get_stats(orch=Depends(get_orchestrator)):
    detailed = orch.get_detailed_stats()
    return {
        "total_packets": detailed["system_status"]["packets_captured"],
        "total_flows": detailed["system_status"]["flows_aggregated"],
        "total_alerts": detailed["system_status"]["alerts_generated"],
        "ml_detections": detailed["system_status"]["ml_predictions"],
        "signature_detections": detailed["system_status"]["signature_matches"],
        "detection_rate": detailed["detection_rates"]["overall_detection_rate"],
        "average_confidence": 0.85 # Mock for now
    }

# ============================================================
# Security & IPS
# ============================================================

@router.post("/ips/block", dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.ANALYST))])
async def block_ip(req: BlockIPRequest, orch=Depends(get_orchestrator)):
    if orch.ips_manager.block_ip(req.ip_address, req.duration_minutes, req.reason):
        return {"status": "success", "message": f"IP {req.ip_address} blocked"}
    raise HTTPException(status_code=500, detail="Failed to block IP")

@router.get("/ips/blocked-ips", dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.ANALYST))])
async def get_blocked_ips(orch=Depends(get_orchestrator)):
    return orch.ips_manager.get_blocked_ips()

# ============================================================
# Configuration
# ============================================================

@router.get("/config")
async def get_config(orch=Depends(get_orchestrator)):
    return {
        "sniffer": orch.sniffer_config,
        "ml": orch.ml_config,
        "ips": orch.ips_manager.config
    }

@router.post("/config/sniffer", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def update_sniffer_config(config: SnifferConfig, orch=Depends(get_orchestrator)):
    if orch.update_sniffer_config(config):
        return {"status": "success", "message": "Sniffer configuration updated"}
    raise HTTPException(status_code=500, detail="Failed to update sniffer configuration")

# ============================================================
# Health
# ============================================================

@router.get("/health", response_model=HealthResponse)
async def health_check(orch=Depends(get_orchestrator)):
    stats = orch.get_detailed_stats()
    return {
        "status": "healthy" if orch.is_running else "ready",
        "version": "2.0.0",
        "uptime_seconds": stats["system_status"]["uptime"],
        "components": [
            {"name": "Capture Engine", "status": "healthy" if stats["component_health"]["capture"] else "down"},
            {"name": "ML Engine", "status": "healthy" if stats["component_health"]["ml"] else "down"},
            {"name": "Signatures", "status": "healthy" if stats["component_health"]["signatures"] else "down"},
        ]
    }
