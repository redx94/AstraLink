#!/usr/bin/env python3

"""
AstraLink Quantum Readiness Check
================================

Validates system capabilities for quantum operations, including:
- CPU features for quantum computations
- Memory requirements for quantum states
- Hardware encryption support
- TPM for quantum key storage
- System timing precision

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
"""

import os
import sys
import cpuinfo
import psutil
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path
import subprocess
import logging
from logging_config import get_logger

logger = get_logger(__name__)

class QuantumReadinessChecker:
    def __init__(self):
        self.cpu_info = cpuinfo.get_cpu_info()
        self.memory_info = psutil.virtual_memory()
        self.required_features = {
            'cpu': [
                'avx2',        # Required for quantum state vectors
                'aes',         # Hardware encryption
                'pclmulqdq',   # Polynomial multiplication
                'rdseed',      # Hardware random number generation
                'rdrnd'        # Hardware random number generation
            ],
            'memory': 32 * 1024 * 1024 * 1024,  # 32GB minimum
            'timing_precision': 1e-6              # 1 microsecond
        }

    def check_cpu_features(self) -> Tuple[bool, List[str]]:
        """Check CPU features required for quantum operations"""
        try:
            missing_features = []
            flags = self.cpu_info.get('flags', [])
            
            for feature in self.required_features['cpu']:
                if feature not in flags:
                    missing_features.append(feature)
            
            success = len(missing_features) == 0
            logger.info(
                "CPU feature check",
                extra={
                    'success': success,
                    'missing': missing_features
                }
            )
            
            return success, missing_features
            
        except Exception as e:
            logger.error(f"CPU feature check failed: {e}")
            return False, self.required_features['cpu']

    def check_memory(self) -> Tuple[bool, Dict]:
        """Check memory requirements for quantum states"""
        try:
            total_memory = self.memory_info.total
            memory_sufficient = total_memory >= self.required_features['memory']
            
            result = {
                'total_memory': total_memory,
                'required_memory': self.required_features['memory'],
                'available_memory': self.memory_info.available,
                'sufficient': memory_sufficient
            }
            
            logger.info(
                "Memory check",
                extra={
                    'success': memory_sufficient,
                    'details': result
                }
            )
            
            return memory_sufficient, result
            
        except Exception as e:
            logger.error(f"Memory check failed: {e}")
            return False, {}

    def check_tpm(self) -> Tuple[bool, str]:
        """Check TPM availability for quantum key storage"""
        try:
            # Check TPM 2.0 device
            tpm_path = Path("/dev/tpm0")
            if not tpm_path.exists():
                return False, "TPM device not found"
                
            # Check TPM capabilities
            result = subprocess.run(
                ["tpm2_getcap", "properties-fixed"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return False, "TPM capability check failed"
                
            # Verify TPM version and algorithms
            if "TPM2_ALG_RSA" not in result.stdout or "TPM2_ALG_ECC" not in result.stdout:
                return False, "TPM missing required algorithms"
                
            logger.info("TPM check passed")
            return True, "TPM 2.0 available and capable"
            
        except Exception as e:
            logger.error(f"TPM check failed: {e}")
            return False, str(e)

    def check_timing_precision(self) -> Tuple[bool, float]:
        """Check system timing precision for quantum operations"""
        try:
            # Measure time precision using high-resolution timer
            samples = []
            for _ in range(1000):
                start = time.perf_counter_ns()
                end = time.perf_counter_ns()
                samples.append(end - start)
                
            precision = np.mean(samples) / 1e9  # Convert to seconds
            sufficient = precision <= self.required_features['timing_precision']
            
            logger.info(
                "Timing precision check",
                extra={
                    'success': sufficient,
                    'precision': precision
                }
            )
            
            return sufficient, precision
            
        except Exception as e:
            logger.error(f"Timing check failed: {e}")
            return False, float('inf')

    def check_encryption_support(self) -> Tuple[bool, Dict]:
        """Check hardware encryption support"""
        try:
            # Check CPU AES-NI support
            aesni_support = 'aes' in self.cpu_info.get('flags', [])
            
            # Check kernel crypto API
            with open('/proc/crypto', 'r') as f:
                crypto_content = f.read()
                
            required_algorithms = {
                'aes': False,
                'gcm(aes)': False,
                'sha256': False,
                'sha512': False
            }
            
            for line in crypto_content.split('\n'):
                if 'name' in line:
                    name = line.split(':')[1].strip()
                    if name in required_algorithms:
                        required_algorithms[name] = True
                        
            all_algorithms = all(required_algorithms.values())
            
            result = {
                'aesni_support': aesni_support,
                'required_algorithms': required_algorithms,
                'sufficient': aesni_support and all_algorithms
            }
            
            logger.info(
                "Encryption support check",
                extra={
                    'success': result['sufficient'],
                    'details': result
                }
            )
            
            return result['sufficient'], result
            
        except Exception as e:
            logger.error(f"Encryption check failed: {e}")
            return False, {}

    def run_all_checks(self) -> Dict:
        """Run all quantum readiness checks"""
        results = {
            'cpu_features': self.check_cpu_features(),
            'memory': self.check_memory(),
            'tpm': self.check_tpm(),
            'timing': self.check_timing_precision(),
            'encryption': self.check_encryption_support()
        }
        
        success = all(result[0] for result in results.values())
        
        if success:
            logger.info("All quantum readiness checks passed")
        else:
            logger.error("Some quantum readiness checks failed")
            
        return {
            'success': success,
            'details': results
        }

def main():
    checker = QuantumReadinessChecker()
    results = checker.run_all_checks()
    
    if results['success']:
        print("\n✅ System is quantum-ready!")
        sys.exit(0)
    else:
        print("\n❌ System does not meet quantum requirements:")
        
        if not results['details']['cpu_features'][0]:
            print("- Missing CPU features:", ", ".join(results['details']['cpu_features'][1]))
            
        if not results['details']['memory'][0]:
            mem = results['details']['memory'][1]
            print(f"- Insufficient memory: {mem['total_memory']/1024**3:.1f}GB available, {mem['required_memory']/1024**3:.1f}GB required")
            
        if not results['details']['tpm'][0]:
            print("- TPM issue:", results['details']['tpm'][1])
            
        if not results['details']['timing'][0]:
            print(f"- Insufficient timing precision: {results['details']['timing'][1]*1e6:.1f}µs (required: {1:.1f}µs)")
            
        if not results['details']['encryption'][0]:
            enc = results['details']['encryption'][1]
            if not enc['aesni_support']:
                print("- Missing AES-NI support")
            missing_algos = [algo for algo, supported in enc['required_algorithms'].items() if not supported]
            if missing_algos:
                print("- Missing encryption algorithms:", ", ".join(missing_algos))
                
        sys.exit(1)

if __name__ == "__main__":
    main()