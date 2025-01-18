
"""
File: nft_mining_rewards.py
Author: Reece Dixon
Copyright (C) 2025 Reece Dixon
License: Refer to LICENSE file in the root directory of this repository.

Disclaimer:
This file is part of AstraLink. The author assumes no responsibility
for any misuse of this system.
"""

from web3 import Web3
from mining_rewards_manager import MiningRewardsManager

class NFTMiningRewards:
    """
    Manages NFT minting for top mining contributors.
    """

    def __init__(self, rpc_url, contract_address, private_key):
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address = contract_address
        self.private_key = private_key
        self.rewards_manager = MiningRewardsManager()

    def mint_nft(self, recipient_address, metadata_uri):
        """Mints an NFT to the recipient's address."""
        contract = self.web3.eth.contract(address=self.contract_address, abi=self.get_contract_abi())
        nonce = self.web3.eth.get_transaction_count(self.get_deployer_address())
        tx = contract.functions.mint(recipient_address, metadata_uri).buildTransaction({
            'chainId': 1,  # Replace with appropriate chain ID
            'gas': 2000000,
            'gasPrice': self.web3.toWei('50', 'gwei'),
            'nonce': nonce,
        })
        signed_tx = self.web3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self.web3.toHex(tx_hash)

    def reward_top_contributors(self):
        """Mints NFTs for the top contributors."""
        self.rewards_manager.calculate_rewards()
        top_contributors = sorted(self.rewards_manager.rewards.items(), key=lambda x: x[1], reverse=True)[:3]

        for user_id, reward in top_contributors:
            recipient_address = self.get_user_wallet(user_id)
            metadata_uri = f"https://example.com/nft/{user_id}"
            tx_hash = self.mint_nft(recipient_address, metadata_uri)
            print(f"Minted NFT for User {user_id}. Transaction Hash: {tx_hash}")

    def get_contract_abi(self):
        """Returns the ABI of the NFT contract."""
        return [  # Simplified ABI for demonstration purposes
            {
                "inputs": [
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "string", "name": "uri", "type": "string"}
                ],
                "name": "mint",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

    def get_deployer_address(self):
        """Returns the address of the deployer account."""
        return self.web3.eth.account.from_key(self.private_key).address

    def get_user_wallet(self, user_id):
        """Placeholder to retrieve a user's wallet address."""
        # Replace with actual logic to fetch user wallets.
        return "0x1234567890abcdef1234567890abcdef12345678"

if __name__ == "__main__":
    # Example usage
    rpc_url = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
    contract_address = "0xYourNFTContractAddress"
    private_key = "0xYourPrivateKey"

    nft_rewards = NFTMiningRewards(rpc_url, contract_address, private_key)

    # Reward top contributors
    nft_rewards.reward_top_contributors()
