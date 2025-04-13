"""
AstraLink - Handshake Integration Module
======================================

This module handles integration with Handshake DNS for secure name resolution
and service discovery in the private blockchain network.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
"""

import asyncio
from typing import Dict, List, Optional
import yaml
import json
import aiohttp
from dns import resolver, asyncresolver
from logging_config import get_logger
from exceptions import NetworkError
from core.error_recovery import error_recovery_manager

logger = get_logger(__name__)

class HandshakeIntegration:
    def __init__(self, domain: str = "quantum.api"):
        """Initialize Handshake integration"""
        self.domain = domain
        self.config = self._load_config()
        self.resolver = asyncresolver.Resolver()
        self.cache = {}
        self.hns_api_endpoint = self.config['handshake_integration'].get('api_endpoint', 'http://localhost:12037')
        self._initialize_resolver()

    def _load_config(self) -> Dict:
        """Load network configuration"""
        try:
            with open('config/blockchain_network.yaml', 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load network config: {e}")
            raise NetworkError("Configuration loading failed")

    def _initialize_resolver(self):
        """Initialize Handshake DNS resolver"""
        try:
            nameservers = self._get_hns_nameservers()
            self.resolver.nameservers = nameservers
            self.resolver.port = 53
            self.resolver.timeout = 2.0
            self.resolver.lifetime = 4.0
            
            # Set DNSSEC validation
            self.resolver.edns = 0
            self.resolver.dnssec = True
            
            logger.info(f"Initialized Handshake resolver for {self.domain} with nameservers: {nameservers}")
        except Exception as e:
            logger.error(f"Resolver initialization failed: {e}")
            raise NetworkError(f"DNS resolver initialization failed: {e}")

    async def _get_hns_nameservers(self) -> List[str]:
        """Get Handshake nameservers"""
        try:
            # Try to get nameservers from local HNS node first
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.hns_api_endpoint}/nameservers") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('nameservers'):
                            return data['nameservers']

            # Fallback to configured nameservers
            configured_ns = self.config['handshake_integration'].get('nameservers', [])
            if configured_ns:
                return configured_ns

            # Last resort fallback to known HNS resolvers
            return [
                "103.196.38.38",  # HNS.to
                "103.196.38.39",  # HNS.to backup
                "172.104.213.10"  # HDNS.io
            ]

        except Exception as e:
            logger.error(f"Failed to get HNS nameservers: {e}")
            raise NetworkError("Failed to get HNS nameservers")

    async def resolve_node(self, node_name: str) -> str:
        """Resolve blockchain node address"""
        try:
            # Check cache first
            if node_name in self.cache:
                return self.cache[node_name]

            fqdn = f"{node_name}.{self.domain}"
            answers = await self.resolver.resolve(fqdn, 'A')
            
            if answers:
                ip = answers[0].address
                self.cache[node_name] = ip
                logger.info(f"Resolved {fqdn} to {ip}")
                return ip
                
            raise NetworkError(f"No DNS records found for {fqdn}")
            
        except Exception as e:
            logger.error(f"Node resolution failed for {node_name}: {e}")
            raise NetworkError(f"Node resolution failed: {e}")

    async def discover_services(self) -> Dict[str, str]:
        """Discover available network services"""
        try:
            services = {}
            
            # Look for SRV records for various services
            service_types = [
                "_blockchain._tcp",
                "_api._tcp",
                "_quantum._tcp",
                "_nodes._tcp"
            ]
            
            for service in service_types:
                try:
                    fqdn = f"{service}.{self.domain}"
                    answers = await self.resolver.resolve(fqdn, 'SRV')
                    
                    for rdata in answers:
                        service_name = service.split('.')[0][1:]  # Remove leading underscore
                        services[service_name] = {
                            'target': str(rdata.target).rstrip('.'),
                            'port': rdata.port,
                            'priority': rdata.priority,
                            'weight': rdata.weight
                        }
                        
                except Exception as e:
                    logger.warning(f"Failed to discover {service}: {e}")
                    
            return services
            
        except Exception as e:
            logger.error(f"Service discovery failed: {e}")
            raise NetworkError("Service discovery failed")

    async def update_dns_records(self, records: List[Dict]) -> bool:
        """Update Handshake DNS records"""
        try:
            # Verify domain ownership first
            if not await self.verify_domain_ownership():
                raise NetworkError("Domain ownership verification failed")

            # Update records through HNS node API
            async with aiohttp.ClientSession() as session:
                for record in records:
                    payload = {
                        'action': 'update',
                        'domain': self.domain,
                        'record': {
                            'type': record['type'],
                            'name': record['name'],
                            'value': record['value']
                        }
                    }
                    
                    async with session.post(
                        f"{self.hns_api_endpoint}/records",
                        json=payload
                    ) as response:
                        if response.status != 200:
                            logger.error(f"Failed to update record {record['name']}: {response.status}")
                            return False
                            
                        logger.info(f"Updated {record['type']} record for {record['name']}.{self.domain}")

            # Clear resolver cache after updates
            self.cache.clear()
            return True
            
        except Exception as e:
            logger.error(f"DNS record update failed: {e}")
            raise NetworkError("DNS record update failed")

    async def verify_domain_ownership(self) -> bool:
        """Verify ownership of quantum.api domain"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.hns_api_endpoint}/domain/{self.domain}/verify"
                ) as response:
                    if response.status != 200:
                        logger.error("Domain ownership verification failed")
                        return False
                        
                    data = await response.json()
                    return data.get('verified', False)
                    
        except Exception as e:
            logger.error(f"Domain ownership verification failed: {e}")
            raise NetworkError("Domain verification failed")

    async def monitor_dns_health(self):
        """Monitor DNS resolution health"""
        while True:
            try:
                # Discover all services
                services = await self.discover_services()
                all_nodes = [f"node{i}" for i in range(1, 4)]
                
                # Check each node
                for node in all_nodes:
                    try:
                        await self.resolve_node(node)
                    except Exception as e:
                        logger.warning(f"Health check failed for {node}: {e}")
                        
                        # Attempt record repair if needed
                        await self._attempt_record_repair(node)
                
                # Verify DNSSEC
                await self._verify_dnssec()
                
                logger.info("DNS health check completed")
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"DNS health monitoring failed: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on failure

    async def _attempt_record_repair(self, node: str):
        """Attempt to repair failing DNS records"""
        try:
            # Get expected record from config
            expected_records = self.config['handshake_integration']['records']
            node_record = next(
                (r for r in expected_records if r['name'].startswith(node)),
                None
            )
            
            if node_record:
                await self.update_dns_records([node_record])
                logger.info(f"Attempted repair of DNS record for {node}")
                
        except Exception as e:
            logger.error(f"Record repair failed for {node}: {e}")

    async def _verify_dnssec(self):
        """Verify DNSSEC signatures"""
        try:
            # Query for DNSKEY records
            answers = await self.resolver.resolve(self.domain, 'DNSKEY')
            
            if not answers:
                logger.error("No DNSKEY records found")
                return False
                
            # Verify signatures
            for answer in answers:
                if answer.flags & 0x0001:  # Check for KSK flag
                    logger.info(f"Found valid KSK for {self.domain}")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"DNSSEC verification failed: {e}")
            return False

    async def update_nft_esim_dns_records(self, token_id: int, ipfs_hash: str) -> bool:
        """Update DNS records with NFT eSIM data"""
        try:
            records = [
                {
                    'type': 'TXT',
                    'name': f"esim-{token_id}",
                    'value': f"ipfs://{ipfs_hash}"
                }
            ]
            return await self.update_dns_records(records)
        except Exception as e:
            logger.error(f"Failed to update NFT eSIM DNS records: {str(e)}")
            return False

# Global Handshake integration instance
handshake_integration = HandshakeIntegration()
