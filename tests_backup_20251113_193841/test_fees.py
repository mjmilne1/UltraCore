"""Fee Management Tests"""
from decimal import Decimal

def test_management_fee():
    from ultracore.fees.calculators.fee_calculator import FeeCalculator
    calc = FeeCalculator()
    fee = calc.calculate_management_fee(Decimal("1000000"), Decimal("1.0"), 365)
    assert fee == Decimal("10000")

def test_tiered_fee():
    from ultracore.fees.calculators.fee_calculator import FeeCalculator
    calc = FeeCalculator()
    tiers = [
        {"threshold": 100000, "rate": 1.0},
        {"threshold": None, "rate": 0.5}
    ]
    fee = calc.calculate_tiered_fee(Decimal("150000"), tiers)
    assert fee > Decimal("0")
