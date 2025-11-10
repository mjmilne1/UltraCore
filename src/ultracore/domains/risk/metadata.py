"""
Risk & Compliance Domain - Data Mesh Domain
Domain Owner: TuringDynamics
Classification: Confidential
"""

DOMAIN_METADATA = {
    "domain_name": "risk",
    "domain_owner": "data-risk@turingdynamics.com.au",
    "description": "Risk & Compliance Domain",
    "data_products": [
        "risk_scores",         "fraud_alerts",         "compliance_reports",
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
