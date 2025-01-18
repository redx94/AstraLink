
"""
File: mining_rewards_manager.py
Author: Reece Dixon
Copyright (C) 2025 Reece Dixon
License: Refer to LICENSE file in the root directory of this repository.

Disclaimer:
This file is part of AstraLink. The author assumes no responsibility
for any misuse of this system.
"""

from wallet_manager import WalletManager

class MiningRewardsManager:
    """
    Manages rewards for mining contributions.
    """

    def __init__(self):
        self.contributions = {}
        self.rewards = {}
        self.wallet_manager = WalletManager()

    def add_contribution(self, user_id, amount):
        """Logs a user's contribution."""
        if user_id not in self.contributions:
            self.contributions[user_id] = 0
        self.contributions[user_id] += amount

    def calculate_rewards(self):
        """Calculates rewards based on contributions."""
        total_contributions = sum(self.contributions.values())
        if total_contributions == 0:
            raise ValueError("No contributions to calculate rewards.")

        for user_id, contribution in self.contributions.items():
            self.rewards[user_id] = (contribution / total_contributions) * 100  # Example: Percentage-based rewards

    def distribute_rewards(self):
        """Distributes rewards to user wallets."""
        if not self.rewards:
            raise ValueError("No rewards to distribute. Have you calculated rewards?")

        for user_id, reward in self.rewards.items():
            wallet_address = self.wallet_manager.get_user_wallet(user_id)
            if wallet_address:
                print(f"Distributed {reward}% reward to Wallet: {wallet_address} for User: {user_id}.")
            else:
                print(f"No wallet found for User: {user_id}. Skipping reward distribution.")

    def get_user_rewards(self, user_id):
        """Returns the reward for a specific user."""
        return self.rewards.get(user_id, 0)

if __name__ == "__main__":
    # Example usage
    manager = MiningRewardsManager()

    # Log contributions
    manager.add_contribution("user1", 50)
    manager.add_contribution("user2", 30)
    manager.add_contribution("user3", 20)

    # Calculate and distribute rewards
    try:
        manager.calculate_rewards()
        manager.distribute_rewards()
    except ValueError as e:
        print(f"Error: {e}")

    # Check rewards for a specific user
    print("User1 Reward:", manager.get_user_rewards("user1"))
