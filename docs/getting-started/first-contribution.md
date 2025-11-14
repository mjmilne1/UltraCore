# 🎯 Your First Contribution

Make your first contribution to UltraCore! This guide walks you through finding an issue, making changes, and submitting a pull request.

---

## ⏱️ Time Estimate

- **Find an Issue:** 10 minutes
- **Make Changes:** 30-60 minutes
- **Submit PR:** 10 minutes

**Total:** ~1-2 hours for your first contribution

---

## 📋 Prerequisites

Before you start, ensure you have:

✅ [Installed UltraCore](installation.md)  
✅ [Completed Quick Start](quick-start.md)  
✅ GitHub account  
✅ Git configured with your name and email

```bash
# Configure Git (if not already done)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## 🔍 Step 1: Find an Issue

### Good First Issues

We label beginner-friendly issues with `good first issue`. These are:
- Well-defined and scoped
- Have clear acceptance criteria
- Include helpful context
- Typically take 1-4 hours

**Find issues:**
- [Good First Issues](https://github.com/TuringDynamics3000/UltraCore/labels/good%20first%20issue)
- [Help Wanted](https://github.com/TuringDynamics3000/UltraCore/labels/help%20wanted)
- [Documentation](https://github.com/TuringDynamics3000/UltraCore/labels/documentation)

### Example Good First Issues

| Issue | Type | Difficulty | Time |
|-------|------|------------|------|
| Add unit tests for `AccountService` | Testing | Easy | 2 hours |
| Fix typo in API documentation | Documentation | Easy | 30 min |
| Add validation for account creation | Feature | Medium | 3 hours |
| Improve error messages | Enhancement | Easy | 1 hour |

### Claim an Issue

Once you find an issue:

1. **Read the issue carefully** - Understand the problem and acceptance criteria
2. **Comment on the issue** - "I'd like to work on this!"
3. **Wait for confirmation** - A maintainer will assign it to you
4. **Ask questions** - If anything is unclear, ask in the issue comments

---

## 🍴 Step 2: Fork and Clone

### Fork the Repository

1. Go to https://github.com/TuringDynamics3000/UltraCore
2. Click the "Fork" button (top right)
3. Wait for GitHub to create your fork

### Clone Your Fork

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/UltraCore.git
cd UltraCore

# Add upstream remote (to sync with main repo)
git remote add upstream https://github.com/TuringDynamics3000/UltraCore.git

# Verify remotes
git remote -v
# Expected:
# origin    https://github.com/YOUR_USERNAME/UltraCore.git (fetch)
# origin    https://github.com/YOUR_USERNAME/UltraCore.git (push)
# upstream  https://github.com/TuringDynamics3000/UltraCore.git (fetch)
# upstream  https://github.com/TuringDynamics3000/UltraCore.git (push)
```

---

## 🌿 Step 3: Create a Branch

Always create a new branch for your changes:

```bash
# Sync with upstream main
git checkout main
git pull upstream main

# Create a new branch
git checkout -b fix/issue-123-account-validation

# Branch naming convention:
# - fix/issue-XXX-description      (for bug fixes)
# - feat/issue-XXX-description     (for new features)
# - docs/issue-XXX-description     (for documentation)
# - test/issue-XXX-description     (for tests)
# - refactor/issue-XXX-description (for refactoring)
```

---

## ✏️ Step 4: Make Your Changes

### Example: Add Validation for Account Creation

Let's say you're working on issue #123: "Add validation for account creation to ensure balance is non-negative".

#### 1. Find the Relevant Code

```bash
# Search for account creation logic
grep -r "create_account" src/

# Expected: src/ultracore/domains/accounting/services/account_service.py
```

#### 2. Make Your Changes

Edit `src/ultracore/domains/accounting/services/account_service.py`:

```python
# Before:
def create_account(self, account_data: AccountCreate) -> Account:
    account = Account(**account_data.dict())
    self.db.add(account)
    self.db.commit()
    return account

# After:
def create_account(self, account_data: AccountCreate) -> Account:
    # Validate balance is non-negative
    if account_data.initial_balance < 0:
        raise ValueError("Initial balance cannot be negative")
    
    account = Account(**account_data.dict())
    self.db.add(account)
    self.db.commit()
    return account
```

#### 3. Add Tests

Create or update `tests/unit/accounting/test_account_service.py`:

```python
def test_create_account_with_negative_balance_raises_error(account_service):
    """Test that creating an account with negative balance raises ValueError."""
    account_data = AccountCreate(
        tenant_id="test-tenant",
        user_id="test-user",
        account_type="savings",
        currency="AUD",
        initial_balance=-100.00  # Negative balance
    )
    
    with pytest.raises(ValueError, match="Initial balance cannot be negative"):
        account_service.create_account(account_data)

def test_create_account_with_zero_balance_succeeds(account_service):
    """Test that creating an account with zero balance succeeds."""
    account_data = AccountCreate(
        tenant_id="test-tenant",
        user_id="test-user",
        account_type="savings",
        currency="AUD",
        initial_balance=0.00  # Zero balance (valid)
    )
    
    account = account_service.create_account(account_data)
    assert account.balance == 0.00
```

#### 4. Update Documentation

Update `docs/api/rest-api.md`:

```markdown
### POST /api/v1/accounts

Create a new account.

**Request Body:**
```json
{
  "tenant_id": "string",
  "user_id": "string",
  "account_type": "savings",
  "currency": "AUD",
  "initial_balance": 1000.00  // Must be >= 0
}
```

**Validation:**
- `initial_balance` must be non-negative (>= 0)
```

---

## ✅ Step 5: Test Your Changes

### Run Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/accounting/test_account_service.py

# Run with coverage
pytest tests/ --cov=src/ultracore --cov-report=html

# Check coverage report
open htmlcov/index.html
```

### Run Linters

```bash
# Format code with Black
black src/ tests/

# Check with Flake8
flake8 src/ tests/

# Type check with mypy
mypy src/
```

### Manual Testing

```bash
# Start UltraCore
python server.py

# Test your changes manually
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant",
    "user_id": "test-user",
    "account_type": "savings",
    "currency": "AUD",
    "initial_balance": -100.00
  }'

# Expected: 400 Bad Request with error message
```

---

## 📝 Step 6: Commit Your Changes

### Stage Your Changes

```bash
# Check what changed
git status

# Stage specific files
git add src/ultracore/domains/accounting/services/account_service.py
git add tests/unit/accounting/test_account_service.py
git add docs/api/rest-api.md

# Or stage all changes
git add .
```

### Write a Good Commit Message

```bash
git commit -m "fix: add validation for negative account balance

- Add validation to ensure initial_balance >= 0
- Raise ValueError with descriptive message
- Add unit tests for negative and zero balance cases
- Update API documentation with validation rules

Fixes #123"
```

**Commit Message Format:**

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `fix:` - Bug fix
- `feat:` - New feature
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `style:` - Code style (formatting)
- `chore:` - Maintenance

**Example:**
```
feat: add investment pod glide path engine

- Implement linear, exponential, and stepped glide paths
- Add automatic risk reduction as target date approaches
- Include rebalancing recommendations
- Add comprehensive unit tests

Closes #456
```

---

## 🚀 Step 7: Push and Create Pull Request

### Push to Your Fork

```bash
# Push your branch to your fork
git push origin fix/issue-123-account-validation
```

### Create Pull Request

1. Go to https://github.com/YOUR_USERNAME/UltraCore
2. Click "Compare & pull request" (GitHub will show this banner)
3. Fill out the PR template:

```markdown
## Description
Adds validation to ensure account initial balance is non-negative.

## Related Issue
Fixes #123

## Changes Made
- Added validation in `AccountService.create_account()`
- Raises `ValueError` if `initial_balance < 0`
- Added unit tests for negative and zero balance cases
- Updated API documentation

## Testing
- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manual testing completed
- [x] Code coverage maintained/improved

## Checklist
- [x] Code follows style guidelines (Black, Flake8)
- [x] Tests added/updated
- [x] Documentation updated
- [x] Commit messages follow convention
- [x] No breaking changes

## Screenshots (if applicable)
N/A
```

4. Click "Create pull request"

---

## 👀 Step 8: Code Review

### What to Expect

- A maintainer will review your PR within 1-3 days
- They may request changes or ask questions
- Be responsive and collaborative

### Responding to Feedback

```bash
# Make requested changes
# ... edit files ...

# Commit changes
git add .
git commit -m "refactor: use custom exception for validation

Address review feedback from @reviewer"

# Push changes
git push origin fix/issue-123-account-validation
```

**The PR will automatically update with your new commits.**

### Common Review Feedback

| Feedback | How to Address |
|----------|----------------|
| "Add more tests" | Write additional test cases |
| "Update documentation" | Add/improve docs |
| "Fix linting errors" | Run `black` and `flake8` |
| "Simplify this logic" | Refactor for clarity |
| "Add type hints" | Add Python type annotations |

---

## ✅ Step 9: Merge and Celebrate! 🎉

Once your PR is approved:

1. A maintainer will merge your PR
2. Your changes will be in the main branch
3. You'll be listed as a contributor!

### After Merge

```bash
# Sync your fork with upstream
git checkout main
git pull upstream main
git push origin main

# Delete your feature branch (optional)
git branch -d fix/issue-123-account-validation
git push origin --delete fix/issue-123-account-validation
```

---

## 🏆 What's Next?

Congratulations on your first contribution! Here's what to do next:

### Continue Contributing

- Find another [Good First Issue](https://github.com/TuringDynamics3000/UltraCore/labels/good%20first%20issue)
- Tackle a [Help Wanted](https://github.com/TuringDynamics3000/UltraCore/labels/help%20wanted) issue
- Improve [Documentation](https://github.com/TuringDynamics3000/UltraCore/labels/documentation)

### Level Up

- [Coding Standards](../development/coding-standards.md) - Write better code
- [Architecture Overview](../architecture/overview.md) - Understand the system
- [Module Documentation](../modules/README.md) - Deep dive into modules

### Get Involved

- Join [GitHub Discussions](https://github.com/TuringDynamics3000/UltraCore/discussions)
- Review other PRs
- Help answer questions in issues

---

## 💡 Tips for Success

### Do's ✅

- **Start small** - Pick simple issues first
- **Ask questions** - No question is too basic
- **Write tests** - Tests are required for all code changes
- **Follow conventions** - Use Black, Flake8, and our style guide
- **Be patient** - Reviews take time
- **Be respectful** - We're all learning

### Don'ts ❌

- **Don't work on unassigned issues** - Always claim an issue first
- **Don't make large PRs** - Keep changes focused and small
- **Don't skip tests** - Tests are mandatory
- **Don't ignore feedback** - Address all review comments
- **Don't force push** - Use regular pushes after initial PR

---

## 🆘 Need Help?

### Stuck on Something?

- **Comment on the issue** - Ask for clarification
- **Join Discussions** - [GitHub Discussions](https://github.com/TuringDynamics3000/UltraCore/discussions)
- **Check docs** - [Development Guide](../development/setup.md)
- **Email us** - michael@turingdynamics.ai

### Common Issues

| Problem | Solution |
|---------|----------|
| Tests failing | Run `pytest tests/` locally first |
| Linting errors | Run `black src/ tests/` |
| Merge conflicts | Sync with upstream: `git pull upstream main` |
| Can't find code | Use `grep -r "search_term" src/` |

---

## 📚 Additional Resources

- [Contributing Guidelines](../development/contributing.md)
- [Coding Standards](../development/coding-standards.md)
- [Testing Guide](../development/testing.md)
- [Git Workflow](../development/git-workflow.md)

---

**Thank you for contributing to UltraCore!** 🙏

Every contribution, no matter how small, makes UltraCore better. We appreciate your time and effort!
