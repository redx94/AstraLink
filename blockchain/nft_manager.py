from web3 import Web3
from eth_account import Account
from typing import Dict
import json

class NFTManager:
    def __init__(self, contract_address: str, web3_provider: str):
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        self.contract_address = contract_address
        with open('blockchain/abi/esim_nft.json') as f:
            self.contract_abi = json.load(f)
        self.contract = self.web3.eth.contract(
            address=contract_address,
            abi=self.contract_abi
        )

    async def mint_esim_nft(self, user_address: str, esim_data: Dict) -> Dict:
        try:
            # Prepare NFT metadata
            metadata = {
                'esim_id': esim_data['iccid'],
                'carrier': esim_data['carrier'],
                'activation_date': esim_data['activation_date'],
                'plan_details': esim_data['plan_details']
            }

            # Upload metadata to IPFS
            ipfs_hash = await self._upload_to_ipfs(metadata)

            # Mint NFT
            nonce = self.web3.eth.get_transaction_count(user_address)
            mint_txn = self.contract.functions.mintESIMNFT(
                user_address,
                ipfs_hash
            ).build_transaction({
                'nonce': nonce,
                'gas': 2000000,
                'gasPrice': self.web3.eth.gas_price
            })

            # Execute transaction
            signed_txn = self.web3.eth.account.sign_transaction(
                mint_txn,
                private_key=self._get_signing_key()
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            return {
                'success': True,
                'token_id': receipt['logs'][0]['topics'][3],
                'transaction_hash': receipt['transactionHash'].hex(),
                'ipfs_hash': ipfs_hash
            }

        except Exception as e:
            raise NFTError(f"NFT minting failed: {str(e)}")

    async def verify_ownership(self, token_id: int, user_address: str) -> bool:
        """Verify NFT ownership for eSIM validation"""
        try:
            owner = self.contract.functions.ownerOf(token_id).call()
            return owner.lower() == user_address.lower()
        except Exception as e:
            raise NFTError(f"Ownership verification failed: {str(e)}")
