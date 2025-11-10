"""
Account Domain - Data Mesh Domain
Domain Owner: TuringDynamics
Classification: Confidential
"""

DOMAIN_METADATA = {
    "domain_name": "account",
    "domain_owner": "data-account@turingdynamics.com.au",
    "description": "Account Domain",
    "data_products": [
        "account_balances",         "transaction_history",         "account_health",
    ],
    "sla": {
        "availability": "99.9%",
        "latency_p99": "100ms",
        "freshness": "5 minutes"
    },
    "compliance": {
        "privacy_act": True,
        "aml_ctf": True,
        "data_retention_days": 2555  # 7 years
    }
}
