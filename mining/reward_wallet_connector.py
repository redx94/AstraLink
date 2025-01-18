
"""
File: reward_wallet_connector.py
Author: Reece Dixon
Copyright (C) 2025 Reece Dixon
License: Refer to LICENSE file in the root directory of this repository.

Disclaimer:
This file is part of AstraLink. The author assumes no responsibility
for any misuse of this system.
"""

from mining_rewards_manager import MiningRewardsManager
from wallet_manager import WalletManager

class RewardWalletConnector:
    """
    Facilitates integration between mining rewards and wallet transactions.
    """

    def __init__(self, wallet_rpc_url):
        self.rewards_manager = MiningRewardsManager()
        self.wallet_manager = WalletManager(wallet_rpc_url)

    def distribute_rewards_to_wallets(self):
        """Transfers mining rewards to user wallets."""
        self.rewards_manager.calculate_rewards()
        
        for user_id, reward in self.rewards_manager.rewards.items():
            wallet = self.wallet_manager.create_wallet()
            print(f"Reward {reward}% sent to wallet: {wallet['address']} for User: {user_id}")

    def log_contribution(self, user_id, amount):
        """Logs user contribution into the rewards manager."""
        self.rewards_manager.add_contribution(user_id, amount)

if __name__ == "__main__":
    # Example usage
    rpc_url = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
    connector = RewardWalletConnector(rpc_url)

    # Log contributions
    connector.log_contribution("user1", 100)
    connector.log_contribution("user2", 50)

    # Distribute rewards to wallets
    connector.distribute_rewards_to_wallets()
