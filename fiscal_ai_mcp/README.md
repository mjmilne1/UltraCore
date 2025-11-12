# Fiscal.ai MCP Integration

Integration of Fiscal.ai financial data with UltraCore platform via Model Context Protocol.

## Features

- Company profiles and fundamentals
- Income statements, balance sheets, cash flow
- Financial ratios and metrics
- Historical stock prices
- SEC filings access
- Company search

## Setup

1. Install dependencies:
```powershell
cd fiscal_ai_mcp
pip install -r requirements.txt
```

2. Configure your API key in .env

3. Run the MCP server:
```powershell
python server.py
```

## Claude Desktop Integration

Add to your Claude Desktop config (%APPDATA%\Claude\claude_desktop_config.json):
```json
{
  "mcpServers": {
    "fiscal-ai": {
      "command": "python",
      "args": ["-m", "fiscal_ai_mcp.server"],
      "env": {
        "FISCAL_AI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Usage Examples
```python
# In Claude or your application:
"Get Apple's latest income statement"
"Show me Microsoft's financial ratios"
"Search for tech companies"
```

## API Documentation

See: https://docs.fiscal.ai/
