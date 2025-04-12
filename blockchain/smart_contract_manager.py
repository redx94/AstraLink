"""
AstraLink - Smart Contract Manager Module
====================================

This module handles blockchain smart contract operations including service provider
setup, plan management, service activation, and revenue distribution.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
See LICENSE file for licensing information.
"""
import os

from web3 import Web3
from typing import Dict, List, Optional, Any
import json
import asyncio
import yaml
from dns import resolver
from logging_config import get_logger
from exceptions import NetworkError, ContractError, NFTError
from datetime import datetime
import time
import hashlib
import uuid

logger = get_logger(__name__)

class SmartContractManager:
    def __init__(self, contract_address: str = None, web3_provider: str = None):
        """Initialize with optional params, will load from config if not provided"""
        self.load_network_config()
        self._connection_pool = {}
        self._cache = {}
        self._cache_ttl = self.config.get('cache', {}).get('ttl', 300)  # 5 minutes default
        self._max_pool_size = self.config.get('web3', {}).get('max_pool_size', 10)
        self._web3_instances = []
        self.web3 = self._get_web3_connection(web3_provider)
        self.contract_address = contract_address or self.config['smart_contracts']['deployment'][0]['address']
        self._load_contract()
        self.dns_resolver = resolver.Resolver()
        self.dns_resolver.nameservers = self._get_handshake_nameservers()

    def load_network_config(self):
        """Load network configuration from YAML"""
        try:
            with open('config/blockchain_network.yaml', 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info("Loaded network configuration successfully")
        except Exception as e:
            logger.error(f"Failed to load network config: {e}")
            raise NetworkError("Network configuration loading failed")

    def _get_web3_connection(self, web3_provider: Optional[str] = None) -> Web3:
        """Get a Web3 connection from the pool or create a new one"""
        try:
            # Try to get an existing connection
            for web3 in self._web3_instances:
                if web3.is_connected():
                    return web3

            # Create new connection if pool not full
            if len(self._web3_instances) < self._max_pool_size:
                web3 = self._initialize_web3(web3_provider)
                self._web3_instances.append(web3)
                return web3

            # Pool is full, find least recently used connection
            least_recent = min(self._web3_instances, key=lambda w: w._last_used)
            self._web3_instances.remove(least_recent)
            web3 = self._initialize_web3(web3_provider)
            self._web3_instances.append(web3)
            return web3

        except Exception as e:
            logger.error(f"Failed to get Web3 connection: {e}")
            raise NetworkError("Failed to establish Web3 connection")

    def _initialize_web3(self, web3_provider: Optional[str] = None) -> Web3:
        """Initialize Web3 with fallback to network nodes"""
        try:
            if web3_provider:
                web3 = Web3(Web3.HTTPProvider(web3_provider))
                web3._last_used = time.time()
                return web3
            
            # Try connecting to network nodes through Handshake DNS
            for node in self.config['dns']['bootstrap_nodes']:
                try:
                    node_ip = self._resolve_handshake_domain(node)
                    provider_url = f"http://{node_ip}:{self.config['security']['firewall_rules'][1].split(': ')[1].split(' ')[0]}"
                    web3 = Web3(Web3.HTTPProvider(
                        provider_url,
                        request_kwargs={
                            'timeout': 10,
                            'headers': {
                                'X-Client-Version': '2.0.0',
                                'X-Request-ID': str(uuid.uuid4())
                            }
                        }
                    ))
                    if web3.is_connected():
                        web3._last_used = time.time()
                        logger.info(f"Connected to network node: {node}")
                        return web3
                except Exception as e:
                    logger.warning(f"Failed to connect to {node}: {e}")
                    continue
                    
            raise NetworkError("Failed to connect to any network nodes")
            
        except Exception as e:
            logger.error(f"Web3 initialization failed: {e}")
            raise NetworkError(f"Web3 initialization failed: {e}")

    def _resolve_handshake_domain(self, domain: str) -> str:
        """Resolve Handshake domain to IP address"""
        try:
            answers = self.dns_resolver.resolve(domain, 'A')
            return answers[0].address
        except Exception as e:
            logger.error(f"Failed to resolve domain {domain}: {e}")
            raise NetworkError(f"DNS resolution failed for {domain}")

    def _get_handshake_nameservers(self) -> List[str]:
        """Get Handshake nameservers for quantum.api"""
        try:
            answers = self.dns_resolver.resolve("quantum.api", "NS")
            nameservers = [str(ns.target) for ns in answers]
            return nameservers
        except Exception as e:
            logger.error(f"Failed to get Handshake nameservers: {e}")
            logger.warning("Falling back to Google DNS. This bypasses decentralized DNS resolution.")
            return ["8.8.8.8", "8.8.4.4"]  # Fallback to Google DNS

    def _load_contract(self):
        """Load contract ABI and create contract instance"""
        try:
            with open('blockchain/contracts/abi/AstraLinkService.json') as f:
                self.contract_abi = json.load(f)
            self.contract = self.web3.eth.contract(
                address=self.contract_address,
                abi=self.contract_abi
            )
            logger.info("Contract loaded successfully")
        except Exception as e:
            logger.error(f"Contract loading failed: {e}")
            raise ContractError(f"Failed to load contract: {e}")
        
    async def _get_cached_data(self, key: str) -> Optional[Any]:
        """Get data from cache if available and not expired"""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry['timestamp'] < self._cache_ttl:
                return entry['data']
            del self._cache[key]
        return None

    async def _set_cached_data(self, key: str, data: Any):
        """Cache data with timestamp"""
        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }

    async def _cleanup_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time - entry['timestamp'] >= self._cache_ttl
        ]
        for key in expired_keys:
            del self._cache[key]

    async def setup_provider(self, provider_address: str, commission_rate: int) -> Dict:
        """Setup new service provider with commission rate"""
        try:
            # Check cache first
            cache_key = f"provider_{provider_address}"
            cached_data = await self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

            # Get Web3 connection
            web3 = self._get_web3_connection()
            web3._last_used = time.time()

            # Execute contract call
            tx = await self.contract.functions.setupProvider(
                provider_address,
                commission_rate
            ).build_transaction({
                'from': web3.eth.accounts[0],
                'gas': self.config['smart_contracts']['gas_limit'],
                'gasPrice': await web3.eth.gas_price,
                'nonce': await web3.eth.get_transaction_count(web3.eth.defaultAccount)
            })

            signed_tx = web3.eth.account.sign_transaction(tx, private_key=self.config['private_key'])
            tx_hash = await web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = await web3.eth.wait_for_transaction_receipt(tx_hash)

            result = {
                'success': receipt.status == 1,
                'transaction_hash': receipt.transactionHash.hex(),
                'block_number': receipt.blockNumber
            }

            # Cache the result
            await self._set_cached_data(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"Failed to setup provider: {e}")
            raise

    async def add_service_plan(self, plan_details: Dict) -> Dict:
        """Add new service plan"""
        try:
            # Generate cache key based on plan details
            cache_key = f"plan_{hashlib.sha256(json.dumps(plan_details, sort_keys=True).encode()).hexdigest()}"
            cached_data = await self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

            web3 = self._get_web3_connection()
            web3._last_used = time.time()

            tx = await self.contract.functions.addServicePlan(
                plan_details['name'],
                plan_details['price'],
                plan_details['duration'],
                plan_details['features']
            ).build_transaction({
                'from': web3.eth.accounts[0],
                'gas': self.config['smart_contracts']['gas_limit'],
                'gasPrice': await web3.eth.gas_price,
                'nonce': await web3.eth.get_transaction_count(web3.eth.defaultAccount)
            })

            signed_tx = web3.eth.account.sign_transaction(tx, private_key=self.config['private_key'])
            tx_hash = await web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = await web3.eth.wait_for_transaction_receipt(tx_hash)

            result = {
                'success': receipt.status == 1,
                'plan_id': receipt.logs[0].topics[1].hex(),
                'transaction_hash': receipt.transactionHash.hex()
            }

            await self._set_cached_data(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"Failed to add service plan: {e}")
            raise

    async def process_service_activation(self, user_address: str, plan_id: int, payment_amount: float) -> Dict:
        """Process service activation and handle revenue distribution"""
        try:
            nonce = self.web3.eth.get_transaction_count(user_address)
            
            txn = self.contract.functions.activateService(
                plan_id
            ).build_transaction({
                'nonce': nonce,
                'gas': self.config['smart_contracts']['gas_limit'],
                'gasPrice': self.web3.eth.gas_price,
                'value': self.web3.to_wei(payment_amount, 'ether')
            })
            
            signed_txn = self.web3.eth.account.sign_transaction(
                txn,
                private_key=self._get_user_private_key(user_address)
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': True,
                'user': user_address,
                'plan_id': plan_id,
                'amount': payment_amount,
                'transaction_hash': receipt['transactionHash'].hex()
            }
            
        except Exception as e:
            raise ContractError(f"Service activation failed: {str(e)}")

    async def get_provider_earnings(self, provider_address: str) -> Dict:
        """Get provider's current earnings"""
        try:
            provider = await self.contract.functions.providers(provider_address).call()
            return {
                'address': provider_address,
                'total_earnings': self.web3.from_wei(provider[3], 'ether'),
                'commission_rate': provider[1]
            }
        except Exception as e:
            raise ContractError(f"Failed to get provider earnings: {str(e)}")

    async def verify_ownership(self, token_id: int, user_address: str) -> bool:
        """Verify NFT ownership with caching"""
        try:
            cache_key = f"ownership_{token_id}_{user_address}"
            cached_data = await self._get_cached_data(cache_key)
            if cached_data is not None:
                return cached_data

            web3 = self._get_web3_connection()
            web3._last_used = time.time()

            owner = self.contract.functions.ownerOf(token_id).call()
            result = owner.lower() == user_address.lower()

            # Cache for a shorter duration since ownership can change
            self._cache[cache_key] = {
                'data': result,
                'timestamp': time.time(),
                'ttl': 60  # 1 minute TTL for ownership checks
            }

            return result

        except Exception as e:
            logger.error(f"Ownership verification failed: {e}")
            raise NFTError(f"Ownership verification failed: {e}")

    def _maintain_connections(self):
        """Maintain Web3 connection pool"""
        try:
            current_time = time.time()
            
            # Remove disconnected instances
            self._web3_instances = [
                web3 for web3 in self._web3_instances
                if web3.is_connected()
            ]

            # Remove old instances if pool is too large
            while len(self._web3_instances) > self._max_pool_size:
                oldest = min(self._web3_instances, key=lambda w: w._last_used)
                self._web3_instances.remove(oldest)

        except Exception as e:
            logger.error(f"Connection maintenance failed: {e}")

    async def start_maintenance_tasks(self):
        """Start background maintenance tasks"""
        while True:
            try:
                self._maintain_connections()
                await self._cleanup_cache()
                await asyncio.sleep(60)  # Run maintenance every minute
            except Exception as e:
                logger.error(f"Maintenance tasks failed: {e}")
                await asyncio.sleep(5)

    def _get_private_key(self) -> str:
        """Retrieve the service provider's private key from environment variables."""
        try:
            return os.environ["SERVICE_PROVIDER_PRIVATE_KEY"]
        except KeyError:
            logger.warning("SERVICE_PROVIDER_PRIVATE_KEY environment variable not set.")
            raise ContractError("Service provider private key not set.")

    def _get_user_private_key(self, user_address: str) -> str:
        """Retrieve the user's private key from environment variables."""
        try:
            # In a real-world scenario, you would not store user private keys in environment variables.
            # This is just for demonstration purposes. Instead, use a secure key management system.
            return os.environ[f"USER_{user_address.upper()}_PRIVATE_KEY"]
        except KeyError:
            logger.warning(f"USER_{user_address.upper()}_PRIVATE_KEY environment variable not set.")
            raise ContractError(f"User private key not set for address: {user_address}")
