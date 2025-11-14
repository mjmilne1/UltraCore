"""Broker Format Parsers - Support for major brokers"""
import csv
from typing import List, Dict, Any
from decimal import Decimal
from datetime import datetime

class BrokerParser:
    """Base parser for broker formats"""
    
    def parse(self, file_content: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

class VanguardParser(BrokerParser):
    """Vanguard CSV format parser"""
    
    def parse(self, file_content: str) -> List[Dict[str, Any]]:
        rows = []
        reader = csv.DictReader(file_content.splitlines())
        for row in reader:
            rows.append({
                "date": self._parse_date(row.get("Trade Date")),
                "symbol": row.get("Symbol"),
                "description": row.get("Description"),
                "quantity": Decimal(row.get("Quantity", "0")),
                "price": Decimal(row.get("Price", "0")),
                "amount": Decimal(row.get("Amount", "0")),
                "transaction_type": row.get("Transaction Type")
            })
        return rows
    
    def _parse_date(self, date_str: str) -> datetime:
        return datetime.strptime(date_str, "%m/%d/%Y") if date_str else None

class FidelityParser(BrokerParser):
    """Fidelity CSV format parser"""
    
    def parse(self, file_content: str) -> List[Dict[str, Any]]:
        rows = []
        reader = csv.DictReader(file_content.splitlines())
        for row in reader:
            rows.append({
                "date": self._parse_date(row.get("Run Date")),
                "symbol": row.get("Symbol"),
                "description": row.get("Description"),
                "quantity": Decimal(row.get("Quantity", "0")),
                "price": Decimal(row.get("Price", "0")),
                "amount": Decimal(row.get("Amount", "0")),
                "transaction_type": row.get("Action")
            })
        return rows
    
    def _parse_date(self, date_str: str) -> datetime:
        return datetime.strptime(date_str, "%m/%d/%Y") if date_str else None

class CommSecParser(BrokerParser):
    """CommSec (Australian) CSV format parser"""
    
    def parse(self, file_content: str) -> List[Dict[str, Any]]:
        rows = []
        reader = csv.DictReader(file_content.splitlines())
        for row in reader:
            rows.append({
                "date": self._parse_date(row.get("Date")),
                "symbol": row.get("Code"),
                "description": row.get("Description"),
                "quantity": Decimal(row.get("Quantity", "0")),
                "price": Decimal(row.get("Price", "0")),
                "amount": Decimal(row.get("Value", "0")),
                "transaction_type": row.get("Type"),
                "brokerage": Decimal(row.get("Brokerage", "0"))
            })
        return rows
    
    def _parse_date(self, date_str: str) -> datetime:
        return datetime.strptime(date_str, "%d/%m/%Y") if date_str else None

class NABTradeParser(BrokerParser):
    """NABTrade (Australian) CSV format parser"""
    
    def parse(self, file_content: str) -> List[Dict[str, Any]]:
        rows = []
        reader = csv.DictReader(file_content.splitlines())
        for row in reader:
            rows.append({
                "date": self._parse_date(row.get("Trade Date")),
                "symbol": row.get("Stock Code"),
                "description": row.get("Stock Name"),
                "quantity": Decimal(row.get("Quantity", "0")),
                "price": Decimal(row.get("Price", "0")),
                "amount": Decimal(row.get("Consideration", "0")),
                "transaction_type": row.get("Buy/Sell"),
                "brokerage": Decimal(row.get("Brokerage", "0"))
            })
        return rows
    
    def _parse_date(self, date_str: str) -> datetime:
        return datetime.strptime(date_str, "%d/%m/%Y") if date_str else None

def get_parser(broker_format: str) -> BrokerParser:
    """Factory method to get appropriate parser"""
    parsers = {
        "vanguard": VanguardParser(),
        "fidelity": FidelityParser(),
        "commsec": CommSecParser(),
        "nabtrade": NABTradeParser()
    }
    return parsers.get(broker_format, BrokerParser())
