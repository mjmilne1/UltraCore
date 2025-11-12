"""RL Trading Strategies using PPO and A2C"""
import torch
import torch.nn as nn
from stable_baselines3 import PPO, A2C

from ultracore.ml.rl import BaseRLStrategy
from .trading_env import TradingEnvironment


class PPOTradingStrategy(BaseRLStrategy):
    """
    Proximal Policy Optimization for trading.
    
    PPO is well-suited for continuous action spaces and provides
    stable training with good sample efficiency.
    """
    
    def __init__(self, env: TradingEnvironment):
        super().__init__(
            strategy_name="ppo_trading",
            version="1.0.0"
        )
        self.env = env
        
        # Initialize PPO agent
        self.model = PPO(
            "MlpPolicy",
            env,
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            verbose=1
        )
    
    async def train(self, total_timesteps: int = 100000):
        """Train the PPO agent."""
        self.model.learn(total_timesteps=total_timesteps)
    
    async def predict(self, observation):
        """Predict action given current state."""
        action, _states = self.model.predict(observation, deterministic=True)
        return action
    
    async def save(self, path: str):
        """Save trained model."""
        self.model.save(path)
    
    async def load(self, path: str):
        """Load trained model."""
        self.model = PPO.load(path, env=self.env)


class A2CTradingStrategy(BaseRLStrategy):
    """
    Advantage Actor-Critic for trading.
    
    A2C is faster than PPO and works well for online learning
    with continuous market feedback.
    """
    
    def __init__(self, env: TradingEnvironment):
        super().__init__(
            strategy_name="a2c_trading",
            version="1.0.0"
        )
        self.env = env
        
        self.model = A2C(
            "MlpPolicy",
            env,
            learning_rate=7e-4,
            n_steps=5,
            gamma=0.99,
            gae_lambda=1.0,
            verbose=1
        )
    
    async def train(self, total_timesteps: int = 50000):
        """Train the A2C agent."""
        self.model.learn(total_timesteps=total_timesteps)
    
    async def predict(self, observation):
        """Predict action given current state."""
        action, _states = self.model.predict(observation, deterministic=True)
        return action
