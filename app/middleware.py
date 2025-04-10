"""
AstraLink - Middleware Module
=========================

This module implements FastAPI middleware components for request processing,
performance monitoring, and metrics collection.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
See LICENSE file for licensing information.
"""

from fastapi import Request
import time
import uuid
from typing import Callable
from .monitoring import metrics

async def process_time_middleware(request: Request, call_next: Callable):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

async def metrics_middleware(request: Request, call_next: Callable):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        response = await call_next(request)
        metrics.observe_request(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration=time.time() - start_time
        )
        return response
    except Exception as e:
        metrics.observe_error(request_id=request_id, error=str(e))
        raise
