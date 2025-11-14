# 👀 Code Review Guidelines

Comprehensive guide to conducting effective code reviews in UltraCore.

---

## 📚 Quick Links

- **[Overview](#overview)** - Why code reviews matter
- **[Review Process](#review-process)** - Step-by-step workflow
- **[Review Checklist](#review-checklist)** - What to check
- **[Best Practices](#best-practices)** - Effective reviews
- **[Common Issues](#common-issues)** - What to look for
- **[Tools](#tools)** - Review tools

---

## 🎯 Overview

Code reviews are a critical quality gate ensuring code quality, knowledge sharing, and team collaboration.

### Goals

**Quality Assurance:**
- Catch bugs before production
- Ensure code meets standards
- Verify test coverage
- Check security issues

**Knowledge Sharing:**
- Share domain knowledge
- Learn new techniques
- Understand codebase
- Mentor team members

**Collaboration:**
- Build team culture
- Improve communication
- Align on standards
- Foster ownership

---

## 🔄 Review Process

### 1. Author Preparation

**Before Creating PR:**

```bash
# 1. Ensure all tests pass
pytest tests/

# 2. Run pre-commit hooks
pre-commit run --all-files

# 3. Update documentation
# - Update README if needed
# - Add/update docstrings
# - Update CHANGELOG

# 4. Self-review changes
git diff main...feature-branch

# 5. Create PR with description
gh pr create --title "feat(accounts): add account closure" \
  --body "Description of changes..."
```

**PR Description Template:**

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
- [ ] No breaking changes (or documented)

## Related Issues
Closes #123
```

---

### 2. Reviewer Assignment

**Auto-Assignment:**
- GitHub CODEOWNERS file
- Round-robin assignment
- Team-based assignment

**Manual Assignment:**
- Domain experts
- Feature stakeholders
- Security reviewers

**CODEOWNERS Example:**

```
# Global owners
* @ultracore/core-team

# Domain owners
/src/ultracore/domains/accounts/ @ultracore/accounts-team
/src/ultracore/domains/wealth/ @ultracore/wealth-team
/src/ultracore/domains/lending/ @ultracore/lending-team

# Infrastructure
/src/ultracore/infrastructure/ @ultracore/platform-team
/.github/ @ultracore/devops-team

# Security
/src/ultracore/security/ @ultracore/security-team
```

---

### 3. Review Workflow

#### Initial Review (30 minutes)

**1. Understand Context (5 min)**
- Read PR description
- Review linked issues
- Understand business context

**2. High-Level Review (10 min)**
- Check architecture
- Verify approach
- Review design decisions

**3. Detailed Review (15 min)**
- Review code changes
- Check tests
- Verify documentation

#### Provide Feedback

**Comment Types:**

**🔴 Blocking (Must Fix):**
```markdown
**[BLOCKING]** This will cause a security vulnerability.

Current code allows SQL injection. Use parameterized queries instead:

```python
# Bad
query = f"SELECT * FROM users WHERE id = {user_id}"

# Good
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```
```

**🟡 Suggestion (Should Fix):**
```markdown
**[SUGGESTION]** Consider extracting this into a separate function for better readability.

```python
def calculate_interest(balance: Decimal, rate: Decimal) -> Decimal:
    return balance * rate / 100
```
```

**💡 Nitpick (Optional):**
```markdown
**[NITPICK]** Minor style preference: consider using f-string here.

```python
# Current
message = "Account {} created".format(account_id)

# Suggestion
message = f"Account {account_id} created"
```
```

**✅ Praise (Positive Feedback):**
```markdown
**[PRAISE]** Excellent use of the strategy pattern here! This makes the code much more maintainable.
```

---

### 4. Author Response

**Address Feedback:**

```markdown
## Reviewer Feedback Response

### @reviewer1 comments

**Comment 1: SQL injection risk**
✅ Fixed - Switched to parameterized queries

**Comment 2: Extract function**
✅ Done - Created `calculate_interest()` function

**Comment 3: Use f-string**
✅ Updated - Changed to f-string

**Comment 4: Add docstring**
❌ Won't fix - Function is self-explanatory and private
```

---

### 5. Approval & Merge

**Approval Criteria:**
- All blocking comments resolved
- All CI checks passing
- Required approvals received
- No unresolved conversations

**Merge Options:**
- **Squash and merge** - Single commit (default)
- **Rebase and merge** - Linear history
- **Merge commit** - Preserve branch history

---

## ✅ Review Checklist

### Code Quality

- [ ] **Code is readable and maintainable**
  - Clear variable names
  - Logical function structure
  - Appropriate comments
  - Consistent style

- [ ] **Follows coding standards**
  - Passes linting (Ruff)
  - Formatted correctly (Black)
  - Type hints present (MyPy)
  - Docstrings for public APIs

- [ ] **No code smells**
  - No duplicated code
  - No overly complex functions
  - No magic numbers
  - No dead code

---

### Functionality

- [ ] **Implements requirements correctly**
  - Matches specification
  - Handles edge cases
  - Validates input
  - Returns correct output

- [ ] **Error handling is appropriate**
  - Catches expected errors
  - Provides useful error messages
  - Logs errors properly
  - Doesn't swallow exceptions

- [ ] **Performance is acceptable**
  - No obvious bottlenecks
  - Efficient algorithms
  - Appropriate caching
  - Database queries optimized

---

### Testing

- [ ] **Tests are comprehensive**
  - Unit tests for new code
  - Integration tests for workflows
  - Edge cases covered
  - Error cases tested

- [ ] **Tests are well-written**
  - Clear test names
  - Arrange-Act-Assert pattern
  - No flaky tests
  - Fast execution

- [ ] **Test coverage is adequate**
  - Coverage ≥ 80% for new code
  - Critical paths covered
  - No untested branches

---

### Security

- [ ] **No security vulnerabilities**
  - No SQL injection
  - No XSS vulnerabilities
  - No hardcoded secrets
  - Input validation present

- [ ] **Authentication & authorization**
  - Proper authentication checks
  - Authorization enforced
  - Permissions verified
  - Audit logging present

- [ ] **Data protection**
  - Sensitive data encrypted
  - PII handled properly
  - Secure communication
  - Data validation

---

### Documentation

- [ ] **Code is documented**
  - Public APIs have docstrings
  - Complex logic explained
  - TODOs tracked
  - Examples provided

- [ ] **External documentation updated**
  - README updated
  - API docs updated
  - Architecture docs updated
  - CHANGELOG updated

---

### Architecture

- [ ] **Follows system architecture**
  - Domain-driven design
  - Event sourcing patterns
  - Data mesh principles
  - Clean architecture

- [ ] **Proper separation of concerns**
  - Single responsibility
  - Loose coupling
  - High cohesion
  - Dependency injection

- [ ] **Scalability considered**
  - Can handle load
  - Horizontally scalable
  - Resource efficient
  - Caching strategy

---

### Database

- [ ] **Schema changes are safe**
  - Backward compatible
  - Migration tested
  - Rollback plan exists
  - Indexes added

- [ ] **Queries are optimized**
  - No N+1 queries
  - Proper indexes used
  - Batch operations
  - Connection pooling

---

### Event Sourcing

- [ ] **Events are well-designed**
  - Immutable
  - Versioned
  - Self-contained
  - Backward compatible

- [ ] **Event handling is correct**
  - Idempotent
  - Ordered processing
  - Error handling
  - Replay support

---

## 🎯 Best Practices

### For Reviewers

#### 1. Be Respectful

**Do:**
- Focus on code, not person
- Explain reasoning
- Suggest alternatives
- Acknowledge good work

**Don't:**
- Use harsh language
- Make personal attacks
- Be dismissive
- Assume intent

**Examples:**

```markdown
# Good
"This approach might cause performance issues with large datasets. 
Consider using pagination instead."

# Bad
"This is terrible. You should know better."
```

---

#### 2. Be Constructive

**Do:**
- Provide specific feedback
- Suggest solutions
- Share knowledge
- Ask questions

**Don't:**
- Just point out problems
- Be vague
- Assume knowledge
- Be condescending

**Examples:**

```markdown
# Good
"The error handling here could be improved. Consider catching 
specific exceptions and providing actionable error messages:

```python
try:
    account = get_account(account_id)
except AccountNotFoundError:
    raise HTTPException(404, f"Account {account_id} not found")
```
"

# Bad
"Error handling is wrong."
```

---

#### 3. Be Thorough

**Do:**
- Review all changes
- Check tests
- Verify documentation
- Test locally if needed

**Don't:**
- Rubber stamp
- Skip tests
- Ignore documentation
- Rush reviews

---

#### 4. Be Timely

**Do:**
- Review within 24 hours
- Prioritize blocking PRs
- Set aside review time
- Communicate delays

**Don't:**
- Leave PRs hanging
- Review when rushed
- Delay without reason

---

### For Authors

#### 1. Keep PRs Small

**Target:**
- < 400 lines changed
- Single responsibility
- One feature/fix
- Easy to review

**Benefits:**
- Faster reviews
- Better feedback
- Easier to understand
- Less risky

---

#### 2. Write Good Descriptions

**Include:**
- What changed
- Why it changed
- How to test
- Related issues

**Example:**

```markdown
## Description
Add account closure functionality to allow customers to close accounts.

## Why
Customers need ability to close unused accounts per compliance requirements.

## Changes
- Added `close_account()` method to Account aggregate
- Added `AccountClosedEvent` 
- Added API endpoint `/accounts/{id}/close`
- Added validation for closure eligibility

## Testing
1. Create test account
2. POST to `/accounts/{id}/close`
3. Verify account status is 'closed'
4. Verify AccountClosedEvent published

## Related
Closes #456
```

---

#### 3. Respond to Feedback

**Do:**
- Address all comments
- Explain decisions
- Ask for clarification
- Thank reviewers

**Don't:**
- Ignore feedback
- Be defensive
- Argue unnecessarily
- Take it personally

---

#### 4. Self-Review First

**Before Requesting Review:**
- Review your own changes
- Run tests locally
- Check documentation
- Fix obvious issues

---

## 🔍 Common Issues

### 1. Logic Errors

**Look for:**
- Off-by-one errors
- Incorrect conditions
- Missing edge cases
- Wrong calculations

**Example:**

```python
# Bug: Should be <= not <
if balance < minimum_balance:  # ❌
    charge_fee()

# Fixed
if balance <= minimum_balance:  # ✅
    charge_fee()
```

---

### 2. Security Issues

**Look for:**
- SQL injection
- XSS vulnerabilities
- Hardcoded secrets
- Missing authentication

**Example:**

```python
# Vulnerable to SQL injection
query = f"SELECT * FROM accounts WHERE id = {account_id}"  # ❌

# Safe
query = "SELECT * FROM accounts WHERE id = %s"  # ✅
cursor.execute(query, (account_id,))
```

---

### 3. Performance Issues

**Look for:**
- N+1 queries
- Missing indexes
- Inefficient algorithms
- Memory leaks

**Example:**

```python
# N+1 query problem
for account in accounts:  # ❌
    balance = get_balance(account.id)  # Database query in loop

# Fixed with batch query
account_ids = [a.id for a in accounts]  # ✅
balances = get_balances(account_ids)  # Single query
```

---

### 4. Error Handling

**Look for:**
- Swallowed exceptions
- Generic error messages
- Missing error handling
- Incorrect exception types

**Example:**

```python
# Swallows all exceptions
try:  # ❌
    process_payment()
except:
    pass

# Proper error handling
try:  # ✅
    process_payment()
except PaymentError as e:
    logger.error(f"Payment failed: {e}")
    raise
```

---

### 5. Testing Issues

**Look for:**
- Missing tests
- Flaky tests
- Poor test coverage
- Unclear test names

**Example:**

```python
# Bad test name
def test_1():  # ❌
    assert add(1, 2) == 3

# Good test name
def test_add_two_positive_numbers_returns_sum():  # ✅
    assert add(1, 2) == 3
```

---

## 🛠️ Tools

### GitHub Features

**Review Comments:**
- Line comments
- File comments
- General comments
- Suggested changes

**Review Status:**
- Approve
- Request changes
- Comment only

**Draft PRs:**
- Work in progress
- Early feedback
- Not ready to merge

---

### IDE Integration

**VS Code:**
- GitHub Pull Requests extension
- Review in editor
- Inline comments

**PyCharm:**
- Built-in GitHub integration
- Code review tools
- Diff viewer

---

### CLI Tools

**GitHub CLI:**

```bash
# List PRs
gh pr list

# View PR
gh pr view 123

# Review PR
gh pr review 123

# Approve PR
gh pr review 123 --approve

# Request changes
gh pr review 123 --request-changes --body "Please fix..."
```

---

## 📊 Metrics

### Review Effectiveness

**Track:**
- Time to first review
- Time to merge
- Review iterations
- Defects found
- Defects escaped

**Targets:**
- First review: < 24 hours
- Time to merge: < 3 days
- Iterations: < 3
- Defect detection: > 80%

---

## 📚 Additional Resources

- **[CI/CD Pipeline](ci-cd-pipeline.md)** - Automated checks
- **[Pre-commit Hooks](pre-commit-hooks.md)** - Local quality gates
- **[Testing Standards](testing-standards.md)** - Test requirements
- **[Quality Metrics](quality-metrics.md)** - Measuring quality

---

**Last Updated:** November 14, 2024
