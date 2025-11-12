"""Fiscal.ai MCP Server for UltraCore"""
import os
import json
import asyncio
from typing import Any, Dict, List, Optional
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

FISCAL_AI_API_BASE = "https://api.fiscal.ai/v1"
FISCAL_AI_API_KEY = os.getenv("FISCAL_AI_API_KEY", "")

if not FISCAL_AI_API_KEY:
    raise ValueError("FISCAL_AI_API_KEY environment variable is required")

class FiscalAIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = FISCAL_AI_API_BASE
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/{endpoint}"
            response = await client.get(url, headers=self.headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def get_company_profile(self, ticker: str) -> Dict[str, Any]:
        return await self._make_request(f"company/profile/{ticker}")
    
    async def get_income_statement(self, ticker: str, period: str = "annual", limit: int = 10) -> List[Dict[str, Any]]:
        return await self._make_request(f"financials/income-statement/{ticker}", {"period": period, "limit": limit})
    
    async def get_balance_sheet(self, ticker: str, period: str = "annual", limit: int = 10) -> List[Dict[str, Any]]:
        return await self._make_request(f"financials/balance-sheet/{ticker}", {"period": period, "limit": limit})
    
    async def get_cash_flow_statement(self, ticker: str, period: str = "annual", limit: int = 10) -> List[Dict[str, Any]]:
        return await self._make_request(f"financials/cash-flow/{ticker}", {"period": period, "limit": limit})
    
    async def get_company_ratios(self, ticker: str, period: str = "annual", limit: int = 10) -> List[Dict[str, Any]]:
        return await self._make_request(f"ratios/{ticker}", {"period": period, "limit": limit})
    
    async def get_stock_prices(self, ticker: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if from_date: params["from"] = from_date
        if to_date: params["to"] = to_date
        return await self._make_request(f"prices/{ticker}", params)
    
    async def search_companies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        return await self._make_request("companies/search", {"query": query, "limit": limit})

app = Server("fiscal-ai-mcp")
fiscal_client = FiscalAIClient(FISCAL_AI_API_KEY)

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_company_profile",
            description="Get company profile with sector, industry, and key metrics",
            inputSchema={"type": "object", "properties": {"ticker": {"type": "string", "description": "Stock ticker (e.g., AAPL)"}}, "required": ["ticker"]}
        ),
        Tool(
            name="get_income_statement",
            description="Get income statement data",
            inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}, "period": {"type": "string", "enum": ["annual", "quarterly"], "default": "annual"}, "limit": {"type": "integer", "default": 10}}, "required": ["ticker"]}
        ),
        Tool(
            name="get_balance_sheet",
            description="Get balance sheet with assets, liabilities, equity",
            inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}, "period": {"type": "string", "enum": ["annual", "quarterly"], "default": "annual"}, "limit": {"type": "integer", "default": 10}}, "required": ["ticker"]}
        ),
        Tool(
            name="get_cash_flow_statement",
            description="Get cash flow statement",
            inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}, "period": {"type": "string", "enum": ["annual", "quarterly"], "default": "annual"}, "limit": {"type": "integer", "default": 10}}, "required": ["ticker"]}
        ),
        Tool(
            name="get_company_ratios",
            description="Get financial ratios (P/E, ROE, debt ratios)",
            inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}, "period": {"type": "string", "enum": ["annual", "quarterly"], "default": "annual"}, "limit": {"type": "integer", "default": 10}}, "required": ["ticker"]}
        ),
        Tool(
            name="get_stock_prices",
            description="Get historical stock prices",
            inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}, "from_date": {"type": "string", "description": "YYYY-MM-DD"}, "to_date": {"type": "string", "description": "YYYY-MM-DD"}}, "required": ["ticker"]}
        ),
        Tool(
            name="search_companies",
            description="Search companies by name or ticker",
            inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]}
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    try:
        if name == "get_company_profile":
            result = await fiscal_client.get_company_profile(arguments["ticker"])
        elif name == "get_income_statement":
            result = await fiscal_client.get_income_statement(arguments["ticker"], arguments.get("period", "annual"), arguments.get("limit", 10))
        elif name == "get_balance_sheet":
            result = await fiscal_client.get_balance_sheet(arguments["ticker"], arguments.get("period", "annual"), arguments.get("limit", 10))
        elif name == "get_cash_flow_statement":
            result = await fiscal_client.get_cash_flow_statement(arguments["ticker"], arguments.get("period", "annual"), arguments.get("limit", 10))
        elif name == "get_company_ratios":
            result = await fiscal_client.get_company_ratios(arguments["ticker"], arguments.get("period", "annual"), arguments.get("limit", 10))
        elif name == "get_stock_prices":
            result = await fiscal_client.get_stock_prices(arguments["ticker"], arguments.get("from_date"), arguments.get("to_date"))
        elif name == "search_companies":
            result = await fiscal_client.search_companies(arguments["query"], arguments.get("limit", 10))
        else:
            raise ValueError(f"Unknown tool: {name}")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
