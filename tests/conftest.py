"""
Shared pytest fixtures for UltraCore tests.

This module provides common fixtures used across all test suites.
"""

import os
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any
from uuid import uuid4

# Set test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def db_connection_string():
    """Test database connection string."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://ultracore_test:test_password_12345@localhost:5433/ultracore_test"
    )


@pytest.fixture(scope="function")
def db_session(db_connection_string):
    """Create a fresh database session for each test."""
    # Mock database session for testing
    # Returns None as placeholder - tests using this should mock their DB operations
    yield None


@pytest.fixture(scope="function")
def clean_db(db_session):
    """Clean database before each test."""
    # Mock database cleanup for testing
    yield db_session
    # Cleanup after test


# ============================================================================
# Kafka Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def kafka_bootstrap_servers():
    """Kafka bootstrap servers for testing."""
    return os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9093")


@pytest.fixture(scope="function")
def kafka_producer(kafka_bootstrap_servers):
    """Create Kafka producer for event sourcing tests."""
    # Use mock producer for testing (sync)
    from tests.helpers.mock_kafka import MockKafkaProducer
    
    producer = MockKafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        client_id="ultracore-test-producer"
    )
    
    yield producer
    
    # Cleanup
    producer.close()


@pytest.fixture(scope="function")
def kafka_consumer(kafka_bootstrap_servers):
    """Create Kafka consumer for event sourcing tests."""
    # Use mock consumer for testing (sync)
    from tests.helpers.mock_kafka import MockKafkaConsumer
    
    consumer = MockKafkaConsumer(
        bootstrap_servers=kafka_bootstrap_servers,
        group_id="ultracore-test-consumer",
        topics=["ultracore.investment_pods.events"]
    )
    
    yield consumer
    
    # Cleanup
    consumer.close()


# ============================================================================
# Redis Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def redis_connection_params():
    """Redis connection parameters."""
    return {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6380")),
        "password": os.getenv("REDIS_PASSWORD", "test_redis_password"),
        "db": 0
    }


@pytest.fixture(scope="function")
def redis_client(redis_connection_params):
    """Create Redis client for tests."""
    # Mock Redis client for testing
    yield None


# ============================================================================
# Tenant Fixtures
# ============================================================================

@pytest.fixture
def test_tenant_id():
    """Generate unique tenant ID for testing."""
    return f"test_tenant_{uuid4().hex[:8]}"


@pytest.fixture
def ultrawealth_tenant():
    """UltraWealth tenant configuration."""
    return {
        "tenant_id": "ultrawealth",
        "name": "UltraWealth",
        "status": "active",
        "created_at": datetime.utcnow(),
        "config": {
            "management_fee": Decimal("0.005"),  # 0.50%
            "max_etfs_per_pod": 6,
            "circuit_breaker_threshold": Decimal("0.15"),  # 15%
            "rebalance_threshold": Decimal("0.05")  # 5%
        }
    }


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture
def test_user():
    """Create test user."""
    return {
        "user_id": f"user_{uuid4().hex[:8]}",
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "name": "Test User",
        "role": "user",
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def admin_user():
    """Create admin user."""
    return {
        "user_id": f"admin_{uuid4().hex[:8]}",
        "email": f"admin_{uuid4().hex[:8]}@example.com",
        "name": "Admin User",
        "role": "admin",
        "created_at": datetime.utcnow()
    }


# ============================================================================
# Investment Pods Fixtures
# ============================================================================

@pytest.fixture
def first_home_pod_data():
    """First home Pod test data."""
    return {
        "pod_id": f"pod_{uuid4().hex[:8]}",
        "goal_type": "first_home",
        "target_amount": Decimal("100000.00"),
        "target_date": datetime.utcnow() + timedelta(days=1825),  # 5 years
        "initial_deposit": Decimal("10000.00"),
        "monthly_contribution": Decimal("1000.00"),
        "risk_tolerance": "moderate"
    }


@pytest.fixture
def retirement_pod_data():
    """Retirement Pod test data."""
    return {
        "pod_id": f"pod_{uuid4().hex[:8]}",
        "goal_type": "retirement",
        "target_amount": Decimal("1000000.00"),
        "target_date": datetime.utcnow() + timedelta(days=10950),  # 30 years
        "initial_deposit": Decimal("50000.00"),
        "monthly_contribution": Decimal("2000.00"),
        "risk_tolerance": "aggressive"
    }


@pytest.fixture
def wealth_pod_data():
    """Wealth accumulation Pod test data."""
    return {
        "pod_id": f"pod_{uuid4().hex[:8]}",
        "goal_type": "wealth",
        "target_amount": Decimal("500000.00"),
        "target_date": datetime.utcnow() + timedelta(days=3650),  # 10 years
        "initial_deposit": Decimal("25000.00"),
        "monthly_contribution": Decimal("1500.00"),
        "risk_tolerance": "moderate"
    }


# ============================================================================
# ETF Fixtures
# ============================================================================

@pytest.fixture
def australian_etf_universe():
    """Australian ETF universe for testing."""
    return [
        {"ticker": "VAS.AX", "name": "Vanguard Australian Shares", "expense_ratio": 0.0010},
        {"ticker": "VGS.AX", "name": "Vanguard International Shares", "expense_ratio": 0.0018},
        {"ticker": "NDQ.AX", "name": "BetaShares NASDAQ 100", "expense_ratio": 0.0048},
        {"ticker": "VAF.AX", "name": "Vanguard Australian Fixed Interest", "expense_ratio": 0.0020},
        {"ticker": "VGB.AX", "name": "Vanguard Australian Government Bonds", "expense_ratio": 0.0020},
        {"ticker": "IOZ.AX", "name": "iShares Core S&P/ASX 200", "expense_ratio": 0.0009},
    ]


# ============================================================================
# Market Data Fixtures
# ============================================================================

@pytest.fixture
def mock_market_data():
    """Mock market data for testing."""
    return {
        "VAS.AX": {
            "price": Decimal("89.50"),
            "returns_3y": Decimal("0.1028"),
            "volatility": Decimal("0.1261"),
            "max_drawdown": Decimal("0.1518")
        },
        "VGS.AX": {
            "price": Decimal("95.20"),
            "returns_3y": Decimal("0.2110"),
            "volatility": Decimal("0.1450"),
            "max_drawdown": Decimal("0.1820")
        }
    }


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def jwt_secret():
    """JWT secret for testing."""
    return os.getenv("JWT_SECRET_KEY", "test_jwt_secret_key_for_testing_only_32_chars_min")


@pytest.fixture
def valid_jwt_token(jwt_secret, test_user):
    """Generate valid JWT token for testing."""
    # TODO: Implement JWT token generation
    return "test_jwt_token"


@pytest.fixture
def expired_jwt_token(jwt_secret):
    """Generate expired JWT token for testing."""
    # TODO: Implement expired JWT token generation
    return "expired_jwt_token"


# ============================================================================
# API Fixtures
# ============================================================================

@pytest.fixture
def api_client():
    """Create API client for testing."""
    # Mock API client for testing
    yield None


@pytest.fixture
def api_headers(valid_jwt_token):
    """API request headers with authentication."""
    return {
        "Authorization": f"Bearer {valid_jwt_token}",
        "Content-Type": "application/json"
    }


# ============================================================================
# Performance Testing Fixtures
# ============================================================================

@pytest.fixture
def performance_threshold():
    """Performance thresholds for tests."""
    return {
        "api_response_time_ms": 200,
        "database_query_time_ms": 50,
        "kafka_publish_time_ms": 10
    }


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment after each test."""
    yield
    # Cleanup code here if needed


# ============================================================================
# Event Store Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def event_store(kafka_bootstrap_servers, kafka_producer):
    """Event store for retrieving events from Kafka."""
    from tests.helpers.event_store import EventStore
    
    store = EventStore(
        bootstrap_servers=kafka_bootstrap_servers,
        kafka_producer=kafka_producer
    )
    
    yield store
    
    # Cleanup
    store.close()


# ============================================================================
# UltraOptimiser Fixtures
# ============================================================================

@pytest.fixture
def mock_ultraoptimiser():
    """Mock UltraOptimiser service for testing."""
    from tests.helpers.mock_ultraoptimiser import MockOptimisationService
    return MockOptimisationService()


@pytest.fixture
def ultraoptimiser_adapter(mock_ultraoptimiser):
    """UltraOptimiser adapter with mock service."""
    from src.ultracore.domains.wealth.integration.ultraoptimiser_adapter import UltraOptimiserAdapter
    return UltraOptimiserAdapter(optimiser=mock_ultraoptimiser)


@pytest.fixture
def failing_ultraoptimiser():
    """Mock UltraOptimiser that fails for error testing."""
    from tests.helpers.mock_ultraoptimiser import MockOptimiserWithFailure
    return MockOptimiserWithFailure(fail_after=2)


@pytest.fixture
def slow_ultraoptimiser():
    """Mock UltraOptimiser with slow responses."""
    from tests.helpers.mock_ultraoptimiser import MockOptimiserSlow
    return MockOptimiserSlow()
