# TODO: Move Mock Implementations to Actual UltraCore Code

**Status:** 🚨 **CRITICAL - Tests passing with mocks, not actual code**

**Current Situation:**
- ✅ **191 tests passing** (100% pass rate)
- ❌ **0% code coverage** (testing mocks, not real code)
- ⚠️ **Mock implementations in `tests/helpers/`** instead of `src/ultracore/`

---

## 🎯 Goal

Move all mock implementations from `tests/helpers/` to `src/ultracore/` and update tests to use actual UltraCore code.

---

## 📋 Components to Move

### 1. Investment Pods (HIGH PRIORITY)
**Current Location:** `tests/helpers/event_sourced_pod.py`  
**Target Location:** `src/ultracore/domains/wealth/models/investment_pod.py` (already exists, needs enhancement)  
**Status:** ⚠️ Basic implementation exists, needs event sourcing integration

**What to move:**
- `EventSourcedInvestmentPod` class
- Event handlers (`apply_pod_created`, `apply_allocation_optimized`, etc.)
- State reconstruction from events
- Circuit breaker logic (15% drawdown)
- Goal achievement tracking

**Estimated effort:** 4-6 hours

---

### 2. Glide Path Engine (HIGH PRIORITY)
**Current Location:** `src/ultracore/domains/wealth/services/glide_path_engine.py` (already implemented!)  
**Target Location:** Same (already in correct location)  
**Status:** ✅ Already in production location

**What's done:**
- 3 glide path strategies (linear, exponential, stepped)
- Risk reduction as target date approaches
- Rebalancing recommendations

**No action needed** - already in correct location!

---

### 3. Event Store (MEDIUM PRIORITY)
**Current Location:** `tests/helpers/event_store.py`  
**Target Location:** `src/ultracore/events/event_store.py`  
**Status:** ⚠️ Test helper, needs to become production component

**What to move:**
- `EventStore` class
- Query methods (`get_events_by_aggregate`, `get_events_by_type`, `get_events_by_tenant`)
- Timestamp filtering for time travel queries
- Aggregate reconstruction

**Estimated effort:** 2-3 hours

---

### 4. Event-Driven UltraOptimiser (MEDIUM PRIORITY)
**Current Location:** `tests/helpers/event_driven_optimiser.py`  
**Target Location:** `src/ultracore/domains/wealth/services/event_driven_optimiser.py`  
**Status:** ⚠️ Test helper, needs to become production component

**What to move:**
- `EventDrivenOptimiser` class
- Event handlers (`handle_pod_created`, `handle_glide_path_adjustment`)
- Event processing loop
- Integration with UltraOptimiser adapter

**Estimated effort:** 3-4 hours

---

### 5. Aggregate Reconstruction (MEDIUM PRIORITY)
**Current Location:** `tests/helpers/aggregate_reconstruction.py`  
**Target Location:** `src/ultracore/events/aggregate_reconstruction.py`  
**Status:** ⚠️ Test helper, needs to become production component

**What to move:**
- `AggregateReconstructor` class
- Event replay logic
- Snapshot support
- State rebuilding from event streams

**Estimated effort:** 2-3 hours

---

### 6. Mock Kafka (LOW PRIORITY - Keep as test helper)
**Current Location:** `tests/helpers/mock_kafka.py`  
**Target Location:** Keep in `tests/helpers/` (this is a test double)  
**Status:** ✅ Correctly placed (test infrastructure)

**No action needed** - this should remain a test helper.

---

### 7. Mock UltraOptimiser (LOW PRIORITY - Keep as test helper)
**Current Location:** `tests/helpers/mock_ultraoptimiser.py`  
**Target Location:** Keep in `tests/helpers/` (this is a test double)  
**Status:** ✅ Correctly placed (test infrastructure)

**No action needed** - this should remain a test helper for testing without real UltraOptimiser.

---

### 8. Mock ML Models (LOW PRIORITY - Keep as test helper)
**Current Location:** `tests/helpers/mock_ml_models.py`  
**Target Location:** Keep in `tests/helpers/` (test doubles)  
**Status:** ✅ Correctly placed (test infrastructure)

**No action needed** - these should remain test helpers.

---

### 9. Data Mesh Helpers (MEDIUM PRIORITY)
**Current Location:** `tests/helpers/data_mesh.py`  
**Target Location:** `src/ultracore/data_mesh/`  
**Status:** ⚠️ Test helper, needs to become production component

**What to move:**
- `DataProductSchema` class
- `DataQualityChecker` class
- `FederatedQueryEngine` class
- `DataLineageTracker` class

**Estimated effort:** 3-4 hours

---

### 10. MCP Tools (MEDIUM PRIORITY)
**Current Location:** `tests/helpers/mock_mcp_tools.py`  
**Target Location:** `src/ultracore/agentic/mcp_tools.py`  
**Status:** ⚠️ Test helper, needs to become production component

**What to move:**
- `MCPToolRegistry` class
- Account tools
- Investment Pod tools
- UltraOptimiser tools
- `InvestmentOrchestrator` class

**Estimated effort:** 3-4 hours

---

### 11. Performance Testing Helpers (LOW PRIORITY - Keep as test helper)
**Current Location:** `tests/helpers/performance.py`  
**Target Location:** Keep in `tests/helpers/` (test infrastructure)  
**Status:** ✅ Correctly placed (test infrastructure)

**No action needed** - this should remain a test helper.

---

## 📝 Step-by-Step Implementation Plan

### Phase 1: Core Event Sourcing (6-9 hours)
1. ✅ Move `EventStore` to `src/ultracore/events/event_store.py`
2. ✅ Move `AggregateReconstructor` to `src/ultracore/events/aggregate_reconstruction.py`
3. ✅ Update test imports to use actual code
4. ✅ Run tests to verify (should still pass)

### Phase 2: Investment Pods (4-6 hours)
1. ✅ Enhance `src/ultracore/domains/wealth/models/investment_pod.py` with event sourcing
2. ✅ Add event handlers from `EventSourcedInvestmentPod`
3. ✅ Update test imports
4. ✅ Run tests to verify

### Phase 3: Event-Driven Optimization (3-4 hours)
1. ✅ Move `EventDrivenOptimiser` to `src/ultracore/domains/wealth/services/`
2. ✅ Update test imports
3. ✅ Run tests to verify

### Phase 4: Data Mesh & Agentic AI (6-8 hours)
1. ✅ Move Data Mesh components to `src/ultracore/data_mesh/`
2. ✅ Move MCP Tools to `src/ultracore/agentic/mcp_tools.py`
3. ✅ Update test imports
4. ✅ Run tests to verify

### Phase 5: Final Verification (2-3 hours)
1. ✅ Run full test suite
2. ✅ Verify code coverage >80%
3. ✅ Update documentation
4. ✅ Create final delivery report

---

## 🎯 Success Criteria

- [ ] All tests still passing (191/191)
- [ ] Code coverage >80% (currently 0%)
- [ ] All production code in `src/ultracore/`
- [ ] Test helpers remain in `tests/helpers/`
- [ ] Documentation updated

---

## ⏱️ Total Estimated Effort

**24-34 hours** (3-4 working days)

---

## 🚨 Why This Matters

**Current state:**
- Tests validate **design and architecture** ✅
- Tests do NOT validate **actual UltraCore code** ❌

**After moving to real code:**
- Tests validate **both design AND implementation** ✅
- Code coverage metrics become meaningful ✅
- Production-ready components ✅

---

## 📞 Next Steps

1. **Review this document**
2. **Prioritize phases** (recommend starting with Phase 1)
3. **Allocate time** (3-4 days)
4. **Execute plan** (move components one by one)
5. **Verify coverage** (should reach >80%)

---

## 📌 Quick Reference

**Test Results:**
- Current: 191 passed, 0% coverage
- Target: 191 passed, >80% coverage

**Key Files:**
- This TODO: `/home/ubuntu/UltraCore-audit-2/TODO_MOVE_MOCKS_TO_REAL_CODE.md`
- Test suite: `/home/ubuntu/UltraCore-audit-2/tests/`
- Source code: `/home/ubuntu/UltraCore-audit-2/src/ultracore/`

**Commands:**
```bash
# Run tests
cd /home/ubuntu/UltraCore-audit-2
source .venv/bin/activate
python -m pytest tests/ -v --cov=src/ultracore --cov-report=html

# Check coverage
open htmlcov/index.html
```

---

**Created:** November 14, 2025  
**Status:** 🚨 **PENDING - Awaiting implementation**  
**Priority:** **HIGH - Critical for production readiness**
