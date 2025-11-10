"""
Loan Domain - Data Mesh Domain
Domain Owner: TuringDynamics
Classification: Confidential
"""

DOMAIN_METADATA = {
    "domain_name": "loan",
    "domain_owner": "data-loan@turingdynamics.com.au",
    "description": "Loan Domain",
    "data_products": [
        "loan_portfolio",         "default_risk",         "repayment_analytics",
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
