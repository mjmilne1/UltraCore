# 📊 Quality Metrics

Comprehensive guide to measuring and monitoring code quality in UltraCore.

---

## 📚 Quick Links

- **[Overview](#overview)** - Why metrics matter
- **[Code Quality Metrics](#code-quality-metrics)** - Code health
- **[Testing Metrics](#testing-metrics)** - Test coverage
- **[Process Metrics](#process-metrics)** - Development flow
- **[Performance Metrics](#performance-metrics)** - System performance
- **[Dashboards](#dashboards)** - Visualization

---

## 🎯 Overview

Quality metrics provide objective measurements of code health, development process, and system performance.

### Why Metrics Matter

**Visibility:**
- Track quality trends
- Identify issues early
- Measure improvements
- Make data-driven decisions

**Accountability:**
- Set quality standards
- Monitor compliance
- Drive improvements
- Celebrate wins

**Continuous Improvement:**
- Identify bottlenecks
- Optimize processes
- Reduce technical debt
- Improve velocity

---

## 📏 Code Quality Metrics

### 1. Code Coverage

**Definition:** Percentage of code executed by tests

**Targets:**
- **Unit Test Coverage:** ≥ 80%
- **Integration Test Coverage:** ≥ 70%
- **Overall Coverage:** ≥ 75%

**Measurement:**

```bash
# Generate coverage report
pytest --cov=src/ultracore --cov-report=html

# View report
open htmlcov/index.html
```

**Interpretation:**

| Coverage | Status | Action |
|----------|--------|--------|
| ≥ 80% | ✅ Excellent | Maintain |
| 70-79% | ⚠️ Good | Improve |
| 60-69% | ⚠️ Fair | Priority improvement |
| < 60% | ❌ Poor | Immediate action |

**Dashboard:**

```
Code Coverage Trend
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
100% ┤                              ╭─
 90% ┤                         ╭────╯
 80% ┤                    ╭────╯
 70% ┤               ╭────╯
 60% ┤          ╭────╯
 50% ┤     ╭────╯
 40% ┤╭────╯
     └────────────────────────────────────
     Jan  Feb  Mar  Apr  May  Jun  Jul
```

---

### 2. Code Complexity

**Definition:** Cyclomatic complexity of code

**Targets:**
- **Function Complexity:** ≤ 10
- **Class Complexity:** ≤ 50
- **Module Complexity:** ≤ 100

**Measurement:**

```bash
# Install radon
pip install radon

# Check complexity
radon cc src/ultracore -a -s

# Check maintainability index
radon mi src/ultracore -s
```

**Interpretation:**

| Complexity | Grade | Status | Action |
|------------|-------|--------|--------|
| 1-5 | A | ✅ Simple | Maintain |
| 6-10 | B | ✅ Manageable | Monitor |
| 11-20 | C | ⚠️ Complex | Refactor soon |
| 21-50 | D | ⚠️ Very complex | Refactor |
| > 50 | F | ❌ Unmaintainable | Immediate refactor |

---

### 3. Code Duplication

**Definition:** Percentage of duplicated code

**Target:** < 5% duplication

**Measurement:**

```bash
# Install pylint
pip install pylint

# Check duplication
pylint --disable=all --enable=duplicate-code src/ultracore
```

**Interpretation:**

| Duplication | Status | Action |
|-------------|--------|--------|
| < 3% | ✅ Excellent | Maintain |
| 3-5% | ✅ Good | Monitor |
| 5-10% | ⚠️ Fair | Refactor |
| > 10% | ❌ Poor | Immediate refactor |

---

### 4. Code Smells

**Definition:** Indicators of potential issues

**Common Smells:**
- Long functions (> 50 lines)
- Long parameter lists (> 5 parameters)
- Deep nesting (> 4 levels)
- God classes (> 500 lines)
- Dead code

**Measurement:**

```bash
# Use SonarQube or similar
sonar-scanner \
  -Dsonar.projectKey=ultracore \
  -Dsonar.sources=src \
  -Dsonar.host.url=http://localhost:9000
```

---

### 5. Technical Debt

**Definition:** Cost of additional work due to shortcuts

**Measurement:**

```bash
# Technical debt ratio
Technical Debt Ratio = (Remediation Cost / Development Cost) × 100

# Target: < 5%
```

**Tracking:**

```python
# Track in code with TODO comments
# TODO(tech-debt): Refactor this function [Effort: 4h] [Priority: High]
def legacy_function():
    pass
```

---

## 🧪 Testing Metrics

### 1. Test Pass Rate

**Definition:** Percentage of tests passing

**Target:** 100% pass rate

**Measurement:**

```bash
# Run tests and capture results
pytest --junitxml=test-results.xml

# Calculate pass rate
Pass Rate = (Passed Tests / Total Tests) × 100
```

**Interpretation:**

| Pass Rate | Status | Action |
|-----------|--------|--------|
| 100% | ✅ Excellent | Maintain |
| 95-99% | ⚠️ Good | Fix failing tests |
| 90-94% | ⚠️ Fair | Priority fixes |
| < 90% | ❌ Poor | Stop development |

---

### 2. Test Execution Time

**Definition:** Time to run test suite

**Targets:**
- **Unit Tests:** < 5 minutes
- **Integration Tests:** < 10 minutes
- **E2E Tests:** < 30 minutes

**Measurement:**

```bash
# Run tests with timing
pytest --durations=10

# Output:
# slowest 10 durations
# 2.50s call     tests/integration/test_account_workflow.py::test_create_account
# 1.20s call     tests/integration/test_payment_workflow.py::test_process_payment
```

**Optimization:**
- Parallelize tests
- Use test result caching
- Optimize slow tests
- Split large test suites

---

### 3. Test Flakiness

**Definition:** Tests that pass/fail randomly

**Target:** 0% flaky tests

**Measurement:**

```bash
# Run tests multiple times
for i in {1..10}; do pytest; done

# Track failures
Flakiness Rate = (Flaky Tests / Total Tests) × 100
```

**Common Causes:**
- Race conditions
- External dependencies
- Time-dependent code
- Shared state

---

### 4. Test Coverage Trend

**Definition:** Coverage change over time

**Target:** Increasing or stable

**Measurement:**

```bash
# Track coverage over time
Date,Coverage
2024-01-01,75.5
2024-02-01,76.2
2024-03-01,78.1
2024-04-01,79.5
```

---

## 🔄 Process Metrics

### 1. Build Success Rate

**Definition:** Percentage of successful builds

**Target:** ≥ 95%

**Measurement:**

```bash
# From CI/CD system
Build Success Rate = (Successful Builds / Total Builds) × 100
```

**Interpretation:**

| Success Rate | Status | Action |
|--------------|--------|--------|
| ≥ 95% | ✅ Excellent | Maintain |
| 90-94% | ⚠️ Good | Investigate failures |
| 85-89% | ⚠️ Fair | Fix build issues |
| < 85% | ❌ Poor | Stop and fix |

---

### 2. Deployment Frequency

**Definition:** How often code is deployed

**Target:** Multiple times per day (for mature teams)

**Measurement:**

```bash
# Count deployments
Deployments per Day = Total Deployments / Days
```

**Industry Benchmarks:**

| Frequency | Level | Description |
|-----------|-------|-------------|
| Multiple/day | Elite | Continuous deployment |
| Weekly | High | Regular releases |
| Monthly | Medium | Scheduled releases |
| Quarterly | Low | Infrequent releases |

---

### 3. Lead Time for Changes

**Definition:** Time from commit to production

**Target:** < 1 day

**Measurement:**

```bash
# Track time
Lead Time = Production Deploy Time - Commit Time
```

**Breakdown:**
- Code review: < 4 hours
- CI pipeline: < 30 minutes
- Deployment: < 30 minutes
- Verification: < 1 hour

---

### 4. Mean Time to Recovery (MTTR)

**Definition:** Average time to recover from failure

**Target:** < 1 hour

**Measurement:**

```bash
# Track incidents
MTTR = Total Recovery Time / Number of Incidents
```

**Improvement Strategies:**
- Automated rollback
- Feature flags
- Monitoring alerts
- Runbooks

---

### 5. Change Failure Rate

**Definition:** Percentage of deployments causing failure

**Target:** < 15%

**Measurement:**

```bash
# Track failures
Change Failure Rate = (Failed Deployments / Total Deployments) × 100
```

**Interpretation:**

| Failure Rate | Status | Action |
|--------------|--------|--------|
| < 5% | ✅ Elite | Maintain |
| 5-15% | ✅ High | Good |
| 15-30% | ⚠️ Medium | Improve testing |
| > 30% | ❌ Low | Major improvements needed |

---

### 6. Code Review Time

**Definition:** Time to complete code review

**Target:** < 24 hours

**Measurement:**

```bash
# From GitHub/GitLab
Review Time = Approval Time - PR Creation Time
```

**Breakdown:**
- Time to first review: < 4 hours
- Time to approval: < 24 hours
- Number of iterations: < 3

---

## ⚡ Performance Metrics

### 1. API Response Time

**Definition:** Time to respond to API requests

**Targets:**
- **P50:** < 100ms
- **P95:** < 500ms
- **P99:** < 1000ms

**Measurement:**

```python
# Add timing middleware
import time
from fastapi import Request

@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

---

### 2. Database Query Performance

**Definition:** Time to execute database queries

**Target:** < 100ms per query

**Measurement:**

```python
# Log slow queries
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 0.1:  # Log queries > 100ms
        logging.warning(f"Slow query ({total:.2f}s): {statement}")
```

---

### 3. Memory Usage

**Definition:** Application memory consumption

**Target:** < 80% of available memory

**Measurement:**

```python
import psutil

def get_memory_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        'rss': memory_info.rss / 1024 / 1024,  # MB
        'vms': memory_info.vms / 1024 / 1024,  # MB
        'percent': process.memory_percent()
    }
```

---

### 4. Error Rate

**Definition:** Percentage of requests resulting in errors

**Target:** < 0.1%

**Measurement:**

```bash
# From logs/monitoring
Error Rate = (Error Requests / Total Requests) × 100
```

**Breakdown by Type:**
- 4xx errors: Client errors
- 5xx errors: Server errors
- Timeouts: Performance issues

---

## 📈 Dashboards

### Quality Dashboard

```
┌─────────────────────────────────────────────────────────┐
│                  UltraCore Quality Metrics              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Code Coverage                           Test Pass Rate │
│  ████████████████░░░░ 82%               ████████████ 100%│
│  Target: 80% ✅                          Target: 100% ✅ │
│                                                         │
│  Code Complexity                         Build Success  │
│  █████████░░░░░░░░░░ 8.2                ███████████░ 96% │
│  Target: < 10 ✅                         Target: 95% ✅  │
│                                                         │
│  Technical Debt                          Deployment Freq│
│  ██░░░░░░░░░░░░░░░░ 3.5%                12 per week     │
│  Target: < 5% ✅                         Target: Daily   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### Performance Dashboard

```
┌─────────────────────────────────────────────────────────┐
│               UltraCore Performance Metrics             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  API Response Time (P95)                Error Rate      │
│  ████████░░░░░░░░░░░ 420ms              ░░░░░░░░░░░ 0.05%│
│  Target: < 500ms ✅                      Target: < 0.1% ✅│
│                                                         │
│  Database Query Time                    Memory Usage    │
│  ██████░░░░░░░░░░░░░ 85ms               ████████░░░ 65%  │
│  Target: < 100ms ✅                      Target: < 80% ✅ │
│                                                         │
│  Throughput                             CPU Usage       │
│  1,250 req/s                            ██████░░░░ 45%   │
│  Target: > 1000 ✅                       Target: < 70% ✅ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### Process Dashboard

```
┌─────────────────────────────────────────────────────────┐
│                UltraCore Process Metrics                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Lead Time                              MTTR            │
│  ████████░░░░░░░░░░░ 18h                ██░░░░░░░░ 45min │
│  Target: < 24h ✅                        Target: < 1h ✅  │
│                                                         │
│  Change Failure Rate                    Code Review Time│
│  ███░░░░░░░░░░░░░░░ 8%                  ████████░░░ 16h  │
│  Target: < 15% ✅                        Target: < 24h ✅ │
│                                                         │
│  Deployment Frequency                   PR Merge Rate   │
│  12 per week                            ████████░░░ 85%  │
│  Target: Daily ⚠️                        Target: > 80% ✅ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tools

### Code Quality Tools

**SonarQube:**
- Code quality analysis
- Technical debt tracking
- Security vulnerability detection
- Code smell detection

**CodeClimate:**
- Maintainability scoring
- Test coverage tracking
- Duplication detection
- Trend analysis

---

### Monitoring Tools

**Prometheus + Grafana:**
- Metrics collection
- Custom dashboards
- Alerting
- Time-series data

**DataDog:**
- APM monitoring
- Log aggregation
- Infrastructure monitoring
- Custom metrics

---

### CI/CD Metrics

**GitHub Actions:**
- Build metrics
- Test results
- Deployment tracking
- Workflow analytics

---

## 📋 Reporting

### Weekly Quality Report

```markdown
# UltraCore Quality Report - Week 45

## Summary
- Overall Status: ✅ Healthy
- Code Coverage: 82% (+2%)
- Test Pass Rate: 100%
- Build Success: 96%

## Highlights
- Improved code coverage by 2%
- Reduced average complexity from 9.1 to 8.2
- Zero flaky tests this week
- Deployment frequency increased to 12/week

## Areas for Improvement
- Increase deployment frequency to daily
- Reduce lead time from 18h to < 12h
- Address 3 high-complexity functions

## Action Items
1. Refactor high-complexity functions
2. Automate deployment process
3. Add integration tests for new features
```

---

### Monthly Trend Report

```markdown
# UltraCore Quality Trends - November 2024

## Code Quality Trends
- Coverage: 75% → 82% (+7%)
- Complexity: 9.5 → 8.2 (-1.3)
- Technical Debt: 4.2% → 3.5% (-0.7%)

## Process Trends
- Lead Time: 24h → 18h (-6h)
- MTTR: 1.2h → 45min (-25min)
- Deployment Freq: 8/week → 12/week (+50%)

## Performance Trends
- API P95: 520ms → 420ms (-100ms)
- Error Rate: 0.08% → 0.05% (-0.03%)
- Throughput: 980 → 1250 req/s (+27%)
```

---

## 🎯 Goals & Targets

### Short-term Goals (3 months)

- [ ] Achieve 85% code coverage
- [ ] Reduce complexity to < 8
- [ ] Deploy daily
- [ ] Lead time < 12 hours
- [ ] MTTR < 30 minutes

### Long-term Goals (1 year)

- [ ] Achieve 90% code coverage
- [ ] Technical debt < 3%
- [ ] Multiple deployments per day
- [ ] Lead time < 4 hours
- [ ] MTTR < 15 minutes

---

## 📚 Additional Resources

- **[CI/CD Pipeline](ci-cd-pipeline.md)** - Automated quality checks
- **[Pre-commit Hooks](pre-commit-hooks.md)** - Local quality gates
- **[Code Review Guidelines](code-review-guidelines.md)** - Review process
- **[Testing Standards](testing-standards.md)** - Test requirements

---

**Last Updated:** November 14, 2024
