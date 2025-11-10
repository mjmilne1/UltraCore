"""
Payment Domain - Data Mesh Domain
Domain Owner: TuringDynamics
Classification: Confidential
"""

DOMAIN_METADATA = {
    "domain_name": "payment",
    "domain_owner": "data-payment@turingdynamics.com.au",
    "description": "Payment Domain",
    "data_products": [
        "payment_flows",         "settlement_status",         "payment_analytics",
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
