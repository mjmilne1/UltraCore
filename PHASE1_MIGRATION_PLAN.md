# Phase 1: Documentation Migration Plan

**Total Files:** 67 markdown files  
**Root-level:** 56 files (needs reorganization)  
**docs/:** 12 files (already organized)

---

## 📋 Migration Mapping

### Architecture Documentation → `docs/architecture/`
- ARCHITECTURE_AUDIT.md → docs/architecture/audit.md
- KAFKA_FIRST_ARCHITECTURE.md → docs/architecture/kafka-first.md (already exists)
- INTELLIGENT_SECURITY_ARCHITECTURE.md → docs/architecture/security.md (already exists)
- PRODUCTION_SECURITY_ARCHITECTURE.md → docs/architecture/production-security.md (already exists)
- FINERACT_MULTITENANCY_ANALYSIS.md → docs/architecture/multitenancy-analysis.md
- docs/architecture/ARCHITECTURE.md → docs/architecture/overview.md

### Module Documentation → `docs/modules/`
- ACCOUNTING_MODULE.md → docs/modules/accounting.md
- CASH_MANAGEMENT.md → docs/modules/cash-management.md
- CLIENT_MANAGEMENT_IMPLEMENTATION.md → docs/modules/client-management.md
- DATA_IMPORT_EXPORT_SYSTEM.md → docs/modules/data-import-export.md
- DOCUMENT_MANAGEMENT_SUMMARY.md → docs/modules/document-management.md
- FEE_MANAGEMENT_SYSTEM.md → docs/modules/fee-management.md
- HOLDINGS_MODULE.md → docs/modules/holdings.md
- MULTITENANCY_SYSTEM.md → docs/modules/multitenancy.md
- MULTI_CURRENCY_IMPLEMENTATION.md → docs/modules/multi-currency.md
- NOTIFICATION_SYSTEM_IMPLEMENTATION.md → docs/modules/notifications.md
- PERMISSIONS_SYSTEM.md → docs/modules/permissions.md
- CHARGES_FEES_MODULE_ARCHITECTURE.md → docs/modules/charges-fees.md (already in docs/)
- DELINQUENCY_MODULE_ARCHITECTURE.md → docs/modules/delinquency.md (already in docs/)
- FINANCIAL_REPORTING_ARCHITECTURE.md → docs/modules/financial-reporting.md (already in docs/)
- SAVINGS_MODULE_ARCHITECTURE.md → docs/modules/savings.md (already in docs/)
- SAVINGS_PHASE2_ARCHITECTURE.md → docs/modules/savings-phase2.md (already in docs/)

### Compliance Documentation → `docs/compliance/`
- AUSTRALIAN_COMPLIANCE.md → docs/compliance/australian-regulations.md
- CONFIDENTIALITY.md → docs/compliance/confidentiality.md

### Reference Documentation → `docs/reference/`
- DATABASE.md → docs/reference/database.md
- DATABASE_SCHEMA.md → docs/reference/database-schema.md (already in docs/)
- RBAC_USAGE_EXAMPLES.md → docs/reference/rbac-examples.md (already in docs/)

### Development Documentation → `docs/development/`
- CONTRIBUTING.md → docs/development/contributing.md

### Integration Documentation → `docs/integrations/`
- FISCAL_AI_INTEGRATION.md → docs/integrations/fiscal-ai.md (already in docs/)

### Audit/Reports → `docs/audits/` (archive)
- AI_CACHING_AUDIT_IMPLEMENTATION.md
- CAPSULES_AUDIT_REPORT.md
- COMPLIANCE_INTEGRATION_COMPLETE.md
- INTELLIGENT_SECURITY_COMPLETION.md
- PHASE1_COMPLETION_REPORT.md
- PHASE2_COMPLETION_REPORT.md
- PHASE3_COMPLETION_REPORT.md
- FINAL_SUMMARY.md

### Test Suite Documentation → `docs/testing/`
- ENHANCED_TEST_SUITE_DELIVERY.md
- FINAL_DELIVERY_100_PERCENT.md
- FINAL_TEST_REPORT.md
- IMPLEMENTATION_COMPLETE.md
- TODO_MOVE_MOCKS_TO_REAL_CODE.md
- TEST_SUITE_REPORT.md
- TEST_FAILURE_ANALYSIS.md
- ARCHITECTURE_TEST_ANALYSIS.md
- ARCHITECTURE_FIX_TODO.md

### Planning Documents → Keep in root (temporary)
- INSTITUTIONAL_GRADE_PLAN.md
- PHASE1_MIGRATION_PLAN.md (this file)

---

## 🏗️ New Directory Structure

```
docs/
├── README.md                          # Documentation hub
├── getting-started/
│   ├── README.md
│   ├── installation.md
│   ├── quick-start.md
│   └── troubleshooting.md
├── architecture/
│   ├── README.md
│   ├── overview.md
│   ├── kafka-first.md
│   ├── multitenancy-analysis.md
│   ├── security.md
│   ├── production-security.md
│   ├── audit.md
│   └── diagrams/
│       ├── system-context.mmd
│       ├── event-flow.mmd
│       ├── data-mesh.mmd
│       ├── investment-pods.mmd
│       └── deployment.mmd
├── modules/
│   ├── README.md
│   ├── accounting.md
│   ├── cash-management.md
│   ├── charges-fees.md
│   ├── client-management.md
│   ├── data-import-export.md
│   ├── delinquency.md
│   ├── document-management.md
│   ├── fee-management.md
│   ├── financial-reporting.md
│   ├── holdings.md
│   ├── multitenancy.md
│   ├── multi-currency.md
│   ├── notifications.md
│   ├── permissions.md
│   ├── savings.md
│   └── savings-phase2.md
├── api/
│   ├── README.md
│   ├── rest-api.md
│   ├── mcp-tools.md
│   └── webhooks.md
├── development/
│   ├── README.md
│   ├── setup.md
│   ├── contributing.md
│   ├── coding-standards.md
│   └── testing.md
├── deployment/
│   ├── README.md
│   ├── docker.md
│   ├── kubernetes.md
│   └── monitoring.md
├── compliance/
│   ├── README.md
│   ├── australian-regulations.md
│   └── confidentiality.md
├── integrations/
│   ├── README.md
│   └── fiscal-ai.md
├── reference/
│   ├── README.md
│   ├── database.md
│   ├── database-schema.md
│   ├── rbac-examples.md
│   └── glossary.md
├── testing/
│   ├── README.md
│   ├── test-suite-overview.md
│   ├── test-results.md
│   └── implementation-notes.md
└── audits/
    ├── README.md
    └── [historical audit reports]
```

---

## ✅ Implementation Steps

1. ✅ Create directory structure
2. ✅ Create hub README files
3. ✅ Move/copy files to new locations
4. ✅ Update internal links
5. ✅ Create architecture diagrams
6. ✅ Rewrite root README.md
7. ✅ Verify all links work

---

**Status:** Ready for implementation
