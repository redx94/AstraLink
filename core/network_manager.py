import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any
from quantum.quantum_controller import QuantumController
from network.bandwidth_marketplace import QuantumSecureBandwidthMarketplace
from app.security import security_manager
from app.high_availability import ha_manager, NodeState
from app.logging_config import StructuredLogger, MetricsCollector
from functools import wraps
import backoff
import yaml

def with_retry(max_tries=3, max_time=30):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func):
        @wraps(func)
        @backoff.on_exception(
            backoff.expo,
            (Exception,),
            max_tries=max_tries,
            max_time=max_time
        )
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class NetworkManager:
    """Manages quantum-classical hybrid network operations"""
    def __init__(self):
        self.quantum_controller = QuantumController()
        self.bandwidth_marketplace = QuantumSecureBandwidthMarketplace()
        self.active_connections = {}
        self.qos_metrics = {}
        self.last_maintenance = 0
        self.maintenance_interval = 300  # 5 minutes
        self.logger = StructuredLogger("NetworkManager")
        self.metrics = MetricsCollector()
        self.logger.info("Network manager initialized")
        self.config = self._load_config()
        self.max_bandwidth = self.config.get('network', {}).get('max_bandwidth', 10000)  # 10 Gbps default
        self.connection_timeout = self.config.get('network', {}).get('connection_timeout', 3600)  # 1 hour default
        self.max_retries = self.config.get('network', {}).get('max_retries', 3)
        self.retry_delay = self.config.get('network', {}).get('retry_delay', 30)  # 30 seconds between retries

    def _load_config(self) -> Dict:
        """Load network configuration"""
        try:
            with open('config/cellular_network.yaml', 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}

    async def start_maintenance_loop(self):
        """Start periodic maintenance tasks"""
        while True:
            try:
                await self._perform_maintenance()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error("Maintenance loop error", error=str(e))
                self.metrics.record_metric("maintenance_failure", True, {"error": str(e)})
                await asyncio.sleep(5)  # Brief pause on error

    async def _perform_maintenance(self):
        """Perform periodic maintenance tasks"""
        current_time = int(time.time())
        
        if current_time - self.last_maintenance < self.maintenance_interval:
            return
            
        self.logger.info("Starting periodic maintenance")
        
        try:
            start_time = time.time()
            
            # Clean up stale connections
            await self._cleanup_stale_connections()
            
            # Trigger marketplace cleanup
            await self.bandwidth_marketplace._periodic_cleanup()
            
            # Update QoS metrics
            self.qos_metrics = await self._calculate_current_qos()
            
            duration = time.time() - start_time
            self.metrics.record_metric("maintenance_duration", duration)
            self.metrics.record_metric("maintenance_success", True)
            
            self.logger.info("Periodic maintenance completed",
                           duration=duration,
                           active_connections=len(self.active_connections))
            self.last_maintenance = current_time
            
        except Exception as e:
            self.logger.error("Maintenance failed", error=str(e))
            self.metrics.record_metric("maintenance_failure", True, {"error": str(e)})

    async def initialize_network(self):
        """Initialize quantum-classical hybrid network"""
        try:
            self.logger.info("Starting network initialization")
            start_time = time.time()
            
            # Start maintenance loop in background
            asyncio.create_task(self.start_maintenance_loop())
            
            # Initialize quantum subsystem with retry
            try:
                await self._init_quantum_system()
                self.logger.info("Quantum system initialized successfully")
            except Exception as e:
                self.logger.error("Quantum system initialization failed", error=str(e))
                self.metrics.record_metric("quantum_init_failure", True, {"error": str(e)})
                raise
            
            # Setup secure channels with retry
            try:
                quantum_channels = await self._setup_secure_channels()
                self.logger.info("Secure channels established")
            except Exception as e:
                self.logger.error("Failed to setup secure channels", error=str(e))
                self.metrics.record_metric("secure_channels_failure", True, {"error": str(e)})
                raise
            
            # Initialize QoS monitoring with retry
            try:
                self.qos_metrics = await self._init_qos_monitoring()
                self.logger.info("QoS monitoring initialized")
            except Exception as e:
                self.logger.error("QoS monitoring initialization failed", error=str(e))
                self.metrics.record_metric("qos_init_failure", True, {"error": str(e)})
                raise
            
            duration = time.time() - start_time
            self.metrics.record_metric("network_init_duration", duration)
            self.metrics.record_metric("network_init_success", True)
            
            self.logger.info("Network initialization completed",
                           duration=duration,
                           quantum_ready=True)
            
            return {
                "status": "initialized",
                "quantum_ready": True,
                "secure_channels": quantum_channels,
                "qos_status": self.qos_metrics,
                "initialization_time": duration
            }
        except Exception as e:
            self.logger.critical("Network initialization failed", error=str(e))
            self.metrics.record_metric("network_init_failure", True, {"error": str(e)})
            raise

    @with_retry(max_tries=3, max_time=30)
    async def _init_quantum_system(self):
        """Initialize quantum subsystem with retry"""
        return await self.quantum_controller.initializeQuantumSystem()

    @with_retry(max_tries=3, max_time=30)
    async def _setup_secure_channels(self):
        """Setup secure channels with retry"""
        return await self.bandwidth_marketplace._setup_quantum_channels(
            allocation={},
            encryption_scheme="post-quantum"
        )

    @with_retry(max_tries=3, max_time=30)
    async def _init_qos_monitoring(self):
        """Initialize QoS monitoring with retry"""
        return await self._initialize_qos_monitoring()
    
    async def allocate_bandwidth(self, request: Dict):
        """Allocate network bandwidth with quantum security and HA support"""
        try:
            # Encrypt sensitive request data
            encrypted_request = await security_manager.encrypt_data(str(request))
            
            # Check if we're the leader
            if ha_manager.current_role != NodeRole.LEADER:
                self.logger.warning(
                    "Bandwidth allocation request on non-leader node",
                    node_role=str(ha_manager.current_role)
                )
                if ha_manager.current_leader:
                    self.logger.info("Forwarding request to leader node",
                                   leader=ha_manager.current_leader)
                    # Forward the request to the leader
                    import httpx
                    async with httpx.AsyncClient() as client:
                        try:
                            leader_address = ha_manager.cluster_nodes[ha_manager.current_leader]["address"]
                            response = await client.post(f"{leader_address}/allocate_bandwidth", json=request)
                            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                            return response.json()
                        except httpx.HTTPError as e:
                            self.logger.error(f"Failed to forward request to leader: {e}")
                            raise
                else:
                    raise ValueError("No leader available for bandwidth allocation")
            
            # Record metrics before optimization
            self.metrics.record_metric("bandwidth_request", {
                "requested": request.get("bandwidth", 0),
                "timestamp": time.time()
            })
            
            # Optimize allocation with quantum security
            optimization_result = await self.bandwidth_marketplace.optimize_network_allocation([request])
            
            if optimization_result["qos_metrics"]["reliability"] >= 0.99999:
                # Establish connection with audit logging
                connection_id = await self._establish_connection(
                    optimization_result["allocations"],
                    optimization_result["quantum_secure_channels"]
                )
                
                # Log the allocation in security audit
                security_manager.log_audit_event(
                    "bandwidth_allocation",
                    {
                        "connection_id": connection_id,
                        "allocation": str(optimization_result["allocations"]),
                        "reliability": optimization_result["qos_metrics"]["reliability"],
                        "node_id": ha_manager.node_id
                    }
                )
                
                # Record success metrics
                self.metrics.record_metric("bandwidth_allocation_success", {
                    "connection_id": connection_id,
                    "allocated": optimization_result["allocations"].get("bandwidth", 0),
                    "reliability": optimization_result["qos_metrics"]["reliability"]
                })
            
            return optimization_result
            
        except httpx.HTTPError as e:
            self.logger.error(f"Failed to forward request to leader: {e}")
            self.metrics.record_metric("bandwidth_allocation_failure", {
                "error": str(e),
                "timestamp": time.time()
            })
            raise
        except Exception as e:
            self.logger.error("Bandwidth allocation failed", error=str(e))
            self.metrics.record_metric("bandwidth_allocation_failure", {
                "error": str(e),
                "timestamp": time.time()
            })
            raise

    async def _establish_connection(self, allocation: Dict, secure_channels: Dict) -> str:
        """Establish quantum-secure network connection with HA support"""
        try:
            connection_id = f"conn_{str(uuid.uuid4())}"
            timestamp = int(time.time())
            
            self.logger.info(
                "Establishing connection",
                connection_id=connection_id,
                node_id=ha_manager.node_id
            )
            
            # Encrypt sensitive connection data
            encrypted_allocation = await security_manager.encrypt_data(str(allocation))
            encrypted_channels = await security_manager.encrypt_data(str(secure_channels))
            
            connection_data = {
                "allocation": encrypted_allocation,
                "secure_channels": encrypted_channels,
                "status": "active",
                "created_at": timestamp,
                "last_active": timestamp,
                "latency": allocation.get("latency_estimates", {}).get("avg_latency", 0),
                "node_id": ha_manager.node_id,
                "cluster_state": str(ha_manager.current_state)
            }
            
            # Store connection info with encryption
            self.active_connections[connection_id] = connection_data
            
            # Cleanup stale connections
            await self._cleanup_stale_connections()
            
            # Log successful connection
            security_manager.log_audit_event(
                "connection_established",
                {
                    "connection_id": connection_id,
                    "node_id": ha_manager.node_id,
                    "timestamp": timestamp
                }
            )
            
            # Record connection metrics
            self.metrics.record_metric("connection_established", {
                "connection_id": connection_id,
                "latency": connection_data["latency"],
                "timestamp": timestamp
            })
            
            self.logger.info("Connection established successfully",
                           connection_id=connection_id,
                           node_id=ha_manager.node_id)
            return connection_id
            
        except Exception as e:
            self.logger.error(
                "Failed to establish connection",
                error=str(e),
                connection_id=connection_id if 'connection_id' in locals() else None
            )
            self.metrics.record_metric("connection_failure", {
                "error": str(e),
                "timestamp": time.time()
            })
            raise

    async def _cleanup_stale_connections(self, max_idle_time: int = None):
        """Remove connections that have been idle for too long"""
        try:
            current_time = int(time.time())
            max_idle = max_idle_time or self.connection_timeout
            
            self.logger.info("Starting connection cleanup",
                           active_connections=len(self.active_connections))
            
            stale_connections = []
            for conn_id, conn in self.active_connections.items():
                # Check if connection is actually active
                try:
                    if not await self._verify_connection_active(conn):
                        stale_connections.append(conn_id)
                        continue
                    
                    # Check idle time
                    if current_time - conn["last_active"] > max_idle:
                        stale_connections.append(conn_id)
                        continue
                        
                    # Verify quantum channel integrity
                    if not await self._verify_quantum_channel(conn):
                        stale_connections.append(conn_id)
                        continue
                except Exception as e:
                    self.logger.warning(f"Error checking connection {conn_id}: {e}")
                    stale_connections.append(conn_id)
            
            # Remove stale connections
            for conn_id in stale_connections:
                await self._gracefully_terminate_connection(conn_id)
                
            self.logger.info("Connection cleanup completed",
                           removed_connections=len(stale_connections),
                           remaining_connections=len(self.active_connections))
                           
        except Exception as e:
            self.logger.error(f"Connection cleanup failed: {e}")
            self.metrics.record_metric("cleanup_failure", True, {"error": str(e)})

    async def _verify_connection_active(self, connection: Dict) -> bool:
        """Verify if a connection is still active and healthy"""
        try:
            # Decrypt connection data
            allocation = await security_manager.decrypt_data(connection["allocation"])
            channels = await security_manager.decrypt_data(connection["secure_channels"])
            
            # Verify bandwidth allocation is still valid
            if not await self.bandwidth_marketplace.verify_allocation(allocation):
                return False
                
            # Check quantum channel integrity
            if not await self.quantum_controller.verify_channels(channels):
                return False
                
            return True
        except Exception as e:
            self.logger.debug(f"Connection verification failed: {e}")
            return False

    async def _gracefully_terminate_connection(self, conn_id: str):
        """Gracefully terminate a connection and cleanup resources"""
        try:
            connection = self.active_connections[conn_id]
            
            # Release quantum resources
            await self.quantum_controller.release_channels(
                await security_manager.decrypt_data(connection["secure_channels"])
            )
            
            # Release bandwidth allocation
            await self.bandwidth_marketplace.release_allocation(
                await security_manager.decrypt_data(connection["allocation"])
            )
            
            # Log termination
            self.logger.info(f"Connection {conn_id} terminated gracefully")
            self.metrics.record_metric("connection_terminated", {
                "connection_id": conn_id,
                "reason": "cleanup",
                "timestamp": time.time()
            })
            
            # Remove from active connections
            del self.active_connections[conn_id]
            
        except Exception as e:
            self.logger.error(f"Failed to gracefully terminate connection {conn_id}: {e}")
            # Force remove the connection in case of failure
            self.active_connections.pop(conn_id, None)

    async def _verify_quantum_channel(self, connection: Dict) -> bool:
        """Verify quantum channel integrity"""
        try:
            channels = await security_manager.decrypt_data(connection["secure_channels"])
            return await self.quantum_controller.verify_channel_integrity(channels)
        except Exception as e:
            self.logger.debug(f"Quantum channel verification failed: {e}")
            return False

    async def _calculate_current_qos(self) -> Dict[str, Any]:
        """Calculate current QoS metrics"""
        try:
            active_count = len(self.active_connections)
            if active_count == 0:
                return {"status": "idle"}
                
            metrics = {
                "active_connections": active_count,
                "connection_success_rate": await self._calculate_success_rate(),
                "avg_latency": await self._calculate_avg_latency(),
                "bandwidth_utilization": await self._calculate_bandwidth_utilization()
            }
            
            print(f"[NetworkManager] QoS metrics updated: {metrics}")
            return metrics
            
        except Exception as e:
            print(f"[NetworkManager] ERROR: Failed to calculate QoS metrics: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _calculate_success_rate(self) -> float:
        """Calculate connection success rate"""
        try:
            total = len(self.active_connections)
            if total == 0:
                return 1.0
            successful = sum(1 for conn in self.active_connections.values() 
                           if conn["status"] == "active")
            return successful / total
        except Exception as e:
            print(f"[NetworkManager] ERROR: Failed to calculate success rate: {str(e)}")
            return 0.0

    async def _calculate_avg_latency(self) -> float:
        """Calculate average network latency"""
        try:
            if not self.active_connections:
                return 0.0
            total_latency = sum(conn.get("latency", 0) 
                              for conn in self.active_connections.values())
            return total_latency / len(self.active_connections)
        except Exception as e:
            print(f"[NetworkManager] ERROR: Failed to calculate average latency: {str(e)}")
            return 0.0

    async def _calculate_bandwidth_utilization(self) -> float:
        """Calculate current bandwidth utilization"""
        try:
            total_allocated = sum(conn["allocation"].get("bandwidth", 0) 
                                for conn in self.active_connections.values())
            max_bandwidth = self.max_bandwidth  # Use the configured max bandwidth
            return (total_allocated / max_bandwidth) * 100
        except Exception as e:
            print(f"[NetworkManager] ERROR: Failed to calculate bandwidth utilization: {str(e)}")
            return 0.0

    async def _initialize_qos_monitoring(self) -> Dict[str, Any]:
        """Initialize QoS monitoring system"""
        try:
            initial_metrics = {
                "status": "initializing",
                "active_connections": 0,
                "connection_success_rate": 1.0,
                "avg_latency": 0,
                "bandwidth_utilization": 0
            }
            print("[NetworkManager] QoS monitoring system initialized")
            return initial_metrics
        except Exception as e:
            print(f"[NetworkManager] ERROR: Failed to initialize QoS monitoring: {str(e)}")
            raise

async def main():
    """Main entry point for the network system"""
    try:
        print("[Main] Starting AstraLink Network System...")
        network_manager = NetworkManager()
        
        # Initialize the network
        init_result = await network_manager.initialize_network()
        print(f"[Main] Network initialization result: {init_result}")
        
        # Keep the system running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"[Main] CRITICAL: System failed to start: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Main] Shutting down AstraLink Network System...")
    except Exception as e:
        print(f"[Main] FATAL: Unhandled exception: {str(e)}")
        raise
