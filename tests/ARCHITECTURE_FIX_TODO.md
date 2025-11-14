# Architecture Fix: UltraOptimiser Integration

**Issue:** Portfolio optimization is currently implemented directly in UltraCore instead of delegating to UltraOptimiser.

**Required:** All portfolio optimization must be performed by UltraOptimiser, not UltraCore.

---

## Tasks

### 1. Audit Current Optimization Code
- [ ] Identify all direct MPT/optimization implementations in UltraCore
- [ ] Document which modules need refactoring
- [ ] Map current optimization logic to UltraOptimiser capabilities

### 2. Refactor Investment Pods
- [ ] Replace direct portfolio optimization with UltraOptimiser adapter calls
- [ ] Update `test_portfolio_optimizer.py` to test adapter integration (not MPT implementation)
- [ ] Ensure glide path adjustments use UltraOptimiser for reallocation
- [ ] Update circuit breaker to use UltraOptimiser for defensive allocation

### 3. Update UltraOptimiser Adapter
- [ ] Verify adapter supports all Investment Pods use cases
- [ ] Add missing adapter methods if needed
- [ ] Ensure proper error handling and fallbacks

### 4. Create Integration Tests
- [ ] Test Investment Pods → UltraOptimiser adapter → UltraOptimiser service
- [ ] Verify optimization results meet expected performance (8.89% return, 0.66 Sharpe)
- [ ] Test failure scenarios (UltraOptimiser unavailable)
- [ ] Test performance (optimization latency)

### 5. Update Documentation
- [ ] Document UltraOptimiser integration architecture
- [ ] Update Investment Pods README to clarify delegation
- [ ] Add architecture diagrams showing proper separation

---

## Architecture Principles

**Separation of Concerns:**
- **UltraCore:** Business logic, event sourcing, multi-tenancy, workflows
- **UltraOptimiser:** Portfolio optimization, asset allocation, rebalancing algorithms

**Integration Pattern:**
```
Investment Pod → UltraOptimiser Adapter → UltraOptimiser Service
```

**What UltraCore Should NOT Do:**
- ❌ Implement Modern Portfolio Theory
- ❌ Calculate efficient frontier
- ❌ Optimize Sharpe ratio
- ❌ Calculate covariance matrices
- ❌ Perform portfolio optimization algorithms

**What UltraCore SHOULD Do:**
- ✅ Call UltraOptimiser adapter with requirements
- ✅ Handle optimization results (events, persistence)
- ✅ Manage business rules (constraints, glide paths)
- ✅ Track optimization history

---

## Files to Update

### Remove/Refactor:
1. `tests/unit/investment_pods/test_portfolio_optimizer.py` - Remove MPT implementation tests
2. Any direct optimization code in `ultracore/investment_pods/services/`

### Add:
1. `tests/integration/ultraoptimiser/test_adapter_integration.py` - Adapter tests
2. `tests/integration/ultraoptimiser/test_pod_optimization.py` - End-to-end optimization tests
3. `tests/unit/investment_pods/test_optimization_adapter.py` - Adapter unit tests

### Update:
1. `ultracore/investment_pods/services/portfolio_service.py` - Use adapter
2. `ultracore/investment_pods/aggregates/pod_aggregate.py` - Delegate optimization

---

## Success Criteria

- [ ] Zero direct MPT/optimization code in UltraCore
- [ ] All optimization goes through UltraOptimiser adapter
- [ ] Integration tests verify proper delegation
- [ ] Performance tests confirm acceptable latency
- [ ] Documentation clearly explains architecture
- [ ] Tests pass with UltraOptimiser service running

---

**Status:** Ready to implement fixes
