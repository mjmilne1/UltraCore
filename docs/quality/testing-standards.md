# 🧪 Testing Standards

Comprehensive testing standards and best practices for UltraCore.

---

## 📚 Quick Links

- **[Overview](#overview)** - Testing philosophy
- **[Test Types](#test-types)** - Unit, integration, E2E
- **[Testing Standards](#testing-standards)** - Requirements
- **[Best Practices](#best-practices)** - Writing good tests
- **[Test Organization](#test-organization)** - Structure
- **[Tools & Frameworks](#tools--frameworks)** - Testing tools

---

## 🎯 Overview

Testing is critical for maintaining code quality, preventing regressions, and enabling confident refactoring.

### Testing Philosophy

**Test Pyramid:**

```
       ┌─────────┐
       │   E2E   │  ← Few, slow, expensive
       ├─────────┤
       │Integration│ ← Some, medium speed
       ├─────────┤
       │   Unit  │  ← Many, fast, cheap
       └─────────┘
```

**Distribution:**
- **70%** Unit tests
- **20%** Integration tests
- **10%** End-to-end tests

### Goals

**Quality Assurance:**
- Catch bugs early
- Prevent regressions
- Verify functionality
- Ensure reliability

**Documentation:**
- Demonstrate usage
- Document behavior
- Provide examples
- Clarify intent

**Design:**
- Drive good design
- Enforce interfaces
- Promote modularity
- Enable refactoring

---

## 🧩 Test Types

### 1. Unit Tests

**Purpose:** Test individual functions/classes in isolation

**Characteristics:**
- Fast (< 1ms per test)
- Isolated (no external dependencies)
- Focused (single responsibility)
- Deterministic (same input → same output)

**Example:**

```python
# src/ultracore/domains/accounts/models/account.py
class Account:
    def calculate_interest(self, rate: Decimal) -> Decimal:
        return self.balance * rate / 100

# tests/domains/accounts/models/test_account.py
import pytest
from decimal import Decimal
from ultracore.domains.accounts.models.account import Account

class TestAccount:
    def test_calculate_interest_with_positive_balance(self):
        # Arrange
        account = Account(balance=Decimal("1000.00"))
        rate = Decimal("5.0")
        
        # Act
        interest = account.calculate_interest(rate)
        
        # Assert
        assert interest == Decimal("50.00")
    
    def test_calculate_interest_with_zero_balance(self):
        account = Account(balance=Decimal("0.00"))
        rate = Decimal("5.0")
        
        interest = account.calculate_interest(rate)
        
        assert interest == Decimal("0.00")
    
    def test_calculate_interest_with_zero_rate(self):
        account = Account(balance=Decimal("1000.00"))
        rate = Decimal("0.0")
        
        interest = account.calculate_interest(rate)
        
        assert interest == Decimal("0.00")
```

**Coverage Target:** ≥ 80%

---

### 2. Integration Tests

**Purpose:** Test interactions between components

**Characteristics:**
- Medium speed (< 1s per test)
- Real dependencies (database, cache, etc.)
- Workflow-focused
- Transactional (rollback after test)

**Example:**

```python
# tests/integration/test_account_service.py
import pytest
from ultracore.domains.accounts.services.account_service import AccountService
from ultracore.infrastructure.event_store.event_store import EventStore

@pytest.mark.integration
class TestAccountService:
    @pytest.fixture
    async def account_service(self, db_session):
        event_store = EventStore()
        return AccountService(event_store=event_store, db=db_session)
    
    async def test_create_account_publishes_event(self, account_service):
        # Arrange
        customer_id = "customer-123"
        account_type = "savings"
        
        # Act
        account = await account_service.create_account(
            customer_id=customer_id,
            account_type=account_type,
            initial_balance=1000.00
        )
        
        # Assert
        assert account.account_id is not None
        assert account.customer_id == customer_id
        assert account.balance == 1000.00
        
        # Verify event published
        events = await account_service.event_store.get_events(
            aggregate_id=account.account_id
        )
        assert len(events) == 1
        assert events[0].event_type == "AccountCreatedEvent"
```

**Coverage Target:** ≥ 70%

---

### 3. End-to-End Tests

**Purpose:** Test complete user workflows

**Characteristics:**
- Slow (seconds per test)
- Full stack (API → database)
- User-focused
- Realistic scenarios

**Example:**

```python
# tests/e2e/test_account_workflow.py
import pytest
from httpx import AsyncClient

@pytest.mark.e2e
class TestAccountWorkflow:
    async def test_complete_account_lifecycle(self, api_client: AsyncClient):
        # 1. Create customer
        customer_response = await api_client.post(
            "/api/v1/customers",
            json={
                "name": "John Doe",
                "email": "john@example.com"
            }
        )
        assert customer_response.status_code == 201
        customer_id = customer_response.json()["id"]
        
        # 2. Create account
        account_response = await api_client.post(
            "/api/v1/accounts",
            json={
                "customer_id": customer_id,
                "account_type": "savings",
                "initial_balance": 1000.00
            }
        )
        assert account_response.status_code == 201
        account_id = account_response.json()["id"]
        
        # 3. Deposit money
        deposit_response = await api_client.post(
            f"/api/v1/accounts/{account_id}/transactions",
            json={
                "type": "deposit",
                "amount": 500.00
            }
        )
        assert deposit_response.status_code == 201
        
        # 4. Check balance
        balance_response = await api_client.get(
            f"/api/v1/accounts/{account_id}/balance"
        )
        assert balance_response.status_code == 200
        assert balance_response.json()["balance"] == 1500.00
        
        # 5. Close account
        close_response = await api_client.post(
            f"/api/v1/accounts/{account_id}/close"
        )
        assert close_response.status_code == 200
```

**Coverage Target:** Critical paths only

---

### 4. Performance Tests

**Purpose:** Verify performance requirements

**Example:**

```python
# tests/performance/test_account_performance.py
import pytest
import time

@pytest.mark.performance
class TestAccountPerformance:
    async def test_create_account_performance(self, account_service):
        # Warm up
        for _ in range(10):
            await account_service.create_account(
                customer_id="customer-123",
                account_type="savings"
            )
        
        # Measure
        start = time.time()
        iterations = 100
        
        for _ in range(iterations):
            await account_service.create_account(
                customer_id="customer-123",
                account_type="savings"
            )
        
        end = time.time()
        avg_time = (end - start) / iterations
        
        # Assert performance requirement
        assert avg_time < 0.1, f"Average time {avg_time}s exceeds 0.1s"
```

---

## 📏 Testing Standards

### Coverage Requirements

| Code Type | Unit Coverage | Integration Coverage |
|-----------|---------------|---------------------|
| **Domain Models** | ≥ 90% | ≥ 80% |
| **Services** | ≥ 85% | ≥ 75% |
| **API Endpoints** | ≥ 80% | ≥ 70% |
| **Utilities** | ≥ 90% | N/A |
| **Infrastructure** | ≥ 70% | ≥ 80% |

### Test Requirements

**All Code Must Have:**
- Unit tests for business logic
- Integration tests for workflows
- Edge case coverage
- Error case coverage

**Critical Code Must Have:**
- E2E tests for user workflows
- Performance tests
- Security tests
- Load tests

---

## 🎯 Best Practices

### 1. Test Structure

**Use AAA Pattern:**
- **Arrange** - Set up test data
- **Act** - Execute code under test
- **Assert** - Verify results

```python
def test_calculate_interest():
    # Arrange
    account = Account(balance=Decimal("1000.00"))
    rate = Decimal("5.0")
    
    # Act
    interest = account.calculate_interest(rate)
    
    # Assert
    assert interest == Decimal("50.00")
```

---

### 2. Test Naming

**Use Descriptive Names:**

```python
# Bad
def test_1():
    pass

def test_account():
    pass

# Good
def test_calculate_interest_with_positive_balance():
    pass

def test_create_account_with_invalid_customer_id_raises_error():
    pass
```

**Naming Convention:**
```
test_<method>_<scenario>_<expected_result>
```

---

### 3. Test Independence

**Each Test Should:**
- Run independently
- Not depend on other tests
- Clean up after itself
- Use fresh test data

```python
# Bad - Tests depend on each other
def test_create_account():
    global account
    account = create_account()

def test_deposit():
    deposit(account, 100)  # Depends on previous test

# Good - Tests are independent
def test_create_account():
    account = create_account()
    assert account.balance == 0

def test_deposit():
    account = create_account()
    deposit(account, 100)
    assert account.balance == 100
```

---

### 4. Use Fixtures

**Pytest Fixtures:**

```python
import pytest
from ultracore.domains.accounts.models.account import Account

@pytest.fixture
def account():
    """Provide a test account"""
    return Account(
        account_id="acc-123",
        customer_id="customer-456",
        balance=Decimal("1000.00")
    )

@pytest.fixture
async def db_session():
    """Provide a database session"""
    session = create_test_session()
    yield session
    await session.rollback()
    await session.close()

def test_with_fixture(account):
    assert account.balance == Decimal("1000.00")
```

---

### 5. Mock External Dependencies

**Use Mocks for:**
- External APIs
- Databases (in unit tests)
- File systems
- Time-dependent code

```python
from unittest.mock import Mock, patch

def test_send_notification_calls_email_service():
    # Arrange
    email_service = Mock()
    notification_service = NotificationService(email_service)
    
    # Act
    notification_service.send_notification(
        customer_id="customer-123",
        message="Test message"
    )
    
    # Assert
    email_service.send_email.assert_called_once()

@patch('ultracore.utils.time.now')
def test_with_fixed_time(mock_now):
    # Arrange
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)
    mock_now.return_value = fixed_time
    
    # Act
    result = process_with_timestamp()
    
    # Assert
    assert result.timestamp == fixed_time
```

---

### 6. Test Edge Cases

**Always Test:**
- Boundary values
- Empty inputs
- Null values
- Large inputs
- Invalid inputs

```python
def test_calculate_interest_edge_cases():
    account = Account(balance=Decimal("1000.00"))
    
    # Zero rate
    assert account.calculate_interest(Decimal("0")) == Decimal("0")
    
    # Negative rate (if allowed)
    assert account.calculate_interest(Decimal("-5")) == Decimal("-50")
    
    # Very large rate
    assert account.calculate_interest(Decimal("1000")) == Decimal("10000")
    
    # Very small rate
    assert account.calculate_interest(Decimal("0.01")) == Decimal("0.10")
```

---

### 7. Test Error Handling

**Test Exception Cases:**

```python
import pytest

def test_create_account_with_invalid_customer_raises_error():
    with pytest.raises(CustomerNotFoundError) as exc_info:
        create_account(customer_id="invalid")
    
    assert "Customer not found" in str(exc_info.value)

def test_deposit_negative_amount_raises_error():
    account = Account(balance=Decimal("1000.00"))
    
    with pytest.raises(ValueError) as exc_info:
        account.deposit(Decimal("-100"))
    
    assert "Amount must be positive" in str(exc_info.value)
```

---

### 8. Async Testing

**Test Async Code:**

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected_value

@pytest.fixture
async def async_fixture():
    resource = await create_resource()
    yield resource
    await cleanup_resource(resource)
```

---

### 9. Parametrized Tests

**Test Multiple Scenarios:**

```python
import pytest

@pytest.mark.parametrize("balance,rate,expected", [
    (Decimal("1000"), Decimal("5"), Decimal("50")),
    (Decimal("2000"), Decimal("5"), Decimal("100")),
    (Decimal("0"), Decimal("5"), Decimal("0")),
    (Decimal("1000"), Decimal("0"), Decimal("0")),
])
def test_calculate_interest(balance, rate, expected):
    account = Account(balance=balance)
    assert account.calculate_interest(rate) == expected
```

---

## 📁 Test Organization

### Directory Structure

```
tests/
├── unit/                      # Unit tests
│   ├── domains/
│   │   ├── accounts/
│   │   │   ├── models/
│   │   │   │   └── test_account.py
│   │   │   └── services/
│   │   │       └── test_account_service.py
│   │   └── wealth/
│   └── infrastructure/
├── integration/               # Integration tests
│   ├── test_account_workflow.py
│   └── test_payment_workflow.py
├── e2e/                       # End-to-end tests
│   ├── test_account_lifecycle.py
│   └── test_investment_workflow.py
├── performance/               # Performance tests
│   └── test_account_performance.py
├── fixtures/                  # Shared fixtures
│   ├── __init__.py
│   └── account_fixtures.py
└── conftest.py               # Pytest configuration
```

---

### conftest.py

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from ultracore.infrastructure.event_store.event_store import EventStore

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    """Provide database session for tests"""
    engine = create_async_engine("postgresql+asyncpg://localhost/test")
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
def event_store():
    """Provide event store for tests"""
    return EventStore()

# Markers
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
```

---

## 🛠️ Tools & Frameworks

### Testing Framework

**Pytest:**
- Powerful test framework
- Fixture support
- Parametrization
- Plugin ecosystem

**Installation:**
```bash
pip install pytest pytest-asyncio pytest-cov
```

---

### Coverage Tools

**pytest-cov:**

```bash
# Run tests with coverage
pytest --cov=src/ultracore --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Coverage Configuration:**

```ini
# pyproject.toml
[tool.coverage.run]
source = ["src/ultracore"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

---

### Mocking

**unittest.mock:**

```python
from unittest.mock import Mock, patch, MagicMock

# Mock object
mock_service = Mock()
mock_service.method.return_value = "result"

# Patch function
with patch('module.function') as mock_func:
    mock_func.return_value = "result"
    # Test code

# Mock async function
mock_async = AsyncMock()
mock_async.return_value = "result"
```

---

### Factories

**Factory Boy:**

```python
import factory
from ultracore.domains.accounts.models.account import Account

class AccountFactory(factory.Factory):
    class Meta:
        model = Account
    
    account_id = factory.Sequence(lambda n: f"acc-{n}")
    customer_id = factory.Sequence(lambda n: f"customer-{n}")
    balance = factory.Faker('pydecimal', left_digits=5, right_digits=2)
    account_type = "savings"

# Usage
account = AccountFactory()
accounts = AccountFactory.create_batch(10)
```

---

### Database Testing

**pytest-postgresql:**

```python
import pytest
from pytest_postgresql import factories

postgresql_proc = factories.postgresql_proc()
postgresql = factories.postgresql('postgresql_proc')

@pytest.fixture
async def db_session(postgresql):
    # Setup database
    engine = create_async_engine(postgresql.url())
    async with AsyncSession(engine) as session:
        yield session
```

---

## 📊 Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/domains/accounts/test_account.py

# Run specific test
pytest tests/unit/domains/accounts/test_account.py::test_calculate_interest

# Run tests by marker
pytest -m unit
pytest -m integration
pytest -m "not e2e"

# Run with coverage
pytest --cov=src/ultracore

# Run with verbose output
pytest -v

# Run with output
pytest -s

# Run in parallel
pytest -n auto
```

---

### CI Configuration

```yaml
# .github/workflows/ci.yml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -e ".[all]"
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run tests
      run: |
        pytest tests/ \
          --cov=src/ultracore \
          --cov-report=xml \
          --junitxml=test-results.xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## 📚 Additional Resources

- **[CI/CD Pipeline](ci-cd-pipeline.md)** - Automated testing
- **[Pre-commit Hooks](pre-commit-hooks.md)** - Local checks
- **[Code Review Guidelines](code-review-guidelines.md)** - Review process
- **[Quality Metrics](quality-metrics.md)** - Measuring quality

---

**Last Updated:** November 14, 2024
