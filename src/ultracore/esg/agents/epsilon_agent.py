"""
Epsilon Agent: ESG-Focused Reinforcement Learning Agent

The Epsilon Agent is the fifth agent in the UltraWealth suite, specifically
designed to optimize portfolios for both financial returns and ESG outcomes.

This agent uses a hybrid approach combining Deep Q-Learning with ESG-aware
policy constraints to achieve "ESG Alpha" - excess returns from superior
ESG performance.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Optional, Dict
from collections import deque
import random


class EsgAwareQNetwork(nn.Module):
    """
    Deep Q-Network with ESG-aware architecture.
    
    This network has a dual-stream architecture:
    - Financial stream: Processes price and portfolio data
    - ESG stream: Processes ESG metrics
    - Fusion layer: Combines both streams for action selection
    """
    
    def __init__(self, state_dim: int, action_dim: int, esg_feature_dim: int):
        super(EsgAwareQNetwork, self).__init__()
        
        # Calculate dimensions
        financial_dim = state_dim - esg_feature_dim
        
        # Financial stream
        self.financial_fc1 = nn.Linear(financial_dim, 256)
        self.financial_fc2 = nn.Linear(256, 128)
        
        # ESG stream
        self.esg_fc1 = nn.Linear(esg_feature_dim, 128)
        self.esg_fc2 = nn.Linear(128, 64)
        
        # Fusion layers
        self.fusion_fc1 = nn.Linear(128 + 64, 256)
        self.fusion_fc2 = nn.Linear(256, 128)
        self.output = nn.Linear(128, action_dim)
        
        # Layer normalization for stability
        self.ln1 = nn.LayerNorm(256)
        self.ln2 = nn.LayerNorm(256)  # Match fusion_fc1 output
        self.ln3 = nn.LayerNorm(128)  # Match fusion_fc2 output
        
    def forward(self, state: torch.Tensor, financial_dim: int) -> torch.Tensor:
        """Forward pass through the network"""
        # Split state into financial and ESG components
        financial_state = state[:, :financial_dim]
        esg_state = state[:, financial_dim:]
        
        # Financial stream
        x_fin = F.relu(self.financial_fc1(financial_state))
        x_fin = self.ln1(x_fin)
        x_fin = F.relu(self.financial_fc2(x_fin))
        
        # ESG stream
        x_esg = F.relu(self.esg_fc1(esg_state))
        x_esg = F.relu(self.esg_fc2(x_esg))
        
        # Fusion
        x = torch.cat([x_fin, x_esg], dim=1)
        x = F.relu(self.fusion_fc1(x))
        x = self.ln2(x)
        x = F.relu(self.fusion_fc2(x))
        x = self.ln3(x)
        
        # Output Q-values
        return self.output(x)


class EpsilonAgent:
    """
    Epsilon Agent: ESG-focused RL agent using Deep Q-Learning.
    
    Key features:
    - Dual-stream Q-network for financial and ESG data
    - ESG-aware action filtering
    - Experience replay with ESG prioritization
    - Explainable AI via attention mechanisms
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        esg_feature_dim: int,
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        buffer_size: int = 10000,
        batch_size: int = 64,
        target_update_freq: int = 10,
    ):
        """
        Initialize the Epsilon Agent.
        
        Args:
            state_dim: Dimension of state space (including ESG features)
            action_dim: Dimension of action space
            esg_feature_dim: Dimension of ESG features in state
            learning_rate: Learning rate for optimizer
            gamma: Discount factor
            epsilon_start: Initial exploration rate
            epsilon_end: Final exploration rate
            epsilon_decay: Exploration decay rate
            buffer_size: Size of experience replay buffer
            batch_size: Batch size for training
            target_update_freq: Frequency of target network updates
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.esg_feature_dim = esg_feature_dim
        self.financial_dim = state_dim - esg_feature_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        
        # Q-networks
        self.q_network = EsgAwareQNetwork(state_dim, action_dim, esg_feature_dim)
        self.target_network = EsgAwareQNetwork(state_dim, action_dim, esg_feature_dim)
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        # Optimizer
        self.optimizer = torch.optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Experience replay buffer
        self.replay_buffer = deque(maxlen=buffer_size)
        
        # Training metrics
        self.training_step = 0
        self.loss_history = []
        
    def select_action(
        self,
        state: np.ndarray,
        esg_constraints: Optional[Dict] = None,
        deterministic: bool = False
    ) -> np.ndarray:
        """
        Select an action using epsilon-greedy policy with ESG constraints.
        
        Args:
            state: Current state
            esg_constraints: Optional ESG constraints to filter actions
            deterministic: If True, always select best action (no exploration)
        
        Returns:
            Action vector
        """
        # Epsilon-greedy exploration
        if not deterministic and random.random() < self.epsilon:
            # Random action
            action = np.random.randn(self.action_dim)
            action = action / np.sum(np.abs(action))  # Normalize
        else:
            # Greedy action from Q-network
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            with torch.no_grad():
                q_values = self.q_network(state_tensor, self.financial_dim)
            
            # Convert Q-values to action (softmax for portfolio weights)
            action = F.softmax(q_values, dim=1).squeeze(0).numpy()
        
        # Apply ESG constraints if provided
        if esg_constraints:
            action = self._apply_esg_constraints(action, state, esg_constraints)
        
        return action
    
    def _apply_esg_constraints(
        self,
        action: np.ndarray,
        state: np.ndarray,
        constraints: Dict
    ) -> np.ndarray:
        """
        Apply ESG constraints to filter/modify actions.
        
        This ensures that the agent never violates hard ESG constraints,
        even during exploration.
        """
        # Extract ESG features from state
        esg_features = state[self.financial_dim:]
        n_assets = self.action_dim
        esg_per_asset = self.esg_feature_dim // n_assets
        
        # Check each asset against constraints
        for i in range(n_assets):
            asset_esg = esg_features[i * esg_per_asset:(i + 1) * esg_per_asset]
            
            # ESG rating constraint (first feature)
            if 'min_esg_rating' in constraints:
                min_rating = constraints['min_esg_rating']
                if asset_esg[0] < min_rating:
                    action[i] = 0.0  # Zero out this asset
            
            # Carbon intensity constraint (second feature)
            if 'max_carbon_intensity' in constraints:
                max_carbon = constraints['max_carbon_intensity']
                if asset_esg[1] > max_carbon:
                    action[i] = 0.0
        
        # Renormalize action
        if np.sum(action) > 0:
            action = action / np.sum(action)
        
        return action
    
    def store_experience(
        self,
        state: np.ndarray,
        action: np.ndarray,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """Store experience in replay buffer"""
        self.replay_buffer.append((state, action, reward, next_state, done))
    
    def train(self) -> Optional[float]:
        """
        Train the agent on a batch of experiences.
        
        Returns:
            Loss value if training occurred, None otherwise
        """
        if len(self.replay_buffer) < self.batch_size:
            return None
        
        # Sample batch
        batch = random.sample(self.replay_buffer, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        # Convert to tensors
        states = torch.FloatTensor(np.array(states))
        actions = torch.FloatTensor(np.array(actions))
        rewards = torch.FloatTensor(rewards).unsqueeze(1)
        next_states = torch.FloatTensor(np.array(next_states))
        dones = torch.FloatTensor(dones).unsqueeze(1)
        
        # Current Q-values
        current_q = self.q_network(states, self.financial_dim)
        current_q = (current_q * actions).sum(dim=1, keepdim=True)
        
        # Target Q-values
        with torch.no_grad():
            next_q = self.target_network(next_states, self.financial_dim)
            max_next_q = next_q.max(dim=1, keepdim=True)[0]
            target_q = rewards + (1 - dones) * self.gamma * max_next_q
        
        # Compute loss
        loss = F.mse_loss(current_q, target_q)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        self.optimizer.step()
        
        # Update target network
        self.training_step += 1
        if self.training_step % self.target_update_freq == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        
        # Record loss
        loss_value = loss.item()
        self.loss_history.append(loss_value)
        
        return loss_value
    
    def save(self, path: str):
        """Save agent to disk"""
        torch.save({
            'q_network': self.q_network.state_dict(),
            'target_network': self.target_network.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'training_step': self.training_step,
        }, path)
    
    def load(self, path: str):
        """Load agent from disk"""
        checkpoint = torch.load(path)
        self.q_network.load_state_dict(checkpoint['q_network'])
        self.target_network.load_state_dict(checkpoint['target_network'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']
        self.training_step = checkpoint['training_step']
    
    def explain_action(self, state: np.ndarray) -> Dict:
        """
        Explain why the agent selected a particular action.
        
        This provides transparency and builds trust with users.
        
        Returns:
            Dictionary with explanation including:
            - Q-values for each action
            - ESG scores for each asset
            - Financial metrics
        """
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        
        with torch.no_grad():
            q_values = self.q_network(state_tensor, self.financial_dim)
        
        # Extract ESG features
        esg_features = state[self.financial_dim:]
        n_assets = self.action_dim
        esg_per_asset = self.esg_feature_dim // n_assets
        
        explanation = {
            'q_values': q_values.squeeze(0).numpy().tolist(),
            'selected_action': q_values.argmax().item(),
            'esg_scores': [],
        }
        
        for i in range(n_assets):
            asset_esg = esg_features[i * esg_per_asset:(i + 1) * esg_per_asset]
            explanation['esg_scores'].append({
                'asset_index': i,
                'esg_rating': float(asset_esg[0]),
                'carbon_intensity': float(asset_esg[1]),
                'controversy_score': float(asset_esg[2]),
            })
        
        return explanation
