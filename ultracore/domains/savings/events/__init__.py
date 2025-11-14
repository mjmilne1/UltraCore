"""
Savings Domain Events
Event sourcing events for savings accounts
"""

from ultracore.domains.savings.events.account_events import (
    SavingsAccountOpenedEvent,
    SavingsAccountApprovedEvent,
    SavingsAccountActivatedEvent,
    SavingsAccountClosedEvent,
    SavingsAccountFrozenEvent,
    SavingsAccountDormantEvent,
    TFNProvidedEvent,
)

from ultracore.domains.savings.events.transaction_events import (
    DepositMadeEvent,
    WithdrawalMadeEvent,
    TransferInEvent,
    TransferOutEvent,
)

from ultracore.domains.savings.events.interest_events import (
    InterestAccruedEvent,
    InterestPostedEvent,
    BonusInterestEarnedEvent,
    BonusInterestForfeitedEvent,
    WithholdingTaxDeductedEvent,
)

from ultracore.domains.savings.events.fee_events import (
    MonthlyFeeChargedEvent,
    FeeWaivedEvent,
    WithdrawalFeeChargedEvent,
)

__all__ = [
    # Account Events
    "SavingsAccountOpenedEvent",
    "SavingsAccountApprovedEvent",
    "SavingsAccountActivatedEvent",
    "SavingsAccountClosedEvent",
    "SavingsAccountFrozenEvent",
    "SavingsAccountDormantEvent",
    "TFNProvidedEvent",
    # Transaction Events
    "DepositMadeEvent",
    "WithdrawalMadeEvent",
    "TransferInEvent",
    "TransferOutEvent",
    # Interest Events
    "InterestAccruedEvent",
    "InterestPostedEvent",
    "BonusInterestEarnedEvent",
    "BonusInterestForfeitedEvent",
    "WithholdingTaxDeductedEvent",
    # Fee Events
    "MonthlyFeeChargedEvent",
    "FeeWaivedEvent",
    "WithdrawalFeeChargedEvent",
]
