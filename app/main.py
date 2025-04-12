"""
AstraLink - Main Application Module
===============================

This module serves as the core FastAPI application entry point, implementing
the REST API endpoints, middleware, and system-wide exception handling.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
See LICENSE file for licensing information.
"""

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging.config
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from .config import get_settings
from .exceptions import (
    AstraLinkException, QuantumSystemError, AISystemError,
    ValidationError, ResourceExhaustedError, ConfigurationError
)
from .models import HealthStatus, AIModelResult
from .quantum_interface import QuantumSystem
from .ai_interface import AISystem
from .logging_config import LOGGING_CONFIG, get_logger, StructuredLogger
from .monitoring import SystemMonitor, MetricsAggregator

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = StructuredLogger("AstraLinkAPI")

# Initialize components
api_key_header = APIKeyHeader(name="X-API-Key")
system_monitor = SystemMonitor()
metrics_aggregator = MetricsAggregator()
settings = get_settings()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="AstraLink API",
    description="Advanced Quantum-Classical Hybrid System API",
    version="2.0.0",
    docs_url="/api/docs",
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["System"])
@limiter.limit("10/minute")
async def health_check(request: Request):
    """System health check endpoint"""
    try:
        health_status = await system_monitor.check_system_health()
        return JSONResponse(
            status_code=200 if health_status.status == "healthy" else 503,
            content={
                "status": health_status.status,
                "message": health_status.message,
                "timestamp": health_status.timestamp,
                "checks": health_status.checks,
                "version": app.version
            }
        )
    except Exception as e:
        logger.error("Health check endpoint failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/metrics", tags=["System"])
@limiter.limit("30/minute")
async def get_metrics(
    request: Request,
    window: int = Query(300, description="Time window in seconds", ge=60, le=3600)
):
    """System metrics endpoint"""
    try:
        metrics = metrics_aggregator.get_aggregated_metrics(window)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "metrics": metrics,
                "window": window
            }
        )
    except Exception as e:
        logger.error("Metrics endpoint failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log and track all HTTP requests"""
    start_time = datetime.now()
    
    try:
        response = await call_next(request)
        
        # Calculate request duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Log request details
        logger.info(
            "Request processed",
            method=request.method,
            path=request.url.path,
            duration=duration,
            status_code=response.status_code
        )
        
        # Record request metrics
        metrics_aggregator.add_metrics({
            "request_duration": duration,
            "status_code": response.status_code,
            "path": request.url.path
        })
        
        return response
        
    except Exception as e:
        logger.error(
            "Request failed",
            method=request.method,
            path=request.url.path,
            error=str(e)
        )
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    try:
        logger.info("Starting AstraLink API")
        # Perform initial health check
        try:
            await system_monitor.check_system_health()
            logger.info("Initial health check passed")
        except Exception as e:
            logger.warning("Initial health check failed, but continuing startup", error=str(e))
        logger.info("AstraLink API started successfully")
    except Exception as e:
        logger.critical("Failed to start AstraLink API", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("Shutting down AstraLink API")
