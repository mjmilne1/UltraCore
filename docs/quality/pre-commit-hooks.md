# 🪝 Pre-commit Hooks

Automated code quality checks that run before every commit.

---

## 📚 Quick Links

- **[Overview](#overview)** - What are pre-commit hooks?
- **[Installation](#installation)** - Setup guide
- **[Hooks](#hooks)** - Available hooks
- **[Configuration](#configuration)** - Customization
- **[Troubleshooting](#troubleshooting)** - Common issues

---

## 🎯 Overview

Pre-commit hooks are automated checks that run **before you commit code**. They catch issues early, enforce coding standards, and prevent broken code from entering the repository.

### Benefits

**Catch Issues Early:**
- Find bugs before they reach CI
- Fix formatting automatically
- Detect security issues
- Prevent large file commits

**Enforce Standards:**
- Consistent code formatting
- Import organization
- Type safety
- Commit message format

**Save Time:**
- Faster feedback loop
- Fewer CI failures
- Less code review time
- Automatic fixes

---

## 🚀 Installation

### Prerequisites

```bash
# Install pre-commit
pip install pre-commit

# Or with pipx (recommended)
pipx install pre-commit
```

### Setup

```bash
# Navigate to repository
cd /path/to/ultracore

# Install hooks
pre-commit install

# Install commit-msg hook (for commit message validation)
pre-commit install --hook-type commit-msg
```

### Verify Installation

```bash
# Run hooks on all files
pre-commit run --all-files
```

---

## 🔧 Hooks

UltraCore uses the following pre-commit hooks:

### 1. Code Formatting

#### Black

**Purpose:** Automatic Python code formatting

**What it does:**
- Formats Python code consistently
- Enforces 100-character line length
- Fixes formatting issues automatically

**Configuration:**
```yaml
- repo: https://github.com/psf/black
  rev: 23.11.0
  hooks:
    - id: black
      args: ['--line-length=100']
```

**Example:**
```python
# Before
def my_function(arg1,arg2,arg3):
    return arg1+arg2+arg3

# After
def my_function(arg1, arg2, arg3):
    return arg1 + arg2 + arg3
```

---

#### isort

**Purpose:** Sort and organize imports

**What it does:**
- Sorts imports alphabetically
- Groups imports by category
- Removes duplicate imports

**Configuration:**
```yaml
- repo: https://github.com/PyCQA/isort
  rev: 5.12.0
  hooks:
    - id: isort
      args: ['--profile', 'black', '--line-length', '100']
```

**Example:**
```python
# Before
from ultracore.domains.accounts import Account
import os
from ultracore.infrastructure.event_store import EventStore
import sys

# After
import os
import sys

from ultracore.domains.accounts import Account
from ultracore.infrastructure.event_store import EventStore
```

---

### 2. Linting

#### Ruff

**Purpose:** Fast Python linter

**What it does:**
- Checks for code quality issues
- Finds potential bugs
- Enforces best practices
- Auto-fixes many issues

**Configuration:**
```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.1.6
  hooks:
    - id: ruff
      args: ['--fix', '--exit-non-zero-on-fix']
```

**Checks:**
- Unused imports
- Undefined variables
- Syntax errors
- Code complexity
- Best practice violations

---

### 3. Type Checking

#### MyPy

**Purpose:** Static type checking

**What it does:**
- Verifies type hints
- Catches type errors
- Ensures type safety

**Configuration:**
```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.7.1
  hooks:
    - id: mypy
      args: ['--ignore-missing-imports']
```

**Example:**
```python
# Type error caught by MyPy
def add(a: int, b: int) -> int:
    return a + b

result: str = add(1, 2)  # Error: int assigned to str
```

---

### 4. Security

#### Bandit

**Purpose:** Security vulnerability scanner

**What it does:**
- Detects security issues
- Finds common vulnerabilities
- Checks for unsafe patterns

**Configuration:**
```yaml
- repo: https://github.com/PyCQA/bandit
  rev: 1.7.5
  hooks:
    - id: bandit
      args: ['-c', 'pyproject.toml']
```

**Checks:**
- SQL injection risks
- Hardcoded passwords
- Insecure random usage
- Unsafe YAML loading
- Shell injection risks

---

### 5. File Validation

#### Standard Hooks

**Purpose:** Basic file validation

**What it does:**
- Validates YAML syntax
- Fixes end-of-file
- Removes trailing whitespace
- Checks file sizes
- Detects merge conflicts
- Detects private keys

**Configuration:**
```yaml
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.5.0
  hooks:
    - id: check-yaml
    - id: end-of-file-fixer
    - id: trailing-whitespace
    - id: check-added-large-files
      args: ['--maxkb=1000']
    - id: check-merge-conflict
    - id: detect-private-key
```

---

### 6. Dockerfile Linting

#### Hadolint

**Purpose:** Dockerfile best practices

**What it does:**
- Checks Dockerfile syntax
- Enforces best practices
- Detects common mistakes

**Configuration:**
```yaml
- repo: https://github.com/hadolint/hadolint
  rev: v2.12.0
  hooks:
    - id: hadolint-docker
```

---

### 7. Commit Message Validation

#### Conventional Commits

**Purpose:** Enforce commit message format

**What it does:**
- Validates commit message structure
- Enforces conventional commits format
- Ensures consistent commit history

**Configuration:**
```yaml
- repo: https://github.com/compilerla/conventional-pre-commit
  rev: v3.0.0
  hooks:
    - id: conventional-pre-commit
      stages: [commit-msg]
```

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
# Good
feat(accounts): add account creation endpoint
fix(payments): resolve NPP timeout issue
docs(api): update REST API documentation

# Bad
Added stuff
Fixed bug
Update
```

---

## ⚙️ Configuration

### Custom Configuration

Create `.pre-commit-config.yaml` in repository root:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        args: ['--line-length=100']
```

### Skip Hooks

**Skip specific hook:**
```bash
SKIP=mypy git commit -m "feat: add feature"
```

**Skip all hooks:**
```bash
git commit --no-verify -m "feat: add feature"
```

⚠️ **Warning:** Only skip hooks when absolutely necessary!

### Update Hooks

```bash
# Update all hooks to latest versions
pre-commit autoupdate
```

---

## 🔄 Workflow

### Normal Workflow

```bash
# 1. Make changes
vim src/ultracore/domains/accounts/models/account.py

# 2. Stage changes
git add src/ultracore/domains/accounts/models/account.py

# 3. Commit (hooks run automatically)
git commit -m "feat(accounts): add account closure method"

# Hooks run:
# ✓ Black (formatting)
# ✓ isort (imports)
# ✓ Ruff (linting)
# ✓ MyPy (type checking)
# ✓ Bandit (security)
# ✓ File validation
# ✓ Commit message validation

# 4. Push
git push
```

### When Hooks Fail

```bash
# Hooks run and find issues
git commit -m "feat: add feature"

# Output:
# black....................................................................Failed
# - hook id: black
# - files were modified by this hook
# 
# reformatted src/ultracore/domains/accounts/models/account.py

# 1. Review changes made by hooks
git diff

# 2. Stage fixed files
git add src/ultracore/domains/accounts/models/account.py

# 3. Commit again
git commit -m "feat: add feature"
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Hooks Not Running

**Symptoms:**
- Commits succeed without running hooks
- No hook output

**Solutions:**
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install
pre-commit install --hook-type commit-msg

# Verify installation
ls -la .git/hooks/
```

---

#### 2. MyPy Errors

**Symptoms:**
- Type checking fails
- Missing type stubs

**Solutions:**
```bash
# Install type stubs
pip install types-requests types-redis types-PyYAML

# Or ignore missing imports
# Add to pyproject.toml:
[tool.mypy]
ignore_missing_imports = true
```

---

#### 3. Slow Hooks

**Symptoms:**
- Hooks take too long
- Commit is slow

**Solutions:**
```bash
# Run hooks only on changed files (default)
pre-commit run

# Skip slow hooks temporarily
SKIP=mypy git commit -m "feat: add feature"

# Update to faster versions
pre-commit autoupdate
```

---

#### 4. Bandit False Positives

**Symptoms:**
- Security warnings for safe code
- Test code flagged

**Solutions:**
```python
# Ignore specific issue
password = "test"  # nosec B105

# Or configure in pyproject.toml:
[tool.bandit]
exclude_dirs = ["tests/"]
skips = ["B101"]  # Skip assert warnings in tests
```

---

#### 5. Commit Message Rejected

**Symptoms:**
- Commit message validation fails

**Solutions:**
```bash
# Use conventional commit format
git commit -m "feat(accounts): add account creation"

# Valid types:
# feat, fix, docs, style, refactor, test, chore
```

---

## 📋 Best Practices

### 1. Run Hooks Before Committing

```bash
# Test hooks before committing
pre-commit run --all-files
```

### 2. Keep Hooks Updated

```bash
# Update monthly
pre-commit autoupdate
```

### 3. Don't Skip Hooks

- Only skip when absolutely necessary
- Document why you're skipping
- Fix issues properly instead

### 4. Configure Properly

- Match hook config with CI
- Use same tool versions
- Keep configuration in sync

### 5. Review Hook Changes

- Check what hooks changed
- Understand auto-fixes
- Don't blindly accept changes

---

## 🎓 Learning Resources

### Documentation

- **[Pre-commit Official Docs](https://pre-commit.com/)** - Complete guide
- **[Black Documentation](https://black.readthedocs.io/)** - Formatting rules
- **[Ruff Documentation](https://docs.astral.sh/ruff/)** - Linting rules
- **[MyPy Documentation](https://mypy.readthedocs.io/)** - Type checking
- **[Conventional Commits](https://www.conventionalcommits.org/)** - Commit format

### Tools

- **Black** - Code formatter
- **isort** - Import sorter
- **Ruff** - Fast linter
- **MyPy** - Type checker
- **Bandit** - Security scanner

---

## 📚 Additional Resources

- **[CI/CD Pipeline](ci-cd-pipeline.md)** - Continuous integration
- **[Code Review Guidelines](code-review-guidelines.md)** - Review process
- **[Testing Standards](testing-standards.md)** - Test requirements
- **[Quality Metrics](quality-metrics.md)** - Measuring quality

---

**Last Updated:** November 14, 2024
