"""
RL Agent Trainer

Training pipeline for all 4 RL agents on historical ETF data.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import sys
sys.path.append('/home/ubuntu/UltraCore/src')

from ultracore.rl.environments.portfolio_env import PortfolioEnv
from ultracore.rl.agents.alpha_agent import AlphaAgent
from ultracore.rl.agents.beta_agent import BetaAgent
from ultracore.rl.agents.gamma_agent import GammaAgent
from ultracore.rl.agents.delta_agent import DeltaAgent


class AgentTrainer:
    """
    Trainer for RL agents on portfolio optimization tasks.
    """
    
    def __init__(
        self,
        etf_data: Dict[str, pd.DataFrame],
        save_dir: str = '/home/ubuntu/UltraCore/models/rl_agents'
    ):
        """
        Initialize trainer.
        
        Args:
            etf_data: Dict of {ticker: DataFrame} with OHLCV data
            save_dir: Directory to save trained models
        """
        self.etf_data = etf_data
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
    
    def train_alpha_agent(
        self,
        etf_list: List[str],
        n_episodes: int = 500,
        initial_capital: float = 15000
    ) -> AlphaAgent:
        """
        Train Alpha agent for POD1 Preservation.
        
        Args:
            etf_list: List of ETF tickers for POD1
            n_episodes: Number of training episodes
            initial_capital: Starting capital
        
        Returns:
            Trained Alpha agent
        """
        print("=" * 80)
        print("Training Alpha Agent (Q-Learning) - POD1 Preservation")
        print("=" * 80)
        
        # Create environment
        env = PortfolioEnv(
            etf_data=self.etf_data,
            etf_list=etf_list,
            initial_capital=initial_capital,
            objective='volatility',
            max_steps=252
        )
        
        # Create agent
        agent = AlphaAgent(
            state_dim=env.observation_space.shape[0],
            action_dim=len(etf_list),
            n_state_bins=10,
            n_action_bins=5
        )
        
        # Training loop
        for episode in range(n_episodes):
            state, _ = env.reset()  # Gymnasium returns (obs, info)
            episode_reward = 0
            terminated = False
            
            while not terminated:
                # Select action
                action = agent.select_action(state, training=True)
                
                # Take step (Gymnasium returns 5-tuple)
                next_state, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                
                # Train
                metrics = agent.train(state, action, reward, next_state, done)
                
                episode_reward += reward
                state = next_state
            
            # Log progress
            if (episode + 1) % 50 == 0:
                print(f"Episode {episode+1}/{n_episodes}: "
                      f"Reward={episode_reward:.2f}, "
                      f"Epsilon={agent.epsilon:.3f}, "
                      f"Q-table size={len(agent.q_table)}")
        
        # Save agent
        save_path = self.save_dir / 'alpha_agent.pkl'
        agent.save(str(save_path))
        print(f"✅ Alpha agent saved to {save_path}")
        
        return agent
    
    def train_beta_agent(
        self,
        etf_list: List[str],
        n_episodes: int = 500,
        initial_capital: float = 25000
    ) -> BetaAgent:
        """
        Train Beta agent for POD2 Income.
        
        Args:
            etf_list: List of ETF tickers for POD2
            n_episodes: Number of training episodes
            initial_capital: Starting capital
        
        Returns:
            Trained Beta agent
        """
        print("\n" + "=" * 80)
        print("Training Beta Agent (Policy Gradient) - POD2 Income")
        print("=" * 80)
        
        # Create environment
        env = PortfolioEnv(
            etf_data=self.etf_data,
            etf_list=etf_list,
            initial_capital=initial_capital,
            objective='income',
            max_steps=252
        )
        
        # Create agent
        agent = BetaAgent(
            state_dim=env.observation_space.shape[0],
            action_dim=len(etf_list)
        )
        
        # Training loop
        for episode in range(n_episodes):
            state, _ = env.reset()  # Gymnasium returns (obs, info)
            terminated = False
            
            while not terminated:
                # Select action
                action = agent.select_action(state, training=True)
                
                # Take step (Gymnasium returns 5-tuple)
                next_state, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                
                # Store reward
                agent.store_reward(reward)
                
                state = next_state
            
            # Train at end of episode
            metrics = agent.train()
            
            # Log progress
            if (episode + 1) % 50 == 0:
                print(f"Episode {episode+1}/{n_episodes}: "
                      f"Return={metrics.get('episode_return', 0):.2f}, "
                      f"Loss={metrics.get('loss', 0):.4f}")
        
        # Save agent
        save_path = self.save_dir / 'beta_agent.pkl'
        agent.save(str(save_path))
        print(f"✅ Beta agent saved to {save_path}")
        
        return agent
    
    def train_gamma_agent(
        self,
        etf_list: List[str],
        n_episodes: int = 500,
        initial_capital: float = 50000
    ) -> GammaAgent:
        """
        Train Gamma agent for POD3 Growth.
        
        Args:
            etf_list: List of ETF tickers for POD3
            n_episodes: Number of training episodes
            initial_capital: Starting capital
        
        Returns:
            Trained Gamma agent
        """
        print("\n" + "=" * 80)
        print("Training Gamma Agent (DQN) - POD3 Growth")
        print("=" * 80)
        
        # Create environment
        env = PortfolioEnv(
            etf_data=self.etf_data,
            etf_list=etf_list,
            initial_capital=initial_capital,
            objective='sharpe',
            max_steps=252
        )
        
        # Create agent
        agent = GammaAgent(
            state_dim=env.observation_space.shape[0],
            n_assets=len(etf_list)
        )
        
        # Training loop
        for episode in range(n_episodes):
            state, _ = env.reset()  # Gymnasium returns (obs, info)
            episode_reward = 0
            terminated = False
            
            while not terminated:
                # Select action
                action = agent.select_action(state, training=True)
                
                # Take step (Gymnasium returns 5-tuple)
                next_state, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                
                # Store transition
                agent.store_transition(state, action, reward, next_state, done)
                
                # Train
                metrics = agent.train()
                
                episode_reward += reward
                state = next_state
            
            # Log progress
            if (episode + 1) % 50 == 0:
                print(f"Episode {episode+1}/{n_episodes}: "
                      f"Reward={episode_reward:.2f}, "
                      f"Epsilon={agent.epsilon:.3f}, "
                      f"Buffer={len(agent.replay_buffer)}")
        
        # Save agent
        save_path = self.save_dir / 'gamma_agent.pkl'
        agent.save(str(save_path))
        print(f"✅ Gamma agent saved to {save_path}")
        
        return agent
    
    def train_delta_agent(
        self,
        etf_list: List[str],
        n_episodes: int = 500,
        initial_capital: float = 10000
    ) -> DeltaAgent:
        """
        Train Delta agent for POD4 Opportunistic.
        
        Args:
            etf_list: List of ETF tickers for POD4
            n_episodes: Number of training episodes
            initial_capital: Starting capital
        
        Returns:
            Trained Delta agent
        """
        print("\n" + "=" * 80)
        print("Training Delta Agent (A3C) - POD4 Opportunistic")
        print("=" * 80)
        
        # Create environment
        env = PortfolioEnv(
            etf_data=self.etf_data,
            etf_list=etf_list,
            initial_capital=initial_capital,
            objective='alpha',
            max_steps=252
        )
        
        # Create agent
        agent = DeltaAgent(
            state_dim=env.observation_space.shape[0],
            action_dim=len(etf_list)
        )
        
        # Training loop
        for episode in range(n_episodes):
            state, _ = env.reset()  # Gymnasium returns (obs, info)
            terminated = False
            
            while not terminated:
                # Select action
                action = agent.select_action(state, training=True)
                
                # Take step (Gymnasium returns 5-tuple)
                next_state, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                
                # Store reward
                agent.store_reward(reward)
                
                state = next_state
            
            # Train at end of episode
            metrics = agent.train()
            
            # Log progress
            if (episode + 1) % 50 == 0:
                print(f"Episode {episode+1}/{n_episodes}: "
                      f"Return={metrics.get('episode_return', 0):.2f}, "
                      f"Loss={metrics.get('loss', 0):.4f}, "
                      f"Entropy={metrics.get('entropy', 0):.4f}")
        
        # Save agent
        save_path = self.save_dir / 'delta_agent.pkl'
        agent.save(str(save_path))
        print(f"✅ Delta agent saved to {save_path}")
        
        return agent
    
    def train_all_agents(self, n_episodes: int = 500):
        """
        Train all 4 agents with their respective ETF universes.
        
        Args:
            n_episodes: Number of episodes per agent
        """
        print("\n" + "=" * 80)
        print("TRAINING ALL 4 RL AGENTS")
        print("=" * 80)
        
        # Define ETF universes for each pod (only use available ETFs)
        all_available = set(self.etf_data.keys())
        
        pod_etfs = {
            'POD1': [e for e in ['BILL', 'VAF', 'VAS'] if e in all_available],
            'POD2': [e for e in ['VAF', 'VHY', 'VAS', 'GOLD'] if e in all_available],
            'POD3': [e for e in ['VGS', 'VTS', 'VAS', 'NDQ', 'VAF', 'GOLD'] if e in all_available],
            'POD4': [e for e in ['NDQ', 'VTS', 'VGS'] if e in all_available]
        }
        
        # Ensure each pod has at least 2 ETFs
        for pod, etfs in pod_etfs.items():
            if len(etfs) < 2:
                print(f"⚠️  Warning: {pod} has only {len(etfs)} ETFs, skipping...")
                return {}
        
        # Train each agent
        agents = {}
        
        agents['alpha'] = self.train_alpha_agent(pod_etfs['POD1'], n_episodes, 15000)
        agents['beta'] = self.train_beta_agent(pod_etfs['POD2'], n_episodes, 25000)
        agents['gamma'] = self.train_gamma_agent(pod_etfs['POD3'], n_episodes, 50000)
        agents['delta'] = self.train_delta_agent(pod_etfs['POD4'], n_episodes, 10000)
        
        print("\n" + "=" * 80)
        print("✅ ALL AGENTS TRAINED SUCCESSFULLY!")
        print("=" * 80)
        
        return agents
