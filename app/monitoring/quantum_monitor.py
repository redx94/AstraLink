"""
Quantum Monitoring Module
Handles quantum system monitoring including error rates, fidelity, and coherence.
"""

import time
from typing import Dict, Any
from app.quantum_interface import QuantumSystem
from quantum.quantum_error_correction import QuantumErrorCorrection
from .models import QuantumMetrics
from app.logging_config import get_logger

logger = get_logger(__name__)

class QuantumMonitor:
    def __init__(self, thresholds: Dict[str, Any]):
        self.thresholds = thresholds
        self.quantum_system = QuantumSystem()
        self.error_correction = QuantumErrorCorrection()

    async def check_quantum_health(self) -> Dict[str, Any]:
        """Check quantum system health using actual measurements"""
        try:
            # Check basic system health
            system_health = await self.quantum_system.check_health()
            if not system_health:
                return {
                    "status": "critical",
                    "error": "Quantum system not responding",
                    "metrics": None,
                    "timestamp": time.time()
                }

            # Get quantum circuit metrics
            test_circuit = self.error_correction.surface_code
            fidelity = await self.quantum_system._estimate_fidelity(test_circuit)

            # Calculate error rate from recent error correction results
            error_rate = 1.0 - fidelity

            # Measure coherence time using quantum interface
            coherence_results = await self.quantum_system._execute_with_error_mitigation(
                operation='H',  # Hadamard gate for superposition
                qubits=[0],    # Use first qubit
                params=None
            )
            coherence_time = coherence_results.get('coherence_time', 100) if coherence_results else 100

            # Get gate fidelity from quantum system
            gate_fidelity = await self.quantum_system._estimate_fidelity(
                self.quantum_system._create_quantum_circuit('CNOT', [0, 1])
            )

            metrics = QuantumMetrics(
                error_rate=error_rate,
                fidelity=fidelity,
                coherence_time=coherence_time,
                gate_fidelity=gate_fidelity,
                timestamp=time.time()
            )

            status = "healthy"
            warnings = []

            # Check quantum thresholds
            if error_rate > self.thresholds.get("quantum_error_rate", 0.001):
                status = "warning"
                warnings.append(f"High quantum error rate: {error_rate:.4%}")

            if fidelity < self.thresholds.get("min_fidelity", 0.95):
                status = "warning"
                warnings.append(f"Low quantum fidelity: {fidelity:.4%}")

            if gate_fidelity < self.thresholds.get("min_gate_fidelity", 0.99):
                status = "warning"
                warnings.append(f"Low gate fidelity: {gate_fidelity:.4%}")

            if coherence_time < self.thresholds.get("min_coherence_time", 50):
                status = "warning"
                warnings.append(f"Short coherence time: {coherence_time:.1f}μs")

            return {
                "status": status,
                "warnings": warnings,
                "metrics": metrics
            }

        except Exception as e:
            logger.error("Quantum health check failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "metrics": None
            }

    async def collect_and_monitor_metrics(
        self,
        fidelity: float,
        error_rate: float,
        correction_success_rate: float,
        resource_usage: Dict[str, float]
    ) -> Dict[str, Any]:
        """Collect and monitor specific metrics to evaluate quantum error correction"""
        try:
            # Record individual metrics
            metrics = {
                "fidelity": fidelity,
                "error_rate": error_rate,
                "correction_success": correction_success_rate,
                "resource_usage": resource_usage,
                "timestamp": time.time()
            }

            # Analyze error correction effectiveness
            effectiveness = {
                "improvement": 1 - (error_rate / self.thresholds.get("base_error_rate", 0.1)),
                "resource_efficiency": correction_success_rate / sum(resource_usage.values()),
                "overall_quality": fidelity * correction_success_rate
            }

            # Determine optimization recommendations
            recommendations = []
            if error_rate > self.thresholds.get("quantum_error_rate", 0.001):
                recommendations.append("Increase error correction cycles")
            if resource_usage.get("memory", 0) > self.thresholds.get("memory_usage", 80):
                recommendations.append("Optimize memory usage in error correction")
            if fidelity < self.thresholds.get("min_fidelity", 0.95):
                recommendations.append("Recalibrate quantum gates")

            return {
                "metrics": metrics,
                "effectiveness": effectiveness,
                "recommendations": recommendations
            }

        except Exception as e:
            logger.error("Failed to collect quantum metrics", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }