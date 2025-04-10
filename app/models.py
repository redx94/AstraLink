"""
AstraLink - Data Models Module
==========================

This module defines the core data structures and validation logic for quantum
operations, AI predictions, system health monitoring, and state management.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
See LICENSE file for licensing information.
"""

from pydantic import BaseModel, Field, validator, constr
from typing import Dict, Any, List, Optional
import numpy as np
from datetime import datetime

class HealthStatus(BaseModel):
    status: str = Field(..., description="Current system status")
    details: Dict[str, Any] = Field(..., description="Detailed health metrics")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class QuantumState(BaseModel):
    state_vector: list[complex]
    fidelity: float
    error_rate: float

class QuantumOperation(BaseModel):
    operation: constr(regex='^[A-Za-z0-9_]+$') = Field(..., description="Quantum operation name")
    qubits: List[int] = Field(..., description="List of qubit indices")
    params: Optional[List[float]] = Field(default=None, description="Optional operation parameters")
    
    @validator('operation')
    def validate_operation(cls, v):
        valid_operations = {'X', 'Y', 'Z', 'H', 'CNOT', 'SWAP'}
        if v not in valid_operations:
            raise ValueError(f"Invalid operation. Must be one of: {valid_operations}")
        return v
    
    @validator('qubits')
    def validate_qubits(cls, v, values):
        if not v:
            raise ValueError("Must specify at least one qubit")
        if len(v) > 50:
            raise ValueError("Too many qubits specified")
        if len(set(v)) != len(v):
            raise ValueError("Duplicate qubit indices not allowed")
        return v

    @validator('qubits')
    def validate_qubit_range(cls, v):
        if any(q < 0 or q >= 50 for q in v):
            raise ValueError("Qubit indices must be between 0 and 49")
        return v

    @validator('params')
    def validate_params(cls, v, values):
        if v is not None:
            if not all(isinstance(x, (int, float)) for x in v):
                raise ValueError("All parameters must be numeric")
        return v

    @validator('params')
    def validate_param_range(cls, v):
        if v is not None:
            if any(abs(p) > 2*np.pi for p in v):
                raise ValueError("Parameter values must be within [-2π, 2π]")
        return v

class AIModelResult(BaseModel):
    prediction: Dict[str, float] = Field(..., description="Predicted properties")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = Field(..., description="AI model version used")

class SystemHealth(BaseModel):
    status: str = Field(..., description="System health status")
    details: Dict[str, Any] = Field(..., description="Detailed health metrics")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    environment: str = Field(..., description="Current environment")

class QuantumResult(BaseModel):
    operation_id: str = Field(..., description="Unique operation identifier")
    result_data: Dict[str, Any] = Field(..., description="Operation results")
    execution_time: float = Field(..., description="Operation execution time")
    error_metrics: Dict[str, float] = Field(..., description="Error rates and metrics")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
