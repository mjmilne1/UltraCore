# Contributing to UltraCore

Thank you for your interest in contributing to UltraCore! This document provides comprehensive guidelines for contributing to the project.

**TuringDynamics / Richelou Pty Ltd - Proprietary**

---

## 📚 Quick Links

- **[Getting Started](#getting-started)** - Setup and first steps
- **[Development Workflow](#development-workflow)** - How to contribute
- **[Code Standards](#code-standards)** - Quality requirements
- **[Testing](#testing)** - Test requirements
- **[Pull Requests](#pull-requests)** - PR process
- **[Community](#community)** - Communication channels

---

## 🚀 Getting Started

### Prerequisites

**Required:**
- Python 3.10 or higher
- Git
- PostgreSQL 15+
- Redis 7+
- Kafka 3.5+

**Recommended:**
- Docker Desktop (for local services)
- VS Code or PyCharm
- GitHub CLI (`gh`)

---

### Initial Setup

**1. Fork and Clone**

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/UltraCore.git
cd UltraCore

# Add upstream remote
git remote add upstream https://github.com/TuringDynamics3000/UltraCore.git
```

**2. Set Up Development Environment**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -e ".[all]"

# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

**3. Configure Environment**

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your local configuration
# - Database connection
# - Redis connection
# - Kafka connection
# - API keys (if needed)
```

**4. Set Up Local Services**

```bash
# Using Docker Compose
docker-compose up -d postgres redis kafka

# Or install services locally
# PostgreSQL, Redis, Kafka
```

**5. Initialize Database**

```bash
# Run migrations
alembic upgrade head

# (Optional) Load sample data
python scripts/seed_data.py
```

**6. Verify Setup**

```bash
# Run tests
pytest

# Run linting
pre-commit run --all-files

# Start development server
uvicorn ultracore.api.main:app --reload
```

---

## 🔄 Development Workflow

### Finding Work

**1. Check Existing Issues**
- Browse [open issues](https://github.com/TuringDynamics3000/UltraCore/issues)
- Look for `good first issue` or `help wanted` labels
- Comment on issue to claim it

**2. Create New Issue**
- Search for duplicates first
- Use appropriate issue template
- Provide detailed description
- Wait for approval before starting work

---

### Branch Strategy

**Branch Naming:**
```
<type>/<short-description>

Examples:
- feature/account-closure
- fix/payment-timeout
- refactor/event-store
- docs/api-documentation
```

**Branch Types:**
- `feature/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation
- `test/` - Test improvements
- `chore/` - Maintenance tasks

---

### Making Changes

**1. Create Branch**

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature
```

**2. Make Changes**

```bash
# Make your changes
# Follow code standards (see below)
# Write tests for new code
# Update documentation

# Run pre-commit hooks
pre-commit run --all-files

# Run tests
pytest

# Run specific tests
pytest tests/unit/domains/accounts/
```

**3. Commit Changes**

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat(accounts): add account closure functionality"

# Pre-commit hooks will run automatically
# Fix any issues and commit again if needed
```

**4. Push Changes**

```bash
# Push to your fork
git push origin feature/your-feature
```

**5. Create Pull Request**

```bash
# Using GitHub CLI
gh pr create --title "feat(accounts): add account closure" \
  --body "Description of changes..."

# Or create PR on GitHub web interface
```

---

## 📏 Code Standards

### Style Guide

**Python Style:**
- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use type hints for all functions
- Write docstrings for public APIs

**Example:**

```python
from decimal import Decimal
from typing import Optional

def calculate_interest(
    balance: Decimal,
    rate: Decimal,
    period_days: int = 365
) -> Decimal:
    """
    Calculate interest for a given balance and rate.
    
    Args:
        balance: Account balance
        rate: Annual interest rate (percentage)
        period_days: Number of days in period (default: 365)
    
    Returns:
        Calculated interest amount
    
    Raises:
        ValueError: If balance or rate is negative
    """
    if balance < 0 or rate < 0:
        raise ValueError("Balance and rate must be non-negative")
    
    return balance * rate / 100 * period_days / 365
```

---

### Code Quality

**Required:**
- ✅ All tests pass
- ✅ Code coverage ≥ 80%
- ✅ No linting errors
- ✅ Type checking passes
- ✅ No security issues
- ✅ Documentation updated

**Tools:**
- **Black** - Code formatting
- **Ruff** - Linting
- **MyPy** - Type checking
- **Bandit** - Security scanning
- **pytest** - Testing

**Run All Checks:**

```bash
# Format code
black src/ tests/

# Lint code
ruff check --fix src/ tests/

# Type check
mypy src/

# Security scan
bandit -r src/

# Run tests with coverage
pytest --cov=src/ultracore --cov-report=html
```

---

### Architecture Guidelines

**Follow DDD Principles:**
- Keep domain logic in domain layer
- Use aggregates for consistency boundaries
- Emit domain events for state changes
- Use repositories for persistence

**Event Sourcing:**
- All state changes via events
- Events are immutable
- Events are versioned
- Support event replay

**Data Mesh:**
- Domain-owned data products
- Self-serve data infrastructure
- Federated governance
- Product thinking

**Example Domain Structure:**

```python
# Domain aggregate
class Account:
    def __init__(self, account_id: str, customer_id: str):
        self.account_id = account_id
        self.customer_id = customer_id
        self.balance = Decimal("0")
        self._events: List[DomainEvent] = []
    
    def deposit(self, amount: Decimal) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        self.balance += amount
        self._events.append(AccountDepositedEvent(
            account_id=self.account_id,
            amount=amount,
            new_balance=self.balance
        ))
```

---

## 🧪 Testing

### Test Requirements

**Coverage Targets:**
- Unit tests: ≥ 80%
- Integration tests: ≥ 70%
- Critical paths: 100%

**Test Types:**
- **Unit Tests** - Test individual functions/classes
- **Integration Tests** - Test component interactions
- **End-to-End Tests** - Test complete workflows
- **Performance Tests** - Test performance requirements

---

### Writing Tests

**Use AAA Pattern:**

```python
import pytest
from decimal import Decimal
from ultracore.domains.accounts.models.account import Account

def test_calculate_interest_with_positive_balance():
    # Arrange
    account = Account(balance=Decimal("1000.00"))
    rate = Decimal("5.0")
    
    # Act
    interest = account.calculate_interest(rate)
    
    # Assert
    assert interest == Decimal("50.00")
```

**Test Naming:**

```python
# Good
def test_deposit_positive_amount_increases_balance():
    pass

def test_deposit_negative_amount_raises_value_error():
    pass

# Bad
def test_deposit():
    pass

def test_1():
    pass
```

**Use Fixtures:**

```python
@pytest.fixture
def account():
    return Account(
        account_id="acc-123",
        customer_id="customer-456",
        balance=Decimal("1000.00")
    )

def test_with_fixture(account):
    assert account.balance == Decimal("1000.00")
```

---

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/domains/accounts/test_account.py

# Run specific test
pytest tests/unit/domains/accounts/test_account.py::test_calculate_interest

# Run with coverage
pytest --cov=src/ultracore --cov-report=html

# Run by marker
pytest -m unit
pytest -m integration
pytest -m "not e2e"

# Run in parallel
pytest -n auto
```

---

## 🔀 Pull Requests

### PR Guidelines

**Before Creating PR:**
- ✅ All tests pass locally
- ✅ Code is formatted and linted
- ✅ Documentation is updated
- ✅ Self-review completed
- ✅ Commits follow conventional commits

**PR Title:**
```
<type>(<scope>): <description>

Examples:
- feat(accounts): add account closure functionality
- fix(payments): resolve NPP timeout issue
- docs(api): update REST API documentation
```

**PR Description:**

Use the PR template and include:
- Description of changes
- Type of change (feature, fix, etc.)
- Testing performed
- Related issues
- Screenshots (if UI changes)
- Breaking changes (if any)

---

### PR Process

**1. Create PR**
- Use descriptive title
- Fill out PR template completely
- Link related issues
- Add appropriate labels

**2. Code Review**
- Address reviewer feedback
- Make requested changes
- Respond to comments
- Re-request review

**3. Merge**
- Ensure all CI checks pass
- Get required approvals (1+)
- Squash and merge (default)
- Delete branch after merge

---

### Review Checklist

**For Authors:**
- [ ] Code follows style guide
- [ ] Tests are comprehensive
- [ ] Documentation is updated
- [ ] No security issues
- [ ] Performance is acceptable
- [ ] Self-review completed

**For Reviewers:**
- [ ] Code quality is good
- [ ] Functionality is correct
- [ ] Tests are adequate
- [ ] Security is considered
- [ ] Architecture is sound
- [ ] Documentation is clear

---

## 💬 Community

### Communication Channels

**GitHub:**
- [Issues](https://github.com/TuringDynamics3000/UltraCore/issues) - Bug reports, feature requests
- [Discussions](https://github.com/TuringDynamics3000/UltraCore/discussions) - Questions, ideas
- [Pull Requests](https://github.com/TuringDynamics3000/UltraCore/pulls) - Code contributions

**Email:**
- General: info@turingdynamics.com.au
- Security: security@turingdynamics.com.au

---

### Getting Help

**Documentation:**
- [README](README.md) - Project overview
- [Architecture Docs](docs/architecture/) - System design
- [API Docs](docs/api/) - API reference
- [Developer Guide](docs/developer-guide/) - Development guide
- [Quality Gates](docs/quality/) - Quality standards

**Asking Questions:**
1. Search existing issues and discussions
2. Check documentation
3. Ask in GitHub Discussions
4. Create issue if needed

---

## 🔒 Security

### Security Guidelines

**Never Commit:**
- `.env` files
- API keys or secrets
- Credentials or passwords
- Customer data
- Private keys

**Always:**
- Use environment variables for secrets
- Validate all inputs
- Use parameterized queries
- Implement authentication
- Log security events

**Reporting Security Issues:**
- Email: security@turingdynamics.com.au
- Do NOT create public issues
- Include detailed description
- Provide reproduction steps

See [SECURITY.md](SECURITY.md) for full security policy.

---

## 📝 Commit Messages

### Conventional Commits

**Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting
- `refactor` - Code refactoring
- `test` - Tests
- `chore` - Maintenance

**Examples:**

```bash
# Simple commit
git commit -m "feat(accounts): add account closure"

# With body
git commit -m "feat(accounts): add account closure

Implements account closure functionality with proper
event sourcing and audit trail.

Closes #123"

# Breaking change
git commit -m "feat(api)!: change authentication flow

BREAKING CHANGE: Authentication now requires OAuth 2.0
instead of JWT tokens."
```

---

## 📋 Checklist

### Before First Contribution

- [ ] Read this guide completely
- [ ] Set up development environment
- [ ] Run tests successfully
- [ ] Install pre-commit hooks
- [ ] Read code standards
- [ ] Review existing code

### Before Each Contribution

- [ ] Create/claim issue
- [ ] Create feature branch
- [ ] Write code and tests
- [ ] Run all checks locally
- [ ] Update documentation
- [ ] Self-review changes
- [ ] Create pull request

### Before Merging

- [ ] All CI checks pass
- [ ] Code review approved
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Commits are clean

---

## 🎓 Learning Resources

### Internal Documentation

- **[Architecture Overview](docs/architecture/README.md)** - System design
- **[Developer Guide](docs/developer-guide/README.md)** - Development workflow
- **[API Documentation](docs/api/README.md)** - API reference
- **[Code Navigation](docs/code-navigation/README.md)** - Finding code
- **[Quality Gates](docs/quality/README.md)** - Quality standards

### External Resources

- **[Python Style Guide (PEP 8)](https://pep8.org/)** - Python conventions
- **[Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)** - DDD principles
- **[Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)** - Event sourcing pattern
- **[Conventional Commits](https://www.conventionalcommits.org/)** - Commit format

---

## 🙏 Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes
- Project documentation

Thank you for contributing to UltraCore! 🚀

---

## 📞 Contact

**TuringDynamics / Richelou Pty Ltd**

- Website: https://turingdynamics.com.au
- Email: info@turingdynamics.com.au
- Security: security@turingdynamics.com.au

---

**© 2025 Richelou Pty Ltd. All Rights Reserved.**
