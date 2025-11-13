"""
PROPRIETARY AND CONFIDENTIAL
Copyright (c) 2025 Richelou Pty Ltd. All Rights Reserved.
TuringDynamics Division
"""

import pytest
# from ultracore.domains.loan.aggregates import Loan, LoanStatus  # TODO: Fix import path

def test_create_loan():
    loan = Loan("LOAN-001")
    assert loan.loan_id == "LOAN-001"
    assert loan.status == LoanStatus.PENDING
