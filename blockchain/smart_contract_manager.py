"""
AstraLink - Smart Contract Manager Module
====================================

This module handles blockchain smart contract operations including service provider
setup, plan management, service activation, and revenue distribution.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
See LICENSE file for licensing information.
"""

from web3 import Web3
from typing import Dict, List, Optional
import json
import asyncio
import yaml
from dns import resolver
from logging_config import get_logger
from exceptions import NetworkError, ContractError

logger = get_logger(__name__)

class SmartContractManager:
    def __init__(self, contract_address: str = None, web3_provider: str = None):
        """Initialize with optional params, will load from config if not provided"""
        self.load_network_config()
        self.web3 = self._initialize_web3(web3_provider)
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

    def _initialize_web3(self, web3_provider: Optional[str] = None) -> Web3:
        """Initialize Web3 with fallback to network nodes"""
        try:
            if web3_provider:
                return Web3(Web3.HTTPProvider(web3_provider))
            
            # Try connecting to network nodes through Handshake DNS
            for node in self.config['dns']['bootstrap_nodes']:
                try:
                    node_ip = self._resolve_handshake_domain(node)
                    provider_url = f"http://{node_ip}:8545"
                    web3 = Web3(Web3.HTTPProvider(provider_url))
                    if web3.is_connected():
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
            # You would implement actual Handshake nameserver lookup here
            # For now returning placeholder values
            return ["127.0.0.1", "::1"]
        except Exception as e:
            logger.error(f"Failed to get Handshake nameservers: {e}")
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
        
    async def setup_provider(self, provider_address: str, commission_rate: int) -> Dict:
        """Setup new service provider with commission rate"""
        try:
            nonce = self.web3.eth.get_transaction_count(self.web3.eth.default_account)
            
            txn = self.contract.functions.addProvider(
                provider_address,
                commission_rate
            ).build_transaction({
                'nonce': nonce,
                'gas': 2000000,
                'gasPrice': self.web3.eth.gas_price
            })
            
            signed_txn = self.web3.eth.account.sign_transaction(
                txn, 
                private_key=self._get_private_key()
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': True,
                'provider': provider_address,
                'commission_rate': commission_rate,
                'transaction_hash': receipt['transactionHash'].hex()
            }
        
        except Exception as e:
            raise ContractError(f"Provider setup failed: {str(e)}")

    async def add_service_plan(self, plan_details: Dict) -> Dict:
        """Add new service plan to the contract"""
        try:
            nonce = self.web3.eth.get_transaction_count(self.web3.eth.default_account)
            
            txn = self.contract.functions.addServicePlan(
                plan_details['plan_id'],
                self.web3.to_wei(plan_details['price'], 'ether'),
                plan_details['duration'],
                plan_details['data_limit'],
                plan_details['service_type']
            ).build_transaction({
                'nonce': nonce,
                'gas': 2000000,
                'gasPrice': self.web3.eth.gas_price
            })
            
            signed_txn = self.web3.eth.account.sign_transaction(
                txn,
                private_key=self._get_private_key()
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': True,
                'plan_id': plan_details['plan_id'],
                'transaction_hash': receipt['transactionHash'].hex()
            }
            
        except Exception as e:
            raise ContractError(f"Service plan addition failed: {str(e)}")

    async def process_service_activation(self, user_address: str, plan_id: int, payment_amount: float) -> Dict:
        """Process service activation and handle revenue distribution"""
        try:
            nonce = self.web3.eth.get_transaction_count(user_address)
            
            txn = self.contract.functions.activateService(
                plan_id
            ).build_transaction({
                'nonce': nonce,
                'gas': 2000000,
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
