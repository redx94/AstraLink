
"""
File: mining_rewards_manager.py
Author: Reece Dixon
Copyright (C) 2025 Reece Dixon
License: Refer to LICENSE file in the root directory of this repository.

Disclaimer:
This file is part of AstraLink. The author assumes no responsibility
for any misuse of this system.
"""

class MiningRewardsManager:
    """
    Manages rewards for mining contributions.
    """

    def __init__(self):
        self.contributions = {}
        self.rewards = {}

    def add_contribution(self, user_id, amount):
        """Logs a user's contribution."""
        if user_id not in self.contributions:
            self.contributions[user_id] = 0
        self.contributions[user_id] += amount

    def calculate_rewards(self):
        """Calculates rewards based on contributions."""
        total_contributions = sum(self.contributions.values())
        if total_contributions == 0:
            return

        for user_id, contribution in self.contributions.items():
            self.rewards[user_id] = (contribution / total_contributions) * 100  # Example: Percentage-based rewards

    def distribute_rewards(self):
        """Distributes rewards to users."""
        for user_id, reward in self.rewards.items():
            print(f"Distributed {reward}% reward to User {user_id}.")

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
    manager.calculate_rewards()
    manager.distribute_rewards()

    # Check rewards for a specific user
    print("User1 Reward:", manager.get_user_rewards("user1"))
