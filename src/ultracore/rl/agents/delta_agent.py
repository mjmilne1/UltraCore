"""
Delta Agent - A3C for POD4 Opportunistic

Objective: Generate alpha, sector rotation
Algorithm: Asynchronous Advantage Actor-Critic (A3C)
Target: >12% return, 25-35% volatility
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from typing import Dict, List, Tuple
from .base_agent import BaseRLAgent
import sys
sys.path.append('/home/ubuntu/UltraCore/src')
from ultracore.rl.models.actor_critic import ContinuousActorCriticNetwork


class DeltaAgent(BaseRLAgent):
    """
    Delta agent using A3C for alpha generation.
    
    Uses actor-critic architecture with advantage estimation.
    Optimizes for outperformance vs benchmark.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dims: Tuple[int, ...] = (128, 64),
        learning_rate: float = 0.001,
        discount_factor: float = 0.99,
        entropy_coef: float = 0.01,
        value_loss_coef: float = 0.5,
        max_grad_norm: float = 0.5
    ):
        """
        Initialize Delta agent.
        
        Args:
            state_dim: Dimension of state space
            action_dim: Number of assets
            hidden_dims: Hidden layer dimensions
            learning_rate: Learning rate
            discount_factor: Discount factor (gamma)
            entropy_coef: Entropy coefficient (for exploration)
            value_loss_coef: Value loss coefficient
            max_grad_norm: Maximum gradient norm for clipping
        """
        super().__init__(
            name='Delta',
            state_dim=state_dim,
            action_dim=action_dim,
            objective='alpha',
            learning_rate=learning_rate,
            discount_factor=discount_factor
        )
        
        self.entropy_coef = entropy_coef
        self.value_loss_coef = value_loss_coef
        self.max_grad_norm = max_grad_norm
        
        # Actor-Critic network
        self.ac_net = ContinuousActorCriticNetwork(state_dim, action_dim, hidden_dims)
        self.optimizer = optim.Adam(self.ac_net.parameters(), lr=learning_rate)
        
        # Episode buffer
        self.episode_states = []
        self.episode_actions = []
        self.episode_rewards = []
        self.episode_values = []
        self.episode_log_probs = []
    
    def select_action(self, state: np.ndarray, training: bool = True) -> np.ndarray:
        """
        Select action using actor-critic policy.
        
        Args:
            state: Current state
            training: Whether in training mode
        
        Returns:
            Action (portfolio weights)
        """
        action, log_prob, value = self.ac_net.sample_action(state)
        
        # Store for training
        if training:
            self.episode_states.append(state)
            self.episode_actions.append(action)
            self.episode_log_probs.append(log_prob)
            self.episode_values.append(value)
        
        return action
    
    def store_reward(self, reward: float):
        """Store reward for current step"""
        self.episode_rewards.append(reward)
    
    def train(self) -> Dict[str, float]:
        """
        Train agent using A3C algorithm.
        
        Updates actor-critic network using advantage estimation.
        
        Returns:
            Dict of training metrics
        """
        if len(self.episode_rewards) == 0:
            return {}
        
        # Calculate returns and advantages
        returns = []
        advantages = []
        G = 0
        
        for i in reversed(range(len(self.episode_rewards))):
            G = self.episode_rewards[i] + self.discount_factor * G
            returns.insert(0, G)
            
            # Advantage = Return - Value
            advantage = G - self.episode_values[i]
            advantages.insert(0, advantage)
        
        # Convert to tensors
        states = torch.FloatTensor(np.array(self.episode_states))
        actions = torch.FloatTensor(np.array(self.episode_actions))
        returns = torch.FloatTensor(returns)
        advantages = torch.FloatTensor(advantages)
        old_log_probs = torch.FloatTensor(self.episode_log_probs)
        
        # Normalize advantages
        if len(advantages) > 1:
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # Forward pass
        log_probs, values, entropy = self.ac_net.evaluate_actions(states, actions)
        
        # Actor loss (policy gradient with advantage)
        actor_loss = -(log_probs * advantages.detach()).mean()
        
        # Critic loss (value function)
        critic_loss = F.mse_loss(values, returns)
        
        # Entropy loss (for exploration)
        entropy_loss = -entropy.mean()
        
        # Total loss
        loss = (
            actor_loss +
            self.value_loss_coef * critic_loss +
            self.entropy_coef * entropy_loss
        )
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.ac_net.parameters(), self.max_grad_norm)
        
        self.optimizer.step()
        
        # Log episode
        episode_return = sum(self.episode_rewards)
        episode_length = len(self.episode_rewards)
        self.log_episode(episode_return, episode_length)
        
        # Clear episode buffer
        metrics = {
            'loss': loss.item(),
            'actor_loss': actor_loss.item(),
            'critic_loss': critic_loss.item(),
            'entropy': -entropy_loss.item(),
            'episode_return': episode_return,
            'episode_length': episode_length,
            'mean_value': values.mean().item()
        }
        
        self.episode_states = []
        self.episode_actions = []
        self.episode_rewards = []
        self.episode_values = []
        self.episode_log_probs = []
        
        self.training_steps += 1
        
        return metrics
    
    def save(self, path: str):
        """Save agent including actor-critic network"""
        import pickle
        from pathlib import Path
        
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        state_dict = {
            'name': self.name,
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor,
            'entropy_coef': self.entropy_coef,
            'value_loss_coef': self.value_loss_coef,
            'max_grad_norm': self.max_grad_norm,
            'ac_net_state': self.ac_net.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'episode_rewards': self.episode_rewards,
            'episode_lengths': self.episode_lengths,
            'training_steps': self.training_steps
        }
        
        with open(path, 'wb') as f:
            pickle.dump(state_dict, f)
    
    def load(self, path: str):
        """Load agent including actor-critic network"""
        import pickle
        
        with open(path, 'rb') as f:
            state_dict = pickle.load(f)
        
        self.name = state_dict['name']
        self.state_dim = state_dict['state_dim']
        self.action_dim = state_dict['action_dim']
        self.learning_rate = state_dict['learning_rate']
        self.discount_factor = state_dict['discount_factor']
        self.entropy_coef = state_dict['entropy_coef']
        self.value_loss_coef = state_dict['value_loss_coef']
        self.max_grad_norm = state_dict['max_grad_norm']
        
        # Reconstruct network
        self.ac_net = ContinuousActorCriticNetwork(self.state_dim, self.action_dim)
        self.ac_net.load_state_dict(state_dict['ac_net_state'])
        
        self.optimizer = optim.Adam(self.ac_net.parameters(), lr=self.learning_rate)
        self.optimizer.load_state_dict(state_dict['optimizer_state'])
        
        self.episode_rewards = state_dict.get('episode_rewards', [])
        self.episode_lengths = state_dict.get('episode_lengths', [])
        self.training_steps = state_dict.get('training_steps', 0)
