"""
UltraCore Multi-Currency API

Complete REST API for multi-currency and forex operations:
- Currency management
- Exchange rates
- Forex transactions
- Multi-currency accounts
- Currency conversions
- Forex accounting (gains/losses, revaluation)
- Statements and reporting
"""

from fastapi import FastAPI, HTTPException, Query, Path, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from decimal import Decimal

from ultracore.accounting.forex.currency_manager import (
    get_currency_manager, CurrencyCode, RateType, RateSource
)
from ultracore.accounting.forex.forex_accounting import (
    get_forex_engine, ForexGainLossType, RevaluationMethod
)
from ultracore.accounting.forex.multicurrency_accounts import (
    get_mc_account_manager, ConversionType, BalanceType, 
    CurrencyWalletStatus
)


# ============================================================================
# Pydantic Models
# ============================================================================

class CurrencyResponse(BaseModel):
    code: str
    name: str
    symbol: str
    numeric_code: str
    minor_units: int
    active: bool
    countries: List[str]


class ExchangeRateResponse(BaseModel):
    rate_id: str
    from_currency: str
    to_currency: str
    rate: str
    inverse_rate: str
    rate_type: str
    rate_source: str
    effective_date: str
    effective_time: str


class ConvertAmountRequest(BaseModel):
    from_currency: str
    to_currency: str
    amount: str
    rate_type: str = "MID"


class ConvertAmountResponse(BaseModel):
    from_currency: str
    to_currency: str
    from_amount: str
    to_amount: str
    exchange_rate: str
    rate_id: str


class SetExchangeRateRequest(BaseModel):
    from_currency: str
    to_currency: str
    rate: str
    rate_type: str = "MID"
    rate_source: str = "MANUAL"
    effective_date: Optional[str] = None
    created_by: str


class ForexTransactionRequest(BaseModel):
    from_currency: str
    to_currency: str
    from_amount: str
    from_account: str
    to_account: str
    description: str
    created_by: str
    reference: Optional[str] = None
    rate: Optional[str] = None
    auto_post: bool = True


class ForexTransactionResponse(BaseModel):
    transaction_id: str
    from_currency: str
    to_currency: str
    from_amount: str
    to_amount: str
    exchange_rate: str
    realized_gain_loss: Optional[str]
    journal_entry_id: Optional[str]
    transaction_date: str


class RevaluationRequest(BaseModel):
    revaluation_date: str
    currencies: Optional[List[str]] = None
    method: str = "SPOT_RATE"
    created_by: str = "system"
    auto_post: bool = True


class RevaluationResponse(BaseModel):
    revaluation_id: str
    currency: str
    previous_rate: str
    new_rate: str
    rate_change_percent: float
    unrealized_gain_loss: str
    accounts_affected: int
    posted: bool


class ForexSummaryResponse(BaseModel):
    as_of_date: str
    base_currency: str
    total_unrealized_gain_loss: str
    total_positions: int
    by_currency: List[Dict[str, Any]]


class CreateMultiCurrencyAccountRequest(BaseModel):
    account_name: str
    primary_currency: str
    customer_id: Optional[str] = None
    allowed_currencies: Optional[List[str]] = None
    gl_account_code: Optional[str] = None


class MultiCurrencyAccountResponse(BaseModel):
    account_id: str
    account_name: str
    primary_currency: str
    allowed_currencies: List[str]
    wallets: Dict[str, Dict[str, str]]
    active: bool
    customer_id: Optional[str]


class WalletBalanceResponse(BaseModel):
    account_id: str
    currency: str
    available_balance: str
    held_balance: str
    pending_balance: str
    total_balance: str
    status: str


class CreditDebitRequest(BaseModel):
    currency: str
    amount: str
    description: str
    created_by: str
    reference: Optional[str] = None


class CurrencyConversionRequest(BaseModel):
    from_currency: str
    to_currency: str
    from_amount: str
    created_by: str = "system"
    reference: Optional[str] = None


class CurrencyConversionResponse(BaseModel):
    conversion_id: str
    from_currency: str
    to_currency: str
    from_amount: str
    to_amount: str
    exchange_rate: str
    conversion_fee: str
    realized_gain_loss: Optional[str]
    from_wallet_balance: str
    to_wallet_balance: str


class AccountTotalValueResponse(BaseModel):
    account_id: str
    target_currency: str
    total_value: str
    breakdown: Dict[str, str]


class MultiCurrencyStatementResponse(BaseModel):
    statement_id: str
    account_id: str
    period_start: str
    period_end: str
    opening_balance_primary: str
    closing_balance_primary: str
    currency_statements: Dict[str, Dict[str, Any]]
    transaction_count: int
    conversion_count: int
    total_realized_gain_loss: str


# ============================================================================
# FastAPI Application
# ============================================================================

forex_app = FastAPI(
    title="UltraCore Forex & Multi-Currency API",
    description="Enterprise multi-currency and foreign exchange API",
    version="1.0.0"
)

# CORS middleware
forex_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
currency_manager = get_currency_manager()
forex_engine = get_forex_engine()
mc_account_manager = get_mc_account_manager()


# ============================================================================
# Currency Endpoints
# ============================================================================

@forex_app.get("/api/forex/currencies", response_model=List[CurrencyResponse])
async def list_currencies(active_only: bool = Query(True)):
    """List all supported currencies"""
    
    currencies = currency_manager.list_currencies(active_only=active_only)
    
    return [
        CurrencyResponse(
            code=c.code.value,
            name=c.name,
            symbol=c.symbol,
            numeric_code=c.numeric_code,
            minor_units=c.minor_units,
            active=c.active,
            countries=c.countries
        )
        for c in currencies
    ]


@forex_app.get("/api/forex/currencies/{currency_code}", response_model=CurrencyResponse)
async def get_currency(currency_code: str):
    """Get specific currency details"""
    
    try:
        code = CurrencyCode(currency_code)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid currency code: {currency_code}")
    
    currency = currency_manager.get_currency(code)
    if not currency:
        raise HTTPException(status_code=404, detail=f"Currency {currency_code} not found")
    
    return CurrencyResponse(
        code=currency.code.value,
        name=currency.name,
        symbol=currency.symbol,
        numeric_code=currency.numeric_code,
        minor_units=currency.minor_units,
        active=currency.active,
        countries=currency.countries
    )


@forex_app.get("/api/forex/exchange-rates/{from_currency}/{to_currency}", 
               response_model=ExchangeRateResponse)
async def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    rate_type: str = Query("MID"),
    as_of: Optional[str] = Query(None)
):
    """Get exchange rate between two currencies"""
    
    try:
        from_curr = CurrencyCode(from_currency)
        to_curr = CurrencyCode(to_currency)
        r_type = RateType(rate_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    as_of_dt = datetime.fromisoformat(as_of) if as_of else None
    
    rate = await currency_manager.get_exchange_rate(
        from_curr,
        to_curr,
        r_type,
        as_of_dt
    )
    
    if not rate:
        raise HTTPException(
            status_code=404,
            detail=f"No rate available for {from_currency}/{to_currency}"
        )
    
    return ExchangeRateResponse(
        rate_id=rate.rate_id,
        from_currency=rate.from_currency.value,
        to_currency=rate.to_currency.value,
        rate=str(rate.rate),
        inverse_rate=str(rate.inverse_rate),
        rate_type=rate.rate_type.value,
        rate_source=rate.rate_source.value,
        effective_date=rate.effective_date.isoformat(),
        effective_time=rate.effective_time.isoformat()
    )


@forex_app.post("/api/forex/exchange-rates", response_model=ExchangeRateResponse)
async def set_exchange_rate(request: SetExchangeRateRequest):
    """Manually set an exchange rate"""
    
    try:
        from_curr = CurrencyCode(request.from_currency)
        to_curr = CurrencyCode(request.to_currency)
        r_type = RateType(request.rate_type)
        r_source = RateSource(request.rate_source)
        rate_val = Decimal(request.rate)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    eff_date = date.fromisoformat(request.effective_date) if request.effective_date else None
    
    rate = await currency_manager.set_exchange_rate(
        from_curr,
        to_curr,
        rate_val,
        r_type,
        r_source,
        eff_date,
        request.created_by
    )
    
    return ExchangeRateResponse(
        rate_id=rate.rate_id,
        from_currency=rate.from_currency.value,
        to_currency=rate.to_currency.value,
        rate=str(rate.rate),
        inverse_rate=str(rate.inverse_rate),
        rate_type=rate.rate_type.value,
        rate_source=rate.rate_source.value,
        effective_date=rate.effective_date.isoformat(),
        effective_time=rate.effective_time.isoformat()
    )


@forex_app.post("/api/forex/convert", response_model=ConvertAmountResponse)
async def convert_amount(request: ConvertAmountRequest):
    """Convert amount between currencies"""
    
    try:
        from_curr = CurrencyCode(request.from_currency)
        to_curr = CurrencyCode(request.to_currency)
        amount = Decimal(request.amount)
        r_type = RateType(request.rate_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    converted_amount, rate = await currency_manager.convert_amount(
        amount,
        from_curr,
        to_curr,
        r_type
    )
    
    return ConvertAmountResponse(
        from_currency=request.from_currency,
        to_currency=request.to_currency,
        from_amount=request.amount,
        to_amount=str(converted_amount),
        exchange_rate=str(rate.rate),
        rate_id=rate.rate_id
    )


@forex_app.get("/api/forex/format-amount")
async def format_amount(
    amount: str = Query(...),
    currency: str = Query(...)
):
    """Format amount with currency symbol"""
    
    try:
        curr = CurrencyCode(currency)
        amt = Decimal(amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    formatted = currency_manager.format_amount(amt, curr)
    
    return {'formatted': formatted}


# ============================================================================
# Forex Accounting Endpoints
# ============================================================================

@forex_app.post("/api/forex/transactions", response_model=ForexTransactionResponse)
async def record_forex_transaction(request: ForexTransactionRequest):
    """Record a forex transaction"""
    
    try:
        from_curr = CurrencyCode(request.from_currency)
        to_curr = CurrencyCode(request.to_currency)
        from_amt = Decimal(request.from_amount)
        rate_val = Decimal(request.rate) if request.rate else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    transaction = await forex_engine.record_forex_transaction(
        from_currency=from_curr,
        to_currency=to_curr,
        from_amount=from_amt,
        from_account=request.from_account,
        to_account=request.to_account,
        description=request.description,
        created_by=request.created_by,
        reference=request.reference,
        rate=rate_val,
        auto_post=request.auto_post
    )
    
    return ForexTransactionResponse(
        transaction_id=transaction.transaction_id,
        from_currency=transaction.from_currency.value,
        to_currency=transaction.to_currency.value,
        from_amount=str(transaction.from_amount),
        to_amount=str(transaction.to_amount),
        exchange_rate=str(transaction.exchange_rate),
        realized_gain_loss=str(transaction.realized_gain_loss) if transaction.realized_gain_loss else None,
        journal_entry_id=transaction.journal_entry_id,
        transaction_date=transaction.transaction_date.isoformat()
    )


@forex_app.post("/api/forex/revaluation", response_model=List[RevaluationResponse])
async def perform_revaluation(request: RevaluationRequest):
    """Perform period-end forex revaluation"""
    
    try:
        reval_date = date.fromisoformat(request.revaluation_date)
        method = RevaluationMethod(request.method)
        currencies = [CurrencyCode(c) for c in request.currencies] if request.currencies else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    revaluations = await forex_engine.perform_period_end_revaluation(
        revaluation_date=reval_date,
        currencies=currencies,
        method=method,
        created_by=request.created_by,
        auto_post=request.auto_post
    )
    
    return [
        RevaluationResponse(
            revaluation_id=r.revaluation_id,
            currency=r.currency.value,
            previous_rate=str(r.previous_rate),
            new_rate=str(r.new_rate),
            rate_change_percent=r.rate_change_percent,
            unrealized_gain_loss=str(r.unrealized_gain_loss),
            accounts_affected=len(r.accounts),
            posted=r.posted
        )
        for r in revaluations
    ]


@forex_app.get("/api/forex/summary", response_model=ForexSummaryResponse)
async def get_forex_summary(as_of_date: Optional[str] = Query(None)):
    """Get forex positions and unrealized gains/losses summary"""
    
    as_of = date.fromisoformat(as_of_date) if as_of_date else None
    
    summary = await forex_engine.get_forex_summary(as_of)
    
    return ForexSummaryResponse(**summary)


@forex_app.get("/api/forex/realized-gains-losses")
async def get_realized_gains_losses(
    start_date: str = Query(...),
    end_date: str = Query(...)
):
    """Get realized forex gains/losses for period"""
    
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    gains_losses = await forex_engine.get_realized_gains_losses(start, end)
    
    return {
        'period_start': start_date,
        'period_end': end_date,
        'gains_losses': gains_losses,
        'total': str(sum(Decimal(gl['realized_gain_loss']) for gl in gains_losses))
    }


# ============================================================================
# Multi-Currency Account Endpoints
# ============================================================================

@forex_app.post("/api/forex/accounts", response_model=MultiCurrencyAccountResponse)
async def create_multicurrency_account(request: CreateMultiCurrencyAccountRequest):
    """Create a new multi-currency account"""
    
    try:
        primary_curr = CurrencyCode(request.primary_currency)
        allowed_curr = [CurrencyCode(c) for c in request.allowed_currencies] if request.allowed_currencies else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    account = await mc_account_manager.create_account(
        account_name=request.account_name,
        primary_currency=primary_curr,
        customer_id=request.customer_id,
        allowed_currencies=allowed_curr,
        gl_account_code=request.gl_account_code
    )
    
    wallets = {}
    for currency, wallet in account.wallets.items():
        wallets[currency.value] = {
            'wallet_id': wallet.wallet_id,
            'available_balance': str(wallet.available_balance),
            'total_balance': str(wallet.total_balance()),
            'status': wallet.status.value
        }
    
    return MultiCurrencyAccountResponse(
        account_id=account.account_id,
        account_name=account.account_name,
        primary_currency=account.primary_currency.value,
        allowed_currencies=[c.value for c in account.allowed_currencies],
        wallets=wallets,
        active=account.active,
        customer_id=account.customer_id
    )


@forex_app.get("/api/forex/accounts/{account_id}", response_model=MultiCurrencyAccountResponse)
async def get_multicurrency_account(account_id: str):
    """Get multi-currency account details"""
    
    account = await mc_account_manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    wallets = {}
    for currency, wallet in account.wallets.items():
        wallets[currency.value] = {
            'wallet_id': wallet.wallet_id,
            'available_balance': str(wallet.available_balance),
            'total_balance': str(wallet.total_balance()),
            'status': wallet.status.value
        }
    
    return MultiCurrencyAccountResponse(
        account_id=account.account_id,
        account_name=account.account_name,
        primary_currency=account.primary_currency.value,
        allowed_currencies=[c.value for c in account.allowed_currencies],
        wallets=wallets,
        active=account.active,
        customer_id=account.customer_id
    )


@forex_app.get("/api/forex/accounts/{account_id}/balances")
async def get_account_balances(account_id: str):
    """Get all currency balances for an account"""
    
    balances = await mc_account_manager.get_all_balances(account_id)
    
    return {
        'account_id': account_id,
        'balances': {
            currency.value: {
                'available': str(bal['available']),
                'held': str(bal['held']),
                'pending': str(bal['pending']),
                'total': str(bal['total'])
            }
            for currency, bal in balances.items()
        }
    }


@forex_app.get("/api/forex/accounts/{account_id}/balances/{currency}", 
               response_model=WalletBalanceResponse)
async def get_wallet_balance(
    account_id: str,
    currency: str,
    balance_type: str = Query("AVAILABLE")
):
    """Get balance for specific currency wallet"""
    
    try:
        curr = CurrencyCode(currency)
        bal_type = BalanceType(balance_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    account = await mc_account_manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    wallet = account.get_wallet(curr)
    if not wallet:
        raise HTTPException(status_code=404, detail=f"Wallet for {currency} not found")
    
    return WalletBalanceResponse(
        account_id=account_id,
        currency=currency,
        available_balance=str(wallet.available_balance),
        held_balance=str(wallet.held_balance),
        pending_balance=str(wallet.pending_balance),
        total_balance=str(wallet.total_balance()),
        status=wallet.status.value
    )


@forex_app.get("/api/forex/accounts/{account_id}/total-value", 
               response_model=AccountTotalValueResponse)
async def get_account_total_value(
    account_id: str,
    target_currency: str = Query(...)
):
    """Get total account value in specified currency"""
    
    try:
        target_curr = CurrencyCode(target_currency)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    total_value, breakdown = await mc_account_manager.get_total_value_in_currency(
        account_id,
        target_curr
    )
    
    return AccountTotalValueResponse(
        account_id=account_id,
        target_currency=target_currency,
        total_value=str(total_value),
        breakdown={c.value: str(v) for c, v in breakdown.items()}
    )


@forex_app.post("/api/forex/accounts/{account_id}/credit")
async def credit_account(account_id: str, request: CreditDebitRequest):
    """Credit (add to) account balance"""
    
    try:
        curr = CurrencyCode(request.currency)
        amount = Decimal(request.amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    transaction = await mc_account_manager.credit_balance(
        account_id=account_id,
        currency=curr,
        amount=amount,
        description=request.description,
        created_by=request.created_by,
        reference=request.reference
    )
    
    return {
        'transaction_id': transaction.transaction_id,
        'account_id': account_id,
        'currency': request.currency,
        'amount': request.amount,
        'balance_after': str(transaction.balance_after),
        'transaction_date': transaction.transaction_date.isoformat()
    }


@forex_app.post("/api/forex/accounts/{account_id}/debit")
async def debit_account(account_id: str, request: CreditDebitRequest):
    """Debit (subtract from) account balance"""
    
    try:
        curr = CurrencyCode(request.currency)
        amount = Decimal(request.amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        transaction = await mc_account_manager.debit_balance(
            account_id=account_id,
            currency=curr,
            amount=amount,
            description=request.description,
            created_by=request.created_by,
            reference=request.reference
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        'transaction_id': transaction.transaction_id,
        'account_id': account_id,
        'currency': request.currency,
        'amount': request.amount,
        'balance_after': str(transaction.balance_after),
        'transaction_date': transaction.transaction_date.isoformat()
    }


@forex_app.post("/api/forex/accounts/{account_id}/convert", 
                response_model=CurrencyConversionResponse)
async def convert_currency_in_account(
    account_id: str,
    request: CurrencyConversionRequest
):
    """Convert currency within account"""
    
    try:
        from_curr = CurrencyCode(request.from_currency)
        to_curr = CurrencyCode(request.to_currency)
        from_amount = Decimal(request.from_amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        conversion = await mc_account_manager.convert_currency(
            account_id=account_id,
            from_currency=from_curr,
            to_currency=to_curr,
            from_amount=from_amount,
            conversion_type=ConversionType.MANUAL,
            created_by=request.created_by,
            reference=request.reference
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return CurrencyConversionResponse(
        conversion_id=conversion.conversion_id,
        from_currency=conversion.from_currency.value,
        to_currency=conversion.to_currency.value,
        from_amount=str(conversion.from_amount),
        to_amount=str(conversion.to_amount),
        exchange_rate=str(conversion.exchange_rate),
        conversion_fee=str(conversion.conversion_fee),
        realized_gain_loss=str(conversion.realized_gain_loss) if conversion.realized_gain_loss else None,
        from_wallet_balance=str(conversion.from_wallet_balance),
        to_wallet_balance=str(conversion.to_wallet_balance)
    )


@forex_app.get("/api/forex/accounts/{account_id}/transactions")
async def get_account_transactions(
    account_id: str,
    currency: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get account transaction history"""
    
    try:
        curr = CurrencyCode(currency) if currency else None
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    transactions = await mc_account_manager.get_transactions(
        account_id=account_id,
        currency=curr,
        start_date=start,
        end_date=end,
        limit=limit
    )
    
    return {
        'account_id': account_id,
        'transaction_count': len(transactions),
        'transactions': [
            {
                'transaction_id': t.transaction_id,
                'date': t.transaction_date.isoformat(),
                'type': t.transaction_type,
                'currency': t.currency.value,
                'amount': str(t.amount),
                'balance_after': str(t.balance_after),
                'description': t.description,
                'reference': t.reference
            }
            for t in transactions
        ]
    }


@forex_app.get("/api/forex/accounts/{account_id}/conversions")
async def get_account_conversions(
    account_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get account conversion history"""
    
    try:
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    conversions = await mc_account_manager.get_conversions(
        account_id=account_id,
        start_date=start,
        end_date=end
    )
    
    return {
        'account_id': account_id,
        'conversion_count': len(conversions),
        'conversions': [
            {
                'conversion_id': c.conversion_id,
                'date': c.created_at.isoformat(),
                'from_currency': c.from_currency.value,
                'to_currency': c.to_currency.value,
                'from_amount': str(c.from_amount),
                'to_amount': str(c.to_amount),
                'rate': str(c.exchange_rate),
                'fee': str(c.conversion_fee),
                'realized_gain_loss': str(c.realized_gain_loss) if c.realized_gain_loss else None
            }
            for c in conversions
        ]
    }


@forex_app.get("/api/forex/accounts/{account_id}/statement", 
               response_model=MultiCurrencyStatementResponse)
async def generate_account_statement(
    account_id: str,
    period_start: str = Query(...),
    period_end: str = Query(...),
    generated_by: Optional[str] = Query(None)
):
    """Generate multi-currency statement"""
    
    try:
        start = date.fromisoformat(period_start)
        end = date.fromisoformat(period_end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    statement = await mc_account_manager.generate_statement(
        account_id=account_id,
        period_start=start,
        period_end=end,
        generated_by=generated_by
    )
    
    return MultiCurrencyStatementResponse(
        statement_id=statement.statement_id,
        account_id=statement.account_id,
        period_start=statement.period_start.isoformat(),
        period_end=statement.period_end.isoformat(),
        opening_balance_primary=str(statement.opening_balance_primary),
        closing_balance_primary=str(statement.closing_balance_primary),
        currency_statements=statement.currency_statements,
        transaction_count=len(statement.transactions),
        conversion_count=len(statement.conversions),
        total_realized_gain_loss=str(statement.total_realized_gain_loss)
    )


# ============================================================================
# Dashboard & Reporting
# ============================================================================

@forex_app.get("/api/forex/dashboard")
async def get_forex_dashboard():
    """Get forex dashboard with key metrics"""
    
    # Get forex summary
    forex_summary = await forex_engine.get_forex_summary()
    
    # Get exchange rates for major pairs
    major_pairs = [
        ("AUD", "USD"),
        ("AUD", "EUR"),
        ("AUD", "GBP"),
        ("AUD", "JPY"),
        ("EUR", "USD"),
        ("GBP", "USD")
    ]
    
    rates = []
    for from_curr, to_curr in major_pairs:
        try:
            rate = await currency_manager.get_exchange_rate(
                CurrencyCode(from_curr),
                CurrencyCode(to_curr),
                RateType.MID
            )
            if rate:
                rates.append({
                    'pair': f"{from_curr}/{to_curr}",
                    'rate': str(rate.rate),
                    'source': rate.rate_source.value,
                    'time': rate.effective_time.isoformat()
                })
        except:
            pass
    
    return {
        'forex_positions': forex_summary,
        'exchange_rates': rates,
        'timestamp': datetime.utcnow().isoformat()
    }


# ============================================================================
# Health & Status
# ============================================================================

@forex_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'UltraCore Forex API',
        'version': '1.0.0'
    }


@forex_app.get("/")
async def root():
    """Root endpoint"""
    return {
        'message': 'UltraCore Forex & Multi-Currency API',
        'version': '1.0.0',
        'docs': '/docs',
        'health': '/health',
        'features': [
            'Multi-currency accounts',
            'Foreign exchange',
            'Forex accounting',
            'Revaluation',
            'Real-time rates'
        ]
    }


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        forex_app,
        host="0.0.0.0",
        port=8005,
        log_level="info"
    )
