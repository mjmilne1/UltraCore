# Fee Management MCP Tools

## Overview
MCP tools for fee calculation, optimization, and Australian GST handling.

## Functions
- `calculate_fee()` - Calculate all fee types
- `get_fee_schedule()` - Get client fee schedule
- `optimize_fee_structure()` - Optimize fee structure
- `calculate_australian_gst()` - Calculate Australian GST

## Fee Types Supported
- Management fees (% of AUM)
- Performance fees (% of gains)
- Tiered fees (multiple brackets)
- Transaction fees (fixed or %)
- Subscription fees

## Australian GST
Handles 10% GST calculation with input tax credit support for GST-registered clients.

## Usage
```python
from ultracore.mcp.fee_tools.fee_mcp_tools import calculate_fee

result = await calculate_fee(
    fee_type="management",
    amount=Decimal("1000000"),
    parameters={"annual_rate": 1.0, "billing_frequency": "monthly"},
    tenant_id="tenant_001"
)
```
