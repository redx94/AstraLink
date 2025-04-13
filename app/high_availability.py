"""
High Availability Manager - Handles failover, load balancing, and service discovery
"""
import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple
import time
import random
import socket
import aiohttp
from dataclasses import dataclass
from enum import Enum
import json
from .logging_config import get_logger
from .config import get_settings
from .monitoring import metrics_collector
from core.connection_pool import pool_manager
from core.rate_limiter import rate_limiter
from core.error_recovery import error_recovery_manager, ResourceType, OperationType

logger = get_logger(__name__)

class NodeState(Enum):
    ACTIVE = "active"
    STANDBY = "standby"
    FAILING = "failing"
    FAILED = "failed"
    RECOVERING = "recovering"

class ServiceType(Enum):
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    BLOCKCHAIN = "blockchain"
    QUANTUM = "quantum"

@dataclass
class Node:
    id: str
    host: str
    port: int
    service_type: ServiceType
    state: NodeState
    last_heartbeat: float
    load: float = 0.0
    priority: int = 0
    capabilities: Set[str] = None
    metadata: Dict[str, Any] = None

class LoadBalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_LOAD = "least_load"
    WEIGHTED = "weighted"
    LATENCY_BASED = "latency_based"

class HAManager:
    """High Availability Manager"""
    def __init__(self):
        self.settings = get_settings()
        self.config = getattr(self.settings, 'high_availability', {})
        self.nodes: Dict[str, Node] = {}
        self.service_nodes: Dict[ServiceType, List[str]] = {
            service_type: [] for service_type in ServiceType
        }
        self.node_stats: Dict[str, Dict[str, Any]] = {}
        self.failover_in_progress: Set[str] = set()
        self.load_balancing_strategy = LoadBalancingStrategy(
            self.config.get('load_balancing', {}).get('strategy', 'round_robin')
        )
        self._round_robin_counters = {
            service_type: 0 for service_type in ServiceType
        }
        
        # Start background tasks
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._load_monitoring_loop())
        asyncio.create_task(self._service_discovery_loop())

    async def register_node(self, 
                          host: str,
                          port: int,
                          service_type: ServiceType,
                          capabilities: Optional[Set[str]] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """Register a new node"""
        try:
            node_id = f"{host}:{port}"
            
            # Check if node already exists
            if node_id in self.nodes:
                logger.warning(f"Node {node_id} already registered")
                return node_id
            
            # Create new node
            node = Node(
                id=node_id,
                host=host,
                port=port,
                service_type=service_type,
                state=NodeState.STANDBY,
                last_heartbeat=time.time(),
                capabilities=capabilities or set(),
                metadata=metadata or {}
            )
            
            # Add to nodes and service_nodes
            self.nodes[node_id] = node
            self.service_nodes[service_type].append(node_id)
            
            # Initialize node stats
            self.node_stats[node_id] = {
                'connections': 0,
                'load': 0.0,
                'latency': 0.0,
                'success_rate': 1.0,
                'last_check': time.time()
            }
            
            # Record metric
            await metrics_collector.record_metric(
                f"node_registration",
                1,
                labels={
                    'node_id': node_id,
                    'service_type': service_type.value
                }
            )
            
            logger.info(f"Registered new node: {node_id}")
            return node_id
            
        except Exception as e:
            logger.error(f"Failed to register node: {e}")
            raise

    async def deregister_node(self, node_id: str):
        """Deregister a node"""
        try:
            if node_id not in self.nodes:
                logger.warning(f"Node {node_id} not found")
                return
                
            node = self.nodes[node_id]
            
            # Remove from nodes and service_nodes
            del self.nodes[node_id]
            self.service_nodes[node.service_type].remove(node_id)
            
            # Remove stats
            if node_id in self.node_stats:
                del self.node_stats[node_id]
                
            # Record metric
            await metrics_collector.record_metric(
                f"node_deregistration",
                1,
                labels={
                    'node_id': node_id,
                    'service_type': node.service_type.value
                }
            )
            
            logger.info(f"Deregistered node: {node_id}")
            
        except Exception as e:
            logger.error(f"Failed to deregister node: {e}")

    async def get_node(self, 
                      service_type: ServiceType,
                      capabilities: Optional[Set[str]] = None) -> Optional[Node]:
        """Get a node based on load balancing strategy"""
        try:
            # Get eligible nodes
            eligible_nodes = [
                node_id for node_id in self.service_nodes[service_type]
                if self.nodes[node_id].state == NodeState.ACTIVE and
                (not capabilities or capabilities.issubset(self.nodes[node_id].capabilities))
            ]
            
            if not eligible_nodes:
                logger.warning(f"No eligible nodes found for {service_type}")
                return None
                
            # Apply load balancing strategy
            if self.load_balancing_strategy == LoadBalancingStrategy.ROUND_ROBIN:
                node_id = await self._round_robin_select(service_type, eligible_nodes)
            elif self.load_balancing_strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                node_id = await self._least_connections_select(eligible_nodes)
            elif self.load_balancing_strategy == LoadBalancingStrategy.LEAST_LOAD:
                node_id = await self._least_load_select(eligible_nodes)
            elif self.load_balancing_strategy == LoadBalancingStrategy.WEIGHTED:
                node_id = await self._weighted_select(eligible_nodes)
            elif self.load_balancing_strategy == LoadBalancingStrategy.LATENCY_BASED:
                node_id = await self._latency_based_select(eligible_nodes)
            else:
                node_id = random.choice(eligible_nodes)
                
            return self.nodes[node_id]
            
        except Exception as e:
            logger.error(f"Failed to get node: {e}")
            return None

    async def _round_robin_select(self, service_type: ServiceType, eligible_nodes: List[str]) -> str:
        """Round-robin node selection"""
        try:
            if not eligible_nodes:
                raise ValueError("No eligible nodes")
                
            counter = self._round_robin_counters[service_type]
            node_id = eligible_nodes[counter % len(eligible_nodes)]
            self._round_robin_counters[service_type] = (counter + 1) % len(eligible_nodes)
            return node_id
            
        except Exception as e:
            logger.error(f"Round-robin selection failed: {e}")
            return eligible_nodes[0]

    async def _least_connections_select(self, eligible_nodes: List[str]) -> str:
        """Least connections node selection"""
        try:
            return min(
                eligible_nodes,
                key=lambda node_id: self.node_stats[node_id]['connections']
            )
        except Exception as e:
            logger.error(f"Least connections selection failed: {e}")
            return eligible_nodes[0]

    async def _least_load_select(self, eligible_nodes: List[str]) -> str:
        """Least load node selection"""
        try:
            return min(
                eligible_nodes,
                key=lambda node_id: self.node_stats[node_id]['load']
            )
        except Exception as e:
            logger.error(f"Least load selection failed: {e}")
            return eligible_nodes[0]

    async def _weighted_select(self, eligible_nodes: List[str]) -> str:
        """Weighted node selection"""
        try:
            weights = [
                1.0 / (self.nodes[node_id].priority + 1)
                for node_id in eligible_nodes
            ]
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            return random.choices(eligible_nodes, normalized_weights)[0]
            
        except Exception as e:
            logger.error(f"Weighted selection failed: {e}")
            return eligible_nodes[0]

    async def _latency_based_select(self, eligible_nodes: List[str]) -> str:
        """Latency-based node selection"""
        try:
            return min(
                eligible_nodes,
                key=lambda node_id: self.node_stats[node_id]['latency']
            )
        except Exception as e:
            logger.error(f"Latency-based selection failed: {e}")
            return eligible_nodes[0]

    async def update_node_state(self, node_id: str, state: NodeState):
        """Update node state"""
        try:
            if node_id not in self.nodes:
                logger.warning(f"Node {node_id} not found")
                return
                
            old_state = self.nodes[node_id].state
            self.nodes[node_id].state = state
            
            # Record state change metric
            await metrics_collector.record_metric(
                f"node_state_change",
                1,
                labels={
                    'node_id': node_id,
                    'old_state': old_state.value,
                    'new_state': state.value
                }
            )
            
            logger.info(f"Node {node_id} state changed: {old_state} -> {state}")
            
            # Handle state changes
            if state == NodeState.FAILING:
                asyncio.create_task(self._handle_failing_node(node_id))
            elif state == NodeState.FAILED:
                asyncio.create_task(self._handle_failed_node(node_id))
            elif state == NodeState.RECOVERING:
                asyncio.create_task(self._handle_recovering_node(node_id))
                
        except Exception as e:
            logger.error(f"Failed to update node state: {e}")

    async def _handle_failing_node(self, node_id: str):
        """Handle a failing node"""
        try:
            node = self.nodes[node_id]
            
            # Start failover if not already in progress
            if node_id not in self.failover_in_progress:
                self.failover_in_progress.add(node_id)
                
                # Find backup node
                backup_nodes = [
                    n_id for n_id in self.service_nodes[node.service_type]
                    if n_id != node_id and self.nodes[n_id].state == NodeState.STANDBY
                ]
                
                if backup_nodes:
                    backup_node_id = backup_nodes[0]
                    await self.update_node_state(backup_node_id, NodeState.ACTIVE)
                    logger.info(f"Activated backup node {backup_node_id} for failing node {node_id}")
                    
                # Record failover metric
                await metrics_collector.record_metric(
                    f"node_failover_start",
                    1,
                    labels={'node_id': node_id}
                )
                
        except Exception as e:
            logger.error(f"Failed to handle failing node: {e}")

    async def _handle_failed_node(self, node_id: str):
        """Handle a failed node"""
        try:
            # Complete failover
            if node_id in self.failover_in_progress:
                self.failover_in_progress.remove(node_id)
                
                # Record failover completion metric
                await metrics_collector.record_metric(
                    f"node_failover_complete",
                    1,
                    labels={'node_id': node_id}
                )
                
            # Start recovery process
            asyncio.create_task(self._start_recovery(node_id))
            
        except Exception as e:
            logger.error(f"Failed to handle failed node: {e}")

    async def _handle_recovering_node(self, node_id: str):
        """Handle a recovering node"""
        try:
            # Monitor recovery progress
            recovery_success = await self._monitor_recovery(node_id)
            
            if recovery_success:
                await self.update_node_state(node_id, NodeState.STANDBY)
                logger.info(f"Node {node_id} recovered successfully")
            else:
                await self.update_node_state(node_id, NodeState.FAILED)
                logger.warning(f"Node {node_id} recovery failed")
                
        except Exception as e:
            logger.error(f"Failed to handle recovering node: {e}")

    async def _start_recovery(self, node_id: str):
        """Start node recovery process"""
        try:
            node = self.nodes[node_id]
            
            # Attempt to recover node
            recovery_operation = lambda: self._attempt_node_recovery(node)
            
            success = await error_recovery_manager.execute_quantum_operation(
                recovery_operation,
                OperationType.WRITE,
                fallback=lambda: self._fallback_recovery(node)
            )
            
            if success:
                await self.update_node_state(node_id, NodeState.RECOVERING)
            else:
                logger.error(f"Failed to start recovery for node {node_id}")
                
        except Exception as e:
            logger.error(f"Failed to start recovery: {e}")

    async def _attempt_node_recovery(self, node: Node) -> bool:
        """Attempt to recover a node"""
        try:
            # Simulate recovery process
            await asyncio.sleep(5)  # Replace with actual recovery logic
            return True
            
        except Exception as e:
            logger.error(f"Node recovery attempt failed: {e}")
            return False

    async def _fallback_recovery(self, node: Node) -> bool:
        """Fallback recovery procedure"""
        try:
            # Implement fallback recovery logic
            await asyncio.sleep(2)  # Replace with actual fallback logic
            return True
            
        except Exception as e:
            logger.error(f"Fallback recovery failed: {e}")
            return False

    async def _monitor_recovery(self, node_id: str) -> bool:
        """Monitor node recovery progress"""
        try:
            recovery_timeout = self.config.get('recovery', {}).get('timeout', 300)
            check_interval = self.config.get('recovery', {}).get('check_interval', 10)
            start_time = time.time()
            
            while time.time() - start_time < recovery_timeout:
                # Check node health
                if await self._check_node_health(node_id):
                    return True
                    
                await asyncio.sleep(check_interval)
                
            return False
            
        except Exception as e:
            logger.error(f"Recovery monitoring failed: {e}")
            return False

    async def _health_check_loop(self):
        """Periodic health check of all nodes"""
        while True:
            try:
                for node_id, node in self.nodes.items():
                    # Skip nodes in terminal states
                    if node.state in [NodeState.FAILED]:
                        continue
                        
                    healthy = await self._check_node_health(node_id)
                    
                    if not healthy and node.state == NodeState.ACTIVE:
                        await self.update_node_state(node_id, NodeState.FAILING)
                        
                await asyncio.sleep(self.config.get('health_check_interval', 5))
                
            except Exception as e:
                logger.error(f"Health check loop failed: {e}")
                await asyncio.sleep(5)

    async def _check_node_health(self, node_id: str) -> bool:
        """Check health of a specific node"""
        try:
            node = self.nodes[node_id]
            
            # Check connectivity
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://{node.host}:{node.port}/health",
                        timeout=self.config.get('health_check_timeout', 5)
                    ) as response:
                        healthy = response.status == 200
            except:
                healthy = False
                
            # Update stats
            self.node_stats[node_id]['last_check'] = time.time()
            self.node_stats[node_id]['success_rate'] = (
                0.9 * self.node_stats[node_id]['success_rate'] +
                0.1 * (1.0 if healthy else 0.0)
            )
            
            # Record health check metric
            await metrics_collector.record_metric(
                f"node_health_check",
                1 if healthy else 0,
                labels={'node_id': node_id}
            )
            
            return healthy
            
        except Exception as e:
            logger.error(f"Node health check failed: {e}")
            return False

    async def _load_monitoring_loop(self):
        """Monitor load on all nodes"""
        while True:
            try:
                for node_id, node in self.nodes.items():
                    if node.state == NodeState.ACTIVE:
                        # Update load statistics
                        stats = await self._get_node_stats(node_id)
                        self.node_stats[node_id].update(stats)
                        
                        # Check load thresholds
                        if stats['load'] > self.config.get('load_threshold', 0.8):
                            logger.warning(f"Node {node_id} load exceeds threshold: {stats['load']}")
                            
                await asyncio.sleep(self.config.get('load_check_interval', 60))
                
            except Exception as e:
                logger.error(f"Load monitoring failed: {e}")
                await asyncio.sleep(5)

    async def _get_node_stats(self, node_id: str) -> Dict[str, Any]:
        """Get statistics for a node"""
        try:
            node = self.nodes[node_id]
            
            # Get stats from node
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://{node.host}:{node.port}/stats",
                        timeout=self.config.get('stats_timeout', 5)
                    ) as response:
                        if response.status == 200:
                            return await response.json()
            except:
                pass
                
            # Return default stats if request fails
            return {
                'load': self.node_stats[node_id].get('load', 0.0),
                'connections': self.node_stats[node_id].get('connections', 0),
                'latency': self.node_stats[node_id].get('latency', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get node stats: {e}")
            return {'load': 0.0, 'connections': 0, 'latency': 0.0}

    async def _service_discovery_loop(self):
        """Service discovery and registration loop"""
        while True:
            try:
                # Discover new nodes
                await self._discover_nodes()
                
                # Clean up stale nodes
                await self._cleanup_stale_nodes()
                
                await asyncio.sleep(self.config.get('discovery_interval', 300))
                
            except Exception as e:
                logger.error(f"Service discovery failed: {e}")
                await asyncio.sleep(5)

    async def _discover_nodes(self):
        """Discover new nodes in the network"""
        try:
            # Implement service discovery logic
            # This could use DNS, consul, etcd, etc.
            pass
            
        except Exception as e:
            logger.error(f"Node discovery failed: {e}")

    async def _cleanup_stale_nodes(self):
        """Clean up stale node registrations"""
        try:
            current_time = time.time()
            stale_timeout = self.config.get('stale_timeout', 300)
            
            stale_nodes = [
                node_id for node_id, node in self.nodes.items()
                if current_time - node.last_heartbeat > stale_timeout
            ]
            
            for node_id in stale_nodes:
                logger.warning(f"Removing stale node: {node_id}")
                await self.deregister_node(node_id)
                
        except Exception as e:
            logger.error(f"Stale node cleanup failed: {e}")

# Global HA manager instance
ha_manager = HAManager()
