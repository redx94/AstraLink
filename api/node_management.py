#!/usr/bin/env python3

"""
AstraLink Node Management Interface
================================

Provides a RESTful API for managing nodes through quantum.api domain with
quantum-safe authentication and monitoring.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
"""

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Optional
import asyncio
import json
import yaml
from datetime import datetime
import aiohttp
import uuid
from quantum.quantum_error_correction import QuantumErrorCorrection
from network.handshake_integration import HandshakeIntegration
from tools.security_auditor import SecurityAuditor
from logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="AstraLink Node Management API",
    description="Manage AstraLink nodes through quantum.api",
    version="1.0.0"
)

security = HTTPBearer()
quantum_correction = QuantumErrorCorrection()
handshake = HandshakeIntegration()

class NodeManager:
    def __init__(self):
        self.nodes = {}
        self.security_auditor = SecurityAuditor()
        self._load_config()

    def _load_config(self):
        """Load node management configuration"""
        try:
            with open('config/cellular_network.yaml', 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    async def verify_auth_token(self, token: str) -> bool:
        """Verify quantum-safe authentication token"""
        try:
            # Apply quantum error correction to token
            corrected_token = await quantum_correction.correct_errors(token)
            
            # Verify token signature
            return await quantum_correction.verify_signature(corrected_token)
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return False

    async def get_node_status(self, node_id: str) -> Dict:
        """Get node status and metrics"""
        try:
            node = self.nodes.get(node_id)
            if not node:
                raise ValueError(f"Node {node_id} not found")

            # Get node metrics
            metrics = await self._fetch_node_metrics(node)
            
            # Get quantum state quality
            quantum_metrics = await self._check_quantum_state(node)
            
            # Get network status
            network_status = await self._check_network_status(node)
            
            return {
                "node_id": node_id,
                "status": "active" if metrics['healthy'] else "degraded",
                "last_seen": datetime.utcnow().isoformat(),
                "metrics": metrics,
                "quantum_state": quantum_metrics,
                "network": network_status
            }
        except Exception as e:
            logger.error(f"Failed to get node status: {e}")
            raise

    async def update_configuration(self, node_id: str, config: Dict) -> Dict:
        """Update node configuration"""
        try:
            node = self.nodes.get(node_id)
            if not node:
                raise ValueError(f"Node {node_id} not found")

            # Apply quantum error correction to config
            corrected_config = await self._protect_configuration(config)
            
            # Push configuration to node
            response = await self._push_config(node, corrected_config)
            
            # Verify configuration application
            if not await self._verify_config(node, corrected_config):
                raise ValueError("Configuration verification failed")
                
            return {
                "node_id": node_id,
                "status": "updated",
                "timestamp": datetime.utcnow().isoformat(),
                "config_hash": await quantum_correction.generate_hash(
                    json.dumps(corrected_config).encode()
                )
            }
        except Exception as e:
            logger.error(f"Configuration update failed: {e}")
            raise

    async def _protect_configuration(self, config: Dict) -> Dict:
        """Apply quantum protection to configuration"""
        try:
            # Generate quantum key
            key = await quantum_correction.generate_key()
            
            # Encrypt sensitive fields
            protected_config = {}
            for k, v in config.items():
                if k in ['security', 'credentials', 'keys']:
                    protected_config[k] = await quantum_correction.encrypt(v, key)
                else:
                    protected_config[k] = v
                    
            return protected_config
            
        except Exception as e:
            logger.error(f"Configuration protection failed: {e}")
            raise

node_manager = NodeManager()

@app.get("/nodes", response_model=List[Dict])
async def list_nodes(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """List all registered nodes"""
    if not await node_manager.verify_auth_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return list(node_manager.nodes.values())

@app.get("/nodes/{node_id}/status")
async def get_node_status(
    node_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Get node status and metrics"""
    if not await node_manager.verify_auth_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        return await node_manager.get_node_status(node_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/nodes/{node_id}/config")
async def update_node_config(
    node_id: str,
    config: Dict,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Update node configuration"""
    if not await node_manager.verify_auth_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        return await node_manager.update_configuration(node_id, config)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/nodes/{node_id}/restart")
async def restart_node(
    node_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Restart node services"""
    if not await node_manager.verify_auth_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        node = node_manager.nodes.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
            
        # Execute restart command
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://{node['domain']}/control/restart",
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            ) as response:
                if response.status != 200:
                    raise ValueError("Restart failed")
                    
        return {
            "node_id": node_id,
            "status": "restarting",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/nodes/{node_id}/logs")
async def get_node_logs(
    node_id: str,
    service: Optional[str] = None,
    lines: Optional[int] = 100,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Get node logs"""
    if not await node_manager.verify_auth_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        node = node_manager.nodes.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
            
        # Fetch logs from node
        async with aiohttp.ClientSession() as session:
            params = {"service": service, "lines": lines} if service else {"lines": lines}
            async with session.get(
                f"https://{node['domain']}/logs",
                params=params,
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            ) as response:
                if response.status != 200:
                    raise ValueError("Failed to fetch logs")
                logs = await response.json()
                
        return {
            "node_id": node_id,
            "service": service,
            "logs": logs,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/nodes/{node_id}/audit")
async def run_node_audit(
    node_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Run security audit on node"""
    if not await node_manager.verify_auth_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        results = await node_manager.security_auditor.run_all_audits(node_id)
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/nodes/{node_id}/metrics")
async def get_node_metrics(
    node_id: str,
    metric_type: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Get node performance metrics"""
    if not await node_manager.verify_auth_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        node = node_manager.nodes.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
            
        # Fetch metrics from node
        async with aiohttp.ClientSession() as session:
            params = {"type": metric_type} if metric_type else {}
            async with session.get(
                f"https://{node['domain']}/metrics",
                params=params,
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            ) as response:
                if response.status != 200:
                    raise ValueError("Failed to fetch metrics")
                metrics = await response.json()
                
        return {
            "node_id": node_id,
            "type": metric_type,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
