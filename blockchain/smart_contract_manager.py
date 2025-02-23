from web3 import Web3
from typing import Dict, List
import json
import asyncio

class SmartContractManager:
    def __init__(self, contract_address: str, web3_provider: str):
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        self.contract_address = contract_address
        with open('blockchain/contracts/abi/AstraLinkService.json') as f:
            self.contract_abi = json.load(f)
        self.contract = self.web3.eth.contract(
            address=contract_address,
            abi=self.contract_abi
        )
        
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
