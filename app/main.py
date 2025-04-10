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
import logging
import time
import uuid
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
from .logging_config import LOGGING_CONFIG, get_logger

logging.config.dictConfig(LOGGING_CONFIG)

logger = get_logger(__name__)
api_key_header = APIKeyHeader(name="X-API-Key")

app = FastAPI(title="AstraLink API",
             description="Advanced Quantum-Classical Hybrid System API",
             version="2.0.0",
             docs_url="/api/docs",
             redoc_url="/api/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()
quantum_system = QuantumSystem(settings.quantum_system_endpoint)
ai_system = AISystem(settings.ai_system_endpoint)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

class HealthStatus(BaseModel):
    status: str = Field(..., description="Current system status")
    details: Dict[str, Any] = Field(..., description="Detailed health metrics")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if not api_key == settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    start_time = time.time()
    
    context = {
        "path": request.url.path,
        "method": request.method,
        "client_ip": request.client.host,
    }
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        context["duration"] = duration
        context["status_code"] = response.status_code
        
        logger.info(
            f"Request completed",
            correlation_id=correlation_id,
            context=context
        )
        
        response.headers["X-Correlation-ID"] = correlation_id
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        context["duration"] = duration
        context["error"] = str(e)
        
        logger.error(
            f"Request failed",
            correlation_id=correlation_id,
            context=context,
            exc_info=True
        )
        raise

@app.get("/", response_model=Dict[str, str])
async def read_root():
    return {"message": "Welcome to AstraLink"}

@app.get("/health", response_model=HealthStatus)
async def health_check():
    try:
        status = await check_system_health()
        return HealthStatus(
            status="healthy" if all(status.values()) else "degraded",
            details=status,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def check_system_health() -> Dict[str, bool]:
    try:
        return {
            "database": await check_database_health(),
            "quantum_system": await quantum_system.check_health(),
            "ai_systems": await ai_system.check_health()
        }
    except AstraLinkException as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "error", "detail": str(e)}

@app.post("/quantum/execute")
@limiter.limit("10/minute")
async def execute_quantum_operation(
    background_tasks: BackgroundTasks,
    operation: str = Query(..., min_length=1, max_length=50),
    qubits: List[int] = Query(..., min_items=1, max_items=50),
    params: Optional[List[float]] = Query(None),
    api_key: str = Depends(verify_api_key)
):
    """Execute quantum operation with validation and rate limiting."""
    try:
        result = await quantum_system.execute_quantum_operation(operation, qubits, params)
        background_tasks.add_task(log_quantum_operation, operation, qubits, result)
        return {"status": "success", "result": result}
    except QuantumSystemError as e:
        logger.error(f"Quantum operation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/quantum/batch-execute")
async def batch_execute_quantum_operations(
    operations: List[QuantumOperation],
    background_tasks: BackgroundTasks,
    max_concurrent: Optional[int] = 5
):
    semaphore = asyncio.Semaphore(max_concurrent)
    async with semaphore:
        results = await quantum_system.execute_batch(operations)
    return results

@app.post("/ai/predict", response_model=AIModelResult)
async def predict_properties(
    structure: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    try:
        result = await ai_system.predict_material_properties(structure)
        return result
    except AISystemError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.exception_handler(AstraLinkException)
async def astralink_exception_handler(request: Request, exc: AstraLinkException):
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    error_detail = exc.to_dict()
    error_detail['correlation_id'] = correlation_id
    
    logger.error(
        f"AstraLink error: {str(exc)}",
        correlation_id=correlation_id,
        context=error_detail
    )
    
    return JSONResponse(
        status_code=determine_status_code(exc),
        content={"error": error_detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    error_detail = {
        "error_code": "INTERNAL_ERROR",
        "message": "An unexpected error occurred",
        "correlation_id": correlation_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.error(
        f"Unhandled error: {str(exc)}",
        correlation_id=correlation_id,
        context={"error_type": type(exc).__name__},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={"error": error_detail}
    )

def determine_status_code(exc: AstraLinkException) -> int:
    """Map exception types to HTTP status codes."""
    status_codes = {
        ValidationError: 400,
        QuantumSystemError: 503,
        AISystemError: 503,
        ResourceExhaustedError: 429,
        ConfigurationError: 500
    }
    
    return status_codes.get(type(exc), 500)