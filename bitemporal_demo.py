"""
Bitemporal Ledger Demonstration
Shows WHY this is essential for banking
"""

from datetime import datetime, timedelta
from decimal import Decimal

class BitemporalBankingExample:
    """Real banking scenarios showing bitemporal importance"""
    
    def __init__(self):
        self.ledger = []
    
    def scenario_1_backdated_correction(self):
        """Scenario: Bank error discovered after 3 days"""
        
        print("\n SCENARIO 1: BACKDATED CORRECTION")
        print("="*50)
        
        # What actually happened
        events = [
            {
                "business_time": "2025-01-10 09:00",  # Friday morning
                "system_time": "2025-01-13 14:00",    # Recorded Monday
                "event": "Deposit $5000 (was missed due to system error)",
                "balance": 5000
            },
            {
                "business_time": "2025-01-10 15:00",  # Friday afternoon
                "system_time": "2025-01-10 15:01",    # Recorded immediately
                "event": "Customer tries to withdraw $3000",
                "result": "REJECTED - insufficient funds"
            },
            {
                "business_time": "2025-01-10 15:00",  # Same time
                "system_time": "2025-01-13 14:01",    # Corrected Monday
                "event": "Withdrawal $3000 (now approved retroactively)",
                "balance": 2000
            }
        ]
        
        print("WITHOUT Bitemporal: Customer angry, no proof of bank error")
        print("WITH Bitemporal: Can prove deposit was valid Friday morning")
        print("\nLegal Protection: Complete audit trail for disputes")
        
        return events
    
    def scenario_2_regulatory_reporting(self):
        """Scenario: Regulator asks for exact state at specific time"""
        
        print("\n📋 SCENARIO 2: REGULATORY AUDIT")
        print("="*50)
        
        print("AUSTRAC: 'Show us all accounts over $10K at March 31, 11:59pm'")
        print("\nWithout Bitemporal:")
        print("  ❌ Can only show current state")
        print("  ❌ Can't recreate past reports")
        print("  ❌ May face penalties for non-compliance")
        
        print("\nWith Bitemporal:")
        print("  ✅ Instantly recreate EXACT state at any microsecond")
        print("  ✅ Prove compliance at any point in time")
        print("  ✅ Handle backdated transactions correctly")
        
    def scenario_3_fraud_investigation(self):
        """Scenario: Investigating suspicious patterns"""
        
        print("\n🔍 SCENARIO 3: FRAUD INVESTIGATION")  
        print("="*50)
        
        print("Fraud detected on account. Need to investigate:")
        print("\n1. When did unusual pattern ACTUALLY start?")
        print("2. When did we RECORD each transaction?")
        print("3. Were there delays in processing that hidden the pattern?")
        
        print("\nBitemporal Analysis:")
        print("  • Business time: Shows true sequence of events")
        print("  • System time: Shows when we became aware")
        print("  • Gap analysis: Identifies processing delays")
        print("  • Pattern detection: Find suspicious timing gaps")
        
    def scenario_4_interest_calculations(self):
        """Scenario: Precise interest calculations"""
        
        print("\n💰 SCENARIO 4: INTEREST CALCULATIONS")
        print("="*50)
        
        print("Customer: 'Why did I get less interest?'")
        print("\nThe Problem:")
        print("  • Deposit made Friday 4pm")
        print("  • System recorded Monday 9am")
        print("  • Customer lost 3 days of interest")
        
        print("\nBitemporal Solution:")
        print("  • Calculate interest from BUSINESS TIME (Friday)")
        print("  • System time just for audit")
        print("  • Customer gets correct interest")
        print("  • Bank maintains trust")
        
    def scenario_5_legal_evidence(self):
        """Scenario: Court case requiring evidence"""
        
        print("\n⚖️ SCENARIO 5: LEGAL EVIDENCE")
        print("="*50)
        
        print("Court: 'Prove account state during divorce proceedings'")
        print("\nBitemporal provides:")
        print("  ✅ Exact balance at separation date")
        print("  ✅ All transactions during marriage")
        print("  ✅ Proof of when transfers occurred")
        print("  ✅ Immutable audit trail")
        print("  ✅ Court-admissible evidence")

# Run demonstration
demo = BitemporalBankingExample()
demo.scenario_1_backdated_correction()
demo.scenario_2_regulatory_reporting()
demo.scenario_3_fraud_investigation()
demo.scenario_4_interest_calculations()
demo.scenario_5_legal_evidence()
