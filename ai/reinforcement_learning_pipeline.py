"""
AstraLink - Reinforcement Learning Pipeline
========================================

AI-powered pipeline for optimizing network bandwidth allocation
using reinforcement learning techniques.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Tuple, Any
import gymnasium as gym
from gymnasium import spaces
from collections import deque
import random
from dataclasses import dataclass
from logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class NetworkState:
    bandwidth_usage: float
    user_count: int
    latency: float
    packet_loss: float
    time_of_day: int

class NetworkEnvironment(gym.Env):
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        
        # Define action space (bandwidth allocation adjustments)
        self.action_space = spaces.Discrete(5)  # [-20%, -10%, 0%, +10%, +20%]
        
        # Define observation space
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0, 0, 0]),
            high=np.array([1, 1000, 1000, 1, 24]),
            dtype=np.float32
        )
        
        self.state = NetworkState(
            bandwidth_usage=0.5,
            user_count=100,
            latency=20.0,
            packet_loss=0.01,
            time_of_day=12
        )
        
        self.config = config
        self._max_steps = config.get('max_steps', 1000)
        self._current_step = 0

    def reset(self, seed=None):
        super().reset(seed=seed)
        self._current_step = 0
        self.state = NetworkState(
            bandwidth_usage=random.uniform(0.3, 0.7),
            user_count=random.randint(50, 150),
            latency=random.uniform(10, 30),
            packet_loss=random.uniform(0, 0.05),
            time_of_day=random.randint(0, 23)
        )
        return self._get_observation(), {}

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        self._current_step += 1
        
        # Apply bandwidth adjustment
        adjustment = (action - 2) * 0.1  # Convert to [-0.2, -0.1, 0, 0.1, 0.2]
        new_bandwidth = np.clip(self.state.bandwidth_usage + adjustment, 0, 1)
        
        # Update network state
        self.state.bandwidth_usage = new_bandwidth
        self.state.latency = self._calculate_latency()
        self.state.packet_loss = self._calculate_packet_loss()
        
        # Calculate reward
        reward = self._calculate_reward()
        
        # Check if episode should end
        done = self._current_step >= self._max_steps
        
        return self._get_observation(), reward, done, False, {}

    def _get_observation(self) -> np.ndarray:
        return np.array([
            self.state.bandwidth_usage,
            self.state.user_count / 1000,  # Normalize
            self.state.latency / 1000,     # Normalize
            self.state.packet_loss,
            self.state.time_of_day / 24    # Normalize
        ], dtype=np.float32)

    def _calculate_latency(self) -> float:
        base_latency = 20.0
        usage_factor = 1 + (self.state.bandwidth_usage - 0.5) * 2
        return base_latency * usage_factor

    def _calculate_packet_loss(self) -> float:
        base_loss = 0.01
        usage_factor = 1 + max(0, self.state.bandwidth_usage - 0.8) * 4
        return base_loss * usage_factor

    def _calculate_reward(self) -> float:
        # Penalize high latency and packet loss
        latency_penalty = -0.1 * (self.state.latency / 20.0)
        loss_penalty = -10.0 * self.state.packet_loss
        
        # Reward efficient bandwidth usage
        efficiency_reward = 1.0 - abs(0.7 - self.state.bandwidth_usage)
        
        return latency_penalty + loss_penalty + efficiency_reward

class DQNAgent:
    def __init__(self, state_dim: int, action_dim: int, config: Dict[str, Any]):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.learning_rate = config.get('learning_rate', 0.001)
        self.gamma = config.get('gamma', 0.99)
        self.epsilon = config.get('epsilon_start', 1.0)
        self.epsilon_min = config.get('epsilon_min', 0.01)
        self.epsilon_decay = config.get('epsilon_decay', 0.995)
        self.memory = deque(maxlen=config.get('memory_size', 10000))
        self.batch_size = config.get('batch_size', 64)

        self.policy_net = self._build_network().to(self.device)
        self.target_net = self._build_network().to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=self.learning_rate)

    def _build_network(self) -> nn.Module:
        return nn.Sequential(
            nn.Linear(self.state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, self.action_dim)
        )

    def select_action(self, state: np.ndarray) -> int:
        if random.random() < self.epsilon:
            return random.randrange(self.action_dim)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_tensor)
            return q_values.argmax().item()

    def train(self, batch: List[Tuple[np.ndarray, int, float, np.ndarray, bool]]):
        if len(batch) < self.batch_size:
            return
            
        states, actions, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        current_q_values = self.policy_net(states).gather(1, actions.unsqueeze(1))
        next_q_values = self.target_net(next_states).max(1)[0].detach()
        target_q_values = rewards + (1 - dones) * self.gamma * next_q_values
        
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def update_target_network(self):
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def remember(self, state: np.ndarray, action: int, reward: float, 
                next_state: np.ndarray, done: bool):
        self.memory.append((state, action, reward, next_state, done))

def train_network_optimization(config: Dict[str, Any]):
    """
    Train the reinforcement learning agent to optimize network bandwidth allocation.
    
    Args:
        config: Configuration dictionary containing hyperparameters
    """
    env = NetworkEnvironment(config)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n
    
    agent = DQNAgent(state_dim, action_dim, config)
    episodes = config.get('episodes', 1000)
    
    for episode in range(episodes):
        state, _ = env.reset()
        episode_reward = 0
        
        while True:
            action = agent.select_action(state)
            next_state, reward, done, _, _ = env.step(action)
            
            agent.remember(state, action, reward, next_state, done)
            agent.train(random.sample(agent.memory, min(len(agent.memory), agent.batch_size)))
            
            state = next_state
            episode_reward += reward
            
            if done:
                break
        
        if episode % 10 == 0:
            agent.update_target_network()
            logger.info(f"Episode {episode}/{episodes}, Reward: {episode_reward:.2f}, Epsilon: {agent.epsilon:.2f}")

    return agent
