"""OpenMarkets Configuration Management"""
from typing import Optional, Literal
from pydantic import BaseModel, Field, SecretStr
from functools import lru_cache


class OpenMarketsConfig(BaseModel):
    """OpenMarkets API configuration."""
    
    # API Credentials
    api_key: SecretStr = Field(..., description="OpenMarkets API key")
    api_secret: SecretStr = Field(..., description="OpenMarkets API secret")
    
    # Environment
    environment: Literal["sandbox", "production"] = Field(
        default="sandbox",
        description="API environment"
    )
    
    # API Endpoints
    base_url: str = Field(
        default="https://api.openmarkets.com.au/v1",
        description="Base API URL"
    )
    websocket_url: str = Field(
        default="wss://stream.openmarkets.com.au/v1",
        description="WebSocket streaming URL"
    )
    
    # Timeouts and Retries
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_backoff_factor: float = Field(default=1.5, ge=1.0, le=10.0)
    
    # Rate Limiting
    rate_limit_per_second: int = Field(default=10, ge=1, le=100)
    rate_limit_burst: int = Field(default=20, ge=1, le=200)
    
    # Trading Configuration
    default_exchange: Literal["ASX", "Chi-X", "NSX"] = Field(default="ASX")
    enable_paper_trading: bool = Field(default=False)
    
    # Event Sourcing
    event_store_enabled: bool = Field(default=True)
    event_store_topic: str = Field(default="openmarkets.trading.events")
    
    # Data Mesh
    data_mesh_enabled: bool = Field(default=True)
    data_mesh_namespace: str = Field(default="openmarkets")
    
    # ML/RL Configuration
    ml_enabled: bool = Field(default=True)
    rl_enabled: bool = Field(default=False)
    model_registry_url: Optional[str] = Field(default=None)
    
    # MCP Configuration
    mcp_enabled: bool = Field(default=True)
    mcp_server_port: int = Field(default=8100, ge=1024, le=65535)
    
    # Compliance
    aml_screening_enabled: bool = Field(default=True)
    best_execution_monitoring: bool = Field(default=True)
    asic_reporting_enabled: bool = Field(default=True)
    
    class Config:
        env_prefix = "OPENMARKETS_"


@lru_cache()
def get_openmarkets_config() -> OpenMarketsConfig:
    """Get cached OpenMarkets configuration."""
    return OpenMarketsConfig()
