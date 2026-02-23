# The Peripheral - Public MCP Server

Public-facing MCP (Model Context Protocol) server providing access to The Peripheral's OSINT intelligence data.

## Architecture

```
MCP Clients (Claude, etc.)
    ↓
FastMCP Server
    ↓
FastAPI (controlled endpoints)
    ↓
Supabase (Sentinel database)
```

## Features

- 📰 Latest intelligence briefings (24h, 7d, regional)
- 🎯 Military signals by region
- 📊 Trending stories (by cluster size)
- 🔍 Semantic search (when available)
- 📡 Real-time Ukraine air defense alerts

## Deployment

Deployed via Prefect Cloud + GitHub Actions.

## Development

```bash
uv sync
uv run uvicorn src.api.main:app --reload
```

## MCP Usage

Add to your MCP settings:

```json
{
  "mcpServers": {
    "peripheral": {
      "command": "uvx",
      "args": ["--from", "peripheral-mcp", "peripheral-mcp"]
    }
  }
}
```
