# The Peripheral - Public MCP Server

Public-facing MCP (Model Context Protocol) server providing access to **The Peripheral's** OSINT intelligence data.

[![Website](https://img.shields.io/badge/website-theperipheral.org-blue)](https://theperipheral.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## What is The Peripheral?

[The Peripheral](https://theperipheral.org) is an OSINT intelligence platform that tracks global news and military signals in real-time. We aggregate over 95,000+ articles from diverse sources and track 336,000+ military signals to provide verified, context-rich intelligence briefings.

This MCP server makes that data accessible to AI assistants like Claude Desktop via the Model Context Protocol.

## Architecture

Two server modes are available:

**Cloud (recommended for remote access):** Single service, direct Supabase queries, token auth.
```
AI Agents (Claude Code, OpenClaw, custom)
    |  Streamable HTTP + Bearer Token
    v
Cloud Server (FastMCP HTTP transport)
    /mcp    — MCP protocol (10 tools)
    /health — monitoring
    |  PostgREST
    v
Supabase (118K articles, 80K stories, 338K signals)
```

**Local (stdio):** For Claude Desktop via `uvx`, proxies through FastAPI.
```
Claude Desktop -> FastMCP (stdio) -> FastAPI -> Supabase
```

## Connect to Cloud Server

For streamable-http capable clients (Claude Code, etc.), add to your MCP config:

```json
{
  "mcpServers": {
    "peripheral": {
      "type": "streamable-http",
      "url": "https://<railway-url>/mcp",
      "headers": { "Authorization": "Bearer <your-token>" }
    }
  }
}
```

Ask your admin for a bearer token, or if auth is disabled, omit the `headers` field.

### Install via Claude Desktop (stdio)

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

### Cloud MCP Server (Railway)

Deploy the cloud server which exposes MCP over HTTP:

```bash
# Set env vars on Railway
railway variables set SUPABASE_URL=... SUPABASE_KEY=... MCP_AUTH_TOKENS=...

# Deploy
railway up
```

Generate tokens for friends:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Set `MCP_AUTH_TOKENS` to a comma-separated list of tokens. Empty = open access (no auth).

### Local Cloud Server Testing

```bash
export SUPABASE_URL=... SUPABASE_KEY=... MCP_AUTH_TOKENS=""
uv run uvicorn src.mcp.cloud_server:app --port 8000

# Health check
curl http://localhost:8000/health

# MCP initialize handshake
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
```

### Legacy FastAPI Server

```bash
uv run uvicorn src.api.main:app --reload --port 8000
```

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
