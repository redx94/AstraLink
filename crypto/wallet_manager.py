""
File: wallet_manager.py
Author: Reece Dixon
Copyright (C) 2025 Reece Dixon
License: Refer to LICENSE file in the root directory of this repository.

Disclaimer:
This file is part of AstraLink. The author assumes no responsibility for any misuse of this system.

from web3 import Web3

class WalletManager:
    "Responsible for managing wallets for cryptocurrencies."

    def __init__(self, rpc_url):
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))

    def create_wallet(self):
        "Generates a new wallet and returns its address and private key."
        account = self.web3.eth.account.create()
        return {
            "address": account.address,
            "private_key": account.privateKey.hex()
        }

    def get_balance(self, address):
        "Fetches the ETH balance of the specified wallet address."
        balance_wei = self.web3.eth.get_balance(address)
        return self.web3.fromWei(balance_wei, 'ether')

    def send_transaction(self, from_address, private_key, to_address, amount):
        "Sends a transaction from one wallet to another."
        nonce = self.web3.eth.getTransactionCount(from_address)
        tx = {
            'nonce': nonce,
            'to': to_address,
            'value': self.web3.toWei(amount, 'ether'),
            'gas': 21000,
            'gasPrice': self.web3.toWei('50', 'gwei')
        }
        signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return self.web3.toHex(tx_hash)

#if __name__ == "__main__":
    # Example usage
    rpc_url = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
    manager = WalletManager(rpc_url)

    # Create a wallet
    wallet = manager.create_wallet()
    print("New Wallet:", wallet)

    # Check balance
    balance = manager.get_balance(wallet["address"])
    print("Wallet Balance:", balance)
