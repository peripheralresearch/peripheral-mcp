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
    |
FastMCP Server (10 tools)
    |
FastAPI (controlled endpoints)
    |
Supabase (Peripheral database)
```

**Security-first:** Layered architecture provides curated views, not raw database access.

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
- *"Search for stories about drone strikes"*
- *"Who is Zelensky mentioned with in recent articles?"*
- *"Show me the signal timeline for Kyiv this week"*
- *"Find articles about ceasefire negotiations"*

Claude will use the MCP tools to fetch live data from The Peripheral.

## MCP Tools (10 Total)

| Tool | Description |
|------|-------------|
| `health_check()` | Check API and database health |
| `get_latest_briefing(hours, region)` | Get intelligence briefing |
| `get_military_signals(region, hours, signal_type)` | Get military signals by region |
| `get_trending_stories(hours, limit)` | Get top stories by article count |
| `search_stories(query, hours, limit)` | Search stories by keyword/topic |
| `get_story_details(story_id)` | Get full story with articles and entities |
| `search_entities(name, entity_type, limit)` | Search people, orgs, locations, countries |
| `get_entity_context(entity_id, entity_type, hours)` | Get articles/stories mentioning an entity |
| `search_articles(query, hours, limit)` | Search individual news articles |
| `get_signal_timeline(region, hours)` | Get hourly signal timeline for escalation tracking |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info and endpoint list |
| GET | `/health` | Health check + DB connectivity |
| GET | `/briefing/latest` | Intelligence briefing |
| GET | `/signals/region/{region}` | Military signals by region |
| GET | `/signals/timeline/{region}` | Hourly signal timeline |
| GET | `/stories/trending` | Trending stories |
| GET | `/stories/search?q={query}` | Search stories |
| GET | `/stories/{story_id}` | Full story details with entities |
| GET | `/articles/search?q={query}` | Search articles |
| GET | `/entities/search?name={name}` | Search entities |
| GET | `/entities/{type}/{id}/context` | Entity context (articles/stories) |

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
uv run uvicorn src.api.main:app --reload --port 8000

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/briefing/latest?hours=24
curl "http://localhost:8000/stories/search?q=ukraine&hours=48"
curl "http://localhost:8000/entities/search?name=putin&type=person"
curl http://localhost:8000/signals/timeline/KYIV?hours=24
```

### Testing the MCP Server

```bash
# Run the MCP server locally
uv run peripheral-mcp

# Or directly
uv run python -m src.mcp.server
```

## Deployment

### API Server (Railway/Render)

Deploy the FastAPI server to your preferred platform:

```bash
# Railway
railway up

# Or Render (connect GitHub repo)
# Auto-deploys from main branch
```

### Prefect Cloud (Automated Workflows)

```bash
./deploy.sh
```

Deploys daily briefing generation to Prefect Cloud with automatic scheduling.

## Tech Stack

- **FastAPI** - REST API framework
- **FastMCP** - Model Context Protocol implementation
- **Prefect** - Workflow orchestration
- **Supabase** - PostgreSQL database
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
