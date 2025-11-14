# UltraCore Testing Guide

Comprehensive testing documentation for the UltraCore platform.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Test Categories](#test-categories)
- [Fixtures](#fixtures)
- [Coverage](#coverage)
- [CI/CD Integration](#cicd-integration)

---

## Quick Start

### Run All Tests

```bash
# Using Docker Compose (recommended)
docker-compose -f docker-compose.test.yml up --build

# Locally (requires services running)
pytest tests/
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit/ -m unit

# Integration tests
pytest tests/integration/ -m integration

# E2E tests
pytest tests/e2e/ -m e2e

# Security tests
pytest tests/security/ -m security

# Performance tests
pytest tests/performance/ -m performance
```

---

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── pytest.ini                     # Pytest configuration
├── README.md                      # This file
│
├── unit/                          # Fast, isolated tests
│   ├── investment_pods/           # Investment Pods module
│   │   ├── test_pod_aggregate.py
│   │   ├── test_portfolio_optimizer.py
│   │   ├── test_glide_path_engine.py
│   │   ├── test_downside_protection.py
│   │   └── test_tax_optimizer.py
│   ├── multitenancy/              # Multi-tenancy module
│   │   ├── test_tenant_service.py
│   │   └── test_tenant_isolation.py
│   ├── security/                  # Security module
│   │   ├── test_jwt_auth.py
│   │   └── test_encryption.py
│   ├── clients/                   # Client management
│   └── transactions/              # Transaction processing
│
├── integration/                   # Tests with real dependencies
│   ├── api/                       # API endpoint tests
│   │   ├── test_pod_api.py
│   │   └── test_tenant_api.py
│   ├── database/                  # Database integration
│   │   ├── test_repositories.py
│   │   └── test_migrations.py
│   ├── kafka/                     # Kafka integration
│   │   ├── test_event_publishing.py
│   │   └── test_event_consumption.py
│   └── redis/                     # Redis caching
│       └── test_cache.py
│
├── e2e/                          # End-to-end workflows
│   ├── test_pod_lifecycle.py      # Full Pod creation to completion
│   ├── test_tenant_provisioning.py
│   └── test_user_journey.py
│
├── security/                     # Security & penetration tests
│   ├── test_sql_injection.py
│   ├── test_xss.py
│   ├── test_authentication.py
│   ├── test_authorization.py
│   └── test_secrets_management.py
│
├── performance/                  # Load & stress tests
│   ├── test_api_performance.py
│   ├── test_database_performance.py
│   └── locustfile.py              # Load testing with Locust
│
└── fixtures/                     # Test data & factories
    ├── factories.py               # Factory Boy factories
    ├── seed_data.py               # Test data generation
    └── sql/
        └── init_test_db.sql       # Database initialization
```

---

## Running Tests

### Local Development

**Prerequisites:**
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL, Redis, Kafka (or use Docker Compose)

**Setup:**

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Start test services
docker-compose -f docker-compose.test.yml up -d postgres-test redis-test kafka-test

# Run tests
pytest tests/
```

### Using Docker Compose (Recommended)

```bash
# Build and run all tests
docker-compose -f docker-compose.test.yml up --build

# Run specific test suite
docker-compose -f docker-compose.test.yml run test-runner pytest tests/unit/

# Run with coverage
docker-compose -f docker-compose.test.yml run test-runner pytest tests/ --cov=ultracore --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Markers

Use pytest markers to run specific test categories:

```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# Tests that require database
pytest -m requires_db

# Investment Pods tests
pytest -m investment_pods

# Slow tests (skip for quick feedback)
pytest -m "not slow"
```

---

## Writing Tests

### Test Naming Convention

- **Files**: `test_<module_name>.py`
- **Classes**: `Test<ClassName>`
- **Functions**: `test_<what_it_tests>`

### Example Unit Test

```python
import pytest
from ultracore.investment_pods.aggregates.pod_aggregate import PodAggregate

@pytest.mark.unit
@pytest.mark.investment_pods
def test_pod_creation(first_home_pod_data, ultrawealth_tenant):
    """Test creating a first home Pod."""
    # Arrange
    tenant_id = ultrawealth_tenant["tenant_id"]
    client_id = "test_client_123"
    
    # Act
    pod = PodAggregate.create(
        tenant_id=tenant_id,
        client_id=client_id,
        **first_home_pod_data
    )
    
    # Assert
    assert pod.pod_id is not None
    assert pod.goal_type == "first_home"
    assert pod.target_amount == first_home_pod_data["target_amount"]
```

### Example Integration Test

```python
import pytest

@pytest.mark.integration
@pytest.mark.requires_db
@pytest.mark.asyncio
async def test_pod_repository_save(clean_db, first_home_pod_data):
    """Test saving Pod to database."""
    # Arrange
    from ultracore.investment_pods.repository.pod_repository import PodRepository
    repo = PodRepository(clean_db)
    
    # Act
    pod_id = await repo.save(first_home_pod_data)
    
    # Assert
    assert pod_id is not None
    retrieved_pod = await repo.get_by_id(pod_id)
    assert retrieved_pod["goal_type"] == "first_home"
```

### Example E2E Test

```python
import pytest

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_complete_pod_lifecycle(api_client, api_headers, ultrawealth_tenant):
    """Test complete Pod lifecycle from creation to goal achievement."""
    # 1. Create Pod
    response = await api_client.post(
        "/api/pods/create",
        json={
            "tenant_id": ultrawealth_tenant["tenant_id"],
            "goal_type": "first_home",
            "target_amount": 100000,
            "target_date": "2029-11-14",
            "initial_deposit": 10000,
            "monthly_contribution": 1000
        },
        headers=api_headers
    )
    assert response.status_code == 201
    pod_id = response.json()["pod_id"]
    
    # 2. Optimize allocation
    response = await api_client.post(
        f"/api/pods/{pod_id}/optimize",
        headers=api_headers
    )
    assert response.status_code == 200
    
    # 3. Check glide path
    response = await api_client.get(
        f"/api/pods/{pod_id}/glide-path",
        headers=api_headers
    )
    assert response.status_code == 200
    assert len(response.json()["transitions"]) > 0
```

---

## Test Categories

### Unit Tests (`tests/unit/`)

**Characteristics:**
- Fast (< 100ms per test)
- No external dependencies
- Test single units of code
- Use mocks for dependencies

**When to write:**
- Testing business logic
- Testing domain models
- Testing pure functions
- Testing calculations

### Integration Tests (`tests/integration/`)

**Characteristics:**
- Slower (100ms - 1s per test)
- Use real external services
- Test component interactions
- Require test infrastructure

**When to write:**
- Testing database operations
- Testing API endpoints
- Testing Kafka events
- Testing Redis caching

### E2E Tests (`tests/e2e/`)

**Characteristics:**
- Slow (1s+ per test)
- Test complete workflows
- Use real services
- Simulate user journeys

**When to write:**
- Testing critical user flows
- Testing multi-step processes
- Testing system integration
- Before major releases

### Security Tests (`tests/security/`)

**Characteristics:**
- Test security vulnerabilities
- Penetration testing
- Authentication/authorization
- Input validation

**When to write:**
- After security fixes
- Before production deployment
- Regular security audits
- Compliance requirements

### Performance Tests (`tests/performance/`)

**Characteristics:**
- Test system performance
- Load testing
- Stress testing
- Benchmark comparisons

**When to write:**
- Before scaling
- After optimization
- Regular performance audits
- Capacity planning

---

## Fixtures

### Using Fixtures

Fixtures are defined in `conftest.py` and automatically available in all tests:

```python
def test_with_fixtures(test_user, ultrawealth_tenant, first_home_pod_data):
    """Fixtures are automatically injected."""
    assert test_user["role"] == "user"
    assert ultrawealth_tenant["tenant_id"] == "ultrawealth"
    assert first_home_pod_data["goal_type"] == "first_home"
```

### Available Fixtures

**Database:**
- `db_connection_string` - Test database URL
- `db_session` - Database session
- `clean_db` - Clean database for each test

**Kafka:**
- `kafka_bootstrap_servers` - Kafka servers
- `kafka_producer` - Kafka producer
- `kafka_consumer` - Kafka consumer

**Redis:**
- `redis_connection_params` - Redis connection
- `redis_client` - Redis client

**Tenants:**
- `test_tenant_id` - Unique tenant ID
- `ultrawealth_tenant` - UltraWealth tenant config

**Users:**
- `test_user` - Regular user
- `admin_user` - Admin user

**Investment Pods:**
- `first_home_pod_data` - First home Pod data
- `retirement_pod_data` - Retirement Pod data
- `wealth_pod_data` - Wealth Pod data

**Market Data:**
- `australian_etf_universe` - Australian ETFs
- `mock_market_data` - Mock market data

**Authentication:**
- `jwt_secret` - JWT secret key
- `valid_jwt_token` - Valid JWT token
- `api_headers` - API headers with auth

---

## Coverage

### Running Coverage

```bash
# Generate coverage report
pytest tests/ --cov=ultracore --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Check coverage threshold (80% minimum)
pytest tests/ --cov=ultracore --cov-fail-under=80
```

### Coverage Goals

- **Overall**: 80%+ coverage
- **Critical modules**: 90%+ coverage
  - Investment Pods
  - Multi-tenancy
  - Security
  - Authentication

### Excluded from Coverage

- Test files
- Migration scripts
- Configuration files
- `__init__.py` files

---

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Pull requests
- Pushes to `main`
- Nightly builds

### Test Pipeline

1. **Lint & Format** - Code quality checks
2. **Security Scan** - Vulnerability scanning
3. **Unit Tests** - Fast feedback
4. **Integration Tests** - Component testing
5. **E2E Tests** - Full workflow testing
6. **Coverage Report** - Coverage analysis
7. **Performance Tests** - Benchmark comparison

### Required Checks

All PRs must pass:
- ✅ All tests passing
- ✅ 80%+ code coverage
- ✅ No security vulnerabilities
- ✅ No linting errors

---

## Best Practices

### DO

✅ Write tests before fixing bugs  
✅ Use descriptive test names  
✅ Follow AAA pattern (Arrange, Act, Assert)  
✅ Test edge cases and error conditions  
✅ Keep tests independent  
✅ Use fixtures for common setup  
✅ Mock external dependencies in unit tests  
✅ Clean up resources after tests  

### DON'T

❌ Write tests that depend on execution order  
❌ Use sleep() for timing (use proper async/await)  
❌ Test implementation details  
❌ Share state between tests  
❌ Ignore flaky tests  
❌ Skip writing tests for "simple" code  
❌ Commit commented-out tests  

---

## Troubleshooting

### Tests Fail Locally

```bash
# Clean test environment
docker-compose -f docker-compose.test.yml down -v

# Rebuild containers
docker-compose -f docker-compose.test.yml up --build

# Check service health
docker-compose -f docker-compose.test.yml ps
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.test.yml ps postgres-test

# View logs
docker-compose -f docker-compose.test.yml logs postgres-test

# Test connection
psql postgresql://ultracore_test:test_password_12345@localhost:5433/ultracore_test
```

### Kafka Issues

```bash
# Check Kafka is running
docker-compose -f docker-compose.test.yml ps kafka-test

# View logs
docker-compose -f docker-compose.test.yml logs kafka-test

# List topics
docker-compose -f docker-compose.test.yml exec kafka-test kafka-topics --list --bootstrap-server localhost:9093
```

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)

---

## Contact

For questions about testing:
- Create an issue in GitHub
- Contact the DevOps team
- Check the testing channel in Slack

---

**Happy Testing! 🧪**
