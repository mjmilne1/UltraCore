"""
Client/Customer Domain - Data Mesh Domain
Domain Owner: TuringDynamics
Classification: Confidential
"""

DOMAIN_METADATA = {
    "domain_name": "client",
    "domain_owner": "data-client@turingdynamics.com.au",
    "description": "Client/Customer Domain",
    "data_products": [
        "customer_360",         "kyc_status",         "customer_segments",
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
