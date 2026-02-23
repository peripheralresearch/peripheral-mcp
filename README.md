# The Peripheral - Public MCP Server

Public-facing MCP (Model Context Protocol) server providing access to **The Peripheral's** OSINT intelligence data.

[![Website](https://img.shields.io/badge/website-theperipheral.org-blue)](https://theperipheral.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## What is The Peripheral?

[The Peripheral](https://theperipheral.org) is an OSINT intelligence platform that tracks global news and military signals in real-time. We aggregate over 95,000+ articles from diverse sources and track 336,000+ military signals to provide verified, context-rich intelligence briefings.

This MCP server makes that data accessible to AI assistants like Claude Desktop via the Model Context Protocol.

## Architecture

```
MCP Clients (Claude Desktop, etc.)
    ↓
FastMCP Server (4 tools)
    ↓
FastAPI (controlled endpoints)
    ↓
Supabase (Peripheral database)
```

**Security-first:** Layered architecture provides curated views, not raw database access.

## Features

- 📰 **Latest intelligence briefings** (24h, 7d, regional)
- 🎯 **Military signals by region** (Ukraine, Middle East, etc.)
- 📊 **Trending stories** (ranked by cluster size)
- 🔍 **Semantic search** (coming soon)
- 📡 **Real-time alerts** (air defense, threats)

## For Users

### Install in Claude Desktop

Add to your Claude Desktop MCP settings (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "peripheral": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/peripheralresearch/peripheral-mcp", "peripheral-mcp"]
    }
  }
}
```

### Usage Examples

Once configured, you can ask Claude:

- *"What's happening in Ukraine today?"*
- *"Show me the latest Peripheral intelligence briefing"*
- *"Get military signals for Kharkiv region in the last 12 hours"*
- *"What are the top 5 trending stories?"*

Claude will use the MCP tools to fetch live data from The Peripheral.

## For Developers

### Local Development

```bash
# Clone the repository
git clone https://github.com/peripheralresearch/peripheral-mcp
cd peripheral-mcp

# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Run the API server
uv run uvicorn src.api.main:app --reload

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/briefing/latest?hours=24
```

### API Endpoints

- `GET /` - API info and endpoint list
- `GET /health` - Health check + DB connectivity
- `GET /briefing/latest` - Intelligence briefing (24h default)
- `GET /signals/region/{region}` - Military signals by region
- `GET /stories/trending` - Trending stories by cluster size

### MCP Tools

The FastMCP server exposes 4 tools:

1. **get_latest_briefing(hours, region)** - Fetch intelligence briefing
2. **get_military_signals(region, hours, signal_type)** - Get regional military activity
3. **get_trending_stories(hours, limit)** - Get top stories
4. **health_check()** - Verify system health

## Deployment

### Prefect Cloud (Automated Workflows)

```bash
./deploy.sh
```

This deploys daily briefing generation to Prefect Cloud with automatic scheduling.

### API Server (Railway/Render)

Deploy the FastAPI server to your preferred platform:

```bash
# Railway
railway up

# Or Render (connect GitHub repo)
# Auto-deploys from master branch
```

## Tech Stack

- **FastAPI** - REST API framework
- **FastMCP** - Model Context Protocol implementation
- **Prefect** - Workflow orchestration
- **Supabase** - PostgreSQL database + real-time subscriptions
- **uv** - Python package manager

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## About The Peripheral

Visit [theperipheral.org](https://theperipheral.org) to learn more about our OSINT platform and intelligence methodology.

For questions or feedback: [Contact Us](https://theperipheral.org/contact)

---

**Built with ❤️ for the OSINT community**
