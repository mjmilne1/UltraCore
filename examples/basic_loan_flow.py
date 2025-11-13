"""
PROPRIETARY AND CONFIDENTIAL
Copyright (c) 2025 Richelou Pty Ltd. All Rights Reserved.
TuringDynamics Division
"""

# from ultracore.domains.loan.aggregates import Loan  # TODO: Fix import path

def main():
    print("🏦 UltraCore - Loan Example")
    print("© 2025 Richelou Pty Ltd - TuringDynamics\n")
    
    loan = Loan("LOAN-001")
    print(f"Created loan: {loan.to_dict()}")

if __name__ == "__main__":
    main()
