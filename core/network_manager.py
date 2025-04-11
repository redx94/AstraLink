import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any
from quantum.quantum_controller import QuantumController
from network.bandwidth_marketplace import QuantumSecureBandwidthMarketplace

class NetworkManager:
    """Manages quantum-classical hybrid network operations"""
    def __init__(self):
        self.quantum_controller = QuantumController()
        self.bandwidth_marketplace = QuantumSecureBandwidthMarketplace()
        self.active_connections = {}
        self.qos_metrics = {}
        self.last_maintenance = 0
        self.maintenance_interval = 300  # 5 minutes

    async def start_maintenance_loop(self):
        """Start periodic maintenance tasks"""
        while True:
            try:
                await self._perform_maintenance()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                print(f"[NetworkManager] ERROR: Maintenance loop error: {str(e)}")
                await asyncio.sleep(5)  # Brief pause on error

    async def _perform_maintenance(self):
        """Perform periodic maintenance tasks"""
        current_time = int(time.time())
        
        if current_time - self.last_maintenance < self.maintenance_interval:
            return
            
        print("[NetworkManager] Starting periodic maintenance...")
        
        try:
            # Clean up stale connections
            await self._cleanup_stale_connections()
            
            # Trigger marketplace cleanup
            await self.bandwidth_marketplace._periodic_cleanup()
            
            # Update QoS metrics
            self.qos_metrics = await self._calculate_current_qos()
            
            print("[NetworkManager] Periodic maintenance completed successfully")
            self.last_maintenance = current_time
            
        except Exception as e:
            print(f"[NetworkManager] ERROR: Maintenance failed: {str(e)}")

    async def initialize_network(self):
        """Initialize quantum-classical hybrid network"""
        try:
            print("[NetworkManager] Starting network initialization...")
            
            # Start maintenance loop in background
            asyncio.create_task(self.start_maintenance_loop())
            
            # Initialize quantum subsystem
            try:
                await self.quantum_controller.initializeQuantumSystem()
                print("[NetworkManager] Quantum system initialized successfully")
            except Exception as e:
                print(f"[NetworkManager] ERROR: Quantum system initialization failed: {str(e)}")
                raise
            
            # Setup secure channels
            try:
                quantum_channels = await self.bandwidth_marketplace._setup_quantum_channels(
                    allocation={},
                    encryption_scheme="post-quantum"
                )
                print("[NetworkManager] Secure channels established")
            except Exception as e:
                print(f"[NetworkManager] ERROR: Failed to setup secure channels: {str(e)}")
                raise
            
            # Initialize QoS monitoring
            try:
                self.qos_metrics = await self._initialize_qos_monitoring()
                print("[NetworkManager] QoS monitoring initialized")
            except Exception as e:
                print(f"[NetworkManager] ERROR: QoS monitoring initialization failed: {str(e)}")
                raise
            
            print("[NetworkManager] Network initialization completed successfully")
            return {
                "status": "initialized",
                "quantum_ready": True,
                "secure_channels": quantum_channels,
                "qos_status": self.qos_metrics
            }
        except Exception as e:
            print(f"[NetworkManager] CRITICAL: Network initialization failed: {str(e)}")
            raise
    
    async def allocate_bandwidth(self, request: Dict):
        """Allocate network bandwidth with quantum security"""
        optimization_result = await self.bandwidth_marketplace.optimize_network_allocation([request])
        
        if optimization_result["qos_metrics"]["reliability"] >= 0.99999:
            await self._establish_connection(
                optimization_result["allocations"],
                optimization_result["quantum_secure_channels"]
            )
            
        return optimization_result

    async def _establish_connection(self, allocation: Dict, secure_channels: Dict):
        """Establish quantum-secure network connection"""
        connection_id = f"conn_{str(uuid.uuid4())}"
        timestamp = int(time.time())
        
        print(f"[NetworkManager] Establishing connection {connection_id}")
        
        self.active_connections[connection_id] = {
            "allocation": allocation,
            "secure_channels": secure_channels,
            "status": "active",
            "created_at": timestamp,
            "last_active": timestamp
        }
        
        # Cleanup stale connections
        await self._cleanup_stale_connections()
        
        print(f"[NetworkManager] Connection {connection_id} established successfully")
        return connection_id

    async def _cleanup_stale_connections(self, max_idle_time: int = 3600):
        """Remove connections that have been idle for too long"""
        current_time = int(time.time())
        
        stale_connections = [
            conn_id for conn_id, conn in self.active_connections.items()
            if current_time - conn["last_active"] > max_idle_time
        ]
        
        for conn_id in stale_connections:
            print(f"[NetworkManager] Removing stale connection {conn_id}")
            del self.active_connections[conn_id]

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
            max_bandwidth = 10000  # 10 Gbps maximum theoretical bandwidth
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
